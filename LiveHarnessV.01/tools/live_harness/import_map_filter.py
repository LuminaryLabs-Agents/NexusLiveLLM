from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re

from .common import tool_result

ALLOWED_PREFIXES = [
    "https://cdn.jsdelivr.net/gh/LuminaryLabs-Dev/NexusRealtime@",
    "https://cdn.jsdelivr.net/gh/LuminaryLabs-Agents/NexusRealtime-ProtoKits@",
    "https://unpkg.com/three@"
]


def _extract_import_map(text: str) -> dict[str, Any]:
    match = re.search(r'<script\s+type=["\']importmap["\']\s*>(.*?)</script>', text, re.S | re.I)
    if not match:
        return {}
    try:
        data = json.loads(match.group(1))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {"__parse_error__": True}


def check(candidate_dir: Path) -> dict[str, Any]:
    html = candidate_dir / "index.html"
    if not html.exists():
        return tool_result("import_map_filter", False, "index.html missing", errors=["index.html missing"])
    data = _extract_import_map(html.read_text(encoding="utf-8", errors="replace"))
    errors = []
    if not data:
        errors.append("import map missing")
    if data.get("__parse_error__"):
        errors.append("import map JSON parse failed")
    imports = data.get("imports", {}) if isinstance(data.get("imports"), dict) else {}
    for required in ["@nexus/core", "@protokits/action-input", "three"]:
        if required not in imports:
            errors.append(f"missing import alias {required}")
    for alias, url in imports.items():
        if isinstance(url, str) and url.startswith("http") and not any(url.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            errors.append(f"remote import not allowlisted: {alias}")
    boot = candidate_dir / "src" / "boot.js"
    if not boot.exists():
        errors.append("src/boot.js missing")
    return tool_result("import_map_filter", not errors, "Import map passed" if not errors else "Import map failed", errors=errors, data={"aliases": sorted(imports.keys())})


if __name__ == "__main__":
    import sys
    print(json.dumps(check(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("docs")), indent=2))
