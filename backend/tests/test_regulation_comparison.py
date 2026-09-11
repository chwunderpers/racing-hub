import copy
import json
from datetime import date
from pathlib import Path

import pytest

from app.publication import InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule
from app.review import ReviewService
from backend.tests.test_regulations import approve_and_publish, regulation_candidate, translated_candidate


def comparison_candidate(state="accepted"):
    candidate = regulation_candidate()
    nls = translated_candidate(state)["regulations"][0]
    nls["competition_identity"] = "nls"
    document = nls["documents"][0]
    document.update(authority="DMSB", title="Synthetic NLS scoring regulations",
                    source_url="https://www.nuerburgring-langstrecken-serie.de/synthetic-test.pdf")
    passage = nls["passages"][0]
    passage["text"] = "Synthetic NLS fixture: class points depend on the number of starters and class position."
    passage["translation"]["source_url"] = document["source_url"]
    provision = nls["provisions"][0]
    provision.update(summary="Synthetic class-dependent points", applicability="NLS 2026 class classification, not overall race position.")
    nls["profile"][0]["value"] = "Synthetic class points depend on starters and class position; no fixed overall winner value."
    season = copy.deepcopy(candidate["seasons"][0])
    season.update(source_identity="nls:2026", competition_identity="nls")
    season["meetings"][0]["source_identity"] = "nls:2026:synthetic"
    season["meetings"][0]["meeting"].update(competition_identity="nls", competition_name="NLS")
    candidate["seasons"].append(season)
    candidate["regulations"].append(nls)
    return candidate


def test_nls_private_review_preserves_f1_and_requires_translation_approval(tmp_path):
    store = InMemoryOperationalStore()
    review = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    candidate = comparison_candidate("pending")
    item = review.preview(candidate)
    assert item["preview"]["validationErrors"] == []
    assert {entry["competition_identity"] for entry in item["candidate"]["regulations"]} == {"formula-one", "nls"}
    with pytest.raises(ValueError, match="translations require"):
        approve_and_publish(review, candidate)
    assert store.current_publication_version() is None


@pytest.mark.parametrize("invalid", [False, True])
def test_organizer_inventory_accepts_unknown_issue_date_but_rejects_wrong_host(tmp_path, invalid):
    candidate = comparison_candidate("pending")
    bundle = candidate["regulations"][1]
    document = bundle["documents"][0]
    document.update(authority="VLN", issued_on=None,
                    source_url="https://untrusted.example/rules.pdf" if invalid else "https://teilnehmer.vln.de/download.php?file=synthetic.pdf")
    bundle["passages"][0]["translation"]["source_url"] = document["source_url"]
    store = InMemoryOperationalStore()
    review = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    item = review.preview(candidate)
    assert bool(item["preview"]["validationErrors"]) is invalid


def test_two_profiles_keep_competition_labels_and_citations_separate(isolated_services, tmp_path):
    from app.assistant import ReadTools, RegulationQuery

    store, graph = isolated_services
    review = ReviewService(tmp_path, store, PublicationModule(store, graph))
    receipt = publish_comparison(review, comparison_candidate())
    reader = store.assistant_reader()
    tools = ReadTools(reader, receipt["version"], "UTC")
    f1 = tools.regulations(RegulationQuery(competition="formula-one", season=2026, topic="scoring"))
    nls = tools.regulations(RegulationQuery(competition="nls", season=2026, topic="scoring"))
    document = reader.lookup_document("https://w3id.org/motorsport-hub/resource/competition-profile/nls%3A2026", receipt["version"])
    assert document["title"] == "NLS 2026 Competition Profile"
    first = f1["profile"][0]["provisions"][0]
    second = nls["profile"][0]["provisions"][0]
    assert first["iri"] != second["iri"]
    assert first["citation"] != second["citation"]
    assert tools.citations[first["citation"]].sourceUrl.startswith("https://www.fia.com/")
    assert tools.citations[second["citation"]].sourceUrl.startswith("https://www.nuerburgring-langstrecken-serie.de/")
    assert second["evidence"]["kind"] == "translation"
    assert "Private translation reviewer" not in json.dumps(document)
    assert "Private explicit translation approval" not in json.dumps(document)
    assert graph.agrees(receipt["version"], "", store.publication_envelope(receipt["version"]))


