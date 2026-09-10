import argparse
import hashlib
import json
from pathlib import Path

from owlrl import DeductiveClosure, OWLRL_Semantics
from pydantic import BaseModel, ConfigDict, Field
from rdflib import Dataset, Graph, Namespace, RDF, URIRef
from rdflib.compare import graph_diff, to_isomorphic

from .ontology_validation import ONTOLOGY, rename_term, validate_graph


REVIEW_GRAPH = Namespace("https://w3id.org/motorsport-hub/graph/ontology-review/")


class Proposal(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=200)
    rationale: str = Field(min_length=1, max_length=5000)
    compatibility_notes: str = Field(min_length=1, max_length=5000)
    migration_notes: str = Field(min_length=1, max_length=5000)
    renames: dict[str, str] = Field(default_factory=dict, max_length=100)


def load_graph(path: Path) -> Graph:
    if path.stat().st_size > 1_000_000:
        raise ValueError("Review inputs must be at most 1 MB")
    graph = Graph().parse(data=path.read_text(encoding="utf-8"), format="turtle", publicID=str(ONTOLOGY))
    if len(graph) > 5000:
        raise ValueError("Review inputs must be at most 5000 triples")
    return graph


def migrate(data: Graph, renames: dict[URIRef, URIRef]) -> Graph:
    migrated = Graph()
    for subject, predicate, value in data:
        migrated.add((rename_term(subject, renames), rename_term(predicate, renames), rename_term(value, renames)))
    return migrated


def competency_checks(ontology: Graph, renames: dict[URIRef, URIRef]) -> tuple[dict[str, bool], Dataset]:
    resource = Namespace("https://w3id.org/motorsport-hub/resource/")
    examples = migrate(load_graph(Path(__file__).resolve().parents[2] / "ontology/examples/schedule.ttl"), renames)
    closure = ontology + examples
    DeductiveClosure(OWLRL_Semantics).expand(closure)
    inferred = closure - ontology - examples
    expectations = {
        "class": (resource["example-championship-a"], RDF.type, ONTOLOGY.Competition),
        "inverse": (resource["example-circuit"], ONTOLOGY.isCircuitOf, resource["example-meeting-a"]),
        "shared-circuit": (resource["example-meeting-a"], ONTOLOGY.sharesCircuitWith, resource["example-meeting-b"]),
    }
    results = {}
    for name, triple in expectations.items():
        subject, predicate, value = (renames.get(term, term) for term in triple)
        results[name] = bool(inferred.query("ASK { ?subject ?predicate ?value }", initBindings={
            "subject": subject, "predicate": predicate, "value": value,
        }))
    results["distinct-circuit-identities"] = (
        resource["example-meeting-a"], renames.get(ONTOLOGY.sharesCircuitWith, ONTOLOGY.sharesCircuitWith),
        resource["unrelated-meeting"],
    ) not in closure
    results["graph-separation"] = not bool(set(examples) & set(inferred))
    dataset = Dataset()
    asserted_graph = dataset.graph(REVIEW_GRAPH.asserted)
    asserted_graph += examples
    inferred_graph = dataset.graph(REVIEW_GRAPH.inferred)
    inferred_graph += inferred
    ontology_graph = dataset.graph(REVIEW_GRAPH.ontology)
    ontology_graph += ontology
    return results, dataset


