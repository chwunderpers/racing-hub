import os

import httpx

from app.graph_mcp import GraphMcpClient


def maintenance_auth():
    username = os.environ.get("GRAPHDB_MAINTENANCE_USER")
    password = os.environ.get("GRAPHDB_MAINTENANCE_PASSWORD")
    return httpx.BasicAuth(username, password) if username and password else None


def configured_graph_factory():
    endpoint = os.environ.get("GRAPHDB_MCP_URL")
    username = os.environ.get("GRAPHDB_ASSISTANT_USER")
    password = os.environ.get("GRAPHDB_ASSISTANT_PASSWORD")
    if not endpoint or not username or not password:
        return None
    return lambda version: GraphMcpClient(endpoint, version, username, password)