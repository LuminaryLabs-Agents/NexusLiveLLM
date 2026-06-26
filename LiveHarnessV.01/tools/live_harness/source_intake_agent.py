from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import os
import subprocess

from .common import harness_root, read_json, write_json, write_text, ledger, utc_id
from .repo_capability_classifier import classify_text

DEFAULT_MUST_ANSWER = [
    "What can be imported?",
    "What should only be referenced?",
    "What should become a validation rule?",
    "What should not be copied?",
    "What APIs are stable enough for generated apps?"
]

SEED_TEXT = {
    "nexusrealtime-core": "NexusRealtime exposes createRealtimeGame, createEngine, runtime-kit, domain-service-kit, defineDomainServiceKit, validateDomainServiceKit, SequenceNode, deploySequenceNode, terrain-kit, procedural-kit, navmesh-kit, pathfinding-kit, locomotion-kit, camera-kit, renderers and surfaces. Runtime, Kits, Sequences, Renderer, and Host should stay separated.",
    "nexusrealtime-protokits": "ProtoKits include action-input-kit, terrain-sampler-kit, world-patch-kit, performance-budget-kit, material-palette-kit, instanced-render-kit, render-layer-kit, visual-pipeline-kit, next-ledge-kit, flight-motion-kit, and generic open-world patterns. ProtoKits prove features before promotion to core.",
    "kitbuilder03-local": "KitBuilder03 contains LiveHarness massive build loop, sandbox write-set apply, massive validation runner, public output membrane, DSK boundary filter, renderer boundary filter, GameHost filter, final public validation, docs launcher ownership, run ledgers, state, and generated voxel builds."
}

QUERY_MAP = {
    "nexusrealtime-core": ["createRealtimeGame defineDomainServiceKit", "SequenceNode deploySequenceNode", "terrain-kit procedural-kit"],
    "nexusrealtime-protokits": ["action-input-kit terrain-sampler-kit world-patch-kit", "render-layer visual-pipeline instanced-render", "generic open-world flight kits"],
    "kitbuilder03-local": ["massive_build_loop validation GameHost", "sandbox write-set DSK boundary", "LiveHarness Massive Build"],
}


def _agent_config(agent_id: str) -> dict[str, Any]:
    agents = read_json(harness_root() / "state" / "source-intake-agents.json", {"agents": []}).get("agents", [])
    for agent in agents:
        if agent.get("agent_id") == agent_id:
            return dict(agent)
    raise SystemExit(f"Unknown intake agent: {agent_id}")


def _contract(agent: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "liveharness.source-intake-contract.v1",
        "agent_id": agent["agent_id"],
        "source": {"type": "github_repo", "repo": agent["repo"], "default_branch": "main"},
        "role": agent.get("role"),
        "exploration_task": agent.get("exploration_task"),
        "allowed_uses": agent.get("allowed_uses", []),
        "blocked_paths": [".github/", "node_modules/", "dist/", ".env", "credentials"],
        "must_answer": DEFAULT_MUST_ANSWER,
        "trusted_as_instruction": False
    }


def _gh_search(repo: str, query: str, limit: int = 8) -> list[dict[str, Any]]:
    if not os.environ.get("GH_TOKEN"):
        return []
    cmd = ["gh", "search", "code", query, "--repo", repo, "--json", "path,repository,sha,url", "--limit", str(limit)]
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, timeout=25, check=False)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return [{"kind": "github_error", "repo": repo, "query": query, "stderr": proc.stderr.strip()[:500]}]
    try:
        data = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        data = []
    out = []
    for item in data:
        path = str(item.get("path") or "")
        if any(block in path for block in [".github/", "node_modules/", "dist/", ".env"]):
            continue
        out.append({"kind": "github_code", "repo": repo, "query": query, "path": path, "sha": item.get("sha"), "url": item.get("url")})
    return out


def _seed_capsules(agent_id: str, repo: str) -> list[dict[str, Any]]:
    return classify_text(repo, "seed:intake", SEED_TEXT.get(agent_id, ""))


def run_agent(run_dir: Path, agent_id: str) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    agent = _agent_config(agent_id)
    contract = _contract(agent)
    agent_dir = run_dir / "intake" / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    write_json(agent_dir / "source-contract.json", contract)

    queries = QUERY_MAP.get(agent_id, [agent.get("exploration_task", agent_id)])
    search_plan = {"schema": "liveharness.intake-search-plan.v1", "agent_id": agent_id, "repo": agent["repo"], "queries": queries, "trusted_as_instruction": False}
    write_json(agent_dir / "search-plan.json", search_plan)

    results: list[dict[str, Any]] = []
    for query in queries:
        results.extend(_gh_search(agent["repo"], query))
    write_json(agent_dir / "search-results.json", {"results": results})
    write_json(agent_dir / "fetched-files.json", {"files": [], "note": "Intake currently classifies search hits and seed summaries; raw source is not copied."})

    capsules = _seed_capsules(agent_id, agent["repo"])
    for hit in results[:16]:
        text = " ".join(str(hit.get(k, "")) for k in ["query", "path", "repo"])
        capsules.extend(classify_text(agent["repo"], str(hit.get("path", "unknown")), text))
    # dedupe by id + source path
    seen = set()
    deduped = []
    for cap in capsules:
        key = (cap.get("capability_id"), cap.get("source_path"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cap)
    coverage = {
        "schema": "liveharness.intake-coverage-review.v1",
        "agent_id": agent_id,
        "capsule_count": len(deduped),
        "answers_required": DEFAULT_MUST_ANSWER,
        "ok": len(deduped) > 0,
        "gaps": [] if deduped else ["No capabilities classified."],
        "reviewed_at": utc_id()
    }
    capability_index = {"schema": "liveharness.intake-capability-index.v1", "agent_id": agent_id, "repo": agent["repo"], "capabilities": deduped, "updated_at": utc_id()}
    report = {"schema": "liveharness.final-intake-report.v1", "agent_id": agent_id, "repo": agent["repo"], "role": agent.get("role"), "capability_count": len(deduped), "coverage_ok": coverage["ok"], "trusted_as_instruction": False, "completed_at": utc_id()}
    write_json(agent_dir / "capability-capsules.json", {"capsules": deduped})
    write_json(agent_dir / "capability-index.json", capability_index)
    write_json(agent_dir / "coverage-review.json", coverage)
    write_json(agent_dir / "gaps.json", {"gaps": coverage["gaps"]})
    write_json(agent_dir / "final-intake-report.json", report)
    write_text(agent_dir / "final-intake-report.md", f"# {agent_id}\n\n- Repo: {agent['repo']}\n- Capabilities: {len(deduped)}\n- Coverage OK: {coverage['ok']}\n")
    ledger("context-ledger.jsonl", {"time": utc_id(), "event": "source_intake.completed", "agent_id": agent_id, "repo": agent["repo"], "capabilities": len(deduped)})
    return report


def run_all(run_dir: Path) -> dict[str, Any]:
    agents = [a.get("agent_id") for a in read_json(harness_root() / "state" / "source-intake-agents.json", {"agents": []}).get("agents", [])]
    reports = [run_agent(run_dir, agent_id) for agent_id in agents if agent_id]
    summary = {"schema": "liveharness.source-intake-summary.v1", "reports": reports, "completed_at": utc_id()}
    write_json(run_dir / "intake" / "source-intake-summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a source-specific intake loop.")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--agent", default="all")
    args = parser.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else harness_root() / "runs" / "intake-run"
    if not run_dir.is_absolute():
        run_dir = harness_root() / run_dir
    result = run_all(run_dir) if args.agent == "all" else run_agent(run_dir, args.agent)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
