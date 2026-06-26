from __future__ import annotations

from pathlib import Path
from typing import Any

from .bounded_loop import synthetic_turn


def run(run_dir: Path, agent_id: str, scope: str, children: list[str] | None = None) -> dict[str, Any]:
    return synthetic_turn(run_dir / "orchestrators" / agent_id, agent_id, "orchestrator", "Created bounded orchestration artifact.", {"scope": scope, "children": children or []})
