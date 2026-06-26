from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import write_json, ledger, utc_id


def store(run_dir: Path, name: str, artifact: dict[str, Any]) -> Path:
    path = run_dir / ("feed-forward-" + name + ".json")
    write_json(path, artifact)
    ledger("action-ledger.jsonl", {"time": utc_id(), "kind": "feed_forward", "path": str(path)})
    return path
