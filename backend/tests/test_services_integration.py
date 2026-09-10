import json
import os
from pathlib import Path

import httpx
import pytest

from app.publication import CandidateEnvelope, PublicationModule
from app.stores import GraphDbProjection, PostgresOperationalStore


DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
GRAPHDB_URL = os.environ.get("TEST_GRAPHDB_URL")


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

    publication.publish(envelope)
    publication.publish(envelope)

    meetings = operational.visible_meetings()
    assert len(meetings) == 1
    assert meetings[0]["id"] == "meeting:f1:2026:australia"
    assert operational.canonical_resource_counts() == {
        "competitions": 1,
        "seasons": 1,
        "meetings": 1,
        "circuits": 1,
        "provenance": 1,
    }

    response = httpx.post(
        f"{GRAPHDB_URL}/repositories/motorsport",
        data={
            "query": """SELECT ?meeting WHERE {
                GRAPH ?publication {
                    ?meeting a <https://w3id.org/motorsport-hub/ontology/Meeting> .
                }
            }"""
        },
        headers={"Accept": "application/sparql-results+json"},
        timeout=30,
    )
    response.raise_for_status()
    bindings = response.json()["results"]["bindings"]
    assert {binding["meeting"]["value"] for binding in bindings} == {
        "https://w3id.org/motorsport-hub/resource/meeting/f1%3A2026%3Aaustralia"
    }


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