import os
import json
import subprocess
import sys
import zipfile
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from fastapi.testclient import TestClient

from app.graph_config import maintenance_auth
from app.main import app, operational_store
from app.publication import CandidateEnvelope, PublicationModule
from app.stores import PostgresOperationalStore


@pytest.mark.parametrize("missing_graph", [False, True])
def test_operator_backup_restores_accepted_knowledge_and_refuses_overwrite(isolated_services, tmp_path, missing_graph):
    store, graph = isolated_services
    candidate = CandidateEnvelope.model_validate_json(
        (Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8")
    )
    published = PublicationModule(store, graph).publish(candidate)
    store.record_source_attempt("2026-09-14T10:00:00Z", False)
    container = os.environ.get("TEST_POSTGRES_CONTAINER") or subprocess.run(["docker", "compose", "ps", "-q", "database"], capture_output=True, text=True, check=True).stdout.strip()
    assert container
    environment = {**os.environ, "DATABASE_URL": store._database_url, "POSTGRES_CONTAINER": container,
                   "GRAPHDB_URL": os.environ["TEST_GRAPHDB_URL"], "GRAPHDB_REPOSITORY": graph.repository_url.rsplit("/", 1)[1]}
    archive = tmp_path / "private-backup.zip"

    def command(action, environment):
        return subprocess.run([sys.executable, "-m", "app.recovery", action, str(archive)],
                              env=environment, capture_output=True, text=True, timeout=180)

    backup = command("backup", environment)
    assert backup.returncode == 0, backup.stderr
    assert archive.is_file()
    refused = command("restore", environment)
    assert refused.returncode != 0
    assert "empty" in refused.stderr
    assert store.current_publication_version() == published.version
    if missing_graph:
        with zipfile.ZipFile(archive) as source:
            manifest = json.loads(source.read("manifest.json"))
            files = {name: source.read(name) for name in manifest["checksums"]}
        del manifest["checksums"][f"graphs/{published.version}.ttl"]
        del files[f"graphs/{published.version}.ttl"]
        with zipfile.ZipFile(archive, "w") as target_archive:
            target_archive.writestr("manifest.json", json.dumps(manifest))
            for name, body in files.items():
                target_archive.writestr(name, body)
    parameters = conninfo_to_dict(store._database_url)
    identifier = "review_test_" + uuid4().hex
    parameters["dbname"] = "postgres"
    with psycopg.connect(make_conninfo("", **parameters), autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(identifier)))
        try:
            parameters["dbname"] = identifier
            target_url = make_conninfo("", **parameters)
            restored = command("restore", {**environment, "DATABASE_URL": target_url, "GRAPHDB_REPOSITORY": identifier})
            target = PostgresOperationalStore(target_url)
            app.dependency_overrides[operational_store] = lambda: target
            if missing_graph:
                assert restored.returncode == 1
                with TestClient(app) as client:
                    assert client.get("/api/exports").json()["publicationVersion"] is None
                    assert client.get(f"/api/exports/publications/{published.version}/turtle").status_code == 409
                return
            assert restored.returncode == 0, restored.stderr
            with TestClient(app) as client:
                assert client.get("/api/exports").json()["publicationVersion"] == published.version
                assert client.get(f"/api/exports/publications/{published.version}/turtle").status_code == 200
                schedule = client.get("/api/schedule").json()
                assert schedule["meetings"][0]["id"] == "meeting:f1:2026:australia"
                assert target.source_freshness() == store.source_freshness()
            graph_url = os.environ["TEST_GRAPHDB_URL"].rstrip("/")
            response = httpx.get(f"{graph_url}/repositories/{identifier}/statements",
                                params={"context": f"<https://w3id.org/motorsport-hub/graph/publication/{published.version}>", "infer": "false"},
                                headers={"Accept": "text/turtle"}, auth=maintenance_auth())
            assert response.status_code == 200 and "Australian" in response.text
            response = httpx.delete(f"{graph_url}/repositories/{identifier}/statements",
                                    params={"context": f"<https://w3id.org/motorsport-hub/graph/publication/{published.version}>"},
                                    auth=maintenance_auth(), timeout=30)
            response.raise_for_status()
            reconciled = subprocess.run([sys.executable, "-m", "app.recovery", "reconcile"],
                                       env={**environment, "DATABASE_URL": target_url, "GRAPHDB_REPOSITORY": identifier},
                                       capture_output=True, text=True, timeout=180)
            assert reconciled.returncode == 0, reconciled.stderr
            assert target.current_publication_version() == published.version
            response = httpx.get(f"{graph_url}/repositories/{identifier}/statements",
                                params={"context": f"<https://w3id.org/motorsport-hub/graph/publication/{published.version}>", "infer": "false"},
                                headers={"Accept": "text/turtle"}, auth=maintenance_auth(), timeout=30)
            assert response.status_code == 200 and "Australian" in response.text
        finally:
            app.dependency_overrides.clear()
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(identifier)))
            response = httpx.delete(f"{os.environ['TEST_GRAPHDB_URL'].rstrip('/')}/rest/repositories/{identifier}", auth=maintenance_auth(), timeout=30)
            assert response.status_code in (200, 204, 404)


def test_operator_rejects_corrupt_backup_without_exposing_secrets(tmp_path):
    archive = tmp_path / "tampered.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("manifest.json", '{"format":1,"publicationVersion":null,"checksums":{"database.dump":"bad"}}')
        output.writestr("database.dump", "corrupt")
    result = subprocess.run([sys.executable, "-m", "app.recovery", "restore", str(archive)],
                            env={**os.environ, "DATABASE_URL": "private-canary-connection"}, capture_output=True, text=True)
    assert result.returncode == 1
    assert "checksum mismatch" in result.stderr
    assert "private-canary-connection" not in result.stdout + result.stderr