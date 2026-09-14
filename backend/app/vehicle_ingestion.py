import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.publication import CandidateEnvelope, PublicationModule, PublicationSnapshot
from app.review import ReviewService, ReviewStore
from app.stores import GraphDbProjection, PostgresOperationalStore
from app.vehicles import BasicVehicleSpecification


APPROVED_HOSTS = {"newsroom.porsche.com", "www.bmw-m.com", "www.mercedes-amg.com",
                  "en.wikipedia.org", "www.wikidata.org"}


class VehicleInventory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vehicles: list[BasicVehicleSpecification] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def unique_identities(self) -> "VehicleInventory":
        if len({vehicle.identity for vehicle in self.vehicles}) != len(self.vehicles):
            raise ValueError("Duplicate vehicle identity")
        return self


def prepare_candidate(path: Path, store: ReviewStore, client: httpx.Client) -> PublicationSnapshot:
    if path.stat().st_size > 1_000_000:
        raise ValueError("Vehicle inventory exceeds 1 MB")
    inventory = VehicleInventory.model_validate_json(path.read_text("utf-8-sig"))
    version = store.current_publication_version()
    if version is None:
        raise ValueError("Publish the schedule before collecting vehicle specifications")
    baseline = store.publication_envelope(version)
    if isinstance(baseline, CandidateEnvelope):
        raise ValueError("A season-scoped publication is required")
    verified = {}
    for vehicle in inventory.vehicles:
        for assertions in vehicle.fields.values():
            for assertion in assertions:
                source = assertion.source
                if source.url.host not in APPROVED_HOSTS or source.url.port not in (None, 443):
                    raise ValueError("Vehicle source host is not approved for private collection")
                url = str(source.url)
                if url not in verified:
                    checksum = hashlib.sha256()
                    size = 0
                    with client.stream("GET", url, follow_redirects=False, timeout=20,
                                       headers={"Accept-Encoding": "identity"}) as response:
                        response.raise_for_status()
                        if response.headers.get("content-encoding", "identity").lower() != "identity":
                            raise ValueError("Compressed vehicle responses are not accepted")
                        if response.headers.get("content-type", "").split(";", 1)[0].lower() not in {"text/html", "application/pdf", "application/json"}:
                            raise ValueError("Unsupported vehicle source content type")
                        for chunk in response.iter_raw():
                            size += len(chunk)
                            if size > 10_000_000:
                                raise ValueError("Vehicle source exceeds 10 MB")
                            checksum.update(chunk)
                    if not size:
                        raise ValueError("Vehicle source is empty")
                    verified[url] = (checksum.hexdigest(), datetime.now(UTC))
                digest, retrieved = verified[url]
                if digest != source.sha256:
                    raise ValueError("Vehicle source checksum changed; review a new inventory")
                source.retrieved_at = retrieved
    snapshot = baseline if isinstance(baseline, PublicationSnapshot) else PublicationSnapshot(seasons=[baseline])
    identities = {vehicle.identity for vehicle in inventory.vehicles}
    return PublicationSnapshot(seasons=snapshot.seasons, regulations=snapshot.regulations,
        vehicles=[vehicle for vehicle in snapshot.vehicles if vehicle.identity not in identities] + inventory.vehicles)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify sourced vehicle descriptions and prepare one private preview; never accept or publish.")
    parser.add_argument("inventory", type=Path)
    parser.add_argument("--reviews-dir", type=Path, default=Path(__file__).parents[2] / "reviews")
    options = parser.parse_args()
    try:
        store = PostgresOperationalStore(os.environ["DATABASE_URL"])
        graph = GraphDbProjection(os.environ["GRAPHDB_URL"], os.environ.get("GRAPHDB_REPOSITORY", "motorsport"),
                                  Path(__file__).parents[2] / "graphdb/repository-config.ttl")
        baseline = store.current_publication_version()
        if baseline is None:
            raise ValueError("Existing publication required")
        with httpx.Client() as client:
            candidate = prepare_candidate(options.inventory, store, client)
        service = ReviewService(options.reviews_dir, store, PublicationModule(store, graph))
        item = service.preview(candidate.model_dump(mode="json"), expected_baseline=baseline)
        print(json.dumps({"id": item["id"], "baselineVersion": item["baselineVersion"], "preview": item["preview"]}, indent=2))
        return 0
    except (ValueError, OSError, KeyError, httpx.HTTPError):
        parser.exit(2, "Vehicle preview failed. Check inventory, official sources and local configuration. Nothing was published.\n")


if __name__ == "__main__":
    raise SystemExit(main())