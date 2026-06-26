from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from .common import repo_root, harness_root, write_json, ledger, utc_id, tool_result
from .public_output_check import scan_docs as public_output_membrane_check


def js_syntax() -> dict[str, Any]:
    root = repo_root()
    files = [p for base in [root / "docs", root / "src", root / "generated"] if base.exists() for p in base.rglob("*.js")]
    errors: list[str] = []
    for path in files:
        try:
            proc = subprocess.run(["node", "--check", str(path)], text=True, capture_output=True, timeout=20)
            if proc.returncode != 0:
                errors.append(str(path) + ": " + (proc.stderr.strip() or proc.stdout.strip()))
        except FileNotFoundError:
            return tool_result("js_syntax_check", True, "Node not found; skipped", warnings=["node missing"])
    return tool_result("js_syntax_check", not errors, "JavaScript syntax passed" if not errors else "JavaScript syntax failed", errors, data={"files": [str(p) for p in files]})


def html_smoke() -> dict[str, Any]:
    root = repo_root()
    files = list((root / "docs").rglob("*.html")) if (root / "docs").exists() else []
    errors: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if "<html" not in text or "</html>" not in text:
            errors.append(str(path) + " is not complete HTML")
    return tool_result("html_smoke_check", not errors, "HTML smoke passed" if not errors else "HTML smoke failed", errors, data={"count": len(files)})


def launcher_manifest() -> dict[str, Any]:
    root = repo_root()
    manifest_path = root / "docs" / "games.json"
    errors: list[str] = []
    if not manifest_path.exists():
        return tool_result("launcher_manifest_check", False, "Missing docs/games.json", ["docs/games.json missing"])
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return tool_result("launcher_manifest_check", False, "Invalid games.json", [str(exc)])
    if not isinstance(manifest, list):
        errors.append("games.json must be a list")
        manifest = []
    for item in manifest:
        url = str(item.get("url", "")) if isinstance(item, dict) else ""
        folder = root / "docs" / url.strip("/")
        if url and not (folder / "index.html").exists():
            errors.append("missing game index: " + str(folder))
    return tool_result("launcher_manifest_check", not errors, "Launcher manifest passed" if not errors else "Launcher manifest failed", errors, data={"entries": len(manifest)})


def run_all() -> dict[str, Any]:
    results = [js_syntax(), html_smoke(), launcher_manifest(), public_output_membrane_check()]
    out = {"ok": all(r["ok"] for r in results), "tools": results}
    ledger("tool-ledger.jsonl", {"time": utc_id(), "ok": out["ok"], "tools": [r["id"] for r in results]})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    out = run_all()
    print(json.dumps(out, indent=2))
    if args.output:
        path = Path(args.output)
        if not path.is_absolute():
            path = harness_root() / path
        write_json(path, out)
    if not out["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
