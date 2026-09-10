# Assistant and GraphDB Prerequisites

Research date: 2026-09-10. Scope: the supplied Issue 8/9 requirements, not a fresh issue-tracker review. This is research only, not an implementation or approval to change infrastructure. Microsoft facts were investigated through Microsoft Learn search, fetch, and code-sample search, then checked against release-tagged package metadata/source where APIs differed. GraphDB facts come from its official versioned documentation.

## Decision Summary

- The Python 3.12/FastAPI assistant shell, explicit provider configuration interface, per-tab ephemeral sessions, typed PostgreSQL tools, and SPARQL policy boundary can be implemented without a live model or upgraded GraphDB. Offline doubles cannot establish real provider or native MCP compatibility.
- The latest published stable `agent-framework` verified on the research date is **1.18.0**. Its core metadata supports Python 3.12. Examined dependency ranges overlap the existing FastAPI stack; a complete dependency resolution and runtime check remain future gates, not completed verification.
- **GraphDB 11.1.0, released 2025-08-21, introduced the built-in MCP server** (GDB-12656). The current `ontotext/graphdb:10.8.10` cannot satisfy native MCP. **11.3 introduced Streamable HTTP**, the transport supported by the selected framework client; 11.1/11.2 used legacy SSE only. Current documentation is for 11.5.0, released 2026-08-19. These are evidence, not an approved upgrade target. [G1][G2][G3]
- Native MCP documents `SELECT`, `CONSTRUCT`, and `DESCRIBE`, **not `ASK`**. Ordinary SPARQL support does not prove native MCP `ASK` support. Keep the four-form requirement open pending vendor confirmation or later authorized verification; do not silently substitute REST, a wrapper MCP server, or a rewritten query. [G2][S1]
- GraphDB 11 requires a separately obtained, installed license, including Free. Official licensing lists Talk to Your Graph in Free and Enterprise but does not explicitly enumerate native MCP entitlement. Exact edition entitlement for the approved deployment remains a confirmation gate. [G4]

## Existing Baseline

The following are checked-in metadata, not observations of a running installation:

| Area | Baseline | Constraint |
| --- | --- | --- |
| Python/backend | Python 3.12 requirement; FastAPI 0.116.1 | Retain the existing FastAPI application. |
| Client/database libraries | HTTPX 0.28.1, Uvicorn 0.35.0, Psycopg 3.2.9, RDFLib 7.1.4 | Do not change dependencies in this research task. |
| Services | PostgreSQL 17 Alpine; GraphDB 10.8.10 | No service startup, image pull, upgrade, or live query performed. |
| GraphDB identity | Repository `motorsport`; persistent `w3id.org/motorsport-hub` ontology/entity IRIs | Preserve exact existing identifiers, including their original schemes and suffixes. |
| Persistence | `graphdb-data` at `/opt/graphdb/home`; `postgres-data` at `/var/lib/postgresql/data` | Preserve actual existing Compose-project volume identities and contents. |
| GraphDB sizing | Checked-in JVM maximum heap is 1 GiB | Not evidence of adequate resources for an upgrade or concurrent assistant load. |

Local references: [backend/requirements.txt](../../backend/requirements.txt), [compose.yaml](../../compose.yaml). No environment or secret files were inspected. Credential values are deliberately omitted. Preserve the existing publication contract: graph reads associated with a schedule must use its `publicationVersion`, not the default/all-graphs union that can include staged or historical data.

## Agent Framework Version and APIs

### Package Evidence

