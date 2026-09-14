from datetime import UTC, datetime

import pytest

from app.freshness import regulation_freshness_view


@pytest.mark.parametrize("f1_dates,expected_stale", [
    (["2026-09-14T06:00:00Z"], False),
    (["2026-09-14T06:00:00Z", "2026-09-10T06:00:00Z"], True),
    ([None], True),
    (["2026-09-14T06:00:00Z", None], True),
    ([], True),
])
def test_comparison_freshness_uses_oldest_verified_document_or_unknown(f1_dates, expected_stale):
    comparison = {"profiles": [{"competition": competition, "profile": [{
        "provisions": [{"evidence": {"retrievedAt": retrieved}} for retrieved in dates],
    }]} for competition, dates in [
        ("formula-one", f1_dates), ("nls", ["2026-09-14T06:15:00Z"]),
    ]]}
    result = regulation_freshness_view(comparison, now=datetime(2026, 9, 14, 7, tzinfo=UTC))
    assert result["stale"] is expected_stale
    assert [source["sourceFamily"] for source in result["sources"]] == [
        "formula-one-regulations", "nls-regulations",
    ]
    assert result["sources"][1]["stale"] is False
    assert result["sources"][1]["checkedAt"] == "2026-09-14T06:15:00Z"
    if len(f1_dates) == 2 and all(f1_dates):
        assert result["sources"][0]["checkedAt"] == "2026-09-10T06:00:00Z"
        assert result["reason"] == "Regulation document verification expired"


def test_unavailable_comparison_does_not_claim_fresh_sources():
    result = regulation_freshness_view({"profiles": []})
    assert result["stale"] is True
    assert all(source["checkedAt"] is None for source in result["sources"])


def test_regulation_policy_is_independent_of_schedule_default(monkeypatch):
    from datetime import timedelta
    from app.freshness import REGULATION_VERIFICATION_MAX_AGE, freshness_view

    monkeypatch.setitem(REGULATION_VERIFICATION_MAX_AGE, "nls", timedelta(hours=1))
    comparison = {"profiles": [{"competition": competition, "profile": [{
        "provisions": [{"evidence": {"retrievedAt": "2026-09-14T05:00:00Z"}}],
    }]} for competition in ("formula-one", "nls")]}
    now = datetime(2026, 9, 14, 7, tzinfo=UTC)
    result = regulation_freshness_view(comparison, now=now)
    assert result["sources"][0]["stale"] is False
    assert result["sources"][1]["stale"] is True
    assert result["checkedAt"] == "2026-09-14T05:00:00Z"
    assert freshness_view({"success": True, "lastSuccessAt": "2026-09-14T05:00:00Z"}, now=now)["stale"] is False