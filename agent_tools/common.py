from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def result(tool_id: str, ok: bool, summary: str, errors: list[str] | None = None, warnings: list[str] | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": tool_id,
        "ok": bool(ok),
        "summary": summary,
        "errors": errors or [],
        "warnings": warnings or [],
        "data": data or {},
    }


def load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(path: str | Path, value: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_text(path: str | Path, default: str = "") -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else default


def write_text(path: str | Path, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def append_text(path: str | Path, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    old = p.read_text(encoding="utf-8") if p.exists() else ""
    p.write_text(old + content, encoding="utf-8")


def extract_json_object(raw: str) -> dict[str, Any]:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object found")
    value = json.loads(text[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("JSON value was not an object")
    return value


def safe_repo_path(path: str, allowed_prefixes: list[str]) -> Path:
    clean = path.strip().replace("\\", "/")
    candidate = Path(clean)
    if not clean or clean.startswith("/") or ".." in candidate.parts:
        raise ValueError(f"Unsafe path: {path}")
    if clean.startswith(".github/"):
        raise ValueError("The turn agent may not edit workflow files")
    allowed = any(clean == prefix.rstrip("/") or clean.startswith(prefix) for prefix in allowed_prefixes)
    if not allowed:
        raise ValueError(f"Path outside allowed prefixes: {path}")
    return candidate


def list_known_files(prefixes: list[str], limit: int = 160) -> list[str]:
    out: list[str] = []
    for prefix in prefixes:
        root = Path(prefix)
        if root.is_file():
            out.append(str(root))
        elif root.exists():
            for p in root.rglob("*"):
                if p.is_file() and ".git" not in p.parts:
                    out.append(str(p))
                    if len(out) >= limit:
                        return sorted(out)
    return sorted(out)
