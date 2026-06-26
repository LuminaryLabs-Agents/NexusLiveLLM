from __future__ import annotations

from typing import Any

CORE_IMPORT = "https://cdn.jsdelivr.net/gh/LuminaryLabs-Dev/NexusRealtime@main/src/index.js"
PROTOKIT_BASE = "https://cdn.jsdelivr.net/gh/LuminaryLabs-Agents/NexusRealtime-ProtoKits@main/protokits/"

IMPORTS = {
    "nexusrealtime.createRealtimeGame": CORE_IMPORT,
    "nexusrealtime.domain-service-kit": CORE_IMPORT,
    "nexusrealtime.sequence-node": CORE_IMPORT,
    "protokit.action-input-kit": PROTOKIT_BASE + "action-input-kit/index.js",
}


def resolve_import(capability: dict[str, Any]) -> dict[str, Any]:
    cap_id = str(capability.get("capability_id", ""))
    url = IMPORTS.get(cap_id)
    return {
        "capability_id": cap_id,
        "classification": capability.get("classification"),
        "safe_to_import": bool(url and capability.get("safe_to_import")),
        "import": url,
        "use_as": "runtime_dependency" if url and capability.get("safe_to_import") else capability.get("use_as", "reference_pattern")
    }


def build_import_map(capabilities: list[dict[str, Any]]) -> dict[str, Any]:
    imports: dict[str, str] = {}
    for cap in capabilities:
        resolved = resolve_import(cap)
        if resolved.get("safe_to_import") and resolved.get("import"):
            key = cap.get("capability_id", "capability")
            imports[str(key)] = str(resolved["import"])
    return {"schema": "liveharness.import-map.v1", "imports": imports}