def prepare_review(baseline_path: Path, ontology_path: Path, data_path: Path, proposal_path: Path, output: Path) -> bool:
    if output.exists():
        raise ValueError("Use a new output directory; existing review bundles are never overwritten")
    baseline = load_graph(baseline_path)
    ontology = load_graph(ontology_path)
    original = load_graph(data_path)
    proposal = Proposal.model_validate_json(proposal_path.read_text(encoding="utf-8"))
    renames = {URIRef(old): URIRef(new) for old, new in proposal.renames.items()}
    if len(set(renames.values())) != len(renames) or set(renames) & set(renames.values()):
        raise ValueError("Renames must be one-to-one, without cycles or chains")
    for old, new in renames.items():
        if not str(old).startswith(str(ONTOLOGY)) or not str(new).startswith(str(ONTOLOGY)):
            raise ValueError("Only vocabulary IRIs under the approved authority can be renamed")
        if (old, None, None) not in baseline or (new, None, None) not in ontology:
            raise ValueError("Each rename must map a declared baseline term to a declared candidate term")
        if (new, None, None) in baseline or any(old in triple for triple in ontology):
            raise ValueError("Renames cannot merge existing terms or leave the old term in the candidate")
    instances = migrate(original, renames)
    ontology_valid, ontology_report, ontology_text = validate_graph(ontology, vocabulary=True, renames=renames)
    instances_valid, instances_report, instances_text = validate_graph(instances, renames=renames)
    conforms = ontology_valid and instances_valid
    competency, competency_dataset = competency_checks(ontology, renames) if conforms else ({}, Dataset())
    ready = conforms and bool(competency) and all(competency.values())
    closure = ontology + instances
    if conforms:
        DeductiveClosure(OWLRL_Semantics).expand(closure)
    dataset = Dataset()
    vocabulary_graph = dataset.graph(REVIEW_GRAPH.ontology)
    vocabulary_graph += ontology
    asserted = dataset.graph(REVIEW_GRAPH.asserted)
    asserted += instances
    inferred = dataset.graph(REVIEW_GRAPH.inferred)
    inferred += closure - ontology - instances
    _, removed, added = graph_diff(to_isomorphic(baseline), to_isomorphic(ontology))
    compatibility = "breaking" if len(removed) else "additive" if len(added) else "unchanged"
    report = {
        "status": "pending-review" if ready else "blocked", "published": False, "conforms": conforms,
        "competency": competency,
        "proposal": proposal.model_dump(), "compatibility": compatibility,
        "removed_triples": len(removed), "added_triples": len(added),
        "migration": {"renames": proposal.renames, "changed_triples": len(original - instances)},
        "inputs_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in (
            ("baseline", baseline_path), ("ontology", ontology_path), ("data", data_path), ("proposal", proposal_path),
        )},
        "asserted_triples": len(asserted), "inferred_triples": len(inferred),
    }
    output.mkdir(parents=True, exist_ok=False)
    dataset.serialize(output / "knowledge.trig", format="trig")
    competency_dataset.serialize(output / "competency.trig", format="trig")
    instances.serialize(output / "migrated.ttl", format="turtle")
    ontology.serialize(output / "ontology.ttl", format="turtle")
    removed.serialize(output / "removed.ttl", format="turtle")
    added.serialize(output / "added.ttl", format="turtle")
    (ontology_report + instances_report).serialize(output / "validation.ttl", format="turtle")
    (output / "validation.txt").write_text(ontology_text + "\n" + instances_text, encoding="utf-8")
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (output / "review.md").write_text(
        f"# {proposal.title}\n\n{proposal.rationale}\n\n"
        f"Status: {report['status']}. Private review only; nothing has been published.\n\n"
        f"## Compatibility\n\nClassification: {compatibility}. Removed {len(removed)} triples; added {len(added)}.\n\n"
        f"{proposal.compatibility_notes}\n\n## Migration\n\n{proposal.migration_notes}\n\n"
        f"Changed {len(original - instances)} example triples. Resource identities are preserved.\n\n"
        "## Human Review\n\nRecord reviewer, timestamp, rationale and exact input hashes in the issue. "
        "Inspect the vocabulary delta, validation results and competency tests. "
        "Approval does not publish this bundle; publication requires a separate authorized workflow.\n",
        encoding="utf-8",
    )
    return ready


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a private ontology review; never publish.")
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--ontology", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--proposal", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        conforms = prepare_review(args.baseline, args.ontology, args.data, args.proposal, args.output)
    except (ValueError, OSError) as error:
        parser.exit(2, f"Review blocked: {error}\n")
    return 0 if conforms else 2


if __name__ == "__main__":
    raise SystemExit(main())