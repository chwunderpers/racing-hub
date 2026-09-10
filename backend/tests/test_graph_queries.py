import pytest
import asyncio
import json
import httpx

from app.graph_queries import GraphQueryPolicy, shared_circuits_query


VERSION = "a" * 64
GRAPH = "https://w3id.org/motorsport-hub/graph/publication/" + VERSION
QUERY = f"SELECT ?meeting FROM <{GRAPH}> WHERE {{ ?meeting a <https://w3id.org/motorsport-hub/ontology/Meeting> }} LIMIT 10"


def test_shared_circuit_query_uses_canonical_identity_across_publication():
    from rdflib import Graph, Namespace, RDF, RDFS, Literal
    namespace = Namespace("https://w3id.org/motorsport-hub/resource/")
    ontology = Namespace("https://w3id.org/motorsport-hub/ontology/")
    graph = Graph(identifier=GRAPH)
    for suffix, competition, circuit in [("first", "f1", "spa"), ("second", "gt", "spa"), ("third", "nls", "different")]:
        meeting = namespace[suffix]
        graph.add((meeting, RDF.type, ontology.Meeting))
        graph.add((meeting, ontology.circuit, namespace[circuit]))
        graph.add((meeting, ontology.competition, namespace[competition]))
        graph.add((meeting, ontology.provenance, namespace["source-" + suffix]))
        graph.add((namespace[circuit], RDFS.label, Literal("Same display label", lang="en")))
        graph.add((namespace[competition], RDFS.label, Literal(competition, lang="en")))
        graph.add((namespace["source-" + suffix], ontology.sourceUrl, namespace["source-" + suffix]))
        graph.add((namespace["source-" + suffix], ontology.retrievedAt, Literal("2026-09-10")))
    query = shared_circuits_query(VERSION)
    assert GraphQueryPolicy(VERSION).validate(query).form == "SELECT"
    rows = list(graph.query(query))
    assert len(rows) == 1
    assert str(rows[0].circuit) == str(namespace.spa)
    assert {str(rows[0].nameA), str(rows[0].nameB)} == {"f1", "gt"}


def test_publication_query_policy_accepts_bounded_select():
    validated = GraphQueryPolicy(VERSION).validate(QUERY)
    assert validated.form == "SELECT"
    assert validated.limit == 10
    assert validated.query == QUERY


@pytest.mark.parametrize("query", [
    QUERY.replace("LIMIT 10", ""),
    QUERY.replace(VERSION, "b" * 64),
    QUERY.replace("?meeting a", "SERVICE <https://example.com/sparql> { ?meeting a").replace("} LIMIT", "} } LIMIT"),
    "INSERT DATA { <urn:subject> <urn:predicate> <urn:object> }",
])
def test_publication_query_policy_rejects_unsafe_queries(query):
    with pytest.raises(ValueError):
        GraphQueryPolicy(VERSION).validate(query)


@pytest.mark.parametrize("form, native", [
    ("ASK", "true"),
    ("SELECT", json.dumps('?meeting\n<https://w3id.org/motorsport-hub/resource/meeting/australia>')),
    ("CONSTRUCT", json.dumps('<https://w3id.org/motorsport-hub/resource/meeting/australia> a <https://w3id.org/motorsport-hub/ontology/Meeting> .')),
    ("DESCRIBE", json.dumps('<https://w3id.org/motorsport-hub/resource/meeting/australia> a <https://w3id.org/motorsport-hub/ontology/Meeting> .')),
])
def test_native_mcp_client_returns_typed_results(form, native):
    from app.graph_mcp import GraphMcpClient

    def respond(request):
        if request.method == "DELETE":
            return httpx.Response(200)
        if request.method == "GET":
            return httpx.Response(405)
        message = json.loads(request.content)
        if "id" not in message:
            return httpx.Response(202)
        if message["method"] == "initialize":
            result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "GraphDB", "version": "test"}}
        elif message["method"] == "tools/list":
            result = {"tools": [{"name": "sparql_query", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "repositoryId": {"type": "string"}}}}]}
        else:
            assert message["method"] == "tools/call"
            assert message["params"]["name"] == "sparql_query"
            assert message["params"]["arguments"]["repositoryId"] == "motorsport"
            result = {"content": [{"type": "text", "text": native}], "isError": False}
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": message["id"], "result": result})

    async def scenario():
        async with GraphMcpClient("http://localhost:7200/mcp", VERSION, transport=httpx.MockTransport(respond)) as client:
            query = QUERY if form == "SELECT" else QUERY.replace("SELECT ?meeting", "CONSTRUCT { ?meeting a <https://w3id.org/motorsport-hub/ontology/Meeting> }") if form == "CONSTRUCT" else QUERY.replace("SELECT ?meeting", "DESCRIBE <https://w3id.org/motorsport-hub/resource/meeting/australia>") if form == "DESCRIBE" else f"ASK FROM <{GRAPH}> {{ ?meeting a <https://w3id.org/motorsport-hub/ontology/Meeting> }}"
            answer = await client.query(query)
            if form == "ASK":
                assert answer["boolean"] is True
            elif form == "SELECT":
                assert answer["rows"][0]["meeting"]["value"].endswith("/meeting/australia")
            else:
                assert answer["triples"][0]["object"].endswith("/ontology/Meeting")
            assert answer["relationshipKind"] == ("derived" if form == "CONSTRUCT" else "asserted")
    asyncio.run(scenario())


