from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import re

from .common import harness_root, repo_root, write_json, write_text, utc_id

VARIANTS = [
    {"id": "rpc-voxel-frontier", "title": "RPC Voxel Frontier", "mechanic": "remote-command style build and clear actions", "world": "rolling frontier mesas, caves, and crystal groves"},
    {"id": "biome-switcher", "title": "Biome Switcher Lab", "mechanic": "biome objectives and terrain mutation", "world": "rapidly shifting moss, dunes, basalt, and glacier zones"},
    {"id": "sky-island-builder", "title": "Sky Island Builder", "mechanic": "floating island traversal and block bridges", "world": "stacked islands with vertical world loading"},
    {"id": "cavern-miner", "title": "Cavern Miner RPC", "mechanic": "digging, exposed ore, and command-ledger mining", "world": "layered caves, ore ribs, and underground chambers"},
    {"id": "signal-tower-crafter", "title": "Signal Tower Crafter", "mechanic": "build signal pylons to unlock scan radius", "world": "wide terrain with landmarks and beacon loops"},
    {"id": "river-delta-builder", "title": "River Delta Builder", "mechanic": "bridge building and water-edge traversal", "world": "procedural rivers, deltas, banks, and islands"},
    {"id": "night-forge-survival", "title": "Night Forge Survival", "mechanic": "day/night resource loop and defensive placement", "world": "dark forge fields, glow blocks, and ridges"},
    {"id": "terrain-sculptor", "title": "Terrain Sculptor RPC", "mechanic": "raise, flatten, and clear terrain through RPC commands", "world": "editable hills and terraces"},
    {"id": "portal-chunk-runner", "title": "Portal Chunk Runner", "mechanic": "activate portals that shift chunk windows", "world": "portal-linked patches and distant biomes"},
    {"id": "tower-defense-voxels", "title": "Voxel Defense Grid", "mechanic": "place blocks as barriers around a core", "world": "arena valleys with procedural spawn lanes"}
]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "game"


def load_theme(theme_file: str) -> tuple[str, str]:
    if theme_file:
        path = Path(theme_file)
        if not path.is_absolute():
            path = repo_root() / path
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace"), str(path.relative_to(repo_root()))
    default = repo_root() / "LiveHarnessV.01" / "game-spec-harness" / "theme-prompts" / "001-rpc-voxel-world.md"
    if default.exists():
        return default.read_text(encoding="utf-8", errors="replace"), str(default.relative_to(repo_root()))
    return "Build ten experimental RPC voxel worlds with procedural terrain and kit-aware GameHost surfaces.", "default"


def build_specs(run_dir: Path, theme_file: str = "", count: int = 10) -> dict[str, Any]:
    theme, theme_ref = load_theme(theme_file)
    spec_dir = run_dir / "game-specs"
    prompt_dir = run_dir / "generated-prompts"
    spec_dir.mkdir(parents=True, exist_ok=True)
    prompt_dir.mkdir(parents=True, exist_ok=True)
    specs: list[dict[str, Any]] = []
    for index, variant in enumerate(VARIANTS[:count], start=1):
        spec_id = f"{index:02d}-{variant['id']}"
        title = variant["title"]
        prompt = f"""---
mode: kit-builder
game_spec_id: {spec_id}
public_title: {title}
public_goal: Build a browser playable RPC voxel world variant with procedural loading, top-of-world spawn, kit-aware integration diagnostics, and a distinct mechanic: {variant['mechanic']}.
---

# Theme Source

{theme.strip()}

# GameSpec Variant

Build {title}.

Required differentiator:
- Mechanic: {variant['mechanic']}
- World: {variant['world']}

Required common surface:
- Thin shell or bounded host entry.
- Procedural voxel world loading around the player.
- RPC-style command bus for player actions.
- Build/clear/place commands with command IDs and duplicate protection.
- Inventory or tool bar.
- HUD with biome, loaded chunks, visible blocks, selected block/tool, and latest command.
- GameHost.getState() with player, worldLoader, rpc/domain trace, input, inventory, renderer diagnostics, and integration/provider state.
- Generated result must feel like a separate game, not a reskin of the previous variant.
"""
        spec = {"schema": "liveharness.game-spec.v1", "spec_id": spec_id, "title": title, "theme_ref": theme_ref, "mechanic": variant["mechanic"], "world": variant["world"], "prompt_file": str((prompt_dir / f"{spec_id}.md").relative_to(run_dir)), "created_at": utc_id()}
        write_text(prompt_dir / f"{spec_id}.md", prompt)
        write_json(spec_dir / f"{spec_id}.json", spec)
        specs.append(spec)
    manifest = {"schema": "liveharness.game-spec-batch.v1", "theme_ref": theme_ref, "count": len(specs), "specs": specs, "created_at": utc_id()}
    write_json(run_dir / "game-spec-batch.json", manifest)
    write_json(spec_dir / "manifest.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 10 GameSpec variants from one theme prompt.")
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--theme-file", default="")
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()
    run_id = utc_id() + "-game-spec-batch"
    run_dir = Path(args.run_dir) if args.run_dir else harness_root() / "runs" / run_id
    if not run_dir.is_absolute():
        run_dir = harness_root() / run_dir
    print(json.dumps(build_specs(run_dir, args.theme_file, args.count), indent=2))


if __name__ == "__main__":
    main()
