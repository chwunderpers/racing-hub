from pathlib import Path
import json

import pytest
import httpx
from rdflib import Graph, RDF

from app.publication import ScheduledEnvelope, meeting_view
from app.stores import GraphDbProjection, MOTORSPORT


def prologue():
    return {
        "source_identity": "gtwce:meeting:244",
        "source_url": "https://www.gt-world-challenge-europe.com/event/244/official-test-days",
        "retrieved_at": "2026-09-10T09:47:13Z", "source_language": "en",
        "evidence": "Official calendar: Test Day; official Meeting: Official Test Days - Prologue",
        "meeting": {
            "competition_identity": "gt-world-challenge-europe", "competition_name": "GT World Challenge Europe",
            "season_year": 2026, "circuit_identity": "gtwce:paul-ricard",
            "meeting_name": "Official Test Days - Prologue", "circuit_name": "Paul Ricard",
            "start_date": "2026-04-08", "end_date": "2026-04-09",
            "kind": "prologue", "round_number": None, "sessions": [],
        },
    }


def test_prologue_is_a_meeting_without_a_championship_round(monkeypatch):
    candidate = ScheduledEnvelope.model_validate(prologue())
    view = meeting_view(candidate)
    assert view["kind"] == "prologue"
    assert view["round"] is None
    assert view["roundId"] is None
    projection = GraphDbProjection("http://unused", "unused", Path("unused"))
    graph = Graph()
    def capture(url, **kwargs):
        graph.parse(data=kwargs["content"], format="turtle")
        return httpx.Response(204, request=httpx.Request("PUT", url))
    monkeypatch.setattr(httpx, "put", capture)
    projection.project("test", candidate)
    assert len(list(graph.subjects(RDF.type, MOTORSPORT.Meeting))) == 1
    assert not list(graph.subjects(RDF.type, MOTORSPORT.Round))


@pytest.mark.parametrize("kind,number", [("prologue", 1), ("test", 2), ("championship", None)])
def test_round_number_must_match_sporting_kind(kind, number):
    value = prologue()
    value["meeting"].update(kind=kind, round_number=number)
    with pytest.raises(ValueError):
        ScheduledEnvelope.model_validate(value)


def test_verified_gt_fixture_maps_shared_circuits_and_keeps_conflicting_prologue_assertions():
    from app.gt_world_challenge import adapt_season
    source = json.loads((Path(__file__).parents[1] / "fixtures/gtwce-2026-source.json").read_text("utf-8"))
    candidate = adapt_season(source)
    assert len(candidate.meetings) == 12
    assert sorted(entry.meeting.round_number for entry in candidate.meetings if entry.meeting.round_number) == list(range(1, 11))
    meetings = {entry.source_identity: entry for entry in candidate.meetings}
    assert meetings["gtwce:meeting:248"].meeting.circuit_identity == "f1-circuit-39"
    assert meetings["gtwce:meeting:245"].meeting.circuit_identity == "f1-circuit-7"
    test_day = meetings["gtwce:meeting:244"]
    assert test_day.meeting.kind == "prologue"
    assert test_day.meeting.round_number is None
    assert test_day.meeting.sessions == []
    assertions = test_day.field_assertions
    assert any(assertion.field == "kind" and assertion.value == "Test Day" and assertion.preferred for assertion in assertions)
    assert any(assertion.field == "kind" and "Round 1" in assertion.value and not assertion.preferred for assertion in assertions)
    assert all(assertion.source_url and assertion.locator and assertion.retrieved_at for assertion in assertions)


def gt_candidate():
    from app.gt_world_challenge import adapt_season
    return adapt_season(json.loads((Path(__file__).parents[1] / "fixtures/gtwce-2026-source.json").read_text("utf-8")))


def accept_review(service, candidate):
    from app.publication import candidate_meetings
    item = service.preview(candidate.model_dump(mode="json"))
    assert not item["preview"]["conflicts"]
    assert not item["preview"]["validationErrors"]
    identities = {f"{entry.source_identity}/circuit_identity": entry.meeting.circuit_identity for entry in candidate_meetings(candidate)}
    proposal = service.propose_decision(item["id"], "accepted", "Test Operator", "Verified test fixture and crosswalk", ["https://www.gt-world-challenge-europe.com/calendar"], identity_resolutions=identities)
    service.record_decision(item["id"], proposal["confirmation"])
    publication = service.propose_publication(item["id"])
    return service.publish(item["id"], publication["confirmation"])


