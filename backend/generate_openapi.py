import json
from pathlib import Path

from app.main import app


output_path = Path(__file__).with_name("openapi.json")
output_path.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")