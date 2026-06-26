from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import harness_root, read_json, write_json, ledger, utc_id


def plan(scored: list[dict[str, Any]], run_dir: Path) -> dict[str, Any]:
    policy = read_json(harness_root() / "state" / "gallery-policy.json", {"max_active_games": 10, "protect_latest_count": 2})
    max_active = int(policy.get("max_active_games", 10))
    protect_latest = int(policy.get("protect_latest_count", 2))
    ordered = sorted(scored, key=lambda x: (int(x.get("score", 0) or 0), str(x.get("id", ""))), reverse=True)
    latest = list(scored)[:protect_latest]
    protected_ids = {str(item.get("id")) for item in latest if item.get("id")}
    keep: list[dict[str, Any]] = []
    prune: list[dict[str, Any]] = []
    for item in ordered:
        gid = str(item.get("id"))
        if gid in protected_ids and item not in keep:
            keep.append(item)
    for item in ordered:
        if item in keep:
            continue
        if len(keep) < max_active:
            keep.append(item)
        else:
            prune.append(item)
    plan_doc = {
        "version": 1,
        "run_id": run_dir.name,
        "created_at": utc_id(),
        "policy": policy,
        "summary": {"total_games": len(scored), "keep": len(keep), "prune": len(prune), "max_active_games": max_active},
        "keep_ids": [item.get("id") for item in keep],
        "decisions": [
            {
                "game_id": item.get("id"),
                "score": item.get("score"),
                "decision": "prune_after_capsule",
                "reason": ["outside max_active_games after deterministic scoring"],
                "safe_to_apply": True
            }
            for item in prune
        ]
    }
    write_json(run_dir / "purge" / "purge-plan.json", plan_doc)
    ledger("purge-ledger.jsonl", {"time": utc_id(), "event": "purge.plan", "keep": len(keep), "prune": len(prune)})
    return plan_doc
