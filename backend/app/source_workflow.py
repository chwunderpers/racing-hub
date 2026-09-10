import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.formula_one import adapt_season, fetch_season
from app.publication import SeasonCandidateEnvelope, PublicationModule
from app.review import ReviewService
from app.stores import PostgresOperationalStore, GraphDbProjection


def semantic_version(candidate: SeasonCandidateEnvelope) -> str:
    value = candidate.model_dump(mode="json")
    value.pop("retrieved_at")
    for entry in value["meetings"]:
        entry.pop("retrieved_at")
    value["meetings"].sort(key=lambda entry: entry["source_identity"])
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def fetch_for_review(season: int, client: httpx.Client, store, review: ReviewService, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    try:
        candidate = adapt_season(fetch_season(season, client, now))
        current = store.current_publication_version()
        previous = store.publication_envelope(current) if current else None
        if isinstance(previous, SeasonCandidateEnvelope) and semantic_version(previous) == semantic_version(candidate):
            result = {"status": "unchanged", "version": current}
        else:
            item = review.preview(candidate.model_dump(mode="json"))
            if item["preview"]["conflicts"] or item["preview"]["validationErrors"]:
                store.record_source_attempt(now, False)
                return {"status": "failed", "reason": "Candidate requires conflict resolution", "itemId": item["id"]}
            result = {"status": "pending-review", "itemId": item["id"], "meetings": len(candidate.meetings)}
        store.record_source_attempt(now, True, pending=result["status"] == "pending-review")
        return result
    except (httpx.HTTPError, ValueError, KeyError, TypeError, IndexError):
        store.record_source_attempt(now, False)
        return {"status": "failed", "reason": "Source fetch failed"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch official Formula One schedule for private review; never publish")
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
            candidate = adapt_season(json.loads(options.fixture.read_text("utf-8")))
            item = review.preview(candidate.model_dump(mode="json"))
            result = {"status": "pending-review", "itemId": item["id"], "meetings": len(candidate.meetings)}
        else:
            with httpx.Client(timeout=30, follow_redirects=False) as client:
                result = fetch_for_review(options.season, client, store, review)
        print(json.dumps(result))
        return 1 if result["status"] == "failed" else 0
    except Exception as error:
        print(f"Source workflow failed ({type(error).__name__}); no publication was approved")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())