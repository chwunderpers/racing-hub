from pathlib import Path
from datetime import UTC, datetime
import hashlib
import json
from functools import wraps
from typing import Protocol
from uuid import uuid4

import yaml
from filelock import FileLock
from pydantic import ValidationError

from app.publication import CandidateEnvelope, PublicationModule, publication_version


class ReviewStore(Protocol):
    def visible_meetings(self) -> list[dict[str, object]]: ...

    def publication_envelope(self, version: str) -> CandidateEnvelope: ...


def serialized(method):
    @wraps(method)
    def locked(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return locked


class ReviewService:
    def __init__(self, directory: Path, store: ReviewStore, publisher: PublicationModule) -> None:
        self.directory = directory
        self.store = store
        self.publisher = publisher
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = FileLock(self.directory / ".review.lock", timeout=0)

    @serialized
    def preview(self, candidate: dict) -> dict:
        if candidate.get("source_language") != "en":
            raise ValueError("Only English candidate artifacts may be retained")
        item = self._preview(candidate)
        queue = self._queue()
        queue["items"].append(item)
        self._write(self.directory / "queue.yaml", queue)
        return item

    @serialized
    def show(self, item_id: str) -> dict:
        return next(item for item in self._queue()["items"] if item["id"] == item_id)

    @serialized
    def propose_decision(
        self, item_id: str, outcome: str, person: str, rationale: str,
        evidence: list[str], corrected_candidate: dict | None = None,
        identity_resolutions: dict[str, str] | None = None,
    ) -> dict:
        if outcome not in ("accepted", "rejected", "corrected", "deferred"):
            raise ValueError("Unknown decision outcome")
        if not person.strip() or not rationale.strip() or not evidence or not all(value.strip() for value in evidence):
            raise ValueError("Person, rationale and evidence are required")
        if (outcome == "corrected") != (corrected_candidate is not None):
            raise ValueError("A correction requires exactly one corrected candidate")
        if corrected_candidate is not None:
            CandidateEnvelope.model_validate(corrected_candidate)
        queue = self._queue()
        item = next(entry for entry in queue["items"] if entry["id"] == item_id)
        decision = {
            "id": str(uuid4()), "itemId": item_id, "outcome": outcome,
            "person": person, "rationale": rationale, "evidence": evidence,
            "proposedAt": datetime.now(UTC).isoformat(),
            "candidate": item["candidate"], "baselineVersion": item["baselineVersion"],
            "preview": item["preview"], "correctedCandidate": corrected_candidate,
            "identityResolutions": identity_resolutions or {},
        }
        proposal = {"decision": decision, "confirmation": self._digest(decision)}
        item["proposal"] = proposal
        self._write(self.directory / "queue.yaml", queue)
        return proposal

    @serialized
    def record_decision(self, item_id: str, confirmation: str) -> dict:
        queue = self._queue()
        item = next(entry for entry in queue["items"] if entry["id"] == item_id)
        proposal = item.get("proposal")
        if not proposal or confirmation != self._digest(proposal["decision"]):
            raise ValueError("Exact proposal confirmation is required")
        decision = proposal["decision"]
        if decision["candidate"] != item["candidate"] or decision["baselineVersion"] != item["baselineVersion"]:
            raise ValueError("Candidate changed after proposal confirmation")
        decision["decidedAt"] = datetime.now(UTC).isoformat()
        destination = self.directory / "decisions"
        destination.mkdir(exist_ok=True)
        path = destination / f"{decision['id']}.yaml"
        if path.exists():
            recorded = yaml.safe_load(path.read_text("utf-8"))
            content = {key: value for key, value in recorded.items() if key != "decidedAt"}
            if self._digest(content) != confirmation:
                raise ValueError("Recorded decision does not match the proposal confirmation")
            decision = recorded
        else:
            self._write(path, decision)
        item.pop("proposal")
        item.pop("acceptedDecision", None)
        item.setdefault("decisions", []).append(decision["id"])
        if decision["outcome"] == "accepted":
            item["acceptedDecision"] = decision["id"]
        elif decision["outcome"] == "rejected":
            queue["items"].remove(item)
        elif decision["outcome"] == "corrected":
            replacement = self._preview(decision["correctedCandidate"])
            for field in ("candidate", "preview", "baselineVersion"):
                item[field] = replacement[field]
        self._write(self.directory / "queue.yaml", queue)
        return decision

    @serialized
    def propose_publication(self, item_id: str) -> dict:
        item = self.show(item_id)
        decision, envelope = self._accepted_candidate(item)
        proposal = {
            "itemId": item_id, "decisionId": decision["id"],
            "baselineVersion": item["baselineVersion"], "version": publication_version(envelope),
            "candidate": decision["candidate"],
        }
        return {**proposal, "confirmation": self._digest(proposal)}

    @serialized
    def publish(self, item_id: str, confirmation: str) -> dict:
        proposal = self.propose_publication(item_id)
        if confirmation != proposal["confirmation"]:
            raise ValueError("Separate publication confirmation is required")
        queue = self._queue()
        item = next(entry for entry in queue["items"] if entry["id"] == item_id)
        decision, envelope = self._accepted_candidate(item)
        result = self.publisher.publish_revision(envelope, item["baselineVersion"])
        receipt = {
            "itemId": item_id, "decisionId": decision["id"],
            "version": result.version, "status": result.status,
            "publishedAt": datetime.now(UTC).isoformat(),
        }
        destination = self.directory / "publications"
        destination.mkdir(exist_ok=True)
        self._write(destination / f"{decision['id']}.yaml", receipt)
        queue["items"].remove(item)
        self._write(self.directory / "queue.yaml", queue)
        return receipt

    def _accepted_candidate(self, item: dict) -> tuple[dict, CandidateEnvelope]:
        decision_id = item.get("acceptedDecision")
        if not decision_id:
            raise ValueError("An accepted decision is required")
        decision = yaml.safe_load((self.directory / "decisions" / f"{decision_id}.yaml").read_text("utf-8"))
        if decision["outcome"] != "accepted" or decision["itemId"] != item["id"]:
            raise ValueError("An accepted decision for this item is required")
        if decision["candidate"] != item["candidate"] or decision["baselineVersion"] != item["baselineVersion"]:
            raise ValueError("The accepted candidate or baseline has changed")
        current = self._preview(item["candidate"])
        envelope = CandidateEnvelope.model_validate(item["candidate"])
        if current["baselineVersion"] not in (item["baselineVersion"], publication_version(envelope)):
            raise ValueError("Publication baseline is stale; preview and review again")
        preview = current["preview"]
        if preview["validationErrors"] or preview["conflicts"] or decision["preview"]["conflicts"]:
            raise ValueError("Candidate has validation errors or publication conflicts")
        for field in set(preview["unresolvedIdentities"] + decision["preview"]["unresolvedIdentities"]):
            identity = item["candidate"]["meeting"].get(field)
            if not identity or decision["identityResolutions"].get(field) != identity:
                raise ValueError("Candidate has unresolved identities")
        return decision, envelope

    @staticmethod
    def _digest(value: dict) -> str:
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _queue(self) -> dict:
        path = self.directory / "queue.yaml"
        return yaml.safe_load(path.read_text("utf-8")) if path.exists() else {"items": []}

    @staticmethod
    def _write(path: Path, data: dict) -> None:
        temporary = path.with_suffix(f".{uuid4()}.tmp")
        temporary.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), "utf-8")
        temporary.replace(path)

    def _preview(self, candidate: dict) -> dict:
        meetings = self.store.visible_meetings()
        baseline_version = str(meetings[0]["publicationVersion"]) if meetings else None
        baseline = self.store.publication_envelope(baseline_version) if baseline_version else None
        errors = []
        try:
            candidate = CandidateEnvelope.model_validate(candidate).model_dump(mode="json")
        except ValidationError as error:
            errors = [f"{'.'.join(map(str, entry['loc']))}: {entry['msg']}" for entry in error.errors()]
        previous = baseline.meeting.model_dump(mode="json") if baseline else {}
        proposed = candidate.get("meeting", {})
        changes = {
            field: {"before": previous.get(field), "after": value}
            for field, value in proposed.items()
            if previous.get(field) != value
        }
        old_envelope = baseline.model_dump(mode="json") if baseline else {}
        for field in ("source_identity", "source_url", "retrieved_at", "evidence"):
            if old_envelope.get(field) != candidate.get(field):
                changes[field] = {"before": old_envelope.get(field), "after": candidate.get(field)}
        unresolved = [
            field for field in ("competition_identity", "circuit_identity")
            if not proposed.get(field) or (baseline and previous[field] != proposed.get(field))
        ]
        conflicts = []
        source_identity = candidate.get("source_identity")
        if baseline and source_identity != baseline.source_identity:
            conflicts.append("This single-Meeting publication would replace a different Meeting; merge the schedule first")
        if not source_identity:
            unresolved.append("source_identity")
        return {
            "id": str(uuid4()),
            "createdAt": datetime.now(UTC).isoformat(),
            "status": "open",
            "baselineVersion": baseline_version,
            "candidate": candidate,
            "preview": {
                "additions": [source_identity] if baseline is None or source_identity != baseline.source_identity else [],
                "changes": changes,
                "cancellations": [source_identity] if proposed.get("status") == "cancelled" and previous.get("status") != "cancelled" else [],
                "conflicts": conflicts,
                "unresolvedIdentities": unresolved,
                "validationErrors": errors,
            },
        }