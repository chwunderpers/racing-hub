# Issue 11 Verification

Implementation checkpoint: `e0f03d795a075de765a62299a2d49587d21136b4` on
`feature/11-f1-regulations`. Review baseline:
`cb0b40973a55e524cbdaed60a473a17202871825`. The original checkpoint below
predates approval and publication; the completed closeout is recorded first.

## Approved Publication And Closeout

On 2026-09-10 Chris accepted the evidence with rationale **All fine**, decision
`ba7c325d-1a9e-44af-883b-18816c0f1788`. The additive vocabulary was separately
approved with the same rationale in
[Issue 11's ontology approval record](https://github.com/chwunderpers/racing-hub/issues/11#issuecomment-5623837574).
Chris subsequently confirmed the exact publication version and digest.

- Published at **2026-09-10T18:58:09.679064+00:00**; immutable receipt:
  [publication receipt](../reviews/publications/ba7c325d-1a9e-44af-883b-18816c0f1788.yaml).
- Current version:
  `7eda872e9f7397f4b398a9203b576a2d47e651d1078ff21fa83843a2fb180105`.
- The version recomputes from the accepted candidate. GraphDB's asserted
  projection is RDF-isomorphic to the expected graph. The API is healthy and
  serves the same version for **50 Meetings and 146 Sessions**.
- The published Formula One 2026 profile has **two official documents, four
  English paraphrases and four Provisions**. Synthetic translation and amendment
  examples were not published. The completed Review Item left the queue.
- An initial retry was required because the host CLI had not loaded GraphDB
  maintenance credentials. The previous publication remained complete and the
  candidate was only staged. Loading the local environment file and retrying
  the same confirmed digest completed publication. No new approval was inferred.
- Post-publication verification exposed a stale backend image. Rebuilding and
  restarting only the backend restored its regulation-aware schema; all live
  agreement and API checks then passed.

The private `issue-11-f1-regulations-proposal-001/rehearsal-002` bundle conforms
to vocabulary and instance SHACL and passes all five competency checks: class,
inverse, shared-circuit, distinct-circuit-identities and graph-separation.
The approved delta is **99 added, zero removed vocabulary triples**, with no
renames or changed example triples; **211 asserted and 615 inferred triples**
remain separate. Private proposal inputs and existing reports were preserved.
The canonical vocabulary now matches the approved candidate by RDF isomorphism.
The historical baseline is retained in Git at the closeout review baseline,
`8a9bcf37fbfccf4bee3f6c4386393bb7bbeb1303`.

Approved input SHA-256 hashes:

```text
baseline  3745f15248c08b5655909bedcf4b622ac2aaa841a46d2d8af7d4785b52ac577d
ontology  758310f5747aa043ccfcceb6ac76e92c2a17080ad2f7afc2363aaa65944e801b
data      3c5ad4239ebf0c7d20548c91e02f0fd4853ba4ffb4206daa50191bd51b8431b8
proposal  b247589e5302db465d432e0cb4b0ae1cd37cc5a2c4efb451f484e8d5ab7608f0
```

Closeout checks after canonical vocabulary promotion:

- Ontology, review, review CLI and regulation tests: **80 passed, 3 skipped**.
  The three service-dependent regulation checks were then rerun against
  disposable PostgreSQL databases and GraphDB repositories: **3 passed**.
  All 83 selected tests therefore ran successfully across the two invocations.
- Eight new CLI cases accept neutral machine strings, reject English and French
  language tags on machine fields, and preserve English-only prose validation.
  Queue-only CLI tests cover missing settings, missing items, contention and
  unchanged queue bytes. Other commands report missing setting names only.
- Live Azure assistant evaluation returned **HTTP 200** for the sole full-points
  Formula One 2026 race-winner question. It answered **25 points**, qualified by
  **75% distance**, the required consecutive laps without SC/VSC, final
  classification and dead-heat rules. All four reviewed Provisions were cited
  with canonical IRIs and FIA PDF page links. The answer used the exact current
  publication version and did not infer historical applicability or an event
  award. The temporary assistant session was deleted after the check.

Scope remains the approved single-Competition conditional scoring topic. Live
FIA evidence was originally English; translation behavior is verified with
explicitly synthetic fixtures, not represented as a real FIA translation.
Shared Circuit does not prove shared Layout. Comparison with NLS, curated
documentation, exports and whole-PoC acceptance belong to other open tickets.

## Executed Checks

- Full backend suite: **204 passed**, 703 warnings, 457.52 seconds.
  Executed once at the end against disposable PostgreSQL databases and GraphDB
  repositories, using the project's Python 3.12 virtual environment. Test
  connections used loopback IPv4. Live stores were not used as test fixtures.
- Frontend: **14 passed** across two files; production `tsc -b && vite build`
  succeeded. No frontend source or public HTTP contract changed.
- Focused regulation and assistant checks: 26 passed before the last state and
  baseline additions. Those additions are included in the full suite above.
  Review and review CLI regressions: 27 passed.
- New regulation model, projection and ingestion modules: Pyright reported zero
  errors. A broader check of changed application modules reported 29 errors in
  shared modules. An isolated archive of `cb0b409` reported the same 29-error
  count for those six shared modules. This is not a claim that the whole backend
  typechecks cleanly; no unrelated type cleanup was included.
- New agent/skill YAML frontmatter parsed successfully. Editor diagnostics for
  the inspected regulation modules, tests and workflow files were clear.

Coverage includes hash and response failures, schedule preservation, stale
ingestion preview rejection before queue persistence, English pre-persistence
gates, complete translation provenance, pending translation rejection, explicit
regulation confirmation, invalid references and amendment cycles, distinct
knowledge states, real RDF/search agreement, restricted current-version reads,
translation correction history and failed-publication preservation.

The assistant test uses the actual Agent Framework and OpenAI Responses client
with synthetic HTTP responses to exercise the typed tool boundary, citations,
unknown-topic refusal and private-review exclusion. It is not a live Azure model
evaluation of rule interpretation. That evaluation remains pending publication
approval and accepted evidence.

## Two-Axis Review

Two read-only agents reviewed `git diff cb0b409...HEAD` at the implementation
checkpoint in parallel.

### Standards

No confirmed documented-standard violations. Four judgment-call advisories were
raised for `profile_projection`: evidence-field grouping (Data Clumps), graph
access ownership (Feature Envy), sorted traversal repetition (Duplicated Code),
and provision-to-passage-to-document traversal (Message Chains). These remain
advisories: the traversal is already localized in a single projection module,
and introducing additional classes/helpers was not justified for this slice.

The reviewer also questioned first-publication confirmation, translation checks
on envelope types, and graph ordering. The first-publication rejection test
passes; only `PublicationSnapshot` can carry regulations; RDF agreement compares
graph content rather than insertion order. These were not confirmed defects.

### Spec

No confirmed implementation defects were reported against the six Issue #11
criteria and the approved narrow topic. The reviewer identified the intentionally
pending vocabulary integration. This is a workflow approval gate, not an added
code-level authentication mechanism. Passing tests does not satisfy it.

Review totals: **Standards: 0 confirmed violations, 4 advisories**;
**Spec: 0 confirmed defects, vocabulary integration pending**.

## Live Review Checkpoint

Official FIA document downloads matched both inventoried SHA-256 values.
Private Review Item: `bdd3bfac-7b7d-42f9-8fb5-b61329213860`.

- Baseline and still-current Publication:
  `df5eb36a8bff2a30bfd9d258f0599357c9bd84abab95d5c50163ea7aaa6d0af5`.
- Proposed change: only `regulations/formula-one:2026`.
- Preview: no validation errors, conflicts or unresolved identities.
- Regulation confirmation token:
  `regulations/formula-one:2026/9d14b4a36d698d86983ecf08086b7f4d8bd89fe6a0f777d46c4a97a07298fc9d`.
- Live post-test check: **50 Meetings, 146 Sessions, zero regulation profiles**.

The pending candidate has two official English documents, four factual
paraphrases and four linked Provisions. It supports only the conditional 25-point
sole full-points race-winner rule, with distance/lap, dead-heat and classification
caveats. Historical applicability and actual race awards remain unestablished.
See [the source inventory](f1-regulations-source-inventory.md) and
[the workflow](regulation-workflow.md).

Remaining human steps: review the exact evidence, identities and permissible
reuse; confirm the proposed additive vocabulary scope before its separate
ontology rehearsal; record an exact accepted decision; then obtain separate
publication approval. No decision or publication authorization has been inferred.
The operational queue remains local and is excluded from the implementation
commit, as are unrelated workspace and Compose changes.