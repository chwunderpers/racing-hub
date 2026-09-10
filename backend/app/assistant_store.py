import psycopg

from app.freshness import source_freshness_view


class AssistantReadStore:
    def __init__(self, database_url: str):
        self._database_url = database_url

    def _read(self, query, parameters=()):
        with psycopg.connect(self._database_url, connect_timeout=2,
                             options="-c default_transaction_read_only=on -c statement_timeout=3000 -c lock_timeout=1000") as connection:
            return connection.execute(query, parameters).fetchall()

    def current_publication_version(self):
        rows = self._read("SELECT current_version FROM assistant_public.state")
        return rows[0][0] if rows else None

    def visible_meetings(self, version):
        rows = self._read("SELECT payload FROM assistant_public.meetings WHERE publication_version = %s ORDER BY payload->>'startDate', payload->>'id'", (version,))
        return [{**row[0], "publicationVersion": version} for row in rows]

    def coverage(self, version):
        rows = self._read("SELECT scope FROM assistant_public.state WHERE current_version = %s", (version,))
        result = []
        for season in rows[0][0]["seasons"] if rows else []:
            assessment = season.get("coverage") or {"state": "unassessed", "activity": "present" if season.get("has_meetings") else "unknown", "reason": "Coverage has not been assessed", "source_url": season["source_url"]}
            result.append({"competitionId": "competition:" + season["competition_identity"], "season": season["season_year"], **assessment})
        return result

    def lookup_document(self, iri, version):
        rows = self._read("SELECT payload FROM assistant_public.documents WHERE publication_version = %s AND iri = %s", (version, iri))
        return rows[0][0] if rows else None

    def search_documents(self, query, version, limit=5):
        if not 1 <= len(query) <= 200 or not 1 <= limit <= 10:
            raise ValueError("Search bounds exceeded")
        rows = self._read("""SELECT payload FROM assistant_public.documents
            WHERE publication_version = %s AND terms @@ websearch_to_tsquery('english', %s)
            ORDER BY ts_rank(terms, websearch_to_tsquery('english', %s)) DESC, iri LIMIT %s""", (version, query, query, limit))
        return [row[0] for row in rows]

    def source_freshness(self):
        rows = self._read("""SELECT DISTINCT ON (source_family) source_family, checked_at, success,
            max(checked_at) FILTER (WHERE success) OVER (PARTITION BY source_family), pending
            FROM assistant_public.freshness ORDER BY source_family, checked_at DESC""")
        attempts = {row[0]: {"checkedAt": row[1].isoformat(), "success": row[2], "lastSuccessAt": row[3].isoformat() if row[3] else None, "pending": row[4]} for row in rows}
        meetings = self.visible_meetings(self.current_publication_version())
        competitions = {meeting["competitionId"].removeprefix("competition:") for meeting in meetings}
        return source_freshness_view(attempts, competitions)