from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import re
import subprocess

from .common import harness_root, read_json, write_json, ledger, utc_id

HARD_PUBLIC_TERMS = ["NVIDIA", "OpenAI", "nemotron", "reasoning_budget", "workflow_dispatch", "API key", "secret", "GITHUB_TOKEN", "GH_TOKEN", "model tier", "chat.completions"]
LEGACY_TERMS = ["NexusLiveLLM Game Launcher", "Generated Game Ladder", "living language model inside a GitHub Pages arcade launcher", "nvidia/nemotron"]
JS_IMPORT_RE = re.compile(r"(?:import\s+(?:[^'\"]+\s+from\s+)?|import\s*\()\s*['\"]([^'\"]+)['\"]")


def _candidate_dir(run_dir: Path, candidate_id: str) -> Path:
    return run_dir / "sandbox" / "docs" / "games" / candidate_id


def _record(name: str, ok: bool, errors: list[str] | None = None, warnings: list[str] | None = None, data: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"id": name, "ok": ok, "errors": errors or [], "warnings": warnings or [], "data": data or {}}


def path_filter(write_set: dict[str, Any]) -> dict[str, Any]:
    errors = []
    for item in write_set.get("files", []):
        path = str(item.get("path", ""))
        normalized = path.replace("\\", "/").lstrip("/")
        parts = Path(normalized).parts
        if not normalized.startswith("docs/games/"):
            errors.append(f"not under docs/games: {path}")
        if ".." in parts or normalized.startswith("/") or normalized.startswith(".github/") or ".env" in parts or "secret" in normalized.lower():
            errors.append(f"forbidden path: {path}")
    return _record("path-filter", not errors, errors)


def public_output_membrane_filter(candidate_dir: Path) -> dict[str, Any]:
    errors = []
    warnings = []
    for path in candidate_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".css", ".js", ".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        low = text.lower()
        for term in HARD_PUBLIC_TERMS:
            if term.lower() in low:
                errors.append(f"{path.relative_to(candidate_dir)} contains hard public control term: {term}")
        for term in ["agent", "harness", "workflow", "orchestrator", "prompt"]:
            if term in low:
                warnings.append(f"{path.relative_to(candidate_dir)} contains soft term: {term}")
    return _record("public-output-membrane", not errors, errors, warnings)


def file_size_filter(candidate_dir: Path) -> dict[str, Any]:
    files = [p for p in candidate_dir.rglob("*") if p.is_file()]
    errors = []
    total = sum(p.stat().st_size for p in files)
    if len(files) > 80:
        errors.append(f"too many files: {len(files)} > 80")
    if total > 1500 * 1024:
        errors.append(f"candidate too large: {total} bytes")
    for path in files:
        size = path.stat().st_size
        if path.suffix == ".js" and size > 250 * 1024:
            errors.append(f"JS file too large: {path.relative_to(candidate_dir)}")
        if path.name == "index.html" and size > 80 * 1024:
            errors.append("index.html too large")
        if path.name == "style.css" and size > 120 * 1024:
            errors.append("style.css too large")
    return _record("file-size-filter", not errors, errors, data={"files": len(files), "total_bytes": total})


def required_file_filter(candidate_dir: Path) -> dict[str, Any]:
    required = ["index.html", "style.css", "README.md", "src/main.js", "src/host/gameHost.js", "src/domains/buildBreakDomain.js", "src/domains/inventoryDomain.js", "src/domains/movementDomain.js", "src/renderer/threeRenderer.js", "src/runtime/commandQueue.js"]
    missing = [path for path in required if not (candidate_dir / path).exists()]
    return _record("required-file-filter", not missing, [f"missing {path}" for path in missing])


def module_graph_filter(candidate_dir: Path) -> dict[str, Any]:
    errors = []
    for path in candidate_dir.rglob("*.js"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for spec in JS_IMPORT_RE.findall(text):
            if spec.startswith("."):
                target = (path.parent / spec).resolve()
                if not str(target).startswith(str(candidate_dir.resolve())):
                    errors.append(f"import escapes candidate: {path.relative_to(candidate_dir)} -> {spec}")
                elif not target.exists():
                    errors.append(f"missing import: {path.relative_to(candidate_dir)} -> {spec}")
    return _record("module-graph-filter", not errors, errors)


def dsk_boundary_filter(candidate_dir: Path) -> dict[str, Any]:
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in (candidate_dir / "src" / "domains").glob("*.js")) if (candidate_dir / "src" / "domains").exists() else ""
    required = ["build.place.request", "block.break.request", "commandId", "domainTrace", "appliedCommandIds", "getState", "inventory.selected", "movement.input.accepted"]
    missing = [term for term in required if term not in text]
    return _record("dsk-boundary-filter", not missing, [f"missing DSK signal: {term}" for term in missing])


