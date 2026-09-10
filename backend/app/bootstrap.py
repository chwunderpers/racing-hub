import json
import os
from pathlib import Path

from app.publication import CandidateEnvelope, PublicationModule
from app.stores import GraphDbProjection, PostgresOperationalStore


def main() -> None:
    operational = PostgresOperationalStore(os.environ["DATABASE_URL"])
    graph = GraphDbProjection(
        os.environ["GRAPHDB_URL"],
        os.environ.get("GRAPHDB_REPOSITORY", "motorsport"),
        Path("graphdb/repository-config.ttl"),
    )
    operational.initialize()
    graph.initialize()
    fixture_path = Path(
        os.environ.get("SAMPLE_ENVELOPE", "fixtures/f1-2026-australia.json")
    )
    envelope = CandidateEnvelope.model_validate(json.loads(fixture_path.read_text("utf-8")))
    result = PublicationModule(operational, graph).publish(envelope)
    print(f"Published version {result.version}")


if __name__ == "__main__":
    main()