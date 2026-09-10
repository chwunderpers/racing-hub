import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.formula_one import adapt_season, fetch_season
from app import gt_world_challenge, nls
from app.publication import SeasonCandidateEnvelope, PublicationSnapshot, PublicationModule, merge_season
from app.review import ReviewService
from app.stores import PostgresOperationalStore, GraphDbProjection


def semantic_version(candidate: SeasonCandidateEnvelope) -> str:
    value = candidate.model_dump(mode="json")
    value.pop("retrieved_at")
    for entry in value["meetings"]:
        entry.pop("retrieved_at")
        for assertion in entry.get("field_assertions", []):
            assertion.pop("retrieved_at")
            assertion.pop("response_sha256", None)
            if assertion.get("translation"):
                assertion["translation"].pop("translated_at", None)
    value["meetings"].sort(key=lambda entry: entry["source_identity"])
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fetch_for_review(season: int, client: httpx.Client, store, review: ReviewService, now: datetime | None = None, source_family: str = "formula-one") -> dict:
    now = now or datetime.now(UTC)
    if source_family not in ("formula-one", gt_world_challenge.COMPETITION, nls.COMPETITION):
        raise ValueError("Unknown source family")
    try:
        if source_family == nls.COMPETITION:
            candidate = nls.adapt_season(nls.fetch_season(season, client, now))
        elif source_family == gt_world_challenge.COMPETITION:
            candidate = gt_world_challenge.adapt_season(gt_world_challenge.fetch_season(season, client, now))
        else:
            candidate = adapt_season(fetch_season(season, client, now))
        current = store.current_publication_version()
        previous = store.publication_envelope(current) if current else None
        seasons = previous.seasons if isinstance(previous, PublicationSnapshot) else [previous] if isinstance(previous, SeasonCandidateEnvelope) else []
        previous_season = next((entry for entry in seasons if (entry.competition_identity, entry.season_year) == (candidate.competition_identity, candidate.season_year)), None)
        if previous_season is not None and semantic_version(previous_season) == semantic_version(candidate):
            result = {"status": "unchanged", "version": current}
        else:
            item = review.preview(merge_season(previous, candidate).model_dump(mode="json"))
            if item["preview"]["conflicts"] or item["preview"]["validationErrors"]:
                store.record_source_attempt(now, False, source_family=source_family)
                return {"status": "failed", "reason": "Candidate requires conflict resolution", "itemId": item["id"]}
            result = {"status": "pending-review", "itemId": item["id"], "meetings": len(candidate.meetings)}
        store.record_source_attempt(now, True, pending=result["status"] == "pending-review", source_family=source_family)
        return result
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
        store.record_source_attempt(now, False, source_family=source_family)
        return {"status": "failed", "reason": "Source fetch failed"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch official schedules for private review; never publish")
    parser.add_argument("--source-family", choices=["formula-one", gt_world_challenge.COMPETITION, nls.COMPETITION], default="formula-one")
    parser.add_argument("--season", type=int, default=2026)
    parser.add_argument("--reviews-dir", type=Path, default=Path(__file__).parents[2] / "reviews")
    parser.add_argument("--fixture", type=Path)
    options = parser.parse_args()
    try:
        store = PostgresOperationalStore(os.environ["DATABASE_URL"])
        store.initialize()
        graph = GraphDbProjection(os.environ["GRAPHDB_URL"], os.environ.get("GRAPHDB_REPOSITORY", "motorsport"), Path(__file__).parents[2] / "graphdb/repository-config.ttl")
        review = ReviewService(options.reviews_dir, store, PublicationModule(store, graph))
        if options.fixture:
            adapter = {"formula-one": adapt_season, gt_world_challenge.COMPETITION: gt_world_challenge.adapt_season, nls.COMPETITION: nls.adapt_season}[options.source_family]
            candidate = adapter(json.loads(options.fixture.read_text("utf-8")))
            current = store.current_publication_version()
            previous = store.publication_envelope(current) if current else None
            item = review.preview(merge_season(previous, candidate).model_dump(mode="json"))
            result = {"status": "pending-review", "itemId": item["id"], "meetings": len(candidate.meetings)}
        else:
            with httpx.Client(timeout=30, follow_redirects=False) as client:
                result = fetch_for_review(options.season, client, store, review, source_family=options.source_family)
        print(json.dumps(result))
        return 1 if result["status"] == "failed" else 0
    except Exception as error:
        print(f"Source workflow failed ({type(error).__name__}); no publication was approved")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())