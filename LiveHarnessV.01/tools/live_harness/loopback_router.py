from __future__ import annotations

from typing import Any

ROUTES = {
    "public-output-membrane": "product-brief-worker",
    "path-filter": "slot-reconciler",
    "required-file-filter": "slot-reconciler",
    "module-graph-filter": "slot-reconciler",
    "syntax-filter": "repair-worker",
    "renderer-boundary-filter": "domain-map-worker",
    "dsk-boundary-filter": "build-break-dsk-worker",
    "gamehost-filter": "debug-host-worker",
    "file-size-filter": "performance-worker",
    "legacy-builder-output-filter": "launcher-owner-repair",
}


def route_validation_failure(validation: dict[str, Any]) -> dict[str, Any]:
    failed = list(validation.get("failed_filters", []))
    if not failed:
        return {"action": "advance", "target": "promote_candidate", "reason": "all filters passed"}
    first = failed[0]
    return {"action": "repair", "target": ROUTES.get(first, "repair-worker"), "reason": f"{first} failed", "failed_filters": failed}
