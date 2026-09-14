import json
import subprocess
import sys
from pathlib import Path

import pytest
from rdflib import Dataset, Graph, Literal, Namespace, OWL, RDF, RDFS, XSD


ONTOLOGY = Namespace("https://w3id.org/motorsport-hub/ontology/")
RESOURCE = Namespace("https://w3id.org/motorsport-hub/resource/")
GRAPH = Namespace("https://w3id.org/motorsport-hub/graph/ontology-review/")


def test_private_proposal_keeps_asserted_and_inferred_statements_separate(tmp_path):
    ontology = tmp_path / "ontology.ttl"
    ontology.write_text((ROOT / "ontology/motorsport.ttl").read_text(encoding="utf-8"), encoding="utf-8")
    data = tmp_path / "data.ttl"
    data.write_text('''
        @prefix msh: <https://w3id.org/motorsport-hub/ontology/> .
        @prefix resource: <https://w3id.org/motorsport-hub/resource/> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        resource:championship a msh:Championship ; rdfs:label "Example championship"@en .
    ''', encoding="utf-8")
    proposal = tmp_path / "proposal.json"
    proposal.write_text(json.dumps({
        "title": "Prove championship classification",
        "rationale": "Check that the private review separates inference.",
        "compatibility_notes": "No vocabulary change; existing queries remain valid.",
        "migration_notes": "No migration required.",
        "renames": {},
    }), encoding="utf-8")
    output = tmp_path / "review"
    completed = subprocess.run([
        sys.executable, "-m", "app.ontology_maintenance",
        "--baseline", str(ontology), "--ontology", str(ontology),
        "--data", str(data), "--proposal", str(proposal), "--output", str(output),
    ], capture_output=True, text=True, timeout=60)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    dataset = Dataset()
    dataset.parse(output / "knowledge.trig", format="trig")
    asserted = dataset.graph(GRAPH.asserted)
    inferred = dataset.graph(GRAPH.inferred)
    assert (RESOURCE.championship, RDF.type, ONTOLOGY.Championship) in asserted
    assert (RESOURCE.championship, RDF.type, ONTOLOGY.Competition) not in asserted
    assert (RESOURCE.championship, RDF.type, ONTOLOGY.Competition) in inferred
    assert not set(asserted) & set(inferred)
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "pending-review"
    assert report["published"] is False


ROOT = Path(__file__).resolve().parents[2]


def run_example(tmp_path, data=None, ontology=None, proposal=None):
    output = tmp_path / "review"
    completed = subprocess.run([
        sys.executable, "-m", "app.ontology_maintenance",
        "--baseline", str(ROOT / "ontology/motorsport.ttl"),
        "--ontology", str(ontology or ROOT / "ontology/motorsport.ttl"),
        "--data", str(data or ROOT / "ontology/examples/schedule.ttl"),
        "--proposal", str(proposal or ROOT / "ontology/examples/proposal.json"),
        "--output", str(output),
    ], capture_output=True, text=True, timeout=60)
    return completed, output


def test_competency_queries_prove_class_inverse_and_shared_circuit(tmp_path):
    completed, output = run_example(tmp_path)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    dataset = Dataset()
    dataset.parse(output / "knowledge.trig", format="trig")
    inferred = dataset.graph(GRAPH.inferred)
    assert (RESOURCE["example-championship-a"], RDF.type, ONTOLOGY.Competition) in inferred
    assert (RESOURCE["example-circuit"], ONTOLOGY.isCircuitOf, RESOURCE["example-meeting-a"]) in inferred
    assert bool(inferred.query('''ASK {
        <https://w3id.org/motorsport-hub/resource/example-meeting-a>
        <https://w3id.org/motorsport-hub/ontology/sharesCircuitWith>
        <https://w3id.org/motorsport-hub/resource/example-meeting-b>
    }'''))
    assert (RESOURCE["example-meeting-a"], ONTOLOGY.sharesCircuitWith, RESOURCE["unrelated-meeting"]) not in inferred
    assert not set(dataset.graph(GRAPH.asserted)) & set(inferred)


@pytest.mark.parametrize("invalid", ["missing-circuit", "date-order", "duplicate-identity", "non-English", "untagged", "placeholder", "tagged-code"])
def test_shacl_blocks_invalid_and_non_english_examples(tmp_path, invalid):
    data = Graph().parse(ROOT / "ontology/examples/schedule.ttl", format="turtle")
    meeting = RESOURCE["example-meeting-a"]
    if invalid == "missing-circuit":
        data.remove((meeting, ONTOLOGY.circuit, None))
    elif invalid == "date-order":
        data.set((meeting, ONTOLOGY.endDate, Literal("2026-03-01", datatype=XSD.date)))
    elif invalid == "duplicate-identity":
        data.set((RESOURCE["unrelated-circuit"], ONTOLOGY.identity, Literal("example-circuit")))
    elif invalid == "non-English":
        data.set((meeting, RDFS.label, Literal("Rencontre", lang="fr")))
    elif invalid == "untagged":
        data.set((meeting, RDFS.label, Literal("Example meeting")))
    elif invalid == "placeholder":
        data.add((Namespace("https://example.org/").meeting, RDF.type, ONTOLOGY.Meeting))
    elif invalid == "tagged-code":
        data.add((meeting, ONTOLOGY.status, Literal("scheduled", lang="en")))
    path = tmp_path / "invalid.ttl"
    data.serialize(path, format="turtle")
    completed, output = run_example(tmp_path, data=path)
    assert completed.returncode == 2, completed.stdout + completed.stderr
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert report["conforms"] is False
    validation = Graph().parse(output / "validation.ttl", format="turtle")
    assert (None, RDF.type, Namespace("http://www.w3.org/ns/shacl#").ValidationResult) in validation


