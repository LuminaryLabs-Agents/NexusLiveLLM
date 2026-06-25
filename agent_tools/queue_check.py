from __future__ import annotations

from .common import load_json, result

VALID_STATUSES = {"queued", "active", "blocked", "complete", "failed"}


def run(context: dict | None = None) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    queue = load_json(".agent/queue.json", None)
    if queue is None:
        return result("queue_check", False, "Missing .agent/queue.json", [".agent/queue.json does not exist"])
    if not isinstance(queue, dict):
        return result("queue_check", False, "Queue is not a JSON object", ["Top-level queue value must be an object"])
    goals = queue.get("goals")
    if not isinstance(goals, list):
        errors.append("queue.goals must be a list")
        goals = []
    seen: set[str] = set()
    for index, goal in enumerate(goals):
        if not isinstance(goal, dict):
            errors.append(f"goals[{index}] is not an object")
            continue
        goal_id = goal.get("id")
        status = goal.get("status")
        title = goal.get("title")
        if not goal_id or not isinstance(goal_id, str):
            errors.append(f"goals[{index}].id is required")
        elif goal_id in seen:
            errors.append(f"duplicate goal id: {goal_id}")
        else:
            seen.add(goal_id)
        if status not in VALID_STATUSES:
            errors.append(f"goal {goal_id or index} has invalid status: {status}")
        if not title or not isinstance(title, str):
            errors.append(f"goal {goal_id or index} must have a title")
        if "success_criteria" in goal and not isinstance(goal["success_criteria"], list):
            errors.append(f"goal {goal_id or index}.success_criteria must be a list")
        if "required_tools" in goal and not isinstance(goal["required_tools"], list):
            errors.append(f"goal {goal_id or index}.required_tools must be a list")
    if not goals:
        warnings.append("Queue has no goals")
    ok = not errors
    return result("queue_check", ok, "Queue is valid" if ok else "Queue validation failed", errors, warnings, {"goal_count": len(goals)})
