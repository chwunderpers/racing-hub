from pathlib import Path
from urllib.parse import quote

import httpx
import psycopg
from psycopg.rows import dict_row
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD

from app.publication import CandidateEnvelope, canonical_resource_ids, meeting_view


MOTORSPORT = Namespace("https://w3id.org/motorsport-hub/ontology/")
RESOURCE = "https://w3id.org/motorsport-hub/resource/"
PUBLICATION_GRAPH = "https://w3id.org/motorsport-hub/graph/publication/"


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS competitions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS seasons (
    id TEXT PRIMARY KEY,
    competition_id TEXT NOT NULL REFERENCES competitions(id),
    year INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS circuits (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    source_identity TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS provenance (
    id TEXT PRIMARY KEY,
    source_identity TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,
    source_language TEXT NOT NULL CHECK (source_language = 'en'),
    evidence TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS publications (
    version TEXT PRIMARY KEY,
    source_identity TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('staged', 'complete'))
);
CREATE TABLE IF NOT EXISTS publication_meetings (
    publication_version TEXT NOT NULL REFERENCES publications(version),
    meeting_id TEXT NOT NULL REFERENCES meetings(id),
    payload JSONB NOT NULL,
    PRIMARY KEY (publication_version, meeting_id)
);
CREATE TABLE IF NOT EXISTS publication_state (
    singleton BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (singleton),
    current_version TEXT REFERENCES publications(version)
);
INSERT INTO publication_state (singleton, current_version)
VALUES (TRUE, NULL)
ON CONFLICT (singleton) DO NOTHING;
"""


class PostgresOperationalStore:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def initialize(self) -> None:
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            connection.execute(SCHEMA_SQL)

    def stage(self, version: str, envelope: CandidateEnvelope) -> None:
        ids = canonical_resource_ids(envelope)
        meeting = envelope.meeting
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            connection.execute(
                """INSERT INTO competitions (id, name) VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name""",
                (ids["competitions"], meeting.competition_name),
            )
            connection.execute(
                """INSERT INTO seasons (id, competition_id, year) VALUES (%s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET year = EXCLUDED.year""",
                (ids["seasons"], ids["competitions"], meeting.season_year),
            )
            connection.execute(
                """INSERT INTO circuits (id, name) VALUES (%s, %s)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name""",
                (ids["circuits"], meeting.circuit_name),
            )
            connection.execute(
                """INSERT INTO meetings (id, source_identity) VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING""",
                (ids["meetings"], envelope.source_identity),
            )
            connection.execute(
                """INSERT INTO provenance
                (id, source_identity, source_url, retrieved_at, source_language, evidence)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    source_url = EXCLUDED.source_url,
                    retrieved_at = EXCLUDED.retrieved_at,
                    evidence = EXCLUDED.evidence""",
                (
                    ids["provenance"],
                    envelope.source_identity,
                    envelope.source_url,
                    envelope.retrieved_at,
                    envelope.source_language,
                    envelope.evidence,
                ),
            )
            connection.execute(
                """INSERT INTO publications (version, source_identity, status)
                VALUES (%s, %s, 'staged')
                ON CONFLICT (version) DO NOTHING""",
                (version, envelope.source_identity),
            )
            connection.execute(
                """INSERT INTO publication_meetings
                (publication_version, meeting_id, payload)
                VALUES (%s, %s, %s)
                ON CONFLICT (publication_version, meeting_id) DO NOTHING""",
                (version, ids["meetings"], psycopg.types.json.Jsonb(meeting_view(envelope))),
            )

    def promote(self, version: str) -> None:
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            cursor = connection.execute(
                "UPDATE publications SET status = 'complete' WHERE version = %s",
                (version,),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("Publication version was not staged")
            connection.execute(
                "UPDATE publication_state SET current_version = %s WHERE singleton = TRUE",
                (version,),
            )

    def visible_meetings(self) -> list[dict[str, object]]:
        with psycopg.connect(
            self._database_url,
            connect_timeout=2,
            row_factory=dict_row,
        ) as connection:
            rows = connection.execute(
                """SELECT pm.payload
                FROM publication_state ps
                JOIN publications p ON p.version = ps.current_version
                JOIN publication_meetings pm ON pm.publication_version = p.version
                WHERE ps.singleton = TRUE AND p.status = 'complete'
                ORDER BY pm.payload->>'startDate', pm.meeting_id"""
            ).fetchall()
        return [row["payload"] for row in rows]

    def canonical_resource_counts(self) -> dict[str, int]:
        tables = ("competitions", "seasons", "meetings", "circuits", "provenance")
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            return {
                table: connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
                for table in tables
            }


class GraphDbProjection:
    def __init__(
        self,
        base_url: str,
        repository_id: str,
        repository_config: Path,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._repository_id = repository_id
        self._repository_config = repository_config

    @property
    def repository_url(self) -> str:
        return f"{self._base_url}/repositories/{self._repository_id}"

    def initialize(self) -> None:
        response = httpx.get(f"{self._base_url}/rest/repositories", timeout=30)
        response.raise_for_status()
        if any(repository["id"] == self._repository_id for repository in response.json()):
            return
        with self._repository_config.open("rb") as config:
            response = httpx.post(
                f"{self._base_url}/rest/repositories",
                files={"config": (self._repository_config.name, config, "text/turtle")},
                timeout=30,
            )
        response.raise_for_status()

    def project(self, version: str, envelope: CandidateEnvelope) -> None:
        graph = self._build_graph(version, envelope)
        response = httpx.put(
            f"{self.repository_url}/statements",
            params={"context": f"<{PUBLICATION_GRAPH}{version}>"},
            content=graph.serialize(format="turtle"),
            headers={"Content-Type": "text/turtle"},
            timeout=30,
        )
        response.raise_for_status()

    def agrees(self, version: str, meeting_id: str) -> bool:
        meeting_iri = self._resource_iri(meeting_id)
        query = f"""ASK WHERE {{
            GRAPH <{PUBLICATION_GRAPH}{version}> {{
                <{RESOURCE}publication/{version}> <{MOTORSPORT.includesMeeting}> <{meeting_iri}> ;
                    <{MOTORSPORT.version}> \"{version}\" .
            }}
        }}"""
        response = httpx.post(
            self.repository_url,
            data={"query": query},
            headers={"Accept": "application/sparql-results+json"},
            timeout=30,
        )
        response.raise_for_status()
        return bool(response.json()["boolean"])

    def _build_graph(self, version: str, envelope: CandidateEnvelope) -> Graph:
        ids = canonical_resource_ids(envelope)
        meeting = envelope.meeting
        graph = Graph()
        graph.bind("msh", MOTORSPORT)
        competition_iri = self._resource_iri(ids["competitions"])
        season_iri = self._resource_iri(ids["seasons"])
        meeting_iri = self._resource_iri(ids["meetings"])
        circuit_iri = self._resource_iri(ids["circuits"])
        provenance_iri = self._resource_iri(ids["provenance"])
        publication_iri = URIRef(f"{RESOURCE}publication/{version}")
        graph.add((competition_iri, RDF.type, MOTORSPORT.Competition))
        graph.add((competition_iri, RDFS.label, Literal(meeting.competition_name, lang="en")))
        graph.add((season_iri, RDF.type, MOTORSPORT.Season))
        graph.add((season_iri, MOTORSPORT.competition, competition_iri))
        graph.add((season_iri, MOTORSPORT.year, Literal(meeting.season_year, datatype=XSD.integer)))
        graph.add((circuit_iri, RDF.type, MOTORSPORT.Circuit))
        graph.add((circuit_iri, RDFS.label, Literal(meeting.circuit_name, lang="en")))
        graph.add((meeting_iri, RDF.type, MOTORSPORT.Meeting))
        graph.add((meeting_iri, RDFS.label, Literal(meeting.meeting_name, lang="en")))
        graph.add((meeting_iri, MOTORSPORT.competition, competition_iri))
        graph.add((meeting_iri, MOTORSPORT.season, season_iri))
        graph.add((meeting_iri, MOTORSPORT.circuit, circuit_iri))
        graph.add((meeting_iri, MOTORSPORT.startDate, Literal(meeting.start_date, datatype=XSD.date)))
        graph.add((meeting_iri, MOTORSPORT.endDate, Literal(meeting.end_date, datatype=XSD.date)))
        graph.add((meeting_iri, MOTORSPORT.provenance, provenance_iri))
        graph.add((provenance_iri, RDF.type, MOTORSPORT.SourceAssertion))
        graph.add((provenance_iri, MOTORSPORT.sourceUrl, URIRef(envelope.source_url)))
        graph.add((provenance_iri, MOTORSPORT.retrievedAt, Literal(envelope.retrieved_at, datatype=XSD.dateTime)))
        graph.add((publication_iri, RDF.type, MOTORSPORT.Publication))
        graph.add((publication_iri, MOTORSPORT.version, Literal(version)))
        graph.add((publication_iri, MOTORSPORT.includesMeeting, meeting_iri))
        return graph

    @staticmethod
    def _resource_iri(resource_id: str) -> URIRef:
        resource_type, identifier = resource_id.split(":", 1)
        return URIRef(f"{RESOURCE}{resource_type}/{quote(identifier, safe='')}")