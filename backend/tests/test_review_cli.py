import json
from pathlib import Path

from app.publication import InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule
from app.review import ReviewService
from app.review_cli import main


def test_operator_cli_previews_confirms_and_publishes_one_item(tmp_path, capsys) -> None:
    store = InMemoryOperationalStore()
    service = ReviewService(tmp_path / "reviews", store, PublicationModule(store, InMemoryGraphProjection()))
    fixture = Path(__file__).parents[1] / "fixtures/f1-2026-australia.json"

    def invoke(arguments):
        assert main(arguments, service=service) == 0
        return json.loads(capsys.readouterr().out)

    item = invoke(["preview", str(fixture)])
    assert invoke(["show", item["id"]])["id"] == item["id"]
    request = tmp_path / "decision.json"
    request.write_text(json.dumps({
        "outcome": "accepted", "person": "Operator", "rationale": "Source checked",
        "evidence": ["https://www.formula1.com/en/racing/2026/australia"],
    }), "utf-8")
    proposal = invoke(["propose", item["id"], str(request)])
    invoke(["decide", item["id"], "--confirmation", proposal["confirmation"]])
    assert store.visible_meetings() == []
    publication = invoke(["publication", item["id"]])
    result = invoke(["publish", item["id"], "--confirmation", publication["confirmation"]])
    assert result["version"] == store.visible_meetings()[0]["publicationVersion"]