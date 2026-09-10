# GraphDB 11.5 Migration

## Verified Rehearsal: 2026-09-10

The user authorized migration and temporary backups as part of Issue 7. Target:
`ontotext/graphdb:11.5.0`, downloaded digest
`sha256:d688879c4e5751a0c323f996d86bf1b2189191290711b1936e211d4510b53485`.

GraphDB 10.8.10 was stopped for a consistent copy of its entire home volume,
including `data`, `conf` and `work`. The original service was then restarted.
The copy ran on loopback port 7201 under GraphDB 11.5.0. Results:

- Repository discovery: HTTP 200, existing `motorsport` identity preserved.
- Native `/mcp` initialization: HTTP 200, protocol `2025-03-26`, server
  `GraphDB MCP Server` version `2.0.0`, tools/prompts/logging capabilities.
- Repository SELECT: HTTP 500, `Query evaluation error: No license was set`.

**Cutover is blocked by the vendor-issued license.** No license file was found in
the existing GraphDB configuration directory. Startup and MCP discovery are not
evidence that data queries are usable. The live service therefore remains on
10.8.10, and the existing F1/GT publication hash and 35 Meetings were verified
unchanged after the rehearsal.

The disposable container and copied volume `racing-hub-graphdb-upgrade-issue7`
were removed. No backup archive or migrated-data copy is retained. PostgreSQL
was not migrated or reset. No licensing restriction was bypassed.

## Completing The Cutover

Obtain a valid GraphDB 11.5 license from the vendor and place it outside the
repository. Do not paste license contents into chat or commit them. Set
`GRAPHDB_LICENSE_FILE` to its absolute local path. The prepared
`compose.graphdb11.yaml` overlay pins 11.5.0 and mounts this file read-only.

Before using the overlay against the live volume, repeat the consistent-copy
rehearsal with the license mounted, verify exact asserted RDF for every published
named graph, repository identity, namespaces and application reads, and verify
native MCP initialization and a bounded query. Then stop the old instance and
apply the same verified upgrade to the original home volume. Never run 10.x
against an upgraded home directory: rollback requires the pre-upgrade copy.

Use both Compose files for subsequent service operations after cutover:

```powershell
docker compose -f compose.yaml -f compose.graphdb11.yaml up --detach --no-deps graphdb
```

Remove temporary copies only after the final instance passes the same checks,
or after restoration of the original has been verified. A working license is
the remaining operator input; no repeat PoC ingestion approval is needed.
The assistant MCP client and query authorization belong to Issues 8 and 9.

## Sources

- [Official migration guide](https://graphdb.ontotext.com/documentation/11.5/migrating-graphdb-configurations.html).
- [Official licensing requirements](https://graphdb.ontotext.com/documentation/11.5/licensing.html): GraphDB Free also requires a requested and installed license from 11.0 onward.
- [Native MCP transport](https://graphdb.ontotext.com/documentation/11.5/using-graphdb-llm-tools-with-external-clients.html).