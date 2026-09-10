# Issue 9: Native GraphDB Semantic Assistant

## Scope And Environment

- Branch: `feature/9-graphdb-assistant`; review baseline: `769b56a`.
- Separate local GraphDB 11.5.0, native Streamable HTTP endpoint `/mcp`.
- Native server: GraphDB MCP Server 2.0.0, negotiated protocol `2025-03-26`.
- SDK: `mcp==1.24.0`; existing Agent Framework/Azure deployment unchanged.
- No hosting, source ingestion, new publication or inferred-data migration.

## Verification Evidence

Live checks on 2026-09-10:

- Native SELECT, ASK, CONSTRUCT and DESCRIBE all worked. ASK is a JSON boolean;
  native SELECT returns a JSON-encoded TSV string; graph forms return a
  JSON-encoded Turtle string. The client uses structured RDFLib parsers.
- Disposable-repository tests put conflicting labels for the same IRI in the
  current and historical graphs. All four native forms stayed within the current
  graph. Private `evidence` content did not reach the returned graph result.
- Authenticated assistant MCP reads succeeded. Anonymous repository query: 401;
  assistant SPARQL write: 403; assistant user administration: 403.
- Applied and reread server settings: query timeout 10 seconds, result ceiling
  1,000, hard timeout error enabled. Maintenance exact RDF agreement still passed
  for all 6,592 asserted triples; statement export is not truncated by the SPARQL
  result ceiling.
- Accepted Publication remained
  `df5eb36a8bff2a30bfd9d258f0599357c9bd84abab95d5c50163ea7aaa6d0af5`.
- Live website API plus the approved Azure deployment answered the shared-circuit
  acceptance question in 22.2 seconds (HTTP 200). It returned Barcelona-Catalunya
  (`f1-circuit-15`), Monza (`f1-circuit-39`), Zandvoort (`f1-circuit-55`) and Spa
  (`f1-circuit-7`), each shared by Formula One and GT World Challenge Europe.
  The answer carried eight real source citations, canonical Circuit and Competition
  IRIs, the unchanged publication version and classification `derived`.
- The live answer explicitly distinguished derived joins of asserted facts from
  OWL inference, and did not equate shared Circuits with identical Layouts or
  complete season coverage. NLS identities were not merged by display label.
- Actual MCP SDK tests verify separate sessions per tab, cancellation/DELETE on
  reset, native errors, malformed/oversized responses, compression rejection and
  stalled calls failing within the client deadline.
- Actual provider SDK transport tests verify the five backend-owned tools,
  server-resolved citations, no native tool-list forwarding, no credentials in
  model payloads and `store=false`.

## Deliberate Limits

Global GraphDB inferred facts are not exposed: the global default graph can mix
historical and unpublished premises. The assistant identifies asserted inputs and
derived results and explains why inferred-fact retrieval is unavailable. This is
not a new OWL inference facility.

The application still uses one backend worker and ephemeral browser capabilities.
Citation validation proves retrieval, not complete entailment of arbitrary model
prose. The historical generic assistant 503 cause was not recovered by this work.

## Final Gates

Full-suite results and the two-axis review are recorded after their execution.