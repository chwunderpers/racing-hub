import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Protocol

from pydantic import BaseModel


class CandidateMeeting(BaseModel):
    competition_identity: str
    circuit_identity: str
    competition_name: str
    season_year: int
    meeting_name: str
    circuit_name: str
    start_date: date
    end_date: date


class CandidateEnvelope(BaseModel):
    source_identity: str
    source_url: str
    retrieved_at: datetime
    source_language: Literal["en"]
    evidence: str
    meeting: CandidateMeeting


@dataclass(frozen=True)
class PublicationResult:
    status: Literal["published"]
    version: str


class OperationalStore(Protocol):
    def stage(self, version: str, envelope: CandidateEnvelope) -> None: ...

    def promote(self, version: str) -> None: ...


class GraphProjection(Protocol):
    def project(self, version: str, envelope: CandidateEnvelope) -> None: ...

    def agrees(self, version: str, meeting_id: str) -> bool: ...


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


def publication_version(envelope: CandidateEnvelope) -> str:
    payload = envelope.model_dump(mode="json")
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def meeting_view(envelope: CandidateEnvelope) -> dict[str, object]:
    meeting = envelope.meeting
    return {
        "id": canonical_meeting_id(envelope.source_identity),
        "name": meeting.meeting_name,
        "competition": meeting.competition_name,
        "season": meeting.season_year,
        "circuit": meeting.circuit_name,
        "startDate": meeting.start_date.isoformat(),
        "endDate": meeting.end_date.isoformat(),
        "sourceUrl": envelope.source_url,
        "retrievedAt": envelope.retrieved_at.isoformat().replace("+00:00", "Z"),
    }


class PublicationModule:
    def __init__(
        self,
        operational_store: OperationalStore,
        graph_projection: GraphProjection,
    ) -> None:
        self._operational_store = operational_store
        self._graph_projection = graph_projection

    def publish(self, envelope: CandidateEnvelope) -> PublicationResult:
        version = publication_version(envelope)
        meeting_id = canonical_meeting_id(envelope.source_identity)
        self._operational_store.stage(version, envelope)
        self._graph_projection.project(version, envelope)
        if not self._graph_projection.agrees(version, meeting_id):
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
        self._staged: dict[str, CandidateEnvelope] = {}
        self._resources = InMemoryCanonicalResources()

    def stage(self, version: str, envelope: CandidateEnvelope) -> None:
        self._staged[version] = envelope
        self._resources.add(envelope)

    def promote(self, version: str) -> None:
        if version not in self._staged:
            raise RuntimeError("Publication version was not staged")
        self.current_version = version

    def visible_meetings(self) -> list[dict[str, object]]:
        if self.current_version is None:
            return []
        return [{
            **meeting_view(self._staged[self.current_version]),
            "publicationVersion": self.current_version,
        }]

    def canonical_resource_counts(self) -> dict[str, int]:
        return self._resources.counts()


class InMemoryGraphProjection:
    def __init__(self) -> None:
        self.current_version: str | None = None
        self._resources = InMemoryCanonicalResources()

    def project(self, version: str, envelope: CandidateEnvelope) -> None:
        self.current_version = version
        self._resources.add(envelope)

    def agrees(self, version: str, meeting_id: str) -> bool:
        return (
            self.current_version == version
            and self._resources.contains_meeting(meeting_id)
        )

    def canonical_resource_counts(self) -> dict[str, int]:
        return self._resources.counts()