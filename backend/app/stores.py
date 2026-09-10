from pathlib import Path
import hashlib
from contextlib import contextmanager
from collections.abc import Iterator
from urllib.parse import quote

import httpx
import psycopg
from psycopg.rows import dict_row
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef, XSD
from rdflib.compare import isomorphic

from app.publication import CandidateEnvelope, CandidateLayout, PublicationCandidate, PublicationSnapshot, ScheduledEnvelope, ScheduledMeeting, candidate_meetings, parse_candidate, canonical_resource_ids, meeting_view, coverage_view


MOTORSPORT = Namespace("https://w3id.org/motorsport-hub/ontology/")
RESOURCE = "https://w3id.org/motorsport-hub/resource/"
PUBLICATION_GRAPH = "https://w3id.org/motorsport-hub/graph/publication/"


SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS search;
CREATE TABLE IF NOT EXISTS search.documents (
    publication_version TEXT NOT NULL,
    iri TEXT NOT NULL,
    payload JSONB NOT NULL,
    terms TSVECTOR NOT NULL,
    PRIMARY KEY (publication_version, iri)
);
CREATE INDEX IF NOT EXISTS documents_terms ON search.documents USING GIN (terms);
CREATE TABLE IF NOT EXISTS source_attempts (
    checked_at TIMESTAMPTZ PRIMARY KEY,
    success BOOLEAN NOT NULL,
    pending BOOLEAN NOT NULL DEFAULT FALSE
);
ALTER TABLE source_attempts ADD COLUMN IF NOT EXISTS pending BOOLEAN NOT NULL DEFAULT FALSE;
CREATE TABLE IF NOT EXISTS source_checks (
    source_family TEXT NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL,
    success BOOLEAN NOT NULL,
    pending BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (source_family, checked_at)
);
INSERT INTO source_checks (source_family, checked_at, success, pending)
SELECT 'formula-one', checked_at, success, pending FROM source_attempts
ON CONFLICT DO NOTHING;
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
CREATE TABLE IF NOT EXISTS publication_envelopes (
    publication_version TEXT PRIMARY KEY REFERENCES publications(version),
    payload JSONB NOT NULL
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
CREATE SCHEMA IF NOT EXISTS assistant_public;
CREATE OR REPLACE VIEW assistant_public.state AS
SELECT ps.current_version, jsonb_build_object('seasons', COALESCE((
    SELECT jsonb_agg(jsonb_build_object('competition_identity', season->'competition_identity',
        'season_year', season->'season_year', 'coverage', season->'coverage',
        'source_url', season->'source_url', 'has_meetings', jsonb_array_length(season->'meetings') > 0))
    FROM jsonb_array_elements(COALESCE(e.payload->'seasons',
        CASE WHEN e.payload ? 'meetings' THEN jsonb_build_array(e.payload) ELSE '[]'::jsonb END)) season
), '[]'::jsonb)) AS scope
FROM publication_state ps LEFT JOIN publication_envelopes e ON e.publication_version = ps.current_version;
CREATE OR REPLACE VIEW assistant_public.meetings AS
SELECT pm.publication_version, (pm.payload - 'fieldAssertions') || jsonb_build_object('publicAssertions', COALESCE((
    SELECT jsonb_agg(jsonb_build_object('field', assertion->'field', 'value', assertion->'value',
        'subject_identity', assertion->'subject_identity', 'effective_local', assertion->'effective_local',
        'preferred', assertion->'preferred', 'source_url', assertion->'source_url', 'retrieved_at', assertion->'retrieved_at'))
    FROM jsonb_array_elements(COALESCE(pm.payload->'fieldAssertions', '[]'::jsonb)) assertion
), '[]'::jsonb)) AS payload
FROM publication_meetings pm JOIN publication_state ps ON ps.current_version = pm.publication_version
JOIN publications p ON p.version = pm.publication_version WHERE p.status = 'complete';
CREATE OR REPLACE VIEW assistant_public.documents AS
SELECT d.publication_version, d.iri, d.payload, d.terms
FROM search.documents d JOIN publication_state ps ON ps.current_version = d.publication_version
JOIN publications p ON p.version = d.publication_version WHERE p.status = 'complete';
CREATE OR REPLACE VIEW assistant_public.freshness AS
SELECT source_family, checked_at, success, pending FROM source_checks;
"""


class PostgresOperationalStore:
    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def initialize(self) -> None:
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            connection.execute(SCHEMA_SQL)

    def assistant_reader(self):
        from app.assistant_store import AssistantReadStore
        return AssistantReadStore(self._database_url)

    def record_source_attempt(self, checked_at, success: bool, pending: bool = False, source_family: str = "formula-one") -> None:
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            connection.execute("INSERT INTO source_checks (source_family, checked_at, success, pending) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING", (source_family, checked_at, success, pending))

    def source_freshness(self) -> dict:
        from app.freshness import source_freshness_view
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            try:
                rows = connection.execute("SELECT DISTINCT ON (source_family) source_family, checked_at, success, max(checked_at) FILTER (WHERE success) OVER (PARTITION BY source_family), pending FROM source_checks ORDER BY source_family, checked_at DESC").fetchall()
            except psycopg.errors.UndefinedTable:
                rows = []
        attempts = {row[0]: {"checkedAt": row[1].isoformat(), "success": row[2], "lastSuccessAt": row[3].isoformat() if row[3] else None, "pending": row[4]} for row in rows}
        version = self.current_publication_version()
        competitions = {entry.meeting.competition_identity for entry in candidate_meetings(self.publication_envelope(version))} if version else set()
        return source_freshness_view(attempts, competitions)

    @contextmanager
    def publication_lock(self) -> Iterator[None]:
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            row = connection.execute("SELECT pg_try_advisory_xact_lock(426804)").fetchone()
            if row is None or not row[0]:
                raise RuntimeError("Another publication is in progress")
            yield

    def current_publication_version(self) -> str | None:
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            row = connection.execute("SELECT current_version FROM publication_state WHERE singleton").fetchone()
            return row[0] if row else None

    def stage(self, version: str, envelope: PublicationCandidate) -> None:
        from app.documentation import canonical_documents
        documents = canonical_documents(GraphDbProjection.build_graph(version, envelope), version)
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            connection.execute(
                "INSERT INTO publications (version, source_identity, status) VALUES (%s, %s, 'staged') ON CONFLICT DO NOTHING",
                (version, envelope.source_identity),
            )
            connection.execute(
                "INSERT INTO publication_envelopes (publication_version, payload) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (version, psycopg.types.json.Jsonb(envelope.model_dump(mode="json"))),
            )
            for entry in candidate_meetings(envelope):
                self._stage_meeting(connection, version, entry)
            for document in documents:
                connection.execute(
                    """INSERT INTO search.documents (publication_version, iri, payload, terms)
                    VALUES (%s, %s, %s, to_tsvector('english', %s))
                    ON CONFLICT (publication_version, iri) DO UPDATE
                    SET payload = EXCLUDED.payload, terms = EXCLUDED.terms""",
                    (version, document["iri"], psycopg.types.json.Jsonb(document), document["title"] + " " + document["markdown"]),
                )

    def lookup_document(self, iri: str, version: str) -> dict | None:
        with psycopg.connect(self._database_url, connect_timeout=2) as connection:
            row = connection.execute(
                """SELECT d.payload FROM search.documents d JOIN publications p ON p.version = d.publication_version
                WHERE p.status = 'complete' AND d.publication_version = %s AND d.iri = %s""",
                (version, iri),
            ).fetchone()
        return row[0] if row else None

    def replace_search_documents(self, version: str, documents: list[dict]) -> None:
        from app.documentation import project_markdown
        envelope = self.publication_envelope(version)
        project_markdown([document["markdown"] for document in documents], GraphDbProjection.build_graph(version, envelope), version)
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            status = connection.execute("SELECT status FROM publications WHERE version = %s FOR UPDATE", (version,)).fetchone()
            if not status or status[0] != "staged":
                raise ValueError("Only staged search documents may be replaced")
            connection.execute("DELETE FROM search.documents WHERE publication_version = %s", (version,))
            for document in documents:
                connection.execute("""INSERT INTO search.documents (publication_version, iri, payload, terms)
                    VALUES (%s, %s, %s, to_tsvector('english', %s))""",
                    (version, document["iri"], psycopg.types.json.Jsonb(document), document["title"] + " " + document["markdown"]))

    def search_documents(self, query: str, version: str, limit: int = 10) -> list[dict]:
        if not 1 <= len(query) <= 200 or not 1 <= limit <= 20:
            raise ValueError("Search bounds exceeded")
        with psycopg.connect(self._database_url, connect_timeout=2) as connection:
            rows = connection.execute(
                """SELECT d.payload FROM search.documents d JOIN publications p ON p.version = d.publication_version
                WHERE p.status = 'complete' AND d.publication_version = %s
                AND d.terms @@ websearch_to_tsquery('english', %s)
                ORDER BY ts_rank(d.terms, websearch_to_tsquery('english', %s)) DESC, d.iri LIMIT %s""",
                (version, query, query, limit),
            ).fetchall()
        return [row[0] for row in rows]

    def _stage_meeting(self, connection, version: str, envelope: CandidateEnvelope) -> None:
        ids = canonical_resource_ids(envelope)
        meeting = envelope.meeting
        with connection.transaction():
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
                """INSERT INTO publication_meetings
                (publication_version, meeting_id, payload)
                VALUES (%s, %s, %s)
                ON CONFLICT (publication_version, meeting_id) DO NOTHING""",
                (version, ids["meetings"], psycopg.types.json.Jsonb(meeting_view(envelope))),
            )

    def publication_envelope(self, version: str) -> PublicationCandidate:
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            row = connection.execute(
                "SELECT payload FROM publication_envelopes WHERE publication_version = %s",
                (version,),
            ).fetchone()
        if row is None:
            raise LookupError("Publication envelope not found")
        return parse_candidate(row[0])

    def promote(self, version: str) -> None:
        from app.documentation import canonical_documents
        with psycopg.connect(self._database_url, connect_timeout=5) as connection:
            row = connection.execute("SELECT payload FROM publication_envelopes WHERE publication_version = %s", (version,)).fetchone()
            if row is None:
                raise RuntimeError("Publication version was not staged")
            expected = canonical_documents(GraphDbProjection.build_graph(version, parse_candidate(row[0])), version)
            actual = connection.execute("SELECT payload FROM search.documents WHERE publication_version = %s ORDER BY iri", (version,)).fetchall()
            if [entry[0] for entry in actual] != expected:
                raise RuntimeError("Search projection does not agree with publication")
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

    def visible_meetings(self, version: str | None = None) -> list[dict[str, object]]:
        with psycopg.connect(
            self._database_url,
            connect_timeout=2,
            row_factory=dict_row,
        ) as connection:
            rows = connection.execute(
                """SELECT pm.payload, p.version
                FROM publication_state ps
                JOIN publications p ON p.version = COALESCE(%s, ps.current_version)
                JOIN publication_meetings pm ON pm.publication_version = p.version
                WHERE ps.singleton = TRUE AND p.status = 'complete'
                ORDER BY pm.payload->>'startDate', pm.meeting_id""",
                (version,),
            ).fetchall()
        if not rows:
            return []
        identities = {canonical_resource_ids(entry)["meetings"]: canonical_resource_ids(entry) for entry in candidate_meetings(self.publication_envelope(rows[0]["version"]))}
        return [{**row["payload"], "competitionId": identities[row["payload"]["id"]]["competitions"], "circuitId": identities[row["payload"]["id"]]["circuits"], "publicationVersion": row["version"]} for row in rows]

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

    def project(self, version: str, envelope: PublicationCandidate) -> None:
        graph = self._build_graph(version, envelope)
        response = httpx.put(
            f"{self.repository_url}/statements",
            params={"context": f"<{PUBLICATION_GRAPH}{version}>"},
            content=graph.serialize(format="turtle"),
            headers={"Content-Type": "text/turtle"},
            timeout=30,
        )
        response.raise_for_status()

    def agrees(self, version: str, meeting_id: str, envelope: PublicationCandidate | None = None) -> bool:
        if envelope is not None:
            response = httpx.get(
                f"{self.repository_url}/statements",
                params={"context": f"<{PUBLICATION_GRAPH}{version}>", "infer": "false"},
                headers={"Accept": "application/n-triples"},
                timeout=30,
            )
            response.raise_for_status()
            actual = Graph().parse(data=response.text, format="nt")
            return isomorphic(actual, self._build_graph(version, envelope))
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

    def _build_graph(self, version: str, envelope: PublicationCandidate) -> Graph:
        return self.build_graph(version, envelope)

    @classmethod
    def build_graph(cls, version: str, envelope: PublicationCandidate) -> Graph:
        if not isinstance(envelope, CandidateEnvelope):
            graph = Graph()
            for entry in candidate_meetings(envelope):
                graph += cls.build_graph(version, entry)
            seasons = envelope.seasons if isinstance(envelope, PublicationSnapshot) else [envelope]
            for season in seasons:
                if season.coverage is None:
                    continue
                assessment = coverage_view(season)[0]
                season_iri = cls._resource_iri(f"season:{assessment['competitionId']}:{assessment['season']}")
                graph.add((season_iri, RDF.type, MOTORSPORT.Season))
                graph.add((season_iri, MOTORSPORT.coverageState, Literal(assessment["state"])))
                graph.add((season_iri, MOTORSPORT.activity, Literal(assessment["activity"])))
                graph.add((season_iri, MOTORSPORT.coverageReason, Literal(assessment["reason"], lang="en")))
                graph.add((season_iri, MOTORSPORT.sourceUrl, URIRef(assessment["source_url"])))
                publication_iri = URIRef(f"{RESOURCE}publication/{version}")
                graph.add((publication_iri, RDF.type, MOTORSPORT.Publication))
                graph.add((publication_iri, MOTORSPORT.version, Literal(version)))
                graph.add((publication_iri, MOTORSPORT.includesSeason, season_iri))
            return graph
        ids = canonical_resource_ids(envelope)
        meeting = envelope.meeting
        graph = Graph()
        graph.bind("msh", MOTORSPORT)
        competition_iri = cls._resource_iri(ids["competitions"])
        season_iri = cls._resource_iri(ids["seasons"])
        meeting_iri = cls._resource_iri(ids["meetings"])
        circuit_iri = cls._resource_iri(ids["circuits"])
        provenance_iri = cls._resource_iri(ids["provenance"])
        publication_iri = URIRef(f"{RESOURCE}publication/{version}")
        graph.add((competition_iri, RDF.type, MOTORSPORT.Competition))
        graph.add((competition_iri, RDFS.label, Literal(meeting.competition_name, lang="en")))
        graph.add((season_iri, RDF.type, MOTORSPORT.Season))
        graph.add((season_iri, MOTORSPORT.competition, competition_iri))
        graph.add((season_iri, MOTORSPORT.year, Literal(meeting.season_year, datatype=XSD.integer)))
        graph.add((circuit_iri, RDF.type, MOTORSPORT.Circuit))
        graph.add((circuit_iri, RDFS.label, Literal(meeting.circuit_name, lang="en")))
        graph.add((meeting_iri, RDF.type, MOTORSPORT.Meeting))
        graph.add((meeting_iri, MOTORSPORT.status, Literal(meeting.status)))
        graph.add((meeting_iri, RDFS.label, Literal(meeting.meeting_name, lang="en")))
        graph.add((meeting_iri, MOTORSPORT.competition, competition_iri))
        graph.add((meeting_iri, MOTORSPORT.season, season_iri))
        graph.add((meeting_iri, MOTORSPORT.circuit, circuit_iri))
        graph.add((meeting_iri, MOTORSPORT.startDate, Literal(meeting.start_date, datatype=XSD.date)))
        graph.add((meeting_iri, MOTORSPORT.endDate, Literal(meeting.end_date, datatype=XSD.date)))
        graph.add((meeting_iri, MOTORSPORT.provenance, provenance_iri))
        graph.add((provenance_iri, RDF.type, MOTORSPORT.SourceAssertion))
        graph.add((provenance_iri, MOTORSPORT.sourceIdentity, Literal(envelope.source_identity)))
        graph.add((provenance_iri, MOTORSPORT.evidence, Literal(envelope.evidence, lang="en")))
        graph.add((provenance_iri, MOTORSPORT.sourceLanguage, Literal(envelope.source_language)))
        graph.add((provenance_iri, MOTORSPORT.sourceUrl, URIRef(envelope.source_url)))
        graph.add((provenance_iri, MOTORSPORT.retrievedAt, Literal(envelope.retrieved_at, datatype=XSD.dateTime)))
        graph.add((publication_iri, RDF.type, MOTORSPORT.Publication))
        graph.add((publication_iri, MOTORSPORT.version, Literal(version)))
        graph.add((publication_iri, MOTORSPORT.includesMeeting, meeting_iri))
        if isinstance(envelope, ScheduledEnvelope):
            subjects = {entry.identity: cls._resource_iri(f"round:{entry.identity}") for entry in envelope.meeting.rounds}
            subjects.update({session.identity: cls._resource_iri(f"session:{session.identity}") for session in envelope.meeting.sessions})
            for assertion in envelope.field_assertions:
                digest = hashlib.sha256(assertion.model_dump_json().encode("utf-8")).hexdigest()
                assertion_iri = cls._resource_iri(f"assertion:{envelope.source_identity}:{digest}")
                graph.add((meeting_iri, MOTORSPORT.fieldAssertion, assertion_iri))
                graph.add((assertion_iri, RDF.type, MOTORSPORT.SourceAssertion))
                graph.add((assertion_iri, MOTORSPORT.subject, subjects.get(assertion.subject_identity, circuit_iri if assertion.field.startswith("circuit_") else meeting_iri)))
                graph.add((assertion_iri, MOTORSPORT.field, Literal(assertion.field)))
                graph.add((assertion_iri, MOTORSPORT.value, Literal(assertion.value)))
                graph.add((assertion_iri, MOTORSPORT.locator, Literal(assertion.locator)))
                graph.add((assertion_iri, MOTORSPORT.rule, Literal(assertion.rule)))
                graph.add((assertion_iri, MOTORSPORT.preferred, Literal(assertion.preferred)))
                graph.add((assertion_iri, MOTORSPORT.sourceUrl, URIRef(assertion.source_url)))
                graph.add((assertion_iri, MOTORSPORT.retrievedAt, Literal(assertion.retrieved_at, datatype=XSD.dateTime)))
                if assertion.response_sha256:
                    graph.add((assertion_iri, MOTORSPORT.responseSha256, Literal(assertion.response_sha256)))
                if assertion.effective_local:
                    graph.add((assertion_iri, MOTORSPORT.effectiveLocal, Literal(assertion.effective_local)))
                if assertion.translation:
                    graph.add((assertion_iri, MOTORSPORT.sourceLanguage, Literal(assertion.translation.source_language)))
                    graph.add((assertion_iri, MOTORSPORT.translationMethod, Literal(assertion.translation.method, lang="en")))
                    graph.add((assertion_iri, MOTORSPORT.translationVersion, Literal(assertion.translation.version)))
                    graph.add((assertion_iri, MOTORSPORT.translatedAt, Literal(assertion.translation.translated_at, datatype=XSD.dateTime)))
                    graph.add((assertion_iri, MOTORSPORT.translationReviewState, Literal(assertion.translation.review_state)))
                    graph.add((assertion_iri, MOTORSPORT.translationReviewer, Literal(assertion.translation.reviewer, lang="en")))
                    graph.add((assertion_iri, MOTORSPORT.translationAuthorization, Literal(assertion.translation.authorization, lang="en")))
        if isinstance(meeting, ScheduledMeeting):
            round_iri = cls._resource_iri(f"round:{envelope.source_identity}") if meeting.round_number is not None else None
            for entry in meeting.rounds:
                explicit_round = cls._resource_iri(f"round:{entry.identity}")
                graph.add((explicit_round, RDF.type, MOTORSPORT.Round))
                graph.add((explicit_round, RDFS.label, Literal(entry.name, lang="en")))
                graph.add((explicit_round, MOTORSPORT.meeting, meeting_iri))
                graph.add((explicit_round, MOTORSPORT.season, season_iri))
                graph.add((explicit_round, MOTORSPORT.number, Literal(entry.number, datatype=XSD.integer)))
                graph.add((explicit_round, MOTORSPORT.status, Literal(entry.status)))
            if meeting.venue:
                venue_iri = cls._resource_iri(f"venue:{meeting.venue.identity}")
                graph.add((venue_iri, RDF.type, MOTORSPORT.Venue))
                graph.add((venue_iri, RDFS.label, Literal(meeting.venue.name, lang="en")))
                graph.add((meeting_iri, MOTORSPORT.venue, venue_iri))
                graph.add((circuit_iri, MOTORSPORT.venue, venue_iri))
            if meeting.layout:
                layout_iri = cls._add_layout(graph, meeting.layout, circuit_iri)
                graph.add((meeting_iri, MOTORSPORT.layout, layout_iri))
            if meeting.coverage:
                graph.add((meeting_iri, MOTORSPORT.coverageState, Literal(meeting.coverage.state)))
                graph.add((meeting_iri, MOTORSPORT.activity, Literal(meeting.coverage.activity)))
                graph.add((meeting_iri, MOTORSPORT.coverageReason, Literal(meeting.coverage.reason, lang="en")))
            if meeting.kind != "championship":
                graph.add((meeting_iri, MOTORSPORT.kind, Literal(meeting.kind)))
            if round_iri is not None:
                graph.add((round_iri, RDF.type, MOTORSPORT.Round))
                graph.add((round_iri, MOTORSPORT.meeting, meeting_iri))
                graph.add((round_iri, MOTORSPORT.season, season_iri))
                graph.add((round_iri, MOTORSPORT.number, Literal(meeting.round_number, datatype=XSD.integer)))
            if meeting.event_timezone:
                graph.add((meeting_iri, MOTORSPORT.timeZone, Literal(meeting.event_timezone)))
            for session in meeting.sessions:
                session_iri = cls._resource_iri(f"session:{session.identity}")
                graph.add((session_iri, RDF.type, MOTORSPORT.Session))
                graph.add((session_iri, RDFS.label, Literal(session.name, lang="en")))
                graph.add((session_iri, MOTORSPORT.meeting, meeting_iri))
                if round_iri is not None:
                    graph.add((session_iri, MOTORSPORT.round, round_iri))
                if session.round_identity:
                    graph.add((session_iri, MOTORSPORT.round, cls._resource_iri(f"round:{session.round_identity}")))
                if session.duration_minutes is not None:
                    graph.add((session_iri, MOTORSPORT.durationMinutes, Literal(session.duration_minutes, datatype=XSD.integer)))
                session_circuit = circuit_iri
                if session.circuit_identity:
                    session_circuit = cls._resource_iri(f"circuit:{session.circuit_identity}")
                    graph.add((session_circuit, RDF.type, MOTORSPORT.Circuit))
                    graph.add((session_iri, MOTORSPORT.circuit, session_circuit))
                    if meeting.venue:
                        graph.add((session_circuit, MOTORSPORT.venue, venue_iri))
                if session.layout:
                    session_layout = cls._add_layout(graph, session.layout, session_circuit)
                    graph.add((session_iri, MOTORSPORT.layout, session_layout))
                graph.add((session_iri, MOTORSPORT.status, Literal(session.status)))
                graph.add((session_iri, MOTORSPORT.provenance, provenance_iri))
                for label, clock in (("start", session.start), ("end", session.end)):
                    if clock is None:
                        continue
                    graph.add((session_iri, MOTORSPORT[label + "Local"], Literal(clock.local)))
                    if clock.offset:
                        graph.add((session_iri, MOTORSPORT[label + "Offset"], Literal(clock.offset)))
                    if clock.zone:
                        graph.add((session_iri, MOTORSPORT[label + "Zone"], Literal(clock.zone)))
                    if clock.instant:
                        graph.add((session_iri, MOTORSPORT[label + "Instant"], Literal(clock.instant, datatype=XSD.dateTime)))
        return graph

    @classmethod
    def _add_layout(cls, graph: Graph, layout: CandidateLayout, circuit: URIRef) -> URIRef:
        layout_iri = cls._resource_iri(f"layout:{layout.identity}")
        graph.add((layout_iri, RDF.type, MOTORSPORT.Layout))
        graph.add((layout_iri, RDFS.label, Literal(layout.name, lang="en")))
        graph.add((layout_iri, MOTORSPORT.circuit, circuit))
        if layout.length_km is not None:
            graph.add((layout_iri, MOTORSPORT.lengthKm, Literal(layout.length_km)))
        return layout_iri

    @staticmethod
    def _resource_iri(resource_id: str) -> URIRef:
        resource_type, identifier = resource_id.split(":", 1)
        return URIRef(f"{RESOURCE}{resource_type}/{quote(identifier, safe='')}")