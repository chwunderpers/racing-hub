# Formula One 2026 Source Investigation

Verified: **2026-09-10**. Scope: Racing Hub issue #5, privately reviewed full-season candidates, never automatic publication. This is source research, not a licence determination or an approved season dataset.

## Decision

**Update:** the user subsequently authorized factual PoC acquisition. The
[follow-up investigation](formula-one-endpoint.md) verifies public structured
session fields and records the captured factual fixture. The operational workflow
is now documented in [source workflow](../source-workflow.md). The original
rights findings below remain evidence, not an implementation prohibition or a
claim of legal clearance.

**Do not enable automated Formula1.com acquisition or commit a full-season raw fixture yet.** The official pages are publicly reachable, but current F1 terms expressly prohibit scraping and its guidelines restrict substantial timing-data reuse and AI use. Private review alone does not resolve these restrictions. Obtain written permission covering acquisition, retention, deterministic fixtures, private processing and any later display, or use a separately licensed source. No raw fixture was saved during this investigation.

The live F1 calendar displays **23 numbered race rounds plus two testing events**. FIA independently lists **23 non-called-off events and one called-off Saudi Arabian event**. These are observations of the current revision, not proof that the application has approved that revision. Do not hard-code an assumed 24 active races or silently discard cancellation history. [F1 calendar][f1-calendar] [FIA season][fia-season]

## Verified Endpoints And Response Behavior

| Endpoint | Observed structure and use | Limitations |
| --- | --- | --- |
| [F1 season calendar][f1-calendar] | Public HTML; numbered race cards with event links, sponsor title and meeting date range; testing cards separately labelled. Direct GET returned 200, `text/html; charset=utf-8`, 583782 bytes, HTTP Date `Thu, 10 Sep 2026 08:20:12 GMT`. | No ETag or Last-Modified observed. Inspection found no `script#__NEXT_DATA__` or `application/ld+json` script opening tag. No verified standalone JSON endpoint or embedded JSON field paths. Do not assume older Next.js page-data recipes apply. |
| [F1 Australia meeting][f1-australia] | Rendered schedule has Practice 1/2/3, Qualifying and Race, dates, start times, practice/qualifying end times, report/results links, and My time / Track time controls. Race results link identifies Australia as `1279` in `/en/results/2026/races/1279/australia/race-result`. | This is a results-route identifier, not a verified circuit ID or universal meeting API key. Session timestamps, offsets, source status enums and embedded schema were not verified. |
| [FIA season information][fia-season] | Public HTML calendar entries carry race date, event name, circuit label, country label and explicit notices such as `CALLED OFF`. Some entries link to individual events/classifications. | No stable machine-ID/schema contract verified. A country label may describe the event's identity rather than the circuit's physical country. |
| [FIA start-times entry link][fia-start-entry] | The season page links this path containing `season-2025`; fetched content identifies the [2026 canonical page][fia-start]. | Preserve the discovered link and canonical URL separately; do not rewrite the year by assumption. |
| [FIA canonical start-times page][fia-start] | Direct GET returned 200, `text/html; charset=utf-8`, 71393 bytes, HTTP Date `Thu, 10 Sep 2026 08:21:50 GMT`. Timetable is an HTML image, not a text table; no iframe/embed/object or timetable PDF/CSV/ICS link found in the inspected markup. | No verified machine-readable full-season session feed. |
| [FIA timetable JPEG][fia-timetable] | Exact image `src` observed on the canonical start-times page. The `itok` query is part of the published image URL, not an API credential. | Asset URL verified from HTML only; image contents, update date, individual times and offset legend were not decoded or verified. Not suitable for an unattended structured-data adapter. |

F1's page exposes an Add F1 calendar control, but no direct ICS link was found in the calendar inspection. No ICS service or private/internal API is claimed to work. No authentication, browser-exposed API keys, access-control workarounds or protected endpoints were used. F1 network inspection stopped after the restrictive terms were read.

## Identity, Status And Coverage

