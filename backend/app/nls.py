import json
import hashlib
import re
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.publication import FieldAssertion, ScheduledEnvelope, ScheduledMeeting, SeasonCandidateEnvelope


ORIGIN = "https://www.nuerburgring-langstrecken-serie.de"
COMPETITION = "nls"
CALENDAR = ORIGIN + "/language/de/termine-adac-ravenol-nuerburgring-langstrecken-serie-2026/"
PREVIEW = ORIGIN + "/language/en/2026/04/15/back-to-back-the-first-double-header-of-the-year/"
TESTS = ORIGIN + "/language/en/vln-test-and-set-up-sessions/"
GROUPING = ORIGIN + "/language/en/2025/09/08/ten-races-in-the-50th-season-of-the-nls/"
VENUE = ORIGIN + "/language/en/the-nurburgring/"
RULE = "nls-2026-v1: explicit source URL and Round identity mapping; no label joins; docs/sources/nls.md"
AUTHORIZATION = "Chris, 2026-09-10 conversation: standing PoC approval for ingestion, translations, identity mappings and publication; not a claim of individual source review"
FIXTURE = Path(__file__).parents[1] / "fixtures/nls-2026-source.json"
STATUS = {
    1: ("2026/03/14/opening-race-cancelled-for-safety-reasons/", "52a66c738b36b079109144c70d4921d67becb593cbb0ee3270ed660e5cd64759", "Cancelled for safety reasons; planned timetable retained", "2026-03-14T10:45"),
    2: ("2026/01/25/strategic-calendar-adjustment-for-the-nls-2026/", "201b94011346dcb246cc94142e7c92bc2abe60d656cc4805b9f592d1dd5cbb34", "Round 2 moved one week earlier to March 21; same Round identity, not a replacement", None),
    4: ("2026/04/18/race-control-bulletin/", "d768277875335a5327935359f2d83f31384cb2496b0f1d8784f6f3bec43c1699", "Race started, halted and not resumed that evening; abandoned, not pre-start cancelled", "2026-04-18"),
}


def reviewed_source() -> dict:
    return json.loads(FIXTURE.read_text("utf-8"))


