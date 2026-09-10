from pathlib import Path
from datetime import UTC, datetime
import hashlib
import json
from functools import wraps
from typing import Literal, Protocol
from uuid import uuid4

import yaml
from filelock import FileLock
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.publication import CandidateEnvelope, PublicationCandidate, PublicationSnapshot, SeasonCandidateEnvelope, PublicationModule, parse_candidate, candidate_meetings, publication_version


class DecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, str_min_length=1)

    outcome: Literal["accepted", "rejected", "corrected", "deferred"]
    person: str
    rationale: str
    evidence: list[str] = Field(min_length=1)
    corrected_candidate: dict | None = None
    identity_resolutions: dict[str, str] = Field(default_factory=dict)
    regulation_confirmations: list[str] = Field(default_factory=list)


class ReviewStore(Protocol):
    def visible_meetings(self) -> list[dict[str, object]]: ...

    def current_publication_version(self) -> str | None: ...

    def publication_envelope(self, version: str) -> PublicationCandidate: ...


def serialized(method):
    @wraps(method)
    def locked(self, *args, **kwargs):
        with self._lock:
            return method(self, *args, **kwargs)
    return locked


def _read_queue(directory: Path) -> dict:
    path = directory / "queue.yaml"
    return yaml.safe_load(path.read_text("utf-8")) if path.exists() else {"items": []}


def show_review_item(directory: Path, item_id: str) -> dict:
    if not directory.exists():
        raise StopIteration("Review Item not found")
    with FileLock(directory / ".review.lock", timeout=0):
        return next(item for item in _read_queue(directory)["items"] if item["id"] == item_id)


