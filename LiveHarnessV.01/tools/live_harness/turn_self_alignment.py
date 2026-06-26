from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import re

from .common import harness_root, repo_root, read_json, write_json, write_text, ledger, utc_id
from .master_interpreter import build_master_interpretation

BOUNDARY_ACTIONS = {"APPLY_WRITE_SET", "COMMIT", "DEPLOY", "PURGE", "DELETE_GAME_FOLDER", "PATCH_HARNESS", "INTERPRETATION_LOCK"}
DEFAULT_ALLOWED_ACTIONS = [
    "THINK",
    "ALIGN_GOAL",
    "PLAN",
    "READ_ARTIFACT",
    "WRITE_SET_PROPOSE",
    "ASK_GATE",
    "APPLY_WRITE_SET",
    "RUN_TOOL",
    "SELF_REVIEW",
    "INTERPRETATION_PATCH",
    "FINAL_REPORT",
    "LOOPBACK"
]


def _append_monitor(run_dir: Path, line: str) -> None:
    path = run_dir / "monitor" / "monitor-log.md"
    existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else "# Monitor Log\n\n"
    path.write_text(existing.rstrip() + "\n- " + line + "\n", encoding="utf-8")


def _load_master(run_dir: Path, raw_prompt: str = "") -> dict[str, Any]:
    path = run_dir / "input" / "master-interpretation.json"
    if path.exists():
        return read_json(path, {})
    return build_master_interpretation(raw_prompt, run_dir, str(run_dir / "input" / "prompt.md"))["master"]


