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


@pytest.fixture
def isolated_services(tmp_path):
    database_url = os.environ.get("TEST_DATABASE_URL")
    graphdb_url = os.environ.get("TEST_GRAPHDB_URL")
    if not database_url or not graphdb_url:
        pytest.skip("Set TEST_DATABASE_URL and TEST_GRAPHDB_URL for isolated service tests")
    identifier = f"review_test_{uuid4().hex}"
    parameters = conninfo_to_dict(database_url)
    parameters["dbname"] = "postgres"
    with psycopg.connect(make_conninfo(**parameters), autocommit=True, connect_timeout=5) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(identifier)))
        try:
            parameters["dbname"] = identifier
            operational = PostgresOperationalStore(make_conninfo(**parameters))
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
                response = httpx.delete(f"{graphdb_url.rstrip('/')}/rest/repositories/{identifier}", timeout=30)
                if response.status_code != 404:
                    response.raise_for_status()
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(identifier)))