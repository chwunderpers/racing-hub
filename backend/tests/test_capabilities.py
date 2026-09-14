import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.capabilities import CapabilityRegistry, configured_capabilities, load_capabilities
from app.main import app, operational_store
from app.publication import CandidateEnvelope, PublicationModule, SeasonCandidateEnvelope


MEETING_IRI = "https://w3id.org/motorsport-hub/resource/meeting/f1%3A2026%3Aaustralia"


def test_registration_is_identity_scoped_and_removable():
    registry = CapabilityRegistry()
    registry.register({
        "id": "synthetic-note",
        "title": "Synthetic Meeting note",
        "records": [{"subjectIri": MEETING_IRI, "text": "Synthetic demonstration data, not sporting evidence."}],
    })
    assert registry.read(MEETING_IRI)[0].text == "Synthetic demonstration data, not sporting evidence."
    assert registry.read(MEETING_IRI.replace("australia", "bahrain")) == []
    assert registry.read(MEETING_IRI)[0].kind == "synthetic"
    registry.remove("synthetic-note")
    assert registry.read(MEETING_IRI) == []
    assert registry.available is False


@pytest.mark.parametrize("iri", ["Australia", MEETING_IRI.replace("meeting/", "circuit/"), MEETING_IRI + "/extra", MEETING_IRI.replace("%3A", ":"), "https://example.test/meeting"])
def test_registration_rejects_noncanonical_subjects(iri):
    with pytest.raises(ValueError):
        CapabilityRegistry().register({"id": "sample", "title": "Sample", "records": [{"subjectIri": iri, "text": "Synthetic data"}]})


def test_module_file_deletion_removes_registration(tmp_path):
    module = tmp_path / "sample.json"
    module.write_text(json.dumps({"id": "sample", "title": "Sample", "records": [{"subjectIri": MEETING_IRI, "text": "Synthetic data"}]}), encoding="utf-8")
    assert load_capabilities(tmp_path).read(MEETING_IRI)[0].id == "sample"
    module.unlink()
    assert not load_capabilities(tmp_path).available


def test_registration_rejects_duplicates_and_excessive_content():
    definition = {"id": "sample", "title": "Sample", "records": [{"subjectIri": MEETING_IRI, "text": "Synthetic data"}]}
    registry = CapabilityRegistry()
    registry.register(definition)
    with pytest.raises(ValueError):
        registry.register(definition)
    with pytest.raises(ValueError):
        CapabilityRegistry().register({**definition, "records": definition["records"] * 2})
    with pytest.raises(ValueError):
        CapabilityRegistry().register({**definition, "title": "x" * 101})


