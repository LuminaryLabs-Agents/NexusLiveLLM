from __future__ import annotations

from typing import Any


def build_voxel_clone_files(candidate_id: str, title: str, summary: str) -> list[dict[str, str]]:
    """Return a deterministic multi-file Three.js voxel game write-set."""
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
    <canvas id="game" role="application" aria-label="Infinite voxel domain lab"></canvas>
    <aside id="hud" aria-label="Game HUD">
      <header id="status" aria-live="polite">Loading infinite block world...</header>
      <section id="inventory" aria-label="Inventory"></section>
      <section id="inputSurface" aria-label="Input test surface"></section>
      <footer id="controls">WASD move · mouse look · click remove · right-click place · 1-7 select · F toggles fly</footer>
    </aside>
    <section id="errorPanel" role="alert" hidden></section>
  </main>
  <script type="module" src="./src/main.js"></script>
</body>
</html>''', "html")
    add("style.css", '''html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#08131d;color:#f2fbff;font-family:Inter,ui-sans-serif,system-ui,sans-serif}#app,#game{position:fixed;inset:0}#game{width:100vw;height:100vh;display:block;outline:none}#hud{position:fixed;inset:16px auto auto 16px;z-index:2;width:min(520px,calc(100vw - 32px));display:grid;gap:8px;pointer-events:none}#status,#controls,#inventory,#inputSurface{padding:10px 12px;border:1px solid rgba(178,255,209,.24);border-radius:14px;background:rgba(3,12,20,.74);backdrop-filter:blur(10px);box-shadow:0 16px 50px rgba(0,0,0,.24)}#status{font-weight:850;color:#c9ffd8}#controls{color:#d9e9f8;font-size:13px}.inventory-grid{display:grid;grid-template-columns:repeat(7,minmax(44px,1fr));gap:6px}.slot{border:1px solid rgba(255,255,255,.2);border-radius:10px;padding:8px;text-align:center;background:rgba(255,255,255,.07);font-size:12px}.slot.active{border-color:#bfffd2;background:rgba(191,255,210,.2);color:#fff}.input-row{display:flex;flex-wrap:wrap;gap:6px}.pill{padding:4px 8px;border-radius:999px;background:rgba(255,255,255,.09);font-size:12px}.pill.on{background:#bfffd2;color:#06110b;font-weight:900}#errorPanel{position:fixed;left:16px;right:16px;bottom:16px;z-index:4;padding:14px;border-radius:14px;background:#3b1010;color:#fff;white-space:pre-wrap}#errorPanel[hidden]{display:none}''', "css")
    add("README.md", f'''# {title}

{summary}

This is a browser-playable infinite voxel world experiment. It is structured as Runtime, Domain Service Kits, Sequences, Renderer, and Host modules.

## Play

- WASD: move
- Mouse: look after clicking the canvas
- Left click: remove a block through `block.break.request`
- Right click: place a selected block through `build.place.request`
- 1-7: select inventory block
- F: toggle fly mode

## Proof surface

`window.GameHost.getState()` exposes player, world, inventory, buildBreak, domainTrace, events, sequence, input, and debug state.
''', "readme")
    add("src/data/blocks.js", '''export const BLOCK_TYPES = {
  air: { id: 0, name: "air", color: 0x000000, solid: false },
  grass: { id: 1, name: "grass", color: 0x4faf65, solid: true },
  dirt: { id: 2, name: "dirt", color: 0x8a5a35, solid: true },
  stone: { id: 3, name: "stone", color: 0x8a93a3, solid: true },
  wood: { id: 4, name: "wood", color: 0x8b5a2b, solid: true },
  glass: { id: 5, name: "glass", color: 0x84d8ff, solid: true, transparent: true },
  sand: { id: 6, name: "sand", color: 0xd8c27a, solid: true },
  leaf: { id: 7, name: "leaf", color: 0x3f9f47, solid: true, transparent: true }
};
export const BLOCK_BY_ID = Object.fromEntries(Object.values(BLOCK_TYPES).map((block) => [block.id, block]));
export const PLACEABLE_BLOCKS = Object.values(BLOCK_TYPES).filter((block) => block.id !== 0);''')
    add("src/runtime/commandQueue.js", '''export function createCommandQueue() {
  const queue = [];
  const appliedCommandIds = new Set();
  return {
    push(command) { queue.push({ ...command }); return command; },
    drain(type) { const picked = queue.filter((command) => command.type === type); for (const command of picked) queue.splice(queue.indexOf(command), 1); return picked; },
    markApplied(commandId) { if (!commandId || appliedCommandIds.has(commandId)) return false; appliedCommandIds.add(commandId); return true; },
    hasApplied(commandId) { return appliedCommandIds.has(commandId); },
    getState() { return { pending: queue.slice(), appliedCommandIds: Array.from(appliedCommandIds).slice(-48) }; }
  };
}''')
    add("src/runtime/eventBus.js", '''export function createEventBus() {
  const events = [];
  return {
    emit(type, payload = {}) { const event = { type, payload, eventId: `${type}:${events.length}:${payload.commandId ?? "event"}` }; events.push(event); return event; },
    read(type) { return events.filter((event) => event.type === type); },
    readAll() { return events.slice(); },
    recent(limit = 48) { return events.slice(-limit); },
    clear() { events.length = 0; }
  };
}''')
    add("src/runtime/clock.js", '''export function createClock() {
  let frame = 0;
  let elapsed = 0;
  return {
    tick(dt) { const safeDt = Math.max(0, Math.min(1 / 20, Number(dt) || 1 / 60)); frame += 1; elapsed += safeDt; return { frame, dt: safeDt, elapsed }; },
    getState() { return { frame, elapsed }; }
  };
}''')
    add("src/world/noise.js", '''export function hash2(x, z, seed = 1337) { let h = Math.imul(x, 374761393) ^ Math.imul(z, 668265263) ^ seed; h = (h ^ (h >>> 13)) >>> 0; h = Math.imul(h, 1274126177) >>> 0; return ((h ^ (h >>> 16)) >>> 0) / 4294967295; }
export function smoothNoise(x, z) { const xi = Math.floor(x); const zi = Math.floor(z); const xf = x - xi; const zf = z - zi; const a = hash2(xi, zi); const b = hash2(xi + 1, zi); const c = hash2(xi, zi + 1); const d = hash2(xi + 1, zi + 1); const u = xf * xf * (3 - 2 * xf); const v = zf * zf * (3 - 2 * zf); return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v; }
export function heightAt(x, z) { const broad = smoothNoise(x * 0.025, z * 0.025) * 26; const medium = smoothNoise(x * 0.085 + 99, z * 0.085 - 77) * 8; return Math.max(2, Math.floor(3 + broad + medium)); }
export function biomeAt(x, z) { const n = smoothNoise(x * 0.018 - 15, z * 0.018 + 28); if (n < 0.27) return "dunes"; if (n < 0.55) return "moss"; if (n < 0.76) return "stonefield"; return "glass-ridge"; }''')
    add("src/world/chunkStore.js", '''import { heightAt, biomeAt, hash2 } from "./noise.js";
export function createChunkStore({ chunkSize = 16, radius = 3 } = {}) {
  const overrides = new Map();
  const dirtyChunks = new Set();
  const key = (x, y, z) => `${x},${y},${z}`;
  const chunkKey = (cx, cz) => `${cx},${cz}`;
  const chunkOf = (value) => Math.floor(value / chunkSize);
  function generatedBlock(x, y, z) { const h = heightAt(x, z); if (y < 0 || y > h + 5) return 0; if (y === h) { const biome = biomeAt(x, z); if (biome === "dunes") return 6; if (biome === "glass-ridge") return 5; if (biome === "stonefield") return 3; return 1; } if (y > h - 3) return 2; return 3; }
  function treeBlock(x, y, z) { const h = heightAt(x, z); const trunk = hash2(x, z) > 0.986 && biomeAt(x, z) === "moss"; if (!trunk) return 0; if (y > h && y <= h + 4) return 4; if (y > h + 4 && y <= h + 6 && Math.abs((x % 3 + 3) % 3 - 1) <= 1 && Math.abs((z % 3 + 3) % 3 - 1) <= 1) return 7; return 0; }
  function getBlock(x, y, z) { const override = overrides.get(key(x, y, z)); if (override !== undefined) return override; return treeBlock(x, y, z) || generatedBlock(x, y, z); }
  function setBlock(x, y, z, blockId) { overrides.set(key(x, y, z), blockId); dirtyChunks.add(chunkKey(chunkOf(x), chunkOf(z))); }
  function entriesNear(px, pz, viewRadius = radius) { const pcx = chunkOf(Math.round(px)); const pcz = chunkOf(Math.round(pz)); const blocks = []; for (let cx = pcx - viewRadius; cx <= pcx + viewRadius; cx += 1) { for (let cz = pcz - viewRadius; cz <= pcz + viewRadius; cz += 1) { for (let lx = 0; lx < chunkSize; lx += 1) { for (let lz = 0; lz < chunkSize; lz += 1) { const x = cx * chunkSize + lx; const z = cz * chunkSize + lz; const h = heightAt(x, z); const minY = Math.max(0, h - 2); const maxY = h + 7; for (let y = minY; y <= maxY; y += 1) { const blockId = getBlock(x, y, z); if (!blockId) continue; const exposed = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]].some(([a,b,c]) => !getBlock(x+a, y+b, z+c)); if (exposed) blocks.push({ x, y, z, blockId }); } } } } } return blocks; }
  return { getBlock, setBlock, entriesNear, key, chunkOf, heightAt, biomeAt, getState() { return { overrides: overrides.size, dirtyChunks: Array.from(dirtyChunks).slice(-32), chunkSize, radius }; } };
}''')
    add("src/domains/inventoryDomain.js", '''import { PLACEABLE_BLOCKS, BLOCK_BY_ID } from "../data/blocks.js";
export function createInventoryDomain({ events }) {
  const state = { selectedBlockId: PLACEABLE_BLOCKS[0].id, palette: PLACEABLE_BLOCKS, counts: Object.fromEntries(PLACEABLE_BLOCKS.map((block) => [block.id, 999])), inventoryLedger: [] };
  return {
    select(blockId, commandId = `inventory.select:${blockId}`) { const found = state.palette.find((block) => block.id === Number(blockId)); if (!found) { events.emit("inventory.command.rejected", { commandId, reason: "unknown block" }); return state; } state.selectedBlockId = found.id; state.inventoryLedger.push(commandId); events.emit("inventory.selected", { commandId, blockId: found.id, blockName: found.name }); return state; },
    consume(blockId, commandId) { if ((state.counts[blockId] ?? 0) <= 0) { events.emit("inventory.command.rejected", { commandId, reason: "empty stack" }); return false; } state.counts[blockId] -= 1; events.emit("inventory.consumed", { commandId, blockId }); return true; },
    getSelectedBlock() { return state.selectedBlockId; },
    getSelectedName() { return BLOCK_BY_ID[state.selectedBlockId]?.name ?? "block"; },
    getState() { return { ...state, selectedName: this.getSelectedName(), inventoryLedger: state.inventoryLedger.slice(-24) }; }
  };
}''')
    add("src/domains/buildBreakDomain.js", '''export function createBuildBreakDomain({ chunkStore, inventory, events, commandQueue }) {
  const domainTrace = [];
  function record(event) { domainTrace.push(event); if (domainTrace.length > 64) domainTrace.shift(); }
  function accept(command) { if (!command.commandId || !commandQueue.markApplied(command.commandId)) return { ok: false, duplicate: true }; if (Math.abs(command.y) > 80) { const rejected = events.emit("build.command.rejected", { commandId: command.commandId, reason: "outside vertical build limit" }); record(rejected); return { ok: false, rejected }; } if (command.type === "build.place.request") { const blockId = command.blockId ?? inventory.getSelectedBlock(); chunkStore.setBlock(command.x, command.y, command.z, blockId); const event = events.emit("build.block.placed", { commandId: command.commandId, x: command.x, y: command.y, z: command.z, blockId }); record(event); return { ok: true, event }; } if (command.type === "block.break.request") { chunkStore.setBlock(command.x, command.y, command.z, 0); const event = events.emit("build.block.removed", { commandId: command.commandId, x: command.x, y: command.y, z: command.z }); record(event); return { ok: true, event }; } return { ok: false }; }
  return {
    requestPlace(x, y, z, blockId, commandId) { return commandQueue.push({ type: "build.place.request", commandId, x, y, z, blockId }); },
    requestBreak(x, y, z, commandId) { return commandQueue.push({ type: "block.break.request", commandId, x, y, z }); },
    tick() { for (const command of commandQueue.drain("build.place.request")) accept(command); for (const command of commandQueue.drain("block.break.request")) accept(command); },
    getState() { return { domain: "build-break-domain-service-kit", commands: ["build.place.request", "block.break.request"], events: events.recent(16), domainTrace: domainTrace.slice(), appliedCommandIds: commandQueue.getState().appliedCommandIds }; }
  };
}''')
    add("src/domains/movementDomain.js", '''export function createMovementDomain({ events, chunkStore }) {
  const state = { player: { x: 0, y: 20, z: 12, yaw: 0, pitch: -0.12, fly: false }, inputIntent: { forward: 0, strafe: 0, rise: 0, turn: 0, pitch: 0 }, movementTrace: [] };
  function clampPitch(value) { return Math.max(-1.25, Math.min(1.1, value)); }
  return {
    requestInput(intent, commandId) { state.inputIntent = { ...state.inputIntent, ...intent }; const event = events.emit("movement.input.accepted", { commandId, intent: state.inputIntent }); state.movementTrace.push(event); if (state.movementTrace.length > 32) state.movementTrace.shift(); },
    rotate(dx, dy, commandId) { state.player.yaw -= dx * 0.0028; state.player.pitch = clampPitch(state.player.pitch - dy * 0.0022); events.emit("camera.look.updated", { commandId, yaw: state.player.yaw, pitch: state.player.pitch }); },
    toggleFly(commandId) { state.player.fly = !state.player.fly; events.emit("movement.mode.changed", { commandId, fly: state.player.fly }); },
    tick(dt) { const p = state.player; const speed = p.fly ? 15 : 8; p.yaw += state.inputIntent.turn * dt * 1.8; p.pitch = clampPitch(p.pitch + state.inputIntent.pitch * dt); p.x += Math.sin(p.yaw) * state.inputIntent.forward * dt * speed + Math.cos(p.yaw) * state.inputIntent.strafe * dt * speed; p.z += -Math.cos(p.yaw) * state.inputIntent.forward * dt * speed + Math.sin(p.yaw) * state.inputIntent.strafe * dt * speed; if (p.fly) p.y += state.inputIntent.rise * dt * speed; else { const ground = chunkStore.heightAt(Math.round(p.x), Math.round(p.z)) + 2.1; p.y += (ground - p.y) * Math.min(1, dt * 8); } },
    getPlayer() { return state.player; },
    getState() { return { ...state, biome: chunkStore.biomeAt(Math.round(state.player.x), Math.round(state.player.z)), movementTrace: state.movementTrace.slice(-12) }; }
  };
}''')
    add("src/domains/objectiveSequence.js", '''export function createObjectiveSequence({ movement, events }) {
  const state = { current: "sample three biomes and place a marker block", visitedBiomes: [], placedBlocks: 0, completed: false };
  return {
    observeBuildBreak(buildBreak) { const placed = buildBreak.getState().domainTrace.filter((event) => event.type === "build.block.placed").length; state.placedBlocks = placed; },
    tick() { const biome = movement.getState().biome; if (!state.visitedBiomes.includes(biome)) { state.visitedBiomes.push(biome); events.emit("sequence.objective.updated", { biome, visitedBiomes: state.visitedBiomes.slice() }); } if (state.visitedBiomes.length >= 3 && state.placedBlocks >= 1 && !state.completed) { state.completed = true; events.emit("sequence.completed", { objective: state.current }); } },
    getState() { return { ...state }; }
  };
}''')
    add("src/renderer/materials.js", '''import { BLOCK_BY_ID } from "../data/blocks.js";
export function createMaterials(THREE) { const materials = {}; for (const block of Object.values(BLOCK_BY_ID)) { if (block.id === 0) continue; materials[block.id] = new THREE.MeshStandardMaterial({ color: block.color, roughness: 0.82, transparent: !!block.transparent, opacity: block.transparent ? 0.56 : 1 }); } return materials; }''')
    add("src/renderer/cameraRig.js", '''export function createCameraRig(camera) { return { update(player) { camera.position.set(player.x, player.y, player.z); camera.rotation.order = "YXZ"; camera.rotation.y = player.yaw; camera.rotation.x = player.pitch; } }; }''')
    add("src/renderer/threeRenderer.js", '''import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";
import { createMaterials } from "./materials.js";
import { createCameraRig } from "./cameraRig.js";
export function createThreeRenderer({ canvas, chunkStore, movement }) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x9dd3ff); scene.fog = new THREE.Fog(0x9dd3ff, 48, 160);
  const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.1, 420);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2)); renderer.setSize(innerWidth, innerHeight);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x3b6740, 1.35)); const sun = new THREE.DirectionalLight(0xffffff, 1.65); sun.position.set(32, 60, 20); scene.add(sun);
  const geometry = new THREE.BoxGeometry(1, 1, 1); const materials = createMaterials(THREE); const group = new THREE.Group(); scene.add(group); const rig = createCameraRig(camera); let lastKey = "";
  function rebuild(force = false) { const p = movement.getPlayer(); const key = `${Math.floor(p.x/8)},${Math.floor(p.z/8)}`; if (!force && key === lastKey) return; lastKey = key; group.clear(); const buckets = new Map(); for (const block of chunkStore.entriesNear(p.x, p.z, 3)) { if (!buckets.has(block.blockId)) buckets.set(block.blockId, []); buckets.get(block.blockId).push(block); } for (const [blockId, blocks] of buckets) { const mesh = new THREE.InstancedMesh(geometry, materials[blockId], blocks.length); const helper = new THREE.Object3D(); blocks.forEach((block, index) => { helper.position.set(block.x, block.y, block.z); helper.updateMatrix(); mesh.setMatrixAt(index, helper.matrix); }); group.add(mesh); } }
  function draw() { rig.update(movement.getPlayer()); renderer.render(scene, camera); }
  function resize() { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); }
  function getForwardTarget(distance = 5) { const p = movement.getPlayer(); const x = Math.round(p.x + Math.sin(p.yaw) * distance); const z = Math.round(p.z - Math.cos(p.yaw) * distance); const y = Math.max(0, Math.round(p.y - 2)); return { x, y, z }; }
  addEventListener("resize", resize);
  return { draw, rebuild, resize, getForwardTarget, getState() { return { visibleGroups: group.children.length, lastKey, fog: true }; } };
}''')
    add("src/host/inputAdapter.js", '''export function createInputAdapter({ canvas, movement, inventory, buildBreak, renderer }) {
  const keys = new Set(); const pointer = { locked: false, moves: 0 }; let frame = 0; let lastCommand = "none";
  canvas.tabIndex = 1; canvas.addEventListener("click", () => { canvas.focus(); canvas.requestPointerLock?.(); });
  document.addEventListener("pointerlockchange", () => { pointer.locked = document.pointerLockElement === canvas; });
  document.addEventListener("mousemove", (event) => { if (pointer.locked) { pointer.moves += 1; movement.rotate(event.movementX, event.movementY, `camera.look:${frame}:${pointer.moves}`); } });
  addEventListener("keydown", (event) => { keys.add(event.key.toLowerCase()); const number = Number(event.key); if (number >= 1 && number <= 7) { inventory.select(number, `inventory.select:${frame}:${number}`); lastCommand = `select ${number}`; } if (event.key.toLowerCase() === "f") { movement.toggleFly(`movement.mode:${frame}`); lastCommand = "toggle fly"; } });
  addEventListener("keyup", (event) => keys.delete(event.key.toLowerCase())); addEventListener("blur", () => keys.clear());
  canvas.addEventListener("contextmenu", (event) => event.preventDefault());
  canvas.addEventListener("pointerdown", (event) => { const target = renderer.getForwardTarget(5); if (event.button === 2) { buildBreak.requestPlace(target.x, target.y, target.z, inventory.getSelectedBlock(), `place:${frame}:${target.x}:${target.y}:${target.z}:${inventory.getSelectedBlock()}`); lastCommand = "place"; } else { buildBreak.requestBreak(target.x, target.y, target.z, `break:${frame}:${target.x}:${target.y}:${target.z}`); lastCommand = "break"; } });
  return { flush() { frame += 1; movement.requestInput({ forward: (keys.has("w") || keys.has("arrowup") ? 1 : 0) - (keys.has("s") || keys.has("arrowdown") ? 1 : 0), strafe: (keys.has("d") ? 1 : 0) - (keys.has("a") ? 1 : 0), rise: (keys.has(" ") ? 1 : 0) - (keys.has("shift") ? 1 : 0), turn: (keys.has("arrowleft") ? 1 : 0) - (keys.has("arrowright") ? 1 : 0), pitch: 0 }, `movement.input:${frame}`); }, getState() { return { keys: Array.from(keys).sort(), pointerLocked: pointer.locked, pointerMoves: pointer.moves, frame, lastCommand }; } };
}''')
    add("src/host/hud.js", '''export function createHud({ status, inventoryEl, inputEl }) { return { draw(snapshot) { const inv = snapshot.inventory; status.textContent = `Biome ${snapshot.movement.biome} · Samples ${snapshot.sequence.visitedBiomes.length}/3 · Block ${inv.selectedName} · Events ${snapshot.buildBreak.domainTrace.length} · Fly ${snapshot.movement.player.fly ? "on" : "off"}`; inventoryEl.innerHTML = `<div class="inventory-grid">${inv.palette.map((block,index)=>`<div class="slot ${block.id===inv.selectedBlockId?"active":""}">${index+1}<br>${block.name}</div>`).join("")}</div>`; inputEl.innerHTML = `<div class="input-row"><span class="pill ${snapshot.input.pointerLocked?"on":""}">mouse ${snapshot.input.pointerLocked?"locked":"free"}</span>${["w","a","s","d"," ","shift"].map(k=>`<span class="pill ${snapshot.input.keys.includes(k)?"on":""}">${k===" "?"space":k}</span>`).join("")}<span class="pill">last ${snapshot.input.lastCommand}</span></div>`; } }; }''')
    add("src/host/gameHost.js", '''export function installGameHost(parts) {
  window.GameHost = {
    getState() { return { clock: parts.clock.getState(), movement: parts.movement.getState(), inventory: parts.inventory.getState(), buildBreak: parts.buildBreak.getState(), sequence: parts.sequence.getState(), world: parts.chunkStore.getState(), renderer: parts.renderer.getState(), input: parts.input.getState(), events: parts.events.recent(24), debug: { candidate: "infinite-voxel-domain-lab", moduleCount: 20 } }; },
    tick: parts.tick,
    rebuild: () => parts.renderer.rebuild(true),
    issueCommand(command) { if (command.type === "build.place.request") return parts.buildBreak.requestPlace(command.x, command.y, command.z, command.blockId, command.commandId); if (command.type === "block.break.request") return parts.buildBreak.requestBreak(command.x, command.y, command.z, command.commandId); return null; }
  };
}''')
    add("src/main.js", '''import { createCommandQueue } from "./runtime/commandQueue.js";
import { createEventBus } from "./runtime/eventBus.js";
import { createClock } from "./runtime/clock.js";
import { createChunkStore } from "./world/chunkStore.js";
import { createInventoryDomain } from "./domains/inventoryDomain.js";
import { createBuildBreakDomain } from "./domains/buildBreakDomain.js";
import { createMovementDomain } from "./domains/movementDomain.js";
import { createObjectiveSequence } from "./domains/objectiveSequence.js";
import { createThreeRenderer } from "./renderer/threeRenderer.js";
import { createInputAdapter } from "./host/inputAdapter.js";
import { createHud } from "./host/hud.js";
import { installGameHost } from "./host/gameHost.js";
const canvas = document.querySelector("#game"); const status = document.querySelector("#status"); const inventoryEl = document.querySelector("#inventory"); const inputEl = document.querySelector("#inputSurface"); const errorPanel = document.querySelector("#errorPanel");
function showFatal(error) { errorPanel.hidden = false; errorPanel.textContent = String(error?.stack ?? error?.message ?? error); }
try {
  const commandQueue = createCommandQueue(); const events = createEventBus(); const clock = createClock(); const chunkStore = createChunkStore({ chunkSize: 16, radius: 3 });
  const inventory = createInventoryDomain({ events }); const movement = createMovementDomain({ events, chunkStore }); const buildBreak = createBuildBreakDomain({ chunkStore, inventory, events, commandQueue }); const sequence = createObjectiveSequence({ movement, events });
  const renderer = createThreeRenderer({ canvas, chunkStore, movement }); renderer.rebuild(true); const input = createInputAdapter({ canvas, movement, inventory, buildBreak, renderer }); const hud = createHud({ status, inventoryEl, inputEl });
  function tick(dt = 1 / 60) { const time = clock.tick(dt); input.flush(); movement.tick(time.dt); buildBreak.tick(); sequence.observeBuildBreak(buildBreak); sequence.tick(); renderer.rebuild(); renderer.draw(); hud.draw(window.GameHost.getState()); }
  installGameHost({ clock, events, chunkStore, inventory, movement, buildBreak, sequence, renderer, input, tick });
  let last = performance.now(); function frame(now) { const dt = Math.min(1 / 30, (now - last) / 1000 || 1 / 60); last = now; tick(dt); requestAnimationFrame(frame); }
  status.textContent = "Infinite voxel domain lab ready"; requestAnimationFrame(frame);
} catch (error) { showFatal(error); }''')
    add("tests/smoke.mjs", '''import assert from "node:assert/strict";
import { createCommandQueue } from "../src/runtime/commandQueue.js";
const queue = createCommandQueue();
assert.equal(queue.markApplied("cmd-1"), true);
assert.equal(queue.markApplied("cmd-1"), false);
console.log("smoke passed");''', "test")
    return files
