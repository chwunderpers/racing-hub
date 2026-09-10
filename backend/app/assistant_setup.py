import os
import secrets
from pathlib import Path

import psycopg
from dotenv import set_key
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app.stores import GraphDbProjection, PostgresOperationalStore


def provision_reader(database_url: str, role: str, password: str) -> str:
    with psycopg.connect(database_url, connect_timeout=5) as connection:
        existing = connection.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (role,)).fetchone()
        verb = sql.SQL("ALTER ROLE") if existing else sql.SQL("CREATE ROLE")
        connection.execute(sql.SQL("{} {} LOGIN PASSWORD {} NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION").format(verb, sql.Identifier(role), sql.Literal(password)))
        connection.execute(sql.SQL("ALTER ROLE {} SET default_transaction_read_only = on").format(sql.Identifier(role)))
        connection.execute(sql.SQL("ALTER ROLE {} SET statement_timeout = '3s'").format(sql.Identifier(role)))
        connection.execute(sql.SQL("GRANT USAGE ON SCHEMA assistant_public TO {}").format(sql.Identifier(role)))
        connection.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA assistant_public TO {}").format(sql.Identifier(role)))
    settings = conninfo_to_dict(database_url)
    settings.update(user=role, password=password)
    return make_conninfo(**settings)


def main():
    database_url = os.environ["DATABASE_URL"]
    store = PostgresOperationalStore(database_url)
    store.initialize()
    with store.publication_lock():
        version = store.current_publication_version()
        if version:
            envelope = store.publication_envelope(version)
            graph = GraphDbProjection(os.environ["GRAPHDB_URL"], "motorsport", Path("graphdb/repository-config.ttl"))
            if not graph.agrees(version, "", envelope):
                raise RuntimeError("Current publication graph does not agree; search backfill aborted")
            store.stage(version, envelope)
    password = secrets.token_urlsafe(36)
    connection_string = provision_reader(database_url, "racing_assistant", password)
    local_path = Path(".env")
    set_key(local_path, "ASSISTANT_DATABASE_URL", connection_string)
    docker_settings = conninfo_to_dict(connection_string)
    docker_settings["host"] = "database"
    set_key(local_path, "ASSISTANT_DOCKER_DATABASE_URL", make_conninfo(**docker_settings))
    print("Published search documents prepared and restricted assistant login configured. No credentials displayed.")


if __name__ == "__main__":
    main()