# Private Formula One Regulation Workflow

Issue #11 adds a local operator path for the approved Formula One 2026 race-points
slice. Select **Racing Regulations** or invoke `/racing-regulations`. The website
assistant has read-only access to completed Publications, never this workflow.

## Prepare Evidence

Use `backend/fixtures/f1-2026-regulations.json` as the pending native-English
candidate, with the findings and limitations in
[the source inventory](f1-regulations-source-inventory.md). It contains factual
paraphrases, not a redistribution of the PDFs. Document versions, section/page
anchors, checksum and retrieval metadata are retained. Unknown effective dates
stay null: an issue's publication date does not establish historical applicability.

For a new source, inventory the official HTTPS FIA PDF and review its identity,
season, authority, version, section anchors and permissible evidence reuse before
acceptance. The command verifies bytes and bounded PDF responses, not the truth of
a paraphrase or a reuse licence. It rejects redirects, content compression,
checksum drift and documents over 10 MB. It never retains downloaded PDF bodies.

Translate non-English text before writing an inventory or Review Item. Retain
only English evidence plus source-language metadata, source URL, checksum and
anchor. Each Translation Record needs method, version, translation time and review
state. Accepted translations additionally require the actual reviewer, review time
and explicit authorization. Synthetic translation fixtures exercise this contract;
there is no configured translation service. An English language flag cannot prove
that text is English. The human review must inspect its wording.

## Private Preview

From the repository root, use the existing virtual environment and
[locally configured connections](review-workflow.md#prerequisites). Keep
connection values outside chat:

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m app.regulation_ingestion backend/fixtures/f1-2026-regulations.json
```

This requires an existing season-scoped Publication. It merges only the selected
regulation profile into that snapshot, preserving all schedule seasons and other
profiles. A concurrent schedule publication invalidates the preview. The command
prints the private Review Item ID, baseline and diff, and performs no acceptance
or publication. The local `reviews/` queue and decisions stay outside retrieval;
keep operational review artifacts out of implementation commits.

## Human Gates

1. Inspect every document identity, English passage, Provision and normalized
   value. Known values require same-topic Provisions and English evidence.
   `unknown`, `not-published` and `not-applicable` are distinct; the latter two
   require evidence, not an inference from missing data. Applicability, exceptions,
   amendments and discretion must remain visible. Empty amendment lists mean no
   encoded relationship, not proof that no amendment exists.
2. Hand the item to **Racing Review** using the existing `app.review_cli` workflow.
   Include the preview's exact `regulationConfirmations` values as
   `regulation_confirmations` in the decision request, along with the actual
   person, rationale, evidence and any `identity_resolutions`. For corrections,
   submit a corrected candidate, then review and accept its new preview. Display
   the decision proposal and obtain explicit human confirmation before `decide`.
3. New regulation vocabulary also requires the separate
   [ontology review](ontology-maintenance.md). Issue #11's new RDF terms have not
   yet been approved in the baseline ontology. Complete that review before live
   publication; do not treat passing isolated-store tests as vocabulary approval.
4. Request a separate publication proposal and explicit confirmation before
   `publish`. It checks the accepted candidate, regulation confirmation tokens,
   translation review, identities and publication baseline. SQL/search and RDF
   must agree before current-version promotion. Failure retains the previous
   current Publication; corrections preserve earlier private envelopes by version.

## Assistant Contract

`competition_regulations` reads a completed season-scoped Competition Profile
through the restricted document view. It returns governing Provisions, English
evidence kind, official page URL, document version/checksum, applicability,
exceptions, amendments and discretion. Citation IDs are created by the tool, not
the model. Private reviewers and authorization text are excluded.

The initial supported question is conditional: how many points does a sole
full-points Formula One 2026 race winner receive? The candidate says 25, with the
distance and consecutive-lap conditions, dead-heat exception and classification
caveats. It does not establish any real race award, earlier issue applicability,
sprint rule, other Competition rule or complete regulation coverage. Missing
reviewed evidence produces an explicit refusal. Existing call, byte and iteration
budgets and Responses `store=False` still apply.