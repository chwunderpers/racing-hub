import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx

from app.publication import CandidateEnvelope, PublicationModule, PublicationSnapshot
from app.regulations import CompetitionRegulations
from app.review import ReviewService, ReviewStore
from app.stores import GraphDbProjection, PostgresOperationalStore


def prepare_candidate(path: Path, store: ReviewStore, client: httpx.Client) -> PublicationSnapshot:
    if path.stat().st_size > 1_000_000:
        raise ValueError("Regulation inventory exceeds 1 MB")
    bundle = CompetitionRegulations.model_validate_json(path.read_text("utf-8"))
    version = store.current_publication_version()
    if version is None:
        raise ValueError("Publish the Competition schedule before preparing its regulation profile")
    baseline = store.publication_envelope(version)
    if isinstance(baseline, CandidateEnvelope):
        raise ValueError("A season-scoped schedule is required for regulation ingestion")
    for document in bundle.documents:
        checksum = hashlib.sha256()
        size = 0
        prefix = b""
        with client.stream("GET", str(document.source_url), follow_redirects=False, timeout=20, headers={"Accept-Encoding": "identity"}) as response:
            response.raise_for_status()
            if response.headers.get("content-encoding", "identity").lower() != "identity":
                raise ValueError("Compressed document responses are not accepted")
            for chunk in response.iter_raw():
                size += len(chunk)
                if size > 10_000_000:
                    raise ValueError("Regulation document exceeds 10 MB")
                prefix = (prefix + chunk)[:5]
                checksum.update(chunk)
        if checksum.hexdigest() != document.sha256:
            raise ValueError("Regulation document checksum changed; investigate and review a new version")
        if prefix != b"%PDF-":
            raise ValueError("Expected an official PDF document")
        document.retrieved_at = datetime.now(UTC)
    seasons = baseline.seasons if isinstance(baseline, PublicationSnapshot) else [baseline]
    previous = baseline.regulations if isinstance(baseline, PublicationSnapshot) else []
    retained = [entry for entry in previous if (entry.competition_identity, entry.season_year) != (bundle.competition_identity, bundle.season_year)]
    return PublicationSnapshot(seasons=seasons, regulations=[*retained, bundle],
                               vehicles=baseline.vehicles if isinstance(baseline, PublicationSnapshot) else [])


def main() -> int:
    parser = argparse.ArgumentParser(description="Privately verify official Formula One or NLS document checksums and preview a regulation candidate; never approve or publish.")
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--reviews-dir", type=Path, default=Path(__file__).parents[2] / "reviews")
    options = parser.parse_args()
    try:
        store = PostgresOperationalStore(os.environ["DATABASE_URL"])
        graph = GraphDbProjection(os.environ["GRAPHDB_URL"], os.environ.get("GRAPHDB_REPOSITORY", "motorsport"), Path(__file__).parents[2] / "graphdb/repository-config.ttl")
        service = ReviewService(options.reviews_dir, store, PublicationModule(store, graph))
        baseline_version = store.current_publication_version()
        if baseline_version is None:
            raise ValueError("Publish the Competition schedule before regulation ingestion")
        with httpx.Client() as client:
            candidate = prepare_candidate(options.inventory, store, client)
        result = service.preview(candidate.model_dump(mode="json"), expected_baseline=baseline_version)
        print(json.dumps({"id": result["id"], "baselineVersion": result["baselineVersion"], "preview": result["preview"]}, indent=2))
        return 0
    except (ValueError, OSError, httpx.HTTPError, KeyError):
        parser.exit(2, "Regulation preview failed. Check the inventory, official source response and local configuration; no publication was performed.\n")


if __name__ == "__main__":
    raise SystemExit(main())