| Package | Verified evidence | Consequence |
| --- | --- | --- |
| `agent-framework==1.18.0` | Published stable, not yanked; Python `>=3.10`, including 3.12 classifier; wheel uploaded 2026-09-10. Depends on `agent-framework-core[all]==1.18.0`. [M1] | Umbrella installation brings optional integrations; it is not the minimal dependency choice. |
| `agent-framework-core==1.18.0` | Release-tagged manifest: Python `>=3.10`; `pydantic>=2,<3`, `typing-extensions>=4.15,<5`, `msgspec>=0.20,<0.22`, `python-dotenv>=1,<2`, `opentelemetry-api>=1.39,<2`. Its `all` extra includes `mcp>=1.24,<2`. [M2] | Prefer core plus explicitly selected integrations when implementing. Core alone does not install the OpenAI provider or MCP dependency. |
| `agent-framework-openai==1.14.3` | Version in the framework `python-1.18.0` release tag and published package metadata; Python `>=3.10`; core `>=1.17,<2`; OpenAI SDK `>=2.25,<4`. [M3] | Provider package versions are not necessarily aligned with the core version. This provider is an example, not a selection. |
| `mcp==1.24.0` | Examined supported lower bound, not claimed latest. Python `>=3.10`; HTTPX `>=0.27.1`, Pydantic `>=2.11,<3`, Starlette `>=0.27`, Uvicorn `>=0.31.1` on applicable platforms; additional dependencies include AnyIO and SSE-Starlette. [M4] | Current HTTPX/Uvicorn pins meet these examined minima. Full transitive resolution remains necessary. |
| `fastapi==0.116.1` | Tagged manifest: Starlette `>=0.40,<0.48`; Pydantic `<3` with exclusions for early incompatible versions; Python 3.12 classifier. [M5] | Pydantic `>=2.11,<3` and Starlette `>=0.40,<0.48` overlap the examined requirements. |

This establishes **metadata-level plausibility only**. Newer dependencies permitted by open ranges, SSE-Starlette, the chosen provider, and platform-specific wheels can change the resolved result. No resolver, install, import, runtime, or tests were run. A stable release classifier is not a vendor support SLA. Recheck versions when implementation begins and record the resolved set then.

### Verified API Surface

The current core exports `Agent`, `AgentSession`, `InMemoryHistoryProvider`, `tool`, `FunctionTool`, `FunctionInvocationContext`, `FunctionMiddleware`, and `MCPStreamableHTTPTool`. Use `Agent(client=..., instructions=..., tools=...)`, `agent.create_session()`, and `await agent.run(..., session=session)`. These are the current documented contracts; old `ChatAgent(chat_client=...)` examples should not drive new implementation. [M6][M7][M8]

Function tools can use annotated Python parameters and structured input models. Keep database clients, authorization, fixed repository identity, and other trusted dependencies outside model-supplied arguments. Typed schemas improve validation but do not grant authorization or guarantee safe queries. The application owns those checks. [M8]

The existing FastAPI routes can host the framework directly. Dedicated agent hosting packages are not a prerequisite for this design; routing, authentication, lifecycle, and authorization remain application responsibilities. [M9]

### Provider Configuration Contract

The implementation must accept an explicitly configured provider kind, API family, model/deployment ID, endpoint/base URL, authentication mechanism/secret reference, and applicable API version. Also require finite timeouts, output/context limits, and tool-call budgets. The provider and endpoint are **unknown and user-supplied**; do not select a cloud, create resources, or infer a provider from ambient credentials.

For the verified OpenAI integration, `OpenAIChatClient` uses the Responses API; `OpenAIChatCompletionClient` uses Chat Completions. They are not interchangeable merely because a server is described as OpenAI-compatible. Azure routing uses the same clients with explicit Azure configuration; a full `/openai/v1` URL is a base URL, distinct from an Azure resource endpoint. Explicit configuration matters because ambient OpenAI settings can otherwise take precedence. Other providers require their own selected adapter and metadata check. [M3][M10]

Missing or invalid configuration must produce an honest unavailable/degraded state without making a model call. Validate actual tool calling, streaming if required, cancellation, and structured outputs later against the supplied endpoint. Application-ephemeral history does not imply that a remote model provider retains no requests: its retention/storage behavior requires explicit configuration and review.

### Per-Tab Ephemeral Sessions

