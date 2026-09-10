import argparse
import json
import os
import sys
from pathlib import Path

from filelock import Timeout

from app.publication import PublicationModule
from app.review import ReviewService
from app.stores import GraphDbProjection, PostgresOperationalStore


def main(arguments: list[str] | None = None, *, service: ReviewService | None = None) -> int:
    parser = argparse.ArgumentParser(description="Private Motorsport Hub review workflow")
    parser.add_argument("--reviews-dir", type=Path, default=Path(__file__).parents[2] / "reviews")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("preview").add_argument("candidate", type=Path)
    commands.add_parser("show").add_argument("item_id")
    proposal = commands.add_parser("propose")
    proposal.add_argument("item_id")
    proposal.add_argument("decision", type=Path)
    for name in ("decide", "publish"):
        command = commands.add_parser(name)
        command.add_argument("item_id")
        command.add_argument("--confirmation", required=True)
    commands.add_parser("publication").add_argument("item_id")
    options = parser.parse_args(arguments)
    try:
        if service is None:
            store = PostgresOperationalStore(os.environ["DATABASE_URL"])
            graph = GraphDbProjection(
                os.environ["GRAPHDB_URL"], os.environ.get("GRAPHDB_REPOSITORY", "motorsport"),
                Path(__file__).parents[2] / "graphdb/repository-config.ttl",
            )
            service = ReviewService(options.reviews_dir, store, PublicationModule(store, graph))
        match options.command:
            case "preview":
                result = service.preview(json.loads(options.candidate.read_text("utf-8-sig")))
            case "show":
                result = service.show(options.item_id)
            case "propose":
                request = json.loads(options.decision.read_text("utf-8-sig"))
                result = service.propose_decision(options.item_id, **request)
            case "decide":
                result = service.record_decision(options.item_id, options.confirmation)
            case "publication":
                result = service.propose_publication(options.item_id)
            case "publish":
                result = service.publish(options.item_id, options.confirmation)
            case _:
                raise ValueError("Unknown review command")
        print(json.dumps(result, indent=2, ensure_ascii=True))
        return 0
    except Timeout:
        print("Another review command is active. Try again when it finishes.", file=sys.stderr)
    except (ValueError, StopIteration) as error:
        message = str(error) if isinstance(error, ValueError) else "Review Item not found"
        print(message, file=sys.stderr)
    except Exception as error:
        print(
            f"Review command failed ({type(error).__name__}). No item was automatically approved. "
            "Inspect the queue and current publication before retrying. Connection details are not logged.",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())