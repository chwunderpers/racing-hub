import json
from pathlib import Path

import pytest

from app.publication import InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule, parse_candidate, merge_season
from app.review import ReviewService


FIXTURES = Path(__file__).parents[1] / "fixtures"


def regulation_candidate():
    meeting = json.loads((FIXTURES / "f1-2026-australia.json").read_text("utf-8"))
    meeting["meeting"].update(round_number=1, sessions=[])
    return {
        "source_identity": "racing-hub:snapshot", "source_language": "en",
        "seasons": [{
            "source_identity": "f1:2026", "source_language": "en",
            "source_url": meeting["source_url"], "retrieved_at": meeting["retrieved_at"],
            "competition_identity": "formula-one", "season_year": 2026, "meetings": [meeting],
        }],
        "regulations": [{
            "competition_identity": "formula-one", "season_year": 2026,
            "documents": [{
                "identity": "fia:2026:synthetic-a:1", "title": "Synthetic regulation fixture",
                "version": "Test issue 1", "season_year": 2026, "authority": "FIA",
                "source_url": "https://www.fia.com/sites/default/files/synthetic-test.pdf",
                "sha256": "a" * 64, "retrieved_at": "2026-09-10T12:00:00Z",
                "issued_on": "2026-01-01", "source_language": "en",
                "sections": [{"anchor": "A2.2.1", "page": 9}],
            }],
            "passages": [{
                "identity": "synthetic-points-evidence", "document_identity": "fia:2026:synthetic-a:1",
                "anchor": "A2.2.1", "language": "en", "text": "Synthetic fixture: the winner receives 25 points when full points apply.",
                "kind": "paraphrase",
            }],
            "provisions": [{
                "identity": "synthetic-points", "passage_identity": "synthetic-points-evidence",
                "topic": "scoring", "summary": "The sole winner receives 25 points when full points apply.",
                "applicability": "2026 Formula One race, full points, sole winner, final classification.",
                "exceptions": ["Reduced distance and dead heats require separate provisions."],
                "discretion": "Classification may be affected by penalties and appeals.",
                "amends": [], "effective_from": "2026-01-01", "effective_until": None,
            }],
            "profile": [{"topic": "scoring", "state": "known", "value": "Sole full-points race winner: 25 points.", "provision_ids": ["synthetic-points"]}],
        }],
    }


def test_private_review_accepts_structured_english_regulation_candidate(tmp_path):
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    preview = service.preview(regulation_candidate())
    assert preview["preview"]["validationErrors"] == []
    assert store.current_publication_version() is None


def test_regulation_publication_requires_explicit_evidence_and_identity_confirmation(tmp_path):
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    item = service.preview(regulation_candidate())
    proposal = service.propose_decision(item["id"], "accepted", "Test reviewer", "Fixture review", ["synthetic-points"])
    service.record_decision(item["id"], proposal["confirmation"])
    with pytest.raises(ValueError, match="regulation.*confirm|Regulation.*confirm"):
        service.propose_publication(item["id"])
    assert store.current_publication_version() is None


def test_schedule_refresh_retains_accepted_regulation_profile():
    previous = parse_candidate(regulation_candidate())
    refreshed = merge_season(previous, previous.seasons[0])
    assert refreshed.model_dump(mode="json")["regulations"] == previous.model_dump(mode="json")["regulations"]


def test_ingestion_preview_rejects_a_changed_schedule_baseline_before_persistence(tmp_path):
    store = InMemoryOperationalStore()
    publisher = PublicationModule(store, InMemoryGraphProjection())
    original = regulation_candidate()
    first = publisher.publish(parse_candidate(original))
    updated = regulation_candidate()
    updated["seasons"][0]["meetings"][0]["meeting"]["meeting_name"] = "Updated official Meeting name"
    publisher.publish(parse_candidate(updated))
    service = ReviewService(tmp_path, store, publisher)
    with pytest.raises(ValueError, match="baseline"):
        service.preview(original, expected_baseline=first.version)
    assert not (tmp_path / "queue.yaml").exists()


