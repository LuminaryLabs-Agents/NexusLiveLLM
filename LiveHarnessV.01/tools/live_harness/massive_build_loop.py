from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import os
import shutil

from .common import harness_root, repo_root, read_json, write_json, write_text, ledger, utc_id
from .master_interpreter import build_master_interpretation
from .action_ast_runner import ensure_action_ast
from .swarm_planner import plan_swarm
from .async_slot_dispatcher import run_dispatch
from .slot_validator import validate_slots
from .slot_reconciler import reconcile
from .sandbox_write_set_apply import apply_to_sandbox
from .massive_validation_runner import validate_sandbox
from .repair_plan_builder import build_repair_plan
from .final_public_validation import run_final_public_validation
from .product_brief import sanitize_public_text

LEGACY_MARKERS = ["NexusLiveLLM", "nvidia/nemotron", "living language model inside a GitHub Pages arcade launcher", "Generated Game Ladder"]


def _resolve_run_dir(run_id: str, run_dir_arg: str) -> Path:
    run_dir = Path(run_dir_arg) if run_dir_arg else harness_root() / "runs" / run_id
    if not run_dir.is_absolute():
        run_dir = harness_root() / run_dir
    return run_dir


def _load_prompt(run_dir: Path, prompt_file: str = "") -> tuple[str, str]:
    if prompt_file:
        p = Path(prompt_file)
        if not p.is_absolute():
            p = repo_root() / p
        if p.exists():
            return p.read_text(encoding="utf-8", errors="replace"), str(p.relative_to(repo_root()))
    prompt_doc = run_dir / "input" / "prompt.md"
    if prompt_doc.exists():
        return prompt_doc.read_text(encoding="utf-8", errors="replace"), str(prompt_doc.relative_to(harness_root()))
    return os.environ.get("GAME_PROMPT", "Build a self-aligned voxel DSK lab."), "env:GAME_PROMPT"


def _prepare_run(run_dir: Path, prompt: str, prompt_ref: str) -> None:
    for child in ["input", "logs", "status", "validation", "swarm", "write-sets/proposed", "write-sets/applied-to-sandbox", "write-sets/rejected", "self-alignment", "loops", "sandbox", "tools", "review", "learning", "gates"]:
        (run_dir / child).mkdir(parents=True, exist_ok=True)
    write_text(run_dir / "input" / "prompt.md", prompt)
    write_text(run_dir / "input" / "prompt-ref.txt", prompt_ref + "\n")


def _render_launcher(manifest: list[dict[str, Any]]) -> None:
    docs = repo_root() / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    cards = []
    for index, item in enumerate(manifest, start=1):
        title = sanitize_public_text(str(item.get("title") or item.get("id")))
        summary = sanitize_public_text(str(item.get("summary") or item.get("prompt") or ""))
        url = str(item.get("url") or "#")
        cards.append(f"<article class='game-card'><div class='rank'>#{index:02d}</div><div><h2>{title}</h2><p>{summary}</p><p class='score'>Score {item.get('score', 100)}</p><a class='play' href='{url}'>Play build</a></div></article>")
    latest = manifest[0].get("url", "#") if manifest else "#"
    index_html = "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>NexusRealtime KitBuilder03</title><link rel='stylesheet' href='./launcher.css'></head><body><main class='shell'><section class='hero'><p class='eyebrow'>one-commit sandbox build</p><h1>KitBuilder03 Active Builds</h1><p class='lede'>Every active build is promoted from a sandbox only after file-filter validation, DSK boundary checks, and self-alignment.</p><a class='primary' href='" + latest + "'>Play top build</a><a class='secondary' href='./cleanup.html'>Review cleanup ledger</a></section><section class='ladder'>" + ("".join(cards) if cards else "<p>No active builds yet.</p>") + "</section></main></body></html>"
    css = ":root{color-scheme:dark;font-family:system-ui,sans-serif}body{margin:0;background:#06110c;color:#eefbf1}.shell{width:min(1120px,calc(100% - 32px));margin:auto;padding:48px 0}.hero,.game-card,.cleanup-card{border:1px solid rgba(157,255,190,.22);background:linear-gradient(135deg,rgba(6,28,18,.9),rgba(10,18,32,.84));border-radius:28px;padding:24px;margin:16px 0}.eyebrow{color:#afffc6;text-transform:uppercase;letter-spacing:.16em;font-weight:900}.lede{max-width:820px;color:#cbd8d0;font-size:18px}.primary,.secondary,.play{display:inline-flex;margin:10px 10px 0 0;padding:11px 15px;border-radius:999px;text-decoration:none;font-weight:900}.primary,.play{background:#bfffd2;color:#06110b}.secondary{border:1px solid rgba(255,255,255,.2);color:#eefbf1}.game-card{display:grid;grid-template-columns:74px 1fr;gap:18px}.rank{font-size:28px;font-weight:1000;color:#bfffd2}.score{color:#9fffc0;font-weight:900}table{border-collapse:collapse;width:100%;margin-top:16px}td,th{border:1px solid rgba(255,255,255,.18);padding:8px;text-align:left}th{background:rgba(191,255,210,.14)}"
    cleanup = "<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Cleanup</title><link rel='stylesheet' href='./launcher.css'></head><body><main class='shell'><section class='hero'><p class='eyebrow'>Cleanup and Learning</p><h1>Rolling Gallery</h1><p class='lede'>The public manifest keeps at most ten active builds. Older outputs are retained as run artifacts or capsules before they are removed from public navigation.</p><a class='secondary' href='./index.html'>Back to launcher</a></section></main></body></html>"
    write_text(docs / "index.html", index_html)
    write_text(docs / "launcher.css", css)
    write_text(docs / "cleanup.html", cleanup)


