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
    fixture_path = Path(__file__).parents[1] / "fixtures/f1-2026-australia.json"
    envelope = CandidateEnvelope.model_validate(json.loads(fixture_path.read_text("utf-8")))
    result = PublicationModule(operational, graph).publish_initial(envelope)
    print(f"Current publication version {result.version}")


if __name__ == "__main__":
    main()