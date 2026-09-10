import os
import secrets
from pathlib import Path

import httpx
from dotenv import dotenv_values, set_key
from rdflib import Graph, Literal, URIRef


def configure_local_graphdb(base_url: str, env_path: Path):
    settings = {**dotenv_values(env_path), **os.environ}
    admin_user = settings.get("GRAPHDB_ADMIN_USER")
    admin_password = settings.get("GRAPHDB_ADMIN_PASSWORD")
    auth = httpx.BasicAuth(admin_user, admin_password) if admin_user and admin_password else None
    with httpx.Client(base_url=base_url, auth=auth, timeout=30, follow_redirects=False) as client:
        response = client.get("/rest/security")
        response.raise_for_status()
        enabled = response.json()
        if enabled and auth is None:
            raise RuntimeError("Configure local GraphDB administrator credentials before setup")
        default_admin = False
        if not enabled:
            login = client.post("/rest/login", json={"username": "admin", "password": "root"})
            default_admin = login.is_success
        users = [("GRAPHDB_ADMIN", "racing_admin", ["ROLE_ADMIN"]),
                 ("GRAPHDB_MAINTENANCE", "racing_maintenance", ["ROLE_USER", "READ_REPO_motorsport", "WRITE_REPO_motorsport"]),
                 ("GRAPHDB_ASSISTANT", "racing_assistant", ["ROLE_USER", "READ_REPO_motorsport"])]
        for prefix, name, authorities in users:
            if prefix == "GRAPHDB_ADMIN" and enabled:
                continue
            existing = client.get("/rest/security/users/" + name)
            password = settings.get(prefix + "_PASSWORD")
            if existing.status_code == 200 and not password:
                raise RuntimeError("Existing GraphDB account has no locally managed credential; refusing to replace it")
            password = password or secrets.token_urlsafe(36)
            set_key(env_path, prefix + "_USER", name)
            set_key(env_path, prefix + "_PASSWORD", password)
            method = "PUT" if existing.status_code == 200 else "POST"
            if existing.status_code not in {200, 404}:
                existing.raise_for_status()
            response = client.request(method, "/rest/security/users/" + name, json={"username": name,
                "password": password, "grantedAuthorities": authorities, "appSettings": {}})
            response.raise_for_status()
            if prefix == "GRAPHDB_ADMIN":
                admin_user, admin_password = name, password
        client.auth = httpx.BasicAuth(admin_user, admin_password)
        if default_admin:
            response = client.put("/rest/security/users/admin", json={"username": "admin", "password": "",
                "grantedAuthorities": ["ROLE_ADMIN"], "appSettings": {}})
            response.raise_for_status()
        response = client.post("/rest/security/free-access", json={"enabled": False, "authorities": [], "appSettings": {}})
        response.raise_for_status()
        response = client.post("/rest/security", json=True)
        response.raise_for_status()
        response = client.get("/rest/repositories/motorsport", headers={"Accept": "text/turtle"})
        response.raise_for_status()
        graph = Graph().parse(data=response.text, format="turtle")
        namespace = "http://www.ontotext.com/config/graphdb#"
        predicate = URIRef(namespace + "query-timeout")
        subject = next(graph.subjects(predicate, None))
        for name, value in {"query-timeout": "10", "query-limit-results": "1000", "throw-QueryEvaluationException-on-timeout": "true"}.items():
            graph.set((subject, URIRef(namespace + name), Literal(value)))
        response = client.put("/rest/repositories/motorsport", files={"config": ("repository.ttl", graph.serialize(format="turtle"), "text/turtle")})
        response.raise_for_status()
    set_key(env_path, "GRAPHDB_MCP_URL", base_url.rstrip("/") + "/mcp")
    print("GraphDB security and query limits configured; credentials remain in ignored local configuration. Restart GraphDB to apply limits.")


if __name__ == "__main__":
    configure_local_graphdb(os.environ.get("GRAPHDB_URL", "http://localhost:7200"), Path(".env"))