def adapt_season(source: dict) -> SeasonCandidateEnvelope:
    approved = reviewed_source()
    if source["season"] != 2026 or source["source_url"] != CALENDAR:
        raise ValueError("Unverified NLS season or source")
    rounds = source["rounds"]
    if len(rounds) != 10 or {entry["number"] for entry in rounds} != set(range(1, 11)):
        raise ValueError("NLS Round inventory changed")
    if source["tests"] != approved["tests"]:
        raise ValueError("NLS test inventory changed")
    retrieved = source["retrieved_at"]
    groups = {}
    for entry in sorted(rounds, key=lambda entry: entry["number"]):
        number = entry["number"]
        expected = approved["rounds"][number - 1]
        if any(entry[field] != expected[field] for field in ("source_url", "name", "date", "sessions")):
            raise ValueError("NLS schedule changed; reassess the factual projection")
        date.fromisoformat(entry["date"])
        group = "qualifiers" if number in (4, 5) else "september" if number in (8, 9) else f"round-{number}"
        groups.setdefault(group, []).append(entry)
    meetings = []
    translation = {"source_language": "de", "method": "bounded factual translation and reviewed label mapping", "version": "nls-2026-v1", "translated_at": "2026-09-10T10:39:40.875Z", "review_state": "accepted-standing-poc", "reviewer": "Chris", "authorization": AUTHORIZATION}
    def assertion(field, value, url, checksum, locator, preferred=True, translated=False, subject=None, effective=None):
        checksum = source.get("documents", {}).get(url, checksum)
        return FieldAssertion(field=field, value=value, source_url=url, retrieved_at=retrieved, response_sha256=checksum,
            locator=locator, rule=RULE, preferred=preferred, translation=translation if translated else None,
            subject_identity=subject, effective_local=effective)
    for group, entries in groups.items():
        is_qualifiers = group == "qualifiers"
        source_url = PREVIEW if is_qualifiers else entries[0]["source_url"]
        assertions = []
        sessions = []
        candidate_rounds = []
        for entry in entries:
            number = entry["number"]
            round_id = f"nls:2026:round:{number}"
            status = "cancelled" if number == 1 else "abandoned" if number == 4 else "scheduled"
            candidate_rounds.append({"identity": round_id, "number": number, "name": entry["name"], "status": status})
            assertions.append(assertion("round", f"Round {number}: {entry['name']}; race date {entry['date']}; planned", entry["source_url"], entry["sha256"], ".entry-content h2 and calendar row" if not is_qualifiers else ".entry-content p[0,13,14]", translated=not is_qualifiers, subject=round_id))
            for period in entry["sessions"]:
                session_id = f"{round_id}:{period['key']}"
                start = {"local": f"{entry['date']}T{period['start']}"}
                end = {"local": f"{entry['date']}T{period['end']}"} if period["end"] else None
                sessions.append({"identity": session_id, "round_identity": round_id, "name": period["name"],
                    "status": status if number == 1 or period["key"] == "race" else "scheduled", "start": start, "end": end,
                    "duration_minutes": period.get("duration_minutes")})
                assertions.append(assertion("timetable", json.dumps(period, sort_keys=True), entry["source_url"], entry["sha256"], ".entry-content p[13,14]" if is_qualifiers else f".entry-content table.table: {period['key']} row", translated=not is_qualifiers, subject=session_id))
            for observation in entry.get("ancillary", []):
                assertions.append(assertion("timetable", json.dumps(observation, sort_keys=True), entry["source_url"], entry["sha256"], ".entry-content table.table: ancillary row", preferred=False, translated=True, subject=round_id))
            if number in STATUS:
                path, checksum, statement, effective = STATUS[number]
                assertions.append(assertion("status" if number != 2 else "schedule_revision", statement, ORIGIN + "/language/en/" + path, checksum, ".entry-content p[0-3]", subject=round_id, effective=effective))
        assertions.append(assertion("meeting_grouping", "April 17-19 programme, Rounds 4 and 5" if is_qualifiers else "September double-header, Rounds 8 and 9" if group == "september" else "One numbered programme", PREVIEW if is_qualifiers else GROUPING, "c9f879135807e312ccf054cca637f5d3e61b53edfed5b735f652340cafb5bc64" if is_qualifiers else "13e0c5ec25eb4fd3279d52a1aeccb830c46bf02f1401ba919bdfaf31e7b7c131", ".entry-content programme dates"))
        assertions.append(assertion("layout", "2026 Qualifiers: 25.378 km; omit AMG Arena, include Muellenbach loop" if is_qualifiers else "Generic NLS description: 24.358 km; exact 2026 route version unverified, canonical length unset", PREVIEW if is_qualifiers else VENUE, "c9f879135807e312ccf054cca637f5d3e61b53edfed5b735f652340cafb5bc64" if is_qualifiers else "0d31b9fc1fae8251406230357a14fb0ee2963cce617042e342f7d72af447fe21", ".entry-content p[12]" if is_qualifiers else ".entry-content p[9]"))
        if is_qualifiers:
            assertions.append(assertion("layout", "Calendar generalizes the short GP-course and Nordschleife combination to all races; Qualifiers preview is the narrower 2026 exception", CALENDAR, source["calendar_sha256"], ".entry-content p[0]", preferred=False, translated=True))
        meetings.append(ScheduledEnvelope(source_identity=f"nls:2026:{group}", source_url=source_url, retrieved_at=retrieved,
            source_language="en", evidence=RULE + "; scheduled inventory, not a claim of completion; " + AUTHORIZATION,
            field_assertions=assertions,
            meeting=ScheduledMeeting(competition_identity=COMPETITION, competition_name="NLS", season_year=2026,
                circuit_identity="nls:nordschleife-combined", circuit_name="Nordschleife combined course",
                venue={"identity": "nuerburgring", "name": "Nuerburgring"},
                layout={"identity": "nls:qualifiers:2026" if is_qualifiers else "nls:ordinary:2026-unverified", "name": "Qualifiers route 2026" if is_qualifiers else "NLS configuration (2026 route unverified)", "length_km": 25.378 if is_qualifiers else None},
                meeting_name="NLS Qualifiers" if is_qualifiers else "NLS September double-header" if group == "september" else entries[0]["name"],
                status="cancelled" if entries[0]["number"] == 1 else "scheduled", start_date="2026-04-17" if is_qualifiers else entries[0]["date"], end_date=entries[-1]["date"],
                round_number=None, rounds=candidate_rounds, sessions=sessions,
                coverage={"state": "incomplete", "activity": "present", "reason": "Friday and detailed Qualifiers timetable unverified; no verified offsets or actual finish times" if is_qualifiers else "Planned HTML timetable only; detailed PDFs, actual timings and offsets unverified", "source_url": source_url})))
    for entry in source["tests"]:
        identity = f"nls:2026:test:{entry['date']}"
        sessions = [{"identity": f"{identity}:{route}", "name": "Test - sprint course" if route == "sprint" else "Test - NLS configuration", "status": "scheduled", "start": {"local": f"{entry['date']}T{start}"}, "end": {"local": f"{entry['date']}T{end}"}, "circuit_identity": "nls:gp-sprint" if route == "sprint" else "nls:nordschleife-combined", "layout": {"identity": "nls:sprint:2026-unverified" if route == "sprint" else "nls:ordinary:2026-unverified", "name": "Sprint course (2026 route unverified)" if route == "sprint" else "NLS configuration (2026 route unverified)"}} for start, end, route in entry["windows"]]
        meetings.append(ScheduledEnvelope(source_identity=identity, source_url=TESTS, retrieved_at=retrieved, source_language="en", evidence=RULE + "; separate unnumbered test Meeting; association does not assert race cancellation",
            field_assertions=[assertion("timetable", json.dumps(entry, sort_keys=True), TESTS, source.get("tests_sha256", "f91357b706e79421e20caed71d4e031f1cb3c225cc25dbd5855285563390fdb3"), ".entry-content p[0,1]", translated=True)],
            meeting=ScheduledMeeting(competition_identity=COMPETITION, competition_name="NLS", season_year=2026, circuit_identity="nls:nordschleife-combined", circuit_name="Nordschleife combined course", venue={"identity": "nuerburgring", "name": "Nuerburgring"},
                meeting_name=f"NLS test and setup - {entry['association']}", start_date=entry["date"], end_date=entry["date"], kind="test", round_number=None, sessions=sessions,
                coverage={"state": "incomplete", "activity": "present", "reason": "Published track windows; detailed route versions, offsets and actual operation unverified", "source_url": TESTS})))
    return SeasonCandidateEnvelope(source_identity="nls:2026", source_url=CALENDAR, retrieved_at=retrieved, source_language="en", competition_identity=COMPETITION, season_year=2026, meetings=sorted(meetings, key=lambda entry: (entry.meeting.start_date, entry.source_identity)),
        coverage={"state": "incomplete", "activity": "present", "reason": "10 numbered Round slots and 7 test dates; Qualifiers detailed timetable blocked, PDFs and complete status history unassessed", "source_url": CALENDAR})


