from pathlib import Path
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from rdflib import Graph, RDF

from app.publication import ScheduledEnvelope, meeting_view


def qualifiers():
    return {
        "source_identity": "nls:2026:qualifiers",
        "source_url": "https://www.nuerburgring-langstrecken-serie.de/language/en/2026/04/15/back-to-back-the-first-double-header-of-the-year/",
        "retrieved_at": "2026-09-10T10:38:33Z", "source_language": "en",
        "evidence": "Qualifiers programme April 17-19; Rounds 4 and 5.",
        "meeting": {
            "competition_identity": "nls", "competition_name": "NLS",
            "season_year": 2026, "circuit_identity": "nls:nordschleife-combined",
            "meeting_name": "NLS Qualifiers", "circuit_name": "Nordschleife combined course",
            "start_date": "2026-04-17", "end_date": "2026-04-19", "round_number": None,
            "rounds": [
                {"identity": "nls:2026:round:4", "number": 4, "name": "Qualifiers first race", "status": "abandoned"},
                {"identity": "nls:2026:round:5", "number": 5, "name": "Qualifiers second race", "status": "scheduled"},
            ],
            "sessions": [{
                "identity": "nls:2026:round:4:race", "name": "Race", "status": "abandoned",
                "round_identity": "nls:2026:round:4", "duration_minutes": 240,
                "start": {"local": "2026-04-18T17:30"}, "end": None,
            }],
        },
    }


def test_double_header_preserves_round_membership_and_abandonment_without_estimated_finish():
    candidate = ScheduledEnvelope.model_validate(qualifiers())
    view = meeting_view(candidate)
    assert [entry["number"] for entry in view["rounds"]] == [4, 5]
    assert view["round"] is None
    session = view["sessions"][0]
    assert session["roundId"] == "nls:2026:round:4"
    assert session["status"] == "abandoned"
    assert session["durationMinutes"] == 240
    assert session["start"]["instant"] is None
    assert session["end"] is None


def test_nls_place_and_coverage_survive_publication_api_and_graph(tmp_path, monkeypatch):
    from app.main import app, operational_store
    from app.publication import InMemoryOperationalStore, PublicationModule, SeasonCandidateEnvelope
    from app.stores import GraphDbProjection, MOTORSPORT
    source = qualifiers()
    source["meeting"].update(
        venue={"identity": "nuerburgring", "name": "Nuerburgring"},
        layout={"identity": "nls:qualifiers:2026", "name": "Qualifiers route 2026", "length_km": 25.378},
        coverage={"state": "incomplete", "activity": "present", "reason": "Friday timetable unverified", "source_url": source["source_url"]},
    )
    season = SeasonCandidateEnvelope.model_validate({
        "source_identity": "nls:2026", "source_url": source["source_url"],
        "retrieved_at": source["retrieved_at"], "source_language": "en",
        "competition_identity": "nls", "season_year": 2026, "meetings": [source],
        "coverage": {"state": "incomplete", "activity": "present", "reason": "Detailed timetables unverified", "source_url": source["source_url"]},
    })
    projected = Graph()
    def put(url, **kwargs):
        projected.parse(data=kwargs["content"], format="turtle")
        return httpx.Response(204, request=httpx.Request("PUT", url))
    def get(url, **kwargs):
        return httpx.Response(200, text=projected.serialize(format="nt"), request=httpx.Request("GET", url))
    monkeypatch.setattr(httpx, "put", put)
    monkeypatch.setattr(httpx, "get", get)
    store = InMemoryOperationalStore()
    PublicationModule(store, GraphDbProjection("http://unused", "unused", Path("unused"))).publish(season)
    app.dependency_overrides[operational_store] = lambda: store
    try:
        response = TestClient(app).get("/api/schedule")
        assert response.status_code == 200
        data = response.json()
        assert data["coverage"][0]["state"] == "incomplete"
        meeting = data["meetings"][0]
        assert meeting["layout"]["length_km"] == 25.378
        assert meeting["venue"]["name"] == "Nuerburgring"
        assert meeting["coverage"]["state"] == "incomplete"
        assert meeting["rounds"][0]["status"] == "abandoned"
        assert meeting["sessions"][0]["durationMinutes"] == 240
    finally:
        app.dependency_overrides.clear()
    assert len(list(projected.subjects(RDF.type, MOTORSPORT.Round))) == 2
    assert len(list(projected.subjects(RDF.type, MOTORSPORT.Venue))) == 1
    assert len(list(projected.subjects(RDF.type, MOTORSPORT.Layout))) == 1
    assert len(list(projected.triples((None, MOTORSPORT.round, None)))) == 1