@pytest.mark.parametrize("real", [False, True])
def test_combined_publication_preserves_f1_and_requires_reviewed_gt_mappings(tmp_path, request, real):
    from app.publication import InMemoryOperationalStore, InMemoryGraphProjection, PublicationModule, merge_season, publication_version
    from app.review import ReviewService
    from test_formula_one import source_fixture, adapt_season, publish_reviewed
    store, graph = request.getfixturevalue("isolated_services") if real else (InMemoryOperationalStore(), InMemoryGraphProjection())
    service = ReviewService(tmp_path, store, PublicationModule(store, graph))
    f1 = adapt_season(source_fixture())
    original = publish_reviewed(service, f1)
    before = store.visible_meetings()
    combined = merge_season(f1, gt_candidate())
    item = service.preview(combined.model_dump(mode="json"))
    assert len(item["preview"]["additions"]) == 12
    assert len(item["preview"]["unresolvedIdentities"]) == 12
    proposal = service.propose_decision(item["id"], "accepted", "Test Operator", "Missing mapping approval", ["https://www.gt-world-challenge-europe.com/calendar"])
    service.record_decision(item["id"], proposal["confirmation"])
    with pytest.raises(ValueError, match="unresolved identities"):
        service.propose_publication(item["id"])
    assert store.visible_meetings() == before
    result = accept_review(service, combined)
    visible = store.visible_meetings()
    assert len(visible) == 35
    assert sum(len(entry["sessions"]) for entry in visible) == 115
    assert {entry["publicationVersion"] for entry in visible} == {result["version"]}
    assert publication_version(store.publication_envelope(original["version"])) == original["version"]
    assert store.publication_envelope(result["version"]) == combined
    assert graph.agrees(result["version"], "meeting:f1:2026:australia", combined)
    removal = service.preview(gt_candidate().model_dump(mode="json"))
    assert any("Missing published Meetings" in conflict for conflict in removal["preview"]["conflicts"])


def test_review_blocks_loss_of_published_timetable_observations(tmp_path):
    from app.gt_world_challenge import fetch_season, adapt_season
    from app.publication import InMemoryOperationalStore, InMemoryGraphProjection, PublicationModule
    from app.review import ReviewService
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    with httpx.Client(transport=gt_transport()) as client:
        candidate = adapt_season(fetch_season(2026, client))
    accept_review(service, candidate)
    candidate.meetings[0].field_assertions = [assertion for assertion in candidate.meetings[0].field_assertions if assertion.field != "timetable"]
    item = service.preview(candidate.model_dump(mode="json"))
    assert any("Missing published timetable observations" in conflict for conflict in item["preview"]["conflicts"])


def gt_transport(mutation=None):
    source = json.loads((Path(__file__).parents[1] / "fixtures/gtwce-2026-source.json").read_text("utf-8"))
    def respond(request):
        if str(request.url) == source["source_url"]:
            entries = source["meetings"][:-1] if mutation == "missing" else source["meetings"]
            markup = '<h1>2026 Calendar</h1>' + ''.join(
                f'<div class="past-events__list-item"><a href="/event/{entry["id"]}/{entry["slug"]}">Event</a><span class="past-events__piped-list-span">{entry["classification"]}</span></div>' for entry in entries
            )
            if mutation == "season":
                markup = markup.replace("2026 Calendar", "2027 Calendar")
            markup = markup.replace("n%C3%BCrburgring", "n\u00fcrburgring")
        else:
            if mutation == "blocked":
                return httpx.Response(403)
            entry = next(entry for entry in source["meetings"] if f'/event/{entry["id"]}/' in request.url.path)
            event = {"@type": "Event", "name": entry["name"], "startDate": entry["start"], "endDate": entry["end"], "description": entry.get("description", "Calendar description"), "performer": {"name": "Endurance"}, "location": {"name": entry["place"], "address": {"streetAddress": "Source street"}}}
            markup = '<script type="application/ld+json">' + json.dumps(event) + '</script>'
            markup += '<table class="timetable__table"><caption class="timetable__caption">Thursday, 1 October</caption><thead><tr><th>Session</th><th>Local Time</th><th>GMT</th></tr></thead><tbody><tr><td></td><td>13:30</td><td>11:30</td></tr></tbody></table>'
            if mutation == "no-timetable":
                markup = markup.replace('class="timetable__table"', 'class="changed"')
            elif mutation == "empty-timetable":
                markup = markup.replace('<tr><td></td><td>13:30</td><td>11:30</td></tr>', '')
        return httpx.Response(200, text=markup, headers={"Content-Type": "text/html"})
    return httpx.MockTransport(respond)


