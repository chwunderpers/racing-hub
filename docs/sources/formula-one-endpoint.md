# Formula1.com 2026 Public Schedule Payload

Observed **2026-09-10**, through ordinary unauthenticated HTTPS GETs. The user authorized this factual PoC investigation; that authorization is **not a licence or legal clearance**. This note adds verified extraction evidence to [the earlier investigation](formula-one.md); it does not change that historical report or approve publication.

## Result

The [public calendar](https://www.formula1.com/en/racing/2026) provides discoverable meeting links. Each of its **23 numbered meeting pages** exposes structured F1 schedule data in inline React Flight pushes. All 23 were retrieved successfully and each supplied five `meetingSessions` records: **115 sessions**, with **115 distinct `meetingSessionKey` values**. Every captured session has a separate explicit `gmtOffset` and `timezone`. No guessed timezone, flag-based mapping, authenticated API, or browser execution was needed.

The factual projection is [backend/fixtures/f1-2026-source.json](../../backend/fixtures/f1-2026-source.json). It contains all numbered rounds observed on this revision, not an invented expected 24-round season. Two separately labelled testing cards were observed and excluded; their session pages were not acquired. Removed/cancelled meetings and historical revisions are not reconstructed from absence. No FIA data was needed for this capture.

Calendar retrieval: `2026-09-10T08:34:12.2355199+00:00`, HTTP 200, `text/html; charset=utf-8`. Meeting retrievals run from `2026-09-10T08:35:35.2147847+00:00` to `2026-09-10T08:38:36.5248186+00:00`; each fixture record gives its own exact URL and UTC retrieval time. There were 26 GETs: one calendar, 23 meetings, and two repeated meeting GETs to correct terminal encoding of accented names. This is not an atomic season snapshot or a provider revision timestamp.

## Exact Source Paths

1. Calendar DOM selector: `a[href^="/en/racing/2026/"]`. Within each anchor, find a `span` whose trimmed text matches `^ROUND \d+$`; deduplicate by `href` and sort by that round. This excludes testing and avoids repeated featured cards. Do not parse dates or identities from flag titles. A single-month date-text pattern misses Mexico's October/November boundary; the fixture instead uses meeting payload date bounds.
2. Meeting DOM selector: `script` elements, parsed as JavaScript syntax without executing them. Select call expressions whose callee is exactly `self.__next_f.push`, JSON-decode their literal array argument, and concatenate `payload[1]` for `payload[0] === 1`, in document order.
3. Decode the resulting React Flight stream. Records have a hexadecimal ID followed by `:`. `T<hex byte length>,<text>` records must be skipped by **UTF-8 byte count**, not by newline or JavaScript character count. JSON model records are newline-terminated; retain arrays/objects and skip module/hint records. A naive newline split misses model records following text payloads.
4. Walk the decoded model objects and find an object with `pageData.race`. Require exactly one match. The schedule array is **`pageData.race.meetingSessions`**. Do not use global navigation/event-tracker sessions or nested results copies.

Exact observed model path on Australia and 21 other meeting pages:

```text
flight[5][2][3].children[1][0][3].children[3].children[3].children[0][3].children[2][3].pageData.race
```

Las Vegas differs at the child before the final `children[2]`:

```text
flight[5][2][3].children[1][0][3].children[3].children[3].children[1][3].children[2][3].pageData.race
```

These positional paths and record ID `5` are evidence, not stable API contracts. The structural `pageData.race` search succeeded on all 23 pages. The calendar itself had no `script#__NEXT_DATA__`; its decoded models were rendered component trees, not the meeting-page `pageData.race` object. No standalone JSON/ICS endpoint is asserted here.

## Input Shape

The fixture wrapper is ours: `{source_url, retrieved_utc, season, meetings: [{source_url, retrieved_utc, race}]}`. Inside `race`, the selected field names, IDs, names, offsets, zones and states come from the provider payload. It is a small allowlisted export, **not a full HTML/Flight snapshot and not the application's existing publication envelope**.

| Source field under `pageData.race` | Observed type and meaning |
| --- | --- |
| `meetingNumber` | String; numbered round for this calendar revision, not durable identity. |
| `meetingKey` | String; source meeting identifier. Australia is `"1279"`. |
| `meetingName` | String; factual event name without sponsor/presentation fields. |
| `meetingStartDate`, `meetingEndDate` | ISO strings with `Z`, spanning day bounds. They are not F1 session start/end instants. |
| `circuitKey`, `circuitOfficialName` | String ID and circuit name, independent of the meeting's country/slug. |
| `meetingTimezone` | Source timezone identifier; includes the alias `US/Central`. |
| `meetingSessions` | Array; five records on each captured page, including sprint-format weekends. |
| `meetingSessions[].session` | Codes observed: `p1`, `p2`, `p3`, `q`, `r`, `ss`, `s`. Preserve codes; they are not globally unique IDs. |
| `meetingSessions[].meetingSessionKey` | Integer; distinct for every captured session. |
| `meetingSessions[].startTime`, `endTime` | Local ISO clock strings without an offset suffix, e.g. `2026-03-06T12:30:00`. |
| `meetingSessions[].gmtOffset` | Explicit signed offset string, e.g. `+11:00`; do not derive this from flags. |
| `meetingSessions[].timezone` | Per-session source timezone, e.g. `Australia/Melbourne`. |
| `meetingSessions[].state` | Observed strings `completed` and `upcoming`; not a complete documented enumeration. |

PowerShell's JSON round trip normalized zero-millisecond meeting bounds from `.000Z` to `Z`. This is a lexical normalization of supplied date bounds, not an inferred midnight. The session clock strings were retained separately from their supplied offsets and zones. Accented names are represented with JSON Unicode escapes. No results, articles, sponsor descriptions, images, SVG, page configuration or credentials are retained in the fixture.

## Time And Identity Evidence

- [Australia](https://www.formula1.com/en/racing/2026/australia): round `1`, meeting `1279`, circuit `10`, `Albert Park Grand Prix Circuit`. First practice is source local `2026-03-06T12:30:00`, offset `+11:00`, zone `Australia/Melbourne`. Those supplied fields resolve to `2026-03-06T01:30:00Z`; the UTC value is derived, not a separate raw source field.
- [Bahrain](https://www.formula1.com/en/racing/2026/bahrain): round `16`, meeting `1308`, circuit `12`, `Sepang International Circuit`, zone `Asia/Kuala_Lumpur`, offset `+08:00`, October 2-4. This records exactly what this response reported. Do not substitute a Bahrain timezone or circuit based on its name, slug or flag.
- [Barcelona-Catalunya](https://www.formula1.com/en/racing/2026/barcelona-catalunya) is meeting `1287`, circuit `15`, `Circuit de Barcelona-Catalunya`; [Spain](https://www.formula1.com/en/racing/2026/spain) is meeting `1294`, circuit `153`, `Madring`. They remain distinct despite sharing `Europe/Madrid`.
- [Las Vegas](https://www.formula1.com/en/racing/2026/las-vegas): source race starts `2026-11-21T20:00:00`, offset `-08:00`, zone `America/Los_Angeles`. This resolves to November 22 at `04:00:00Z`, demonstrating why UTC calendar dates cannot replace local meeting dates.
- Raw `endTime` is a schedule boundary. Australia's race has `15:00:00` through `17:00:00`; this is not evidence that the actual race lasted two hours. Do not infer real finish times from it.

For a session, append its explicit offset to its offset-free local ISO clock before parsing an instant. Never parse that clock alone in the host timezone. Retain the source zone, including aliases; any canonicalization and date-specific tzdb consistency check is a separate adapter responsibility. Missing or contradictory offsets on future responses must remain unresolved or be flagged, not filled from this fixture.

## Reproduce

Run from the repository root using existing Node modules `jsdom` and `typescript` under `frontend/node_modules`. No installation, Python environment, API key, cookies, special request headers, or application server is required. The extractor below is deliberately limited to the Flight framing observed here; it is not a general React Flight implementation. Unexpected schema/framing should fail acquisition rather than silently publish partial data.

This JavaScript reads one HTML response on stdin and takes `calendar` or `race` as its first argument:

```javascript
const fs = require('node:fs');
const { JSDOM } = require(require.resolve('jsdom', { paths: ['./frontend'] }));
const ts = require(require.resolve('typescript', { paths: ['./frontend'] }));
const document = new JSDOM(fs.readFileSync(0, 'utf8')).window.document;
const emit = value => console.log(JSON.stringify(value).replace(
  /[\u007f-\uffff]/g,
  character => '\\u' + character.charCodeAt(0).toString(16).padStart(4, '0')
));

if (process.argv[1] === 'calendar') {
  const meetings = new Map();
  for (const anchor of document.querySelectorAll('a[href^="/en/racing/2026/"]')) {
    const label = [...anchor.querySelectorAll('span')]
      .map(span => span.textContent.trim()).find(text => /^ROUND \d+$/.test(text));
    if (label) meetings.set(anchor.getAttribute('href'), Number(label.slice(6)));
  }
  emit([...meetings].map(([href, round]) => ({ href, round }))
    .sort((left, right) => left.round - right.round));
} else {
  let flight = '';
  for (const script of document.querySelectorAll('script')) {
    const ast = ts.createSourceFile('inline.js', script.textContent,
      ts.ScriptTarget.Latest, true, ts.ScriptKind.JS);
    function visit(node) {
      if (ts.isCallExpression(node) && node.expression.getText(ast) === 'self.__next_f.push') {
        const payload = JSON.parse(node.arguments[0].getText(ast));
        if (payload[0] === 1) flight += payload[1];
      }
      ts.forEachChild(node, visit);
    }
    visit(ast);
  }
  const bytes = Buffer.from(flight, 'utf8');
  const records = new Map();
  let offset = 0;
  while (offset < bytes.length) {
    const colon = bytes.indexOf(58, offset);
    if (colon < 0) throw Error('Missing Flight record separator');
    const id = bytes.subarray(offset, colon).toString();
    const start = colon + 1;
    if (bytes[start] === 84) {
      const comma = bytes.indexOf(44, start);
      if (comma < 0) throw Error('Missing text length separator');
      const length = Number.parseInt(bytes.subarray(start + 1, comma).toString(), 16);
      if (!Number.isFinite(length) || comma + 1 + length > bytes.length) {
        throw Error('Invalid Flight text length');
      }
      offset = comma + 1 + length;
      continue;
    }
    const newline = bytes.indexOf(10, start);
    const stop = newline < 0 ? bytes.length : newline;
    const raw = bytes.subarray(start, stop).toString();
    if (raw.startsWith('{') || raw.startsWith('[')) records.set(id, JSON.parse(raw));
    offset = stop + 1;
  }
  const matches = [];
  function walk(value, path) {
    if (!value || typeof value !== 'object') return;
    if (value.pageData?.race) matches.push({ raw_path: path + '.pageData.race', race: value.pageData.race });
    for (const [key, child] of Object.entries(value)) walk(child, path + '.' + key);
  }
  for (const [id, value] of records) walk(value, 'flight[' + id + ']');
  if (matches.length !== 1) throw Error('Expected exactly one pageData.race');
  const { raw_path, race } = matches[0];
  const pick = (value, fields) => Object.fromEntries(fields.map(field => {
    if (!Object.hasOwn(value, field)) throw Error('Missing field: ' + field);
    return [field, value[field]];
  }));
  const selected = pick(race, ['meetingNumber', 'meetingKey', 'meetingName',
    'meetingStartDate', 'meetingEndDate', 'circuitKey', 'circuitOfficialName', 'meetingTimezone']);
  selected.meetingSessions = race.meetingSessions.map(session => pick(session,
    ['session', 'meetingSessionKey', 'startTime', 'endTime', 'gmtOffset', 'timezone', 'state']));
  emit({ raw_path, race: selected });
}
```

These PowerShell commands load that JavaScript directly from this note, then reproduce calendar discovery and one meeting extraction in memory. Repeat the last GET/extraction for each discovered `href` to reproduce season coverage. The script prints only the factual projection, not the original HTML or other page payloads.

```powershell
$note = Get-Content 'docs/sources/formula-one-endpoint.md' -Raw
$extractor = [regex]::Match($note, '(?s)```javascript\r?\n(.*?)\r?\n```').Groups[1].Value
$calendarResponse = Invoke-WebRequest 'https://www.formula1.com/en/racing/2026'
$calendarRetrievedUtc = [DateTimeOffset]::UtcNow.ToString('o')
$calendarJson = $calendarResponse.Content | node -e $extractor calendar
if ($LASTEXITCODE -ne 0) { throw 'Calendar extraction failed' }
$meetings = $calendarJson | ConvertFrom-Json
$meetingUrl = 'https://www.formula1.com' + $meetings[0].href
$meetingResponse = Invoke-WebRequest $meetingUrl
$meetingRetrievedUtc = [DateTimeOffset]::UtcNow.ToString('o')
$meetingResponse.Content | node -e $extractor race
if ($LASTEXITCODE -ne 0) { throw 'Meeting extraction failed' }
```

Retain the JSON text before `ConvertFrom-Json` when exact timestamp spelling is important: PowerShell may coerce ISO strings to dates. ASCII-escaped JSON output avoids the Windows native-stdout encoding mismatch encountered for Mexico and Brazil. Neither technique changes a timezone or translates an event name.

## Verification And Unknowns

The fixture was compared field-for-field with the in-memory allowlisted acquisition projection after the disclosed date normalization: 23 meetings, 115 sessions, 115 unique session keys, sequential rounds 1-23, and parseable explicit start/end offsets. This validates capture fidelity and structure, not independent truth of the schedule or a provider SLA. No application tests were run, no application/test files were edited, no environment was changed, and no commit was made.

Remaining unknowns: future schema stability, provider status vocabulary beyond the two observed states, durable ID guarantees, historical cancellation coverage, testing/support-session coverage, and whether future revisions supply missing or conflicting timezone data. No complete-season licence or publication approval is established. The payload is sufficient practical input for a reviewed PoC adapter, but not a promise that the observed schedule will remain unchanged.