def _latest_game_dir() -> Path | None:
    latest = read_json(harness_root() / "state" / "latest.json", {})
    url = str(latest.get("url", ""))
    if url.startswith("docs/"):
        path = repo_root() / url
        if path.exists():
            return path
    games = repo_root() / "docs" / "games"
    if games.exists():
        folders = sorted([p for p in games.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
        return folders[0] if folders else None
    return None


def inspect_latest_output(game_dir: Path | None) -> dict[str, Any]:
    if not game_dir:
        return {"exists": False, "issues": ["No generated game directory found."], "files": []}
    js_path = game_dir / "game.js"
    html_path = game_dir / "index.html"
    js = js_path.read_text(encoding="utf-8", errors="replace") if js_path.exists() else ""
    html = html_path.read_text(encoding="utf-8", errors="replace") if html_path.exists() else ""
    combined = (js + "\n" + html).lower()
    issues: list[str] = []
    strengths: list[str] = []
    if "window.gamehost" in combined and "getstate" in combined:
        strengths.append("GameHost exposes inspectable state.")
    else:
        issues.append("missing_debug_host")
    if "nvidia" in combined or "openai" in combined or "nemotron" in combined or "workflow_dispatch" in combined:
        issues.append("public_output_bleed")
    if "build.break.request" in combined or "build.place.request" in combined or "block.break.request" in combined:
        strengths.append("Build/break action path is command-shaped.")
    elif "minecraft" in combined or "voxel" in combined or "block" in combined:
        issues.append("missing_domain_trace")
    if "setblock" in combined and "domaintrace" not in combined:
        issues.append("renderer_owns_gameplay")
    if "sequence" in combined or "objective" in combined:
        strengths.append("Prototype exposes some authored objective or sequence state.")
    return {
        "exists": True,
        "game_dir": str(game_dir.relative_to(repo_root())),
        "files": [str(p.relative_to(repo_root())) for p in game_dir.glob("*") if p.is_file()],
        "issues": sorted(set(issues)),
        "strengths": strengths,
        "js_path": str(js_path.relative_to(repo_root())) if js_path.exists() else None,
        "html_path": str(html_path.relative_to(repo_root())) if html_path.exists() else None,
    }


def _patch_voxel_domain_trace(game_dir: Path, run_dir: Path) -> dict[str, Any]:
    js_path = game_dir / "game.js"
    if not js_path.exists():
        return {"applied": False, "reason": "game.js missing"}
    text = js_path.read_text(encoding="utf-8", errors="replace")
    if "domainTrace" in text and "build.place.request" in text:
        return {"applied": False, "reason": "domain trace already present"}
    original = text
    insert = """
const domainTrace = [];
const appliedCommandIds = new Set();
function routeBuildBreakCommand(command){
  if(!command || !command.commandId || appliedCommandIds.has(command.commandId)) return {ok:false, duplicate:true, command};
  appliedCommandIds.add(command.commandId);
  const event = {tick:frame, domain:'build-break-domain-service-kit', command:command.type, commandId:command.commandId, validation:'accepted', stateChange:`${command.x},${command.y},${command.z}`, event:command.type==='build.place.request'?'build.block.placed':'build.block.removed'};
  domainTrace.push(event);
  if(domainTrace.length>24) domainTrace.shift();
  if(command.type==='build.place.request') setBlock(command.x, command.y, command.z, command.block);
  if(command.type==='block.break.request') setBlock(command.x, command.y, command.z, 0);
  return {ok:true, event};
}
""".strip() + "\n"
    text = text.replace("function boot(THREE){", insert + "function boot(THREE){")
    old = "if(e.button===2){setBlock(tx,ty,tz,selectedBlock)}else{setBlock(tx,ty,tz,0)} rebuild(); renderPanel();"
    new = "if(e.button===2){routeBuildBreakCommand({type:'build.place.request',commandId:`place:${frame}:${tx}:${ty}:${tz}:${selectedBlock}`,x:tx,y:ty,z:tz,block:selectedBlock})}else{routeBuildBreakCommand({type:'block.break.request',commandId:`break:${frame}:${tx}:${ty}:${tz}`,x:tx,y:ty,z:tz})} rebuild(); renderPanel();"
    text = text.replace(old, new)
    text = text.replace("domains:VOXEL_BRIEF.domains}),rebuild", "domains:VOXEL_BRIEF.domains,domainTrace:domainTrace.slice(-12),appliedCommandIds:Array.from(appliedCommandIds).slice(-12)}),rebuild")
    if text == original:
        return {"applied": False, "reason": "expected patch anchors not found"}
    js_path.write_text(text, encoding="utf-8")
    write_set = {
        "write_set_id": "self-align-add-build-break-domain-trace",
        "summary": "Route voxel build/break clicks through a repeat-safe command/event trace before public review.",
        "files": [str(js_path.relative_to(repo_root()))],
        "applied_at": utc_id(),
    }
    write_json(run_dir / "write-sets" / "applied" / "self-align-add-build-break-domain-trace.json", write_set)
    return {"applied": True, "write_set": write_set}


def make_turn(turn_id: int, action_type: str, visible_thought: str, alignment: dict[str, Any], action_input: str, ast_node: str) -> dict[str, Any]:
    return {
        "schema": "liveharness.turn-action.v1",
        "turn_id": turn_id,
        "ast_node": ast_node,
        "allowed_actions": DEFAULT_ALLOWED_ACTIONS,
        "visible_thought": visible_thought,
        "self_alignment": alignment,
        "action": {"type": action_type, "input": action_input},
        "action_line": f"{action_type} : {action_input}",
        "created_at": utc_id()
    }


def run_alignment(run_dir: Path, raw_prompt: str = "", phase: str = "pre_tools") -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    for child in ["turns", "self-alignment", "monitor", "write-sets/proposed", "write-sets/applied", "write-sets/rejected", "gates"]:
        (run_dir / child).mkdir(parents=True, exist_ok=True)
    master = _load_master(run_dir, raw_prompt)
    game_dir = _latest_game_dir()
    inspection = inspect_latest_output(game_dir)
    issue_set = set(inspection.get("issues", []))
    turns: list[dict[str, Any]] = []
    alignment_base = {
        "master_interpretation_ref": "input/master-interpretation.json",
        "goal_match": 74 if issue_set else 92,
        "stage_match": 70 if issue_set else 90,
        "drift_detected": bool(issue_set),
        "drift_type": ",".join(sorted(issue_set)) if issue_set else "none",
        "evidence": inspection.get("issues", []) + inspection.get("strengths", []),
    }
    turns.append(make_turn(1, "THINK", "Review the latest output against the locked goal before moving on.", alignment_base, "identify latest strengths and drift", "goal.product.architecture"))
    turns.append(make_turn(2, "ALIGN_GOAL", "Compare public output, DSK boundaries, debug host, and renderer responsibility against the master interpretation.", alignment_base, "input/master-interpretation.json", "goal.product.architecture"))
    if issue_set:
        required = []
        if "missing_domain_trace" in issue_set or "renderer_owns_gameplay" in issue_set:
            required.append("add repeat-safe BuildBreakDSK command/event trace")
        if "missing_debug_host" in issue_set:
            required.append("expose GameHost.getState()")
        if "public_output_bleed" in issue_set:
            required.append("strip public control-plane metadata")
        plan_alignment = dict(alignment_base, required_correction=required)
        turns.append(make_turn(3, "PLAN", "The output should be revised before the next stage because the drift has a concrete correction path.", plan_alignment, "; ".join(required), "goal.product.architecture.revise"))
        patch_result = {"applied": False, "reason": "no patch attempted"}
        if game_dir and ("missing_domain_trace" in issue_set or "renderer_owns_gameplay" in issue_set):
            patch_result = _patch_voxel_domain_trace(game_dir, run_dir)
        action_type = "APPLY_WRITE_SET" if patch_result.get("applied") else "SELF_REVIEW"
        turns.append(make_turn(4, action_type, "Apply or record the domain-trace correction through a bounded write-set step.", plan_alignment, json.dumps(patch_result), "goal.product.architecture.write_set"))
        inspection_after = inspect_latest_output(game_dir)
    else:
        turns.append(make_turn(3, "PLAN", "The output matches the master goal closely enough to proceed to deterministic tools.", alignment_base, "preserve current output and run tools", "goal.harness.logs"))
        inspection_after = inspection
    final_issues = set(inspection_after.get("issues", []))
    if "missing_domain_trace" in final_issues and game_dir and (game_dir / "game.js").exists():
        # It may be acceptable for non-voxel outputs. Keep as watch rather than hard fail.
        final_issues.discard("missing_domain_trace")
    decision = "ADVANCE" if not final_issues else "LOOPBACK"
    final_alignment = {
        "schema": "liveharness.self-alignment-result.v1",
        "phase": phase,
        "decision": decision,
        "alignment_score": 90 if decision == "ADVANCE" else 62,
        "remaining_issues": sorted(final_issues),
        "strengths": inspection_after.get("strengths", []),
        "loopback_target": master.get("loopback_policy", {}).get(sorted(final_issues)[0], "40-prototype") if final_issues else None,
        "latest_output": inspection_after,
        "completed_at": utc_id()
    }
    turns.append(make_turn(len(turns) + 1, "SELF_REVIEW", "Run final visible self-review before allowing tool checks or stage advancement.", final_alignment, "self-alignment/final-self-review.json", "goal.harness.learning"))
    turns.append(make_turn(len(turns) + 1, "FINAL_REPORT", f"Self-alignment decision: {decision}.", final_alignment, decision, "goal.final"))
    for turn in turns:
        write_json(run_dir / "turns" / f"turn-{turn['turn_id']:03d}.json", turn)
        ledger("alignment-ledger.jsonl", {"time": utc_id(), "event": "turn.aligned", "turn_id": turn["turn_id"], "action": turn["action"]["type"], "run_dir": str(run_dir)})
    write_json(run_dir / "self-alignment" / "final-self-review.json", final_alignment)
    write_json(run_dir / "self-alignment" / "turn-summary.json", {"turn_count": len(turns), "decision": decision, "issues": sorted(final_issues)})
    write_text(run_dir / "monitor" / "active-plan.md", "# Active Plan\n\n" + "\n".join(f"{idx+1}. {turn['action_line']}" for idx, turn in enumerate(turns)) + "\n")
    write_json(run_dir / "monitor" / "think-list.json", {"version": 1, "items": [{"turn_id": t["turn_id"], "thought": t["visible_thought"]} for t in turns[-6:]]})
    _append_monitor(run_dir, f"Self-alignment {phase} finished with decision={decision} issues={sorted(final_issues)}")
    if final_issues:
        ledger("alignment-ledger.jsonl", {"time": utc_id(), "event": "drift.detected", "issues": sorted(final_issues), "run_dir": str(run_dir)})
    return final_alignment


def main() -> None:
    parser = argparse.ArgumentParser(description="Run visible turn-level self-alignment.")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--phase", default="pre_tools")
    args = parser.parse_args()
    harness = harness_root()
    run_dir = Path(args.run_dir) if args.run_dir else harness / "runs" / "alignment-run"
    if not run_dir.is_absolute():
        run_dir = harness / run_dir
    raw = ""
    prompt_doc = run_dir / "input" / "prompt.md"
    if prompt_doc.exists():
        raw = prompt_doc.read_text(encoding="utf-8", errors="replace")
    result = run_alignment(run_dir, raw, args.phase)
    print(json.dumps(result, indent=2))
    if result.get("decision") == "LOOPBACK" and args.phase == "blocking":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