def parse_round(entry: dict, content: bytes) -> dict:
    document = BeautifulSoup(content, "html.parser")
    headings = [node.get_text(" ", strip=True) for node in document.select(".entry-content h2")]
    if headings != [f"NLS{entry['number']}"]:
        raise ValueError("NLS Round heading changed")
    rows = document.select(".entry-content table.table tr")
    if len(rows) != 5:
        raise ValueError("NLS timetable inventory changed")
    sessions, ancillary = [], []
    labels = {"Qualifying": ("qualifying", "Qualifying"), "Pitwalk": ("pit-walk", "Pit walk"), "Gridwalk": ("grid-walk", "Grid walk"), "Startaufstellung": ("grid-formation", "Grid formation")}
    for row in rows:
        cells = [node.get_text(" ", strip=True) for node in row.select("td")]
        if len(cells) != 2:
            raise ValueError("NLS timetable columns changed")
        clock = re.fullmatch(r"([0-2]\d:[0-5]\d)\s*[-\u2013]\s*([0-2]\d:[0-5]\d)\s+Uhr", cells[0])
        if not clock or clock[1] >= clock[2] or any(int(value[:2]) > 23 for value in clock.groups()):
            raise ValueError("NLS clock range is invalid")
        race = re.fullmatch(r"Rennen \(([46]) Stunden\)", cells[1])
        if race:
            sessions.append({"key": "race", "name": "Race", "start": clock[1], "end": clock[2], "duration_minutes": int(race[1]) * 60})
        elif cells[1] in labels:
            key, name = labels[cells[1]]
            value = {"key": key, "name": name, "start": clock[1], "end": clock[2]}
            (sessions if key == "qualifying" else ancillary).append(value)
        else:
            raise ValueError("Unverified NLS activity label")
    if [period["key"] for period in sessions] != ["qualifying", "race"] or {period["key"] for period in ancillary} != {"pit-walk", "grid-walk", "grid-formation"}:
        raise ValueError("NLS track and ancillary activity inventory changed")
    return {**entry, "sessions": sessions, "ancillary": ancillary, "sha256": hashlib.sha256(content).hexdigest()}