def test_gt_public_fetch_retains_unnamed_timetable_observations_without_inventing_sessions():
    from app.gt_world_challenge import fetch_season, adapt_season
    with httpx.Client(transport=gt_transport()) as client:
        candidate = adapt_season(fetch_season(2026, client))
    barcelona = next(entry for entry in candidate.meetings if entry.source_identity == "gtwce:meeting:254")
    assert barcelona.meeting.start_date.isoformat() == "2026-10-02"
    assert barcelona.meeting.sessions == []
    observations = [entry for entry in barcelona.field_assertions if entry.field == "timetable"]
    assert len(observations) == 1
    assert json.loads(observations[0].value) == {"caption": "Thursday, 1 October", "name": "", "local": "13:30", "gmt": "11:30"}
    assert not observations[0].preferred


@pytest.mark.parametrize("mutation", ["missing", "season", "blocked", "no-timetable", "empty-timetable"])
def test_gt_fetch_rejects_partial_changed_or_blocked_sources(mutation):
    from app.gt_world_challenge import fetch_season
    with httpx.Client(transport=gt_transport(mutation)) as client:
        with pytest.raises((ValueError, httpx.HTTPError)):
            fetch_season(2026, client)


@pytest.mark.parametrize("real", [False, True])
def test_gt_workflow_queues_combined_snapshot_and_does_not_mask_f1_failure(tmp_path, request, real):
    from datetime import UTC, datetime
    from app.publication import InMemoryOperationalStore, InMemoryGraphProjection, PublicationModule, parse_candidate
    from app.review import ReviewService
    from app.source_workflow import fetch_for_review
    from test_formula_one import source_fixture, adapt_season, publish_reviewed, source_transport
    store, graph = request.getfixturevalue("isolated_services") if real else (InMemoryOperationalStore(), InMemoryGraphProjection())
    service = ReviewService(tmp_path, store, PublicationModule(store, graph))
    publish_reviewed(service, adapt_season(source_fixture()))
    before = store.visible_meetings()
    store.record_source_attempt(datetime.now(UTC), False)
    with httpx.Client(transport=gt_transport()) as client:
        result = fetch_for_review(2026, client, store, service, source_family="gt-world-challenge-europe")
        assert result["status"] == "pending-review"
        item = service.show(result["itemId"])
        assert len(item["preview"]["unresolvedIdentities"]) == 12
        assert store.visible_meetings() == before
        accept_review(service, parse_candidate(item["candidate"]))
        repeat = fetch_for_review(2026, client, store, service, source_family="gt-world-challenge-europe")
        assert repeat["status"] == "unchanged"
    freshness = store.source_freshness()
    assert freshness["stale"] is True
    sources = {entry["sourceFamily"]: entry for entry in freshness["sources"]}
    assert sources["formula-one"]["reason"] == "Source fetch failed"
    assert sources["gt-world-challenge-europe"]["stale"] is False
    with httpx.Client(transport=source_transport(source_fixture())) as client:
        assert fetch_for_review(2026, client, store, service)["status"] == "unchanged"
    assert store.source_freshness()["stale"] is False
    assert len(store.visible_meetings()) == 35


