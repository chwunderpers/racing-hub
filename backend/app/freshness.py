from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field


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


def freshness_view(attempt: dict | None, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    if attempt is None:
        return {"stale": True, "reason": "Source has not been verified", "checkedAt": None, "lastSuccessAt": None}
    success = attempt.get("lastSuccessAt")
    expired = success is None or now - datetime.fromisoformat(success) > timedelta(hours=24)
    return {
        **attempt,
        "stale": not attempt["success"] or expired or attempt.get("pending", False),
        "reason": "Source fetch failed" if not attempt["success"] else "New source revision awaits review" if attempt.get("pending") else "Source verification expired" if expired else None,
    }