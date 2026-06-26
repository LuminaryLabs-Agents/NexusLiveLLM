from __future__ import annotations

import argparse
import os
from pathlib import Path

from .common import harness_root, write_json, ledger, utc_id
from . import repo_context, context_injector, game_catalog, game_scorer, learning_compressor, capability_tracker, purge_agent, apply_purge, launcher_renderer
from .run_tools import run_all


def run(run_dir: Path, prompt: str) -> dict:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "context").mkdir(exist_ok=True)
    (run_dir / "learning").mkdir(exist_ok=True)
    (run_dir / "purge").mkdir(exist_ok=True)
    (run_dir / "tools").mkdir(exist_ok=True)
    context = repo_context.collect(run_dir, prompt)
    injections = context_injector.inject_from_run(run_dir)
    entries = game_catalog.scan()
    game_catalog.write_index(entries)
    scored = game_scorer.score_all(entries)
    capsules = learning_compressor.compress(scored, run_dir)
    caps_state = capability_tracker.update(capsules, run_dir)
    plan = purge_agent.plan(scored, run_dir)
    result = apply_purge.apply(plan, scored, run_dir)
    entries2 = game_catalog.scan()
    scored2 = game_scorer.score_all(entries2)
    launcher_renderer.render(scored2, plan, run_dir)
    final_tools = run_all()
    write_json(run_dir / "tools" / "post-run-tool-results.json", final_tools)
    summary = {
        "ok": bool(final_tools.get("ok")),
        "run_dir": str(run_dir),
        "context_capsules": len(context.get("capsules", [])),
        "injections": len(injections.get("active_injections", [])),
        "games_scored": len(scored),
        "capsules": len(capsules),
        "capabilities": len(caps_state.get("capabilities", [])),
        "purge_decisions": len(plan.get("decisions", [])),
        "hidden_game_ids": result.get("hidden_game_ids", []),
        "post_run_tools_ok": bool(final_tools.get("ok")),
    }
    write_json(run_dir / "post-run-summary.json", summary)
    ledger("project-ledger.jsonl", {"time": utc_id(), "event": "post_run.completed", **summary})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="LiveHarness post-run learning/purge pipeline")
    parser.add_argument("--run-dir", default=os.environ.get("LIVEHARNESS_RUN_DIR", ""))
    parser.add_argument("--prompt-file", default="")
    args = parser.parse_args()
    harness = harness_root()
    run_dir = Path(args.run_dir) if args.run_dir else harness / "runs" / (os.environ.get("LIVEHARNESS_RUN_ID") or utc_id())
    if not run_dir.is_absolute():
        run_dir = harness / run_dir
    prompt = os.environ.get("GAME_PROMPT", "")
    if args.prompt_file:
        p = Path(args.prompt_file)
        if p.exists():
            prompt = p.read_text(encoding="utf-8", errors="replace")
    if not prompt:
        prompt_doc = run_dir / "input" / "prompt.md"
        prompt = prompt_doc.read_text(encoding="utf-8", errors="replace") if prompt_doc.exists() else ""
    print(run(run_dir, prompt))


if __name__ == "__main__":
    main()