def publish_comparison(review, candidate):
    item = review.preview(candidate)
    assert item["preview"]["validationErrors"] == []
    proposal = review.propose_decision(
        item["id"], "accepted", "Fixture reviewer", "Reviewed synthetic competition and Circuit identities",
        ["synthetic-points-evidence"], regulation_confirmations=item["preview"]["regulationConfirmations"],
        identity_resolutions={"nls:2026:synthetic/circuit_identity": candidate["seasons"][1]["meetings"][0]["meeting"]["circuit_identity"]},
    )
    review.record_decision(item["id"], proposal["confirmation"])
    proposal = review.propose_publication(item["id"])
    return review.publish(item["id"], proposal["confirmation"])


@pytest.mark.parametrize("case", ["scoring", "unknown", "outside-period", "unresolved-period", "amendment", "future-amendment"])
def test_comparison_discloses_scope_gaps_and_amendments(isolated_services, tmp_path, case):
    from app.assistant import ReadTools, RegulationComparisonQuery

    candidate = comparison_candidate()
    nls = candidate["regulations"][1]
    if case == "unresolved-period":
        nls["provisions"][0]["effective_from"] = None
    if case in ("amendment", "future-amendment"):
        amendment = copy.deepcopy(nls["provisions"][0])
        amendment.update(identity="synthetic-amendment", summary="Conflicting synthetic amended allocation; resolve applicability before comparison.",
                         amends=["synthetic-points"], effective_from="2026-07-01")
        nls["provisions"].append(amendment)
    store, graph = isolated_services
    receipt = publish_comparison(ReviewService(tmp_path, store, PublicationModule(store, graph)), candidate)
    tools = ReadTools(store.assistant_reader(), receipt["version"], "UTC")
    request = RegulationComparisonQuery(season=2026, topic="tyres" if case == "unknown" else "scoring",
                                       on_date=date(2025, 12, 1) if case == "outside-period" else date(2026, 3, 1) if case == "future-amendment" else date(2026, 8, 1))
    result = tools.compare_regulations(request)
    assert [side["competition"] for side in result["profiles"]] == ["formula-one", "nls"]
    assert result["season"] == 2026 and result["publicationVersion"] == receipt["version"]
    assert result["status"] == ("available" if case in ("scoring", "future-amendment") else "insufficient-evidence")
    if case == "unknown":
        assert all(side["profile"][0]["state"] == "unknown" for side in result["profiles"])
    elif case in ("amendment", "future-amendment"):
        provisions = result["profiles"][1]["profile"][0]["provisions"]
        assert len(provisions) == 2
        assert any(provision["amends"] for provision in provisions)
        assert len({provision["citation"] for provision in provisions}) == 2
        if case == "future-amendment":
            future = next(provision for provision in provisions if provision["amends"])
            assert future["temporalStatus"] == "outside-period" and not future["governing"]
    elif case != "scoring":
        assert result["limitations"]