`AgentSession` carries mutable state and can also hold a provider-side service session ID. Use application-owned in-memory history and no file/database serialization or provider conversation persistence for this requirement. Create an independent session for each browser tab and bind its opaque application ID to the authenticated user/browser owner. A shared login cookie alone does not isolate tabs. [M7]

- Keep tab identity out of shared `localStorage`; handle duplicated tabs so a copied identifier cannot silently join the same mutable session.
- Enforce owner checks on every request, bounded history, finite idle/absolute TTL, cleanup on expiry/logout, and explicit reset. Tab-close notifications are only best effort.
- Serialize simultaneous turns in one session, or otherwise enforce a defined concurrency contract. Never share mutable `AgentSession` state across tabs.
- In-memory state needs an explicit worker-routing strategy; arbitrary multi-worker routing cannot be assumed to find the session. Do not add persistent storage to hide this limitation.
- Keep provider conversation IDs and transport credentials backend-only. Disable prompt/tool-content logging and tracing unless separately approved with retention controls.

## GraphDB Native MCP

### Versions and Transport

| Version | Official evidence | Planning implication |
| --- | --- | --- |
| 10.8.10 | Current checked-in image predates native MCP. | No native MCP implementation can be demonstrated on this baseline. |
| 11.1.0 | Native MCP introduced; legacy SSE uses GET `/mcp/sse` and POST `/mcp/message`, on GraphDB's HTTP port. [G1][G2a] | Historical minimum, not a recommended deployment target. |
| 11.2.1 | Fixes GDB-13534, GraphDB dying after days of MCP use, introduced in 11.1; also fixes an HTTPS-forwarding MCP issue. [G5] | Do not choose the first release merely because it has MCP. |
| 11.3+ | Streamable HTTP available and default; `/mcp` accepts POST and GET on GraphDB's port. Legacy SSE remains configurable. [G2][G3] | Direct match for `MCPStreamableHTTPTool`; SSE response framing is not the same as the old SSE transport. |
| 11.5.0 | Current release documentation verified. [G6] | Candidate for user evaluation, not selected or installed here. |

GraphDB itself supplies the MCP server. The Python backend is a client with a policy boundary, **not a replacement MCP server wrapping SPARQL REST**. The separate `/rest/llm` OpenAPI/Dify interface and its YAML/TTYG configuration IDs are not native MCP endpoints. A legacy stdio-to-SSE gateway is unnecessary for the direct Streamable HTTP design. [G2]

### License, Authority, and Operation

GraphDB Free and Enterprise both list Talk to Your Graph; advanced authentication (including OpenID/OAuth and LDAP) and fine-grained access control are Enterprise features in the current comparison. Free is single-core, permits at most five repositories, and its descriptive text specifies two concurrent queries. All 11.x editions require a valid license; Free must be requested and manually installed, including the documented minor-version upgrade case. The page describes a free non-commercial option and refers to distribution license files for full terms. [G4]

**Unresolved entitlement:** native MCP has no explicit row in the verified edition comparison, and the native MCP page does not state an edition restriction. Neither “Enterprise-only” nor “guaranteed Free entitlement for this deployment” is established. The operator must confirm the target edition/license permits native MCP and the intended use. Do not purchase anything or assume a Free license is suitable for commercial use.

GraphDB must remain separately acquired, installed, licensed, and operated by the user/operator. Do not bundle GraphDB binaries, license files, or a repackaged vendor image with the assistant. This is a project constraint; the researched pages do not establish redistribution rights. Separate operation does not remove the need to comply with the applicable license.

For assistant queries, use a dedicated principal with **`ROLE_USER` and `READ_REPO_motorsport`**, with no write, maintainer, manager, admin, or wildcard repository rights. The documented native MCP security model enforces repository access; it also permits anonymous connections when free access grants READ. This project should require authenticated backend access instead of enabling anonymous access. No additional MCP-specific authority is documented in the reviewed pages. [G2][G7][G8]

