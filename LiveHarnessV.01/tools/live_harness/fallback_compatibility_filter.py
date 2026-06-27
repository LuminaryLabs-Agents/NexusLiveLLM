from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .common import read_json, tool_result


def check(run_dir: Path, candidate_dir: Path) -> dict[str, Any]:
    plan = read_json(run_dir / "kit-resolution" / "fallback-plan.json", {"fallbacks": {}})
    fallbacks = plan.get("fallbacks", {}) if isinstance(plan.get("fallbacks"), dict) else {}
    errors = []
    for name, path in fallbacks.items():
        if not (candidate_dir / str(path)).exists():
            errors.append(f"missing fallback {name}: {path}")
    adapter = candidate_dir / "src" / "integration" / "nexusRuntimeAdapter.js"
    if adapter.exists():
        text = adapter.read_text(encoding="utf-8", errors="replace")
        if "local-fallback" not in text:
            errors.append("adapter does not record local-fallback provider")
    else:
        errors.append("nexusRuntimeAdapter.js missing")
    return tool_result("fallback_compatibility_filter", not errors, "Fallback compatibility passed" if not errors else "Fallback compatibility failed", errors=errors, data={"fallbacks": fallbacks})


if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    candidate = Path(sys.argv[2]) if len(sys.argv) > 2 else root
    print(json.dumps(check(root, candidate), indent=2))
