import copy
import hashlib
import json

import pytest

from app.publication import InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule, merge_season, parse_candidate
from app.review import ReviewService
from backend.tests.test_regulations import regulation_candidate


def vehicle_candidate():
    candidate = regulation_candidate()
    source = {
        "url": "https://example.test/manufacturer/model", "publisher": "Fixture manufacturer",
        "kind": "authoritative", "retrieved_at": "2026-09-14T08:00:00Z",
        "sha256": "a" * 64, "anchor": "Model overview", "language": "en",
    }
    def assertion(value):
        return {"value": value, "applicability": "Synthetic model variant, not a homologated configuration",
                "source": copy.deepcopy(source)}
    candidate["vehicles"] = [{
        "identity": "fixture:gt-model", "language": "en",
        "fields": {"manufacturer": [assertion("Fixture manufacturer")],
                   "model_name": [assertion("Fixture GT Model")],
                   "category": [assertion("GT racing car")]},
    }]
    return candidate


def test_private_preview_includes_sparse_vehicle_with_field_evidence(tmp_path):
    candidate = vehicle_candidate()
    store = InMemoryOperationalStore()
    review = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    baseline = review.preview({key: value for key, value in candidate.items() if key != "vehicles"})
    item = review.preview(candidate)
    assert item["preview"]["validationErrors"] == []
    assert item["candidate"]["seasons"] == baseline["candidate"]["seasons"]
    assert item["candidate"]["vehicles"][0]["fields"]["model_name"][0]["value"] == "Fixture GT Model"
    assert "power" not in item["candidate"]["vehicles"][0]["fields"]
    assert "vehicles/fixture:gt-model" in item["preview"]["changes"]


def test_vehicle_evidence_requires_separate_exact_review_confirmation(tmp_path):
    store = InMemoryOperationalStore()
    review = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    item = review.preview(vehicle_candidate())
    proposal = review.propose_decision(item["id"], "accepted", "Test reviewer", "Fixture approval",
        ["https://example.test/manufacturer/model"],
        regulation_confirmations=item["preview"]["regulationConfirmations"])
    review.record_decision(item["id"], proposal["confirmation"])
    with pytest.raises(ValueError, match="vehicle evidence"):
        review.propose_publication(item["id"])
    assert store.current_publication_version() is None


def test_schedule_merge_retains_published_vehicle_descriptions():
    previous = parse_candidate(vehicle_candidate())
    updated = merge_season(previous, previous.seasons[0])
    assert updated.model_dump(mode="json")["vehicles"] == previous.model_dump(mode="json")["vehicles"]


def test_pending_curated_inventory_is_sparse_and_strictly_sourced():
    from pathlib import Path
    from app.vehicle_ingestion import VehicleInventory

    inventory = VehicleInventory.model_validate_json((Path(__file__).parents[2] / "examples/vehicle-inventory.json").read_text("utf-8"))
    assert len(inventory.vehicles) == 3
    assert sum(len(vehicle.fields) for vehicle in inventory.vehicles) == 11
    assert all(set(vehicle.fields).issubset({"manufacturer", "model_name", "category", "generation", "variant"}) for vehicle in inventory.vehicles)
    assert all(assertion.source.kind == "authoritative" for vehicle in inventory.vehicles for assertions in vehicle.fields.values() for assertion in assertions)


def test_authoritative_conflicts_remain_unresolved_in_preview(tmp_path):
    candidate = vehicle_candidate()
    alternative = copy.deepcopy(candidate["vehicles"][0]["fields"]["category"][0])
    alternative.update(value="Different authoritative category")
    candidate["vehicles"][0]["fields"]["category"].append(alternative)
    store = InMemoryOperationalStore()
    receipt = publish_vehicle(ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection())), candidate)
    from app.stores import GraphDbProjection
    from app.vehicle_projection import vehicle_projection, vehicle_iri

    graph = GraphDbProjection.build_graph(receipt["version"], store.publication_envelope(receipt["version"]))
    category = next(field for field in vehicle_projection(graph, vehicle_iri("fixture:gt-model"))["fields"] if field["field"] == "category")
    assert category["value"] is None
    assert category["conflict"] is True


def publish_vehicle(review, candidate):
    item = review.preview(candidate)
    assert not item["preview"]["validationErrors"]
    proposal = review.propose_decision(item["id"], "accepted", "Private test reviewer", "Private vehicle approval",
        ["https://example.test/manufacturer/model"],
        regulation_confirmations=item["preview"]["regulationConfirmations"],
        vehicle_confirmations=item["preview"]["vehicleConfirmations"])
    review.record_decision(item["id"], proposal["confirmation"])
    publication = review.propose_publication(item["id"])
    return review.publish(item["id"], publication["confirmation"])


