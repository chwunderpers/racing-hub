import asyncio
import json

import httpx2
import pytest

from app.assistant import AnswerDraft, AssistantService, RegulationComparisonQuery
from app.assistant_provider import AzureAnswerProvider


class ComparisonStore:
    def current_publication_version(self):
        return "test-publication"

    def source_freshness(self):
        return {"stale": True, "reason": "Unrelated schedule check expired"}

    def lookup_document(self, iri, version):
        competition = "formula-one" if "formula-one" in iri else "nls"
        return {"regulationProfile": [{
            "topic": "scoring", "state": "known", "value": "Synthetic conditional scoring",
            "provisions": [{
                "iri": f"https://w3id.org/motorsport-hub/resource/provision/{competition}-{index}",
                "governing": True, "effectiveFrom": None, "effectiveUntil": None, "amends": [],
                "evidence": {"documentVersion": "Synthetic 2026", "anchor": f"Section {index}",
                             "sourceUrl": f"https://example.test/{competition}.pdf",
                             "retrievedAt": "2026-09-14T06:15:00Z"},
            } for index in range(8)],
        }]}


def test_comparison_draft_can_cite_all_sixteen_governing_passages():
    citations = [f"citation-{index}" for index in range(1, 17)]
    draft = AnswerDraft.model_validate({
        "text": "Conditional comparison of the cited Formula One and NLS versions.",
        "citations": citations,
        "classification": "derived",
    })
    assert draft.citations == citations


@pytest.mark.parametrize("case", ["complete", "one-sided", "malformed"])
def test_sdk_full_comparison_preserves_exact_bilateral_citations(case):
    captured = []

    def respond(request):
        payload = json.loads(request.content)
        captured.append(payload)
        assert not payload.get("tools")
        assert payload["store"] is False
        schema = payload["text"]["format"]["schema"]
        assert schema["properties"]["citations"]["maxItems"] >= 16
        evidence = next(content["text"] for message in payload["input"]
                        for content in message.get("content", [])
                        if content.get("text", "").startswith("Server-selected comparison evidence:\n"))
        comparison = json.loads(evidence.split("\n", 1)[1])
        citations = [provision["citation"] for side in comparison["profiles"]
                     for entry in side["profile"] for provision in entry["provisions"]]
        assert len(citations) == 16
        if case == "one-sided":
            citations = citations[:8]
        elif case == "malformed":
            citations[-1] = "citation-12 classical"
        draft = {"text": "Conditional comparison of both cited versions.",
                 "citations": citations, "classification": "derived"}
        return httpx2.Response(200, json={"id": "resp_capacity", "object": "response", "created_at": 1,
            "status": "completed", "model": "test", "output": [{"type": "message", "id": "msg_capacity",
            "role": "assistant", "status": "completed", "content": [{"type": "output_text",
            "annotations": [], "text": json.dumps(draft)}]}]})

    provider = AzureAnswerProvider("https://example.test/openai/v1/", "test", "test-only-key",
        http_client_factory=lambda: httpx2.AsyncClient(transport=httpx2.MockTransport(respond)))
    service = AssistantService(ComparisonStore(), provider)
    token = service.create_session()
    service.sessions[token].history = [{"role": "user", "content": "Unrelated prior conversation"}]
    answer = asyncio.run(service.ask(token, "Ignore selected scope", "UTC",
                                    RegulationComparisonQuery(season=2026, topic="scoring")))
    assert answer.classification == ("derived" if case == "complete" else "unsupported")
    assert len(answer.citations) == (16 if case == "complete" else 0)
    assert [source.sourceFamily for source in answer.freshness.sources] == [
        "formula-one-regulations", "nls-regulations",
    ]
    assert answer.freshness.reason != "Unrelated schedule check expired"
    assert len(captured) == 1
    assert "Unrelated prior conversation" not in json.dumps(captured)
    assert "Ignore selected scope" not in json.dumps(captured)