# NLS 2026 Source Research

Implementation update: Issue 7 now uses these observations under Chris's explicit
2026-09-10 standing local-PoC authorization. See [the implemented contract](../source-workflow.md#nls-and-poc-authorization).
The research wording below records the earlier investigation state; it does not
override that later authorization. Source-rights and incomplete-evidence limits
remain. Ordinary 2026 route length is not promoted from unversioned venue prose.

Research for Issue 7, observed 2026-09-10. Scope: factual local PoC acquisition through ordinary public GETs only. This is not rights clearance, implementation, identity-mapping acceptance, or publication approval. Only this English Markdown research note is retained in the repository.

## Result And Scope

The [current calendar][C] contains **nine rows covering ten numbered Round slots**, with eight NLS-hosted round pages and one externally linked Qualifiers entry. The [English season announcement][A] describes **eight programme groups**, combining both April races and both September races. All eight NLS round pages returned HTTP 200 and yielded **40 timetable rows: 16 qualifying/race rows and 24 spectator/grid activities**. These are planned observations, not 16 verified completed Sessions. The [linked test page][T] adds **seven unnumbered test dates with ten published track-time windows**. No independent preseason test Meeting was found in these calendar/test inventories; this is not proof that none exists elsewhere.

Two material status changes are verified in original English: **NLS1 cancelled on March 14** and **NLS4 halted and not resumed on April 18**. The April 19 report explicitly says the season consequently comprises **eight countable races**, while the calendar retains ten numbered slots. Preserve both scopes and both histories. NLS2 was moved one week earlier to March 21. **No replacement race is established by the reviewed sources.** Do not reclassify the next numbered race as a replacement or renumber the calendar.

This is a different acquisition surface from F1 and GT: server-rendered WordPress HTML, editorial status articles, and a public document portal. A representative round page's JSON-LD is a `@graph` of WebPage/BreadcrumbList/WebSite/Organization, **not a sporting Event/session feed**. No public schedule API, durable provider Session IDs, numeric circuit registry or timezone field was verified. A future adapter should parse calendar/timetable DOM and preserve field-level assertions, with PDF ingestion and review as separate requirements.

**Access blocker:** the calendar's linked Qualifiers organiser, [24h-rennen.de][Q], returned HTTP 403 with a Cloudflare challenge. No retry with a changed identity, authentication or bypass was attempted. NLS's original-English preview and race-control articles nevertheless supply Round 4/5 numbering, several session clocks, duration, route and status evidence. **Parsing blocker:** five linked PDFs returned HTTP 200 with valid PDF signatures, but the available webpage reader could not extract meaningful text from the sporting rules and September timetable. No existing local PDF reader was found in the checked commands/modules. PDF contents, governing provisions and conflicts with HTML are therefore unverified, not inaccessible and not approved.

## Authority And Rights

The [English legal notice][L] identifies VLN VV GmbH & Co. KG, commercial register HRA 22096, as website operator. Official homepage and round-page links establish the discovery chain to `teilnehmer.vln.de`, the public participant/document portal. That landing page exposes downloads without login; no authenticated team, entry or race-control area was accessed. The calendar itself links the Qualifiers organiser. This establishes source authority and relationship, not an unrestricted right to copy their works.

The legal notice's Copyright section says operator-created content is subject to German copyright law, exploitation outside copyright limits requires written consent, and downloads/copies are permitted only for private, non-commercial use. No open-data licence, database-reuse permission, automated-access agreement, completeness warranty or API stability commitment was established. The test page also links a **2025** terms PDF from its 2026 page; applicability of those terms was not verified. Event participation terms are not a schedule-publication licence. The blocked Qualifiers site's own terms could not be assessed.

The user's factual public-GET PoC permission is **not rights clearance**. Broader retention, translations, redistribution and commercial/public publication need separate rights review, including third-party document rights. This note retains English factual summaries, not source prose, images, results, personal data, HTML or PDF payloads. Parser projections were bounded text/metadata in tool output; no raw HTML was logged and no raw PDF was saved. No page scripts were executed, no subresources were loaded by JSDOM, and no API paths or provider identifiers were invented.

## Complete Scheduled Inventory

Dates are Published Local Time at day precision. Numbering comes from explicit `NLS` labels, with Rounds 4/5 established by [the Qualifiers preview][P], not guessed from a numbering gap. Names below are English descriptions, not approved canonical names. Descriptions of German calendar/round fields are **translation proposals** under the provenance policy below. Nominal duration is distinct from scheduled or actual finish time.

| Round | Race date | Source record / English description | Nominal race duration | Status evidence and grouping |
| --- | --- | --- | --- | --- |
| 1 | 2026-03-14 | [R1: 71st ADAC Westphalia race][R1] | 4 hours | [Cancelled][S1]; retain calendar entry and planned clocks. |
| 2 | 2026-03-21 | [R2: 58th ADAC Barbarossa prize][R2] | 4 hours | [Date brought forward][S2]; round page links March 21 race reporting. |
| 3 | 2026-04-11 | [R3: 57th Adenau ADAC circuit trophy][R3] | 4 hours | Round page links April 11 race reporting. |
| 4 | 2026-04-18 | [Qualifiers, first race][P] | 4 hours | [Halted, no Saturday restart][S4]; same Qualifiers programme as Round 5. |
| 5 | 2026-04-19 | [Qualifiers, second race][P] | 4 hours | [April 19 report confirms fifth race][S5]; not a replacement for Round 4. |
| 6 | 2026-06-20 | [R6: first ADAC Eifel Trophy][R6] | 4 hours | Round page links June 20 race reporting. |
| 7 | 2026-08-01 | [R7: KW six-hour ADAC Ruhr Cup race][R7] | 6 hours | [English preview corroborates six-hour format and noon start][H]; round page links August 2 reporting. |
| 8 | 2026-09-12 | [R8: 65th ADAC Reinoldus endurance race][R8] | 4 hours | Future date at observation; separate source page, grouped with Round 9 in [A]. |
| 9 | 2026-09-13 | [R9: 66th ADAC ACAS Cup][R9] | 4 hours | Future date at observation; separate source page, not a second Session of Round 8. |
| 10 | 2026-10-10 | [R10: second NLS marshals' trophy][R10] | 4 hours | Future date at observation; URL and displayed name differ in wording. Preserve exact discovered URL. |

Eight programme groups are not nine HTML rows or ten Rounds. A **proposed** Meeting grouping can combine April 17-19 with Rounds 4/5 and September 12-13 with Rounds 8/9, preserving the separate race/round source records. That yields eight championship programme groups, not an approved canonical Meeting count. The Qualifiers preview explicitly gives April **17-19** as its overall span, while the calendar gives race dates April **18-19**. Preserve their scopes instead of fabricating Friday sessions or treating either span as a silent correction. Grouping September's separately named round pages, assigning stable Meeting IDs and attaching Friday tests require reviewed identity rules; one-calendar-row-equals-one-Meeting is not an adequate contract.

### Ancillary Test Inventory

The original [English test page][T] lists every date below in `.entry-content p` index 0 (zero-based), separated by six `br` elements. Paragraph index 1 defines the `*`/`**` formats. Some route words within that English page are German; the English route descriptions below are explicitly translation proposals. These are test activity assertions, not extra numbered Rounds or automatically seven separate canonical Meetings. Do not attach them to race Meetings merely by subtracting a day.

| Test date | Published association | Local track-time windows | Route description |
| --- | --- | --- | --- |
| 2026-03-13 | NLS1, `*` | 09:00-18:00 | NLS configuration |
| 2026-03-20 | NLS2, `*` | 09:00-18:00 | NLS configuration |
| 2026-04-10 | NLS3, `*` | 09:00-18:00 | NLS configuration |
| 2026-06-19 | NLS6, `**` | 08:00-14:00; 16:00-19:00 | Sprint course; then NLS configuration |
| 2026-07-31 | NLS7, `*` | 09:00-18:00 | NLS configuration |
| 2026-09-11 | NLS8/9, `**` | 08:00-14:00; 16:00-19:00 | Sprint course; then NLS configuration |
| 2026-10-09 | NLS10, `**` | 08:00-14:00; 16:00-19:00 | Sprint course; then NLS configuration |

The `*` span has a computed elapsed length of 540 minutes; the `**` spans are 360 and 180 minutes. These are **derived window lengths**, not a claim of continuous driving or a provider-stated Session duration. No test entry for April 17 is present in this inventory; Qualifiers Friday-session coverage remains incomplete, not verified empty. NLS1's race cancellation does not establish cancellation of the March 13 test.

## Session Precision And Status Conflicts

| Source and locator | Verified observation | Proposed extraction / limit |
| --- | --- | --- |
| R1/R2/R3/R6/R8/R9/R10, `.entry-content table.table tr`, first and fifth rows | Qualifying 08:30-10:00; race 12:00-16:00, stated 4 hours | Two planned track Sessions per round-page date. Preserve minute precision, both local clocks and stated duration. Qualifying elapsed 90 minutes is derived, not a new source field. R1's cancelled status must coexist with these original planned values. |
| R7, same table/rows | Qualifying 08:30-10:00; race 12:00-18:00, stated 6 hours | Distinct six-hour format; corroborated by H paragraphs 0 and 12. Never default every NLS race to four hours. |
| All eight round pages, middle three rows | Pit walk 10:20-11:00; grid walk 11:10-11:30; grid formation 11:00-11:40 | Preserve as non-session timetable activities. Do not create sporting Sessions from every row or infer chronology from row order. Grid formation is listed after the later-starting grid walk. |
| P paragraph 13, Saturday April 18 | Qualifying 08:30-10:00; race starts 17:30 | Race duration 4 hours is supported by C's two-four-hour-races label and P's race format. No published race end clock in this paragraph: leave it null, not an estimated 21:30. The noon three-hour race mentioned nearby belongs to a different championship; exclude it from NLS sporting applicability. |
| P paragraph 14, Sunday April 19 | Qualifying 08:15-09:45; Top Qualifying begins 10:40; second four-hour race starts 13:00 | Three distinct NLS track periods. Top Qualifying end/duration are unknown; race end clock is not supplied here. Do not estimate 17:00 or borrow Saturday times. |
| P paragraph 0 versus C's Qualifiers row | Overall Qualifiers April 17-19 versus race dates April 18-19 | Preserve programme span and race dates separately. Friday timetable is unverified. |
| S1 paragraphs 0-2, published March 14 | Qualifying initially delayed; final cancellation at 10:45; next Round 2 on March 21 | Meeting/round cancellation assertion, effective local March 14 at 10:45. Do not count the scheduled qualifying/race as completed or claim the next round is a replacement. No actual qualifying start established. |
| S2 paragraphs 0 and 3, published January 25 | Round 2 moved one week earlier to March 21; organisers agreed a date swap with RCN | Schedule Revision retaining NLS2 identity. English prose says both postponed and moved forward; direction is established by the explicit earlier-week explanation. March 28 as the old date is an arithmetic derivation, not a literal old-date field in this article. RCN is not an NLS replacement Meeting. |
| S4 paragraphs 0 and 3, published April 18 | First Qualifiers race halted in its early stages and would not resume that evening | Abandoned race assertion, not pre-start cancellation. Actual stop clock, elapsed driving duration and any classification consequence are not established by this bulletin. |
| S5 paragraph 10, published April 19 | Opening race did not take place; fourth race abandoned; season now eight races and no further discarded results | Evidence for sporting-count scope, not authority to delete Rounds 1/4 or renumber 5-10. Rules interpretation requires governing-PDF review. |

This establishes **21 planned qualifying/race observations** across the ten Round slots (16 in HTML tables and five in P), plus ten ancillary test windows. It does not establish a complete season Session inventory: Friday Qualifiers activity, detailed PDFs, final actual timings and further timetable revisions remain unassessed. Stream start times, spectator activities and other championships' races are not NLS Sessions.

No inspected source supplies an IANA zone or verified UTC offset for these clocks. Keep `published_local_date`, `start_local`, `end_local`, source precision and optional stated duration independently. A future `Europe/Berlin` association and date-specific DST conversion would be a reviewed derived rule, not a published field. Do not create UTC instants, assume one season-wide offset, or confuse event duration with the actual finish after safety interruptions.

## Venue, Circuit And Layout

Follow [CONTEXT.md](../../CONTEXT.md) and the [GT research](gt-world-challenge-europe.md): Venue, Circuit and versioned Layout are distinct. The existing GT source key **`gtwce:nurburgring` has unresolved layout identity**. A shared venue name, official domain, town or address does not approve a circuit/layout crosswalk. No canonical ID or crosswalk is allocated here.

The current calendar's opening paragraph describes the short GP-course/Nordschleife combination for all races (German evidence, English translation proposal). The generic [English venue page][V], paragraph 9, gives **24.358 km**, including the sprint course, Mercedes-Arena, motorcycle chicane and Nordschleife. It is unversioned explanatory evidence, not verified 2026 homologation or proof of every round's layout.

Crucially, the 2026 [Qualifiers preview][P], paragraph 12, explicitly says that the Qualifiers omit the AMG Arena, include the Muellenbach loop and use **25.378 km**, unlike ordinary NLS races. Thus the calendar's all-races route summary has a **season-specific exception/conflict**. Keep at least distinct ordinary-NLS and Qualifiers route assertions; do not attach 24.358 km to Rounds 4/5. T additionally distinguishes a standalone sprint-course test window from an NLS-configuration window. These three route descriptions do not themselves establish three approved canonical Layout IDs. Exact route version, ordinary-race season applicability and any relation to GT remain review items pending governing documents and explicit mapping acceptance.

## Regulations And Document Inventory

The [public participant landing page][D] links the [regulations index][I], [sporting bulletins index][B], technical bulletins, DMSB regulations and date-scoped noticeboards. Link labels below are English translation proposals of the German index, **not claims that the PDFs themselves are English or that their provisions were read**. Discover exact `a[href]` values; do not synthesize `download.php` file names or date-board identifiers.

| Published surface | Verified inventory / acquisition | Remaining requirement |
| --- | --- | --- |
| I, document anchors | Parts A1 sporting and A2 technical labelled 2026 approved after Bulletin 5; A3 organisational labelled 2026 final | A1 PDF GET verified as P1 below; A2/A3 are linked, contents not fetched/parsed. Approval in a provider filename is not Hub acceptance. |
| I, accompanying documents | 2026 TCR technical rules; Annex 1.1 vehicle classes/DPN, 1.2 season entry; technical annexes 2.1 and 2.5-2.15 including tyre procedure after Bulletin 2 | Inventory only. Do not invent missing annex numbers or derive eligibility, tyres, scoring or mandatory stops from labels. |
| B, document anchors | Eight sporting bulletins numbered 1-8, plus one rear-wing attachment to Bulletin 6 | Later Bulletins 6-8 are not proven incorporated into A1/A2 labelled after Bulletin 5. Applicability dates, superseded provisions and precedence require content parsing. |
| D, linked September noticeboards | Separate `onb.php?d=2026-09-12` and `onb.php?d=2026-09-13`; separate V1 timetables and approved supplementary regulations for R8/R9 | Both timetable PDFs GET-verified, different hashes; do not assume shared date grouping means byte-identical timetables. R8 supplementary PDF GET-verified; contents unparsed. |
| T, public links | 2026 test regulations PDF, 2026 English driver/passenger forms, but 2025 terms PDF | Test regulations GET-verified. Forms not acquired. Test rule/terms applicability and route details are unverified. |
| Q, calendar-linked organiser | HTTP 403 challenge | Independent Qualifiers regulations, official detailed timetable, legal terms and revision history blocked. No fabricated direct document URLs. |

The exact linked A2 and A3 URLs are [technical rules](https://teilnehmer.vln.de/download.php?file=teilnehmer/Ausschreibung/A2%20Ausschreibung%20Teil%202_TECHNISCHES%20REGLEMENT_2026_genehmigt_nachBulletin5.pdf) and [organisational rules](https://teilnehmer.vln.de/download.php?file=teilnehmer/Ausschreibung/A3%20Ausschreibung%20Teil%203_ORGANISATORISCHES%20REGLEMENT_2026_final.pdf). The [2025 terms link](https://www.nuerburgring-langstrecken-serie.de/wp-content/uploads/2025/01/2025-Terms-and-conditions.pdf) is recorded exactly, without silently changing its year. No provision-level citation or purported PDF-language precedence can responsibly be supplied from this investigation.

## Proposed Extractor Contract

This is an actionable research contract, not an implemented or approved adapter. Existing JSDOM was used with scripts/resources disabled; standard HTML DOM and JSON parsing are sufficient for the verified HTML surface. All eight round pages were actually read, not extrapolated from one example.

| Output / responsibility | Verified selector or input | Deterministic rule and fail condition |
| --- | --- | --- |
| Season discovery and race-date rows | C: `.entry-content table.table tr`; each row has two `td`; date in first, linked label in second | Require 2026 heading/context, nonempty table, valid literal date or date range and one link per row. Snapshot has nine rows, eight internal round URLs, one external Qualifiers URL. Treat changed counts as a coverage review, not a constant to force forever. |
| Source record identity | Discovered calendar `td:nth-child(2) a[href]`, exact absolute URL | URL is the observed source reference, not a promised durable provider ID. Keep aliases and revision history under an approved reconciliation rule. Do not use name/date equality, ordinal race names or array index as canonical identity. |
| Numbered Round | Calendar's explicit NLS label; internal page `.entry-content h2` with full `NLS` plus integer match | Cross-check values and reject ambiguous/mismatched labels. Expected internal set is 1,2,3,6,7,8,9,10. Rounds 4/5 require P's explicit dated editorial evidence, not gap filling. |
| Meeting grouping | A date groups, separate calendar source URLs, P's overall Qualifiers span | Preserve row, round and programme entities separately. Propose eight groups only with traceable grouping evidence; do not silently collapse two named round records or duplicate one Qualifiers Meeting per championship-bearing Session. |
| Planned timetable rows | Each internal page `.entry-content table.table tr`; first `td` clock interval, second activity label | All eight inspected tables have five two-cell rows. Parse both clocks at minute precision, preserving English factual assertions and source anchors. Missing table, malformed clocks, unknown labels, extra/removed rows or no matching season are incomplete/acquisition failure, never successful empty. |
| Session classification | Row label meaning and its reviewed translation record | Qualifying and race are track periods; three other rows remain ancillary activities. Unknown labels require review, not classification by row position alone. Row numbers are evidence locators, not Session IDs. Reconciliation across timetable versions is still required. |
| Qualifiers sessions | P `.entry-content p` indices 13/14, with indices 0/12 for scope/route | Editorial English is not a structured session API. Keep a checksum-anchored reviewed projection of the five known periods; changed article content requires reassessment. Do not blindly apply the ordinary-round table format. |
| Tests | T `.entry-content p` indices 0/1 and `br` boundaries | Require seven observed dates and their explicit markers for this snapshot; expand `*` once and `**` twice. Preserve route per window and null round membership; association with NLS8/9 does not duplicate the shared Friday windows. |
| Time and duration | Literal date/clock cells, stated race-hour labels, P's English clock assertions | Separate stated nominal duration, derived elapsed window length, planned end and actual end. Missing end/zone stays null with a reason. No estimated times. |
| Status / Revision / Replacement | S1/S2/S4/S5 dated assertions and their effective-date scopes | Store subject, asserted state/change, effective local time if known, publication context, source and competing schedule. Distinguish reschedule, cancellation and abandonment. Replacement link must be explicitly sourced and retain both identities; none is established here. |
| Place mapping | C/V/P/T route assertions and approved source-to-canonical lookup | Do not join to GT by name. Missing/version-conflicting Layout evidence blocks mapping acceptance, not retention of a source assertion. |
| Regulations | I/B/noticeboard document anchors and exact response hashes | Store discovered URL, link-version claim, MIME/signature, retrieval and parse state. Parse PDFs with a real document reader and section/page anchors before emitting any Provision. Filename order alone cannot settle applicability or supersession. |

Proposed provenance envelope for every field: `source_url`, `retrieved_at_utc`, `response_sha256`, `locator`, `source_language`, `assertion_kind`, `published_precision`, `source_publication_context`, `english_evidence`, optional `translation_record`, and explicit `review_state`. Add competing-assertion references, subject/source-record reference and effective time for status changes. These are proposed contract names, not fields published by the provider. German originals remain transient in-memory input; do not put them in fixtures, logs intended for repository retention or canonical records. Translation records require method/version/time/review state plus original URL/checksum/locator before persistence.

## Failure And Coverage Policy

1. GET only discovered public resources; validate scheme, expected host/redirect, status, content type, season and selector shape. Follow legitimate observed redirects, but stop on 401/403/429, login/challenge pages or an unexpected host. No invented API route, authenticated portal, identity switching or bypass.
2. Audit **scheduled inventory**, **status history**, **session detail**, **ancillary tests** and **regulations** separately for a named season and retrieval. This note covers the complete currently displayed C/T inventories; it does not prove complete document history, all cancelled/replacement notices or every Session ever planned.
3. `empty` is not `complete`. A successful empty timetable requires an explicit scoped source assertion of no activity and assessed coverage. Missing selectors, blocked organiser data, unparsed PDFs or missing Friday clocks mean incomplete/unassessed, not zero Sessions. A past/future filter returning zero matches says nothing about source coverage.
4. Preserve the last accepted publication on an acquisition failure, inventory reduction or unresolved conflict. Rounds 1/4 remain in history even where the expected countable-race scope is eight. No silent deletion, renumbering, reactivation from stale timetables or reassignment as a replacement.
5. Official English is preferred when available, but language is not authority or freshness precedence. R1-R10 timetable assertions rely on German evidence; P's 2026 layout exception is narrower than V's unversioned description. C/A currently show the revised March 21 date even though A has a September 2025 publication path: never interpret current page bytes as an immutable original calendar.
6. Remaining blockers: governing-PDF parsing and provision applicability; Qualifiers organiser access; Friday/detailed/final session coverage; exact time-zone resolution; durable Session and Meeting reconciliation; route versions and GT/NLS mapping review; translation acceptance; reuse rights and separate publication approval.

Status-history discovery used linked round articles and [English archive][N] pages one and [two](https://www.nuerburgring-langstrecken-serie.de/language/en/news-archive/page/2/), then the relevant January/April/July articles. This is a bounded first-party investigation, not an exhaustive audit of every German article or PDF bulletin. No replacement is established within that scope; absence of one is not a verified no-replacements assertion.

## Evidence Ledger

All timestamps below are on **2026-09-10 UTC**. SHA-256 covers complete HTTP response-body bytes held only in memory. Dynamic HTML hashes changed between GETs, including generated element IDs; byte inequality and WordPress metadata must not automatically create a Schedule Revision. Use assertion-level semantic change detection while preserving every Retrieval.

For all German-derived descriptions in this note, the translation record is: `sourceLanguage=de` (page `de-DE` or `de`), method `assistant factual translation`, version `nls-research-v1`, translated on `2026-09-10`, review state `unreviewed / translation proposal`. Each ledger URL/checksum plus the field locator identifies its original anchor. This applies to C, R1-R10, D/I/B link-label summaries and German route terms embedded in T. English article summaries are paraphrases of original English evidence, not new translations. PDF language is **unverified**; German link labels are not evidence of PDF language. No non-English passage or raw payload is retained in this file.

Paragraph indices below are zero-based `.entry-content p` selections; table rows are one-based. Paragraph locators refer to this observed representation and must be paired with a checksum, not assumed stable after edits.

| Ref | Retrieval time | Response SHA-256 | Language / factual locator |
| --- | --- | --- | --- |
| [C] | 10:35:17.602Z | `576fd43bccd09bd915758679635b6a5c14a05d10247ba47d8b4e4ffd8f94c38d` | de-DE; first paragraph, calendar table rows 1-9 |
| [A] | 10:35:18.099Z | `13e0c5ec25eb4fd3279d52a1aeccb830c46bf02f1401ba919bdfaf31e7b7c131` | en-GB; opening paragraph and date table |
| [R1] | 10:36:46.491Z | `9972d10ccf38218fcad5203fa660ec5cca0069491471c6c9fa01579e1b32bea5` | de-DE; h2 NLS1, timetable rows 1-5, linked cancellation article |
| [R2] | 10:36:46.984Z | `27aaf183e42ce928aa759ef3e037d09c890dd11251995637075c8d73e855c539` | de-DE; h2 NLS2, timetable rows 1-5, date introduction |
| [R3] | 10:36:47.383Z | `b8b58bf0e7fa2d6f03bae03570908fe7041223acb1f81731dd391c067699559d` | de-DE; h2 NLS3, timetable rows 1-5, date introduction |
| [R6] | 10:36:47.820Z | `420d0e5687624b9c8132653bedf1bbe33b6ed0b032b0c6e4ca679296afc3fc47` | de-DE; h2 NLS6, timetable rows 1-5, date introduction |
| [R7] | 10:36:48.244Z | `3e518c2a40d191da6fe04b69c12adf5ce5d955bf4646c844fbfee3f54609515f` | de-DE; h2 NLS7, timetable rows 1-5, six-hour race label |
| [R8] | 10:36:48.657Z | `0e7df250c884ed66e09355db61f3519972c6108f721a311ec9ac687ff6e0e1e3` | de-DE; h2 NLS8, timetable rows 1-5, date introduction |
| [R9] | 10:36:49.114Z | `21a9391db66a4b951cb9be0df4a32350750e0132e1cae086f65b7df8eb4bd6f8` | de-DE; h2 NLS9, timetable rows 1-5, date introduction |
| [R10] | 10:36:49.479Z | `9162b87bc5ffa46465a5834b837614be268717334c011bdd5a451eb2124f9285` | de-DE; h2 NLS10, timetable rows 1-5, date introduction |
| [S1] | 10:37:46.583Z | `52a66c738b36b079109144c70d4921d67becb593cbb0ee3270ed660e5cd64759` | en-GB; paragraphs 0-2, cancellation and effective local clock |
| [S2] | 10:38:32.895Z | `201b94011346dcb246cc94142e7c92bc2abe60d656cc4805b9f592d1dd5cbb34` | en-GB; paragraphs 0/3, date revision and RCN swap |
| [P] | 10:38:33.358Z | `c9f879135807e312ccf054cca637f5d3e61b53edfed5b735f652340cafb5bc64` | en-GB; paragraphs 0/12/13/14, rounds, span, route and schedule |
| [S4] | 10:38:50.761Z | `d768277875335a5327935359f2d83f31384cb2496b0f1d8784f6f3bec43c1699` | en-GB; paragraphs 0/3, halt and no restart |
| [S5] | 10:38:51.715Z | `49344ac2047a759f6b6a697226ec1ed320177cedc1d8d5f4b4f265afb57b83d8` | en-GB; paragraphs 0/10, fifth race and revised sporting count |
| [V] | 10:36:17.631Z | `0d31b9fc1fae8251406230357a14fb0ee2963cce617042e342f7d72af447fe21` | en-GB; paragraph 9, generic 24.358 km route |
| [T] | 10:39:40.875Z | `f91357b706e79421e20caed71d4e031f1cb3c225cc25dbd5855285563390fdb3` | en-GB with German route terms; paragraphs 0/1, dates and marker legend |
| [H] | 10:39:10.893Z | `201314176af8797cc85c22a68291b301edae9f2695d7ff7935ff463aedf8f3ea` | en-GB; paragraphs 0/12, August 1 qualifying and six-hour race |
| [L] | 10:37:57.805Z | `b53667a8b48a81d670f1f30263aa332ea1326283d01cca98ec3c3e5b45e308b8` | en-GB; paragraphs 12-14, Copyright section |
| [D] | 10:36:59.473Z | `5df5674d343fa9a19fd20a3689275658c2e02941a9982dbca4bb7c31a19db5ae` | de; public document and noticeboard anchors |
| [I] | 10:37:14.351Z | `e9a072f5c1fdbcf30baf86edf0e1e370f1c63c13e9f938905207820e26583922` | de; linked A1/A2/A3, TCR and annex document labels |
| [B] | 10:39:16.560Z | `b6f962970f577191a6a8df74e85247323306fb886187f15be0ba3e4e1215957e` | de; eight numbered bulletin links plus attachment |
| [Q] | 10:37:08.902Z | `e905b0bc1717dd9a44e80c18380b6e30b6dab882cc4ba8c99a41d6a054a17583` | HTTP 403 challenge; no sporting evidence extracted |

Each PDF below was a successful ordinary GET with MIME `application/pdf` and `%PDF-` signature. Checksums establish the acquired bytes, **not parsed provisions or language**. No PDF bytes or extracted raw text were saved.

| Ref / linked document | Retrieval time | Bytes | SHA-256 |
| --- | --- | --- | --- |
| [P1: 2026 sporting rules, after Bulletin 5][P1] | 10:39:51.383Z | 1809857 | `462f1172233f5591ef681b38c99563a2ab989c15a7280ab4ac64ae67b2683897` |
| [P8: September 12 timetable V1][P8] | 10:39:51.704Z | 550794 | `65b14e3a97ea722c8c5485a96aed03d481dd5accc96e50cce16d588324b44918` |
| [P9: September 13 timetable V1][P9] | 10:39:51.893Z | 539202 | `6bf89e7fe650ca41a974852fa8df599a637348ddc009bddd61511bfffa296eee` |
| [P8R: Round 8 supplementary regulations][P8R] | 10:39:52.055Z | 415488 | `dd050c5e231070fda3bef9ce31b91e67dc923c4444c675ef5717e2bbfd52ab79` |
| [PT: 2026 test regulations][PT] | 10:39:52.276Z | 795043 | `0161832c0e2b8c30abced1bbfefd7a5a378fccb4f485e46a1e6746a625d42a56` |

## Verification And Boundaries

The factual DOM projection retrieved all eight calendar-linked NLS round pages between 10:36:46Z and 10:36:49Z: each HTTP 200, one five-row two-cell timetable, and the round set 1,2,3,6,7,8,9,10. A later structural check verified nine calendar rows, date/link column positions, the NLS8 h2 selector, seven test-date lines and the two-format legend. No site scripts or invented API calls were required. This verifies extraction feasibility, not a successful complete exact-session import.

Only this Markdown file was created/edited. No runtime, test, fixture, dependency or configuration files were changed; no application tests were run. No commits, issue operations, delegation, canonical approval or publication were performed. Final document validation checks reference definitions, URL syntax, local paths and ASCII content; it does not claim that linked-but-unfetched PDFs or the blocked organiser became accessible.

[C]: https://www.nuerburgring-langstrecken-serie.de/language/de/termine-adac-ravenol-nuerburgring-langstrecken-serie-2026/
[A]: https://www.nuerburgring-langstrecken-serie.de/language/en/2025/09/08/ten-races-in-the-50th-season-of-the-nls/
[R1]: https://www.nuerburgring-langstrecken-serie.de/language/de/2026-71-adac-westfalenfahrt/
[R2]: https://www.nuerburgring-langstrecken-serie.de/language/de/2026-58-adac-barbarossapreis/
[R3]: https://www.nuerburgring-langstrecken-serie.de/language/de/2026-57-adenauer-adac-rundstrecken-trophy/
[R6]: https://www.nuerburgring-langstrecken-serie.de/language/de/2026-1-adac-eifel-trophy/
[R7]: https://www.nuerburgring-langstrecken-serie.de/language/de/2026-kw-6h-adac-ruhr-pokal-rennen/
[R8]: https://www.nuerburgring-langstrecken-serie.de/language/de/2026-65-adac-reinoldus-langstreckenrennen/
[R9]: https://www.nuerburgring-langstrecken-serie.de/language/de/2026-66-adac-acas-cup/
[R10]: https://www.nuerburgring-langstrecken-serie.de/language/de/2026-2-nls-sportwarte-rennen/
[S1]: https://www.nuerburgring-langstrecken-serie.de/language/en/2026/03/14/opening-race-cancelled-for-safety-reasons/
[S2]: https://www.nuerburgring-langstrecken-serie.de/language/en/2026/01/25/strategic-calendar-adjustment-for-the-nls-2026/
[P]: https://www.nuerburgring-langstrecken-serie.de/language/en/2026/04/15/back-to-back-the-first-double-header-of-the-year/
[S4]: https://www.nuerburgring-langstrecken-serie.de/language/en/2026/04/18/race-control-bulletin/
[S5]: https://www.nuerburgring-langstrecken-serie.de/language/en/2026/04/19/five-brands-in-the-top-five-audis-success-and-a-nail-biting-finish-at-the-nurburgring/
[V]: https://www.nuerburgring-langstrecken-serie.de/language/en/the-nurburgring/
[T]: https://www.nuerburgring-langstrecken-serie.de/language/en/vln-test-and-set-up-sessions/
[H]: https://www.nuerburgring-langstrecken-serie.de/language/en/2026/07/30/the-6-hour-adac-ruhr-cup-race-marks-the-start-of-the-crunch-phase/
[L]: https://www.nuerburgring-langstrecken-serie.de/language/en/imprint/
[D]: https://teilnehmer.vln.de/
[I]: https://teilnehmer.vln.de/formulare.php?d=Ausschreibung
[B]: https://teilnehmer.vln.de/formulare.php?d=Bulletins
[Q]: https://www.24h-rennen.de/
[N]: https://www.nuerburgring-langstrecken-serie.de/language/en/news-archive/
[P1]: https://teilnehmer.vln.de/download.php?file=teilnehmer/Ausschreibung/A1%20Ausschreibung%20Teil%201_SPORTLICHES%20REGLEMENT_2026_genehmigt_nachBulletin5.pdf
[P8]: https://teilnehmer.vln.de/download.php?file=onb/2026-09-12/Zeitplan_V1.pdf
[P9]: https://teilnehmer.vln.de/download.php?file=onb/2026-09-13/Zeitplan_V1.pdf
[P8R]: https://teilnehmer.vln.de/download.php?file=onb/2026-09-12/NLS8_Ausschreibung_genehmigt.pdf
[PT]: https://www.nuerburgring-langstrecken-serie.de/wp-content/uploads/2026/01/2026-Ausschreibung-PuE.pdf