@pytest.mark.parametrize("fragment", [
    "?subject ?predicate ?value", "?subject <https://w3id.org/motorsport-hub/ontology/evidence> ?value",
    "?subject a/<http://www.w3.org/2000/01/rdf-schema#label> ?value",
    "GRAPH ?graph { ?subject a ?value }", "SERVICE SILENT <https://example.org/> { ?subject a ?value }",
    "{ SELECT ?subject WHERE { SERVICE <https://example.org/> { ?subject a ?value } } }",
    "?subject a ?value FILTER(EXISTS { SERVICE <https://example.org/> { ?subject a ?value } })",
    "?subject a ?value FILTER(<http://example.org/function>(?subject))",
])
def test_query_policy_rejects_hidden_access_paths(fragment):
    with pytest.raises(ValueError):
        GraphQueryPolicy(VERSION).validate(f"SELECT ?subject FROM <{GRAPH}> WHERE {{ {fragment} }} LIMIT 10")


@pytest.mark.parametrize("suffix", ["; DELETE WHERE { ?subject ?predicate ?object }", " SELECT * WHERE {}", " OFFSET 1001"])
def test_query_policy_rejects_trailing_operations_and_excessive_offsets(suffix):
    with pytest.raises(ValueError):
        GraphQueryPolicy(VERSION).validate(QUERY + suffix)


def test_construct_cannot_manufacture_a_published_fact():
    query = QUERY.replace("SELECT ?meeting", 'CONSTRUCT { ?meeting <https://w3id.org/motorsport-hub/ontology/status> "completed" }')
    with pytest.raises(ValueError):
        GraphQueryPolicy(VERSION).validate(query)


@pytest.mark.parametrize("failure", ["native-error", "oversized", "compressed", "malformed", "stalled"])
def test_native_mcp_rejects_errors_and_excessive_responses(failure):
    import gzip
    import time
    from app.graph_mcp import GraphMcpClient

    async def respond(request):
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
            result = {"tools": [{"name": "sparql_query", "inputSchema": {"type": "object"}}]}
        else:
            if failure == "stalled":
                await asyncio.Event().wait()
            result = {"content": [{"type": "text", "text": "true"}], "isError": failure == "native-error"}
            if failure == "oversized":
                result["content"][0]["text"] = " " * 150000
            if failure == "malformed":
                result["content"][0]["text"] = '"not a boolean"'
        content = json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}).encode()
        headers = {"Content-Type": "application/json"}
        if failure == "compressed":
            content = gzip.compress(content)
            headers["Content-Encoding"] = "gzip"
        return httpx.Response(200, headers=headers, stream=httpx.ByteStream(content))

    async def scenario():
        client = GraphMcpClient("http://localhost:7200/mcp", VERSION, transport=httpx.MockTransport(respond))
        started = time.monotonic()
        with pytest.raises(Exception):
            await client.query(QUERY.replace("SELECT ?meeting", "ASK"))
        if failure == "stalled":
            assert 10 <= time.monotonic() - started < 16
    asyncio.run(scenario())


