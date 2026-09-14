import os
import asyncio
import hashlib
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated, Literal

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, Path, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.assistant import AssistantAnswer, AssistantService, RegulationComparisonQuery
from app.assistant_provider import configured_provider
from app.assistant_store import AssistantReadStore
from app.graph_config import configured_graph_factory
from app.freshness import FreshnessResponse
from app.stores import PostgresOperationalStore
from app.publication import FieldAssertion, CandidatePlace, CandidateLayout, CoverageAssessment, coverage_view
from app.vehicle_projection import vehicle_iri
from app.vehicles import VehicleDetailsResponse, VehicleListResponse
from app.capabilities import CapabilityQuery, CapabilityRegistry, CapabilityResponse, configured_capabilities, published_contributions
from app.exports import EXPORT_TYPES, ExportFormat, ExportSelection, ontology_bytes, publication_graph, serialize_publication


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]


class TimeResponse(BaseModel):
    local: str
    offset: str | None
    zone: str | None
    instant: str | None


class SessionResponse(BaseModel):
    id: str
    name: str
    status: Literal["scheduled", "completed", "cancelled", "abandoned"]
    start: TimeResponse
    end: TimeResponse | None
    roundId: str | None = None
    durationMinutes: int | None = None
    circuitId: str | None = None
    layout: CandidateLayout | None = None


class RoundResponse(BaseModel):
    id: str
    number: int
    name: str
    status: Literal["scheduled", "completed", "cancelled", "abandoned"]


class SeasonCoverageResponse(CoverageAssessment):
    competitionId: str
    season: int


class MeetingResponse(BaseModel):
    status: Literal["scheduled", "cancelled"] = "scheduled"
    publicationVersion: str
    id: str
    name: str
    competition: str
    season: int
    circuit: str
    competitionId: str | None = None
    circuitId: str | None = None
    startDate: str
    endDate: str
    sourceUrl: str
    retrievedAt: str
    round: int | None = None
    roundId: str | None = None
    rounds: list[RoundResponse] = Field(default_factory=list)
    venue: CandidatePlace | None = None
    layout: CandidateLayout | None = None
    coverage: CoverageAssessment | None = None
    kind: Literal["championship", "test", "prologue"] | None = None
    fieldAssertions: list[FieldAssertion] = Field(default_factory=list)
    eventTimezone: str | None = None
    sessions: list[SessionResponse] = Field(default_factory=list)


class ScheduleResponse(BaseModel):
    meetings: list[MeetingResponse]
    freshness: FreshnessResponse | None = None
    coverage: list[SeasonCoverageResponse] = Field(default_factory=list)


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql://motorsport:motorsport@localhost:5432/motorsport",
    )


def operational_store() -> PostgresOperationalStore:
    return PostgresOperationalStore(database_url())


def database_status() -> str:
    try:
        with psycopg.connect(database_url(), connect_timeout=2) as connection:
            connection.execute("SELECT 1")
        return "ok"
    except psycopg.Error:
        return "unavailable"


@asynccontextmanager
async def application_lifespan(application):
    loop = asyncio.get_running_loop()
    handle = None

    def cleanup():
        nonlocal handle
        if assistant_service.cache_info().currsize:
            assistant_service().expire_sessions()
        handle = loop.call_later(60, cleanup)

    cleanup()
    try:
        yield
    finally:
        if handle:
            handle.cancel()
        if assistant_service.cache_info().currsize:
            service = assistant_service()
            for token in list(service.sessions):
                service.reset(token)
        assistant_service.cache_clear()


app = FastAPI(title="Racing Hub", version="0.1.0", lifespan=application_lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(","),
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


@app.get(
    "/api/health",
    response_model=HealthResponse,
    responses={503: {"model": HealthResponse}},
)
def health(database: str = Depends(database_status)) -> Response:
    status = "ok" if database == "ok" else "degraded"
    return JSONResponse(
        status_code=200 if status == "ok" else 503,
        content=HealthResponse(status=status, database=database).model_dump(),
    )


@app.get("/api/schedule", response_model=ScheduleResponse, response_model_exclude_unset=True)
def schedule(store: PostgresOperationalStore = Depends(operational_store)) -> ScheduleResponse:
    version = store.current_publication_version() if hasattr(store, "current_publication_version") else None
    return ScheduleResponse(
        meetings=[MeetingResponse.model_validate(meeting) for meeting in (store.visible_meetings(version=version) if version else store.visible_meetings())],
        **({"coverage": coverage_view(store.publication_envelope(version))} if version else {}),
        **({"freshness": FreshnessResponse.model_validate(store.source_freshness())} if hasattr(store, "source_freshness") else {}),
    )


@app.get("/api/exports", response_model=ExportSelection, responses={503: {"description": "Publication store unavailable"}})
def export_selection(response: Response, store: PostgresOperationalStore = Depends(operational_store)) -> ExportSelection:
    response.headers["Cache-Control"] = "no-store"
    try:
        return ExportSelection(publicationVersion=store.current_publication_version())
    except psycopg.Error:
        raise HTTPException(503, "Publication service unavailable", headers={"Cache-Control": "no-store"}) from None


@app.get("/api/exports/ontology", response_class=Response, responses={200: {"content": {"text/turtle": {}}}})
def export_ontology() -> Response:
    body = ontology_bytes()
    checksum = hashlib.sha256(body).hexdigest()
    return Response(body, media_type="text/turtle", headers={
        "Content-Disposition": f'attachment; filename="racing-hub-ontology-{checksum}.ttl"',
        "ETag": f'"{checksum}"', "Cache-Control": "no-cache", "X-Content-Type-Options": "nosniff",
    })


@app.get("/api/exports/publications/{version}/{format}", response_class=Response,
         responses={200: {"content": {"application/ld+json": {}, "text/csv": {}, "text/turtle": {}}},
                    409: {"description": "Publication unavailable or changed"}, 503: {"description": "Publication store unavailable"}})
def export_publication(version: Annotated[str, Path(pattern=r"^[0-9a-f]{64}$")], format: ExportFormat,
                       store: PostgresOperationalStore = Depends(operational_store)) -> Response:
    try:
        graph = publication_graph(store, version)
    except LookupError:
        raise HTTPException(409, "Publication unavailable or changed; refresh the export selection", headers={"Cache-Control": "no-store"}) from None
    except psycopg.Error:
        raise HTTPException(503, "Publication service unavailable", headers={"Cache-Control": "no-store"}) from None
    media_type, extension = EXPORT_TYPES[format]
    return Response(serialize_publication(graph, version, format), media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="racing-hub-{version}.{extension}"',
                             "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff", "X-Publication-Version": version})


