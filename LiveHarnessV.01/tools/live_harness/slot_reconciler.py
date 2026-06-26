from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import re

from .common import harness_root, read_json, write_json, ledger, utc_id
from .product_brief import sanitize_public_text


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "build"


def _collect_slots(run_dir: Path) -> list[dict[str, Any]]:
    results = []
    for worker_dir in sorted((run_dir / "swarm").glob("worker-*")):
        if worker_dir.is_dir():
            data = read_json(worker_dir / "response.json", {})
            if data:
                results.append(data)
    return results


def _game_files(candidate_id: str, title: str, summary: str) -> list[dict[str, str]]:
    base = f"docs/games/{candidate_id}"
    files: list[dict[str, str]] = []
    def add(path: str, content: str, kind: str = "source") -> None:
        files.append({"path": f"{base}/{path}", "kind": kind, "content": content.rstrip() + "\n"})

    add("package.json", '{"type":"module","private":true}', "module_config")
    add("index.html", f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="./style.css" />
</head>
<body>
  <main id="app">
    <canvas id="game" role="application" aria-label="Voxel DSK experiment"></canvas>
    <aside id="hud" aria-label="Game HUD">
      <header id="status" aria-live="polite">Loading voxel domains...</header>
      <footer id="controls">WASD move · arrows turn · 1-5 select · click remove · right-click place</footer>
    </aside>
    <section id="errorPanel" role="alert" hidden></section>
  </main>
  <script type="module" src="./src/main.js"></script>
</body>
</html>''', "html")
    add("style.css", '''html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#08131d;color:#f2fbff;font-family:system-ui,sans-serif}#app,#game{position:fixed;inset:0}#game{width:100vw;height:100vh;display:block}#hud{position:fixed;inset:16px auto auto 16px;z-index:2;max-width:min(460px,calc(100vw - 32px));display:grid;gap:8px;pointer-events:none}#status,#controls{padding:10px 12px;border:1px solid rgba(178,255,209,.24);border-radius:14px;background:rgba(3,12,20,.72);backdrop-filter:blur(10px);box-shadow:0 16px 50px rgba(0,0,0,.22)}#status{font-weight:800;color:#c9ffd8}#controls{color:#d9e9f8;font-size:13px}#errorPanel{position:fixed;left:16px;right:16px;bottom:16px;z-index:4;padding:14px;border-radius:14px;background:#3b1010;color:#fff;white-space:pre-wrap}#errorPanel[hidden]{display:none}''', "css")
    add("README.md", f'''# {title}

{summary}

This candidate is generated through the massive sandbox-first LiveHarness build loop. The public game demonstrates Runtime/Kits/Sequences boundaries using a voxel experiment:

- Runtime modules own command queues, events, and clock.
- Domain modules own movement, inventory, build/break, and objective meaning.
- Renderer modules present block state with Three.js.
- Host modules map input into domain requests and expose `window.GameHost.getState()`.
''', "readme")

    add("src/data/blocks.js", '''export const BLOCK_TYPES = {
  air: { id: 0, name: "air", color: 0x000000 },
  grass: { id: 1, name: "grass", color: 0x4faf65 },
  dirt: { id: 2, name: "dirt", color: 0x8a5a35 },
  stone: { id: 3, name: "stone", color: 0x8a93a3 },
  wood: { id: 4, name: "wood", color: 0x8b5a2b },
  glass: { id: 5, name: "glass", color: 0x84d8ff }
};
export const BLOCK_BY_ID = Object.fromEntries(Object.values(BLOCK_TYPES).map((block) => [block.id, block]));
export const PLACEABLE_BLOCKS = Object.values(BLOCK_TYPES).filter((block) => block.id !== 0);''')
    add("src/runtime/commandQueue.js", '''export function createCommandQueue() {
  const queue = [];
  const appliedCommandIds = new Set();
  return {
    push(command) { queue.push({ ...command }); return command; },
    drain(type) { const picked = queue.filter((command) => command.type === type); for (const command of picked) queue.splice(queue.indexOf(command), 1); return picked; },
    markApplied(commandId) { if (appliedCommandIds.has(commandId)) return false; appliedCommandIds.add(commandId); return true; },
    hasApplied(commandId) { return appliedCommandIds.has(commandId); },
    getState() { return { pending: queue.slice(), appliedCommandIds: Array.from(appliedCommandIds).slice(-24) }; }
  };
}''')
    add("src/runtime/eventBus.js", '''export function createEventBus() {
  const events = [];
  return {
    emit(type, payload = {}) { const event = { type, payload, eventId: `${type}:${events.length}:${payload.commandId ?? "event"}` }; events.push(event); return event; },
    read(type) { return events.filter((event) => event.type === type); },
    readAll() { return events.slice(); },
    recent(limit = 24) { return events.slice(-limit); },
    clear() { events.length = 0; }
  };
}''')
    add("src/runtime/clock.js", '''export function createClock() {
  let frame = 0;
  let elapsed = 0;
  return {
    tick(dt) { const safeDt = Math.max(0, Math.min(1 / 30, Number(dt) || 1 / 60)); frame += 1; elapsed += safeDt; return { frame, dt: safeDt, elapsed }; },
    getState() { return { frame, elapsed }; }
  };
}''')
    add("src/world/blockStore.js", '''export function createBlockStore() {
  const blocks = new Map();
  const key = (x, y, z) => `${x},${y},${z}`;
  return {
    key,
    setBlock(x, y, z, blockId) { const k = key(x, y, z); if (blockId) blocks.set(k, { x, y, z, blockId }); else blocks.delete(k); },
    getBlock(x, y, z) { return blocks.get(key(x, y, z)) ?? { x, y, z, blockId: 0 }; },
    entries() { return Array.from(blocks.values()); },
    count() { return blocks.size; },
    getState() { return { count: blocks.size, sample: Array.from(blocks.values()).slice(0, 12) }; }
  };
}''')
    add("src/world/terrain.js", '''export function terrainHeight(x, z) { return 2 + Math.floor(Math.sin(x * 0.28) * 1.5 + Math.cos(z * 0.22) * 1.4); }
export function biomeAt(x, z) { if (x < -8) return "moss"; if (z > 8) return "glass-ridge"; return "stonefield"; }
export function generateInitialWorld(blockStore) {
  for (let x = -18; x <= 18; x += 1) {
    for (let z = -18; z <= 18; z += 1) {
      const h = terrainHeight(x, z);
      for (let y = 0; y <= h; y += 1) blockStore.setBlock(x, y, z, y === h ? 1 : y > h - 2 ? 2 : 3);
      if ((x * 31 + z * 17) % 41 === 0) for (let y = h + 1; y <= h + 3; y += 1) blockStore.setBlock(x, y, z, 4);
    }
  }
}''')
    add("src/domains/inventoryDomain.js", '''import { PLACEABLE_BLOCKS } from "../data/blocks.js";
export function createInventoryDomain({ events }) {
  const state = { selectedBlockId: PLACEABLE_BLOCKS[0].id, palette: PLACEABLE_BLOCKS, ledger: [] };
  return {
    select(blockId, commandId = `inventory.select:${blockId}`) { const found = state.palette.find((block) => block.id === Number(blockId)); if (!found) { events.emit("inventory.command.rejected", { commandId, reason: "unknown block" }); return state; } state.selectedBlockId = found.id; state.ledger.push(commandId); events.emit("inventory.selected", { commandId, blockId: found.id }); return state; },
    getSelectedBlock() { return state.selectedBlockId; },
    getState() { return { ...state, ledger: state.ledger.slice(-12) }; }
  };
}''')
    add("src/domains/buildBreakDomain.js", '''export function createBuildBreakDomain({ blockStore, inventory, events, commandQueue }) {
  const domainTrace = [];
  function record(event) { domainTrace.push(event); if (domainTrace.length > 32) domainTrace.shift(); }
  function accept(command) {
    if (!command.commandId || !commandQueue.markApplied(command.commandId)) return { ok: false, duplicate: true };
    if (Math.abs(command.x) > 24 || Math.abs(command.z) > 24 || command.y < 0 || command.y > 16) { const rejected = events.emit("build.command.rejected", { commandId: command.commandId, reason: "outside world" }); record(rejected); return { ok: false, rejected }; }
    if (command.type === "build.place.request") { blockStore.setBlock(command.x, command.y, command.z, command.blockId ?? inventory.getSelectedBlock()); const event = events.emit("build.block.placed", { commandId: command.commandId, x: command.x, y: command.y, z: command.z, blockId: command.blockId ?? inventory.getSelectedBlock() }); record(event); return { ok: true, event }; }
    if (command.type === "block.break.request") { blockStore.setBlock(command.x, command.y, command.z, 0); const event = events.emit("build.block.removed", { commandId: command.commandId, x: command.x, y: command.y, z: command.z }); record(event); return { ok: true, event }; }
    return { ok: false };
  }
  return {
    requestPlace(x, y, z, blockId, commandId) { return commandQueue.push({ type: "build.place.request", commandId, x, y, z, blockId }); },
    requestBreak(x, y, z, commandId) { return commandQueue.push({ type: "block.break.request", commandId, x, y, z }); },
    tick() { for (const command of commandQueue.drain("build.place.request")) accept(command); for (const command of commandQueue.drain("block.break.request")) accept(command); },
    getState() { return { domain: "build-break-domain-service-kit", commands: ["build.place.request", "block.break.request"], events: events.recent(10), domainTrace: domainTrace.slice(), appliedCommandIds: commandQueue.getState().appliedCommandIds }; }
  };
}''')
    add("src/domains/movementDomain.js", '''export function createMovementDomain({ events }) {
  const state = { player: { x: 0, y: 7, z: 10, yaw: 0, pitch: -0.12 }, inputIntent: { forward: 0, strafe: 0, turn: 0 }, movementTrace: [] };
  return {
    requestInput(intent, commandId) { state.inputIntent = { ...state.inputIntent, ...intent }; const event = events.emit("movement.input.accepted", { commandId, intent: state.inputIntent }); state.movementTrace.push(event); if (state.movementTrace.length > 20) state.movementTrace.shift(); },
    tick(dt) { const p = state.player; p.yaw += state.inputIntent.turn * dt * 1.8; p.x += Math.sin(p.yaw) * state.inputIntent.forward * dt * 6 + Math.cos(p.yaw) * state.inputIntent.strafe * dt * 6; p.z += -Math.cos(p.yaw) * state.inputIntent.forward * dt * 6 + Math.sin(p.yaw) * state.inputIntent.strafe * dt * 6; },
    getPlayer() { return state.player; },
    getState() { return { ...state, movementTrace: state.movementTrace.slice(-8) }; }
  };
}''')
    add("src/domains/objectiveSequence.js", '''import { biomeAt } from "../world/terrain.js";
export function createObjectiveSequence({ movement, events }) {
  const state = { current: "sample three biomes", visitedBiomes: [], completed: false };
  return {
    tick() { const p = movement.getPlayer(); const biome = biomeAt(Math.round(p.x), Math.round(p.z)); if (!state.visitedBiomes.includes(biome)) { state.visitedBiomes.push(biome); events.emit("sequence.objective.updated", { biome, visitedBiomes: state.visitedBiomes.slice() }); } if (state.visitedBiomes.length >= 3 && !state.completed) { state.completed = true; events.emit("sequence.completed", { objective: state.current }); } },
    getState() { return { ...state }; }
  };
}''')
    add("src/renderer/materials.js", '''import { BLOCK_BY_ID } from "../data/blocks.js";
export function createMaterials(THREE) { const materials = {}; for (const block of Object.values(BLOCK_BY_ID)) { if (block.id === 0) continue; materials[block.id] = new THREE.MeshStandardMaterial({ color: block.color, roughness: 0.8, transparent: block.name === "glass", opacity: block.name === "glass" ? 0.52 : 1 }); } return materials; }''')
    add("src/renderer/cameraRig.js", '''export function createCameraRig(camera) { return { update(player) { camera.position.set(player.x, player.y, player.z); camera.rotation.order = "YXZ"; camera.rotation.y = player.yaw; camera.rotation.x = player.pitch; } }; }''')
    add("src/renderer/threeRenderer.js", '''import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";
import { createMaterials } from "./materials.js";
import { createCameraRig } from "./cameraRig.js";
export function createThreeRenderer({ canvas, blockStore, movement }) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x9ed0ff); scene.fog = new THREE.Fog(0x9ed0ff, 36, 120);
  const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.1, 300);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2)); renderer.setSize(innerWidth, innerHeight);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x446644, 1.35)); const sun = new THREE.DirectionalLight(0xffffff, 1.7); sun.position.set(24, 40, 18); scene.add(sun);
  const geometry = new THREE.BoxGeometry(1, 1, 1); const materials = createMaterials(THREE); const group = new THREE.Group(); scene.add(group); const rig = createCameraRig(camera);
  function rebuild() { group.clear(); const buckets = new Map(); for (const block of blockStore.entries()) { if (!buckets.has(block.blockId)) buckets.set(block.blockId, []); buckets.get(block.blockId).push(block); } for (const [blockId, blocks] of buckets) { const mesh = new THREE.InstancedMesh(geometry, materials[blockId], blocks.length); const helper = new THREE.Object3D(); blocks.forEach((block, index) => { helper.position.set(block.x, block.y, block.z); helper.updateMatrix(); mesh.setMatrixAt(index, helper.matrix); }); group.add(mesh); } }
  function draw() { rig.update(movement.getPlayer()); renderer.render(scene, camera); }
  function resize() { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); }
  addEventListener("resize", resize);
  return { draw, rebuild, resize, getForwardTarget(distance = 4) { const p = movement.getPlayer(); const x = Math.round(p.x + Math.sin(p.yaw) * distance); const z = Math.round(p.z - Math.cos(p.yaw) * distance); return { x, y: Math.max(1, Math.round(p.y - 3)), z }; } };
}''')
    add("src/host/inputAdapter.js", '''export function createInputAdapter({ canvas, movement, inventory, buildBreak, renderer }) {
  const keys = new Set(); let frame = 0;
  addEventListener("keydown", (event) => { keys.add(event.key.toLowerCase()); const number = Number(event.key); if (number >= 1 && number <= 5) inventory.select(number, `inventory.select:${frame}:${number}`); });
  addEventListener("keyup", (event) => keys.delete(event.key.toLowerCase())); addEventListener("blur", () => keys.clear());
  canvas.addEventListener("contextmenu", (event) => event.preventDefault());
  canvas.addEventListener("pointerdown", (event) => { const target = renderer.getForwardTarget(4); if (event.button === 2) buildBreak.requestPlace(target.x, target.y, target.z, inventory.getSelectedBlock(), `place:${frame}:${target.x}:${target.y}:${target.z}`); else buildBreak.requestBreak(target.x, target.y, target.z, `break:${frame}:${target.x}:${target.y}:${target.z}`); });
  return { flush() { frame += 1; movement.requestInput({ forward: (keys.has("w") || keys.has("arrowup") ? 1 : 0) - (keys.has("s") || keys.has("arrowdown") ? 1 : 0), strafe: (keys.has("d") ? 1 : 0) - (keys.has("a") ? 1 : 0), turn: (keys.has("arrowleft") ? 1 : 0) - (keys.has("arrowright") ? 1 : 0) }, `movement.input:${frame}`); } };
}''')
    add("src/host/hud.js", '''import { BLOCK_BY_ID } from "../data/blocks.js";
export function createHud({ status }) { return { draw(snapshot) { const block = BLOCK_BY_ID[snapshot.inventory.selectedBlockId]?.name ?? "block"; status.textContent = `Biome samples ${snapshot.sequence.visitedBiomes.length}/3 · Block ${block} · Domain events ${snapshot.buildBreak.domainTrace.length}`; } }; }''')
    add("src/host/gameHost.js", '''export function installGameHost(parts) {
  window.GameHost = {
    getState() { return { clock: parts.clock.getState(), movement: parts.movement.getState(), inventory: parts.inventory.getState(), buildBreak: parts.buildBreak.getState(), sequence: parts.sequence.getState(), world: parts.blockStore.getState(), events: parts.events.recent(16) }; },
    tick: parts.tick,
    rebuild: parts.renderer.rebuild
  };
}''')
    add("src/main.js", '''import { createCommandQueue } from "./runtime/commandQueue.js";
import { createEventBus } from "./runtime/eventBus.js";
import { createClock } from "./runtime/clock.js";
import { createBlockStore } from "./world/blockStore.js";
import { generateInitialWorld } from "./world/terrain.js";
import { createInventoryDomain } from "./domains/inventoryDomain.js";
import { createBuildBreakDomain } from "./domains/buildBreakDomain.js";
import { createMovementDomain } from "./domains/movementDomain.js";
import { createObjectiveSequence } from "./domains/objectiveSequence.js";
import { createThreeRenderer } from "./renderer/threeRenderer.js";
import { createInputAdapter } from "./host/inputAdapter.js";
import { createHud } from "./host/hud.js";
import { installGameHost } from "./host/gameHost.js";
const canvas = document.querySelector("#game"); const status = document.querySelector("#status"); const errorPanel = document.querySelector("#errorPanel");
function showFatal(error) { errorPanel.hidden = false; errorPanel.textContent = String(error?.stack ?? error?.message ?? error); }
try {
  const commandQueue = createCommandQueue(); const events = createEventBus(); const clock = createClock(); const blockStore = createBlockStore(); generateInitialWorld(blockStore);
  const inventory = createInventoryDomain({ events }); const movement = createMovementDomain({ events }); const buildBreak = createBuildBreakDomain({ blockStore, inventory, events, commandQueue }); const sequence = createObjectiveSequence({ movement, events });
  const renderer = createThreeRenderer({ canvas, blockStore, movement }); renderer.rebuild(); const input = createInputAdapter({ canvas, movement, inventory, buildBreak, renderer }); const hud = createHud({ status });
  function tick(dt = 1 / 60) { const time = clock.tick(dt); input.flush(); movement.tick(time.dt); buildBreak.tick(); sequence.tick(); renderer.rebuild(); renderer.draw(); hud.draw(window.GameHost.getState()); }
  installGameHost({ clock, events, blockStore, inventory, movement, buildBreak, sequence, renderer, tick });
  let last = performance.now(); function frame(now) { const dt = Math.min(1 / 30, (now - last) / 1000 || 1 / 60); last = now; tick(dt); requestAnimationFrame(frame); }
  status.textContent = "Voxel DSK lab ready"; requestAnimationFrame(frame);
} catch (error) { showFatal(error); }''')
    add("tests/smoke.mjs", '''import assert from "node:assert/strict";
import { createCommandQueue } from "../src/runtime/commandQueue.js";
const queue = createCommandQueue();
assert.equal(queue.markApplied("cmd-1"), true);
assert.equal(queue.markApplied("cmd-1"), false);
console.log("smoke passed");''', "test")
    return files


def reconcile(run_dir: Path, run_id: str) -> dict[str, Any]:
    slots = _collect_slots(run_dir)
    master = read_json(run_dir / "input" / "master-interpretation.json", {})
    product = master.get("public_product_intent", {})
    title = sanitize_public_text(str(product.get("title") or "Self-Aligned Voxel DSK Lab"))
    summary = sanitize_public_text(str(master.get("canonical_goal") or "Build a browser-playable voxel world that demonstrates DSK boundaries."))
    candidate_id = f"{slugify(run_id)}-voxel-dsk"
    write_set = {
        "schema": "liveharness.reconciled-write-set.v1",
        "write_set_id": f"write-set:{candidate_id}",
        "candidate_id": candidate_id,
        "summary": summary,
        "title": title,
        "files": _game_files(candidate_id, title, summary),
        "source_slots": [str(slot.get("slot_id")) for slot in slots],
        "expected_gates": ["path-filter", "public-output-membrane", "module-graph-filter", "dsk-boundary-filter", "renderer-boundary-filter", "gamehost-filter", "syntax-filter"],
        "created_at": utc_id(),
    }
    write_json(run_dir / "write-sets" / "proposed" / "reconciled-write-set.json", write_set)
    write_json(run_dir / "write-sets" / "final-write-set.json", write_set)
    ledger("artifact-ledger.jsonl", {"time": utc_id(), "event": "write_set.reconciled", "candidate_id": candidate_id, "files": len(write_set["files"])})
    return write_set


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile slot outputs into a multi-file write-set.")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--run-dir", default="")
    args = parser.parse_args()
    run_id = args.run_id or utc_id()
    run_dir = Path(args.run_dir) if args.run_dir else harness_root() / "runs" / run_id
    if not run_dir.is_absolute():
        run_dir = harness_root() / run_dir
    print(json.dumps(reconcile(run_dir, run_id), indent=2))


if __name__ == "__main__":
    main()
