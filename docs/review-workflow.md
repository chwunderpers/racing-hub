# Private schedule review

Select **Motorsport Review** in the VS Code Chat agent picker and give it a
structured candidate JSON file or a pending Review Item ID. This is a local
operator workflow, not a new web interface. The agent reads the file, presents
the deterministic preview, conducts the decision conversation and invokes the
private command. Arbitrary document acquisition/normalization is a later slice.

## Prerequisites

Use the existing Python 3.12 virtual environment with
`backend/requirements-dev.txt` installed. Start the local Compose stores first.
In the operator terminal, set `PYTHONPATH=backend`, `DATABASE_URL` and
`GRAPHDB_URL`; optionally set `GRAPHDB_REPOSITORY` (default `motorsport`).
Connection values must be configured locally, never pasted into chat. Commands
do not create repositories, install dependencies, or run deployment.

From the repository root, the command prefix on Windows is:

```powershell
.venv\Scripts\python -m app.review_cli
```

The default artifact root is this repository's `reviews/`. For isolated tests
or a separate operator worktree, `--reviews-dir PATH` precedes the subcommand.
Use one artifact root per operational database to preserve a single audit trail.

## Candidate and decisions

The candidate schema is demonstrated by `backend/fixtures/f1-2026-australia.json`.
Meeting `status` can be `scheduled` (default) or `cancelled`. Dates must be ordered,
identities and evidence nonempty, source URLs HTTP(S), retrieval timestamps
timezone-aware, and `source_language` must be `en`. Unknown fields are rejected.
The language flag is a declaration, not a language detector: the human must check
that labels, evidence and retained rationale are English.

```powershell
.venv\Scripts\python -m app.review_cli preview PATH_TO_CANDIDATE.json
.venv\Scripts\python -m app.review_cli show ITEM_ID
.venv\Scripts\python -m app.review_cli propose ITEM_ID reviews/requests/decision.json
```

A decision request is JSON, with these fields:

```json
{
  "outcome": "accepted",
  "person": "Operator name confirmed by the human",
  "rationale": "English rationale confirmed by the human",
  "evidence": ["https://www.formula1.com/en/racing/2026/australia"]
}
```

Outcomes: `accepted`, `rejected`, `corrected`, `deferred`. For `corrected`, add
`corrected_candidate` containing the entire corrected candidate envelope. A
correction records what the human changed, refreshes the preview, and requires
a separate acceptance. To approve a changed identity explicitly, add
`identity_resolutions`, mapping the flagged field (for example `circuit_identity`)
to its exact proposed identity. The rationale and evidence must justify it.
Do not derive identity from a matching display name.

`propose` persists the exact proposed decision and returns its confirmation digest.
The digest binds
content; it is not authentication and is not evidence of a human response by itself.

```powershell
.venv\Scripts\python -m app.review_cli decide ITEM_ID --confirmation DECISION_DIGEST
.venv\Scripts\python -m app.review_cli publication ITEM_ID
```

`decide` records the decision; `publication` only prepares and validates the
publication proposal. Apply the conversation gates below before either confirmation:

```powershell
.venv\Scripts\python -m app.review_cli publish ITEM_ID --confirmation PUBLICATION_DIGEST
```

## Conversation

1. Given a candidate file, run `preview`; given an Item ID, run `show`. Present the
  additions, changes (including provenance), cancellations, conflicts, unresolved
  identities and validation errors. State the baseline version and Item ID.
2. Ask the human for acceptance, rejection, correction or deferral, their identity,
  rationale and evidence references. Do not invent any of these. Translate the
  rationale into English when necessary and present it for confirmation. Check
  that candidate labels and retained evidence are English.
3. Create the structured decision request and run `propose`. Show the exact returned
  decision, including the complete candidate, any corrected candidate, identity
  resolutions, person, evidence, rationale, baseline and confirmation digest.
  Ask the human to confirm this exact proposal. **End the turn here.**
4. Only after a new explicit human confirmation, run `decide` with the displayed
  digest. Report the recorded decision ID. A correction is not acceptance of the
  corrected candidate: refresh its preview and return to the decision steps.
5. For an accepted decision, run `publication`. Display its exact candidate,
  decision ID, baseline, version and confirmation digest. Ask separately whether
  to publish this specific version now. **End the turn here**, even if the earlier
  acceptance was explicit.
6. Only after a new explicit publication approval, run `publish` with that proposal's
  digest. Report the decision ID, published version and receipt path on success.
  On failure, report the pending item without claiming success. Inspect current
  status before retrying a promotion whose receipt write failed. A changed
  candidate or stale baseline requires a fresh preview and human decision,
  never automatic reapproval.

Stop after one item. Do not continue with the next item without the human asking.

## Persistence and failure

- `reviews/queue.yaml`: pending items with stable UUIDs, preview, evidence-bearing
  candidate, baseline, timestamps and decision references. Accepted items remain
  open until publication succeeds. Rejection removes the item after recording it.
- `reviews/decisions/ID.yaml`: immutable decision records containing the person,
  timestamp, rationale, evidence, exact candidate and correction/resolution details.
- `reviews/publications/DECISION_ID.yaml`: completion receipt and publication version.
- `reviews/requests/`: operator/agent-authored requests, not authoritative decisions.

Commands use an OS-backed lock and atomic file replacement. Concurrent local
writers fail fast; process exit releases the lock. Publication writers also use
a PostgreSQL advisory lock and compare the reviewed baseline before staging.
Schema, unresolved-identity, conflict or projection failures leave the item open
and the previous Publication visible. Accepted staging may remain for retry.
After promotion, a receipt-write interruption can be retried using the same digest
without republishing. Audit files belong in operator-controlled version control;
they are not signed, and a local user with filesystem/database access is trusted.

The current publication model still contains one Meeting. Preview lists additions
but blocks replacing a different Meeting because that would silently discard the
existing schedule. Creating the first Meeting, revising it, explicitly resolving
its changed identities and marking it cancelled are supported. Multi-Meeting
snapshot merging and a formal ontology/SHACL validation layer are later slices.
Projection checks operate on the versioned graph, never the union of histories.