from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .common import read_json, write_json, ledger, utc_id


def default_registry() -> list[dict[str, Any]]:
    return [
        {
            "kit_id": "nexusrealtime.core-runtime",
            "source": "NexusRealtime",
            "role": "runtime",
            "import_alias": "@nexus/core",
            "public_api": ["createRealtimeGame", "defineDomainServiceKit", "validateDomainServiceKit"],
            "expected_inputs": ["kit descriptors", "domain services", "sequence descriptors"],
            "expected_outputs": ["runtime surface", "events", "snapshots"],
            "adapter": "src/integration/nexusRuntimeAdapter.js",
            "fallback": "src/runtime/localRuntime.js",
            "proof_tasks": ["GameHost exposes runtime provider", "fallback exists", "domain services expose command IDs"]
        },
        {
            "kit_id": "protokit.action-input-kit",
            "source": "NexusRealtime-ProtoKits",
            "role": "input",
            "import_alias": "@protokits/action-input",
            "public_api": ["semantic input routing", "pressed/released events"],
            "expected_inputs": ["keydown", "keyup", "pointer"],
            "expected_outputs": ["movement.input.request", "inventory.select.request"],
            "adapter": "src/integration/adapters/actionInputAdapter.js",
            "fallback": "src/host/inputAdapter.js",
            "proof_tasks": ["input provider recorded", "input surface exists", "movement input state exists"]
        },
        {
            "kit_id": "protokit.world-patch-kit",
            "source": "NexusRealtime-ProtoKits",
            "role": "world-loader",
            "import_alias": "@protokits/world-patch",
            "public_api": ["patch lifecycle", "active window", "near/far pruning"],
            "expected_inputs": ["player position", "view radius"],
            "expected_outputs": ["loadedChunks", "recentlyUnloaded", "revision"],
            "adapter": "src/integration/adapters/worldPatchAdapter.js",
            "fallback": "src/world/worldLoader.js",
            "proof_tasks": ["worldLoader provider recorded", "loaded chunk count exposed", "revision exposed"]
        },
        {
            "kit_id": "protokit.terrain-sampler-kit",
            "source": "NexusRealtime-ProtoKits",
            "role": "terrain",
            "import_alias": "@protokits/terrain-sampler",
            "public_api": ["height sampling", "biome sampling", "terrain descriptors"],
            "expected_inputs": ["x", "z", "seed"],
            "expected_outputs": ["surfaceY", "biome"],
            "adapter": "src/integration/adapters/terrainSamplerAdapter.js",
            "fallback": "src/world/chunkStore.js",
            "proof_tasks": ["terrain provider recorded", "surfaceY exposed", "biome exposed"]
        },
        {
            "kit_id": "nexusrealtime.domain-service-kit",
            "source": "NexusRealtime",
            "role": "domain-service",
            "import_alias": "@nexus/core",
            "public_api": ["domain membrane", "validation", "snapshot/reset", "idempotency"],
            "expected_inputs": ["commands", "owned state", "idempotency keys"],
            "expected_outputs": ["events", "domainTrace", "appliedCommandIds"],
            "adapter": "src/integration/adapters/domainServiceAdapter.js",
            "fallback": "src/domains/buildBreakDomain.js",
            "proof_tasks": ["domain provider recorded", "domainTrace exists", "appliedCommandIds exists"]
        }
    ]


def build_kit_registry(run_dir: Path) -> dict[str, Any]:
    fused_dir = run_dir / "intake" / "fused"
    fused_dir.mkdir(parents=True, exist_ok=True)
    registry = {"schema": "liveharness.kit-registry.v1", "kits": default_registry(), "created_at": utc_id()}
    adapter_contracts = {"schema": "liveharness.adapter-contracts.v1", "contracts": {kit["kit_id"]: {"adapter": kit["adapter"], "fallback": kit["fallback"], "expected_inputs": kit["expected_inputs"], "expected_outputs": kit["expected_outputs"]} for kit in registry["kits"]}}
    proof_tasks = {"schema": "liveharness.kit-proof-tasks.v1", "tasks": [{"kit_id": kit["kit_id"], "role": kit["role"], "proof_tasks": kit["proof_tasks"]} for kit in registry["kits"]]}
    api_summary = {"schema": "liveharness.kit-api-summary.v1", "summaries": [{"kit_id": kit["kit_id"], "public_api": kit["public_api"], "role": kit["role"]} for kit in registry["kits"]]}
    write_json(fused_dir / "kit-registry.json", registry)
    write_json(fused_dir / "adapter-contracts.json", adapter_contracts)
    write_json(fused_dir / "proof-tasks.json", proof_tasks)
    write_json(fused_dir / "kit-api-summary.json", api_summary)
    ledger("context-ledger.jsonl", {"time": utc_id(), "event": "kit_registry.built", "kits": len(registry["kits"])})
    return registry


if __name__ == "__main__":
    import argparse
    from .common import harness_root
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", default="")
    args = parser.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else harness_root() / "runs" / "kit-registry-run"
    if not run_dir.is_absolute():
        run_dir = harness_root() / run_dir
    print(json.dumps(build_kit_registry(run_dir), indent=2))
