import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

import httpx
import psycopg
from psycopg.conninfo import conninfo_to_dict
from rdflib import Graph, Literal, URIRef

from app.graph_config import maintenance_auth
from app.stores import GraphDbProjection, PostgresOperationalStore, PUBLICATION_GRAPH


MAX_ARCHIVE_BYTES = 256 * 1024 * 1024


def postgres_tool(tool: str, database_url: str, arguments: list[str], content: bytes | None = None) -> bytes:
    parameters = conninfo_to_dict(database_url)
    if parameters.get("host") not in ("localhost", "127.0.0.1"):
        raise ValueError("Recovery requires a local PostgreSQL connection")
    environment = {**os.environ, "PGUSER": parameters.get("user", ""),
                   "PGPASSWORD": parameters.get("password", ""), "PGDATABASE": parameters["dbname"]}
    container = os.environ["POSTGRES_CONTAINER"]
    result = subprocess.run(
        ["docker", "exec", "-i", "-e", "PGUSER", "-e", "PGPASSWORD", "-e", "PGDATABASE", container,
         tool, "--host=127.0.0.1", "--no-password", *arguments],
        input=content, capture_output=True, env=environment, timeout=180,
    )
    if result.returncode:
        raise RuntimeError("PostgreSQL backup tool failed; inspect local service health")
    return result.stdout


def graph_location() -> tuple[str, str]:
    base = os.environ["GRAPHDB_URL"].rstrip("/")
    repository = os.environ.get("GRAPHDB_REPOSITORY", "motorsport")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", repository):
        raise ValueError("Invalid repository identifier")
    return base, repository


def backup(path: Path) -> str | None:
    store = PostgresOperationalStore(os.environ["DATABASE_URL"])
    base, repository = graph_location()
    with store.publication_lock():
        version = store.current_publication_version()
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=5) as connection:
            versions = [row[0] for row in connection.execute("SELECT version FROM publications ORDER BY version")]
        files = {"database.dump": postgres_tool("pg_dump", os.environ["DATABASE_URL"], ["--format=custom", "--no-owner", "--no-privileges"])}
        with httpx.Client(auth=maintenance_auth(), timeout=60) as client:
            for entry in versions:
                if not re.fullmatch(r"[0-9a-f]{64}", entry):
                    raise ValueError("Invalid stored publication version")
                response = client.get(f"{base}/repositories/{repository}/statements",
                                      params={"context": f"<{PUBLICATION_GRAPH}{entry}>", "infer": "false"},
                                      headers={"Accept": "text/turtle"})
                response.raise_for_status()
                files[f"graphs/{entry}.ttl"] = response.content
        manifest = {"format": 1, "publicationVersion": version,
                    "checksums": {name: hashlib.sha256(body).hexdigest() for name, body in files.items()}}
        if sum(len(body) for body in files.values()) > MAX_ARCHIVE_BYTES:
            raise ValueError("Backup exceeds local PoC size limit")
        with path.open("xb") as output, zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest))
            for name, body in files.items():
                archive.writestr(name, body)
    return version


def read_backup(path: Path) -> tuple[dict, dict[str, bytes]]:
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Backup exceeds local PoC size limit")
    with zipfile.ZipFile(path) as archive:
        if sum(entry.file_size for entry in archive.infolist()) > MAX_ARCHIVE_BYTES:
            raise ValueError("Expanded backup exceeds local PoC size limit")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest["format"] != 1:
            raise ValueError("Unsupported backup version")
        files = {name: archive.read(name) for name in manifest["checksums"]}
        if "database.dump" not in files or any(hashlib.sha256(body).hexdigest() != manifest["checksums"][name] for name, body in files.items()):
            raise ValueError("Backup checksum mismatch")
        if any(name != "database.dump" and not re.fullmatch(r"graphs/[0-9a-f]{64}\.ttl", name) for name in files):
            raise ValueError("Invalid backup member")
        return manifest, files


def restore(path: Path) -> str | None:
    manifest, files = read_backup(path)
    database_url = os.environ["DATABASE_URL"]
    base, repository = graph_location()
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        if connection.execute("SELECT 1 FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') LIMIT 1").fetchone():
            raise ValueError("Restore requires an empty PostgreSQL database")
    response = httpx.get(f"{base}/rest/repositories", auth=maintenance_auth(), timeout=30)
    response.raise_for_status()
    if any(entry["id"] == repository for entry in response.json()):
        raise ValueError("Restore requires a new, empty GraphDB repository")
    postgres_tool("pg_restore", database_url, ["--dbname=" + str(conninfo_to_dict(database_url)["dbname"]),
                                               "--single-transaction", "--no-owner", "--no-privileges"], files["database.dump"])
    store = PostgresOperationalStore(database_url)
    version = store.current_publication_version()
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        connection.execute("UPDATE publication_state SET current_version = NULL")
    if version != manifest["publicationVersion"]:
        raise ValueError("Restored publication does not match backup manifest")
    config = Graph().parse(Path(__file__).resolve().parents[2] / "graphdb/repository-config.ttl")
    predicate = URIRef("http://www.openrdf.org/config/repository#repositoryID")
    config.set((next(config.subjects(predicate, None)), predicate, Literal(repository)))
    with tempfile.TemporaryDirectory(prefix="racing-restore-") as temporary:
        config_path = Path(temporary) / "repository.ttl"
        config.serialize(destination=config_path, format="turtle")
        graph = GraphDbProjection(base, repository, config_path)
        graph.initialize()
        for name, body in files.items():
            if name == "database.dump":
                continue
            entry = Path(name).stem
            response = httpx.put(f"{graph.repository_url}/statements", params={"context": f"<{PUBLICATION_GRAPH}{entry}>"},
                                content=body, headers={"Content-Type": "text/turtle"}, auth=maintenance_auth(), timeout=60)
            response.raise_for_status()
        if version and not graph.agrees(version, "", store.publication_envelope(version)):
            raise ValueError("Restored current graph does not agree with the publication")
        if version:
            store.promote(version)
    return version


def reconcile() -> str | None:
    store = PostgresOperationalStore(os.environ["DATABASE_URL"])
    base, repository = graph_location()
    graph = GraphDbProjection(base, repository, Path(__file__).resolve().parents[2] / "graphdb/repository-config.ttl")
    with store.publication_lock():
        version = store.current_publication_version()
        if version:
            candidate = store.publication_envelope(version)
            graph.project(version, candidate)
            if not graph.agrees(version, "", candidate):
                raise ValueError("Reconciliation did not restore graph agreement")
            store.stage(version, candidate)
        return version


def main() -> int:
    parser = argparse.ArgumentParser(description="Private local PoC backup and empty-target restoration")
    parser.add_argument("action", choices=("backup", "restore", "reconcile"))
    parser.add_argument("archive", type=Path, nargs="?")
    args = parser.parse_args()
    try:
        if args.action == "reconcile":
            version = reconcile()
        elif args.archive is None:
            raise ValueError("An archive path is required")
        else:
            version = backup(args.archive) if args.action == "backup" else restore(args.archive)
        print(json.dumps({"status": "complete", "publicationVersion": version}))
        return 0
    except ValueError as error:
        print(str(error), file=sys.stderr)
    except Exception:
        print("Recovery failed; no credentials are included in this diagnostic", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())