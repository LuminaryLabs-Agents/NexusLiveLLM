from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from .common import harness_root, write_json, utc_id
from .idea_injector import normalize_idea
from .ten_game_batch_runner import run_batch


def run_idea_batch(run_dir: Path, idea_file: str = "", count: int = 10, max_workers: int = 16, max_loops: int = 2, max_parallel: int = 16, power: str = "") -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    intake = normalize_idea(run_dir, idea_file)
    theme_file = str(run_dir / intake["theme_file"])
    batch = run_batch(run_dir, theme_file, count, max_workers, max_loops, max_parallel, power)
    status = {"schema": "liveharness.idea-batch-status.v1", "run_id": run_dir.name, "idea": intake, "batch": batch, "completed_at": utc_id()}
    write_json(run_dir / "idea-batch-status.json", status)
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description="Run newest idea inbox item through GameSpec and LiveHarness batch.")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--idea-file", default="")
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--max-workers", type=int, default=16)
    parser.add_argument("--max-loops", type=int, default=2)
    parser.add_argument("--max-parallel", type=int, default=16)
    parser.add_argument("--power", default="")
    args = parser.parse_args()
    run_id = args.run_id or utc_id() + "-idea-batch"
    run_dir = Path(args.run_dir) if args.run_dir else harness_root() / "runs" / run_id
    if not run_dir.is_absolute():
        run_dir = harness_root() / run_dir
    print(json.dumps(run_idea_batch(run_dir, args.idea_file, args.count, args.max_workers, args.max_loops, args.max_parallel, args.power), indent=2))


if __name__ == "__main__":
    main()