@pytest.mark.parametrize("case", ["scoring", "tyres", "dated", "one-sided", "invented-citation", "conflict", "wrong-season", "future-citation"])
def test_agent_framework_compares_with_scoped_citations_or_declines(isolated_services, tmp_path, case):
    import asyncio
    import httpx2
    from app.assistant import AssistantService
    from app.assistant_provider import AzureAnswerProvider

    store, graph = isolated_services
    candidate = comparison_candidate()
    topic = "tyres" if case == "tyres" else "scoring"
    if case == "dated":
        candidate["regulations"][1]["provisions"][0]["effective_from"] = None
    if case == "future-citation":
        bundle = candidate["regulations"][1]
        amendment = copy.deepcopy(bundle["provisions"][0])
        amendment.update(identity="future-amendment", amends=[amendment["identity"]], effective_from="2026-07-01")
        bundle["provisions"].append(amendment)
    if case == "conflict":
        bundle = candidate["regulations"][1]
        conflicting = copy.deepcopy(bundle["provisions"][0])
        conflicting.update(identity="conflicting-points", summary="Independent conflicting authoritative allocation; priority unresolved.",
                           exceptions=["Conflict unresolved: this assertion is not selected over the original allocation."])
        bundle["provisions"].append(conflicting)
        bundle["profile"][0]["provision_ids"].append(conflicting["identity"])
    receipt = publish_comparison(ReviewService(tmp_path, store, PublicationModule(store, graph)), candidate)
    captured = []

    def respond(request):
        payload = json.loads(request.content)
        captured.append(payload)
        if len(captured) == 1:
            assert any(tool["name"] == "compare_regulations" for tool in payload["tools"])
            query = {"season": 2025 if case == "wrong-season" else 2026, "topic": topic}
            if case == "dated":
                query["on_date"] = "2026-08-01"
            elif case == "future-citation":
                query["on_date"] = "2026-03-01"
            output = [{"type": "function_call", "id": "fc_compare", "call_id": "call_compare", "name": "compare_regulations",
                       "arguments": json.dumps({"request": query}), "status": "completed"}]
        else:
            result = json.loads(next(entry["output"] for entry in payload["input"] if entry.get("type") == "function_call_output"))
            assert [side["competition"] for side in result["profiles"]] == ["formula-one", "nls"]
            if case not in ("tyres", "wrong-season"):
                first, second = (side["profile"][0] for side in result["profiles"])
                assert "25 points" in first["value"] and "class points" in second["value"]
                draft = {"text": "Formula One: a sole full-points race winner receives 25 points. NLS: the synthetic class-points rule depends on starters and class position, not overall race victory. These 2026 rules require their applicability, exceptions and final classifications; no actual event award is calculated.",
                         "citations": [first["provisions"][0]["citation"], second["provisions"][0]["citation"]], "classification": "derived"}
                if case == "dated":
                    assert result["status"] == "insufficient-evidence" and result["limitations"]
                elif case == "one-sided":
                    draft["citations"] = draft["citations"][:1]
                elif case == "invented-citation":
                    draft["citations"].append("citation-invented")
                elif case == "future-citation":
                    assert result["status"] == "available"
                    future = next(provision for provision in second["provisions"] if provision["amends"])
                    assert future["temporalStatus"] == "outside-period" and not future["governing"]
                    draft["citations"] = [first["provisions"][0]["citation"], future["citation"]]
                elif case == "conflict":
                    assert len(second["provisions"]) == 2
                    assert any("Conflict unresolved" in " ".join(provision["exceptions"]) for provision in second["provisions"])
                    draft["citations"] = [first["provisions"][0]["citation"], *[provision["citation"] for provision in second["provisions"]]]
                    draft["text"] += " NLS has two conflicting authoritative assertions; their priority is unresolved, so neither is selected as the applicable allocation."
            else:
                assert result["status"] == "insufficient-evidence"
                draft = {"text": "No reviewed tyre evidence supports this comparison.", "citations": [], "classification": "unsupported"}
            output = [{"type": "message", "id": "msg_compare", "role": "assistant", "status": "completed",
                       "content": [{"type": "output_text", "annotations": [], "text": json.dumps(draft)}]}]
        return httpx2.Response(200, json={"id": "resp_compare", "object": "response", "created_at": 1,
                                        "status": "completed", "model": "test", "output": output})

    provider = AzureAnswerProvider("https://example.test/openai/v1/", "test", "test-only-key",
                                   http_client_factory=lambda: httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
    assistant = AssistantService(store.assistant_reader(), provider)
    answer = asyncio.run(assistant.ask(assistant.create_session(), "Compare Formula One and NLS 2026 " + topic, "UTC"))
    assert len(captured) == 2
    assert answer.publicationVersion == receipt["version"]
    assert answer.classification == ("derived" if case in ("scoring", "conflict") else "unsupported")
    if case in ("scoring", "conflict"):
        assert len(answer.citations) == (3 if case == "conflict" else 2)
        assert "formula-one%3A2026" in answer.citations[0].iri
        assert "nls%3A2026" in answer.citations[1].iri
        assert answer.citations[0].sourceUrl.startswith("https://www.fia.com/")
        assert answer.citations[1].sourceUrl.startswith("https://www.nuerburgring-langstrecken-serie.de/")
    else:
        assert not answer.citations
        if case in ("tyres", "dated", "wrong-season"):
            assert "nls" in answer.text.casefold()
            assert "unresolved" in answer.text if case == "dated" else "unavailable" in answer.text
    for payload in captured:
        assert payload["store"] is False
        assert "Private translation reviewer" not in json.dumps(payload)
        assert "Private explicit translation approval" not in json.dumps(payload)


@pytest.mark.parametrize("state", ["unknown", "not-published", "not-applicable"])
def test_nls_absence_states_preserve_evidence(isolated_services, tmp_path, state):
    from app.assistant import ReadTools, RegulationComparisonQuery

    candidate = comparison_candidate()
    entry = candidate["regulations"][1]["profile"][0]
    entry.update(state=state, value=None)
    if state == "unknown":
        entry["provision_ids"] = []
    store, graph = isolated_services
    receipt = publish_comparison(ReviewService(tmp_path, store, PublicationModule(store, graph)), candidate)
    tools = ReadTools(store.assistant_reader(), receipt["version"], "UTC")
    result = tools.compare_regulations(RegulationComparisonQuery(season=2026, topic="scoring"))
    nls = result["profiles"][1]["profile"][0]
    assert nls["state"] == state and nls["value"] is None
    assert bool(nls["provisions"]) is (state != "unknown")
    assert result["status"] == ("insufficient-evidence" if state == "unknown" else "available")


@pytest.mark.parametrize("invalid", ["wrong-authority", "wrong-host", "wrong-season", "unreviewed-translation"])
def test_nls_rejects_invalid_evidence_scope(tmp_path, invalid):
    candidate = comparison_candidate()
    bundle = candidate["regulations"][1]
    document = bundle["documents"][0]
    if invalid == "wrong-authority":
        document.update(authority="FIA", source_url="https://www.fia.com/synthetic.pdf")
        bundle["passages"][0]["translation"]["source_url"] = document["source_url"]
    elif invalid == "wrong-host":
        document["source_url"] = "https://www.dmsb.de.untrusted.example/synthetic.pdf"
    elif invalid == "wrong-season":
        document["season_year"] = 2025
    else:
        bundle["passages"][0]["translation"]["reviewer"] = None
    store = InMemoryOperationalStore()
    item = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection())).preview(candidate)
    assert item["preview"]["validationErrors"]


