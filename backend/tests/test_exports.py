import csv
import hashlib
import io
from pathlib import Path
import psycopg

from fastapi.testclient import TestClient
from rdflib import Graph, Literal, Namespace, OWL, RDF, RDFS, URIRef
from rdflib.compare import isomorphic
from rdflib.util import from_n3
from rdflib.term import Node

from app.main import app, operational_store
from app.publication import CandidateEnvelope, PublicationModule, parse_candidate, publication_version
from backend.tests.test_vehicles import vehicle_candidate


MOTORSPORT = Namespace("https://w3id.org/motorsport-hub/ontology/")
MEETING = URIRef("https://w3id.org/motorsport-hub/resource/meeting/f1%3A2026%3Aaustralia")


def test_turtle_download_contains_accepted_public_knowledge_only(isolated_services):
    store, projection = isolated_services
    candidate = CandidateEnvelope.model_validate_json((Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8"))
    candidate.evidence = "Private approval notes must never be exported"
    published = PublicationModule(store, projection).publish(candidate)
    app.dependency_overrides[operational_store] = lambda: store
    try:
        with TestClient(app) as client:
            response = client.get(f"/api/exports/publications/{published.version}/turtle")
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/turtle")
            assert published.version in response.headers["content-disposition"]
            graph = Graph().parse(data=response.text, format="turtle")
            assert (MEETING, RDF.type, MOTORSPORT.Meeting) in graph
            assert (MEETING, RDFS.label, Literal("Australian Grand Prix", lang="en")) in graph
            assert (None, MOTORSPORT.includesMeeting, MEETING) in graph
            assert (None, MOTORSPORT.version, Literal(published.version)) in graph
            assert (None, MOTORSPORT.sourceUrl, URIRef(candidate.source_url)) in graph
            assert list(graph.objects(None, MOTORSPORT.retrievedAt))
            assert "Private approval" not in response.text
            assert not list(graph.objects(None, MOTORSPORT.evidence))
    finally:
        app.dependency_overrides.clear()


def test_export_selection_excludes_staged_data_and_rejects_old_versions(isolated_services):
    store, projection = isolated_services
    app.dependency_overrides[operational_store] = lambda: store
    candidate = CandidateEnvelope.model_validate_json((Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8"))
    try:
        with TestClient(app) as client:
            manifest = client.get("/api/exports")
            assert manifest.status_code == 200
            assert manifest.json()["publicationVersion"] is None
            staged = publication_version(candidate)
            store.stage(staged, candidate)
            assert client.get(f"/api/exports/publications/{staged}/json").status_code == 409
            published = PublicationModule(store, projection).publish(candidate)
            assert client.get("/api/exports").json()["publicationVersion"] == published.version
            changed = candidate.model_copy(deep=True)
            changed.meeting.meeting_name = "Updated Australian Grand Prix"
            next_version = publication_version(changed)
            store.stage(next_version, changed)
            assert client.get(f"/api/exports/publications/{next_version}/csv").status_code == 409
            assert "Updated Australian" not in client.get(f"/api/exports/publications/{published.version}/json").text
            PublicationModule(store, projection).publish(changed)
            for format in ("json", "csv", "turtle"):
                assert client.get(f"/api/exports/publications/{published.version}/{format}").status_code == 409
            assert client.get(f"/api/exports/publications/{next_version}/sql").status_code == 422
            assert client.get("/api/exports/publications/not-a-hash/json").status_code == 422
            assert client.post(f"/api/exports/publications/{next_version}/json").status_code == 405
    finally:
        app.dependency_overrides.clear()


def test_ontology_download_is_independent_and_matches_the_canonical_file():
    def unavailable_store():
        raise AssertionError("Ontology download must not access the database")

    app.dependency_overrides[operational_store] = unavailable_store
    try:
        with TestClient(app) as client:
            response = client.get("/api/exports/ontology")
            assert response.status_code == 200
            canonical = (Path(__file__).parents[2] / "ontology/motorsport.ttl").read_bytes()
            assert response.content == canonical
            assert hashlib.sha256(canonical).hexdigest() in response.headers["etag"]
            graph = Graph().parse(data=response.text, format="turtle")
            assert (MOTORSPORT.Meeting, RDF.type, OWL.Class) in graph
            assert not list(graph.subjects(RDF.type, MOTORSPORT.Meeting))
            assert response.headers["content-disposition"].startswith("attachment;")
    finally:
        app.dependency_overrides.clear()


def test_publication_download_failure_is_sanitized_and_ontology_stays_available(monkeypatch):
    def offline(*args, **kwargs):
        raise psycopg.OperationalError("Private connection details")

    monkeypatch.setattr(psycopg, "connect", offline)
    with TestClient(app, raise_server_exceptions=False) as client:
        for path in ("/api/exports", f"/api/exports/publications/{'a' * 64}/json"):
            response = client.get(path)
            assert response.status_code == 503
            assert "Private connection details" not in response.text
        assert client.get("/api/exports/ontology").status_code == 200


def test_all_formats_preserve_the_same_resources_relationships_and_provenance(isolated_services):
    store, projection = isolated_services
    candidate = vehicle_candidate()
    meeting = candidate["seasons"][0]["meetings"][0]
    meeting["meeting"]["sessions"] = [{"identity": "fixture:practice", "name": "Practice", "status": "scheduled", "start": {"local": "2026-03-06T12:30:00", "offset": "+11:00"}}]
    meeting["field_assertions"] = [{"field": "status", "value": '=HYPERLINK("https://example.test")', "source_url": meeting["source_url"], "retrieved_at": meeting["retrieved_at"], "locator": "Published status", "rule": "Private interpretation note", "preferred": True, "response_sha256": "b" * 64}]
    published = PublicationModule(store, projection).publish(parse_candidate(candidate))
    app.dependency_overrides[operational_store] = lambda: store
    try:
        with TestClient(app) as client:
            root = f"/api/exports/publications/{published.version}/"
            turtle = client.get(root + "turtle")
            json_response = client.get(root + "json")
            csv_response = client.get(root + "csv")
            assert turtle.status_code == json_response.status_code == csv_response.status_code == 200
            graph = Graph().parse(data=turtle.text, format="turtle")
            assert isomorphic(graph, Graph().parse(data=json_response.text, format="json-ld"))
            rows = list(csv.DictReader(io.StringIO(csv_response.text)))
            reconstructed = Graph()
            for row in rows:
                assert row["publicationVersion"] == published.version
                subject, predicate, value = (from_n3(row[key]) for key in ("subject", "predicate", "object"))
                assert isinstance(subject, Node) and isinstance(predicate, Node) and isinstance(value, Node)
                reconstructed.add((subject, predicate, value))
                assert not any(value.startswith(("=", "+", "-", "@", "\t", "\r", "\n")) for value in row.values())
            assert isomorphic(graph, reconstructed)
            session = URIRef("https://w3id.org/motorsport-hub/resource/session/fixture%3Apractice")
            vehicle = URIRef("https://w3id.org/motorsport-hub/resource/vehicle-model/fixture%3Agt-model")
            assert (session, MOTORSPORT.meeting, MEETING) in graph
            assert (session, MOTORSPORT.startLocal, Literal("2026-03-06T12:30:00")) in graph
            assert (None, MOTORSPORT.includesVehicle, vehicle) in graph
            assert (None, MOTORSPORT.vehicleField, Literal("category")) in graph
            assert (None, MOTORSPORT.passageText, Literal("Synthetic fixture: the winner receives 25 points when full points apply.", lang="en")) in graph
            assert (None, MOTORSPORT.responseSha256, Literal("b" * 64)) in graph
            assert (MEETING, MOTORSPORT.fieldAssertion, None) in graph
            assert all(value.language in (None, "en") for value in graph.objects() if isinstance(value, Literal))
            assert "Private interpretation note" not in turtle.text + csv_response.text + json_response.text
    finally:
        app.dependency_overrides.clear()