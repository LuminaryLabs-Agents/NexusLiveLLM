from __future__ import annotations

from pathlib import Path
import subprocess

from .common import result


def run(context: dict | None = None) -> dict:
    roots = [Path("docs"), Path("src"), Path("generated")]
    files = [p for root in roots if root.exists() for p in root.rglob("*.js")]
    if not files:
        return result("js_syntax_check", True, "No JavaScript files found", warnings=["No .js files under docs, src, or generated"])
    errors: list[str] = []
    checked: list[str] = []
    for path in files:
        checked.append(str(path))
        try:
            proc = subprocess.run(["node", "--check", str(path)], text=True, capture_output=True, check=False, timeout=20)
        except FileNotFoundError:
            return result("js_syntax_check", True, "Node is not installed; skipped JS syntax check", warnings=["node executable not found"], data={"files": checked})
        except subprocess.TimeoutExpired:
            errors.append(f"node --check timed out for {path}")
            continue
        if proc.returncode != 0:
            errors.append(f"{path}: {proc.stderr.strip() or proc.stdout.strip()}")
    ok = not errors
    return result("js_syntax_check", ok, "JavaScript syntax passed" if ok else "JavaScript syntax failed", errors, data={"files": checked})