def _is_legacy(item: dict[str, Any]) -> bool:
    text = json.dumps(item).lower()
    return any(marker.lower() in text for marker in LEGACY_MARKERS)


def promote_candidate(run_dir: Path, write_set: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(write_set.get("candidate_id"))
    sandbox_game = run_dir / "sandbox" / "docs" / "games" / candidate_id
    public_game = repo_root() / "docs" / "games" / candidate_id
    if public_game.exists():
        shutil.rmtree(public_game)
    public_game.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(sandbox_game, public_game)
    docs = repo_root() / "docs"
    manifest_path = docs / "games.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else []
    except json.JSONDecodeError:
        manifest = []
    manifest = [item for item in manifest if isinstance(item, dict) and str(item.get("id")) != candidate_id and not _is_legacy(item)]
    entry = {"id": candidate_id, "title": sanitize_public_text(str(write_set.get("title") or "Voxel DSK Lab")), "summary": sanitize_public_text(str(write_set.get("summary") or "Sandbox-validated NexusRealtime experiment.")), "prompt": sanitize_public_text(str(write_set.get("summary") or "")), "url": f"games/{candidate_id}/", "score": 100 if validation.get("ok") else 50, "status": "active", "visibility": "public", "promoted_at": utc_id()}
    manifest.insert(0, entry)
    manifest = manifest[:10]
    write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")
    _render_launcher(manifest)
    result = {"candidate_id": candidate_id, "public_path": str(public_game.relative_to(repo_root())), "manifest_entries": len(manifest), "promoted_at": utc_id()}
    write_json(run_dir / "status" / "promotion-result.json", result)
    ledger("artifact-ledger.jsonl", {"time": utc_id(), "event": "candidate.promoted", **result})
    return result


def _write_alignment_round(run_dir: Path, loop_index: int, validation: dict[str, Any]) -> dict[str, Any]:
    decision = "ADVANCE" if validation.get("ok") else "REVISE"
    result = {"schema": "liveharness.self-alignment-result.v1", "phase": "massive-build-loop", "loop_index": loop_index, "decision": decision, "alignment_score": 92 if decision == "ADVANCE" else 64, "remaining_issues": validation.get("failed_filters", []), "strengths": validation.get("passed_filters", []), "loopback_target": validation.get("loopback", {}).get("target") if validation.get("loopback") else None, "completed_at": utc_id()}
    write_json(run_dir / "self-alignment" / f"round-{loop_index:03d}.json", result)
    write_json(run_dir / "self-alignment" / "final-self-review.json", result)
    ledger("alignment-ledger.jsonl", {"time": utc_id(), "event": "massive.self_alignment", "loop_index": loop_index, "decision": decision})
    return result


def _update_learning(run_dir: Path, candidate_id: str, final_ok: bool) -> None:
    memory_path = harness_root() / "state" / "project-memory.json"
    memory = read_json(memory_path, {"version": 1, "latest_lessons": []})
    memory["updated_at"] = utc_id()
    memory["latest_massive_build"] = {"run_id": run_dir.name, "candidate_id": candidate_id, "ok": final_ok}
    lessons = memory.setdefault("latest_lessons", [])
    for lesson in ["Sandbox-first writes prevent half-broken public output.", "Renderer should present state while domains own commands/events.", "Single final commit keeps workflow history readable."]:
        if lesson not in lessons:
            lessons.insert(0, lesson)
    memory["latest_lessons"] = lessons[:12]
    write_json(memory_path, memory)
    caps_path = harness_root() / "state" / "capability-ledger.json"
    caps = read_json(caps_path, {"version": 1, "capabilities": []})
    existing = {c.get("id"): c for c in caps.get("capabilities", []) if isinstance(c, dict)}
    for cap in ["massive.sandbox.build-loop", "public-output.membrane", "dsk.build-break.trace", "gamehost.debug.surface", "single-final-commit.policy"]:
        item = existing.get(cap) or {"id": cap, "status": "candidate", "evidence": []}
        item.setdefault("evidence", []).append(f"{run_dir.name} ok={final_ok}")
        if final_ok:
            item["status"] = "stable" if cap in {"public-output.membrane", "single-final-commit.policy"} else item.get("status", "candidate")
        existing[cap] = item
    caps["capabilities"] = sorted(existing.values(), key=lambda c: c.get("id", ""))
    caps["updated_at"] = utc_id()
    write_json(caps_path, caps)


def run_massive_build(run_id: str, run_dir: Path, prompt: str, prompt_ref: str, max_workers: int, max_loops: int, max_parallel: int) -> dict[str, Any]:
    _prepare_run(run_dir, prompt, prompt_ref)
    build_master_interpretation(prompt, run_dir, prompt_ref)
    ensure_action_ast(run_dir, "40-prototype")
    final_validation: dict[str, Any] = {"ok": False, "failed_filters": ["not-run"]}
    final_write_set: dict[str, Any] = {}
    final_alignment: dict[str, Any] = {}
    promotion: dict[str, Any] | None = None
    for loop_index in range(1, max_loops + 1):
        loop_started = utc_id()
        plan_swarm(run_dir, run_id, max_workers, loop_index)
        dispatch = run_dispatch(run_dir, max_parallel)
        slot_validation = validate_slots(run_dir)
        final_write_set = reconcile(run_dir, run_id)
        sandbox_result = apply_to_sandbox(final_write_set, run_dir)
        final_validation = validate_sandbox(run_dir, final_write_set)
        final_alignment = _write_alignment_round(run_dir, loop_index, final_validation)
        loop_state = {"schema": "liveharness.loop-state.v1", "loop_index": loop_index, "started_at": loop_started, "completed_at": utc_id(), "swarm": dispatch, "slot_validation": slot_validation, "write_set": {"files": len(final_write_set.get("files", [])), "applied_to_sandbox": sandbox_result.get("ok")}, "validation": {"ok": final_validation.get("ok"), "failed": final_validation.get("failed_filters", [])}, "self_alignment": final_alignment, "next": {"action": "promote" if final_validation.get("ok") and final_alignment.get("decision") == "ADVANCE" else "repair", "target": final_validation.get("loopback", {}).get("target") if final_validation.get("loopback") else "promote_candidate"}}
        write_json(run_dir / "loops" / f"loop-{loop_index:03d}.json", loop_state)
        if final_validation.get("ok") and final_alignment.get("decision") == "ADVANCE":
            promotion = promote_candidate(run_dir, final_write_set, final_validation)
            break
        build_repair_plan(run_dir, loop_index, final_validation)
    if promotion:
        public_validation = run_final_public_validation(run_dir)
    else:
        public_validation = {"ok": False, "failed": ["candidate-not-promoted"]}
    candidate_id = str(final_write_set.get("candidate_id", ""))
    final_ok = bool(promotion and public_validation.get("ok"))
    _update_learning(run_dir, candidate_id, final_ok)
    status = {"schema": "liveharness.final-status.v1", "run_id": run_id, "status": "success" if final_ok else "failure_with_artifacts", "single_commit_mode": True, "candidate_id": candidate_id, "public_path": promotion.get("public_path") if promotion else None, "validation_ok": final_ok, "loops_attempted": len(list((run_dir / "loops").glob("loop-*.json"))), "completed_at": utc_id()}
    write_json(run_dir / "status" / "final-status.json", status)
    if not final_ok:
        write_json(run_dir / "status" / "failure.json", {"status": status, "validation": final_validation, "public_validation": public_validation})
    report = f"# Massive Build Final Report\n\n- Run ID: `{run_id}`\n- Prompt: `{prompt_ref}`\n- Candidate: `{candidate_id}`\n- Status: `{status['status']}`\n- Loops attempted: `{status['loops_attempted']}`\n- Public path: `{status['public_path']}`\n- Validation OK: `{final_ok}`\n\n## Failed Filters\n\n{', '.join(final_validation.get('failed_filters', [])) or 'none'}\n"
    write_text(run_dir / "final-report.md", report)
    ledger("build-ledger.jsonl", {"time": utc_id(), "event": "massive_build.completed", "run_id": run_id, "ok": final_ok, "candidate_id": candidate_id})
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the sandbox-first one-commit massive build loop.")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--prompt-file", default="")
    parser.add_argument("--max-workers", type=int, default=16)
    parser.add_argument("--max-loops", type=int, default=4)
    parser.add_argument("--max-parallel", type=int, default=16)
    parser.add_argument("--single-commit-mode", default="true")
    args = parser.parse_args()
    run_id = args.run_id or utc_id() + "-massive-build"
    run_dir = _resolve_run_dir(run_id, args.run_dir)
    prompt, prompt_ref = _load_prompt(run_dir, args.prompt_file)
    status = run_massive_build(run_id, run_dir, prompt, prompt_ref, args.max_workers, args.max_loops, args.max_parallel)
    print(json.dumps(status, indent=2))
    if status.get("status") != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