def test_nls_ingestion_preserves_existing_f1_profile_and_schedule(tmp_path):
    import hashlib
    import httpx
    from app.publication import PublicationSnapshot, parse_candidate
    from app.regulation_ingestion import prepare_candidate

    candidate = comparison_candidate("pending")
    inventory = candidate["regulations"].pop()
    raw = b"%PDF-1.7 synthetic NLS regulation document"
    document = inventory["documents"][0]
    document["sha256"] = hashlib.sha256(raw).hexdigest()
    inventory["passages"][0]["translation"]["source_sha256"] = document["sha256"]
    path = tmp_path / "nls.json"
    path.write_text(json.dumps(inventory), encoding="utf-8")
    store = InMemoryOperationalStore()
    PublicationModule(store, InMemoryGraphProjection()).publish(parse_candidate(candidate))
    version = store.current_publication_version()
    with httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=httpx.ByteStream(raw)))) as client:
        merged = prepare_candidate(path, store, client)
    original = parse_candidate(candidate)
    assert isinstance(original, PublicationSnapshot)
    assert merged.seasons == original.seasons
    assert merged.regulations[0] == original.regulations[0]
    assert merged.regulations[1].competition_identity == "nls"
    assert merged.regulations[1].passages[0].translation is not None
    assert merged.regulations[1].passages[0].translation.review_state == "pending"
    assert store.current_publication_version() == version


