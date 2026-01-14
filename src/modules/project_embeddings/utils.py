import json
from pathlib import Path

def load_projects(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)