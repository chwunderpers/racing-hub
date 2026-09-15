# Local PoC Acceptance

Issue #16 validates the complete local stack without changing an existing
publication. The acceptance command archives the current Git commit into a
temporary clean checkout. Untracked files, live `.env`, private reviews and
existing Docker volumes are not copied.

## Prerequisites

- Python 3.12 with `backend/requirements-dev.txt` installed in a virtualenv.
- Node.js 24 and Docker Compose v2 with enough memory for a second local stack.
- An existing valid GraphDB 11.5 license outside the repository, supplied via
  `GRAPHDB_LICENSE_FILE`. This is an operator/vendor prerequisite, not generated
  by the application. GraphDB is a separate licensed service, never embedded.
- Microsoft Edge for the default Playwright browser channel. On other hosts,
  install a supported browser and set `PLAYWRIGHT_CHANNEL` accordingly.
- Optional approved Azure Responses deployment settings for live assistant
  requests. Keys must be entered directly in the shell or ignored `.env`, not
  supplied through chat. Offline SDK/security tests do not call the provider.

From a clean checkout, create a Python 3.12 virtual environment, install
`backend/requirements-dev.txt`, and run from the repository root:

```powershell
$env:PYTHONPATH = 'backend'
.venv/Scripts/python.exe -m app.acceptance --output acceptance-results/run-001
```

The output directory must not exist. Commit intended changes before running:
the recorded revision, not the dirty working tree, is tested. The command uses
the invoking virtualenv for backend tests and installs locked frontend
dependencies inside the temporary checkout. It builds both application images
from clean sources.

## What Runs

The separate acceptance Compose definition starts uniquely named PostgreSQL
and GraphDB instances with random loopback ports and private volumes. It seeds
captured F1/GT/NLS schedule fixtures and synthetic regulation/vehicle evidence
into the empty rehearsal store. This is test-fixture publication, not approval
of source evidence for the live service. It configures fresh GraphDB accounts
and query limits plus a restricted PostgreSQL assistant reader. No credentials
from the live stores are reused or rotated.

The command runs the full backend suite, rejects skipped tests, runs component
tests and a production/typecheck build, audits frontend dependencies, and runs
real desktop/mobile Playwright and axe accessibility checks. Every phase is
recorded. The browser checks use the newly built disposable app, not a mock API.

The browser suite covers filters, date constraints, detail navigation, UTC and
event time, source links/retrieval, assistant/comparison layout, GT prologues,
NLS cancellation and all export downloads. Existing focused suites cover F1,
GT and NLS source precision/identity/coverage, ontology validation, regulations,
vehicles, optional capabilities, search, native MCP and assistant behavior.

Recovery tests use disposable databases/repositories and exercise private
backup/restore, overwrite refusal, corrupt archives, retained source failure
state, a missing restored graph remaining unpublished, and reconciliation of a
deleted accepted graph. Existing tests cover
retrieval and projection failure with the previous publication retained.
Security suites exercise least-privilege access, bounded queries/tools,
SSRF restrictions, prompt-injection requests, citation enforcement and private
data exclusion. The HTTP/SDK regression supplies malicious retrieved source
text, simulates an attempted SQL/oversized tool request, and checks refusal of
fabricated citations without exposing provider credentials. Its provider
transport is deterministic, not a live-model adversarial evaluation.
Test output is not proof of model immunity to arbitrary
prompt injection; the assistant remains bounded by its server-side tools.

## Reports And Cleanup

`report.json` records the tested commit, phase outcomes, backend count and final
status. Screenshots are retained under `browser/`. Failure output is captured
privately and known credential values are redacted before writing. Reports may
still contain fixture source text or generated answers: do not publish them
without inspection. No environment dump or expanded Compose configuration is
printed. Reports and backups are gitignored.

The runner removes only its own uniquely named containers and volumes in a
finally block. If cleanup fails, the report names the remaining project.
Never run `docker compose down --volumes` against the live stack as a cleanup
shortcut. Interrupted process cleanup must target only the recorded rehearsal
project. A failed run is not acceptance; fix the failing gate and rerun.

## Private Backup And Recovery

Configure `DATABASE_URL`, `GRAPHDB_URL`, `GRAPHDB_REPOSITORY`, GraphDB maintenance
credentials and `POSTGRES_CONTAINER` in the process environment. The database
connection must address localhost/127.0.0.1; the explicitly named container
must own that database and provide PostgreSQL 17 `pg_dump`/`pg_restore` tools.
Passwords are passed through environment variables, not command arguments.

