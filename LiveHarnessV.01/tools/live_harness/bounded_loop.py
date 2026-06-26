from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import write_json, ledger, utc_id
from .action_router import choose_default, route
from .feed_forward_store import store


def synthetic_turn(run_dir: Path, agent_id: str, agent_type: str, move: str, summary: str, artifact: dict[str, Any] | None = None) -> dict[str, Any]:
    response = {
        "agent_id": agent_id,
        "agent_type": agent_type,
        "round": 1,
        "move": move,
        "summary": summary,
        "evidence": ["bootstrap execution path"],
        "artifact": artifact or {},
        "available_actions": ["CONTINUE", "SHOW_ADVANCED", "ASK_SLOT", "RECONCILE", "STOP"],
        "selected_action": {"type": "CONTINUE"},
        "advanced_payload": {"injectable": True, "content": artifact or {}},
        "next": {"continue": True, "recommended_move": "CONTINUE"}
    }
    write_json(run_dir / f"{agent_id}-response.json", response)
    store(run_dir, agent_id, {"agent_id": agent_id, "summary": summary, "artifact": artifact or {}})
    selected = choose_default(response)
    ledger("action-ledger.jsonl", {"time": utc_id(), "agent_id": agent_id, "move": move, "selected_action": selected})
    return {"response": response, "route": route(selected)}
