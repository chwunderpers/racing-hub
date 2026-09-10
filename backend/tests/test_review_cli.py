import json
from pathlib import Path

import pytest
from filelock import FileLock

from app.publication import InMemoryGraphProjection, InMemoryOperationalStore, PublicationModule
from app.review import ReviewService
from app.review_cli import main


def test_show_reads_existing_item_without_connection_settings(tmp_path, monkeypatch, capsys) -> None:
    store = InMemoryOperationalStore()
    directory = tmp_path / "reviews"
    service = ReviewService(directory, store, PublicationModule(store, InMemoryGraphProjection()))
    fixture = Path(__file__).parents[1] / "fixtures/f1-2026-australia.json"
    item = service.preview(json.loads(fixture.read_text("utf-8")))
    original_queue = (directory / "queue.yaml").read_bytes()
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GRAPHDB_URL", raising=False)

    assert main(["--reviews-dir", str(directory), "show", item["id"]]) == 0
    output = capsys.readouterr()
    assert json.loads(output.out) == item
    assert output.err == ""
    assert (directory / "queue.yaml").read_bytes() == original_queue
    assert store.current_publication_version() is None


@pytest.mark.parametrize("queue_state", ["missing-directory", "empty", "locked"])
def test_show_reports_missing_or_locked_queue_without_connections(tmp_path, monkeypatch, capsys, queue_state) -> None:
    directory = tmp_path / "reviews"
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GRAPHDB_URL", raising=False)
    arguments = ["--reviews-dir", str(directory), "show", "missing-item"]
    if queue_state == "missing-directory":
        assert main(arguments) == 1
        assert not directory.exists()
    else:
        directory.mkdir()
        if queue_state == "locked":
            with FileLock(directory / ".review.lock", timeout=0):
                assert main(arguments) == 1
        else:
            assert main(arguments) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert ("Another review command is active" if queue_state == "locked" else "Review Item not found") in output.err
    assert not (directory / "queue.yaml").exists()


def test_commands_requiring_connections_name_missing_settings(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("GRAPHDB_URL", raising=False)
    assert main(["--reviews-dir", str(tmp_path), "publication", "missing-item"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert "Missing required environment settings: DATABASE_URL, GRAPHDB_URL" in output.err


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