@pytest.mark.parametrize("literal_options", [{}, {"datatype": XSD.string}, {"lang": "en"}, {"lang": "fr"}],
                         ids=["plain", "typed-string", "english-tagged", "french-tagged"])
def test_regulation_machine_fields_require_neutral_strings(tmp_path, literal_options):
    values = {
        ONTOLOGY.checksum: "a" * 64,
        ONTOLOGY.sectionAnchor: "B2.2.1",
        ONTOLOGY.evidenceKind: "original",
        ONTOLOGY.topic: "scoring",
        ONTOLOGY.knowledgeState: "known",
        ONTOLOGY.vehicleField: "manufacturer",
    }
    data = Graph()
    for predicate, value in values.items():
        data.add((RESOURCE["example-regulation"], predicate, Literal(value, **literal_options)))
    path = tmp_path / "regulation.ttl"
    data.serialize(path, format="turtle")
    completed, output = run_example(tmp_path, data=path)
    expected_conforms = "lang" not in literal_options
    assert completed.returncode == (0 if expected_conforms else 2), completed.stdout + completed.stderr
    report = json.loads((output / "report.json").read_text("utf-8"))
    assert report["conforms"] is expected_conforms
    assert report["published"] is False
    validation = Graph().parse(output / "validation.ttl", format="turtle")
    paths = set(validation.objects(None, Namespace("http://www.w3.org/ns/shacl#").resultPath))
    assert paths == (set() if expected_conforms else set(values))


@pytest.mark.parametrize("literal_options", [{"lang": "en"}, {}, {"datatype": XSD.string}, {"lang": "fr"}],
                         ids=["english", "untagged", "typed-string", "non-english"])
def test_regulation_prose_still_requires_english(tmp_path, literal_options):
    predicates = {RDFS.label, RDFS.comment, ONTOLOGY.evidence, ONTOLOGY.translationMethod,
                  ONTOLOGY.passageText, ONTOLOGY.normalizedValue, ONTOLOGY.value,
                  ONTOLOGY.authority, ONTOLOGY.applicability}
    data = Graph()
    for predicate in predicates:
        data.add((RESOURCE["example-regulation"], predicate, Literal("Example prose", **literal_options)))
    path = tmp_path / "prose.ttl"
    data.serialize(path, format="turtle")
    completed, output = run_example(tmp_path, data=path)
    expected_conforms = literal_options.get("lang") == "en"
    assert completed.returncode == (0 if expected_conforms else 2), completed.stdout + completed.stderr
    report = json.loads((output / "report.json").read_text("utf-8"))
    assert report["conforms"] is expected_conforms
    assert report["published"] is False
    validation = Graph().parse(output / "validation.ttl", format="turtle")
    paths = set(validation.objects(None, Namespace("http://www.w3.org/ns/shacl#").resultPath))
    assert paths == (set() if expected_conforms else predicates)


def test_vocabulary_rename_rehearses_migration_and_records_compatibility(tmp_path):
    ontology = Graph().parse(ROOT / "ontology/motorsport.ttl", format="turtle")
    candidate = Graph()
    for triple in ontology:
        subject, predicate, value = (ONTOLOGY.usesCircuit if term == ONTOLOGY.circuit else term for term in triple)
        candidate.add((subject, predicate, value))
    path = tmp_path / "candidate.ttl"
    candidate.serialize(path, format="turtle")
    metadata = json.loads((ROOT / "ontology/examples/proposal.json").read_text(encoding="utf-8"))
    metadata["renames"] = {str(ONTOLOGY.circuit): str(ONTOLOGY.usesCircuit)}
    metadata["compatibility_notes"] = "Breaking: SPARQL consumers must use usesCircuit after coordinated approval."
    metadata["migration_notes"] = "Rename the circuit predicate in example assertions; retain all resource identities."
    proposal = tmp_path / "proposal.json"
    proposal.write_text(json.dumps(metadata), encoding="utf-8")
    original = (ROOT / "ontology/examples/schedule.ttl").read_bytes()
    completed, output = run_example(tmp_path, ontology=path, proposal=proposal)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    migrated = Graph().parse(output / "migrated.ttl", format="turtle")
    assert (RESOURCE["example-meeting-a"], ONTOLOGY.usesCircuit, RESOURCE["example-circuit"]) in migrated
    assert (None, ONTOLOGY.circuit, None) not in migrated
    assert (ROOT / "ontology/examples/schedule.ttl").read_bytes() == original
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["compatibility"] == "breaking"
    assert report["migration"]["changed_triples"] == 3
    assert report["status"] == "pending-review"
    notes = (output / "review.md").read_text(encoding="utf-8")
    assert metadata["compatibility_notes"] in notes
    assert metadata["migration_notes"] in notes


