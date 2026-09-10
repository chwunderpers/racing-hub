from datetime import UTC, datetime, timedelta


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