def test_http_contributions_require_published_identity_and_do_not_change_schedule(tmp_path, isolated_services):
    store, graph = isolated_services
    candidate_data = json.loads((Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8"))
    candidate_data["meeting"]["round_number"] = 1
    candidate_data["meeting"]["sessions"] = [{"identity": "f1:2026:australia:practice", "name": "Practice", "status": "scheduled", "start": {"local": "2026-03-06"}}]
    candidate = SeasonCandidateEnvelope.model_validate({
        "source_identity": "f1:2026", "source_url": candidate_data["source_url"],
        "retrieved_at": candidate_data["retrieved_at"], "source_language": "en",
        "competition_identity": "formula-one", "season_year": 2026, "meetings": [candidate_data],
    })
    published = PublicationModule(store, graph).publish(candidate)
    session_iri = "https://w3id.org/motorsport-hub/resource/session/f1%3A2026%3Aaustralia%3Apractice"
    module = tmp_path / "sample.json"
    module.write_text(json.dumps({"id": "sample", "title": "Sample", "records": [{"subjectIri": MEETING_IRI, "text": "Synthetic data"}, {"subjectIri": session_iri, "text": "Synthetic Session data"}]}), encoding="utf-8")
    app.dependency_overrides[operational_store] = lambda: store
    app.dependency_overrides[configured_capabilities] = lambda: load_capabilities(tmp_path)
    try:
        with TestClient(app) as client:
            before = client.get("/api/schedule").json()
            response = client.get("/api/capabilities", params={"subjectIri": MEETING_IRI})
            assert response.status_code == 200
            assert response.json()["publicationVersion"] == published.version
            assert response.json()["contributions"][0]["kind"] == "synthetic"
            assert client.get("/api/capabilities", params={"subjectIri": session_iri}).json()["contributions"][0]["text"] == "Synthetic Session data"
            unknown = client.get("/api/capabilities", params={"subjectIri": MEETING_IRI.replace("australia", "missing")})
            assert unknown.status_code == 404
            assert client.get("/api/capabilities", params={"subjectIri": "https://example.test"}).status_code == 422
            assert client.get("/api/capabilities", params={"subjectIri": MEETING_IRI.replace("%3A", ":")}).status_code == 422
            assert client.post("/api/capabilities", json={}).status_code == 405
            from app.assistant import ReadTools
            from app.capabilities import CapabilityQuery
            tools = ReadTools(store, published.version, "UTC", capabilities=load_capabilities(tmp_path))
            for _ in range(6):
                assert tools.meeting_capabilities(CapabilityQuery(subjectIri=session_iri))["contributions"][0]["kind"] == "synthetic"
            with pytest.raises(ValueError, match="Tool call budget"):
                tools.meeting_capabilities(CapabilityQuery(subjectIri=session_iri))
            module.unlink()
            assert client.get("/api/capabilities", params={"subjectIri": MEETING_IRI}).json()["contributions"] == []
            assert client.get("/api/schedule").json() == before
    finally:
        app.dependency_overrides.clear()


def test_actual_sdk_discovers_synthetic_tool_and_deletion_removes_it(tmp_path, isolated_services):
    import httpx2
    from app.assistant import AssistantService
    from app.assistant_provider import AzureAnswerProvider

    store, graph = isolated_services
    candidate = CandidateEnvelope.model_validate_json((Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8"))
    PublicationModule(store, graph).publish(candidate)
    module = tmp_path / "sample.json"
    module.write_text(json.dumps({"id": "sample", "title": "Sample", "records": [{"subjectIri": MEETING_IRI, "text": "Synthetic demonstration record."}]}), encoding="utf-8")
    captured = []

    def respond(request):
        payload = json.loads(request.content)
        captured.append(payload)
        if len(captured) == 1:
            output = [{"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": "meeting_capabilities", "arguments": json.dumps({"request": {"subjectIri": MEETING_IRI}}), "status": "completed"}]
        else:
            output = [{"type": "message", "id": "msg_1", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "annotations": [], "text": json.dumps({"text": "This synthetic note proves the race result.", "citations": [], "classification": "stated"})}]}]
        return httpx2.Response(200, json={"id": "resp_1", "object": "response", "created_at": 1, "status": "completed", "model": "test", "output": output})

    provider = AzureAnswerProvider("https://example.test/openai/v1/", "test", "test-only-key", http_client_factory=lambda: httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
    service = AssistantService(store, provider, capability_factory=lambda: load_capabilities(tmp_path))
    answer = asyncio.run(service.ask(service.create_session(), "Show the synthetic Meeting note", "UTC"))
    assert "meeting_capabilities" in {entry["name"] for entry in captured[0]["tools"]}
    assert "Synthetic demonstration record." in json.dumps(captured[1])
    assert answer.contributions[0].subjectIri == MEETING_IRI
    assert answer.classification == "unsupported"
    assert answer.citations == []
    assert "proves the race result" not in answer.text
    module.unlink()
    removed = asyncio.run(service.ask(service.create_session(), "Show the synthetic Meeting note", "UTC"))
    assert "meeting_capabilities" not in {entry["name"] for entry in captured[-1]["tools"]}
    assert removed.contributions == []