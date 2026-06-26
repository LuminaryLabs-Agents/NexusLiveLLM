from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from .common import harness_root, repo_root, write_json, ledger, utc_id
from .public_output_check import scan_docs
from .domain_trace_check import check_path as domain_trace_check
from .gamehost_check import check_path as gamehost_check
from .massive_validation_runner import legacy_builder_output_filter


def run_final_public_validation(run_dir: Path) -> dict[str, Any]:
    docs = repo_root() / "docs"
    checks = [scan_docs(), domain_trace_check(docs), gamehost_check(docs), legacy_builder_output_filter(docs)]
    summary = {
        "schema": "liveharness.final-public-validation.v1",
        "run_id": run_dir.name,
        "ok": all(check.get("ok") for check in checks),
        "checks": checks,
        "failed": [check.get("id") for check in checks if not check.get("ok")],
        "completed_at": utc_id(),
    }
    write_json(run_dir / "validation" / "final-public-validation.json", summary)
    ledger("validation-ledger.jsonl", {"time": utc_id(), "event": "public.validated", "ok": summary["ok"], "failed": summary["failed"]})
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run final public output validation.")
    parser.add_argument("--run-dir", default="")
    args = parser.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else harness_root() / "runs" / "massive-run"
    if not run_dir.is_absolute():
        run_dir = harness_root() / run_dir
    print(json.dumps(run_final_public_validation(run_dir), indent=2))


if __name__ == "__main__":
    main()