@pytest.mark.parametrize("real", [False, True])
def test_shared_circuits_are_queryable_by_identity_and_api_preserves_assertions(tmp_path, request, monkeypatch, real):
    from app.publication import InMemoryOperationalStore, PublicationModule, merge_season
    from app.review import ReviewService
    from app.stores import PUBLICATION_GRAPH
    from app.main import app, operational_store
    from fastapi.testclient import TestClient
    from test_formula_one import source_fixture, adapt_season
    if real:
        store, projection = request.getfixturevalue("isolated_services")
    else:
        store = InMemoryOperationalStore()
        projection = GraphDbProjection("http://unused", "unused", Path("unused"))
        graph = Graph()
        def capture(url, **kwargs):
            graph.parse(data=kwargs["content"], format="turtle")
            return httpx.Response(204, request=httpx.Request("PUT", url))
        monkeypatch.setattr(httpx, "put", capture)
        monkeypatch.setattr(httpx, "get", lambda url, **kwargs: httpx.Response(200, text=graph.serialize(format="nt"), request=httpx.Request("GET", url)))
    service = ReviewService(tmp_path, store, PublicationModule(store, projection))
    combined = merge_season(adapt_season(source_fixture()), gt_candidate())
    receipt = accept_review(service, combined)
    pattern = '''
        ?first a msh:Meeting ; msh:competition <https://w3id.org/motorsport-hub/resource/competition/formula-one> ; msh:circuit ?circuit .
        ?second a msh:Meeting ; msh:competition <https://w3id.org/motorsport-hub/resource/competition/gt-world-challenge-europe> ; msh:circuit ?circuit .
    '''
    prefix = 'PREFIX msh: <https://w3id.org/motorsport-hub/ontology/> '
    if real:
        query = prefix + f'SELECT DISTINCT ?circuit WHERE {{ GRAPH <{PUBLICATION_GRAPH}{receipt["version"]}> {{ {pattern} }} }}'
        response = httpx.post(projection.repository_url, data={"query": query}, headers={"Accept": "application/sparql-results+json"})
        response.raise_for_status()
        circuits = {entry["circuit"]["value"].rsplit("/", 1)[1] for entry in response.json()["results"]["bindings"]}
    else:
        circuits = {str(row.circuit).rsplit("/", 1)[1] for row in graph.query(prefix + 'SELECT DISTINCT ?circuit WHERE {' + pattern + '}')}
        assert len(list(graph.subjects(MOTORSPORT.field, None))) > 60
    assert circuits == {"f1-circuit-7", "f1-circuit-15", "f1-circuit-39", "f1-circuit-55"}
    app.dependency_overrides[operational_store] = lambda: store
    try:
        with TestClient(app) as client:
            response = client.get("/api/schedule")
        assert response.status_code == 200
        visible = response.json()["meetings"]
        shared = [entry for entry in visible if entry["circuitId"] == "circuit:f1-circuit-7"]
        assert {entry["competitionId"] for entry in shared} == {"competition:formula-one", "competition:gt-world-challenge-europe"}
        prologue_view = next(entry for entry in visible if entry["id"] == "meeting:gtwce:meeting:244")
        assert prologue_view["round"] is None and prologue_view["roundId"] is None
        assert prologue_view["kind"] == "prologue"
        assert any(entry["value"] == "Test Day" for entry in prologue_view["fieldAssertions"])
        assert all(entry["publicationVersion"] == receipt["version"] for entry in visible)
    finally:
        app.dependency_overrides.clear()


def test_gt_identity_review_cannot_be_bypassed_by_omitting_optional_assertions(tmp_path):
    from app.publication import InMemoryOperationalStore, InMemoryGraphProjection, PublicationModule
    from app.review import ReviewService
    service = ReviewService(tmp_path, InMemoryOperationalStore(), PublicationModule(InMemoryOperationalStore(), InMemoryGraphProjection()))
    candidate = gt_candidate()
    for entry in candidate.meetings:
        entry.field_assertions = []
    item = service.preview(candidate.model_dump(mode="json"))
    assert len(item["preview"]["unresolvedIdentities"]) == 12
    proposal = service.propose_decision(item["id"], "accepted", "Test Operator", "Missing explicit mapping review", [candidate.source_url])
    service.record_decision(item["id"], proposal["confirmation"])
    with pytest.raises(ValueError, match="unresolved identities"):
        service.propose_publication(item["id"])