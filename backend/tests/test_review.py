from pathlib import Path

import yaml
import pytest

from app.publication import CandidateEnvelope, InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule
from app.review import ReviewService


def candidate() -> dict:
    return CandidateEnvelope.model_validate_json(
        (Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8")
    ).model_dump(mode="json")


def test_preview_changes_and_unresolved_identity_without_publication(tmp_path) -> None:
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    publisher.publish(CandidateEnvelope.model_validate(candidate()))
    previous = store.visible_meetings()
    update = candidate()
    update["meeting"]["end_date"] = "2026-03-09"
    update["meeting"]["circuit_identity"] = "unknown-circuit"

    item = ReviewService(tmp_path, store, publisher).preview(update)

    assert item["preview"]["changes"]["end_date"] == {"before": "2026-03-08", "after": "2026-03-09"}
    assert item["preview"]["unresolvedIdentities"] == ["circuit_identity"]
    assert item["status"] == "open"
    assert store.visible_meetings() == previous


def test_preview_persists_cancellation_and_invalid_identity_in_queue(tmp_path) -> None:
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    publisher.publish(CandidateEnvelope.model_validate(candidate()))
    service = ReviewService(tmp_path, store, publisher)
    update = candidate()
    update["meeting"]["status"] = "cancelled"
    cancelled = service.preview(update)
    assert cancelled["preview"]["cancellations"] == ["f1:2026:australia"]

    del update["meeting"]["circuit_identity"]
    invalid = service.preview(update)
    assert invalid["preview"]["validationErrors"]
    assert "circuit_identity" in invalid["preview"]["unresolvedIdentities"]
    queue = yaml.safe_load((tmp_path / "queue.yaml").read_text("utf-8"))
    assert [item["id"] for item in queue["items"]] == [cancelled["id"], invalid["id"]]
    assert ReviewService(tmp_path, store, publisher).show(invalid["id"])["status"] == "open"


@pytest.mark.parametrize("outcome", ["accepted", "rejected", "corrected", "deferred"])
def test_exact_decision_is_confirmed_and_audited_before_any_publication(tmp_path, outcome) -> None:
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    service = ReviewService(tmp_path, store, publisher)
    item = service.preview(candidate())
    corrected = candidate() if outcome == "corrected" else None
    proposal = service.propose_decision(
        item["id"], outcome, "Test Operator", "Checked against the official source",
        ["https://www.formula1.com/en/racing/2026/australia"], corrected_candidate=corrected,
    )
    assert proposal["decision"]["outcome"] == outcome
    assert proposal["decision"]["candidate"] == candidate()
    with pytest.raises(ValueError, match="confirmation"):
        service.record_decision(item["id"], "wrong")
    assert not list((tmp_path / "decisions").glob("*.yaml"))

    decision = service.record_decision(item["id"], proposal["confirmation"])

    assert decision["person"] == "Test Operator"
    assert decision["rationale"] == "Checked against the official source"
    assert decision["evidence"] == ["https://www.formula1.com/en/racing/2026/australia"]
    assert decision["decidedAt"]
    assert yaml.safe_load((tmp_path / "decisions" / f"{decision['id']}.yaml").read_text("utf-8")) == decision
    assert store.visible_meetings() == []
    if outcome != "rejected":
        assert service.show(item["id"])["status"] == "open"


def accept(service, item):
    proposal = service.propose_decision(
        item["id"], "accepted", "Test Operator", "Verified the evidence",
        [item["candidate"]["source_url"]],
    )
    return service.record_decision(item["id"], proposal["confirmation"])


def test_only_accepted_revision_with_separate_publication_confirmation_can_publish(tmp_path) -> None:
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    item = service.preview(candidate())
    with pytest.raises(ValueError, match="accepted"):
        service.propose_publication(item["id"])
    decision = accept(service, item)
    proposal = service.propose_publication(item["id"])
    assert proposal["decisionId"] == decision["id"]
    assert store.visible_meetings() == []
    with pytest.raises(ValueError, match="confirmation"):
        service.publish(item["id"], "wrong")
    result = service.publish(item["id"], proposal["confirmation"])
    assert store.visible_meetings()[0]["publicationVersion"] == result["version"]
    assert yaml.safe_load((tmp_path / "queue.yaml").read_text("utf-8"))["items"] == []
    receipt = yaml.safe_load((tmp_path / "publications" / f"{decision['id']}.yaml").read_text("utf-8"))
    assert receipt["version"] == result["version"]


@pytest.mark.parametrize("failure", ["validation", "projection", "stale", "unresolved", "replacement"])
def test_failed_publication_keeps_review_open_and_previous_version_visible(tmp_path, monkeypatch, failure) -> None:
    store = InMemoryOperationalStore()
    graph = InMemoryGraphProjection()
    publisher = PublicationModule(store, graph)
    publisher.publish(CandidateEnvelope.model_validate(candidate()))
    service = ReviewService(tmp_path, store, publisher)
    update = candidate()
    update["meeting"]["end_date"] = "2026-03-09"
    if failure == "validation":
        update["meeting"]["start_date"] = "2026-03-10"
    elif failure == "unresolved":
        update["meeting"]["circuit_identity"] = "unresolved"
    elif failure == "replacement":
        update["source_identity"] = "f1:2026:china"
    item = service.preview(update)
    accept(service, item)
    if failure == "stale":
        newer = candidate()
        newer["evidence"] = "Newer approved source assertion"
        publisher.publish(CandidateEnvelope.model_validate(newer))
    if failure == "projection":
        monkeypatch.setattr(graph, "agrees", lambda *_: False)
    previous = store.visible_meetings()
    with pytest.raises((ValueError, RuntimeError)):
        proposal = service.propose_publication(item["id"])
        service.publish(item["id"], proposal["confirmation"])
    assert service.show(item["id"])["status"] == "open"
    assert store.visible_meetings() == previous


def test_preview_includes_provenance_changes_and_rejects_invalid_source(tmp_path) -> None:
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    publisher.publish(CandidateEnvelope.model_validate(candidate()))
    service = ReviewService(tmp_path, store, publisher)
    update = candidate()
    update["evidence"] = "Corrected official announcement"
    item = service.preview(update)
    assert item["preview"]["changes"]["evidence"]["after"] == "Corrected official announcement"
    update["source_url"] = "javascript:alert(1)"
    update["meeting"]["circuit_identity"] = " "
    invalid = service.preview(update)
    assert len(invalid["preview"]["validationErrors"]) == 2


def test_concurrent_queue_writer_is_refused(tmp_path) -> None:
    from filelock import FileLock, Timeout

    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    with FileLock(tmp_path / ".review.lock"):
        with pytest.raises(Timeout):
            service.preview(candidate())
    assert not (tmp_path / "queue.yaml").exists()


def test_approved_cancellation_is_visible_with_original_identity(tmp_path) -> None:
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    publisher.publish(CandidateEnvelope.model_validate(candidate()))
    update = candidate()
    update["meeting"]["status"] = "cancelled"
    service = ReviewService(tmp_path, store, publisher)
    item = service.preview(update)
    accept(service, item)
    service.publish(item["id"], service.propose_publication(item["id"])["confirmation"])
    assert store.visible_meetings()[0]["status"] == "cancelled"
    assert store.visible_meetings()[0]["id"] == "meeting:f1:2026:australia"


def test_baseline_change_after_publication_confirmation_cannot_be_overwritten(tmp_path, monkeypatch) -> None:
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    publisher.publish(CandidateEnvelope.model_validate(candidate()))
    service = ReviewService(tmp_path, store, publisher)
    revised = candidate()
    revised["meeting"]["end_date"] = "2026-03-09"
    item = service.preview(revised)
    accept(service, item)
    proposal = service.propose_publication(item["id"])
    newer = candidate()
    newer["evidence"] = "Independently reviewed newer assertion"
    publisher.publish(CandidateEnvelope.model_validate(newer))
    previous = store.visible_meetings()
    with pytest.raises(ValueError, match="stale"):
        service.publish(item["id"], proposal["confirmation"])
    assert store.visible_meetings() == previous


def test_retry_after_receipt_write_failure_finishes_without_republication(tmp_path, monkeypatch) -> None:
    store = InMemoryOperationalStore()
    graph = InMemoryGraphProjection()
    publisher = PublicationModule(store, graph)
    publisher.publish(CandidateEnvelope.model_validate(candidate()))
    service = ReviewService(tmp_path, store, publisher)
    update = candidate()
    update["evidence"] = "Reviewed correction"
    item = service.preview(update)
    accept(service, item)
    proposal = service.propose_publication(item["id"])
    original_replace = Path.replace

    def fail_receipt(path, destination):
        if destination.parent.name == "publications":
            raise OSError("Receipt write interrupted")
        return original_replace(path, destination)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", fail_receipt)
        with pytest.raises(OSError):
            service.publish(item["id"], proposal["confirmation"])
    published = store.visible_meetings()
    assert service.show(item["id"])["status"] == "open"

    def fail_projection(*args):
        raise RuntimeError("Must not republish an already promoted version")

    monkeypatch.setattr(graph, "project", fail_projection)
    service.publish(item["id"], proposal["confirmation"])
    assert store.visible_meetings() == published
    assert yaml.safe_load((tmp_path / "queue.yaml").read_text("utf-8"))["items"] == []


def test_initial_fixture_cannot_replace_a_reviewed_publication(tmp_path) -> None:
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    publisher.publish_initial(CandidateEnvelope.model_validate(candidate()))
    service = ReviewService(tmp_path, store, publisher)
    update = candidate()
    update["meeting"]["status"] = "cancelled"
    item = service.preview(update)
    accept(service, item)
    service.publish(item["id"], service.propose_publication(item["id"])["confirmation"])
    previous = store.visible_meetings()
    publisher.publish_initial(CandidateEnvelope.model_validate(candidate()))
    assert store.visible_meetings() == previous


def test_correction_requires_new_acceptance_before_publication(tmp_path) -> None:
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    item = service.preview(candidate())
    corrected = candidate()
    corrected["meeting"]["end_date"] = "2026-03-09"
    proposal = service.propose_decision(
        item["id"], "corrected", "Operator", "Corrected date from the source",
        [corrected["source_url"]], corrected_candidate=corrected,
    )
    service.record_decision(item["id"], proposal["confirmation"])
    with pytest.raises(ValueError, match="accepted"):
        service.propose_publication(item["id"])
    refreshed = service.show(item["id"])
    assert refreshed["candidate"]["meeting"]["end_date"] == "2026-03-09"
    accept(service, refreshed)
    service.publish(item["id"], service.propose_publication(item["id"])["confirmation"])
    assert store.visible_meetings()[0]["endDate"] == "2026-03-09"


def test_changed_identity_requires_exact_human_resolution(tmp_path) -> None:
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    publisher.publish(CandidateEnvelope.model_validate(candidate()))
    service = ReviewService(tmp_path, store, publisher)
    update = candidate()
    update["meeting"]["circuit_identity"] = "approved-replacement"
    item = service.preview(update)
    for identity in ("different-identity", "approved-replacement"):
        proposal = service.propose_decision(
            item["id"], "accepted", "Operator", "Explicit circuit identity resolution",
            [update["source_url"]], identity_resolutions={"circuit_identity": identity},
        )
        service.record_decision(item["id"], proposal["confirmation"])
        if identity == "different-identity":
            with pytest.raises(ValueError, match="unresolved"):
                service.propose_publication(item["id"])
        else:
            service.publish(item["id"], service.propose_publication(item["id"])["confirmation"])
    version = store.visible_meetings()[0]["publicationVersion"]
    assert store.publication_envelope(version).meeting.circuit_identity == "approved-replacement"


def test_recorded_decision_survives_interrupted_queue_update(tmp_path, monkeypatch) -> None:
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    item = service.preview(candidate())
    proposal = service.propose_decision(
        item["id"], "accepted", "Operator", "Evidence checked", [candidate()["source_url"]],
    )
    original_replace = Path.replace

    def fail_queue(path, destination):
        if destination.name == "queue.yaml":
            raise OSError("Queue write interrupted")
        return original_replace(path, destination)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", fail_queue)
        with pytest.raises(OSError):
            service.record_decision(item["id"], proposal["confirmation"])
    records = list((tmp_path / "decisions").glob("*.yaml"))
    assert len(records) == 1
    recorded = records[0].read_bytes()
    service.record_decision(item["id"], proposal["confirmation"])
    assert records[0].read_bytes() == recorded
    assert service.propose_publication(item["id"])["decisionId"] == proposal["decision"]["id"]