def test_real_nls_inventory_remains_private_pending_translation_review(tmp_path):
    from app.regulations import CompetitionRegulations

    inventory = CompetitionRegulations.model_validate_json(
        (Path(__file__).parents[1] / "fixtures/nls-2026-regulations.json").read_text("utf-8")
    )
    assert len(inventory.documents) == 2 and len(inventory.provisions) == 14
    assert {document.authority for document in inventory.documents} == {"VLN"}
    assert all(document.issued_on is None for document in inventory.documents)
    for passage in inventory.passages:
        assert passage.translation is not None
        assert passage.translation.review_state == "pending"
        assert passage.translation.reviewer is passage.translation.reviewed_at is passage.translation.authorization is None
    assert {entry.topic for entry in inventory.profile if entry.state == "known"} == {"scoring"}
    candidate = comparison_candidate("pending")
    candidate["regulations"][1] = inventory.model_dump(mode="json")
    store = InMemoryOperationalStore()
    review = ReviewService(tmp_path, store, PublicationModule(store, InMemoryGraphProjection()))
    with pytest.raises(ValueError, match="translations require"):
        publish_comparison(review, candidate)
    assert store.current_publication_version() is None


def test_native_graph_queries_retrieve_scoped_regulation_evidence(isolated_services, tmp_path):
    import asyncio
    import os
    from app.graph_mcp import GraphMcpClient
    from app.graph_queries import GraphQueryPolicy

    store, graph = isolated_services
    receipt = publish_comparison(ReviewService(tmp_path, store, PublicationModule(store, graph)), comparison_candidate())
    version = receipt["version"]
    query = f"""PREFIX msh: <https://w3id.org/motorsport-hub/ontology/>
SELECT ?competition ?year ?state ?value ?provision ?text ?source
FROM <https://w3id.org/motorsport-hub/graph/publication/{version}>
WHERE {{
    ?profile a msh:CompetitionProfile; msh:competition ?competition; msh:year ?year; msh:profileValue ?entry .
    ?entry msh:topic "scoring"; msh:knowledgeState ?state; msh:normalizedValue ?value; msh:provision ?provision .
    ?provision msh:provenance ?passage .
    ?passage msh:passageText ?text; msh:sourceUrl ?source .
}} LIMIT 10"""

    async def scenario():
        client = GraphMcpClient(os.environ["TEST_GRAPHDB_URL"] + "/mcp", version,
            os.environ.get("TEST_GRAPHDB_USER"), os.environ.get("TEST_GRAPHDB_PASSWORD"),
            repository=graph.repository_url.rsplit("/", 1)[1])
        result = await client.query(query)
        rows = result["rows"]
        assert isinstance(rows, list) and len(rows) == 2
        assert {row["competition"]["value"].rsplit("/", 1)[1] for row in rows} == {"formula-one", "nls"}
        for row in rows:
            assert row["year"]["value"] == "2026" and row["state"]["value"] == "known"
            scope = row["competition"]["value"].rsplit("/", 1)[1]
            assert scope + "%3A2026" in row["provision"]["value"]
            assert ("fia.com" in row["source"]["value"]) is (scope == "formula-one")
        encoded = json.dumps(result)
        assert "Private translation reviewer" not in encoded
        assert "Private explicit translation approval" not in encoded

    asyncio.run(scenario())
    for private in ("reviewer", "authorization", "evidence"):
        with pytest.raises(ValueError, match="public predicates"):
            GraphQueryPolicy(version).validate(query.replace("msh:passageText", "msh:" + private))