Provisioning is separate: an administrator manages users/access; repository-manager authority includes repository creation/editing and all-repository read/write. TTYG agent creation requires repository-manager authority, but a TTYG agent is not documented as a prerequisite for direct native MCP queries. Do not give the runtime assistant elevated rights to simplify setup. `MAINTAIN_REPO_motorsport` also requires read/write rights and is not a read-only substitute. [G7][G9]

Repository read access alone does not restrict the assistant to the currently published named graph. Enforce publication/dataset scope in the backend; if database-enforced graph-level restrictions are needed, evaluate the separately licensed fine-grained access-control feature. Authentication must use the operator's configured mechanism, for example Basic over TLS or GDB token authentication, not an assumed Bearer scheme. [G4][G7][G8]

### Configuration Facts

These are documented properties/defaults, **not configuration changes**. [G10]

| Property | Documented default | Meaning |
| --- | --- | --- |
| `graphdb.mcp.transport.mode` | `streamable` | Native transport selection in current GraphDB. |
| `graphdb.mcp.server.max.sessions` | `100` | Concurrent MCP sessions; evicts the most idle when reached. |
| `graphdb.mcp.server.sessions.keepalive.interval` | `0` milliseconds | Keep-alive setting; leave unset when clients do not manage lifecycle so idle cleanup remains effective. |
| `graphdb.mcp.server.idle.sessions.timeout` | `30` minutes | MCP transport session cleanup, not browser chat TTL or query deadline. |
| `graphdb.license.file` | Custom path when supplied | Operator-managed license location. |

No `graphdb.mcp.enabled` switch was established. Configure the approved origin, TLS trust, proxy behavior and authentication; do not invent an enable flag. `graphdb.external-url` may be relevant behind a reverse proxy. GraphDB's own LLM settings are unnecessary when its LLM functionality is not being used; external raw MCP queries should not be conflated with GraphDB-hosted TTYG conversations. [G2][G10]

### Documented Tools and Gaps

The official native MCP list describes capabilities rather than a complete wire-level tool-name/schema contract. Obtain exact names and schemas with an authorized MCP `initialize`/`tools/list` later, and pin/review an allowlist. The snake-case names in the same page's Dify section are not proof of native MCP identifiers. [G2]

| Native capability | Prerequisite or restriction |
| --- | --- |
| Repository listing | Can expose repository metadata; exclude from model-visible tools unless necessary. Fixed repository selection belongs to the backend. |
| SPARQL query interface | Documents `SELECT`, `CONSTRUCT`, `DESCRIBE`; native `ASK` remains unverified. |
| Ontology schema extraction | Limit to the approved existing ontology/dataset; validate any query/template input. |
| Full-text search | Requires the repository's FTS index; returns RDF subgraphs. |
| IRI discovery | Label-based full-text matching; validate scope and bounds. |
| Autocomplete IRI discovery | Requires the autocomplete index. |
| Retrieval search | Depends on the selected retrieval configuration/connector; not required for the baseline assistant. |
| Similarity search | Requires a prepared similarity index/appropriate connector. |
| Similarity options discovery | Listed in current 11.5 documentation; do not assume present in every earlier native-MCP release. |

Index-dependent tools are not automatically usable because discovery advertises them. The repository's live indexes, selected edition, exact schemas, error behavior, cancellation, and result formats were not inspected. The `now` tool is listed for the separate Dify interface, not explicitly in the native MCP list; do not manufacture its native availability. [G2][G9]

### Framework Client Boundary

Current `MCPStreamableHTTPTool` supports `url`, `allowed_tools`, `tool_name_prefix`, `load_tools`, `load_prompts`, `request_timeout`, `http_client`, and `header_provider`; use its asynchronous lifecycle to initialize/discover and close connections. Prefer `load_prompts=False`, a reviewed finite allowlist, separate GraphDB/SQL tool namespaces, and disabled server-initiated sampling. An unrestricted `allowed_tools=None` exposes all discovered tools. Enforce the same allowlist at dispatch, including any direct `call_tool` path. [M11][M12]

