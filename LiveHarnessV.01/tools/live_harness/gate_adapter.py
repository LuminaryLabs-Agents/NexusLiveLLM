from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from .common import harness_root, write_json, ledger, utc_id

BOUNDARY_ACTIONS = {
    "APPLY_WRITE_SET",
    "RUN_COMMAND",
    "COMMIT",
    "DEPLOY",
    "PURGE",
    "DELETE_GAME_FOLDER",
    "PROMOTE_PROTOKIT",
    "PATCH_HARNESS",
    "INTERPRETATION_LOCK",
}

ALLOWED_ROOTS = ["docs/", "LiveHarnessV.01/runs/", "LiveHarnessV.01/state/", "LiveHarnessV.01/ledgers/", "LiveHarnessV.01/archive/"]


def review_action(action: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    action_type = str(action.get("type", "")).upper()
    decision = "allow"
    reasons: list[str] = []
    safer_action: dict[str, Any] | None = None
    if action_type in {"DELETE_GAME_FOLDER", "PATCH_HARNESS", "PROMOTE_PROTOKIT"}:
        decision = "revise"
        reasons.append("High-impact action requires an explicit manual or later-stage workflow.")
        safer_action = {"type": "WRITE_PROPOSAL", "input": action.get("input", "")}
    if action_type == "APPLY_WRITE_SET":
        paths = action.get("paths", []) or []
        bad_paths = [p for p in paths if not any(str(p).startswith(root) for root in ALLOWED_ROOTS)]
        if bad_paths:
            decision = "block"
            reasons.append("Write set contains paths outside allowed roots: " + ", ".join(map(str, bad_paths)))
    if action_type not in BOUNDARY_ACTIONS:
        reasons.append("Not a boundary action; gate records local allow.")
    result = {
        "schema": "liveharness.gate-result.v1",
        "gate_id": "boundary-action-gate",
        "action": action,
        "decision": decision,
        "reasons": reasons or ["Action satisfies current boundary policy."],
        "safer_action": safer_action,
        "created_at": utc_id(),
    }
    gate_dir = run_dir / "gates"
    gate_dir.mkdir(parents=True, exist_ok=True)
    path = gate_dir / f"gate-{action_type.lower() or 'unknown'}-{utc_id()}.json"
    write_json(path, result)
    ledger("gate-ledger.jsonl", {"time": utc_id(), "event": "gate.reviewed", "action": action_type, "decision": decision, "path": str(path)})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Review one LiveHarness boundary action.")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--action-json", default="{}")
    args = parser.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else harness_root() / "runs" / "gate-run"
    if not run_dir.is_absolute():
        run_dir = harness_root() / run_dir
    action = json.loads(args.action_json)
    print(json.dumps(review_action(action, run_dir), indent=2))


if __name__ == "__main__":
    main()