- F1 currently labels Australia round 1 and Spain round 14. Round is revision-dependent ordering, not stable identity. Testing must not become championship rounds. [F1 calendar][f1-calendar]
- FIA explicitly labels Saudi Arabia on 19 April `CALLED OFF`; the live F1 numbered calendar omits it. Absence from one source is not sufficient evidence of cancellation; retain FIA's explicit notice and provenance. [FIA season][fia-season]
- The Bahrain-named event is shown on 4 October at **SEPANG**, with an explicit note that it will be held in Malaysia. F1 lists its meeting range as 2-4 October and round 16. Do not derive circuit or timezone from the `bahrain` slug, event country flag, or last year's mapping. [FIA season][fia-season] [F1 calendar][f1-calendar]
- Barcelona-Catalunya and Spain are distinct meetings; FIA labels their circuits CATALUNYA and MADRID IFEMA. Do not collapse them into one country-based identity. [FIA season][fia-season]
- The F1 page's global Event Tracker refers to the next championship session even on the Australia page. It is not Australia's meeting/session status. Result/report links are evidence of available results, not a documented status enumeration. Keep raw explicit statuses separate from application interpretations.
- Stable application identities require a reviewed source-event and circuit crosswalk. Sponsor names, round numbers, dates and venues can change independently. Cancellation, relocation and rescheduling must be reviewed revisions, not silent deletion/recreation.

## Time Semantics

**Verified:** Australia is shown as 6-8 March. Its rendered schedule includes all five standard F1 session labels; practice and qualifying rows have ranges, while the race row shows only a start. My time and Track time modes exist. The text-only rendering does not reliably identify the selected display timezone. Consequently this report does not transcribe those clock values as UTC or event-local timestamps. An HTTP Date header timestamps the response, not the schedule revision. [F1 Australia][f1-australia]

**Not verified:** ISO timestamp fields, numeric offsets, IANA zones, a complete status vocabulary, per-session IDs, the FIA image's local/UTC convention, and complete-season session-time coverage. No exact resolved session instant is supplied here.

Required adapter rules (engineering recommendations, not claimed source schema):

1. Preserve the source date, clock text, precision, offset and stated timezone independently. A day-only meeting date stays day-only; never invent midnight or a session start.
2. A timestamp with an explicit numeric offset resolves an instant: UTC equals local time minus the offset. An offset is not an IANA timezone; do not infer one uniquely from it.
3. Resolve a local clock only with a reviewed circuit-to-IANA mapping and date-specific timezone rules. Record the tzdb version. Reject nonexistent DST times and retain ambiguous times unresolved unless the source disambiguates the fold/offset. Never use the host/browser timezone to interpret source data.
4. When a supplied offset disagrees with the reviewed event zone for that date, preserve the source and quarantine the conversion for review. Do not silently correct it.
5. Browser-local, UTC, event-local and selected-IANA displays must all render the same resolved instant. Unresolved values keep their original precision and an explicit unresolved label; do not show converted alternatives.
6. Keep event-local calendar dates independent of UTC dates. Never assume races occur on Sunday or derive a race end from start plus a conventional duration. Missing duration/end is unknown.

## Deterministic Adapter Input

The following is a **proposed normalized research record**, not raw provider JSON and not a valid existing application envelope. It contains only a compact incidental factual example, with deliberately unresolved session/time metadata. Australia dates/round are from the F1 calendar and circuit label from FIA. These limited facts do not constitute permission to reproduce the season database.

```json
{
  "season_year": 2026,
  "source_event_url": "https://www.formula1.com/en/racing/2026/australia",
  "observed_on": "2026-09-10",
  "round": 1,
  "meeting_start_date": "2026-03-06",
  "meeting_end_date": "2026-03-08",
  "source_circuit_label": "ALBERT PARK",
  "event_zone": null,
  "source_status": null,
  "sessions": null,
  "session_capture_state": "not_verified"
}
```

After rights clearance, acquire an immutable, permission-covered source snapshot through ordinary public GET or a provider-supplied export. Record the exact request and canonical URLs, UTC acquisition time, HTTP validators if present, content type, payload SHA-256, permission reference and parser version. Do not retain page secrets, images, unrelated articles, results or advertising in a factual fixture.

Use an HTML DOM parser to scope the calendar section and follow event-card links, excluding navigation duplicates and testing cards. For any subsequently verified embedded JSON, extract the script text through the DOM and use a JSON parser with explicit schema validation; do not parse JavaScript with `eval` or regex. No concrete JSON selector beyond the negative `__NEXT_DATA__` observation is currently verified. FIA's image needs an authorised export or human transcription with independent review; OCR alone is not authoritative session data.

Pin the permitted payload or approved factual export, parser version, identity crosswalk, timezone mapping and approval manifest as adapter inputs. The manifest must name every included event and distinguish 23 active races from retained cancellation records for this observed revision. A fresh network response or changed source ordering must not alter a deterministic fixture run. Full-season session capture remains blocked until rights and the missing source schema/time semantics are resolved.

## Retrieval, Revisions And Failure Policy

