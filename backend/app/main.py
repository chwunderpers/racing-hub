import os

import psycopg
from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str


class ScheduleResponse(BaseModel):
    meetings: list[dict[str, object]]


def database_status() -> str:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://motorsport:motorsport@localhost:5432/motorsport",
    )
    try:
        with psycopg.connect(database_url, connect_timeout=2) as connection:
            connection.execute("SELECT 1")
        return "ok"
    except psycopg.Error:
        return "unavailable"


app = FastAPI(title="Motorsport Hub", version="0.1.0")
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
def schedule() -> ScheduleResponse:
    return ScheduleResponse(meetings=[])