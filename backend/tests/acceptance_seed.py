import json
import os
from pathlib import Path

from app import formula_one, gt_world_challenge, nls
from app.publication import PublicationModule, PublicationSnapshot
from app.stores import GraphDbProjection, PostgresOperationalStore
from backend.tests.test_vehicles import vehicle_candidate


def main():
    root = Path(__file__).parents[1]
    if not os.environ.get("ACCEPTANCE_REHEARSAL"):
        raise RuntimeError("Fixture seeding is restricted to the disposable acceptance runner")
    store = PostgresOperationalStore(os.environ["DATABASE_URL"])
    store.initialize()
    if store.current_publication_version():
        raise RuntimeError("Acceptance fixture seeding requires an empty store")
    graph = GraphDbProjection(os.environ["GRAPHDB_URL"], "motorsport", root.parent / "graphdb/repository-config.ttl")
    graph.initialize()
    seasons = [adapter(json.loads((root / "fixtures" / name).read_text("utf-8"))) for adapter, name in (
        (formula_one.adapt_season, "f1-2026-source.json"),
        (gt_world_challenge.adapt_season, "gtwce-2026-source.json"),
        (nls.adapt_season, "nls-2026-source.json"),
    )]
    fixture = vehicle_candidate()
    fixture["seasons"] = [season.model_dump(mode="json") for season in seasons]
    result = PublicationModule(store, graph).publish(PublicationSnapshot.model_validate(fixture))
    print(json.dumps({"fixturePublication": result.version, "meetings": sum(len(season.meetings) for season in seasons)}))


if __name__ == "__main__":
    main()