from datetime import datetime
import json
import re
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import esprima

from app.publication import PublishedTime, CandidateSession, ScheduledEnvelope, ScheduledMeeting, SeasonCandidateEnvelope


SESSION_NAMES = {
    "p1": "Practice 1", "p2": "Practice 2", "p3": "Practice 3",
    "q": "Qualifying", "r": "Race", "ss": "Sprint Qualifying", "s": "Sprint",
}
SESSION_STATES = {"upcoming": "scheduled", "completed": "completed", "cancelled": "cancelled"}
VERIFIED_MEETING_KEYS = {
    2026: ("1279", "1280", "1281", "1284", "1285", "1286", "1287", "1288", "1289", "1290", "1291", "1292", "1293", "1294", "1295", "1308", "1296", "1297", "1298", "1299", "1300", "1301", "1302"),
}
SPRINT_MEETING_KEYS = {"1280", "1284", "1285", "1289", "1292", "1296"}


def source_key(value) -> str:
    if not isinstance(value, (str, int)) or not re.fullmatch(r"[1-9][0-9]*", str(value)):
        raise ValueError("Missing or invalid official identity")
    return str(value)


def adapt_season(source: dict) -> SeasonCandidateEnvelope:
    season = source["season"]
    expected = VERIFIED_MEETING_KEYS.get(season)
    ordered = sorted(source["meetings"], key=lambda entry: int(entry["race"]["meetingNumber"]))
    if expected is None or tuple(source_key(entry["race"]["meetingKey"]) for entry in ordered) != expected:
        raise ValueError("Calendar membership differs from the verified season inventory")
    if [int(entry["race"]["meetingNumber"]) for entry in ordered] != list(range(1, len(expected) + 1)):
        raise ValueError("Incomplete or duplicate Round numbers")
    envelopes = []
    for entry in ordered:
        race = entry["race"]
        source_key(race["circuitKey"])
        path = urlparse(entry["source_url"])
        if path.scheme != "https" or path.netloc != "www.formula1.com" or not path.path.startswith(f"/en/racing/{season}/"):
            raise ValueError("Unexpected official Meeting URL")
        sessions = []
        expected_codes = {"p1", "ss", "s", "q", "r"} if str(race["meetingKey"]) in SPRINT_MEETING_KEYS else {"p1", "p2", "p3", "q", "r"}
        if len(race["meetingSessions"]) != len(expected_codes) or {session["session"] for session in race["meetingSessions"]} != expected_codes:
            raise ValueError("Session inventory differs from the verified Meeting schedule")
        for session in race["meetingSessions"]:
            source_key(session["meetingSessionKey"])
            if session["session"] not in SESSION_NAMES or session["state"] not in SESSION_STATES:
                raise ValueError("Unknown source session code or state")
            def clock(field: str) -> PublishedTime | None:
                value = session.get(field)
                return PublishedTime(local=value, offset=session.get("gmtOffset"), zone=session.get("timezone")) if value else None
            start = clock("startTime")
            if start is None:
                raise ValueError("Session start assertion is missing")
            sessions.append(CandidateSession(
                identity=f"f1:session:{session['meetingSessionKey']}", name=SESSION_NAMES[session["session"]],
                status=SESSION_STATES[session["state"]], start=start, end=clock("endTime"),
            ))
        envelopes.append(ScheduledEnvelope(
            source_identity="f1:2026:australia" if season == 2026 and str(race["meetingKey"]) == "1279" else f"f1:meeting:{race['meetingKey']}",
            source_url=entry["source_url"], retrieved_at=entry["retrieved_utc"], source_language="en",
            evidence=f"Official Formula One schedule; meetingKey={race['meetingKey']}; circuitKey={race['circuitKey']}; round={race['meetingNumber']}",
            meeting=ScheduledMeeting(
                competition_identity="formula-one", competition_name="Formula One", season_year=season,
                circuit_identity="albert-park-grand-prix-circuit" if str(race["circuitKey"]) == "10" else f"f1-circuit-{race['circuitKey']}",
                meeting_name=race["meetingName"], circuit_name=race["circuitOfficialName"],
                start_date=datetime.fromisoformat(race["meetingStartDate"]).date(),
                end_date=datetime.fromisoformat(race["meetingEndDate"]).date(),
                round_number=int(race["meetingNumber"]), event_timezone=race.get("meetingTimezone"), sessions=sessions,
            ),
        ))
    return SeasonCandidateEnvelope(
        source_identity=f"f1:{season}", source_url=source["source_url"], retrieved_at=source["retrieved_utc"],
        source_language="en", competition_identity="formula-one", season_year=season, meetings=envelopes,
    )