class ReviewService:
    def __init__(self, directory: Path, store: ReviewStore, publisher: PublicationModule) -> None:
        self.directory = directory
        self.store = store
        self.publisher = publisher
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = FileLock(self.directory / ".review.lock", timeout=0)

    @serialized
    def preview(self, candidate: dict, *, expected_baseline: str | None = None) -> dict:
        if candidate.get("source_language") != "en":
            raise ValueError("Only English candidate artifacts may be retained")
        for bundle in candidate.get("regulations", []):
            for passage in bundle.get("passages", []):
                if passage.get("language") != "en":
                    raise ValueError("Only English regulation evidence may be persisted; translate before preview")
        item = self._preview(candidate)
        if expected_baseline is not None and item["baselineVersion"] != expected_baseline:
            raise ValueError("Publication baseline changed during ingestion; prepare and review again")
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
        regulation_confirmations: list[str] | None = None,
    ) -> dict:
        request = DecisionRequest.model_validate({
            "outcome": outcome, "person": person, "rationale": rationale, "evidence": evidence,
            "corrected_candidate": corrected_candidate, "identity_resolutions": identity_resolutions or {},
            "regulation_confirmations": regulation_confirmations or [],
        })
        if (request.outcome == "corrected") != (request.corrected_candidate is not None):
            raise ValueError("A correction requires exactly one corrected candidate")
        if request.corrected_candidate is not None:
            parse_candidate(request.corrected_candidate)
        queue = self._queue()
        item = next(entry for entry in queue["items"] if entry["id"] == item_id)
        decision = {
            "id": str(uuid4()), "itemId": item_id, "outcome": request.outcome,
            "person": request.person, "rationale": request.rationale, "evidence": request.evidence,
            "proposedAt": datetime.now(UTC).isoformat(),
            "candidate": item["candidate"], "baselineVersion": item["baselineVersion"],
            "preview": item["preview"], "correctedCandidate": request.corrected_candidate,
            "identityResolutions": request.identity_resolutions,
            "regulationConfirmations": request.regulation_confirmations,
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

    def _accepted_candidate(self, item: dict) -> tuple[dict, PublicationCandidate]:
        decision_id = item.get("acceptedDecision")
        if not decision_id:
            raise ValueError("An accepted decision is required")
        decision = yaml.safe_load((self.directory / "decisions" / f"{decision_id}.yaml").read_text("utf-8"))
        if decision["outcome"] != "accepted" or decision["itemId"] != item["id"]:
            raise ValueError("An accepted decision for this item is required")
        if decision["candidate"] != item["candidate"] or decision["baselineVersion"] != item["baselineVersion"]:
            raise ValueError("The accepted candidate or baseline has changed")
        current = self._preview(item["candidate"])
        envelope = parse_candidate(item["candidate"])
        if current["baselineVersion"] not in (item["baselineVersion"], publication_version(envelope)):
            raise ValueError("Publication baseline is stale; preview and review again")
        preview = current["preview"]
        if preview["validationErrors"] or preview["conflicts"] or decision["preview"]["conflicts"]:
            raise ValueError("Candidate has validation errors or publication conflicts")
        required = decision["preview"].get("regulationConfirmations", [])
        if not set(required).issubset(decision.get("regulationConfirmations", [])):
            raise ValueError("Explicit regulation evidence, translation and identity confirmation is required")
        if isinstance(envelope, PublicationSnapshot):
            for bundle in envelope.regulations:
                if any(passage.translation and passage.translation.review_state != "accepted" for passage in bundle.passages):
                    raise ValueError("Regulation translations require explicit accepted human review")
        for field in set(preview["unresolvedIdentities"] + decision["preview"]["unresolvedIdentities"]):
            if not isinstance(envelope, CandidateEnvelope):
                source_id, identity_field = field.rsplit("/", 1)
                entry = next((entry for entry in candidate_meetings(envelope) if entry.source_identity == source_id), None)
                identity = getattr(entry.meeting, identity_field, None) if entry else None
            else:
                identity = item["candidate"]["meeting"].get(field)
            if not identity or decision["identityResolutions"].get(field) != identity:
                raise ValueError("Candidate has unresolved identities")
        return decision, envelope

    @staticmethod
    def _digest(value: dict) -> str:
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    def _queue(self) -> dict:
        return _read_queue(self.directory)

    @staticmethod
    def _write(path: Path, data: dict) -> None:
        temporary = path.with_suffix(f".{uuid4()}.tmp")
        temporary.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), "utf-8")
        temporary.replace(path)

    def _preview(self, candidate: dict) -> dict:
        baseline_version = self.store.current_publication_version()
        baseline = self.store.publication_envelope(baseline_version) if baseline_version else None
        errors = []
        try:
            candidate = parse_candidate(candidate).model_dump(mode="json")
        except ValidationError as error:
            errors = [f"{'.'.join(map(str, entry['loc']))}: {entry['msg']}" for entry in error.errors()]
        if "meetings" in candidate or "seasons" in candidate or (baseline is not None and not isinstance(baseline, CandidateEnvelope)):
            return self._season_preview(candidate, baseline, baseline_version, errors)
        source_identity = candidate.get("source_identity")
        same_meeting = baseline is not None and source_identity == baseline.source_identity
        previous = baseline.meeting.model_dump(mode="json") if same_meeting else {}
        proposed = candidate.get("meeting")
        if not isinstance(proposed, dict):
            proposed = {}
        changes = {
            field: {"before": previous.get(field), "after": value}
            for field, value in proposed.items()
            if previous.get(field) != value
        } if same_meeting else {}
        old_envelope = baseline.model_dump(mode="json") if same_meeting else {}
        for field in ("source_identity", "source_url", "retrieved_at", "evidence"):
            if same_meeting and old_envelope.get(field) != candidate.get(field):
                changes[field] = {"before": old_envelope.get(field), "after": candidate.get(field)}
        unresolved = [
            field for field in ("competition_identity", "circuit_identity")
            if not proposed.get(field) or (same_meeting and previous[field] != proposed.get(field))
        ]
        conflicts = []
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

    def _season_preview(self, candidate: dict, baseline: PublicationCandidate | None, baseline_version: str | None, errors: list) -> dict:
        previous = {entry.source_identity: entry.model_dump(mode="json") for entry in candidate_meetings(baseline)} if baseline else {}
        proposed = {}
        if not errors:
            proposed = {entry.source_identity: entry.model_dump(mode="json") for entry in candidate_meetings(parse_candidate(candidate))}
        conflicts = []
        if "meetings" not in candidate and "seasons" not in candidate:
            conflicts.append("A season publication requires a complete season candidate")
        if not errors:
            missing = sorted(set(previous) - set(proposed))
            if missing:
                conflicts.append("Missing published Meetings; retain them with explicit sourced cancellation: " + ", ".join(missing))
        changes = {}
        regulation_confirmations = []
        previous_regulations = {f"{entry.competition_identity}:{entry.season_year}": entry.model_dump(mode="json") for entry in baseline.regulations} if isinstance(baseline, PublicationSnapshot) else {}
        next_regulations = {f"{entry['competition_identity']}:{entry['season_year']}": entry for entry in candidate.get("regulations", [])} if not errors else {}
        for scope in previous_regulations.keys() | next_regulations.keys():
            before, after = previous_regulations.get(scope), next_regulations.get(scope)
            if before != after:
                changes["regulations/" + scope] = {"before": before, "after": after}
                regulation_confirmations.append("regulations/" + scope + "/" + self._digest({"before": before, "after": after}))
                if after is None:
                    conflicts.append("Missing published regulation profile: " + scope)
        unresolved = [
            f"{identity}/circuit_identity" for identity in sorted(set(proposed) - set(previous))
            if proposed[identity]["meeting"]["competition_identity"] in ("gt-world-challenge-europe", "nls")
        ]
        for identity in previous.keys() & proposed.keys():
            before, after = previous[identity], proposed[identity]
            prior_observations = sum(assertion["field"] == "timetable" for assertion in before.get("field_assertions", []))
            next_observations = sum(assertion["field"] == "timetable" for assertion in after.get("field_assertions", []))
            if next_observations < prior_observations:
                conflicts.append("Missing published timetable observations; retain the evidence or provide a corrected candidate: " + identity)
            prior_sessions = {session["identity"] for session in before["meeting"].get("sessions", [])}
            next_sessions = {session["identity"] for session in after["meeting"].get("sessions", [])}
            prior_rounds = {entry["identity"] for entry in before["meeting"].get("rounds", [])}
            next_rounds = {entry["identity"] for entry in after["meeting"].get("rounds", [])}
            if prior_rounds - next_rounds:
                conflicts.append("Missing published Rounds; retain their identities and sourced status: " + ", ".join(sorted(prior_rounds - next_rounds)))
            if prior_sessions - next_sessions:
                conflicts.append("Missing published Sessions; retain them with explicit sourced cancellation: " + ", ".join(sorted(prior_sessions - next_sessions)))
            fields = {key: {"before": before["meeting"].get(key), "after": after["meeting"].get(key)} for key in before["meeting"].keys() | after["meeting"].keys() if before["meeting"].get(key) != after["meeting"].get(key)}
            for field in ("source_url", "retrieved_at", "evidence", "field_assertions"):
                if before.get(field) != after.get(field):
                    fields[field] = {"before": before.get(field), "after": after.get(field)}
            if fields:
                changes[identity] = fields
            for field in ("competition_identity", "circuit_identity"):
                if before["meeting"][field] != after["meeting"][field]:
                    unresolved.append(f"{identity}/{field}")
            if before["meeting"]["competition_identity"] != after["meeting"]["competition_identity"] or before["meeting"]["season_year"] != after["meeting"]["season_year"]:
                conflicts.append("Published Competition/Season identity cannot be replaced")
        return {
            "id": str(uuid4()), "createdAt": datetime.now(UTC).isoformat(), "status": "open",
            "baselineVersion": baseline_version, "candidate": candidate,
            "preview": {
                "additions": sorted(set(proposed) - set(previous)), "changes": changes,
                "cancellations": [identity for identity, entry in proposed.items() if entry["meeting"]["status"] == "cancelled" and previous.get(identity, {}).get("meeting", {}).get("status") != "cancelled"],
                "conflicts": conflicts, "unresolvedIdentities": unresolved, "validationErrors": errors,
                "regulationConfirmations": regulation_confirmations,
            },
        }