import os
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.stores import PostgresOperationalStore
from app.publication import FieldAssertion


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
    status: Literal["scheduled", "completed", "cancelled"]
    start: TimeResponse
    end: TimeResponse | None


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
    kind: Literal["championship", "test", "prologue"] | None = None
    fieldAssertions: list[FieldAssertion] = Field(default_factory=list)
    eventTimezone: str | None = None
    sessions: list[SessionResponse] = Field(default_factory=list)


class SourceFreshnessResponse(BaseModel):
    sourceFamily: str
    stale: bool
    reason: str | None = None
    checkedAt: str | None = None
    lastSuccessAt: str | None = None


class FreshnessResponse(BaseModel):
    stale: bool
    reason: str | None = None
    checkedAt: str | None = None
    lastSuccessAt: str | None = None
    sources: list[SourceFreshnessResponse] = Field(default_factory=list)


class ScheduleResponse(BaseModel):
    meetings: list[MeetingResponse]
    freshness: FreshnessResponse | None = None


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


app = FastAPI(title="Racing Hub", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(","),
    allow_methods=["GET"],
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
    return ScheduleResponse(
        meetings=[MeetingResponse.model_validate(meeting) for meeting in store.visible_meetings()],
        **({"freshness": FreshnessResponse.model_validate(store.source_freshness())} if hasattr(store, "source_freshness") else {}),
    )