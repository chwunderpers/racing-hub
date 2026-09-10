import asyncio
import json
from contextlib import AsyncExitStack
from datetime import timedelta
from io import StringIO
from urllib.parse import urlsplit

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from rdflib import Graph
from rdflib.query import Result

from app.graph_queries import GraphQueryPolicy, PUBLIC_PREDICATES


GRAPH_CONCURRENCY = asyncio.Semaphore(2)


class BoundedStream(httpx.AsyncByteStream):
    def __init__(self, stream):
        self.stream = stream

    async def __aiter__(self):
        size = 0
        async for chunk in self.stream:
            size += len(chunk)
            if size > 128000:
                raise ValueError("Graph response exceeds byte budget")
            yield chunk

    async def aclose(self):
        await self.stream.aclose()


class BoundedTransport(httpx.AsyncBaseTransport):
    def __init__(self, transport=None):
        self.transport = transport or httpx.AsyncHTTPTransport()

    async def handle_async_request(self, request):
        response = await self.transport.handle_async_request(request)
        if response.headers.get("Content-Encoding", "identity").lower() != "identity":
            await response.aclose()
            raise ValueError("Compressed MCP responses are not permitted")
        response.stream = BoundedStream(response.stream)
        return response

    async def aclose(self):
        await self.transport.aclose()


class GraphMcpClient:
    def __init__(self, endpoint, version, username=None, password=None, repository="motorsport", transport=None):
        parsed = urlsplit(endpoint)
        if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path != "/mcp":
            raise ValueError("Invalid native MCP endpoint")
        if parsed.scheme != "https" and not (parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "graphdb"}):
            raise ValueError("MCP requires HTTPS or the local GraphDB service")
        self.endpoint = endpoint
        self.policy = GraphQueryPolicy(version)
        self.version = version
        self.repository = repository
        self.auth = httpx.BasicAuth(username, password) if username and password else None
        self.transport = transport
        self.stack = AsyncExitStack()
        self.session = None

    async def __aenter__(self):
        return self

    async def _connect(self):
        def factory(headers=None, timeout=None, auth=None):
            return httpx.AsyncClient(headers={**(headers or {}), "Accept-Encoding": "identity"}, timeout=timeout,
                                     auth=auth, follow_redirects=False, transport=BoundedTransport(self.transport))
        try:
            streams = await self.stack.enter_async_context(streamablehttp_client(self.endpoint, auth=self.auth, timeout=12,
                sse_read_timeout=12, httpx_client_factory=factory))
            self.session = await self.stack.enter_async_context(ClientSession(streams[0], streams[1], read_timeout_seconds=timedelta(seconds=12)))
            await self.session.initialize()
            tools = await self.session.list_tools()
            if not any(tool.name == "sparql_query" for tool in tools.tools):
                raise RuntimeError("Native SPARQL tool unavailable")
        except BaseException:
            await self.stack.aclose()
            self.session = None
            raise

    async def __aexit__(self, exc_type, exc, traceback):
        await self.stack.aclose()
        self.session = None

    async def query(self, query):
        async with asyncio.timeout(15):
            async with GRAPH_CONCURRENCY:
                try:
                    return await self._query(query)
                finally:
                    await self.stack.aclose()
                    self.session = None

    async def _query(self, query):
        validated = self.policy.validate(query)
        if self.session is None:
            await self._connect()
        response = await self.session.call_tool("sparql_query", {"repositoryId": self.repository,
            "query": validated.query, "addMissingNamespaces": False}, read_timeout_seconds=timedelta(seconds=12))
        if response.isError or any(content.type != "text" for content in response.content):
            raise RuntimeError("Native graph query failed")
        text = "\n".join(content.text for content in response.content)
        if len(text.encode("utf-8")) > 90000:
            raise ValueError("Graph result exceeds byte budget")
        result = {"form": validated.form, "publicationVersion": self.version,
              "relationshipKind": "derived" if validated.form == "CONSTRUCT" else "asserted",
              "premiseKind": "asserted", "inference": "Unavailable: global inferred facts are not publication-isolated"}
        if validated.form == "ASK":
            value = json.loads(text)
            if not isinstance(value, bool):
                raise ValueError("Malformed ASK result")
            return result | {"boolean": value}
        if validated.form == "SELECT":
            value = json.loads(text)
            if not isinstance(value, str):
                raise ValueError("Malformed native SELECT result")
            parsed = Result.parse(source=StringIO(value + "\n"), format="tsv")
            rows = json.loads(parsed.serialize(format="json"))["results"]["bindings"]
            if len(rows) > validated.limit:
                raise ValueError("Graph row budget exceeded")
            return result | {"rows": rows, "limited": len(rows) == validated.limit}
        value = json.loads(text)
        if not isinstance(value, str):
            raise ValueError("Malformed native graph result")
        graph = Graph().parse(data=value, format="turtle")
        if len(graph) > 300:
            raise ValueError("Graph triple budget exceeded")
        triples = [{"subject": str(subject), "predicate": str(predicate), "object": str(value)}
                   for subject, predicate, value in sorted(graph, key=lambda triple: tuple(map(str, triple))) if predicate in PUBLIC_PREDICATES]
        return result | {"triples": triples, "publicPredicatesOnly": True}