def race_payload(html: str) -> dict:
    chunks = []
    for script in BeautifulSoup(html, "html.parser").find_all("script"):
        text = script.string or ""
        if "self.__next_f.push" not in text:
            continue
        try:
            tree = esprima.parseScript(text, {"range": True}).toDict()
        except esprima.Error as error:
            raise ValueError("Unsupported source script syntax") from error
        def visit(node):
            if isinstance(node, dict):
                if node.get("type") == "CallExpression":
                    start, end = node["callee"]["range"]
                    if text[start:end] == "self.__next_f.push":
                        start, end = node["arguments"][0]["range"]
                        payload = json.loads(text[start:end])
                        if payload[0] == 1:
                            chunks.append(payload[1])
                for value in node.values():
                    visit(value)
            elif isinstance(node, list):
                for value in node:
                    visit(value)
        visit(tree)
    stream = "".join(chunks).encode("utf-8")
    offset = 0
    models = []
    while offset < len(stream):
        colon = stream.find(b":", offset)
        if colon < 0 or not re.fullmatch(rb"[0-9a-f]+", stream[offset:colon]):
            raise ValueError("Unexpected Flight record")
        start = colon + 1
        if stream[start:start + 1] == b"T":
            comma = stream.index(b",", start)
            encoded_length = stream[start + 1:comma]
            if not re.fullmatch(rb"[0-9a-f]+", encoded_length):
                raise ValueError("Invalid Flight text length")
            length = int(encoded_length, 16)
            offset = comma + 1 + length
            if offset > len(stream):
                raise ValueError("Truncated Flight text")
            continue
        newline = stream.find(b"\n", start)
        stop = newline if newline >= 0 else len(stream)
        raw = stream[start:stop]
        if raw.startswith((b"[", b"{")):
            models.append(json.loads(raw))
        offset = stop + 1
    matches = []
    def walk(value):
        if isinstance(value, dict):
            if isinstance(value.get("pageData"), dict) and "race" in value["pageData"]:
                matches.append(value["pageData"]["race"])
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(models)
    if len(matches) != 1:
        raise ValueError("Expected one official race payload")
    race = matches[0]
    if not isinstance(race, dict) or not isinstance(race.get("meetingSessions"), list) or any(not isinstance(session, dict) for session in race["meetingSessions"]):
        raise ValueError("Unexpected race or Session shape")
    fields = ("meetingNumber", "meetingKey", "meetingName", "meetingStartDate", "meetingEndDate", "circuitKey", "circuitOfficialName", "meetingTimezone")
    result = {field: race[field] for field in fields}
    session_fields = ("session", "meetingSessionKey", "startTime", "endTime", "gmtOffset", "timezone", "state")
    result["meetingSessions"] = [{field: session.get(field) for field in session_fields} for session in race["meetingSessions"]]
    return result


def fetch_season(season: int, client, now: datetime) -> dict:
    base = "https://www.formula1.com"
    url = f"{base}/en/racing/{season}"
    def get_html(address):
        response = client.get(address)
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", "") or len(response.content) > 5_000_000:
            raise ValueError("Unexpected source response")
        return response.text
    html = get_html(url)
    links = {}
    for anchor in BeautifulSoup(html, "html.parser").select(f'a[href^="/en/racing/{season}/"]'):
        rounds = [span.get_text(strip=True) for span in anchor.find_all("span") if re.fullmatch(r"ROUND \d+", span.get_text(strip=True))]
        if rounds:
            href = anchor["href"]
            if not re.fullmatch(rf"/en/racing/{season}/[a-z0-9-]+", href):
                raise ValueError("Unexpected Meeting path")
            links[href] = int(rounds[0].split()[1])
    if not links or sorted(links.values()) != list(range(1, len(links) + 1)):
        raise ValueError("Incomplete numbered calendar")
    entries = []
    for href, number in sorted(links.items(), key=lambda entry: entry[1]):
        race = race_payload(get_html(base + href))
        if int(race["meetingNumber"]) != number or not race["meetingSessions"]:
            raise ValueError("Calendar and Meeting disagree")
        entries.append({"source_url": base + href, "retrieved_utc": now.isoformat(), "race": race})
    return {"source_url": url, "retrieved_utc": now.isoformat(), "season": season, "meetings": entries}