@app.get("/api/capabilities", response_model=CapabilityResponse)
def capabilities(request: Annotated[CapabilityQuery, Query()], store: PostgresOperationalStore = Depends(operational_store),
                 registry: CapabilityRegistry = Depends(configured_capabilities)) -> CapabilityResponse:
    try:
        return published_contributions(registry, store, store.current_publication_version(), request)
    except LookupError:
        raise HTTPException(404, "Published Meeting or Session not found") from None


@app.get("/api/vehicles", response_model=VehicleListResponse)
def vehicles(store: PostgresOperationalStore = Depends(operational_store)) -> VehicleListResponse:
    version = store.current_publication_version()
    summaries = []
    if version:
        snapshot = store.publication_envelope(version)
        for vehicle in getattr(snapshot, "vehicles", []):
            document = store.lookup_document(str(vehicle_iri(vehicle.identity)), version)
            if document and "vehicleSpecification" in document:
                summaries.append({"identity": vehicle.identity, "iri": document["iri"], "title": document["title"]})
    return VehicleListResponse.model_validate({"publicationVersion": version, "vehicles": summaries})


@app.get("/api/vehicles/{identity}", response_model=VehicleDetailsResponse)
def vehicle_details(identity: str, store: PostgresOperationalStore = Depends(operational_store)) -> VehicleDetailsResponse:
    version = store.current_publication_version()
    document = store.lookup_document(str(vehicle_iri(identity)), version) if version else None
    if not document or "vehicleSpecification" not in document:
        raise HTTPException(404, "Published vehicle not found")
    return VehicleDetailsResponse.model_validate({"publicationVersion": version, "vehicle": document["vehicleSpecification"]})


class AssistantMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=2000)
    displayTimeZone: str = Field(min_length=1, max_length=100)
    comparison: RegulationComparisonQuery | None = None


class AssistantSessionResponse(BaseModel):
    sessionToken: str
    available: bool


@lru_cache
def assistant_service() -> AssistantService:
    read_url = os.environ.get("ASSISTANT_DATABASE_URL")
    return AssistantService(AssistantReadStore(read_url) if read_url else None, configured_provider() if read_url else None,
                            graph_factory=configured_graph_factory(), capability_factory=configured_capabilities)


def assistant_origin(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    origin = request.headers.get("origin")
    allowed = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin and origin not in allowed:
        raise HTTPException(403, "Origin not allowed")


@app.post("/api/assistant/sessions", response_model=AssistantSessionResponse, dependencies=[Depends(assistant_origin)])
async def assistant_session(service: AssistantService = Depends(assistant_service)):
    try:
        return AssistantSessionResponse(sessionToken=service.create_session(), available=service.provider is not None)
    except ValueError:
        raise HTTPException(429, "Assistant session capacity reached") from None


@app.post("/api/assistant/messages", response_model=AssistantAnswer, dependencies=[Depends(assistant_origin)])
async def assistant_message(payload: AssistantMessage, x_assistant_session: str = Header(min_length=32, max_length=100), service: AssistantService = Depends(assistant_service)):
    try:
        return await service.ask(x_assistant_session, payload.message, payload.displayTimeZone, payload.comparison)
    except LookupError:
        raise HTTPException(410, "Session expired; start a new conversation") from None
    except ValueError:
        raise HTTPException(400, "Invalid request or conversation limit reached") from None
    except Exception:
        raise HTTPException(503, "Assistant temporarily unavailable") from None


@app.delete("/api/assistant/session", status_code=204, dependencies=[Depends(assistant_origin)])
async def assistant_reset(x_assistant_session: str = Header(min_length=32, max_length=100), service: AssistantService = Depends(assistant_service)):
    service.reset(x_assistant_session)