Use a backend-only credential provider for transport headers scoped to the approved origin, including initialization/discovery. Capture credentials in trusted state, never `function_invocation_kwargs`: the inspected implementation can forward matching runtime kwargs to remote tool schemas, and generating headers does not consume/remove those kwargs. Do not copy stale `headers=` examples; use the release-matched API. Never send GraphDB credentials to a hosted model-side MCP connector. [M11][M12]

`max_host_payload_size_bytes` limits retained Host-channel data only; it does **not** bound the parsed result reaching the model or the network response. Framework function-invocation count/time budgets are best effort and checked after batches; they do not replace hard per-query deadlines, response-byte caps, or an overall cancellable request budget. [M8][M11]

## Required Read-Only Policy

The following are project implementation requirements, not guarantees provided by Agent Framework or native MCP:

1. Expose typed schedule listing/search and entity-IRI lookup tools over fixed, parameterized PostgreSQL queries. Bound dates, search lengths, pagination, and result sizes. Do not expose arbitrary SQL, database connection arguments, or write/review/publication operations. Use a dedicated non-owner read principal with narrowly granted data access, read-only transactions, finite `statement_timeout`, and controlled function execution. Read-only transaction mode alone is not a complete sandbox. [S2]
2. Parse the complete SPARQL request using a structured parser; accept exactly one supported query operation. Classify `SELECT`, `ASK`, `CONSTRUCT`, and `DESCRIBE`, then apply the native capability gate. Reject all UPDATE operations, malformed/trailing operations, `SERVICE` including nested or `SILENT` variants, and unsupported extension functions/magic predicates that may cause network access or side effects. Keyword matching alone is insufficient. [S1]
3. Resolve and validate prefixes/base IRIs, dataset clauses, graph selectors and tool arguments against trusted configuration. Fix the repository to `motorsport` and restrict queries to the applicable published snapshot plus approved ontology graphs. Reject arbitrary remote dataset IRIs, repository URLs, unrestricted graph variables, and staged/history graph access. Returned IRIs are data, not permission to dereference URLs. [S1]
4. Require finite result and execution budgets before dispatch. Bound `SELECT` rows and serialized bytes. Bound `CONSTRUCT`/`DESCRIBE` triples and serialized bytes separately: a solution `LIMIT` does not necessarily bound output triples, and `DESCRIBE` expansion is processor-defined. `ASK` returns a boolean but can still require expensive work. Reject a request when its effective bounds cannot be enforced. [S1]
5. Enforce input size/complexity, parallelism, per-tool calls, cumulative calls, deadlines and cancellation. Limit bytes before unbounded buffering/decoding and before model/browser delivery. Treat timeouts, truncation, malformed results and MCP errors as explicit failures or clearly marked partial results, never complete answers or boolean false.
6. Validate every invocation at the backend boundary, including model retries and schema/ontology extraction inputs. Treat tool descriptions, prompts and returned RDF/text as untrusted data, not instructions. Suppress secrets in exceptions, logs, telemetry, prompts, schemas and responses; prevent cross-origin credential forwarding and unrestricted GraphDB egress.

GraphDB repository parameters `query-timeout` (seconds) and `query-limit-results` (result count) both default to `0`, meaning unbounded; values less than or equal to zero disable their bounds. `throw-QueryEvaluationException-on-timeout` defaults to false, which can return partial results instead of an error. These defaults are not acceptable safety guarantees. The parameter table, not the page's inconsistent Workbench result-limit description, establishes the units. [G11]

An approved operator plan must establish effective positive server-side limits and timeout error behavior, and later verify their propagation through native MCP for each query form. Such repository-wide settings can affect existing workloads and require approval. Do not make the whole `motorsport` repository read-only, because legitimate publication still needs writes; isolate the assistant's credentials instead. `graphdb.ttyg.timeout` is an LLM-call timeout, not a SPARQL execution deadline. [G10][G11]

