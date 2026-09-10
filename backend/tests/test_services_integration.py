import json
import os
from datetime import datetime
from pathlib import Path

import httpx
import pytest

from app.publication import CandidateEnvelope, PublicationModule
from app.stores import GraphDbProjection, PostgresOperationalStore


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
GRAPHDB_URL = os.environ.get("TEST_GRAPHDB_URL")


def assert_graph_matches_meeting(graph, meeting) -> None:
    version = meeting["publicationVersion"]
    response = httpx.post(
        graph.repository_url,
        data={"query": f"""
            PREFIX msh: <https://w3id.org/motorsport-hub/ontology/>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?meeting ?name ?competition ?season ?circuit ?start ?end ?source ?retrieved ?evidence
            WHERE {{ GRAPH <https://w3id.org/motorsport-hub/graph/publication/{version}> {{
                ?publication a msh:Publication; msh:version "{version}"; msh:includesMeeting ?meeting .
                ?meeting a msh:Meeting; rdfs:label ?name; msh:competition ?competitionId;
                    msh:season ?seasonId; msh:circuit ?circuitId; msh:startDate ?start;
                    msh:endDate ?end; msh:provenance ?provenance .
                ?competitionId a msh:Competition; rdfs:label ?competition .
                ?seasonId a msh:Season; msh:competition ?competitionId; msh:year ?season .
                ?circuitId a msh:Circuit; rdfs:label ?circuit .
                ?provenance a msh:SourceAssertion; msh:sourceUrl ?source;
                    msh:retrievedAt ?retrieved; msh:evidence ?evidence .
            }} }}
        """},
        headers={"Accept": "application/sparql-results+json"},
        timeout=30,
    )
    response.raise_for_status()
    bindings = response.json()["results"]["bindings"]
    assert len(bindings) == 1
    actual = {key: value["value"] for key, value in bindings[0].items()}
    assert actual["meeting"] == "https://w3id.org/motorsport-hub/resource/meeting/f1%3A2026%3Aaustralia"
    assert actual["name"] == meeting["name"]
    assert actual["competition"] == meeting["competition"]
    assert int(actual["season"]) == meeting["season"]
    assert actual["circuit"] == meeting["circuit"]
    assert actual["start"] == meeting["startDate"]
    assert actual["end"] == meeting["endDate"]
    assert actual["source"] == meeting["sourceUrl"]
    assert datetime.fromisoformat(actual["retrieved"]) == datetime.fromisoformat(meeting["retrievedAt"])
    assert actual["evidence"] == "FORMULA 1 QATAR AIRWAYS AUSTRALIAN GRAND PRIX 2026"


@pytest.mark.skipif(
    not DATABASE_URL or not GRAPHDB_URL,
    reason="Set TEST_DATABASE_URL and TEST_GRAPHDB_URL to run service integration tests",
)
def test_formula_one_meeting_is_published_coherently_and_idempotently() -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "f1-2026-australia.json"
    envelope = CandidateEnvelope.model_validate(json.loads(fixture_path.read_text("utf-8")))
    operational = PostgresOperationalStore(DATABASE_URL)
    graph = GraphDbProjection(
        GRAPHDB_URL,
        "motorsport",
        Path(__file__).parents[2] / "graphdb" / "repository-config.ttl",
    )
    publication = PublicationModule(operational, graph)

    first = publication.publish(envelope)
    publication.publish(envelope)

    meetings = operational.visible_meetings()
    assert len(meetings) == 1
    assert meetings[0]["id"] == "meeting:f1:2026:australia"
    assert meetings[0]["publicationVersion"] == first.version
    assert operational.canonical_resource_counts() == {
        "competitions": 1,
        "seasons": 1,
        "meetings": 1,
        "circuits": 1,
        "provenance": 1,
    }

    assert_graph_matches_meeting(graph, meetings[0])


@pytest.mark.skipif(
    not DATABASE_URL or not GRAPHDB_URL,
    reason="Set TEST_DATABASE_URL and TEST_GRAPHDB_URL to run service integration tests",
)
@pytest.mark.parametrize("failure_point", ["stage", "project", "agrees", "promote"])
def test_failed_update_preserves_previous_publication(failure_point, monkeypatch) -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "f1-2026-australia.json"
    envelope = CandidateEnvelope.model_validate_json(fixture_path.read_text("utf-8"))
    operational = PostgresOperationalStore(DATABASE_URL)
    graph = GraphDbProjection(GRAPHDB_URL, "motorsport", Path("graphdb/repository-config.ttl"))
    publication = PublicationModule(operational, graph)
    first = publication.publish(envelope)
    previous = operational.visible_meetings()
    revised = envelope.model_copy(update={
        "meeting": envelope.meeting.model_copy(update={"meeting_name": "Revised Grand Prix"})
    })

    def fail(*args):
        raise RuntimeError("Injected publication failure")

    target = operational if failure_point in ("stage", "promote") else graph
    with monkeypatch.context() as patch:
        patch.setattr(target, failure_point, fail)
        with pytest.raises(RuntimeError, match="Injected publication failure"):
            publication.publish(revised)

    assert operational.visible_meetings() == previous
    assert graph.agrees(first.version, "meeting:f1:2026:australia")
    assert_graph_matches_meeting(graph, previous[0])


@pytest.mark.skipif(
    not DATABASE_URL or not GRAPHDB_URL,
    reason="Set TEST_DATABASE_URL and TEST_GRAPHDB_URL to run service integration tests",
)
def test_failed_evidence_update_preserves_published_evidence(monkeypatch) -> None:
    fixture_path = Path(__file__).parents[1] / "fixtures" / "f1-2026-australia.json"
    envelope = CandidateEnvelope.model_validate_json(fixture_path.read_text("utf-8"))
    operational = PostgresOperationalStore(DATABASE_URL)
    operational.initialize()
    graph = GraphDbProjection(GRAPHDB_URL, "motorsport", Path("graphdb/repository-config.ttl"))
    publication = PublicationModule(operational, graph)
    first = publication.publish(envelope)
    revised = envelope.model_copy(update={"evidence": "Corrected source passage"})

    def fail(*args):
        raise RuntimeError("Injected graph failure")

    monkeypatch.setattr(graph, "project", fail)
    with pytest.raises(RuntimeError, match="Injected graph failure"):
        publication.publish(revised)

    assert operational.publication_envelope(first.version).evidence == envelope.evidence