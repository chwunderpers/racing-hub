# Issue 11 Verification

Implementation checkpoint: `e0f03d795a075de765a62299a2d49587d21136b4` on
`feature/11-f1-regulations`. Review baseline:
`cb0b40973a55e524cbdaed60a473a17202871825`. This is a pending-review
implementation, not an approved regulation Publication.

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