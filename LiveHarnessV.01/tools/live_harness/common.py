from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


def utc_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")


def harness_root() -> Path:
    return Path.cwd()


def repo_root() -> Path:
    return Path.cwd().parent


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def append_jsonl(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(value) + "\n")


def ledger(name: str, value: dict[str, Any]) -> None:
    append_jsonl(harness_root() / "ledgers" / name, value)


def tool_result(tool_id: str, ok: bool, summary: str, errors: list[str] | None = None, warnings: list[str] | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"id": tool_id, "ok": ok, "summary": summary, "errors": errors or [], "warnings": warnings or [], "data": data or {}}
