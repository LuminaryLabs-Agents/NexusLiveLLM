from __future__ import annotations

from pathlib import Path
from typing import Any

from .common import harness_root, read_json, write_json, ledger, utc_id


def capsule_for(entry: dict[str, Any], fate: str = "evaluated") -> dict[str, Any]:
    game_id = str(entry.get("id"))
    score = int(entry.get("score", 0) or 0)
    breakdown = entry.get("score_breakdown", {})
    text = (str(entry.get("title", game_id)) + " " + str(entry.get("prompt", "")) + " " + str(entry.get("folder", ""))).lower()
    features = []
    for key, label in [
        ("three", "three.js renderer host"),
        ("open", "open world exploration"),
        ("kit", "kit builder surface"),
        ("dsk", "domain service kit modeling"),
        ("ledger", "ledger-driven observability"),
        ("action", "bounded action menu"),
        ("context", "context injection panel"),
    ]:
        if key in text:
            features.append(label)
    promoted = []
    if breakdown.get("capability_contribution", 0) >= 10:
        promoted.append("capability.surface.candidate")
    if breakdown.get("debuggability", 0) >= 6:
        promoted.append("debug.host.visibility")
    if breakdown.get("tools", 0) >= 20:
        promoted.append("static.output.contract")
    issues = []
    if score < 55:
        issues.append("low deterministic score; use as fail-forward lesson")
    if not entry.get("files", {}).get("game.js"):
        issues.append("missing game.js")
    return {
        "game_id": game_id,
        "fate": fate,
        "score": score,
        "source_prompt": entry.get("source_prompt") or entry.get("prompt_file"),
        "features_attempted": features,
        "features_promoted_to_memory": promoted,
        "issues": issues,
        "lessons": [
            "Renderer presents state; kits and DSKs own meaning.",
            "Expose GameHost/debug state when possible.",
            "Carry forward stable manifest and launcher behavior."
        ],
        "created_at": utc_id()
    }


def compress(scored: list[dict[str, Any]], run_dir: Path) -> list[dict[str, Any]]:
    capsules = [capsule_for(entry, entry.get("fate", "evaluated")) for entry in scored]
    write_json(run_dir / "learning" / "game-capsules.json", {"capsules": capsules})
    for capsule in capsules:
        ledger("game-capsule-ledger.jsonl", {"time": utc_id(), "event": "game.capsule", "game_id": capsule["game_id"], "score": capsule["score"], "fate": capsule["fate"]})
    memory_path = harness_root() / "state" / "project-memory.json"
    memory = read_json(memory_path, {"version": 1, "latest_lessons": [], "known_failure_patterns": [], "stable_capabilities": [], "candidate_capabilities": []})
    latest_lessons = []
    for capsule in sorted(capsules, key=lambda c: c.get("score", 0), reverse=True)[:5]:
        latest_lessons.extend(capsule.get("lessons", [])[:2])
    memory["latest_lessons"] = list(dict.fromkeys(latest_lessons))[:12]
    memory["updated_at"] = utc_id()
    write_json(memory_path, memory)
    ledger("project-ledger.jsonl", {"time": utc_id(), "event": "project.memory.updated", "lessons": len(memory["latest_lessons"])})
    return capsules
