import asyncio
import json
import secrets
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal, Protocol
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.publication import coverage_view
from app.freshness import FreshnessResponse


class ScheduleQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(default="", max_length=120)
    competition: str = Field(default="", max_length=100)
    from_date: date | None = None
    through_date: date | None = None
    limit: int = Field(default=10, ge=1, le=10)

    @model_validator(mode="after")
    def ordered_dates(self):
        if self.from_date and self.through_date and self.from_date > self.through_date:
            raise ValueError("Date range is reversed")
        return self


class SearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=200)
    limit: int = Field(default=5, ge=1, le=10)


class IriQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    iri: str = Field(min_length=1, max_length=600, pattern=r"^https://w3id\.org/motorsport-hub/resource/")


class GraphQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=1, max_length=12000)


class Citation(BaseModel):
    id: str
    iri: str
    title: str
    sourceUrl: str
    retrievedAt: str | None


class AnswerDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=6000)
    citations: list[str] = Field(max_length=12)
    classification: Literal["stated", "derived", "unsupported"] = "stated"


class AssistantAnswer(BaseModel):
    text: str
    citations: list[Citation]
    classification: Literal["stated", "derived", "unsupported"]
    displayTimeZone: str
    publicationVersion: str | None
    freshness: FreshnessResponse


class ReadTools:
    def __init__(self, store, version: str | None, zone: str, graph=None):
        self.store = store
        self.version = version
        self.zone = zone
        self.graph = graph
        self.citations: dict[str, Citation] = {}
        self.calls = 0
        self.bytes = 0

    def _bounded(self, value: dict) -> dict:
        self.bytes += len(json.dumps(value, default=str).encode("utf-8"))
        if self.bytes > 90000:
            raise ValueError("Tool result budget exceeded")
        return value

    def _begin(self):
        self.calls += 1
        if self.calls > 6:
            raise ValueError("Tool call budget exceeded")

    def _cite(self, iri, title, source, retrieved):
        identity = "citation-" + str(len(self.citations) + 1)
        self.citations[identity] = Citation(id=identity, iri=iri, title=title, sourceUrl=source, retrievedAt=retrieved)
        return identity

    def schedule(self, request: ScheduleQuery) -> dict:
        self._begin()
        meetings = []
        truncated = False
        candidates = self.store.visible_meetings(version=self.version) if self.version else []
        for meeting in candidates:
            if request.name.casefold() not in meeting["name"].casefold():
                continue
            if request.competition and request.competition.casefold() not in {meeting["competition"].casefold(), meeting["competitionId"].casefold()}:
                continue
            if request.from_date and meeting["endDate"] < request.from_date.isoformat():
                continue
            if request.through_date and meeting["startDate"] > request.through_date.isoformat():
                continue
            if len(meetings) >= request.limit:
                truncated = True
                break
            fields = ("id", "name", "competition", "competitionId", "season", "circuit", "startDate", "endDate", "status", "round", "rounds", "kind", "coverage")
            value = {key: meeting[key] for key in fields if key in meeting}
            value["sessions"] = []
            for session in meeting.get("sessions", []):
                entry = {key: session[key] for key in ("id", "name", "status", "durationMinutes", "roundId") if key in session}
                for key in ("start", "end"):
                    clock = session.get(key)
                    entry[key] = None if not clock else {**clock, "display": datetime.fromisoformat(clock["instant"]).astimezone(ZoneInfo(self.zone)).isoformat() if clock.get("instant") else None}
                value["sessions"].append(entry)
            iri = "https://w3id.org/motorsport-hub/resource/meeting/" + quote(meeting["id"].removeprefix("meeting:"), safe="")
            value["citation"] = self._cite(iri, meeting["name"], meeting["sourceUrl"], meeting["retrievedAt"])
            value["assertions"] = []
            for assertion in meeting.get("publicAssertions", meeting.get("fieldAssertions", [])):
                public = {key: assertion.get(key) for key in ("field", "value", "subject_identity", "effective_local", "preferred")}
                public["citation"] = self._cite(iri, meeting["name"] + ": " + assertion["field"], assertion["source_url"], assertion["retrieved_at"])
                value["assertions"].append(public)
            meetings.append(value)
        return self._bounded({"meetings": meetings[:request.limit], "truncated": truncated, "displayTimeZone": self.zone,
                              "coverage": (self.store.coverage(self.version) if hasattr(self.store, "coverage") else coverage_view(self.store.publication_envelope(self.version))) if self.version else []})

    def search(self, request: SearchQuery) -> dict:
        self._begin()
        records = self.store.search_documents(request.query, self.version, request.limit) if self.version else []
        return self._bounded({"documents": [self._document(record) for record in records], "limited": len(records) == request.limit})

    def lookup(self, request: IriQuery) -> dict:
        self._begin()
        record = self.store.lookup_document(request.iri, self.version) if self.version else None
        return self._bounded({"document": self._document(record) if record else None})

    def _document(self, record):
        references = [self._cite(record["iri"], record["title"], source["url"], source["retrievedAt"]) for source in record["sources"][:3]]
        return {key: record[key] for key in ("iri", "title", "rdfTypes", "language")} | {"excerpt": record["markdown"][:6000], "truncated": len(record["markdown"]) > 6000, "citations": references}

    async def shared_circuits(self):
        from app.graph_queries import shared_circuits_query
        self._begin()
        if self.graph is None or self.version is None:
            raise RuntimeError("Graph tools unavailable")
        result = await self.graph.query(shared_circuits_query(self.version))
        circuits = {}
        for row in result["rows"]:
            iri = row["circuit"]["value"]
            circuit = circuits.setdefault(iri, {"iri": iri, "name": row["circuitName"]["value"], "competitions": {}})
            for suffix in ("A", "B"):
                competition = row["competition" + suffix]["value"]
                entry = circuit["competitions"].setdefault(competition, {"iri": competition, "name": row["name" + suffix]["value"], "citations": []})
                if not entry["citations"]:
                    entry["citations"].append(self._cite(iri, circuit["name"] + " / " + entry["name"], row["source" + suffix]["value"], row["retrieved" + suffix]["value"]))
        for circuit in circuits.values():
            circuit["competitions"] = list(circuit["competitions"].values())
        return self._bounded({"circuits": list(circuits.values()), "limited": result["limited"],
            "publicationVersion": self.version, "relationshipKind": "derived", "premiseKind": "asserted",
            "scope": "Shared canonical Circuit identities in this publication; not necessarily identical Layouts or complete season coverage"})

    async def graph_query(self, request: GraphQuery):
        self._begin()
        if self.graph is None:
            raise RuntimeError("Graph tools unavailable")
        result = await self.graph.query(request.query)
        iris = set()
        for row in result.get("rows", []):
            iris.update(term["value"] for term in row.values() if term.get("type") == "uri")
        for triple in result.get("triples", []):
            iris.add(triple["subject"])
        references = []
        for iri in sorted(iris)[:12]:
            record = self.store.lookup_document(iri, self.version)
            if record:
                references.extend(self._document(record)["citations"])
        return self._bounded({**result, "citations": references})