## Upgrade and Configuration Gates

No migration is authorized by this document. Before changing the current image or touching volumes:

1. Obtain explicit user approval for the target GraphDB version, edition, installation method and maintenance window. Confirm native MCP entitlement and the intended-use license terms without exposing license contents.
2. Have the operator confirm resources. GraphDB 11.5 documents Java 21, minimum 3 GB memory and 8 GB storage; these are baseline requirements, not a sizing guarantee. The existing 1 GiB heap is not total host memory, and neither available memory nor free storage was measured. [G12]
3. Approve a consistent backup/restore and rollback plan for GraphDB home, including `data`, `conf`, and `work`, and a coordinated PostgreSQL snapshot preserving publication references. Preserve the original volume untouched; rehearse against a separate restored copy. Record actual volume identities so a Compose project rename cannot silently select empty volumes.
4. Follow the version-specific migration guide. GraphDB 11 moves to Java 21/RDF4J 5.x and warns that automatic reversal to 10.x is not available. Rollback means restoring the pre-upgrade backup with the old software, not attaching old software to upgraded files. Review every intervening migration note; recreate old Lucene connectors if the documented 10.8/Lucene-8 case applies. Their presence here was not checked. [G3]
5. Later verify preservation of `motorsport`, original ontology/IRIs, namespaces, counts, named graphs, publication versions, and existing application reads/writes. Then verify MCP handshake, exact tool schemas, least-privilege access, query forms, limits and cancellation with a dedicated read principal. Do not run these checks in this research task.

### Inputs Still Needed

| Input or decision | Owner/gate |
| --- | --- |
| Model provider, API family, endpoint, model/deployment, authentication and budget | User supplies non-secret configuration; secrets are provisioned directly through an approved backend mechanism, never chat. |
| Provider request retention and data-sharing policy | User confirms what schedule/graph content may leave the backend and whether remote storage can be disabled. |
| Approved GraphDB target and separate installation | User/operator; current 10.8.10 is insufficient. |
| Valid target-version license and native MCP entitlement | Operator/vendor confirmation; no purchase or license request made here. |
| GraphDB origin/TLS/authentication and dedicated read principal | Operator; no ambient credential discovery. |
| PostgreSQL dedicated read access and allowed data surface | Operator; no role/grant changes here. |
| Exact native tool schemas, `ASK` support and bounded graph-result behavior | Later authorized integration evidence or vendor confirmation. Until then the affected capability remains unavailable. |
| Session TTL/history/call budgets and worker strategy | Application design within the ephemeral, per-tab requirement. |
| Upgrade backup, restore rehearsal and rollback approval | User/operator before any image, configuration or volume change. |

## Offline Versus Live Work

**Can be implemented offline later:** provider-neutral interfaces and unavailable states; FastAPI request/response contracts; isolated in-memory tab sessions; typed schedule/search/IRI tools with database doubles; parser-based read policy for all four requested query forms; tool allowlisting; bounded result normalization; publication-scope enforcement; credential-redaction boundaries. None requires selecting a paid service.

**Requires user configuration or an approved newer GraphDB:** actual model responses/tool calling; end-to-end database authorization; native MCP discovery and calls; edition entitlement; native `ASK`; index-backed search; enforceable server-side query/result limits; lifecycle/cancellation behavior; and migration validation. Offline simulations must not be reported as these acceptance results.

Research limitation: only documentation and public package/source metadata were examined, plus the allowed checked-in baseline metadata. No application runtime, tests, installs, paid resources, environment/secret inspection, service configuration changes, migrations, issue updates, commits, or delegation were performed.

## Primary Sources

All sources below were consulted on the research date. Release-tagged manifests/source take precedence over stale examples; versioned GraphDB docs can still receive later editorial corrections.

