from pathlib import Path

import pytest
from rdflib import Graph, Literal, RDF, RDFS, URIRef

from app.documentation import canonical_documents, project_markdown
from app.publication import CandidateEnvelope, PublicationModule


def test_published_meeting_has_searchable_english_documentation(isolated_services):
    store, graph = isolated_services
    envelope = CandidateEnvelope.model_validate_json(
        (Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8")
    )
    result = PublicationModule(store, graph).publish(envelope)

    iri = "https://w3id.org/motorsport-hub/resource/meeting/f1%3A2026%3Aaustralia"
    document = store.lookup_document(iri, result.version)
    assert document["iri"] == iri
    assert document["rdfTypes"] == ["https://w3id.org/motorsport-hub/ontology/Meeting"]
    assert document["language"] == "en"
    assert document["publicationVersion"] == result.version
    assert "Australian" in document["markdown"]
    assert document["sources"][0]["url"] == envelope.source_url
    assert any(hit["iri"] == iri for hit in store.search_documents("Australian", result.version))
    assert store.lookup_document("https://example.com/not-canonical", result.version) is None


def test_assistant_read_views_exclude_maintenance_fields(isolated_services):
    store, graph = isolated_services
    envelope = CandidateEnvelope.model_validate_json(
        (Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8")
    )
    published = PublicationModule(store, graph).publish(envelope)
    reader = store.assistant_reader()
    assert reader.current_publication_version() == published.version
    assert len(reader.visible_meetings(published.version)) == 1
    document = reader.search_documents("Australian", published.version)[0]
    assert "translationAuthorization" not in document["markdown"]
    assert reader.lookup_document(document["iri"], published.version) == document


def test_search_projection_failure_preserves_previous_publication(isolated_services):
    store, graph = isolated_services
    candidate = CandidateEnvelope.model_validate_json((Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8"))
    publisher = PublicationModule(store, graph)
    first = publisher.publish(candidate)
    revised = candidate.model_copy(update={"meeting": candidate.meeting.model_copy(update={"meeting_name": "Revised Australian Meeting"})})
    from app.publication import publication_version
    revision = publication_version(revised)
    store.stage(revision, revised)
    assert store.search_documents("Revised", revision) == []
    store.replace_search_documents(revision, [])
    with pytest.raises(RuntimeError, match="Search projection"):
        store.promote(revision)
    assert store.current_publication_version() == first.version
    assert store.search_documents("Australian", first.version)
    publisher.publish(revised)
    assert store.current_publication_version() == revision
    assert store.search_documents("Revised", revision)


@pytest.mark.parametrize("invalid", ["duplicate", "iri", "type", "language", "reference"])
def test_invalid_markdown_is_rejected_before_search_projection(invalid):
    iri = URIRef("https://w3id.org/motorsport-hub/resource/circuit/albert-park")
    graph = Graph()
    graph.add((iri, RDF.type, URIRef("https://w3id.org/motorsport-hub/ontology/Circuit")))
    graph.add((iri, RDFS.label, Literal("Albert Park", lang="en")))
    markdown = canonical_documents(graph, "a" * 64)[0]["markdown"]
    documents = [markdown]
    if invalid == "duplicate":
        documents.append(markdown)
    elif invalid == "iri":
        documents = [markdown.replace("resource/circuit/albert-park", "resource/circuit/missing")]
    elif invalid == "type":
        documents = [markdown.replace("ontology/Circuit", "ontology/Meeting")]
    elif invalid == "language":
        documents = [markdown.replace("language: en", "language: de")]
    else:
        documents = [markdown + "\n[Missing](https://w3id.org/motorsport-hub/resource/circuit/missing)\n"]
    with pytest.raises(ValueError):
        project_markdown(documents, graph, "a" * 64)