class AnswerProvider(Protocol):
    async def answer(self, history: list[dict], question: str, tools: ReadTools) -> AnswerDraft: ...


@dataclass
class TabSession:
    created: float
    touched: float
    history: list[dict] = field(default_factory=list)
    busy: bool = False
    task: asyncio.Task | None = None


class AssistantService:
    def __init__(self, store, provider: AnswerProvider | None, clock=time.monotonic, graph_factory=None):
        self.store = store
        self.provider = provider
        self.clock = clock
        self.graph_factory = graph_factory
        self.sessions: dict[str, TabSession] = {}

    def _expire(self):
        now = self.clock()
        for token, session in list(self.sessions.items()):
            if now - session.touched >= 1800 or now - session.created >= 7200:
                self.reset(token)

    def expire_sessions(self):
        self._expire()

    def create_session(self) -> str:
        self._expire()
        if len(self.sessions) >= 100:
            raise ValueError("Assistant session capacity reached")
        token = secrets.token_urlsafe(32)
        self.sessions[token] = TabSession(self.clock(), self.clock())
        return token

    def reset(self, token: str):
        session = self.sessions.pop(token, None)
        if session and session.task and not session.task.done():
            session.task.cancel()

    async def ask(self, token: str, question: str, zone: str) -> AssistantAnswer:
        self._expire()
        session = self.sessions.get(token)
        if not session:
            raise LookupError("Session expired; start a new conversation")
        if not self.provider:
            raise RuntimeError("Assistant is not configured")
        if session.busy:
            raise ValueError("A reply is already in progress")
        if sum(entry.busy for entry in self.sessions.values()) >= 4:
            raise ValueError("Assistant concurrency limit reached")
        if not question.strip() or len(question) > 2000 or len(session.history) >= 24:
            raise ValueError("Conversation limit reached or message invalid")
        try:
            ZoneInfo(zone)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Unknown display time zone") from None
        session.busy = True
        session.task = asyncio.current_task()
        try:
            version = self.store.current_publication_version()
            tools = ReadTools(self.store, version, zone, self.graph_factory(version) if self.graph_factory and version else None)
            async with asyncio.timeout(60):
                draft = await self.provider.answer(list(session.history), question, tools)
            if self.store.current_publication_version() != version:
                raise RuntimeError("Publication changed; retry the question")
            references = [tools.citations[identity] for identity in dict.fromkeys(draft.citations) if identity in tools.citations]
            valid = bool(references) and len(references) == len(set(draft.citations)) and draft.classification != "unsupported"
            text = draft.text if valid else "I could not verify an answer from the published schedule and documentation."
            answer = AssistantAnswer(text=text, citations=references if valid else [], classification=draft.classification if valid else "unsupported",
                                     displayTimeZone=zone, publicationVersion=version, freshness=self.store.source_freshness())
            session.history.extend([{"role": "user", "content": question}, {"role": "assistant", "content": answer.text}])
            session.touched = self.clock()
            return answer
        finally:
            session.busy = False
            session.task = None