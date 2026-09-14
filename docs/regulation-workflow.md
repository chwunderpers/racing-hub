# Private Regulation Workflow

Issues #11 and #12 provide a local operator path for Formula One and NLS 2026
race-points evidence. Select **Racing Regulations** or invoke `/racing-regulations`. The website
assistant has read-only access to completed Publications, never this workflow.

## Prepare Evidence

Use `backend/fixtures/f1-2026-regulations.json` as the pending native-English
candidate, with the findings and limitations in
[the source inventory](f1-regulations-source-inventory.md). It contains factual
paraphrases, not a redistribution of the PDFs. Document versions, section/page
anchors, checksum and retrieval metadata are retained. Unknown effective dates
stay null: an issue's publication date does not establish historical applicability.

The [NLS inventory](../backend/fixtures/nls-2026-regulations.json) contains two
verified VLN documents and 14 English passages with pending Translation Records.
Use the [NLS research](nls-regulations-source-inventory.md) to review exact anchors,
table values, the conflicting approval dates and incomplete amendment coverage.
Its scoring value is conditional; six other topics are unknown. The class-based
A-F championship allocation is distinct from the Speed Trophy H overall award.
The checked-in fixture remains pending. Chris approved the private copy's 14
translations on 2026-09-14; the separately accepted candidate was published as
`5106927820d7b8d6a710009b5ff15b532df54314dd1ad391b0577a1638a72ae3`.
That approval does not change unknown dates or resolve the documented conflicts.

For a new source, inventory the official HTTPS FIA, VLN or DMSB PDF and review its identity,
season, authority, version, section anchors and permissible evidence reuse before
acceptance. The command verifies bytes and bounded PDF responses, not the truth of
a paraphrase or a reuse licence. It rejects redirects, content compression,
checksum drift and documents over 10 MB. It never retains downloaded PDF bodies.
F1 documents require FIA authority; NLS admits VLN or DMSB on their approved
official hosts, including the organizer-linked `teilnehmer.vln.de` portal.
Keep organizer authorship separate from DMSB approval. Unknown `issued_on` dates
remain null; version, approval and retrieval dates do not fill that gap.

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

For NLS, select `backend/fixtures/nls-2026-regulations.json` instead. This only
previews pending translations; it does not accept them.

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
   [ontology review](ontology-maintenance.md). Issue #11's regulation vocabulary
   was approved and published on 2026-09-10. Issue #12 reuses those terms;
   additional vocabulary still needs its own review before live publication.
   Passing isolated-store tests is not vocabulary approval.
4. Request a separate publication proposal and explicit confirmation before
   `publish`. It checks the accepted candidate, regulation confirmation tokens,
   translation review, identities and publication baseline. SQL/search and RDF
   must agree before current-version promotion. Failure retains the previous
   current Publication; corrections preserve earlier private envelopes by version.

## Assistant Contract

Explicit comparison freshness describes the regulation evidence retrieved for
that answer, not schedule-ingestion attempts for unrelated Competitions. F1 and
NLS regulation verification each currently have an explicit 24-hour policy,
independent of schedule policies. Each side uses its oldest document retrieval
timestamp; missing evidence remains unverified. These timestamps originate from
the checksum-verified ingestion, not publication time. Publication does not reset
them, establish historical applicability, or prove complete amendment coverage.
Ordinary Chat retains its existing aggregate schedule-source freshness behavior.

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

`compare_regulations` reads both `formula-one` and `nls` for one requested season
and topic from the same completed Publication. Optional `on_date` reports each
Provision as not assessed, unresolved, outside its period or within its stated
bounds. These labels do not prove full historical applicability. Connected
amendments remain visible even when not directly linked from the profile value;
unresolved applicable amendments prevent a normalized applicable-value conclusion.
Out-of-period related amendments remain disclosed without blocking a currently
governing Provision. Current-publication native graph queries also admit the
public regulation predicates, while retaining existing bounds and private-field
exclusion.

Without an event date, compare only the cited versions conditionally. Retain each
Competition's own citations, exceptions and conflicting authoritative assertions;
do not select an authoritative winner or infer an event award. Missing profiles,
unknown topics and unsupported dates cause explicit scoped refusals. The service
also rejects one-sided or invented citations and marks supported comparisons as
derived. Citation membership is enforced; semantic accuracy and completeness of
the model's prose still require evaluation, not just valid citation IDs.
For controlled comparisons, select **Compare rules** in the Ask panel and choose
season, topic and optional date. The messages API accepts the typed `comparison`
field. The server retrieves both profiles before model invocation and returns a
scoped refusal directly when evidence is unavailable or unresolved. Supported
requests send only the server-selected evidence to the model, with no alternate
tools or chat history. Governing citations from both profiles are mandatory.

Chat remains free-form: model tool selection is still a trust boundary there.
The service does not recognize every comparison phrasing or prove arbitrary prose
correct after unrelated tool calls. The explicit mode establishes request scope
and evidence availability, not an automatic interpretation of every assertion.