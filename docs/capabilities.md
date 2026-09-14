# Optional Meeting Capabilities

Issue #14 proves a removable synthetic capability attached to a canonical
Meeting. "Event" is audience shorthand; the contract uses Meeting and Session
IRIs, not a new canonical Event type. No weather or live-timing provider is
integrated.

## Registration Interface

`CapabilityRegistry.register(definition)` is the single registration interface.
The definition is JSON-compatible data, validated by `CapabilityDefinition`:

```json
{
  "id": "synthetic-note",
  "title": "Synthetic Meeting note",
  "records": [
    {
      "subjectIri": "https://w3id.org/motorsport-hub/resource/meeting/f1%3A2026%3Aaustralia",
      "text": "Demonstration marker: A-01."
    }
  ]
}
```

The shipped module is
`backend/app/optional_capabilities/synthetic-note.json`. The loader discovers
only JSON files in that directory and passes each through `register`. There is
no import-time provider execution, external URL fetch, mutation callback, SQL,
credential, or registration endpoint. The module supplies both UI and assistant
data without registering separately in either consumer.

Contract limits:

- At most 10 modules and 20 unique subject records per module.
- Module files are limited to 100,000 bytes; reads are bounded before parsing.
- IDs are lowercase ASCII slugs of at most 50 characters, unique per registry.
- English titles are at most 100 characters; English text at most 1,000.
- Subject IRIs are at most 500 characters, under the existing resource authority
  and the `meeting/` or `session/` path. Exact canonical percent encoding is
  required. Labels, names, source IDs and external URLs are not join keys.
- Extra fields, duplicate registrations and duplicate subjects are rejected.
- Returned records have an immutable `kind: synthetic` discriminator. Registered
  data is copied; editing the caller's input cannot mutate the registry.

This PoC accepts trusted, repository-reviewed English module files. It is not an
untrusted plugin sandbox, runtime authoring interface, or natural-language
validator. It intentionally supports declarative synthetic notes, not arbitrary
provider code, HTML, custom UI components, or executable tools.

## Read Surfaces

`GET /api/capabilities?subjectIri=<encoded canonical IRI>` returns the current
publication version and up to 10 matching contributions. An exact published
document with the matching Meeting or Session RDF type must exist. Unknown or
unpublished identities return 404; malformed input returns 422. POST is not
supported. The synthetic record is neither added to canonical documentation nor
published to PostgreSQL or GraphDB.

The Meeting detail composition fetches this separate endpoint. It refuses a
publication version different from the displayed schedule and ignores responses
from prior navigation. Errors have a retry control; no records produce no
capability heading, placeholder, or module-specific controls. `MeetingDetails`,
the schedule endpoint, schedule models and schedule projections are unchanged.
Session IRIs are supported by the contract and tool; this sample contributes
only to the Meeting view.

The assistant loads a fresh registry for each turn. When it is nonempty, the
Microsoft Agent Framework provider advertises `meeting_capabilities` with one
typed `CapabilityQuery`. The assistant can obtain canonical subject IRIs through
its existing published-document tools. The read checks the same current
publication and resource type and uses the existing six-call and 90,000-byte
turn limits. Comparison mode still exposes no tools.

Synthetic results are returned in a separate `contributions` field and rendered
as plain text with "Synthetic data / Not sporting evidence". When this tool is
used, server-controlled text replaces model-written claims and classification
remains `unsupported`, with no publication-source citation attached to synthetic
data. The last successful capability read in a turn supplies the displayed
records. This intentionally does not establish schedule facts, results, rules,
eligibility, freshness, or an additional evidence class.

## Removal

Delete the single synthetic module JSON file. No schedule, frontend or assistant
code change is required. `CapabilityRegistry.remove(id)` also supports removal
from an explicitly constructed registry.

For a source-run backend, file removal is observed on the next capability
request and assistant turn. Docker copies the module into the backend image;
rebuild the backend after deleting it from the checkout. An already rendered
page or ephemeral assistant response remains a historical display until
navigation, reload or conversation reset. Removal is not server-push revocation
of already delivered data. New detail reads contain no synthetic block and new
assistant turns do not advertise the capability tool when no modules remain.

Malformed module files fail validation; do not treat these as registered
providers. Schedule reads do not depend on the loader. There is no publication
or database migration to undo, and no source approval is implied by registering
a synthetic note.

## Verification

`backend/tests/test_capabilities.py` exercises the public registration interface,
bounded validation, physical file deletion, HTTP reads against disposable
PostgreSQL/GraphDB publications, unchanged schedule responses, and actual
Microsoft Agent Framework SDK tool discovery/removal through a simulated model
HTTP transport. Frontend tests exercise display/removal, retry, publication
mismatch, navigation isolation and distinct assistant rendering.

The test boundaries follow parent Issue #1's Testing Decisions for optional
registration/deletion, typed assistant tools and detail views. The implementation
baseline is `3c25fa45ad875b6e974511ae453f9924417e6eaa`. Delivery is a local commit on
the current branch; no push, PR, merge or canonical publication is part of this
implementation request.

Verification on 2026-09-14:

- Full backend: 293 passed, no skips (1,270.40 seconds), including disposable
  PostgreSQL and secured GraphDB integration tests.
- Full frontend: 24 passed; TypeScript and production build passed.
- Focused Pyright: zero errors for the capability implementation and tests.
- Live desktop 1440x1000 and mobile 390x844 screenshots: synthetic marker and
  disclaimer visible, canonical identity expandable, no horizontal overflow.
- Live assistant HTTP 200: marker `A-01` returned in `contributions`, zero
  citations, `unsupported` evidence classification, server-controlled disclaimer.
  Existing schedule source freshness remained stale; no refresh was fabricated.
- Live schedule retained 50 Meetings and publication
  `61f2c49c6232aa786352eeb667c102fb14ec0be341d263a68413d23e694da7b1`.
  Only backend/frontend images were rebuilt; stores were not rebuilt and no
  canonical data was published.

Standards and specification review results are recorded after the implementation
commit. Existing unrelated Compose, review queue and local customization files
are excluded from this work.