def renderer_boundary_filter(candidate_dir: Path) -> dict[str, Any]:
    renderer_dir = candidate_dir / "src" / "renderer"
    errors = []
    if renderer_dir.exists():
        text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in renderer_dir.glob("*.js"))
        forbidden = ["setBlock(", "build.place.request", "block.break.request", "inventory.select"]
        for term in forbidden:
            if term in text:
                errors.append(f"renderer appears to own gameplay term: {term}")
    return _record("renderer-boundary-filter", not errors, errors)


def gamehost_filter(candidate_dir: Path) -> dict[str, Any]:
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in candidate_dir.rglob("*.js"))
    required = ["window.GameHost", "getState", "movement", "inventory", "buildBreak", "domainTrace", "sequence"]
    missing = [term for term in required if term not in text]
    return _record("gamehost-filter", not missing, [f"missing GameHost field: {term}" for term in missing])


def syntax_filter(candidate_dir: Path) -> dict[str, Any]:
    errors = []
    for path in candidate_dir.rglob("*.js"):
        proc = subprocess.run(["node", "--check", str(path)], text=True, capture_output=True, timeout=30)
        if proc.returncode != 0:
            errors.append(f"{path.relative_to(candidate_dir)}: {proc.stderr.strip() or proc.stdout.strip()}")
    return _record("syntax-filter", not errors, errors)


def ledger_completeness_filter(run_dir: Path) -> dict[str, Any]:
    required = ["input/master-interpretation.json", "input/goal-ast.json", "swarm/swarm-plan.json", "write-sets/final-write-set.json"]
    missing = [path for path in required if not (run_dir / path).exists()]
    worker_status = list((run_dir / "swarm").glob("worker-*/status.json"))
    if not worker_status:
        missing.append("swarm/worker-*/status.json")
    return _record("ledger-completeness-filter", not missing, [f"missing run artifact: {path}" for path in missing])


def legacy_builder_output_filter(root: Path) -> dict[str, Any]:
    files = [root / "index.html", root / "games.json"]
    errors = []
    for path in files:
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            for term in LEGACY_TERMS:
                if term.lower() in text.lower():
                    errors.append(f"legacy launcher term in {path.name}: {term}")
    return _record("legacy-builder-output-filter", not errors, errors)


def validate_sandbox(run_dir: Path, write_set: dict[str, Any]) -> dict[str, Any]:
    candidate_id = str(write_set.get("candidate_id", "candidate"))
    candidate_dir = _candidate_dir(run_dir, candidate_id)
    checks = [
        path_filter(write_set),
        public_output_membrane_filter(candidate_dir),
        file_size_filter(candidate_dir),
        required_file_filter(candidate_dir),
        module_graph_filter(candidate_dir),
        dsk_boundary_filter(candidate_dir),
        renderer_boundary_filter(candidate_dir),
        gamehost_filter(candidate_dir),
        syntax_filter(candidate_dir),
        ledger_completeness_filter(run_dir),
    ]
    failed = [check["id"] for check in checks if not check["ok"]]
    passed = [check["id"] for check in checks if check["ok"]]
    loopback = None
    if failed:
        first = failed[0]
        target = {
            "public-output-membrane": "product-brief-worker",
            "path-filter": "slot-reconciler",
            "module-graph-filter": "slot-reconciler",
            "syntax-filter": "repair-worker",
            "renderer-boundary-filter": "domain-map-worker",
            "dsk-boundary-filter": "build-break-dsk-worker",
            "gamehost-filter": "debug-host-worker",
        }.get(first, "repair-worker")
        loopback = {"target": target, "reason": f"{first} failed"}
    summary = {"schema": "liveharness.validation-summary.v1", "run_id": run_dir.name, "candidate_id": candidate_id, "ok": not failed, "passed_filters": passed, "failed_filters": failed, "checks": checks, "loopback": loopback, "repair_prompt": {"required_fix": failed, "target": loopback["target"] if loopback else None} if failed else None, "completed_at": utc_id()}
    write_json(run_dir / "validation" / "validation-summary.json", summary)
    for check in checks:
        write_json(run_dir / "validation" / f"{check['id']}.json", check)
    ledger("validation-ledger.jsonl", {"time": utc_id(), "event": "sandbox.validated", "candidate_id": candidate_id, "ok": summary["ok"], "failed": failed})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run massive file-filter validation against sandbox candidate.")
    parser.add_argument("--run-dir", default="")
    args = parser.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else harness_root() / "runs" / "massive-run"
    if not run_dir.is_absolute():
        run_dir = harness_root() / run_dir
    write_set = read_json(run_dir / "write-sets" / "final-write-set.json", {})
    print(json.dumps(validate_sandbox(run_dir, write_set), indent=2))


if __name__ == "__main__":
    main()