def approve_and_publish(service, candidate):
    item = service.preview(candidate)
    assert item["preview"]["validationErrors"] == []
    proposal = service.propose_decision(
        item["id"], "accepted", "Fixture reviewer", "Reviewed synthetic evidence and identities",
        ["synthetic-points-evidence"], regulation_confirmations=item["preview"]["regulationConfirmations"],
    )
    service.record_decision(item["id"], proposal["confirmation"])
    publication = service.propose_publication(item["id"])
    return service.publish(item["id"], publication["confirmation"])


def test_reviewed_profile_persists_with_provision_evidence_and_citations(isolated_services, tmp_path):
    from app.assistant import ReadTools, RegulationQuery

    store, graph = isolated_services
    service = ReviewService(tmp_path / "reviews", store, PublicationModule(store, graph))
    receipt = approve_and_publish(service, regulation_candidate())
    reader = store.assistant_reader()
    assert len(reader.visible_meetings(receipt["version"])) == 1
    tools = ReadTools(reader, receipt["version"], "UTC")
    result = tools.regulations(RegulationQuery(competition="formula-one", season=2026, topic="scoring"))
    assert result["status"] == "available"
    entry = result["profile"][0]
    assert entry["value"] == "Sole full-points race winner: 25 points."
    provision = entry["provisions"][0]
    assert provision["applicability"] == "2026 Formula One race, full points, sole winner, final classification."
    assert provision["evidence"]["kind"] == "paraphrase"
    assert provision["evidence"]["text"].startswith("Synthetic fixture:")
    assert tools.citations[provision["citation"]].sourceUrl.endswith("synthetic-test.pdf#page=9")
    assert tools.regulations(RegulationQuery(competition="formula-one", season=2025, topic="scoring"))["status"] == "insufficient-evidence"
    assert tools.regulations(RegulationQuery(competition="nls", season=2026, topic="scoring"))["status"] == "insufficient-evidence"
    assert graph.agrees(receipt["version"], "", store.publication_envelope(receipt["version"]))


def test_non_english_passage_is_rejected_before_queue_persistence(tmp_path):
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    candidate = regulation_candidate()
    candidate["regulations"][0]["passages"][0].update(language="de", text="Nicht speichern")
    with pytest.raises(ValueError, match="English"):
        service.preview(candidate)
    assert not (tmp_path / "queue.yaml").exists()


def translated_candidate(state="pending"):
    candidate = regulation_candidate()
    bundle = candidate["regulations"][0]
    document = bundle["documents"][0]
    document["source_language"] = "de"
    bundle["passages"][0].update(kind="translation", translation={
        "source_language": "de", "method": "Synthetic human translation", "version": "fixture-1",
        "translated_at": "2026-09-10T12:01:00Z", "source_url": document["source_url"],
        "source_sha256": document["sha256"], "source_anchor": "A2.2.1", "review_state": state,
        "reviewer": "Private translation reviewer" if state == "accepted" else None,
        "reviewed_at": "2026-09-10T12:02:00Z" if state == "accepted" else None,
        "authorization": "Private explicit translation approval" if state == "accepted" else None,
    })
    return candidate


def test_pending_translation_requires_review_even_after_candidate_acceptance(tmp_path):
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    with pytest.raises(ValueError, match="translations require"):
        approve_and_publish(service, translated_candidate())
    assert store.current_publication_version() is None