def test_explicit_empty_season_is_distinct_from_unassessed_coverage():
    from app.publication import InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule, SeasonCandidateEnvelope, coverage_view
    value = {
        "source_identity": "synthetic:empty", "source_url": "https://example.org/calendar",
        "retrieved_at": "2026-09-10T11:00:00Z", "source_language": "en",
        "competition_identity": "synthetic", "season_year": 2026, "meetings": [],
        "coverage": {"state": "complete", "activity": "empty", "reason": "Official notice: no scheduled activity in this scope", "source_url": "https://example.org/calendar"},
    }
    candidate = SeasonCandidateEnvelope.model_validate(value)
    store = InMemoryOperationalStore()
    result = PublicationModule(store, InMemoryGraphProjection()).publish(candidate)
    assert store.visible_meetings() == []
    assert coverage_view(store.publication_envelope(result.version))[0]["activity"] == "empty"
    value["coverage"]["state"] = "unassessed"
    with pytest.raises(ValueError):
        SeasonCandidateEnvelope.model_validate(value)


def nls_source():
    return json.loads((Path(__file__).parents[1] / "fixtures/nls-2026-source.json").read_text("utf-8"))


def test_verified_nls_inventory_preserves_groups_tests_status_and_partial_coverage():
    from app.nls import adapt_season
    candidate = adapt_season(nls_source())
    assert len(candidate.meetings) == 15
    championship = [entry for entry in candidate.meetings if entry.meeting.kind == "championship"]
    assert len(championship) == 8
    assert sorted(round.number for entry in championship for round in entry.meeting.rounds) == list(range(1, 11))
    assert sum(len(entry.meeting.sessions) for entry in championship) == 21
    tests = [entry for entry in candidate.meetings if entry.meeting.kind == "test"]
    assert len(tests) == 7
    assert sum(len(entry.meeting.sessions) for entry in tests) == 10
    mixed_test = next(entry for entry in tests if entry.meeting.start_date.isoformat() == "2026-06-19")
    assert [session.circuit_identity for session in mixed_test.meeting.sessions] == ["nls:gp-sprint", "nls:nordschleife-combined"]
    assert mixed_test.meeting.sessions[0].layout.identity == "nls:sprint:2026-unverified"
    rounds = {round.number: round for entry in championship for round in entry.meeting.rounds}
    assert rounds[1].status == "cancelled"
    assert rounds[4].status == "abandoned"
    meetings = {entry.source_identity: entry for entry in candidate.meetings}
    assert meetings["nls:2026:round-2"].meeting.start_date.isoformat() == "2026-03-21"
    assert meetings["nls:2026:qualifiers"].meeting.layout.length_km == 25.378
    assert meetings["nls:2026:round-7"].meeting.sessions[-1].duration_minutes == 360
    assert meetings["nls:2026:round-7"].meeting.layout.length_km is None
    assert all(session.start.instant is None for entry in candidate.meetings for session in entry.meeting.sessions)
    assert candidate.coverage.state == "incomplete"
    assert any(assertion.field == "status" and "not resumed" in assertion.value for assertion in meetings["nls:2026:qualifiers"].field_assertions)
    assert any(assertion.translation and assertion.translation.review_state == "accepted-standing-poc" for entry in championship for assertion in entry.field_assertions)


@pytest.mark.parametrize("mutation", ["missing-round", "duplicate-round", "unknown-date", "unknown-source", "missing-period"])
def test_nls_adapter_rejects_changed_inventory_instead_of_publishing_empty(mutation):
    from app.nls import adapt_season
    source = nls_source()
    if mutation == "missing-round":
        source["rounds"].pop()
    elif mutation == "duplicate-round":
        source["rounds"][0] = source["rounds"][1]
    elif mutation == "unknown-date":
        source["rounds"][0]["date"] = "2027-03-14"
    elif mutation == "unknown-source":
        source["rounds"][0]["source_url"] = "https://untrusted.example/race"
    else:
        source["rounds"][0]["sessions"].pop()
    with pytest.raises(ValueError):
        adapt_season(source)


def round_html():
    return '<div class="entry-content"><h2>NLS7</h2><table class="table">' + ''.join(
        f'<tr><td>{clock}</td><td>{label}</td></tr>' for clock, label in [
            ("08:30 - 10:00 Uhr", "Qualifying"), ("10:20 - 11:00 Uhr", "Pitwalk"),
            ("11:10 - 11:30 Uhr", "Gridwalk"), ("11:00 - 11:40 Uhr", "Startaufstellung"),
            ("12:00 - 18:00 Uhr", "Rennen (6 Stunden)"),
        ]) + '</table></div>'


