# GraphDB 11.5 Migration

## Initial Unlicensed Rehearsal: 2026-09-10

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

**This initial rehearsal was blocked by the vendor-issued license.** No license file was found in
the existing GraphDB configuration directory. Startup and MCP discovery are not
evidence that data queries are usable. The live service therefore remained on
10.8.10, and the existing F1/GT publication hash and 35 Meetings were verified
unchanged after the rehearsal.

The disposable container and copied volume `racing-hub-graphdb-upgrade-issue7`
were removed. No backup archive or migrated-data copy is retained. PostgreSQL
was not migrated or reset. No licensing restriction was bypassed.

## Licensed Cutover Completed: 2026-09-10

Chris supplied a local Free license file named for v11.3. Despite the filename,
GraphDB 11.5.0 accepted it: an isolated repository was created (HTTP 201), and a
SELECT query succeeded (HTTP 200). License contents were not printed or committed.
This is evidence for the supplied file, not a general cross-version entitlement.

The backend was paused, GraphDB stopped cleanly, and separate full-home rollback
and rehearsal copies were made. The old instance was restarted for comparison
while backend publication remained paused. The licensed 11.5 rehearsal passed:

- Repository identity `motorsport` and namespace mappings preserved.
- All seven asserted named graphs isomorphic to the old instance.
- Current NLS, preceding F1/GT and F1 season publication hashes and generated RDF
  agree on both versions.
- Native MCP initialization, discovery and a bounded `sparql_query` SELECT return
  the expected current publication version.

The original home volume was then upgraded to 11.5.0. Final checks:

- Seven named graphs, 13,457 asserted triples, exact isomorphism to the verified
  rehearsal, with unchanged namespace mappings.
- Current publication remains
  `df5eb36a8bff2a30bfd9d258f0599357c9bd84abab95d5c50163ea7aaa6d0af5`
  and agrees exactly with PostgreSQL's envelope.
- Restored API: 50 Meetings and 146 Sessions. PostgreSQL was not migrated or reset.
- Live native MCP: server 2.0.0, protocol 2025-03-26, nine discovered tools and a
  successful bounded SELECT against the exact current publication graph.
- `backend/tests/test_services_integration.py` and `backend/tests/test_nls.py`:
  **34 passed** against the upgraded service.

The oldest seed publication `28c1e67d2560767a65df33e9689d46daed3fa744c49f680ceca6b255c4c5ba32`
does not regenerate to its historical hash/RDF under today's application model.
This was observed on both 10.8.10 and 11.5.0, not introduced by the migration.
Its stored asserted graph was preserved exactly; no historical data was rewritten.

After the live checks and regression tests passed, the license-probe container,
rehearsal container, and both temporary named data volumes were deleted. No
rollback archive remains, as requested. Never attach 10.x to the migrated volume.

## Running The Upgraded Service

Obtain a valid GraphDB 11.5 license from the vendor and place it outside the
repository. Do not paste license contents into chat or commit them. Set
`GRAPHDB_LICENSE_FILE` to its absolute local path in the shell or an ignored `.env`
file. The default `compose.yaml` now pins 11.5.0 and mounts the license read-only.
The previously prepared `compose.graphdb11.yaml` overlay remains compatible but
is no longer required. Missing license configuration fails startup configuration
validation instead of silently reverting to an older database image.

Before using the overlay against the live volume, repeat the consistent-copy
rehearsal with the license mounted, verify exact asserted RDF for every published
named graph, repository identity, namespaces and application reads, and verify
native MCP initialization and a bounded query. Then stop the old instance and
apply the same verified upgrade to the original home volume. Never run 10.x
against an upgraded home directory: rollback requires the pre-upgrade copy.

For subsequent service operations:

```powershell
docker compose up --detach --no-deps --wait graphdb
```

Remove temporary copies only after the final instance passes the same checks,
or after restoration of the original has been verified. The supplied license
resolved the operator-input gate; no repeat PoC ingestion approval is needed.
The assistant MCP client and query authorization belong to Issues 8 and 9.

## Sources

- [Official migration guide](https://graphdb.ontotext.com/documentation/11.5/migrating-graphdb-configurations.html).
- [Official licensing requirements](https://graphdb.ontotext.com/documentation/11.5/licensing.html): GraphDB Free also requires a requested and installed license from 11.0 onward.
- [Native MCP transport](https://graphdb.ontotext.com/documentation/11.5/using-graphdb-llm-tools-with-external-clients.html).