from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import harness_root, read_json, ledger, utc_id


def load_models() -> dict[str, Any]:
    return read_json(harness_root() / "models" / "models.json", {"tiers": {}})


def choose_tier(task_type: str, goal: dict[str, Any] | None = None, latest_tools: dict[str, Any] | None = None) -> str:
    if latest_tools and latest_tools.get("ok") is False:
        return "thinking"
    if goal and goal.get("model_tier"):
        return str(goal["model_tier"])
    if task_type in {"queue_builder", "root_orchestrator", "reconcile"}:
        return "orchestrator"
    if task_type in {"slot_code", "repair"}:
        return "process"
    if task_type in {"copy", "docs"}:
        return "writing"
    if task_type in {"review"}:
        return "answer"
    return "instant"


def route(task_type: str, goal: dict[str, Any] | None = None, latest_tools: dict[str, Any] | None = None) -> dict[str, Any]:
    models = load_models()
    tier = choose_tier(task_type, goal, latest_tools)
    config = dict(models.get("tiers", {}).get(tier, {}))
    item = {"time": utc_id(), "task_type": task_type, "tier": tier, "model": config.get("model"), "reason": "tier selected by LiveHarness model_router"}
    ledger("model-ledger.jsonl", item)
    return {"tier": tier, "config": config, "ledger": item}