def test_nls_html_adapter_classifies_track_periods_not_every_timetable_row():
    from app.nls import parse_round
    entry = parse_round(nls_source()["rounds"][6], round_html().encode())
    assert len(entry["sessions"]) == 2
    assert entry["sessions"][1]["duration_minutes"] == 360
    assert len(entry["ancillary"]) == 3
    assert entry["ancillary"][2]["name"] == "Grid formation"


@pytest.mark.parametrize("before,after", [("table", "changed"), ("18:00", "25:00"), ("NLS7", "NLS8"), ("Qualifying", "Unknown activity")])
def test_nls_html_adapter_rejects_unverified_structure(before, after):
    from app.nls import parse_round
    with pytest.raises(ValueError):
        parse_round(nls_source()["rounds"][6], round_html().replace(before, after).encode())


def test_nls_failed_public_fetch_preserves_last_publication_and_marks_only_nls_stale(tmp_path):
    from app.nls import adapt_season
    from app.publication import InMemoryOperationalStore, InMemoryGraphProjection, PublicationModule
    from app.review import ReviewService
    from app.source_workflow import fetch_for_review
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    original = publisher.publish(adapt_season(nls_source()))
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(403))) as client:
        result = fetch_for_review(2026, client, store, ReviewService(tmp_path, store, publisher), source_family="nls")
    assert result["status"] == "failed"
    assert store.current_publication_version() == original.version
    assert store.source_freshness()["sources"][0]["sourceFamily"] == "nls"
    assert store.source_freshness()["sources"][0]["stale"] is True


@pytest.mark.parametrize("real", [False, True])
def test_nls_combined_publication_preserves_existing_versions_and_requires_mapping_review(tmp_path, request, real):
    from app.nls import adapt_season
    from app.publication import InMemoryOperationalStore, InMemoryGraphProjection, PublicationModule, merge_season, publication_version
    from app.review import ReviewService
    from test_formula_one import source_fixture, adapt_season as f1_adapter
    from test_gt_world_challenge import gt_candidate, accept_review
    store, graph = request.getfixturevalue("isolated_services") if real else (InMemoryOperationalStore(), InMemoryGraphProjection())
    service = ReviewService(tmp_path, store, PublicationModule(store, graph))
    previous = merge_season(f1_adapter(source_fixture()), gt_candidate())
    baseline = accept_review(service, previous)
    combined = merge_season(previous, adapt_season(nls_source()))
    item = service.preview(combined.model_dump(mode="json"))
    assert len(item["preview"]["unresolvedIdentities"]) == 15
    result = accept_review(service, combined)
    assert publication_version(store.publication_envelope(baseline["version"])) == baseline["version"]
    assert len(store.visible_meetings()) == 50
    assert len(store.visible_meetings(version=baseline["version"])) == 35
    assert {entry["publicationVersion"] for entry in store.visible_meetings(version=baseline["version"])} == {baseline["version"]}
    assert sum(len(entry["sessions"]) for entry in store.visible_meetings()) == 146
    assert graph.agrees(result["version"], "meeting:nls:2026:qualifiers", combined)
    reduced = combined.model_copy(deep=True)
    nls_season = next(season for season in reduced.seasons if season.competition_identity == "nls")
    qualifiers_meeting = next(entry.meeting for entry in nls_season.meetings if entry.source_identity == "nls:2026:qualifiers")
    qualifiers_meeting.rounds.pop()
    for session in qualifiers_meeting.sessions:
        if session.round_identity == "nls:2026:round:5":
            session.round_identity = None
    item = service.preview(reduced.model_dump(mode="json"))
    assert any("Missing published Rounds" in conflict for conflict in item["preview"]["conflicts"])


def test_empty_publication_remains_the_review_baseline(tmp_path):
    from app.publication import InMemoryOperationalStore, InMemoryGraphProjection, PublicationModule, SeasonCandidateEnvelope
    from app.review import ReviewService
    source = {"source_identity": "empty:2026", "source_url": "https://example.org/calendar", "retrieved_at": "2026-09-10T11:00:00Z", "source_language": "en", "competition_identity": "empty", "season_year": 2026, "meetings": [], "coverage": {"state": "complete", "activity": "empty", "reason": "Officially no activity", "source_url": "https://example.org/calendar"}}
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    result = publisher.publish(SeasonCandidateEnvelope.model_validate(source))
    item = ReviewService(tmp_path, store, publisher).preview(source)
    assert item["baselineVersion"] == result.version