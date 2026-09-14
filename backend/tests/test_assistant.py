import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.assistant import AssistantService, AnswerDraft, ReadTools, ScheduleQuery
from app.main import app, assistant_service
from app.publication import CandidateEnvelope, InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule


class ScheduleModel:
    async def answer(self, history, question, tools):
        result = tools.schedule(ScheduleQuery(name="Australian"))
        return AnswerDraft(text="The Australian Meeting is scheduled for 6-8 March 2026.", citations=[result["meetings"][0]["citation"]])


def test_assistant_answers_from_typed_schedule_with_citation_and_zone():
    store = InMemoryOperationalStore()
    candidate = CandidateEnvelope.model_validate_json(
        (Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8")
    )
    published = PublicationModule(store, InMemoryGraphProjection()).publish(candidate)
    service = AssistantService(store, ScheduleModel())
    session = service.create_session()
    answer = asyncio.run(service.ask(session, "When is the Australian Meeting?", "Europe/Berlin"))
    assert answer.displayTimeZone == "Europe/Berlin"
    assert answer.publicationVersion == published.version
    assert answer.citations[0].sourceUrl == candidate.source_url
    assert answer.citations[0].iri == "https://w3id.org/motorsport-hub/resource/meeting/f1%3A2026%3Aaustralia"
    assert answer.freshness.stale is True


def test_sessions_are_isolated_ephemeral_and_expire():
    histories = []

    class UnverifiedModel:
        async def answer(self, history, question, tools):
            histories.append(history)
            return AnswerDraft(text="An unverified claim.", citations=[])

    now = [0.0]
    service = AssistantService(InMemoryOperationalStore(), UnverifiedModel(), clock=lambda: now[0])
    first, second = service.create_session(), service.create_session()
    assert first != second
    answer = asyncio.run(service.ask(first, "My first question", "UTC"))
    assert answer.classification == "unsupported"
    assert "unverified claim" not in answer.text
    asyncio.run(service.ask(second, "Separate tab", "UTC"))
    assert histories == [[], []]
    service.reset(first)
    with pytest.raises(LookupError):
        asyncio.run(service.ask(first, "Restore", "UTC"))
    now[0] = 1801
    with pytest.raises(LookupError):
        asyncio.run(service.ask(second, "Expired", "UTC"))


@pytest.mark.parametrize("payload", [{"sql": "DROP TABLE meetings"}, {"limit": 1000}, {"from_date": "2026-10-01", "through_date": "2026-01-01"}])
def test_schedule_tool_rejects_untyped_or_unbounded_requests(payload):
    with pytest.raises(ValueError):
        ScheduleQuery.model_validate(payload)


def test_assistant_does_not_accept_fabricated_citations():
    class FabricatingModel:
        async def answer(self, history, question, tools):
            return AnswerDraft(text="A claim with a fabricated source.", citations=["citation-999"])

    service = AssistantService(InMemoryOperationalStore(), FabricatingModel())
    answer = asyncio.run(service.ask(service.create_session(), "What happened?", "UTC"))
    assert answer.citations == []
    assert answer.classification == "unsupported"


def test_http_sessions_require_capability_and_reject_foreign_origins():
    service = AssistantService(InMemoryOperationalStore(), None)
    app.dependency_overrides[assistant_service] = lambda: service
    try:
        with TestClient(app) as client:
            assert client.post("/api/assistant/sessions", headers={"Origin": "https://evil.example"}).status_code == 403
            response = client.post("/api/assistant/sessions")
            assert response.status_code == 200
            token = response.json()["sessionToken"]
            assert response.headers["cache-control"] == "no-store"
            assert client.post("/api/assistant/messages", json={"message": "Hello", "displayTimeZone": "UTC"}).status_code == 422
            response = client.post("/api/assistant/messages", headers={"X-Assistant-Session": token}, json={"message": "Hello", "displayTimeZone": "UTC"})
            assert response.status_code == 503
            assert response.json()["detail"] == "Assistant temporarily unavailable"
            assert client.delete("/api/assistant/session", headers={"X-Assistant-Session": token}).status_code == 204
    finally:
        app.dependency_overrides.clear()


def test_reset_cancels_active_turn_and_parallel_turn_is_rejected():
    async def scenario():
        entered = asyncio.Event()
        hold = asyncio.Event()

        class SlowModel:
            async def answer(self, history, question, tools):
                entered.set()
                await hold.wait()
                return AnswerDraft(text="No evidence", citations=[])

        service = AssistantService(InMemoryOperationalStore(), SlowModel())
        token = service.create_session()
        pending = asyncio.create_task(service.ask(token, "First", "UTC"))
        await entered.wait()
        with pytest.raises(ValueError, match="already in progress"):
            await service.ask(token, "Second", "UTC")
        service.reset(token)
        with pytest.raises(asyncio.CancelledError):
            await pending
        with pytest.raises(LookupError):
            await service.ask(token, "Restored", "UTC")
    asyncio.run(scenario())


def test_responses_provider_uses_typed_tools_without_remote_history():
    import json
    import httpx2
    from app.assistant_provider import AzureAnswerProvider
    captured = []

    def respond(request):
        payload = json.loads(request.content)
        captured.append(payload)
        if len(captured) == 1:
            output = [{"type": "function_call", "id": "fc_1", "call_id": "call_1", "name": "schedule", "arguments": json.dumps({"request": {"name": "Australian"}}), "status": "completed"}]
        else:
            output = [{"type": "message", "id": "msg_1", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "annotations": [], "text": json.dumps({"text": "Australian Meeting: 6-8 March 2026.", "citations": ["citation-1"], "classification": "stated"})}]}]
        return httpx2.Response(200, json={"id": "resp_1", "object": "response", "created_at": 1, "status": "completed", "model": "test", "output": output})

    store = InMemoryOperationalStore()
    candidate = CandidateEnvelope.model_validate_json((Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8"))
    PublicationModule(store, InMemoryGraphProjection()).publish(candidate)
    provider = AzureAnswerProvider("https://example.test/openai/v1/", "test", "test-only-key", http_client_factory=lambda: httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
    service = AssistantService(store, provider)
    answer = asyncio.run(service.ask(service.create_session(), "When is Australia?", "UTC"))
    assert answer.citations[0].sourceUrl == candidate.source_url
    assert len(captured) == 2
    for payload in captured:
        assert payload["store"] is False
        assert "conversation" not in payload
        assert "previous_response_id" not in payload
        assert "test-only-key" not in json.dumps(payload)
        assert {tool["name"] for tool in payload["tools"]} == {"schedule", "search_documentation", "lookup_iri", "competition_regulations", "compare_regulations", "vehicle_specification"}


def test_nls_tools_preserve_abandonment_unknown_ends_and_unresolved_clocks():
    from app.nls import adapt_season, reviewed_source
    store = InMemoryOperationalStore()
    published = PublicationModule(store, InMemoryGraphProjection()).publish(adapt_season(reviewed_source()))
    tools = ReadTools(store, published.version, "America/New_York")
    result = tools.schedule(ScheduleQuery(name="Qualifiers"))
    meeting = result["meetings"][0]
    assert meeting["rounds"][0]["status"] == "abandoned"
    assert len(meeting["sessions"]) == 5
    assert sum(session["end"] is None for session in meeting["sessions"]) == 3
    assert all(session["start"]["display"] is None for session in meeting["sessions"])
    assert result["coverage"][0]["state"] == "incomplete"
    assert "fieldAssertions" not in meeting
    assert "translationReviewer" not in str(result)


def test_provider_shared_circuit_answer_has_sources_iris_and_asserted_premises():
    import json
    import httpx
    import httpx2
    from app.assistant_provider import AzureAnswerProvider
    from app.graph_mcp import GraphMcpClient
    circuit = "https://w3id.org/motorsport-hub/resource/circuit/spa"
    captured = []

    def graph_response(request):
        if request.method == "GET":
            return httpx.Response(405)
        if request.method == "DELETE":
            return httpx.Response(200)
        message = json.loads(request.content)
        if "id" not in message:
            return httpx.Response(202)
        if message["method"] == "initialize":
            result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "GraphDB", "version": "test"}}
        elif message["method"] == "tools/list":
            result = {"tools": [{"name": "sparql_query", "inputSchema": {"type": "object"}}, {"name": "unsafe_remote_tool", "inputSchema": {"type": "object"}}]}
        else:
            assert message["params"]["name"] == "sparql_query"
            assert "SELECT DISTINCT" in message["params"]["arguments"]["query"]
            columns = "?circuit\t?circuitName\t?competitionA\t?nameA\t?competitionB\t?nameB\t?sourceA\t?retrievedA\t?sourceB\t?retrievedB"
            row = f'<{circuit}>\t"Spa"@en\t<https://w3id.org/motorsport-hub/resource/competition/f1>\t"F1"@en\t<https://w3id.org/motorsport-hub/resource/competition/gt>\t"GT"@en\t<https://example.org/f1>\t"2026-09-10"\t<https://example.org/gt>\t"2026-09-10"'
            result = {"content": [{"type": "text", "text": json.dumps(columns + "\n" + row)}], "isError": False}
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": message["id"], "result": result})

    def azure_response(request):
        payload = json.loads(request.content)
        captured.append(payload)
        if len(captured) == 1:
            output = [{"type": "function_call", "id": "fc_graph", "call_id": "call_graph", "name": "graph_shared_circuits", "arguments": "{}", "status": "completed"}]
        else:
            results = [item for item in payload["input"] if item.get("type") == "function_call_output"]
            result = json.loads(results[0]["output"])
            assert result["relationshipKind"] == "derived"
            assert result["premiseKind"] == "asserted"
            assert result["circuits"][0]["iri"] == circuit
            assert result["limited"] is False
            output = [{"type": "message", "id": "msg_graph", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "annotations": [], "text": json.dumps({"text": "F1 and GT share Spa: " + circuit + ". This is derived from asserted Meeting links, not an inferred relationship.", "citations": ["citation-1", "citation-2"], "classification": "derived"})}]}]
        return httpx2.Response(200, json={"id": "resp_graph", "object": "response", "created_at": 1, "status": "completed", "model": "test", "output": output})

    store = InMemoryOperationalStore()
    candidate = CandidateEnvelope.model_validate_json((Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8"))
    PublicationModule(store, InMemoryGraphProjection()).publish(candidate)
    provider = AzureAnswerProvider("https://example.test/openai/v1/", "test", "test-only-key", http_client_factory=lambda: httpx2.AsyncClient(transport=httpx2.MockTransport(azure_response)))
    factory = lambda version: GraphMcpClient("http://localhost:7200/mcp", version, "test-user", "server-only-password", transport=httpx.MockTransport(graph_response))
    service = AssistantService(store, provider, graph_factory=factory)
    answer = asyncio.run(service.ask(service.create_session(), "Which competitions share circuits?", "UTC"))
    assert answer.classification == "derived"
    assert circuit in answer.text
    assert {citation.sourceUrl for citation in answer.citations} == {"https://example.org/f1", "https://example.org/gt"}
    for payload in captured:
        assert {tool["name"] for tool in payload["tools"]} == {"schedule", "search_documentation", "lookup_iri", "competition_regulations", "compare_regulations", "vehicle_specification", "graph_shared_circuits", "graph_query"}
        assert "server-only-password" not in json.dumps(payload)
        assert payload["store"] is False