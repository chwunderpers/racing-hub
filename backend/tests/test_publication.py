from datetime import UTC, date, datetime

import pytest

from app.publication import (
    CandidateEnvelope,
    CandidateMeeting,
    InMemoryGraphProjection,
    InMemoryOperationalStore,
    PublicationModule,
)


def formula_one_envelope() -> CandidateEnvelope:
    return CandidateEnvelope(
        source_identity="f1:2026:australia",
        source_url="https://www.formula1.com/en/racing/2026/australia",
        retrieved_at=datetime(2026, 1, 15, 12, 0, tzinfo=UTC),
        source_language="en",
        evidence="FORMULA 1 QATAR AIRWAYS AUSTRALIAN GRAND PRIX 2026",
        meeting=CandidateMeeting(
            competition_identity="formula-one",
            circuit_identity="albert-park-grand-prix-circuit",
            competition_name="Formula One",
            season_year=2026,
            meeting_name="Australian Grand Prix",
            circuit_name="Albert Park Grand Prix Circuit",
            start_date=date(2026, 3, 6),
            end_date=date(2026, 3, 8),
        ),
    )


def test_publish_promotes_only_after_operational_and_graph_versions_agree() -> None:
    operational = InMemoryOperationalStore()
    graph = InMemoryGraphProjection()
    publication = PublicationModule(operational, graph)

    result = publication.publish(formula_one_envelope())

    assert result.status == "published"
    assert operational.current_version == result.version
    assert graph.current_version == result.version
    assert operational.visible_meetings() == [
        {
            "publicationVersion": result.version,
            "id": "meeting:f1:2026:australia",
            "name": "Australian Grand Prix",
            "competition": "Formula One",
            "season": 2026,
            "circuit": "Albert Park Grand Prix Circuit",
            "startDate": "2026-03-06",
            "endDate": "2026-03-08",
            "sourceUrl": "https://www.formula1.com/en/racing/2026/australia",
            "retrievedAt": "2026-01-15T12:00:00Z",
        }
    ]


def test_retrying_the_same_source_identity_creates_no_canonical_duplicates() -> None:
    operational = InMemoryOperationalStore()
    graph = InMemoryGraphProjection()
    publication = PublicationModule(operational, graph)
    envelope = formula_one_envelope()

    first = publication.publish(envelope)
    retry = publication.publish(envelope)

    assert retry.version == first.version
    assert operational.canonical_resource_counts() == {
        "competitions": 1,
        "seasons": 1,
        "meetings": 1,
        "circuits": 1,
        "provenance": 1,
    }
    assert graph.canonical_resource_counts() == {
        "competitions": 1,
        "seasons": 1,
        "meetings": 1,
        "circuits": 1,
        "provenance": 1,
    }


def test_correcting_labels_preserves_approved_canonical_identities() -> None:
    operational = InMemoryOperationalStore()
    graph = InMemoryGraphProjection()
    publication = PublicationModule(operational, graph)
    envelope = formula_one_envelope()
    publication.publish(envelope)
    revised = envelope.model_copy(update={"meeting": envelope.meeting.model_copy(update={
        "competition_name": "Formula 1",
        "circuit_name": "Albert Park Circuit",
    })})

    publication.publish(revised)

    assert operational.visible_meetings()[0]["competition"] == "Formula 1"
    assert operational.canonical_resource_counts() == {
        "competitions": 1, "seasons": 1, "meetings": 1, "circuits": 1, "provenance": 1,
    }
    assert graph.canonical_resource_counts() == operational.canonical_resource_counts()


def test_graph_failure_keeps_the_previous_complete_publication_visible() -> None:
    class FailingGraphProjection(InMemoryGraphProjection):
        fail = False

        def project(self, version: str, envelope: CandidateEnvelope) -> None:
            if self.fail:
                raise RuntimeError("GraphDB unavailable")
            super().project(version, envelope)

    operational = InMemoryOperationalStore()
    graph = FailingGraphProjection()
    publication = PublicationModule(operational, graph)
    first = publication.publish(formula_one_envelope())
    revised = formula_one_envelope().model_copy(
        update={"retrieved_at": datetime(2026, 1, 16, 12, 0, tzinfo=UTC)}
    )
    graph.fail = True

    with pytest.raises(RuntimeError, match="GraphDB unavailable"):
        publication.publish(revised)

    assert operational.current_version == first.version
    assert operational.visible_meetings()[0]["retrievedAt"] == "2026-01-15T12:00:00Z"


def test_operational_failure_keeps_the_previous_complete_publication_visible() -> None:
    class FailingOperationalStore(InMemoryOperationalStore):
        fail = False

        def stage(self, version: str, envelope: CandidateEnvelope) -> None:
            if self.fail:
                raise RuntimeError("PostgreSQL unavailable")
            super().stage(version, envelope)

    operational = FailingOperationalStore()
    graph = InMemoryGraphProjection()
    publication = PublicationModule(operational, graph)
    first = publication.publish(formula_one_envelope())
    revised = formula_one_envelope().model_copy(
        update={"retrieved_at": datetime(2026, 1, 16, 12, 0, tzinfo=UTC)}
    )
    operational.fail = True

    with pytest.raises(RuntimeError, match="PostgreSQL unavailable"):
        publication.publish(revised)

    assert operational.current_version == first.version
    assert graph.current_version == first.version


def test_disagreement_does_not_promote_a_staged_publication(monkeypatch) -> None:
    operational = InMemoryOperationalStore()
    graph = InMemoryGraphProjection()
    publication = PublicationModule(operational, graph)
    first = publication.publish(formula_one_envelope())
    monkeypatch.setattr(graph, "agrees", lambda version, meeting_id: False)

    with pytest.raises(RuntimeError, match="does not agree"):
        publication.publish(formula_one_envelope().model_copy(update={"evidence": "Revised evidence"}))

    assert operational.current_version == first.version