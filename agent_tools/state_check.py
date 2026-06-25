from __future__ import annotations

from .common import load_json, result


def run(context: dict | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    state = load_json(".agent/state.json", None)
    if state is None:
        return result("state_check", False, "Missing .agent/state.json", [".agent/state.json does not exist"])
    if not isinstance(state, dict):
        return result("state_check", False, "State is not a JSON object", ["Top-level state value must be an object"])
    if "turn_count" not in state:
        warnings.append("state.turn_count is missing")
    elif not isinstance(state.get("turn_count"), int):
        errors.append("state.turn_count must be an integer")
    if "latest_run_id" not in state:
        warnings.append("state.latest_run_id is missing")
    if "status" not in state:
        warnings.append("state.status is missing")
    ok = not errors
    return result("state_check", ok, "State is valid" if ok else "State validation failed", errors, warnings, {"keys": sorted(state.keys())})