DOCUMENTS = [
    (PREVIEW, [0, 12, 13, 14], "7ffc2ce31f99e3a4213e3fa6e2cb24e2b2b3ecbcabdb18e11873633d900f4947"),
    (TESTS, [0, 1], "766ef93cfed7ff2af66c3a17a8e573123c705454f04beacea757e4a86b725421"),
    (GROUPING, None, "6f45889f0a18c02a9daf28a3992b97ad5dece45f9033868f4610890ea76409b0"),
    (VENUE, [9], "920b28da708734f5c97f1a4b39063d8791222b4af5c8928f079962c3cad478d2"),
    (ORIGIN + "/language/en/" + STATUS[1][0], [0, 1, 2], "51b4d8e2b9a0de1d254b441c3d0867acbf3c6adec62d74028e86964f9125cdf6"),
    (ORIGIN + "/language/en/" + STATUS[2][0], [0, 3], "31593bfc0cc48525a0cd66c1e3d285dbb421c7e18b496b0ffb18d2e0f95ef989"),
    (ORIGIN + "/language/en/" + STATUS[4][0], [0, 3], "ce319e70528b73c16f483ed61f5e8c30381536ceed5ebc1995860b98218d00dd"),
]


def _get(client: httpx.Client, url: str) -> bytes:
    if not url.startswith(ORIGIN + "/language/"):
        raise ValueError("Unapproved NLS source origin")
    with client.stream("GET", url, follow_redirects=False) as response:
        response.raise_for_status()
        if response.status_code != 200 or "text/html" not in response.headers.get("content-type", "").lower():
            raise ValueError("Expected ordinary public NLS HTML")
        content = bytearray()
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > 5_000_000:
                raise ValueError("NLS response exceeds acquisition limit")
    return bytes(content)


def fetch_season(season: int, client: httpx.Client, now: datetime | None = None) -> dict:
    if season != 2026:
        raise ValueError("Only the verified NLS 2026 season is supported")
    source = reviewed_source()
    content = _get(client, CALENDAR)
    document = BeautifulSoup(content, "html.parser")
    if not document.title or "2026" not in document.title.get_text():
        raise ValueError("NLS calendar season changed")
    rows = document.select(".entry-content table.table tr")
    if len(rows) != 9:
        raise ValueError("NLS calendar membership changed")
    observed = set()
    expected = {entry["number"]: entry for entry in source["rounds"] if entry["number"] not in (4, 5)}
    qualifiers = 0
    for row in rows:
        cells = row.select("td")
        if len(cells) != 2 or len(cells[1].select("a[href]")) != 1:
            raise ValueError("NLS calendar structure changed")
        date_text, label = (cell.get_text(" ", strip=True) for cell in cells)
        url = urljoin(CALENDAR, str(cells[1].select_one("a[href]")["href"]))
        match = re.match(r"NLS(\d+):", label)
        if match:
            number = int(match[1])
            if number not in expected or number in observed or url != expected[number]["source_url"] or date_text != date.fromisoformat(expected[number]["date"]).strftime("%d.%m.%Y"):
                raise ValueError("NLS source identity or date changed")
            observed.add(number)
            source["rounds"][number - 1] = parse_round(expected[number], _get(client, url))
        elif url == "https://www.24h-rennen.de/" and date_text == "18.-19.04.2026" and label == "ADAC 24h Qualifiers (2x4h)":
            qualifiers += 1
        else:
            raise ValueError("Unverified NLS calendar record")
    if observed != set(expected) or qualifiers != 1:
        raise ValueError("NLS calendar inventory is incomplete")
    source["calendar_sha256"] = hashlib.sha256(content).hexdigest()
    source["documents"] = {}
    for url, indices, fingerprint in DOCUMENTS:
        content = _get(client, url)
        document = BeautifulSoup(content, "html.parser")
        paragraphs = document.select(".entry-content p")
        nodes = [paragraphs[index] for index in indices] if indices else document.select(".entry-content table")
        normalized = "\n".join(" ".join(node.get_text(" ", strip=True).split()) for node in nodes)
        if hashlib.sha256(normalized.encode()).hexdigest() != fingerprint:
            raise ValueError("NLS editorial evidence changed; reassess the factual projection")
        source["documents"][url] = hashlib.sha256(content).hexdigest()
    for entry in source["rounds"]:
        if entry["number"] in (4, 5):
            entry["sha256"] = source["documents"][PREVIEW]
    source["tests_sha256"] = source["documents"][TESTS]
    source["retrieved_at"] = (now or datetime.now(UTC)).isoformat()
    adapt_season(source)
    return source