from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field


REGULATION_VERIFICATION_MAX_AGE = {
    "formula-one": timedelta(hours=24),
    "nls": timedelta(hours=24),
}


class SourceFreshnessResponse(BaseModel):
    sourceFamily: str
    stale: bool
    reason: str | None = None
    checkedAt: str | None = None
    lastSuccessAt: str | None = None


class FreshnessResponse(BaseModel):
    stale: bool
    reason: str | None = None
    checkedAt: str | None = None
    lastSuccessAt: str | None = None
    sources: list[SourceFreshnessResponse] = Field(default_factory=list)


def source_freshness_view(attempts: dict[str, dict | None], competitions: set[str]) -> dict:
    families = set(attempts) | (competitions & {"formula-one", "gt-world-challenge-europe", "nls"})
    if not families:
        return freshness_view(None)
    sources = [{"sourceFamily": family, **freshness_view(attempts.get(family))} for family in sorted(families)]
    stale = [source for source in sources if source["stale"]]
    selected = (stale or sources)[0]
    return {**{key: value for key, value in selected.items() if key != "sourceFamily"}, "sources": sources}


def regulation_freshness_view(comparison: dict, now: datetime | None = None) -> dict:
    sources = []
    for competition in ("formula-one", "nls"):
        dates = [provision["evidence"].get("retrievedAt")
                 for side in comparison.get("profiles", []) if side["competition"] == competition
                 for entry in side["profile"] for provision in entry["provisions"]]
        checked = min(dates, key=datetime.fromisoformat) if dates and all(dates) else None
        status = freshness_view({"success": True, "checkedAt": checked, "lastSuccessAt": checked}
                                if checked else None, now=now, max_age=REGULATION_VERIFICATION_MAX_AGE[competition])
        if status["stale"]:
            status["reason"] = "Regulation document verification expired" if checked else "Regulation evidence has not been verified"
        sources.append({"sourceFamily": competition + "-regulations", **status})
    selected = next((source for source in sources if source["stale"]), sources[0])
    return {**{key: value for key, value in selected.items() if key != "sourceFamily"}, "sources": sources}


def freshness_view(attempt: dict | None, now: datetime | None = None, *, max_age: timedelta = timedelta(hours=24)) -> dict:
    now = now or datetime.now(UTC)
    if attempt is None:
        return {"stale": True, "reason": "Source has not been verified", "checkedAt": None, "lastSuccessAt": None}
    success = attempt.get("lastSuccessAt")
    expired = success is None or now - datetime.fromisoformat(success) > max_age
    return {
        **attempt,
        "stale": not attempt["success"] or expired or attempt.get("pending", False),
        "reason": "Source fetch failed" if not attempt["success"] else "New source revision awaits review" if attempt.get("pending") else "Source verification expired" if expired else None,
    }