@pytest.mark.parametrize("invalid", ["checksum", "unlinked", "boolean", "translation", "amendment-cycle", "wrong-season"])
def test_invalid_regulation_cannot_pass_private_preview(tmp_path, invalid):
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    candidate = regulation_candidate()
    bundle = candidate["regulations"][0]
    if invalid == "checksum":
        bundle["documents"][0]["sha256"] = "unverified"
    elif invalid == "unlinked":
        bundle["profile"][0]["provision_ids"] = ["missing"]
    elif invalid == "boolean":
        bundle["profile"][0]["value"] = True
    elif invalid == "translation":
        bundle["documents"][0]["source_language"] = "de"
    elif invalid == "wrong-season":
        bundle["documents"][0]["season_year"] = 2025
    else:
        second = {**bundle["provisions"][0], "identity": "amended", "amends": ["synthetic-points"]}
        bundle["provisions"][0]["amends"] = ["amended"]
        bundle["provisions"].append(second)
    assert service.preview(candidate)["preview"]["validationErrors"]


def test_agent_framework_answers_or_declines_from_reviewed_profile(isolated_services, tmp_path):
    import asyncio
    import httpx2
    from app.assistant import AssistantService
    from app.assistant_provider import AzureAnswerProvider

    store, graph = isolated_services
    review = ReviewService(tmp_path / "reviews", store, PublicationModule(store, graph))
    approve_and_publish(review, translated_candidate("accepted"))
    for topic in ("scoring", "tyres"):
        captured = []

        def response(request):
            payload = json.loads(request.content)
            captured.append(payload)
            if len(captured) == 1:
                output = [{"type": "function_call", "id": "fc_reg", "call_id": "call_reg", "name": "competition_regulations",
                    "arguments": json.dumps({"request": {"competition": "formula-one", "season": 2026, "topic": topic}}), "status": "completed"}]
            else:
                result = json.loads(next(entry["output"] for entry in payload["input"] if entry.get("type") == "function_call_output"))
                if topic == "scoring":
                    assert result["profile"][0]["provisions"][0]["evidence"]["kind"] == "translation"
                    assert result["profile"][0]["value"] == "Sole full-points race winner: 25 points."
                    assert result["profile"][0]["provisions"][0]["exceptions"]
                    draft = {"text": "The sole winner receives 25 points when full points apply; final classification is required. Reduced distance and dead heats require separate provisions.", "citations": ["citation-1"], "classification": "stated"}
                else:
                    assert result["status"] == "insufficient-evidence"
                    assert result["profile"][0]["state"] == "unknown"
                    draft = {"text": "Reviewed tyre-rule evidence is unavailable; I cannot establish that rule.", "citations": [], "classification": "unsupported"}
                output = [{"type": "message", "id": "msg_reg", "role": "assistant", "status": "completed", "content": [{"type": "output_text", "annotations": [], "text": json.dumps(draft)}]}]
            return httpx2.Response(200, json={"id": "resp_reg", "object": "response", "created_at": 1, "status": "completed", "model": "test", "output": output})

        provider = AzureAnswerProvider("https://example.test/openai/v1/", "test", "test-only-key", http_client_factory=lambda: httpx2.AsyncClient(transport=httpx2.MockTransport(response)))
        assistant = AssistantService(store.assistant_reader(), provider)
        answer = asyncio.run(assistant.ask(assistant.create_session(), "What is the Formula One 2026 " + topic + " rule?", "UTC"))
        assert len(captured) == 2
        assert answer.classification == ("stated" if topic == "scoring" else "unsupported")
        if topic == "scoring":
            assert "25 points" in answer.text
            assert answer.citations[0].sourceUrl.endswith("#page=9")
        else:
            assert answer.citations == []
        for payload in captured:
            assert payload["store"] is False
            assert "Private translation reviewer" not in json.dumps(payload)
            assert "Private explicit translation approval" not in json.dumps(payload)


