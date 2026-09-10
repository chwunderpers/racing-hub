import os
import secrets
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from app.assistant_setup import provision_reader
from app.assistant_store import AssistantReadStore


def test_assistant_principal_cannot_read_envelopes_or_modify_data(isolated_services, isolated_database_url):
    role = "assistant_test_" + uuid4().hex
    store, graph = isolated_services
    import json
    from pathlib import Path
    from app.publication import CandidateEnvelope, PublicationModule
    candidate = CandidateEnvelope.model_validate(json.loads((Path(__file__).parents[1] / "fixtures/f1-2026-australia.json").read_text("utf-8")))
    version = PublicationModule(store, graph).publish(candidate).version
    database_url = isolated_database_url
    try:
        read_url = provision_reader(database_url, role, secrets.token_urlsafe(32))
        reader = AssistantReadStore(read_url)
        assert reader.current_publication_version() == version
        assert len(reader.visible_meetings(version)) == 1
        assert reader.search_documents("Australian", version)
        for query in ("SELECT * FROM publication_envelopes", "SELECT * FROM provenance", "DELETE FROM assistant_public.documents", "CREATE TABLE assistant_public.bad (id integer)"):
            with psycopg.connect(read_url) as connection:
                with pytest.raises(psycopg.Error):
                    connection.execute(query)
    finally:
        with psycopg.connect(database_url) as connection:
            connection.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
        with psycopg.connect(os.environ["TEST_DATABASE_URL"]) as connection:
            connection.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))