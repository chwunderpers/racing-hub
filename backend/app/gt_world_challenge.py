import html
import json
import re
from datetime import UTC, date, datetime
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from app.publication import FieldAssertion, ScheduledEnvelope, ScheduledMeeting, SeasonCandidateEnvelope


ORIGIN = "https://www.gt-world-challenge-europe.com"
COMPETITION = "gt-world-challenge-europe"
CIRCUITS = {
    "244": ("gtwce:paul-ricard", "Paul Ricard"),
    "246": ("gtwce:paul-ricard", "Paul Ricard"),
    "247": ("gtwce:brands-hatch", "Brands Hatch"),
    "245": ("f1-circuit-7", "Spa-Francorchamps"),
    "248": ("f1-circuit-39", "Autodromo Nazionale Monza"),
    "249": ("f1-circuit-7", "Spa-Francorchamps"),
    "250": ("gtwce:misano", "Misano World Circuit"),
    "251": ("gtwce:magny-cours", "Circuit de Nevers Magny-Cours"),
    "252": ("gtwce:nurburgring", "Nurburgring (layout unresolved)"),
    "253": ("f1-circuit-55", "Circuit Park Zandvoort"),
    "254": ("f1-circuit-15", "Circuit de Barcelona-Catalunya"),
    "255": ("gtwce:portimao", "Portimao Circuit"),
}
CLASSIFICATIONS = {"244": "Test Day", "245": "Test Day", **{str(identity): f"Round {number}" for number, identity in enumerate(range(246, 256), 1)}}
MAPPING_RULE = "gtwce-circuits-2026-v1: explicit source Meeting key crosswalk; evidence docs/sources/gt-world-challenge-europe.md#explicit-circuit-crosswalk-evidence; subject to candidate review"


def adapt_season(source: dict) -> SeasonCandidateEnvelope:
    entries = source["meetings"]
    if source["season"] != 2026 or source["source_url"] != ORIGIN + "/calendar":
        raise ValueError("Unverified GT source or season")
    if len(entries) != 12 or {entry["id"] for entry in entries} != set(CIRCUITS):
        raise ValueError("GT calendar membership differs from the verified inventory")
    meetings = []
    for entry in entries:
        identity = entry["id"]
        classification = entry["classification"]
        if classification != CLASSIFICATIONS[identity]:
            raise ValueError("GT classification differs from verified inventory")
        if not re.fullmatch(r"(?:[a-z0-9-]|%[A-Fa-f0-9]{2})+", entry["slug"]):
            raise ValueError("Unexpected GT Meeting path")
        url = f"{ORIGIN}/event/{identity}/{entry['slug']}"
        retrieved = entry.get("retrieved_at", source["retrieved_at"])
        start, end = date.fromisoformat(entry["start"]), date.fromisoformat(entry["end"])
        if start.year != 2026 or end.year != 2026:
            raise ValueError("GT Meeting is outside the verified season")
        assertions = []
        def assertion(field, value, locator, rule, preferred=False, source_url=url):
            assertions.append(FieldAssertion(field=field, value=value, locator=locator, rule=rule, preferred=preferred, source_url=source_url, retrieved_at=retrieved))
        assertion("kind", classification, f"calendar:event/{identity}/classification", "Calendar classification controls championship membership; Test Day plus Prologue name is a prologue", True, source["source_url"])
        if "description" in entry:
            assertion("kind", entry["description"], "Event.description", "Retained alternative; descriptions do not override calendar Round/Test Day classification")
        assertion("meeting_name", entry["name"], "Event.name", "HTML entity decoding and outer whitespace trimming", True)
        assertion("start_date", entry["start"], "Event.startDate", "Date-only inclusive website bounds", True)
        assertion("end_date", entry["end"], "Event.endDate", "Date-only inclusive website bounds", True)
        assertion("circuit_name", entry["place"], "Event.location.name", "Retained provider label; canonical identity is selected by explicit crosswalk")
        circuit_id, circuit_name = CIRCUITS[identity]
        assertion("circuit_identity", circuit_id, f"event/{identity}:place-and-operator-evidence", MAPPING_RULE, True)
        for observation in entry.get("observations", []):
            assertion(observation["field"], observation["value"], observation["locator"], observation["rule"])
        is_test = classification == "Test Day"
        meetings.append(ScheduledEnvelope(
            source_identity=f"gtwce:meeting:{identity}", source_url=url, retrieved_at=retrieved,
            source_language="en", evidence=f"Official GT World Challenge Europe calendar and Meeting {identity}; {classification}; {MAPPING_RULE}",
            field_assertions=assertions,
            meeting=ScheduledMeeting(
                competition_identity=COMPETITION, competition_name="GT World Challenge Europe", season_year=2026,
                circuit_identity=circuit_id, circuit_name=circuit_name, meeting_name=html.unescape(entry["name"]).strip(),
                start_date=start, end_date=end, kind="prologue" if is_test and "Prologue" in entry["name"] else "test" if is_test else "championship",
                round_number=None if is_test else int(classification.split()[1]), sessions=[],
            ),
        ))
    return SeasonCandidateEnvelope(source_identity="gtwce:2026", source_url=source["source_url"], retrieved_at=source["retrieved_at"], source_language="en", competition_identity=COMPETITION, season_year=2026, meetings=sorted(meetings, key=lambda entry: (entry.meeting.start_date, entry.source_identity)))