def test_published_vehicle_details_preserve_secondary_conflict_and_prefer_authority(isolated_services, tmp_path):
    store, graph = isolated_services
    candidate = vehicle_candidate()
    secondary = copy.deepcopy(candidate["vehicles"][0]["fields"]["category"][0])
    secondary.update(value="Conflicting secondary category")
    secondary["source"].update(kind="secondary", url="https://en.wikipedia.org/wiki/Fixture", retrieved_at="2026-09-15T08:00:00Z")
    candidate["vehicles"][0]["fields"]["category"].append(secondary)
    receipt = publish_vehicle(ReviewService(tmp_path, store, PublicationModule(store, graph)), candidate)
    reader = store.assistant_reader()
    document = reader.lookup_document("https://w3id.org/motorsport-hub/resource/vehicle-model/fixture%3Agt-model", receipt["version"])
    assert document is not None
    details = document["vehicleSpecification"]
    category = next(field for field in details["fields"] if field["field"] == "category")
    assert category["value"] == "GT racing car"
    assert category["conflict"] is True
    assert {assertion["evidenceKind"] for assertion in category["assertions"]} == {"authoritative", "secondary"}
    assert details["eligibilityEstablished"] is False
    assert "Private test reviewer" not in str(document)
    assert len(reader.visible_meetings(receipt["version"])) == 1
    assert reader.search_documents("Fixture GT Model", receipt["version"])
    assert graph.agrees(receipt["version"], "", store.publication_envelope(receipt["version"]))


@pytest.mark.parametrize("change", ["eligibility", "empty", "secondary-authority", "non-english"])
def test_private_vehicle_candidate_rejects_invalid_or_eligibility_claims(tmp_path, change):
    candidate = vehicle_candidate()
    vehicle = candidate["vehicles"][0]
    if change == "eligibility":
        vehicle["fields"]["competition_eligibility"] = vehicle["fields"]["category"]
    elif change == "empty":
        vehicle["fields"]["power"] = []
    elif change == "secondary-authority":
        vehicle["fields"]["category"][0]["source"]["url"] = "https://en.wikipedia.org/wiki/Test"
    else:
        vehicle["fields"]["model_name"][0]["source"]["language"] = "de"
    store = InMemoryOperationalStore()
    review = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    if change == "non-english":
        with pytest.raises(ValueError, match="English vehicle"):
            review.preview(candidate)
    else:
        assert review.preview(candidate)["preview"]["validationErrors"]


def test_vehicle_details_http_uses_published_projection_without_schedule_filters(isolated_services, tmp_path):
    from fastapi.testclient import TestClient
    from app.main import app, operational_store

    store, graph = isolated_services
    receipt = publish_vehicle(ReviewService(tmp_path, store, PublicationModule(store, graph)), vehicle_candidate())
    app.dependency_overrides[operational_store] = lambda: store
    try:
        with TestClient(app) as client:
            response = client.get("/api/vehicles/fixture:gt-model")
            assert response.status_code == 200
            details = response.json()
            assert details["publicationVersion"] == receipt["version"]
            assert details["vehicle"]["title"] == "Fixture GT Model"
            assert details["vehicle"]["eligibilityEstablished"] is False
            listing = client.get("/api/vehicles").json()
            assert [vehicle["title"] for vehicle in listing["vehicles"]] == ["Fixture GT Model"]
            assert client.get("/api/vehicles/missing").status_code == 404
            schedule = client.get("/api/schedule").json()
            assert len(schedule["meetings"]) == 1
            assert "vehicles" not in schedule
            assert "Private vehicle approval" not in response.text
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("case", ["valid", "drift", "redirect", "unapproved-host"])
def test_private_vehicle_collection_verifies_sources_and_preserves_snapshot(tmp_path, case):
    import httpx
    from app.vehicle_ingestion import prepare_candidate

    store = InMemoryOperationalStore()
    review = ReviewService(tmp_path / "reviews", store, PublicationModule(store, InMemoryGraphProjection()))
    publish_vehicle(review, vehicle_candidate())
    baseline = store.publication_envelope(store.current_publication_version())
    vehicle = copy.deepcopy(vehicle_candidate()["vehicles"][0])
    vehicle["identity"] = "fixture:second-model"
    body = b"<html lang='en'>Synthetic manufacturer vehicle evidence</html>"
    for assertions in vehicle["fields"].values():
        for assertion in assertions:
            assertion["source"].update(url="https://unapproved.test/model" if case == "unapproved-host" else "https://www.bmw-m.com/model",
                                       sha256=hashlib.sha256(body).hexdigest())
    path = tmp_path / "inventory.json"
    path.write_text(json.dumps({"vehicles": [vehicle]}), encoding="utf-8")
    calls = []

    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(302 if case == "redirect" else 200, headers={"content-type": "text/html"},
                              stream=httpx.ByteStream(b"changed" if case == "drift" else body))

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        if case == "valid":
            candidate = prepare_candidate(path, store, client)
            assert candidate.seasons == baseline.seasons
            assert candidate.regulations == baseline.regulations
            assert {vehicle.identity for vehicle in candidate.vehicles} == {"fixture:gt-model", "fixture:second-model"}
            assert len(calls) == 1
        else:
            with pytest.raises((ValueError, httpx.HTTPError)):
                prepare_candidate(path, store, client)
            if case == "unapproved-host":
                assert not calls
    assert store.publication_envelope(store.current_publication_version()) == baseline


