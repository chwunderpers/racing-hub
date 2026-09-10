# GT World Challenge Europe 2026 Source Research

Research for [Issue 6](https://github.com/chwunderpers/racing-hub/issues/6), observed 2026-09-10. Scope: factual local PoC acquisition through ordinary public GETs only. This is not legal clearance, implementation, acceptance, or publication approval.

## Result And Scope

The [official calendar](https://www.gt-world-challenge-europe.com/calendar) and all **12 discovered meeting pages** were retrieved successfully by unauthenticated GET. The inventory is **10 numbered championship Rounds (five Endurance Cup, five Sprint Cup), plus two distinct test/prologue Meetings with no round number**. Both past and upcoming calendar sections are required. The meetings represent ten named circuit venues; a complete numeric GT circuit-ID registry was **not** verified.

The meeting pages expose ordinary JSON-LD and HTML tables: **104 timetable rows**, of which **99 have nonempty names** and five Barcelona rows have blank names. All 104 rows have local/GMT clock cells. This is **not 104 verified sporting Sessions**: the tables also contain pit walks, a parade, combined classifications and race checkpoints. No session end times, IANA timezone fields or stable session IDs were established from these tables. PDFs are linked on all 12 pages, but their contents were not acquired or parsed in this investigation.

Recommended factual extraction: **calendar DOM for inclusion and Round/Test Day classification; meeting JSON-LD for date bounds, cup and place evidence; dated timetable DOM for lossless start-clock observations**. No React Flight decoding, page-script execution, authenticated endpoint, browser challenge bypass or invented API route is needed. Existing `jsdom` and JSON parsing were exercised; the same selectors and `json.loads` are suitable for a BeautifulSoup implementation, but no Python adapter was written or run.

The initial complete meeting projection finished on 2026-09-10 between `09:42:15Z` and `09:42:33Z`; Monza reused an earlier response, so its projection timestamp is not a new retrieval time. The documented extractor then retrieved all twelve meeting pages afresh between `09:47:13Z` and `09:47:31Z`. These are local observation times, not a provider revision or atomic season snapshot. The calendar and meeting responses were HTTP 200 HTML. Only this Markdown research artifact is intended for retention; no HTML, PDF, image, JSON fixture, runtime or test artifact is added to the repository.

Method limitation: an early inspection printed markup snippets, and the tool automatically spilled large output to its session cache outside the repository. No raw-response file was deliberately saved, but this means strict zero markup retention in tool logs cannot be claimed. Subsequent probes emitted bounded factual projections only; no page JavaScript was executed.

## Authority And Rights

[SRO's activities directory](https://www.sro-motorsports.com/activities) links this exact Europe site as a GT3 series. Its [corporate homepage](https://www.sro-motorsports.com/) also links Europe meeting `253`, Zandvoort, with September 18-20, 2026 dates. The Europe site's [SRO page](https://www.gt-world-challenge-europe.com/about/sro-motorsports-group) identifies the organising group. The [privacy policy](https://www.gt-world-challenge-europe.com/privacy-policy) names SRO Motorsports Europe Limited, company number `03013210`, and explicitly includes this domain in Appendix 1. These establish first-party authority, not independent corroboration by unrelated publishers.

The footer states SRO Motorsports Group, All Rights Reserved. The privacy policy is about personal data, not a schedule-reuse licence. No open-data licence, redistribution permission, scraping agreement, completeness warranty or API stability commitment was established. Public accessibility and the user's factual local PoC authorization are **not legal clearance**. Copyright/database rights, terms, attribution, automated-access policy, retention and downstream publication need separate review before broader use. Avoid retaining page prose, photographs, circuit graphics, results, personal data or raw page payloads. A future 401/403/429 or challenge is a stop condition, not permission to change identity, borrow credentials or evade controls.

## Complete Meeting Inventory

Dates below are the supplied date-only `Event.startDate` and `Event.endDate`, inclusive as displayed on the website, not UTC intervals. Calendar labels determine Round membership. Each event-name link is its exact source page and evidence for that row. Source meeting IDs come from those URLs, not array position or date arithmetic. All rows have a linked timetable PDF; the last column records **HTML availability**, not PDF validation or published canonical sessions.

| Meeting ID | Event / source | Start date | End date | Type / cup | Round | Circuit evidence / source identifier availability | HTML timing availability |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 244 | [Official Test Days - Prologue](https://www.gt-world-challenge-europe.com/event/244/official-test-days) | 2026-04-08 | 2026-04-09 | Test Day / Prologue; cup unspecified | null | Paul Ricard; official link `circuitpaulricard.com`; asset `track_10.jpg` | 3 named local/GMT start rows |
| 246 | [Circuit Paul Ricard](https://www.gt-world-challenge-europe.com/event/246/circuit-paul-ricard) | 2026-04-10 | 2026-04-12 | Championship / Endurance | 1 | Same Paul Ricard place, address and website as 244; asset `track_10.jpg` | 7 named local/GMT start rows |
| 247 | [Brands Hatch](https://www.gt-world-challenge-europe.com/event/247/brands-hatch) | 2026-05-02 | 2026-05-03 | Championship / Sprint | 2 | Brands Hatch; official link `brandshatch.co.uk`; asset `track_12.png` | 7 named local/GMT rows, including Pit Walk |
| 245 | [CrowdStrike 24 Hours of Spa - Prologue](https://www.gt-world-challenge-europe.com/event/245/crowdstrike-24-hours-of-spa--test-days) | 2026-05-19 | 2026-05-20 | Test Day / Prologue; Endurance affiliation supplied | null | Spa-Francorchamps; official link `spa-francorchamps.be`; asset `track_35.png` | 4 named local/GMT start rows |
| 248 | [Monza](https://www.gt-world-challenge-europe.com/event/248/monza) | 2026-05-28 | 2026-05-31 | Championship / Endurance | 3 | Autodromo Nazionale; official link `monzanet.it`; asset `track-monza.png`; no numeric circuit key verified | 9 named local/GMT rows, including Qualifying Combined |
| 249 | [CrowdStrike 24 Hours of Spa](https://www.gt-world-challenge-europe.com/event/249/crowdstrike-24-hours-of-spa) | 2026-06-23 | 2026-06-28 | Championship / Endurance | 4 | Same Spa place, address and website as 245; asset `track_35.png` | 17 named local/GMT rows, including parade, pit walks and combined classification |
| 250 | [Misano](https://www.gt-world-challenge-europe.com/event/250/misano) | 2026-07-16 | 2026-07-19 | Championship / Sprint | 5 | Misano World Circuit; official link `misanocircuit.com`; asset `track-misano.png`; no numeric circuit key verified | 10 named local/GMT rows |
| 251 | [Magny-Cours](https://www.gt-world-challenge-europe.com/event/251/magny-cours) | 2026-07-30 | 2026-08-02 | Championship / Sprint | 6 | Circuit de Nevers Magny-Cours; no official circuit website link or numeric circuit key found in inspected fields | 11 named local/GMT rows, including combined classifications |
| 252 | [Nurburgring](https://www.gt-world-challenge-europe.com/event/252/n%C3%BCrburgring) | 2026-08-28 | 2026-08-30 | Championship / Endurance | 7 | Place name missing in JSON-LD; Boulevard 1, 53520; official link `nuerburgring.de`; asset `track_27.jpg`; layout identity unresolved | 12 named local/GMT rows, including three race checkpoints |
| 253 | [Zandvoort](https://www.gt-world-challenge-europe.com/event/253/zandvoort) | 2026-09-18 | 2026-09-20 | Championship / Sprint | 8 | Circuit Park Zandvoort; official link `circuitzandvoort.nl/`; assets `track_9.jpg`, calendar `outline_9.svg` | 10 named local/GMT rows, including combined classifications |
| 254 | [Barcelona](https://www.gt-world-challenge-europe.com/event/254/barcelona) | 2026-10-02 | 2026-10-04 | Championship / Sprint | 9 | Circuit de Barcelona - Catalunya; official link `circuitcat.com`; calendar asset `outline_21.svg` | 9 local/GMT rows: 4 named, **5 unnamed** |
| 255 | [Portimao](https://www.gt-world-challenge-europe.com/event/255/portimao) | 2026-10-16 | 2026-10-18 | Championship / Endurance | 10 | Portimao Circuit; malformed official-link host `www.www.autodromodoalgarve.com`; no numeric circuit key verified | 5 named local/GMT start rows; revised race on Saturday |

The ASCII display spelling above does not replace raw provider strings: event 252's JSON-LD name is `N&uuml;rburgring `, with a trailing space. Calendar DOM text decodes the umlaut. Retain the raw string and explicitly record any entity-decoding/display normalization.

## Exact Acquisition Surface

| Endpoint / selector | Observed behavior and fields | Limits |
| --- | --- | --- |
| `GET https://www.gt-world-challenge-europe.com/calendar` | Server-rendered HTML; heading identifies 2026; 12 distinct `/event/{id}/{slug}` links across `.past-events__list-item` and `.calendar__list-item` | Current-season URL, not a versioned API. Require season heading and meeting years; do not assume it always means 2026. |
| Calendar card `.past-events__piped-list-span`, `.calendar__race-text` | Explicit `Test Day` or `Round N`; upcoming cup text also present | Never derive round from a prologue's JSON-LD description, event ID or ordering. |
| Discovered `GET /event/{id}/{slug}` | All 12 return parseable HTML with one JSON-LD `Event` plus separate `Organization` | Numeric meeting key is URL-scoped; stable across these links, but long-term provider durability is not documented. Preserve the complete discovered URL, including encoded Unicode. |
| `script[type="application/ld+json"]`, object `@type == "Event"` | `name`, `startDate`, `endDate`, `performer.name`, `location.name`, `location.address`, `description` | Plain JSON. No Event/Place `@id` or explicit `circuit_id` was verified in these objects. Descriptions contain known classification errors. |
| `table.timetable__table` | `caption.timetable__caption` supplies weekday/day/month; `thead th` is `Session`, `Local Time`, `GMT`; `tbody tr td` supplies three cells per row | Year must be derived from the verified meeting year and validated against bounds. No row IDs, row links, end clocks or timezone fields were found in inspected rows. |
| Track Information `Visit Website` and `Google Map` anchors | Source-published external circuit URL and address/location evidence | These are identity evidence, not an SRO numeric circuit registry. Google links were read as source attributes, not used as independent third-party evidence. |
| `GET /feed/get_event_calendar?meeting_id=253` | HTTP 200; `text/calendar; charset=UTF-8`; attachment `event_zandvoort.ics`; one VEVENT, `UID:GTWCEU-253` | Exact link discovered on calendar. Only this feed was GET-tested; no extrapolated UID claims for other meetings. `fetch_webpage` could not extract meaningful text, but direct GET worked. |
| Event Timetable PDF links | All 12 pages expose a URL, often with draft/version suffix | Link availability only. No PDF parser or contents verified, no PDF retained. Do not assume filename version order settles all conflicts. |

Observed Zandvoort feed facts: `DTSTART;VALUE=DATE:20260918`, `DTEND;VALUE=DATE:20260920`, `SUMMARY:GTWC RD8`, `DESCRIPTION:Zandvoort Round 8`, `LOCATION:Netherlands\, Zandvoort`, `STATUS:CONFIRMED`, and URL back to event `253`. `PRODID` unexpectedly names `gt-world-challenge-america.com`; retain that inconsistency instead of reclassifying this as an American event. `DTSTAMP` and `LAST-MODIFIED` both reported `20260910T104243Z`; they are not verified editorial change timestamps and should not drive schedule freshness. No supplied session timezone or session-level timestamps exist in this feed.

[RFC 5545 section 3.6.1](https://www.rfc-editor.org/rfc/rfc5545#section-3.6.1) specifies non-inclusive VEVENT `DTEND`. A conforming consumer therefore ends this feed before September 20, while the calendar and JSON-LD include September 20. Preserve both source values, prefer the explicit website date span for a proposed meeting envelope, and flag the discrepancy. Do not silently alter raw ICS or manufacture midnight sessions.

## Explicit Circuit Crosswalk Evidence

The existing [F1 factual fixture](../../backend/fixtures/f1-2026-source.json) supplies the F1 keys/names below; [the F1 extraction report](formula-one-endpoint.md) explains their origin. The existing [canonical-ID expression](../../backend/app/formula_one.py#L68) uses `f1-circuit-{circuitKey}` for these circuits. These are existing application identities, **not IDs published by SRO**.

The following is a **documented, evidence-backed proposed lookup**, not a persisted mapping or approval. Runtime use should be an explicit reviewed table keyed by source family plus observed circuit URL alias (or by meeting ID plus place-field provenance where no stable circuit key exists). Do not perform label equality/fuzzy joins at ingestion time. The associated meeting IDs make the intended source records explicit even where provider circuit IDs are absent.

| GT source records / exact published circuit URL alias | Existing F1 identity and source evidence | Physical identity evidence and remaining boundary |
| --- | --- | --- |
| `248`; `https://www.monzanet.it` | **`f1-circuit-39`**; F1 meeting `1293`, `Autodromo Nazionale Monza`; [F1 Italy](https://www.formula1.com/en/racing/2026/italy) | GT Place `Autodromo Nazionale, Italy`, Via Vedano n&deg; 5, Monza, 20900, Parco di Monza. The linked [circuit operator](https://www.monzanet.it/) identifies itself as Autodromo Nazionale Monza and links its Formula 1 event. Name + address + operator corroborate the mapping, not the event slug alone. |
| `245`, `249`; `https://www.spa-francorchamps.be` | **`f1-circuit-7`**; F1 meeting `1290`, `Circuit de Spa-Francorchamps`; [F1 Belgium](https://www.formula1.com/en/racing/2026/belgium) | Both GT pages supply identical Place/address and website: Spa-Francorchamps, Route du Circuit 55, Stavelot, 4970. The [operator site](https://www.spa-francorchamps.be/) independently supplies Route du Circuit 55, B-4970 Francorchamps. Preserve locality-label variation; keep the prologue and race as separate Meetings at one Circuit. |
| `254`; `https://www.circuitcat.com` | **`f1-circuit-15`**; F1 meeting `1287`, `Circuit de Barcelona-Catalunya`; [F1 Barcelona-Catalunya](https://www.formula1.com/en/racing/2026/barcelona-catalunya) | GT Place `Circuit de Barcelona - Catalunya, Spain`, Camino Mas Moreneta, Montmel&oacute;, 08160, Barcelona. The [operator](https://www.circuitcat.com/) identifies Circuit de Barcelona-Catalunya in Montmelo. The spaces around the hyphen are a label variant, not another circuit. Do **not** map to F1 `153` / Madring merely because both are Spanish. |
| `253`; `https://www.circuitzandvoort.nl/` | **`f1-circuit-55`**; F1 meeting `1292`, `Circuit Zandvoort`; [F1 Netherlands](https://www.formula1.com/en/racing/2026/netherlands) | GT Place `Circuit Park Zandvoort, Netherlands`, Burgemeester van Alphenstraat 108, KP Zandvoort, 2041, and its official website link support the venue mapping. The linked operator itself was not separately retrieved in this investigation, so corroboration is narrower than the three mappings above. |

Circuit asset references are recorded exactly, but **`track_35.png` does not establish a contracted `circuit_id=35` field**. The same caution applies to 10, 12, 27, 9 and 21 in the other filenames. Never equate these numbers with F1 keys: GT's observed Zandvoort asset suffix `9` does not mean F1 circuit `9` (Circuit of The Americas). Monza and Misano use descriptive filenames; Magny-Cours and Portimao have no comparable circuit asset in the inspected fields. A complete numeric circuit-ID mapping remains a blocker if the future adapter contract specifically requires provider numeric IDs.

For nonshared circuits, do not allocate new canonical IDs in this research. Paul Ricard's two Meetings share the same explicit Place, address and official website; maintain that evidence for later identity review. Magny-Cours lacks a usable explicit circuit URL in this capture. Portimao's malformed URL is not silently repaired or fetched. Nurburgring's site-level link/address does not settle GP circuit versus Nordschleife/layout identity; do not merge it with a future NLS circuit on name or venue alone.

## Session Precision And Conflicts

| Source field / records | Observations | Proposed handling |
| --- | --- | --- |
| Calendar classification versus JSON-LD `description`, 244 | Calendar `Test Day`; description `, Round 1, Official Test Days - Prologue, France`; `performer.name` is empty | Non-round Test/Prologue Meeting, `round=null`; preserve conflicting description and missing cup with their field paths. |
| Calendar classification versus JSON-LD `description`, 245 | Calendar `Test Day`; description says `Round 3` and supplies Endurance Cup | Non-round Test/Prologue Meeting, `round=null`; cup affiliation does not imply championship membership. Monza is the calendar's actual Round 3. |
| JSON-LD names/addresses | 252: `N&uuml;rburgring `, Place `, Germany`; 250: `Misano World Circuit, Italy, Italy`; 254: `Montmel&oacute;`; 248: `n&deg;` | Retain raw field values. Decode entities/trim only into separately marked normalized display fields. Do not turn missing Place names into inferred identifiers. |
| Barcelona timetable, 254 | Five rows have an empty first cell but valid clock pairs; only FP1, FP2, Race 1 and Race 2 are named | Retain five unresolved row observations. Do not assign practice/qualifying labels from order or another meeting's format. |
| Barcelona timetable caption versus Meeting bounds, 254 | `Thursday, 1 October` contains one unnamed row at `13:30 / 11:30 GMT`; JSON-LD starts `2026-10-02` | **Review required:** the row falls outside the supplied Meeting span. Keep both facts; do not drop the row or silently expand the Meeting to October 1. |
| Portimao timetable caption versus Meeting bounds, 255 | `Thursday, 15 October` contains Official Paid Test Session 1 at `11:50 / 10:50 GMT` and Bronze Test at `17:40 / 16:40 GMT`; JSON-LD starts `2026-10-16` | **Review required:** two rows precede the supplied Meeting span. Preserve the test observations and the original bounds separately. |
| Aggregate/non-driving timetable entries | Brands Hatch: Pit Walk. Spa: Spa Parade, three Pit Walk rows, Qualifying Combined. Nurburgring: `Main Race after 0.5 h`, `Main Race after 1h 30`, `Main Race after 2h 30`. Other meetings also have combined qualifying rows | Do not publish each row as a distinct driving Session. Preserve raw observations; classify or exclude under an explicit reviewed policy with reasons. Never treat checkpoints as new races. |
| Portimao event bounds versus race date | Meeting remains October 16-18. [July 31 organiser revision](https://www.gt-world-challenge-europe.com/news/3284/season-closing-race-at-portimao-to-run-on-saturday-evening) moves race from Sunday October 18 to Saturday October 17, 17:00; qualifying Friday 17:55 | Distinct fields, not contradictory meeting bounds. HTML clocks are Main Race `17:00 / 16:00 GMT`, Qualifying `17:55 / 16:55 GMT`. Keep article and timetable evidence; do not truncate the Meeting to race day or infer a finish time from the stated three-hour format. |
| Meeting span versus popular race-weekend shorthand | Monza starts May 28, Spa June 23, Misano July 16, Magny-Cours July 30 in this capture | Preserve supplied bounds. Do not replace them with a Friday-Sunday pattern or dates from an older season announcement. |
| Timetable clocks versus complete instants | Example Monza: Sunday May 31 Main Race `15:30` local, `13:30` GMT. Captions omit year. All 104 clock pairs are minute precision | Derive the caption year only from the verified Meeting interval and check weekday/bounds. Keep local/GMT clocks separately. UTC calendar-date rollover and an IANA zone are not explicitly supplied; a reviewed conversion rule is required before instant publication. No borrowing F1 offsets for different GT dates. |
| Session identity/end times | No ID, link or end-time field on inspected timetable rows; no verified one-to-one results join to every timetable row | DOM positions are evidence locators, not durable provider IDs. Session identity reconciliation and end-time policy remain unresolved. Do not invent IDs, durations or end instants. |
| Zandvoort ICS `DTEND`, `PRODID`, timestamps | End-date semantics conflict with displayed last day; producer says America; timestamps not established as editorial revisions | Keep field-level discrepancies. Use calendar/meeting source family, not PRODID, for classification. Do not let generated timestamps prove freshness or approval. |

For every proposed normalized field retain source URL, retrieval UTC, selector/JSON path, raw factual value, normalization rule and competing observations. Source precedence is **field-specific**, never a blanket newest-page-wins rule. Material identity, classification, date or timing disagreements require review; resolving one label variant must not erase the alternative assertion. Publication remains independently gated.

## Reproducible Extraction

This is a research-only, one-response projection using existing `frontend/node_modules/jsdom`. It reads HTML on stdin and emits allowlisted JSON. JSDOM's default configuration does not execute scripts or load subresources. The JSON-LD is parsed as data; other inline scripts are ignored. An AST is unnecessary here. In BeautifulSoup, use the same CSS selectors and parse the selected script strings with the JSON parser, not `eval`.

```javascript
const fs = require('node:fs');
const { JSDOM } = require(require.resolve('jsdom', { paths: ['./frontend'] }));
const document = new JSDOM(fs.readFileSync(0, 'utf8')).window.document;
const text = node => node?.textContent.replace(/\s+/g, ' ').trim() ?? '';
const origin = 'https://www.gt-world-challenge-europe.com';
const emit = value => console.log(JSON.stringify(value).replace(
	/[\u007f-\uffff]/g,
	character => '\\u' + character.charCodeAt(0).toString(16).padStart(4, '0')
));

if (process.argv[1] === 'calendar') {
	if (![...document.querySelectorAll('h1,h2')].some(node => /^2026 Calendar/.test(text(node)))) {
		throw Error('Unexpected calendar season');
	}
	const meetings = new Map();
	for (const card of document.querySelectorAll('.past-events__list-item,.calendar__list-item')) {
		const links = [...card.querySelectorAll('a[href^="/event/"]')];
		const urls = [...new Set(links.map(node => new URL(node.getAttribute('href'), origin).href))];
		if (urls.length !== 1) throw Error('Ambiguous meeting card');
		const sourceUrl = urls[0];
		const match = new URL(sourceUrl).pathname.match(/^\/event\/(\d+)\//);
		if (!match) throw Error('Missing source meeting ID');
		const labels = [...card.querySelectorAll('.past-events__piped-list-span,.calendar__race-text')]
			.map(text).filter(value => /^(Test Day|Round \d+)$/.test(value));
		if (labels.length !== 1) throw Error('Ambiguous meeting classification');
		const label = labels[0];
		const meeting = {
			source_url: sourceUrl, meeting_id: match[1], classification_raw: label,
			round: label === 'Test Day' ? null : Number(label.slice(6)),
			card_text: text(card),
			feed_urls: [...card.querySelectorAll('a[href*="get_event_calendar"]')]
				.map(node => new URL(node.getAttribute('href'), origin).href)
		};
		if (meetings.has(match[1])) throw Error('Duplicate source meeting ID');
		meetings.set(match[1], meeting);
	}
	if (!meetings.size) throw Error('Empty inventory');
	emit([...meetings.values()]);
} else if (process.argv[1] === 'event') {
	const events = [...document.querySelectorAll('script[type="application/ld+json"]')]
		.map(node => JSON.parse(node.textContent)).filter(value => value['@type'] === 'Event');
	if (events.length !== 1) throw Error('Expected one Event object');
	const event = events[0];
	for (const field of ['name', 'startDate', 'endDate', 'description']) {
		if (typeof event[field] !== 'string') throw Error('Missing field: ' + field);
	}
	if (!/^2026-\d{2}-\d{2}$/.test(event.startDate) || !/^2026-\d{2}-\d{2}$/.test(event.endDate)) {
		throw Error('Unexpected date shape or season');
	}
	const groups = [...document.querySelectorAll('table.timetable__table')].map(table => {
		const caption = text(table.querySelector('caption.timetable__caption'));
		const headers = [...table.querySelectorAll('thead th')].map(text);
		if (!caption || headers.join('|') !== 'Session|Local Time|GMT') throw Error('Unexpected timetable');
		const rows = [...table.querySelectorAll('tbody tr')].map(row => {
			const cells = [...row.querySelectorAll('td')].map(text);
			if (cells.length !== 3) throw Error('Unexpected timetable row');
			return { name_raw: cells[0], local_clock_raw: cells[1], gmt_clock_raw: cells[2] };
		});
		return { caption_raw: caption, rows };
	});
	const anchors = [...document.querySelectorAll('a[href]')];
	emit({ name_raw: event.name, start_date: event.startDate, end_date: event.endDate,
		cup_raw: event.performer?.name ?? null, place_raw: event.location ?? null,
		description_raw: event.description, timetable_groups: groups,
		circuit_website_urls: anchors.filter(node => /^Visit Website$/i.test(text(node)))
			.map(node => node.getAttribute('href')),
		timetable_pdf_urls: [...new Set(anchors.filter(node => /Event Timetable/i.test(text(node)))
			.map(node => new URL(node.getAttribute('href'), origin).href))]
	});
} else {
	throw Error('Expected calendar or event mode');
}
```

From the repository root, these commands load that code from this document without creating another file. HTTP responses stay in memory; do not print `.Content` or use `-OutFile`. Capture retrieval time immediately after each GET. Keep output JSON text unchanged before a PowerShell round trip if lexical date fidelity matters.

```powershell
$note = Get-Content 'docs/sources/gt-world-challenge-europe.md' -Raw
$extractor = [regex]::Match($note, '(?s)```javascript\r?\n(.*?)\r?\n```').Groups[1].Value
$calendar = Invoke-WebRequest 'https://www.gt-world-challenge-europe.com/calendar'
$calendarUtc = [DateTimeOffset]::UtcNow.ToString('o')
$inventoryJson = $calendar.Content | node -e $extractor calendar
if ($LASTEXITCODE -ne 0) { throw 'Calendar projection failed' }
$inventory = $inventoryJson | ConvertFrom-Json
foreach ($meeting in $inventory) {
		$response = Invoke-WebRequest $meeting.source_url
		$retrievedUtc = [DateTimeOffset]::UtcNow.ToString('o')
		$projectionJson = $response.Content | node -e $extractor event
		if ($LASTEXITCODE -ne 0) { throw "Projection failed: $($meeting.source_url)" }
		[pscustomobject]@{ source_url=$meeting.source_url; retrieved_utc=$retrievedUtc; projection=$projectionJson }
		$response = $null
}
$calendar = $null
```

This deliberately preserves missing names and raw clocks instead of fabricating normalized Sessions. It is not a production adapter, date parser, session-ID allocator, circuit resolver or publication envelope. The cardinalities in this report are snapshot validation expectations, not constants to force onto a future calendar. On a changed schema, fail explicitly and review the change rather than skipping cards or silently publishing a partial season.

### Verification Findings

The documented extractor ran against the observed calendar and all twelve freshly retrieved meeting pages. It found twelve distinct meeting IDs, Rounds 1-10 and two null-round tests, one Event object per page, the per-meeting row counts above, one timetable PDF link per page and the stated circuit website links (none for Magny-Cours). All 104 local/GMT pairs have valid `HH:mm` syntax; five names are blank, all at Barcelona. Caption weekday/date checks use the supplied 2026 season and do not change source precision.

The stricter check requiring all captions to lie within JSON-LD bounds **failed**. Its first failure was Barcelona `2026-10-01`; inspection also found Portimao `2026-10-15`. These are documented source-quality failures, not successful schedule-validation results. Extraction feasibility is established; unconditional exact-session publication is not.

## Failure Policy And Remaining Blockers

1. GET only linked public resources. Reject unexpected hosts/redirects, challenge/login pages, non-200 responses, unexpected content types, ambiguous Event objects, season mismatches and changed selectors. Respect throttling; stop on access controls. Never execute downloaded scripts or inspect authenticated team/press areas.
2. Validate exact discovered meeting-ID set and classification coverage before proposing an update. A missing event is not evidence of cancellation. Keep the last accepted snapshot; record an acquisition failure or review-required change instead of replacing it with partial data.
3. Test/prologue Meetings remain distinct, `round=null`. Paid tests inside championship meetings are timetable activities, not additional season-level Meetings without separate source evidence. Do not promote JSON-LD's erroneous prologue Round descriptions.
4. Circuit lookup requires a versioned, explicit evidence-backed crosswalk. Unknown or conflicting mappings remain unresolved; never allocate a shared identity by label, country, image suffix or timezone. Layout ambiguity is a separate blocker from knowing the venue.
5. Retain day/minute precision. Missing names, UTC-date rollover ambiguity, unknown timezone, missing session identity and end times cannot be filled from defaults, neighbouring rows, F1 data or race duration. A complete exact-session adapter remains blocked pending reviewed resolution or a richer verified source.
6. PDF parsing, provider numeric circuit/session IDs, historic cancellation coverage, semantic classification of all timetable rows, publication rights and final canonical mapping acceptance are **not established**. Date-level season research is viable; Issue 6's adapter, UI, SPARQL tests and publication acceptance criteria remain unimplemented by this task.

No commits, issue comments/label changes, data approval or publication were performed. Application and test files were not edited, and application tests were not run; verification is limited to public-source extraction and the research artifact.