```powershell
.venv/Scripts/python.exe -m app.recovery backup backups/private-snapshot.zip
.venv/Scripts/python.exe -m app.recovery restore backups/private-snapshot.zip
.venv/Scripts/python.exe -m app.recovery reconcile
```

Create the private backup directory first. Backups contain the full PostgreSQL
database, including private source notes, and asserted publication named graphs
with checksums. They are not public exports and are not encrypted by this tool;
use an access-restricted, encrypted disk and an operator-controlled retention
policy. Never commit or upload them. Only restore trusted archives produced by
the operator: PostgreSQL dumps contain executable database definitions.

Backup runs under the publication advisory lock. PostgreSQL supplies its
consistent dump snapshot; asserted historical graphs are preserved as stored,
not regenerated using potentially newer mapping code. Checksums detect
accidental corruption, not malicious replacement. The local PoC size limit is
256 MiB. Credentials/role passwords, GraphDB security configuration/license,
external review files and container configuration are not backed up. Preserve
operator audit files separately in private storage; rebuild access roles with
the documented setup commands after restoring.

Restore requires an existing empty PostgreSQL database and an unused GraphDB
repository ID. It restores SQL without owners/ACLs, hides the publication pointer
while restoring asserted graphs, verifies current graph agreement, and only then
exposes the restored version. Do not start the app on a restore target until the
command succeeds. On failure discard only the disposable target and retry.
Restore does not replace a populated live installation.

`reconcile` replays the currently accepted envelope into its exact graph and
refreshes search under the publication lock; it never accepts new evidence or
changes the version. It requires the repository to exist. Reconciliation is a
maintenance write: stop concurrent external GraphDB edits and check the result
before considering recovery complete.

## Verification Record

Review baseline: `9a78b72b546e32f6e7133735919449c11c7f919b`.

On 2026-09-14, clean-checkout run `issue-16-run-002` passed at revision
`4d1cc1ea200fce620be3560ae2bdc3012cb1811f`:

- 301 backend tests, zero skips, including real disposable PostgreSQL/GraphDB.
- 27 frontend component tests and the production/typecheck build.
- Frontend dependency audit: zero vulnerabilities.
- Four Playwright tests across desktop (1440x1000) and mobile (390x844), with
  zero axe WCAG A/AA violations, no horizontal overflow, and actual downloads.
- Fresh security setup and cleanup of all rehearsal containers/volumes passed.

The private report is `acceptance-results/issue-16-run-002/report.json`.
Saved desktop/mobile screenshots were visually inspected without overlap.
Run 001 failed because restarting GraphDB changed its dynamic host port; the
runner now resolves the port again. Its disposable resources were also removed.

Post-review additions were verified separately: three recovery tests (including
missing-current-graph refusal), 12 assistant tests (including malicious source
text), and all four browser tests with the explicit stale-state assertion
passed. These additions are not included in the 301-test run's recorded commit.
Pyright reported zero errors/warnings for the new modules and touched Python
tests; editor diagnostics were clear. No application runtime code changed after
the successful clean-checkout run.

## Standards

The initial parallel review found zero hard violations and two low-priority
heuristics: repeated dotenv loading and environment/port configuration grouped
as primitive values. These remain in the single operator workflow; no new
abstraction was needed for correctness. A focused follow-up review found no
violations in the added recovery, assistant and browser tests.

## Spec

The initial review's actionable gaps, explicit browser stale-state coverage and
failed restoration staying unpublished, were closed and tested. An additional
malicious-source regression makes the injection boundary explicit. Suggestions
about the audit gate and invoking virtualenv were checked against the command
and documented prerequisites; neither was a missing requirement. Checking the
entire freshness notice's wording was not required for the browser stale-state
assertion. No confirmed defects remain from the focused follow-up review.

Both axes used supplied scoped files, not an independent Git diff. Summary:
Standards zero hard findings/two retained low heuristics; Spec zero remaining
confirmed findings. This is local PoC acceptance, not a production security
certification or a new approval/publication of live source evidence. Existing
source staleness remains visible; no refresh was fabricated. Issue #16 remains
open pending the separately authorized delivery step; no push or merge is part
of this implementation.