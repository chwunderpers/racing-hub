import json
from pathlib import Path

from app.formula_one import adapt_season, race_payload
from app.publication import InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule, publication_version
from app.review import ReviewService
from datetime import UTC, datetime
import httpx
import pytest


def source_fixture():
    return json.loads((Path(__file__).parents[1] / "fixtures/f1-2026-source.json").read_text("utf-8"))


def test_official_fixture_produces_complete_season_with_sourced_session_instants():
    candidate = adapt_season(source_fixture())

    assert len(candidate.meetings) == 23
    assert sum(len(entry.meeting.sessions) for entry in candidate.meetings) == 115
    australia = candidate.meetings[0]
    assert australia.source_identity == "f1:2026:australia"
    assert australia.meeting.sessions[0].start.instant.isoformat() == "2026-03-06T01:30:00+00:00"
    sepang = candidate.meetings[15].meeting
    assert sepang.circuit_name == "Sepang International Circuit"
    assert sepang.event_timezone == "Asia/Kuala_Lumpur"


@pytest.mark.parametrize("offset,zone", [(None, "Australia/Melbourne"), ("+08:00", "Australia/Melbourne")])
def test_unresolved_or_contradictory_clock_never_invents_an_instant(offset, zone):
    source = source_fixture()
    session = source["meetings"][0]["race"]["meetingSessions"][0]
    session.update(gmtOffset=offset, timezone=zone)
    start = adapt_season(source).meetings[0].meeting.sessions[0].start
    assert start.local == "2026-03-06T12:30:00"
    assert start.instant is None


def publish_reviewed(service, candidate):
    item = service.preview(candidate.model_dump(mode="json"))
    assert not item["preview"]["validationErrors"]
    proposal = service.propose_decision(item["id"], "accepted", "Test Operator", "Verified season fixture", [candidate.source_url])
    service.record_decision(item["id"], proposal["confirmation"])
    publication = service.propose_publication(item["id"])
    return service.publish(item["id"], publication["confirmation"])


@pytest.mark.parametrize("real", [False, True])
def test_reviewed_season_has_one_version_and_failed_revision_preserves_it(tmp_path, request, monkeypatch, real):
    store, graph = request.getfixturevalue("isolated_services") if real else (InMemoryOperationalStore(), InMemoryGraphProjection())
    service = ReviewService(tmp_path / "reviews", store, PublicationModule(store, graph))
    candidate = adapt_season(source_fixture())
    result = publish_reviewed(service, candidate)
    visible = store.visible_meetings()
    assert len(visible) == 23
    assert sum(len(meeting["sessions"]) for meeting in visible) == 115
    assert {meeting["publicationVersion"] for meeting in visible} == {result["version"]}
    assert graph.agrees(result["version"], "meeting:f1:2026:australia", candidate)
    assert store.publication_envelope(result["version"]) == candidate
    revised = candidate.model_copy(deep=True)
    revised.meetings[0].meeting.status = "cancelled"
    monkeypatch.setattr(graph, "agrees", lambda *_: False)
    with pytest.raises(RuntimeError, match="does not agree"):
        publish_reviewed(service, revised)
    assert store.visible_meetings() == visible


def test_fetch_failure_marks_existing_publication_stale_without_replacing_it(tmp_path):
    from app.source_workflow import fetch_for_review
    from app.main import app, operational_store
    from fastapi.testclient import TestClient

    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    publish_reviewed(service, adapt_season(source_fixture()))
    previous = store.visible_meetings()
    def unavailable(request):
        return httpx.Response(503)
    with httpx.Client(transport=httpx.MockTransport(unavailable)) as client:
        result = fetch_for_review(2026, client, store, service, datetime(2026, 9, 10, tzinfo=UTC))
    assert result["status"] == "failed"
    assert store.visible_meetings() == previous
    app.dependency_overrides[operational_store] = lambda: store
    try:
        with TestClient(app) as client:
            response = client.get("/api/schedule").json()
        assert len(response["meetings"]) == 23
        assert response["freshness"]["stale"] is True
        assert response["freshness"]["reason"] == "Source fetch failed"
        assert len(response["meetings"][0]["sessions"]) == 5
    finally:
        app.dependency_overrides.clear()


def source_transport(source):
    def respond(request):
        if str(request.url) == source["source_url"]:
            html = "".join(f'<a href="{entry["source_url"].replace("https://www.formula1.com", "")}"><span>ROUND {entry["race"]["meetingNumber"]}</span></a>' for entry in source["meetings"])
        else:
            entry = next(entry for entry in source["meetings"] if entry["source_url"] == str(request.url))
            flight = "0:T2,\u00e9" + "1:" + json.dumps({"children": {"pageData": {"race": entry["race"]}}}) + "\n"
            html = "<script>self.__next_f.push(" + json.dumps([1, flight]) + ")</script>"
        return httpx.Response(200, text=html, headers={"Content-Type": "text/html"})
    return httpx.MockTransport(respond)


def test_repeat_retrieval_is_not_a_revision_and_never_publishes(tmp_path):
    from app.source_workflow import fetch_for_review
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    source = source_fixture()
    with httpx.Client(transport=source_transport(source)) as client:
        result = fetch_for_review(2026, client, store, service)
        assert result["status"] == "pending-review"
        assert store.visible_meetings() == []
        publish_reviewed(service, adapt_season(source))
        before = store.visible_meetings()
        repeat = fetch_for_review(2026, client, store, service)
        assert repeat["status"] == "unchanged"
        assert store.visible_meetings() == before
        assert store.source_freshness()["stale"] is False


def test_season_review_rejects_silent_removal_of_a_published_meeting(tmp_path):
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    candidate = adapt_season(source_fixture())
    publish_reviewed(service, candidate)
    candidate.meetings.pop()
    item = service.preview(candidate.model_dump(mode="json"))
    assert "Missing published Meetings" in item["preview"]["conflicts"][0]


def test_schedule_api_retains_nullable_clock_fields(tmp_path):
    from app.main import app, operational_store
    from fastapi.testclient import TestClient
    source = source_fixture()
    source["meetings"][0]["race"]["meetingSessions"][0]["gmtOffset"] = None
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    publish_reviewed(service, adapt_season(source))
    app.dependency_overrides[operational_store] = lambda: store
    try:
        with TestClient(app) as client:
            start = client.get("/api/schedule").json()["meetings"][0]["sessions"][0]["start"]
        assert start["offset"] is None
        assert start["instant"] is None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("mutation", ["duplicate", "unknown-state", "invalid-date", "missing-id", "truncated", "invalid-offset"])
def test_adapter_rejects_untrustworthy_schedule_records(mutation):
    source = source_fixture()
    if mutation == "duplicate":
        source["meetings"].append(source["meetings"][0])
    elif mutation == "unknown-state":
        source["meetings"][0]["race"]["meetingSessions"][0]["state"] = "guess"
    elif mutation == "invalid-date":
        source["meetings"][0]["race"]["meetingSessions"][0]["startTime"] = "tomorrow"
    elif mutation == "missing-id":
        source["meetings"][0]["race"]["meetingSessions"][0]["meetingSessionKey"] = None
    elif mutation == "invalid-offset":
        source["meetings"][0]["race"]["meetingSessions"][0]["gmtOffset"] = "+10:99"
    else:
        source["meetings"].pop()
    with pytest.raises(ValueError):
        adapt_season(source)