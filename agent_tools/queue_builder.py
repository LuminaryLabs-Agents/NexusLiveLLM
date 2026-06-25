from __future__ import annotations

from datetime import datetime, timezone
import os

from openai import OpenAI

from .common import extract_json_object, load_json, read_text, save_json, write_text
from .queue_check import run as queue_check_run


def main() -> None:
    api_key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("Missing NVIDIA_API_KEY secret")

    model = os.environ.get("NVIDIA_MODEL", "").strip() or "nvidia/nemotron-3-ultra-550b-a55b"
    idea = os.environ.get("QUEUE_IDEA", "").strip()
    if not idea:
        idea = "Build the repo into a YAML-driven LLM build harness with a queue, tests, and a layered browser game template."

    goal = read_text(".agent/goal.md", "")
    workflow = read_text(".agent/workflow.md", "")
    existing_queue = load_json(".agent/queue.json", {})
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    run_dir = f".agent/runs/{run_id}"

    request = {
        "schema_version": 1,
        "mode": "queue_builder",
        "idea": idea,
        "goal_md": goal,
        "workflow_md": workflow,
        "existing_queue": existing_queue,
        "requirements": [
            "Return only a JSON object.",
            "Create or update .agent/queue.json.",
            "Use goal statuses queued, active, blocked, complete, or failed.",
            "Include run_policy with max_goals_per_run, max_turns_per_goal, max_total_turns, and commit_strategy.",
            "Each goal needs id, status, priority, title, description, success_criteria, required_tools, and progress.",
            "Prefer small auditable goals that can be accomplished by bounded turns."
        ],
    }
    save_json(f"{run_dir}/queue-builder-request.json", request)

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You build structured agent work queues. Return only valid JSON."},
            {"role": "user", "content": str(request)},
        ],
        temperature=0.45,
        top_p=0.95,
        max_tokens=8192,
        extra_body={"chat_template_kwargs": {"enable_thinking": True}, "reasoning_budget": 4096},
    )
    raw = completion.choices[0].message.content or ""
    save_json(f"{run_dir}/queue-builder-response.raw.json", {"raw": raw})
    queue = extract_json_object(raw)

    if "version" not in queue:
        queue["version"] = 1
    if "goals" not in queue or not isinstance(queue["goals"], list):
        raise SystemExit("Queue builder response did not contain a goals list")
    if "run_policy" not in queue:
        queue["run_policy"] = {"max_goals_per_run": 7, "max_turns_per_goal": 6, "max_total_turns": 30, "commit_strategy": "single_commit_at_end"}

    save_json(".agent/queue.json", queue)
    save_json(f"{run_dir}/queue-builder-response.json", queue)
    check = queue_check_run({})
    save_json(f"{run_dir}/queue-builder-validation.json", check)
    if not check.get("ok"):
        raise SystemExit("Generated queue failed validation")

    write_text(".agent/LATEST.md", f"# Latest Nexus Queue Builder Run\n\nRun: `{run_id}`\n\nModel: `{model}`\n\nGoals: {len(queue.get('goals', []))}\n")


if __name__ == "__main__":
    main()
