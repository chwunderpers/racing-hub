import os
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.stores import PostgresOperationalStore


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    database: Literal["ok", "unavailable"]


class MeetingResponse(BaseModel):
    status: Literal["scheduled", "cancelled"] = "scheduled"
    publicationVersion: str
    id: str
    name: str
    competition: str
    season: int
    circuit: str
    startDate: str
    endDate: str
    sourceUrl: str
    retrievedAt: str


class ScheduleResponse(BaseModel):
    meetings: list[MeetingResponse]


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


@app.get("/api/schedule", response_model=ScheduleResponse)
def schedule(store: PostgresOperationalStore = Depends(operational_store)) -> ScheduleResponse:
    return ScheduleResponse(
        meetings=[MeetingResponse.model_validate(meeting) for meeting in store.visible_meetings()]
    )