@pytest.mark.parametrize("intent", ["description", "eligibility", "fabricated", "misrouted", "lookup", "discovery"])
def test_vehicle_assistant_sdk_has_field_citations_and_cannot_establish_eligibility(tmp_path, isolated_services, intent):
    import asyncio
    import httpx2
    from app.assistant import AssistantService
    from app.assistant_provider import AzureAnswerProvider

    store, graph = isolated_services
    candidate = vehicle_candidate()
    secondary = copy.deepcopy(candidate["vehicles"][0]["fields"]["category"][0])
    secondary["source"].update(kind="secondary", url="https://en.wikipedia.org/wiki/Fixture")
    candidate["vehicles"][0]["fields"]["category"].append(secondary)
    publish_vehicle(ReviewService(tmp_path, store, PublicationModule(store, graph)), candidate)
    captured = []

    def respond(request):
        payload = json.loads(request.content)
        captured.append(payload)
        outputs = [entry for entry in payload["input"] if entry.get("type") == "function_call_output"]
        if not outputs:
            assert "vehicle_specification" in [tool["name"] for tool in payload["tools"]]
            output = {"type": "function_call", "id": "fc_vehicle", "call_id": "call_vehicle", "name": "vehicle_specification",
                      "arguments": json.dumps({"request": {"identity": "fixture:gt-model", "intent": "eligibility" if intent == "eligibility" else "description"}})}
            if intent == "lookup":
                output.update(name="lookup_iri", arguments=json.dumps({"request": {"iri": "https://w3id.org/motorsport-hub/resource/vehicle-model/fixture%3Agt-model"}}))
            elif intent == "discovery":
                output.update(name="search_documentation", call_id="call_search", arguments=json.dumps({"request": {"query": "Fixture GT Model"}}))
        else:
            result = json.loads(outputs[-1]["output"])
            if outputs[-1]["call_id"] == "call_search":
                document = next(entry for entry in result["documents"] if "vehicleIdentity" in entry)
                assert document["citations"]
                return httpx2.Response(200, json={"id": "resp_discovered", "object": "response", "created_at": 1,
                    "status": "completed", "model": "test", "output": [{"type": "function_call", "id": "fc_discovered", "call_id": "call_discovered", "name": "vehicle_specification",
                    "arguments": json.dumps({"request": {"identity": document["vehicleIdentity"], "intent": "description"}})}]})
            if intent == "eligibility":
                assert result["status"] == "insufficient-evidence"
                draft = {"text": "Specifications cannot establish Competition Eligibility.", "citations": [], "classification": "unsupported"}
            else:
                if intent == "lookup":
                    result = result["document"]
                assert result["vehicle"]["eligibilityEstablished"] is False
                category = next(field for field in result["vehicle"]["fields"] if field["field"] == "category")
                assert {entry["evidenceKind"] for entry in category["assertions"]} == {"authoritative", "secondary"}
                citations = [entry["citation"] for entry in category["assertions"]]
                draft = {"text": "The source describes a GT racing car; secondary evidence is descriptive only.",
                         "citations": ["citation-999"] if intent == "fabricated" else citations, "classification": "stated"}
                if intent in {"misrouted", "lookup"}:
                    draft["text"] = "This car is eligible for NLS based on its GT3 category."
            output = {"type": "message", "id": "msg_vehicle", "role": "assistant", "status": "completed",
                      "content": [{"type": "output_text", "annotations": [], "text": json.dumps(draft)}]}
        return httpx2.Response(200, json={"id": "resp_vehicle", "object": "response", "created_at": 1,
            "status": "completed", "model": "test", "output": [output]})

    provider = AzureAnswerProvider("https://example.test/openai/v1/", "test", "test-only-key",
        http_client_factory=lambda: httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
    service = AssistantService(store, provider)
    answer = asyncio.run(service.ask(service.create_session(), "Describe the fixture vehicle" if intent != "eligibility" else "Is it eligible for NLS?", "UTC"))
    assert answer.classification == ("unsupported" if intent in {"eligibility", "fabricated"} else "stated")
    assert bool(answer.citations) == (intent not in {"eligibility", "fabricated"})
    assert "This car is eligible" not in answer.text
    if intent not in {"eligibility", "fabricated"}:
        assert "cannot establish Competition Eligibility" in answer.text
        assert "GT racing car" in answer.text
    assert "Private test reviewer" not in json.dumps(captured)
    assert "Private vehicle approval" not in json.dumps(captured)
    if answer.citations:
        assert all("/assertion/" in citation.iri for citation in answer.citations)