@pytest.mark.parametrize("axiom", ["class", "inverse", "shared-circuit"])
def test_candidate_with_broken_competency_is_blocked_before_review(tmp_path, axiom):
    candidate = Graph().parse(ROOT / "ontology/motorsport.ttl", format="turtle")
    if axiom == "class":
        candidate.remove((ONTOLOGY.Championship, RDFS.subClassOf, ONTOLOGY.Competition))
    elif axiom == "inverse":
        candidate.remove((ONTOLOGY.circuit, OWL.inverseOf, ONTOLOGY.isCircuitOf))
    else:
        candidate.remove((ONTOLOGY.sharesCircuitWith, OWL.propertyChainAxiom, None))
    path = tmp_path / "candidate.ttl"
    candidate.serialize(path, format="turtle")
    completed, output = run_example(tmp_path, ontology=path)
    assert completed.returncode == 2, completed.stdout + completed.stderr
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["status"] == "blocked"
    assert report["competency"][axiom] is False


def test_current_publication_rdf_can_be_reviewed_without_publication(tmp_path):
    from app.publication import CandidateEnvelope
    from app.stores import GraphDbProjection

    envelope = CandidateEnvelope.model_validate_json((ROOT / "backend/fixtures/f1-2026-australia.json").read_text("utf-8"))
    data = GraphDbProjection.build_graph("a" * 64, envelope)
    path = tmp_path / "publication.ttl"
    data.serialize(path, format="turtle")
    completed, output = run_example(tmp_path, data=path)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["conforms"] is True
    assert all(report["competency"].values())
    assert report["published"] is False


@pytest.mark.parametrize("invalid", ["non-English-vocabulary", "notes", "unknown-option", "rename-cycle", "placeholder-rename"])
def test_invalid_proposals_cannot_become_review_ready(tmp_path, invalid):
    candidate = Graph().parse(ROOT / "ontology/motorsport.ttl", format="turtle")
    metadata = json.loads((ROOT / "ontology/examples/proposal.json").read_text("utf-8"))
    if invalid == "non-English-vocabulary":
        candidate.set((ONTOLOGY.Meeting, RDFS.comment, Literal("Rencontre", lang="fr")))
    elif invalid == "notes":
        metadata["compatibility_notes"] = " "
    elif invalid == "unknown-option":
        metadata["approve_and_publish"] = True
    elif invalid == "rename-cycle":
        metadata["renames"] = {str(ONTOLOGY.circuit): str(ONTOLOGY.competition), str(ONTOLOGY.competition): str(ONTOLOGY.circuit)}
    else:
        metadata["renames"] = {str(ONTOLOGY.circuit): "https://example.org/circuit"}
    path = tmp_path / "candidate.ttl"
    candidate.serialize(path, format="turtle")
    proposal = tmp_path / "proposal.json"
    proposal.write_text(json.dumps(metadata), encoding="utf-8")
    completed, output = run_example(tmp_path, ontology=path, proposal=proposal)
    assert completed.returncode == 2, completed.stdout + completed.stderr
    if (output / "report.json").exists():
        assert json.loads((output / "report.json").read_text("utf-8"))["status"] == "blocked"


def test_existing_review_bundle_is_never_overwritten(tmp_path):
    output = tmp_path / "review"
    output.mkdir()
    marker = output / "review.md"
    marker.write_text("Human-reviewed material", encoding="utf-8")
    completed, _ = run_example(tmp_path)
    assert completed.returncode == 2
    assert marker.read_text("utf-8") == "Human-reviewed material"


def test_identity_rename_keeps_duplicate_identity_validation(tmp_path):
    baseline = Graph().parse(ROOT / "ontology/motorsport.ttl", format="turtle")
    candidate = Graph()
    for triple in baseline:
        subject, predicate, value = (ONTOLOGY.canonicalKey if term == ONTOLOGY.identity else term for term in triple)
        candidate.add((subject, predicate, value))
    path = tmp_path / "candidate.ttl"
    candidate.serialize(path, format="turtle")
    metadata = json.loads((ROOT / "ontology/examples/proposal.json").read_text("utf-8"))
    metadata["renames"] = {str(ONTOLOGY.identity): str(ONTOLOGY.canonicalKey)}
    proposal = tmp_path / "proposal.json"
    proposal.write_text(json.dumps(metadata), encoding="utf-8")
    data = Graph().parse(ROOT / "ontology/examples/schedule.ttl", format="turtle")
    data.set((RESOURCE["unrelated-circuit"], ONTOLOGY.identity, Literal("example-circuit")))
    data_path = tmp_path / "data.ttl"
    data.serialize(data_path, format="turtle")
    completed, output = run_example(tmp_path, ontology=path, proposal=proposal, data=data_path)
    assert completed.returncode == 2, completed.stdout + completed.stderr
    assert json.loads((output / "report.json").read_text("utf-8"))["conforms"] is False