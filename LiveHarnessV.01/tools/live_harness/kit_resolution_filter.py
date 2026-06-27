from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .common import read_json, tool_result


def check(run_dir: Path, candidate_dir: Path) -> dict[str, Any]:
    errors = []
    warnings = []
    plan_path = run_dir / "kit-resolution" / "kit-resolution-plan.json"
    if not plan_path.exists():
        errors.append("kit-resolution-plan.json missing")
        plan = {}
    else:
        plan = read_json(plan_path, {})
    required = plan.get("required_capabilities", []) if isinstance(plan.get("required_capabilities"), list) else []
    if not required:
        errors.append("no required capabilities in kit resolution plan")
    for item in required:
        if not item.get("preferred"):
            errors.append(f"capability missing preferred source: {item.get('id')}")
        fallback = item.get("fallback")
        if fallback and not (candidate_dir / fallback).exists():
            errors.append(f"fallback missing: {fallback}")
    for path in ["src/integration/kitResolver.js", "src/integration/nexusRuntimeAdapter.js", "src/integration/protokitAdapter.js"]:
        if not (candidate_dir / path).exists():
            errors.append(f"integration module missing: {path}")
    gamehost_text = ""
    gh = candidate_dir / "src" / "host" / "gameHost.js"
    if gh.exists():
        gamehost_text = gh.read_text(encoding="utf-8", errors="replace")
    if "integration" not in gamehost_text:
        errors.append("GameHost does not expose integration state")
    report = run_dir / "kit-resolution" / "kit-resolution-report.json"
    if not report.exists():
        warnings.append("kit-resolution-report.json missing")
    return tool_result("kit_resolution_filter", not errors, "Kit resolution passed" if not errors else "Kit resolution failed", errors=errors, warnings=warnings, data={"required_count": len(required)})


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    candidate = Path(sys.argv[2]) if len(sys.argv) > 2 else root
    print(json.dumps(check(root, candidate), indent=2))
