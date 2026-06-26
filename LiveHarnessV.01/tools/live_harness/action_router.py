from __future__ import annotations

from typing import Any

ASK_ACTIONS = {"ASK_ORCHESTRATOR", "ASK_SUB_ORCHESTRATOR", "ASK_SLOT", "ASK_RECONCILER", "ASK_TOOL", "ASK_REVIEWER", "ASK_MODEL_ROUTER", "ASK_HARNESS_ADVISOR"}


def choose_default(response: dict[str, Any], tools: dict[str, Any] | None = None) -> dict[str, Any]:
    if tools and tools.get("ok") is False:
        return {"type": "REPAIR", "reason": "tools_failed"}
    selected = response.get("selected_action")
    if isinstance(selected, dict) and selected.get("type"):
        return selected
    nxt = response.get("next") if isinstance(response.get("next"), dict) else {}
    if nxt.get("recommended_move"):
        return {"type": nxt["recommended_move"]}
    return {"type": "CONTINUE"}


def route(action: dict[str, Any]) -> dict[str, Any]:
    kind = str(action.get("type") or "CONTINUE").upper()
    if kind in ASK_ACTIONS:
        return {"route": "ask", "action": action}
    if kind.startswith("DISPATCH"):
        return {"route": "dispatch", "action": action}
    return {"route": "local", "action": action}