def test_native_queries_isolate_publication_and_private_evidence(isolated_services):
    import os
    from app.graph_config import maintenance_auth
    from app.graph_mcp import GraphMcpClient
    _, projection = isolated_services
    resource = "https://w3id.org/motorsport-hub/resource/meeting/graph-test"
    label = "http://www.w3.org/2000/01/rdf-schema#label"
    evidence = "https://w3id.org/motorsport-hub/ontology/evidence"
    for version, name in [(VERSION, "Published"), ("b" * 64, "Historical-secret")]:
        response = httpx.put(projection.repository_url + "/statements", auth=maintenance_auth(),
            params={"context": f"<https://w3id.org/motorsport-hub/graph/publication/{version}>"},
            content=f'<{resource}> <{label}> "{name}"; <{evidence}> "private-authorization" .',
            headers={"Content-Type": "text/turtle"})
        response.raise_for_status()

    async def scenario():
        client = GraphMcpClient(os.environ["TEST_GRAPHDB_URL"] + "/mcp", VERSION,
            os.environ.get("TEST_GRAPHDB_USER"), os.environ.get("TEST_GRAPHDB_PASSWORD"),
            repository=projection.repository_url.rsplit("/", 1)[1])
        pattern = f'<{resource}> <{label}> ?name'
        for form in ["SELECT ?name", "ASK", f"CONSTRUCT {{ {pattern} }}", f"DESCRIBE <{resource}>"]:
            query = f"{form} FROM <{GRAPH}> WHERE {{ {pattern} }}" + ("" if form == "ASK" else " LIMIT 10")
            result = await client.query(query)
            encoded = json.dumps(result)
            assert "Historical-secret" not in encoded
            assert "private-authorization" not in encoded
            if form == "ASK":
                assert result["boolean"] is True
            else:
                assert "Published" in encoded
            if form.startswith("CONSTRUCT"):
                assert result["relationshipKind"] == "derived"
                assert result["premiseKind"] == "asserted"
    asyncio.run(scenario())


def test_reset_closes_only_its_tabs_native_mcp_session():
    from pathlib import Path
    from app.assistant import AssistantService, AnswerDraft, GraphQuery
    from app.graph_mcp import GraphMcpClient
    from app.publication import CandidateEnvelope, InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule

    async def scenario():
        started = asyncio.Event()
        hold = asyncio.Event()
        sessions = []
        closed = []

        async def respond(request):
            session = request.headers.get("Mcp-Session-Id")
            if request.method == "DELETE":
                closed.append(session)
                return httpx.Response(200)
            if request.method == "GET":
                return httpx.Response(405)
            message = json.loads(request.content)
            if "id" not in message:
                return httpx.Response(202)
            if message["method"] == "initialize":
                session = "test-session-" + str(len(sessions) + 1)
                sessions.append(session)
                result = {"protocolVersion": "2025-03-26", "capabilities": {"tools": {}}, "serverInfo": {"name": "GraphDB", "version": "test"}}
            elif message["method"] == "tools/list":
                result = {"tools": [{"name": "sparql_query", "inputSchema": {"type": "object"}}]}
            else:
                if session == "test-session-1":
                    started.set()
                    await hold.wait()
                result = {"content": [{"type": "text", "text": "true"}], "isError": False}
            return httpx.Response(200, headers={"Mcp-Session-Id": session}, json={"jsonrpc": "2.0", "id": message["id"], "result": result})

        class GraphModel:
            async def answer(self, history, question, tools):
                assert history == []
                result = await tools.graph_query(GraphQuery(query=QUERY.replace(VERSION, tools.version).replace("SELECT ?meeting", "ASK")))
                assert result["boolean"] is True
                return AnswerDraft(text="No source requested.", citations=[])

        store = InMemoryOperationalStore()
        candidate = CandidateEnvelope.model_validate_json((Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8"))
        PublicationModule(store, InMemoryGraphProjection()).publish(candidate)
        factory = lambda version: GraphMcpClient("http://localhost:7200/mcp", version, transport=httpx.MockTransport(respond))
        service = AssistantService(store, GraphModel(), graph_factory=factory)
        first, second = service.create_session(), service.create_session()
        pending = asyncio.create_task(service.ask(first, "First tab", "UTC"))
        await asyncio.wait_for(started.wait(), 3)
        await service.ask(second, "Second tab", "UTC")
        service.reset(first)
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert sessions == ["test-session-1", "test-session-2"]
        assert set(closed) == set(sessions)
    asyncio.run(scenario())