def test_translation_correction_is_a_revision_and_failed_publication_preserves_previous(isolated_services, tmp_path, monkeypatch):
    from app.assistant import ReadTools, RegulationQuery

    store, graph = isolated_services
    review = ReviewService(tmp_path / "reviews", store, PublicationModule(store, graph))
    original = translated_candidate("accepted")
    first = approve_and_publish(review, original)
    correction = translated_candidate("accepted")
    correction["regulations"][0]["passages"][0]["text"] = "Corrected synthetic English translation, retaining the same conditional 25-point value."
    correction["regulations"][0]["passages"][0]["translation"]["version"] = "fixture-2"
    with monkeypatch.context() as patch:
        patch.setattr(graph, "agrees", lambda *args: False)
        with pytest.raises(RuntimeError, match="does not agree"):
            approve_and_publish(review, correction)
    assert store.current_publication_version() == first["version"]
    second = approve_and_publish(review, correction)
    assert second["version"] != first["version"]
    assert store.publication_envelope(first["version"]).regulations[0].passages[0].translation.version == "fixture-1"
    assert store.publication_envelope(second["version"]).regulations[0].passages[0].translation.version == "fixture-2"
    old = ReadTools(store.assistant_reader(), first["version"], "UTC")
    assert old.regulations(RegulationQuery(competition="formula-one", season=2026, topic="scoring"))["status"] == "insufficient-evidence"


def test_regulation_ingestion_merges_existing_schedule_and_verifies_document_bytes(tmp_path):
    import hashlib
    import httpx
    from app.regulation_ingestion import prepare_candidate

    raw = regulation_candidate()
    bundle = raw["regulations"][0]
    document_bytes = b"%PDF-1.7 synthetic regulation test bytes"
    bundle["documents"][0]["sha256"] = hashlib.sha256(document_bytes).hexdigest()
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle), encoding="utf-8")
    store = InMemoryOperationalStore()
    initial = {**raw, "regulations": []}
    PublicationModule(store, InMemoryGraphProjection()).publish(parse_candidate(initial))
    baseline = store.current_publication_version()
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=httpx.ByteStream(document_bytes), headers={"content-type": "application/pdf"}))) as client:
        candidate = prepare_candidate(path, store, client)
    assert candidate.seasons[0].model_dump(mode="json") == parse_candidate(initial).seasons[0].model_dump(mode="json")
    assert candidate.regulations[0].documents[0].sha256 == bundle["documents"][0]["sha256"]
    assert store.current_publication_version() == baseline
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=httpx.ByteStream(b"%PDF-changed")))) as client:
        with pytest.raises(ValueError, match="checksum"):
            prepare_candidate(path, store, client)
    assert store.current_publication_version() == baseline


@pytest.mark.parametrize("state", ["unknown", "not-published", "not-applicable"])
def test_profile_absence_states_remain_distinct(tmp_path, state):
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    candidate = regulation_candidate()
    entry = candidate["regulations"][0]["profile"][0]
    entry.update(state=state, value=None)
    receipt = approve_and_publish(service, candidate)
    persisted = store.publication_envelope(receipt["version"]).regulations[0].profile[0]
    assert persisted.state == state
    assert persisted.value is None


@pytest.mark.parametrize("failure", ["redirect", "compression", "oversized"])
def test_source_failure_never_replaces_current_publication(tmp_path, failure):
    import httpx
    from app.regulation_ingestion import prepare_candidate

    candidate = regulation_candidate()
    inventory = tmp_path / "inventory.json"
    inventory.write_text(json.dumps(candidate["regulations"][0]), encoding="utf-8")
    store = InMemoryOperationalStore()
    PublicationModule(store, InMemoryGraphProjection()).publish(parse_candidate(candidate))
    previous = store.current_publication_version()
    def respond(request):
        if failure == "redirect":
            return httpx.Response(302, headers={"location": "https://unapproved.example/document"})
        if failure == "compression":
            return httpx.Response(200, headers={"content-encoding": "gzip"}, stream=httpx.ByteStream(b"not-retained"))
        return httpx.Response(200, stream=httpx.ByteStream(b"%PDF-" + b"0" * 10_000_000))
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        with pytest.raises((ValueError, httpx.HTTPError)):
            prepare_candidate(inventory, store, client)
    assert store.current_publication_version() == previous