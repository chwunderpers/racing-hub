import hashlib
import json
from contextlib import AbstractContextManager
from dataclasses import dataclass
from datetime import UTC, date, datetime
from importlib.resources import files
import re
from zoneinfo import ZoneInfo
from threading import RLock
from typing import Literal, Protocol

import tzdata
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class CandidateMeeting(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)

    status: Literal["scheduled", "cancelled"] = "scheduled"
    competition_identity: str
    circuit_identity: str
    competition_name: str
    season_year: int
    meeting_name: str
    circuit_name: str
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self) -> "CandidateMeeting":
        if self.start_date > self.end_date:
            raise ValueError("Meeting start_date must not be after end_date")
        return self


class CandidateEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)

    source_identity: str
    source_url: str
    retrieved_at: AwareDatetime
    source_language: Literal["en"]
    evidence: str
    meeting: CandidateMeeting

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str) -> str:
        HttpUrl(value)
        return value


@dataclass(frozen=True)
class PublicationResult:
    status: Literal["published"]
    version: str


class PublishedTime(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local: str
    offset: str | None = None
    zone: str | None = None
    rules_version: Literal["2026.3"] = "2026.3"

    @field_validator("local")
    @classmethod
    def valid_local(cls, value: str) -> str:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}(:\d{2})?)?", value):
            raise ValueError("Expected a published date or local clock without an offset")
        datetime.fromisoformat(value)
        return value

    @field_validator("offset")
    @classmethod
    def valid_offset(cls, value: str | None) -> str | None:
        if value is not None:
            if not re.fullmatch(r"[+-](?:[01]\d|2[0-3]):[0-5]\d", value):
                raise ValueError("Expected signed HH:MM offset")
            datetime.fromisoformat("2026-01-01T00:00:00" + value)
        return value

    @property
    def instant(self) -> datetime | None:
        if "T" not in self.local or not self.offset:
            return None
        resolved = datetime.fromisoformat(self.local + self.offset)
        if self.zone:
            if tzdata.__version__ != self.rules_version:
                raise ValueError("The accepted timezone rules version is not installed")
            if not re.fullmatch(r"[A-Za-z0-9_+-]+(?:/[A-Za-z0-9_+-]+)*", self.zone):
                return None
            try:
                with files("tzdata.zoneinfo").joinpath(*self.zone.split("/")).open("rb") as rules:
                    in_zone = resolved.astimezone(ZoneInfo.from_file(rules, key=self.zone))
            except (FileNotFoundError, IsADirectoryError):
                return None
            if in_zone.replace(tzinfo=None) != resolved.replace(tzinfo=None) or in_zone.utcoffset() != resolved.utcoffset():
                return None
        return resolved.astimezone(UTC)


class CandidateSession(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)

    identity: str
    name: str
    status: Literal["scheduled", "completed", "cancelled"]
    start: PublishedTime
    end: PublishedTime | None = None

    @model_validator(mode="after")
    def valid_range(self) -> "CandidateSession":
        if self.end and self.start.instant and self.end.instant and self.end.instant < self.start.instant:
            raise ValueError("Session end must not precede start")
        return self


class ScheduledMeeting(CandidateMeeting):
    round_number: int = Field(gt=0)
    event_timezone: str | None = None
    sessions: list[CandidateSession]

    @model_validator(mode="after")
    def distinct_sessions(self) -> "ScheduledMeeting":
        identities = [session.identity for session in self.sessions]
        if len(identities) != len(set(identities)):
            raise ValueError("Duplicate session identity")
        return self


class ScheduledEnvelope(CandidateEnvelope):
    meeting: ScheduledMeeting


class SeasonCandidateEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)

    source_identity: str
    source_url: str
    retrieved_at: AwareDatetime
    source_language: Literal["en"]
    competition_identity: str
    season_year: int
    meetings: list[ScheduledEnvelope] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_scope(self) -> "SeasonCandidateEnvelope":
        HttpUrl(self.source_url)
        identities = [entry.source_identity for entry in self.meetings]
        sessions = [session.identity for entry in self.meetings for session in entry.meeting.sessions]
        if len(identities) != len(set(identities)) or len(sessions) != len(set(sessions)):
            raise ValueError("Duplicate Meeting or Session identity")
        if any(entry.meeting.competition_identity != self.competition_identity or entry.meeting.season_year != self.season_year for entry in self.meetings):
            raise ValueError("Mixed Competition or Season scope")
        return self


PublicationCandidate = CandidateEnvelope | SeasonCandidateEnvelope


def parse_candidate(value: dict) -> PublicationCandidate:
    return SeasonCandidateEnvelope.model_validate(value) if "meetings" in value else CandidateEnvelope.model_validate(value)


def candidate_meetings(candidate: PublicationCandidate) -> list[CandidateEnvelope]:
    return list(candidate.meetings) if isinstance(candidate, SeasonCandidateEnvelope) else [candidate]


class OperationalStore(Protocol):
    def publication_lock(self) -> AbstractContextManager: ...

    def current_publication_version(self) -> str | None: ...

    def stage(self, version: str, envelope: PublicationCandidate) -> None: ...

    def promote(self, version: str) -> None: ...


class GraphProjection(Protocol):
    def project(self, version: str, envelope: PublicationCandidate) -> None: ...

    def agrees(self, version: str, meeting_id: str, envelope: PublicationCandidate | None = None) -> bool: ...


def canonical_meeting_id(source_identity: str) -> str:
    return f"meeting:{source_identity}"


def canonical_resource_ids(envelope: CandidateEnvelope) -> dict[str, str]:
    meeting = envelope.meeting
    competition_id = f"competition:{meeting.competition_identity}"
    return {
        "competitions": competition_id,
        "seasons": f"season:{competition_id}:{meeting.season_year}",
        "meetings": canonical_meeting_id(envelope.source_identity),
        "circuits": f"circuit:{meeting.circuit_identity}",
        "provenance": f"source:{envelope.source_identity}",
    }


def publication_version(envelope: PublicationCandidate) -> str:
    payload = envelope.model_dump(mode="json")
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def meeting_view(envelope: CandidateEnvelope) -> dict[str, object]:
    meeting = envelope.meeting
    view = {
        "id": canonical_meeting_id(envelope.source_identity),
        "status": meeting.status,
        "name": meeting.meeting_name,
        "competition": meeting.competition_name,
        "season": meeting.season_year,
        "circuit": meeting.circuit_name,
        "startDate": meeting.start_date.isoformat(),
        "endDate": meeting.end_date.isoformat(),
        "sourceUrl": envelope.source_url,
        "retrievedAt": envelope.retrieved_at.isoformat().replace("+00:00", "Z"),
    }
    if isinstance(meeting, ScheduledMeeting):
        def clock_view(clock: PublishedTime | None):
            return {**clock.model_dump(), "instant": clock.instant.isoformat().replace("+00:00", "Z") if clock.instant else None} if clock else None
        view.update({
            "round": meeting.round_number,
            "roundId": f"round:{envelope.source_identity}",
            "eventTimezone": meeting.event_timezone,
            "sessions": [{
                "id": session.identity, "name": session.name, "status": session.status,
                "start": clock_view(session.start), "end": clock_view(session.end),
            } for session in meeting.sessions],
        })
    return view