def _document(client: httpx.Client, url: str) -> BeautifulSoup:
    with client.stream("GET", url, follow_redirects=False) as response:
        response.raise_for_status()
        if response.status_code != 200 or "text/html" not in response.headers.get("content-type", "").lower():
            raise ValueError("Expected ordinary public HTML")
        content = bytearray()
        for chunk in response.iter_bytes():
            content.extend(chunk)
            if len(content) > 5_000_000:
                raise ValueError("GT page exceeds acquisition limit")
    return BeautifulSoup(content.decode("utf-8"), "html.parser")


def fetch_season(season: int, client: httpx.Client, now: datetime | None = None) -> dict:
    if season != 2026:
        raise ValueError("Only the verified 2026 GT season is supported")
    calendar = _document(client, ORIGIN + "/calendar")
    retrieved = now or datetime.now(UTC)
    if not any(re.match(r"^2026 Calendar\b", heading.get_text(" ", strip=True)) for heading in calendar.select("h1,h2")):
        raise ValueError("Unexpected GT calendar season")
    inventory = {}
    for card in calendar.select(".past-events__list-item,.calendar__list-item"):
        links = {str(anchor["href"]) for anchor in card.select('a[href^="/event/"]')}
        classifications = [node.get_text(" ", strip=True) for node in card.select(".past-events__piped-list-span,.calendar__race-text")]
        classifications = [value for value in classifications if re.fullmatch(r"Test Day|Round \d+", value)]
        if len(links) != 1 or len(classifications) != 1:
            raise ValueError("Ambiguous GT calendar entry")
        path = quote(links.pop(), safe="/-%")
        match = re.fullmatch(r"/event/(\d+)/((?:[a-z0-9-]|%[a-fA-F0-9]{2})+)", path)
        if not match or match[1] in inventory:
            raise ValueError("Unexpected or duplicate GT Meeting identity")
        inventory[match[1]] = {"id": match[1], "slug": match[2], "classification": classifications[0]}
    if set(inventory) != set(CIRCUITS) or any(entry["classification"] != CLASSIFICATIONS[identity] for identity, entry in inventory.items()):
        raise ValueError("GT calendar inventory changed")
    for entry in inventory.values():
        document = _document(client, f"{ORIGIN}/event/{entry['id']}/{entry['slug']}")
        entry["retrieved_at"] = (now or datetime.now(UTC)).isoformat()
        values = [json.loads(script.get_text()) for script in document.select('script[type="application/ld+json"]')]
        events = [value for value in values if isinstance(value, dict) and value.get("@type") == "Event"]
        if len(events) != 1:
            raise ValueError("Expected exactly one GT Event")
        event = events[0]
        if any(not isinstance(event.get(field), str) for field in ("name", "startDate", "endDate", "description")) or not isinstance(event.get("location"), dict):
            raise ValueError("GT Event fields changed")
        place = event["location"]
        if not isinstance(place.get("name"), str):
            raise ValueError("GT Place field missing")
        entry.update(name=event["name"], start=event["startDate"], end=event["endDate"], description=event["description"], place=place["name"])
        observations = []
        def retain(field, value, locator, rule):
            observations.append({"field": field, "value": value if isinstance(value, str) else json.dumps(value, sort_keys=True, ensure_ascii=True), "locator": locator, "rule": rule})
        retain("circuit_address", place.get("address"), "Event.location.address", "Raw identity evidence; never a label join")
        retain("cup", event.get("performer"), "Event.performer", "Cup affiliation does not assign Round membership")
        for anchor in document.select("a[href]"):
            if anchor.get_text(" ", strip=True).lower() == "visit website":
                retain("circuit_website", str(anchor["href"]), "a:Visit Website@href", "Raw operator-link evidence; malformed hosts are not repaired or fetched")
        tables = document.select("table.timetable__table")
        if not tables:
            raise ValueError("Verified GT timetable is missing")
        for table_index, table in enumerate(tables, 1):
            caption_node = table.select_one(".timetable__caption")
            caption = caption_node.get_text(" ", strip=True) if caption_node else ""
            headers = [node.get_text(" ", strip=True) for node in table.select("thead th")]
            if not caption or headers != ["Session", "Local Time", "GMT"]:
                raise ValueError("GT timetable schema changed")
            rows = table.select("tbody tr")
            if not rows:
                raise ValueError("Verified GT timetable rows are missing")
            for row_index, row in enumerate(rows, 1):
                cells = [node.get_text(" ", strip=True) for node in row.select("td")]
                if len(cells) != 3 or any(not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value) for value in cells[1:]):
                    raise ValueError("GT timetable row changed")
                retain("timetable", {"caption": caption, "name": cells[0], "local": cells[1], "gmt": cells[2]}, f"table.timetable__table[{table_index}]/tbody/tr[{row_index}]", "Unresolved activity observation, not a Session: no stable ID, end clock or UTC date supplied; caption retained independently of Meeting bounds")
        entry["observations"] = observations
    source = {"season": season, "source_url": ORIGIN + "/calendar", "retrieved_at": retrieved.isoformat(), "meetings": list(inventory.values())}
    adapt_season(source)
    return source