- A retrieval is an observation, not a revision. Identical normalized factual data with a new retrieval timestamp is a no-op for the candidate revision; retain retrieval audit metadata separately.
- Compare canonical semantic data, not HTML hashes alone. Navigation, advertising, countdowns, current results and sponsor assets can change without a schedule change. Preserve a raw hash for evidence and a semantic hash for revision detection.
- Changes to membership, round order, circuit, date/time, precision, status or source-supported identity create a new private candidate. Retain the previous revision and produce a reviewable diff. Never automatically publish or overwrite the last valid Publication.
- Fail closed on missing permission, robots changes, 401/403/429, CAPTCHA, unexpected redirects/hosts, invalid content types, incomplete pages, schema drift, duplicate identities, missing expected meetings, unrecognised session labels, conflicting evidence or unresolved required time conversions. Do not try alternate identities, credentials, proxies or hidden endpoints to recover access.
- A successful HTTP response is not proof of completeness. Reconcile against the approved manifest, explicit cancellation evidence and available-session expectations; absence of session data must not become an empty verified schedule.
- On acquisition/validation failure, preserve the last valid Publication and mark it stale with last successful verification time and reason. If none exists, report unavailable. Missing authoritative times stay unknown; no invented fallback dates or times.

## Robots, Terms And Rights Gate

- [F1 robots][f1-robots] currently includes `User-Agent: *`, `Allow: /` and a latest-tags restriction. The fetched formatting separates the tags pattern from `Disallow:`; do not normalize that ambiguity into a licensing grant. Calendar crawling is not explicitly excluded in the observed text, but robots permission is not a reuse licence.
- [F1 Digital Products Terms][f1-terms], labelled **Last Updated: August 2025**, expressly prohibit text/data mining and web scraping, collecting/harvesting data, and most extraction/storage/distribution. They reserve text/data-mining rights and discuss AI use. The law-dependent exception is not clearance established by this research.
- [F1 Legal Notices][f1-legal] discuss personal non-commercial copies and limited private educational research, but also prohibit extraction/republication and reserve database rights. These clauses do not clearly license a complete application fixture, shared repository, recurring automated workflow or publication.
- [F1 Guidelines][f1-guidelines], Timing Data section, allow individual data pieces incidentally within genuine editorial material but restrict substantial reproduction. The AI section requires an express licence for use of F1 rights with AI. Logos, images, circuit artwork and other presentation assets are outside this proposed factual dataset. Permission enquiries: `brandprotection@f1.com`; legal notices also provide `admin@formula1.com`.
- [FIA robots][fia-robots] specifies `Crawl-delay: 10` and disallows administrative/search and other paths, not the observed event pages. Honour its delay and scope for any authorised acquisition. The footer's [actual terms URL][fia-terms] could not be meaningfully text-extracted; the guessed `/terms-and-conditions` URL returned 403 and was not bypassed. FIA reuse terms therefore remain **unverified**, not permissive by default.
- Whether particular facts are protectable, a statutory exception applies, or a privately retained factual export is permitted requires rights/legal review in the relevant jurisdiction. Public HTTP 200, non-commercial intent and private review are not substitutes for that decision.

Research boundary: no tests, environment changes, application/configuration edits, commits or raw-source fixture writes. Only this report was created. Remaining blockers are permission for full-season retention/use, verified structured session fields and exact time semantics, and human approval of season membership/revisions.

[f1-calendar]: https://www.formula1.com/en/racing/2026
[f1-australia]: https://www.formula1.com/en/racing/2026/australia
[f1-robots]: https://www.formula1.com/robots.txt
[f1-terms]: https://account.formula1.com/#/en/terms-of-use
[f1-legal]: https://www.formula1.com/en/information/legal-notices.7egvZU48hzrypubGBNcQKt
[f1-guidelines]: https://www.formula1.com/en/information/guidelines.4EOKE9RRqevL4niTK9kWyt
[fia-season]: https://www.fia.com/events/fia-formula-one-world-championship/season-2026/2026-fia-formula-one-world-championship
[fia-start-entry]: https://www.fia.com/events/fia-formula-one-world-championship/season-2025/2026-fia-formula-1-start-times
[fia-start]: https://www.fia.com/events/fia-formula-one-world-championship/season-2026/2026-fia-formula-1-start-times-1
[fia-timetable]: https://www.fia.com/sites/default/files/styles/content_details/public/f1_start_times_16x9.jpg_2.jpeg?itok=YE0UYVpW
[fia-robots]: https://www.fia.com/robots.txt
[fia-terms]: https://www.fia.com/file/83930/download