class PublicationModule:
    def __init__(
        self,
        operational_store: OperationalStore,
        graph_projection: GraphProjection,
    ) -> None:
        self._operational_store = operational_store
        self._graph_projection = graph_projection

    def publish(self, envelope: PublicationCandidate) -> PublicationResult:
        with self._operational_store.publication_lock():
            return self._publish(envelope)

    def publish_initial(self, envelope: PublicationCandidate) -> PublicationResult:
        with self._operational_store.publication_lock():
            current_version = self._operational_store.current_publication_version()
            if current_version is not None:
                return PublicationResult(status="published", version=current_version)
            return self._publish(envelope)

    def publish_revision(self, envelope: PublicationCandidate, baseline_version: str | None) -> PublicationResult:
        with self._operational_store.publication_lock():
            current_version = self._operational_store.current_publication_version()
            version = publication_version(envelope)
            if current_version == version:
                return PublicationResult(status="published", version=version)
            if current_version != baseline_version:
                raise ValueError("Publication baseline is stale; preview and review again")
            return self._publish(envelope)

    def _publish(self, envelope: PublicationCandidate) -> PublicationResult:
        version = publication_version(envelope)
        meeting_id = canonical_meeting_id(candidate_meetings(envelope)[0].source_identity)
        self._operational_store.stage(version, envelope)
        self._graph_projection.project(version, envelope)
        if not self._graph_projection.agrees(version, meeting_id, envelope):
            raise RuntimeError("Graph projection does not agree with publication")
        self._operational_store.promote(version)
        return PublicationResult(status="published", version=version)


class InMemoryCanonicalResources:
    def __init__(self) -> None:
        self._resources: dict[str, set[str]] = {
            resource_type: set()
            for resource_type in (
                "competitions",
                "seasons",
                "meetings",
                "circuits",
                "provenance",
            )
        }

    def add(self, envelope: CandidateEnvelope) -> None:
        for resource_type, resource_id in canonical_resource_ids(envelope).items():
            self._resources[resource_type].add(resource_id)

    def contains_meeting(self, meeting_id: str) -> bool:
        return meeting_id in self._resources["meetings"]

    def counts(self) -> dict[str, int]:
        return {
            resource_type: len(resource_ids)
            for resource_type, resource_ids in self._resources.items()
        }


class InMemoryOperationalStore:
    def __init__(self) -> None:
        self.current_version: str | None = None
        self._staged: dict[str, PublicationCandidate] = {}
        self._resources = InMemoryCanonicalResources()
        self._publication_lock = RLock()
        self._source_attempt: dict | None = None

    def record_source_attempt(self, checked_at: datetime, success: bool, pending: bool = False) -> None:
        previous = self._source_attempt or {}
        self._source_attempt = {"checkedAt": checked_at.isoformat(), "success": success, "pending": pending, "lastSuccessAt": checked_at.isoformat() if success else previous.get("lastSuccessAt")}

    def source_freshness(self) -> dict:
        from app.freshness import freshness_view
        return freshness_view(self._source_attempt)

    def publication_lock(self) -> AbstractContextManager:
        return self._publication_lock

    def current_publication_version(self) -> str | None:
        return self.current_version

    def stage(self, version: str, envelope: PublicationCandidate) -> None:
        self._staged[version] = envelope
        for entry in candidate_meetings(envelope):
            self._resources.add(entry)

    def promote(self, version: str) -> None:
        if version not in self._staged:
            raise RuntimeError("Publication version was not staged")
        self.current_version = version

    def publication_envelope(self, version: str) -> PublicationCandidate:
        return self._staged[version].model_copy(deep=True)

    def visible_meetings(self) -> list[dict[str, object]]:
        if self.current_version is None:
            return []
        return [{
            **meeting_view(entry),
            "publicationVersion": self.current_version,
        } for entry in candidate_meetings(self._staged[self.current_version])]

    def canonical_resource_counts(self) -> dict[str, int]:
        return self._resources.counts()


class InMemoryGraphProjection:
    def __init__(self) -> None:
        self.current_version: str | None = None
        self._resources = InMemoryCanonicalResources()

    def project(self, version: str, envelope: PublicationCandidate) -> None:
        self.current_version = version
        for entry in candidate_meetings(envelope):
            self._resources.add(entry)

    def agrees(self, version: str, meeting_id: str, envelope: CandidateEnvelope | None = None) -> bool:
        return (
            self.current_version == version
            and self._resources.contains_meeting(meeting_id)
        )

    def canonical_resource_counts(self) -> dict[str, int]:
        return self._resources.counts()