- [M1: Microsoft-published agent-framework package metadata](https://pypi.org/pypi/agent-framework/json).
- [M2: Core manifest at python-1.18.0](https://raw.githubusercontent.com/microsoft/agent-framework/python-1.18.0/python/packages/core/pyproject.toml).
- [M3: OpenAI provider manifest at python-1.18.0](https://raw.githubusercontent.com/microsoft/agent-framework/python-1.18.0/python/packages/openai/pyproject.toml) and [published 1.14.3 metadata](https://pypi.org/pypi/agent-framework-openai/1.14.3/json).
- [M4: Official MCP Python SDK v1.24.0 manifest](https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/v1.24.0/pyproject.toml).
- [M5: FastAPI 0.116.1 manifest](https://raw.githubusercontent.com/fastapi/fastapi/0.116.1/pyproject.toml).
- [M6: Core public exports at python-1.18.0](https://raw.githubusercontent.com/microsoft/agent-framework/python-1.18.0/python/packages/core/agent_framework/__init__.py).
- [M7: Microsoft Learn, Agent sessions](https://learn.microsoft.com/agent-framework/concepts/agents/conversations/session).
- [M8: Microsoft Learn, Function tools](https://learn.microsoft.com/agent-framework/agents/tools/function-tools).
- [M9: Microsoft Learn, Self-hosting](https://learn.microsoft.com/agent-framework/hosting/self-hosting/).
- [M10: Microsoft Learn, OpenAI providers](https://learn.microsoft.com/agent-framework/integrations/by-component/model-providers/openai?pivots=programming-language-python).
- [M11: Microsoft Learn, Local MCP tools](https://learn.microsoft.com/agent-framework/agents/tools/local-mcp-tools).
- [M12: MCP implementation at python-1.18.0](https://raw.githubusercontent.com/microsoft/agent-framework/python-1.18.0/python/packages/core/agent_framework/_mcp.py).
- [G1: GraphDB 11.1 release notes](https://graphdb.ontotext.com/documentation/11.1/release-notes.html).
- [G2: GraphDB 11.5 external clients/native MCP](https://graphdb.ontotext.com/documentation/11.5/using-graphdb-llm-tools-with-external-clients.html).
- [G2a: GraphDB 11.1 external clients/native MCP](https://graphdb.ontotext.com/documentation/11.1/using-graphdb-llm-tools-with-external-clients.html).
- [G3: GraphDB migration guide](https://graphdb.ontotext.com/documentation/11.5/migrating-graphdb-configurations.html).
- [G4: GraphDB 11.5 licensing](https://graphdb.ontotext.com/documentation/11.5/licensing.html) and [official product/download/license page](https://graphwise.ai/components/graphdb/).
- [G5: GraphDB 11.2 release notes, including 11.2.1 fixes](https://graphdb.ontotext.com/documentation/11.2/release-notes.html).
- [G6: GraphDB 11.5 release notes](https://graphdb.ontotext.com/documentation/11.5/release-notes.html).
- [G7: GraphDB user roles and permissions](https://graphdb.ontotext.com/documentation/11.5/user-roles-and-permissions.html).
- [G8: GraphDB access control](https://graphdb.ontotext.com/documentation/11.5/access-control.html).
- [G9: GraphDB Talk to Your Graph](https://graphdb.ontotext.com/documentation/11.5/talk-to-graph.html).
- [G10: GraphDB directories and configuration properties](https://graphdb.ontotext.com/documentation/11.5/directories-and-config-properties.html).
- [G11: GraphDB repository configuration](https://graphdb.ontotext.com/documentation/11.5/configuring-a-repository.html).
- [G12: GraphDB requirements](https://graphdb.ontotext.com/documentation/11.5/requirements.html).
- [S1: W3C SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/), especially query forms, grammar, solution modifiers, and security considerations.
- [S2: PostgreSQL 17 client connection defaults](https://www.postgresql.org/docs/17/runtime-config-client.html), especially read-only transactions and statement timeouts.