import os
import subprocess
import sys


def test_acceptance_command_requires_external_license_before_starting_resources(tmp_path):
    environment = {**os.environ, "GRAPHDB_LICENSE_FILE": str(tmp_path / "missing.license"),
                   "AZURE_OPENAI_API_KEY": "private-canary-not-for-output"}
    result = subprocess.run([sys.executable, "-m", "app.acceptance", "--output", str(tmp_path / "report")],
                            env=environment, capture_output=True, text=True, timeout=30)
    assert result.returncode == 2
    assert "GraphDB license" in result.stderr
    assert "private-canary-not-for-output" not in result.stdout + result.stderr
    assert not (tmp_path / "report").exists()