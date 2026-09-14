# Accepted Knowledge Exports

Issue: [#15](https://github.com/chwunderpers/racing-hub/issues/15).

Open the **Exports** view at `http://localhost:5173/?view=exports`.
Choose JSON-LD, CSV, or RDF (Turtle), then download the selected accepted
Publication. The independent OWL ontology download does not require a
Publication or either database.

## HTTP Contract

- `GET /api/exports` returns `publicationVersion`: the current accepted
  Publication's SHA-256 version, or `null` before the first publication.
- `GET /api/exports/publications/{version}/json` returns `application/ld+json`.
- `GET /api/exports/publications/{version}/csv` returns `text/csv`.
- `GET /api/exports/publications/{version}/turtle` returns `text/turtle`.
- `GET /api/exports/ontology` returns the canonical OWL vocabulary as Turtle.

Publication URLs require a lowercase 64-character hexadecimal version.
Every format comes from the same filtered, asserted RDF graph rebuilt from
that accepted PostgreSQL snapshot, not from GraphDB's union of named graphs.
This uses the existing deterministic publication graph builder; it makes no
GraphDB request and requires no GraphDB-specific consumer behavior.

Only the current accepted version is downloadable. A staged, unknown, or
superseded version returns `409`; the selected version is checked before and
after graph construction. The server never substitutes a newer version.
Refresh the selection after a conflict. This is an export of accepted public
knowledge, not a historical archive or backup interface.

Unsupported formats or malformed versions return `422`. Publication store
failures return a sanitized `503`. Publication selections, downloads and
conflicts are non-cacheable. Downloads carry `Content-Disposition`,
`X-Publication-Version`, and `X-Content-Type-Options: nosniff` headers.

## Portable Data

JSON-LD is ordinary JSON with absolute RDF IRIs and explicit literal types
and language tags. It has no remote context to fetch. Turtle represents the
same RDF triples. Neither format contains the ontology or inferred triples.
Canonical `https://w3id.org/motorsport-hub/` identities remain unchanged.

CSV is a lossless statement table rather than a flattened Meeting list:

| Column | Meaning |
| --- | --- |
| `publicationVersion` | Accepted snapshot version, repeated on every row |
| `subject` | RDF subject in N3 term syntax, normally `<absolute-IRI>` |
| `predicate` | RDF predicate in N3 term syntax |
| `object` | RDF term, including quotes, datatype or language suffix |
| `objectKind` | `iri` or `literal` |
| `datatype` | Literal datatype IRI, when present |
| `language` | Literal language tag, when present |

Use a standard CSV parser before parsing the three RDF terms. Quoted or
multiline literals remain single CSV cells. RDF term quoting is part of the
value, not merely CSV escaping: a literal beginning with `=` still begins
with a quote in its decoded cell, preventing spreadsheet formula execution.
Removing RDF quoting before opening a spreadsheet loses this protection.

An independent consumer can parse JSON-LD and Turtle with RDFLib and
reconstruct CSV with `csv.DictReader` and `rdflib.util.from_n3`. The integration
tests compare these reconstructed graphs by RDF isomorphism and assert known
Meeting, Session, vehicle, regulation passage and provenance triples.

## Public Boundary

The export preserves Publication identity/version, source URLs, retrieval
times, source/document checksums where present, evidence locators, language
metadata, field preferences, applicability and translation method/version/time.
Source precision and unresolved time fields are retained without inventing
offsets. Human-readable content is English; neutral IDs, codes and datatypes
are not relabeled. Freshness is not reset by downloading an export.

The public predicate allowlist excludes candidate approval notes (`evidence`),
private interpretation/review notes (`rule`), reviewer identities,
translation authorizations, internal source identities and review state.
Private review artifacts, credentials, assistant conversations, optional
synthetic capabilities, staged data, history and inferred graphs are not
included. This does not claim access to original source documents or grant
new redistribution rights to source material.

## Independent Ontology

The ontology route serves the exact bytes of `ontology/motorsport.ttl`, included
in the backend image. It contains vocabulary declarations, not instance data,
SHACL policy or private proposal artifacts. The SHA-256 checksum appears in
its HTTP download filename and ETag. The browser's download action uses the
stable filename `racing-hub-ontology.ttl`; the downloaded bytes are identical.
The ontology is versioned independently by its content hash and repository
revision, not by the selected Publication. Rebuild the backend after an
approved canonical ontology change. This issue makes no vocabulary changes.

## Verification

The agreed boundaries are public HTTP downloads over isolated publications
and the rendered UI download workflow. Review baseline:
`988a70da17e1fb940ed4df0ff255c722eb83f768`.

- HTTP tests cover cross-format graph agreement, known resources and English
  evidence, source provenance, private-note exclusion, formula-like literals,
  accepted/staged/superseded isolation, input validation, read-only methods,
  unavailable stores and byte-exact independent ontology delivery.
- UI tests cover all formats pinned to one version, conflict and refresh,
  independent ontology download, blob URL cleanup, and empty/unavailable states.
- Full backend suite: **298 passed, no skips** (1,338.72 seconds), using
  disposable PostgreSQL and GraphDB fixtures. Frontend suite: **27 passed**,
  with no unhandled errors. Production build and generated API types pass;
  Pyright reports zero errors for the export module and HTTP tests.
- Live downloads each reconstruct the same **6,688 triples**: 50 Meetings,
  146 Sessions, two Competition Profiles and three Vehicle Models. Publication
  `61f2c49c6232aa786352eeb667c102fb14ec0be341d263a68413d23e694da7b1`
  remains unchanged. No source refresh or data publication was performed.
- Independent ontology: 172 triples, SHA-256
  `a8d6a348cd525ae4a3a74bfc49d73a31d786714fb37ce954cd4bdc51fc84e859`.
- Standalone headless Edge downloaded all four files successfully. JSON-LD:
  1,094,611 bytes; CSV: 2,004,927; Turtle: 510,907; ontology: 11,637.
  The embedded browser did not emit download events, so standalone Edge was
  used to verify actual files rather than treating that timeout as success.
- Desktop (1440px) and mobile (390px) screenshots preserve the existing design;
  320px also has no horizontal overflow. Only backend/frontend containers were
  rebuilt. The local view is available at `http://localhost:5173/?view=exports`.

## Review

Implementation commit: `3c11aab`.
Review command: `git diff 988a70da17e1fb940ed4df0ff255c722eb83f768...HEAD`.
The baseline resolved and the 12-file committed diff was confirmed nonempty.
Two independent agents reviewed the supplied scoped files, rather than
independently reconstructing the Git diff. Test and live evidence above was
supplied by the implementing agent, not independently rerun by reviewers.

### Standards

Zero documented-standard violations and zero named code-smell findings.
The review checked domain terminology, public/private filtering, canonical
IRIs, English content, response handling and consistency with the existing UI.

### Spec

Zero substantive findings: all six Issue #15 criteria are represented in the
implementation and its HTTP/UI tests. No missing requirements or scope creep
were identified. Review did not establish broader PoC acceptance for #16.

Totals: Standards 0; Spec 0. No push, PR, merge or issue closure is authorized
by this implementation step.