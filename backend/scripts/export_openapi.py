"""Write the API contract to `backend/openapi.json` (the frontend mocks against it).

Usage: `uv run python scripts/export_openapi.py` (add `--check` to fail when the file is stale).
"""

import json
import sys
from pathlib import Path

from app.main import app

TARGET = Path(__file__).resolve().parent.parent / "openapi.json"


def render() -> str:
    return json.dumps(app.openapi(), indent=2, sort_keys=True) + "\n"


def main() -> int:
    text = render()
    if "--check" in sys.argv:
        if not TARGET.exists() or TARGET.read_text() != text:
            print("openapi.json is stale: run `uv run python scripts/export_openapi.py`")
            return 1
        return 0
    tmp = TARGET.with_suffix(".json.tmp")
    tmp.write_text(text)
    tmp.replace(TARGET)
    print(f"wrote {TARGET} ({len(app.openapi()['paths'])} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
