# Private Ontology Maintenance

Issue #10 adds an offline proposal and migration rehearsal. Select **Racing
Ontology** in VS Code or invoke `/racing-ontology`. This is an operator workflow,
not a website assistant tool. It makes no network requests, reads no credentials,
and never changes PostgreSQL, GraphDB, published documents or the current
Publication. It runs from the source checkout, not the backend container.

## Run A Review

Install the project's backend development requirements in the existing virtual
environment. From the repository root in PowerShell:

```powershell
$env:PYTHONPATH = 'backend'
.\.venv\Scripts\python.exe -m app.ontology_maintenance `
  --baseline ontology/motorsport.ttl `
  --ontology ontology/motorsport.ttl `
  --data ontology/examples/schedule.ttl `
  --proposal ontology/examples/proposal.json `
  --output ontology-reviews/baseline-001
.\.venv\Scripts\python.exe -m pytest backend/tests/test_ontology_maintenance.py -q
```

Use a fresh output directory each time. Exit 0 means **pending human review**, not
approved; exit 2 means blocked. SHACL or competency failures produce a blocked
report. Malformed requests fail before creating a bundle. Interrupted execution
may leave a partial directory; it is not review evidence without a complete
report and successful exit. Existing bundles are never overwritten.

For a change, pass a separate candidate ontology and a JSON proposal containing
`title`, `rationale`, `compatibility_notes`, `migration_notes` and `renames`.
The notes are required, nonempty English prose. `renames` maps full old vocabulary
IRIs to full new vocabulary IRIs, for example:

```json
{
  "https://w3id.org/motorsport-hub/ontology/circuit":
  "https://w3id.org/motorsport-hub/ontology/usesCircuit"
}
```

This is a migration example, not a proposed change to the live Circuit contract.
The old term must be declared in the baseline, the new term in the candidate,
and the candidate must contain no old-term references. Replacements are
simultaneous, one-to-one, and cannot merge existing vocabulary terms, cycle,
chain or rename resource identities. This command rehearses IRI replacements,
not arbitrary data transformations or executable migration scripts. More complex
changes require separately reviewed fixtures and a new migration implementation.

## Review Evidence

- `report.json`: status, proposal notes, conservative compatibility classification,
  SHA-256 input hashes, changed-triple counts and all competency outcomes.
- `review.md`: compatibility and migration notes plus the human-review gate.
- `added.ttl` / `removed.ttl`: semantic vocabulary delta using blank-node-aware
  RDF comparison. Any removal is classified breaking; additions still require
  review for semantic effects on consumers. Unchanged means RDF-isomorphic.
- `ontology.ttl`: the separately serialized candidate vocabulary.
- `migrated.ttl`: copied, migrated example assertions; input files stay unchanged.
- `knowledge.trig`: separate `ontology`, `asserted` and `inferred` named graphs
  under `https://w3id.org/motorsport-hub/graph/ontology-review/`.
- `competency.trig`: a separate synthetic proof dataset using the same graph
  roles, never mixed into the proposed example knowledge.
- `validation.ttl` / `validation.txt`: actual pySHACL reports for candidate
  vocabulary and migrated assertions. Blocked artifacts are private quarantine
  evidence, not canonical knowledge or publishable exports.

OWL-RL materialization uses the pinned `owlrl` implementation. The inferred
graph is the closure minus both explicit vocabulary and asserted instance
triples. No global GraphDB default graph, historical Publication or unrelated
premises participate. Required competency checks prove Championship-to-Competition
classification, inverse Circuit traversal, a shared-Circuit property chain,
same-label/different-IRI isolation and asserted/inferred graph separation.
Self-pairs follow the property-chain semantics; distinct-resource queries must
filter them. Shared Circuit does not imply shared Layout or season completeness.
This is a competency proof, not a complete OWL consistency or OWL-DL profile checker.

## Validation And Approval

Vocabulary IRIs use `https://w3id.org/motorsport-hub/ontology/`; instance IRIs use
`https://w3id.org/motorsport-hub/resource/`. Standard RDF/RDFS/OWL/XSD references
remain standard. External evidence links are permitted through `sourceUrl`;
placeholder identities and remote ontology imports are rejected. Turtle inputs
are local files capped at 1 MB and 5,000 triples each. This private trusted-input
tool is not a sandbox for hostile ontologies or an unbounded service API.

SHACL checks required Meeting labels, Competition and Circuit links, typed dates,
date ordering and uniqueness of optional canonical `identity` keys. Labels never
establish identity. It rejects explicit non-English and untagged human-readable
strings while keeping machine fields (identifiers, dates, status codes, time
zones, checksums and numeric values) language-neutral. The machine-field policy
is in `backend/app/ontology_validation.py`; unknown string properties default to
English prose. Declared renames also update the bundled validation constraints.

An `en` tag does not prove the text is English. The operator must review actual
wording, translations, definitions and compatibility notes. Record the reviewer,
time, rationale and exact input hashes in the issue before accepting a proposal.
Acceptance is not authorization to publish. Promotion and any canonical data
migration require a separate explicit decision and publication agreement checks.

The parent issue referred to an older executable ontology demonstration that is
not in this checkout. With operator approval, these synthetic fixtures and the
existing RDF builder provide the executable baseline instead. Current published
knowledge and the website assistant's asserted-only graph access are unchanged.