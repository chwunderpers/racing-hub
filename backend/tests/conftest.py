import os
from pathlib import Path
from uuid import uuid4

import httpx
import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from rdflib import Graph, Literal, URIRef

from app.stores import GraphDbProjection, PostgresOperationalStore
from app.graph_config import maintenance_auth


@pytest.fixture
def isolated_database_url():
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Set TEST_DATABASE_URL for isolated service tests")
    identifier = f"review_test_{uuid4().hex}"
    parameters = conninfo_to_dict(database_url)
    parameters["dbname"] = "postgres"
    with psycopg.connect(make_conninfo(**parameters), autocommit=True, connect_timeout=5) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(identifier)))
        try:
            parameters["dbname"] = identifier
            yield make_conninfo(**parameters)
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(identifier)))


@pytest.fixture
def isolated_services(tmp_path, isolated_database_url, monkeypatch):
    graphdb_url = os.environ.get("TEST_GRAPHDB_URL")
    if not graphdb_url:
        pytest.skip("Set TEST_GRAPHDB_URL for isolated service tests")
    for field in ("USER", "PASSWORD"):
        if os.environ.get("TEST_GRAPHDB_" + field):
            monkeypatch.setenv("GRAPHDB_MAINTENANCE_" + field, os.environ["TEST_GRAPHDB_" + field])
    identifier = conninfo_to_dict(isolated_database_url)["dbname"]
    operational = PostgresOperationalStore(isolated_database_url)
    operational.initialize()
    config = Graph().parse(Path(__file__).parents[2] / "graphdb/repository-config.ttl")
    predicate = URIRef("http://www.openrdf.org/config/repository#repositoryID")
    subject = next(config.subjects(predicate, None))
    config.set((subject, predicate, Literal(identifier)))
    config_path = tmp_path / "repository-config.ttl"
    config.serialize(destination=config_path, format="turtle")
    graph = GraphDbProjection(graphdb_url, identifier, config_path)
    try:
        graph.initialize()
        yield operational, graph
    finally:
        response = httpx.delete(f"{graphdb_url.rstrip('/')}/rest/repositories/{identifier}", timeout=30, auth=maintenance_auth())
        if response.status_code != 404:
            response.raise_for_status()