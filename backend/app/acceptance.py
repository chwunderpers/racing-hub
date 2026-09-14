import argparse
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tarfile
import tempfile
from uuid import uuid4
import xml.etree.ElementTree as ElementTree

from dotenv import dotenv_values


def run_acceptance(output: Path, license_path: Path) -> int:
    root = Path(__file__).resolve().parents[2]
    output.mkdir(parents=True, exist_ok=False)
    phases = []
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    project = "racing-accept-" + uuid4().hex[:12]
    report = {"revision": revision, "project": project, "status": "failed", "phases": phases}
    with tempfile.TemporaryDirectory(prefix="racing-accept-") as temporary:
        checkout = Path(temporary) / "checkout"
        checkout.mkdir()
        snapshot = Path(temporary) / "checkout.tar"
        subprocess.run(["git", "archive", "HEAD", "--output", str(snapshot)], cwd=root, check=True, capture_output=True)
        with tarfile.open(snapshot) as archive:
            archive.extractall(checkout, filter="data")
        environment = {key: value for key, value in os.environ.items()
                       if not key.startswith(("GRAPHDB_", "DATABASE_URL", "ASSISTANT_", "TEST_", "POSTGRES_", "ACCEPTANCE_"))}
        password = secrets.token_urlsafe(32)
        environment.update(GRAPHDB_LICENSE_FILE=str(license_path.resolve()), ACCEPTANCE_POSTGRES_PASSWORD=password,
                           ACCEPTANCE_DOCKER_DATABASE_URL=f"postgresql://motorsport:{password}@database:5432/motorsport",
                           PYTHONPATH=str(checkout / "backend"), ACCEPTANCE_REHEARSAL=project)
        compose = ["docker", "compose", "-p", project, "-f", "compose.acceptance.yaml"]

        def run(label: str, command: list[str], timeout: int = 300) -> str:
            print(label, flush=True)
            result = subprocess.run(command, cwd=checkout, env=environment, capture_output=True, text=True, timeout=timeout)
            phases.append({"name": label, "passed": result.returncode == 0})
            if result.returncode:
                diagnostic = result.stdout + result.stderr
                for key, value in environment.items():
                    if value and any(marker in key for marker in ("PASSWORD", "TOKEN", "API_KEY", "DATABASE_URL")):
                        diagnostic = diagnostic.replace(value, "[REDACTED]")
                (output / "failure.txt").write_text(diagnostic, encoding="utf-8")
                raise RuntimeError(label + " failed; see sanitized failure.txt")
            return result.stdout.strip()

        def port(service: str, internal: str) -> str:
            return run("Locate " + service, [*compose, "port", service, internal]).rsplit(":", 1)[1]

        try:
            run("Start separate PostgreSQL and licensed GraphDB", [*compose, "up", "-d", "--wait", "database", "graphdb"], 300)
            environment["DATABASE_URL"] = f"postgresql://motorsport:{password}@127.0.0.1:{port('database', '5432')}/motorsport"
            environment["GRAPHDB_URL"] = "http://127.0.0.1:" + port("graphdb", "7200")
            run("Publish disposable acceptance fixtures", [sys.executable, "-m", "backend.tests.acceptance_seed"])
            run("Configure GraphDB least privilege", [sys.executable, "-m", "app.graph_setup"])
            environment.update({key: value for key, value in dotenv_values(checkout / ".env").items() if value is not None})
            run("Restart secured GraphDB", [*compose, "restart", "graphdb"])
            run("Wait for secured GraphDB", [*compose, "up", "-d", "--no-deps", "--wait", "graphdb"])
            run("Provision restricted PostgreSQL reader", [sys.executable, "-m", "app.assistant_setup"])
            environment.update({key: value for key, value in dotenv_values(checkout / ".env").items() if value is not None})
            run("Build and start clean application", [*compose, "up", "-d", "--build", "--wait", "backend", "frontend"], 900)
            environment["ACCEPTANCE_BASE_URL"] = "http://127.0.0.1:" + port("frontend", "80")
            run("Set exact disposable browser origin", [*compose, "up", "-d", "--no-deps", "--wait", "backend"])
            environment["TEST_DATABASE_URL"] = environment["DATABASE_URL"]
            environment["TEST_GRAPHDB_URL"] = environment["GRAPHDB_URL"]
            environment["TEST_GRAPHDB_USER"] = environment["GRAPHDB_ADMIN_USER"]
            environment["TEST_GRAPHDB_PASSWORD"] = environment["GRAPHDB_ADMIN_PASSWORD"]
            environment["TEST_POSTGRES_CONTAINER"] = run("Locate disposable backup container", [*compose, "ps", "-q", "database"])
            run("Full backend acceptance suite", [sys.executable, "-m", "pytest", "backend/tests", "-q", "--disable-warnings", "--tb=short", "--junitxml=" + str(Path(temporary) / "backend.xml")], 3600)
            suites = ElementTree.parse(Path(temporary) / "backend.xml")
            report["backendTests"] = sum(int(suite.attrib.get("tests", 0)) for suite in suites.iter("testsuite"))
            if any(int(suite.attrib.get("skipped", 0)) for suite in suites.iter("testsuite")):
                raise RuntimeError("Acceptance cannot pass with skipped backend tests")
            npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
            if npm is None:
                raise RuntimeError("Node.js and npm are required")
            run("Install locked frontend dependencies", [npm, "--prefix", "frontend", "ci"], 300)
            run("Frontend component tests", [npm, "--prefix", "frontend", "test"])
            run("Frontend typecheck and production build", [npm, "--prefix", "frontend", "run", "build"])
            run("Frontend dependency audit", [npm, "--prefix", "frontend", "audit", "--audit-level=moderate"])
            run("Desktop/mobile browser and accessibility acceptance", [npm, "--prefix", "frontend", "run", "test:browser"], 300)
            screenshots = checkout / "frontend/test-results"
            if screenshots.exists():
                shutil.copytree(screenshots, output / "browser")
            report["status"] = "passed"
        except Exception as error:
            report["failure"] = type(error).__name__
            print("Acceptance failed; inspect the private report", file=sys.stderr)
        finally:
            try:
                run("Remove disposable containers and volumes", [*compose, "down", "--volumes", "--remove-orphans"], 180)
            except Exception:
                report["status"] = "failed"
                report["cleanupRequired"] = project
            (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": report["status"], "revision": revision, "report": str(output / "report.json")}))
    return 0 if report["status"] == "passed" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Run clean-checkout local PoC acceptance in disposable resources")
    parser.add_argument("--output", type=Path, default=Path("acceptance-results"))
    args = parser.parse_args()
    license_path = Path(os.environ.get("GRAPHDB_LICENSE_FILE", ""))
    if not license_path.is_file():
        print("A valid external GraphDB license file is required", file=sys.stderr)
        return 2
    return run_acceptance(args.output.resolve(), license_path)


if __name__ == "__main__":
    raise SystemExit(main())