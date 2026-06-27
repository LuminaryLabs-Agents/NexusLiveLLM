from __future__ import annotations

from .voxel_clone_files import build_voxel_clone_files as build_base_files


def build_voxel_world_files(candidate_id: str, title: str, summary: str) -> list[dict[str, str]]:
    files = build_base_files(candidate_id, title, summary)
    base = f"docs/games/{candidate_id}/"
    by_path = {item["path"]: dict(item) for item in files}

    def upsert(path: str, content: str, kind: str = "source") -> None:
        by_path[base + path] = {"path": base + path, "kind": kind, "content": content.rstrip() + "\n"}

    upsert("README.md", f'''# {title}

{summary}

A browser-playable NexusRealtime block-world testbed with procedural terrain, top-of-world spawn, world loading, HUD, inventory, input proof surface, and repeat-safe domain commands.

## Play

- WASD: move
- Mouse: look after clicking the canvas
- Left click: clear block
- Right click: place selected block
- 1-7: select inventory block
- F: toggle fly mode

`window.GameHost.getState()` exposes player, world, worldLoader, inventory, buildBreak, domainTrace, events, input, sequence, renderer diagnostics, and debug state.
''', "readme")

    upsert("src/world/spawn.js", '''export function createSpawnPoint(chunkStore, preferred = { x: 0, z: 0 }) {
  const x = Math.round(preferred.x ?? 0);
  const z = Math.round(preferred.z ?? 0);
  const surfaceY = chunkStore.getSurfaceY ? chunkStore.getSurfaceY(x, z) : chunkStore.heightAt(x, z);
  return { x, y: surfaceY + 2.15, z, yaw: 0, pitch: -0.12, fly: false };
}''')

    upsert("src/world/worldLoader.js", '''export function createWorldLoader({ chunkStore, radius = 4, unloadMargin = 2 } = {}) {
  const loaded = new Map();
  const recentlyUnloaded = [];
  let center = { cx: 0, cz: 0 };
  let revision = 0;
  function wantedChunks(player) {
    const cx0 = chunkStore.chunkOf(Math.round(player.x));
    const cz0 = chunkStore.chunkOf(Math.round(player.z));
    center = { cx: cx0, cz: cz0 };
    const want = new Map();
    for (let cx = cx0 - radius; cx <= cx0 + radius; cx += 1) for (let cz = cz0 - radius; cz <= cz0 + radius; cz += 1) { const desc = chunkStore.chunkDescriptor(cx, cz); want.set(desc.key, desc); }
    return want;
  }
  function tick(player) {
    const want = wantedChunks(player); let changed = false;
    for (const [key, desc] of want) if (!loaded.has(key)) { loaded.set(key, desc); changed = true; }
    for (const [key, desc] of Array.from(loaded.entries())) if (!want.has(key) && (Math.abs(desc.cx - center.cx) > radius + unloadMargin || Math.abs(desc.cz - center.cz) > radius + unloadMargin)) { loaded.delete(key); recentlyUnloaded.push(key); if (recentlyUnloaded.length > 32) recentlyUnloaded.shift(); changed = true; }
    if (changed) revision += 1;
    return changed;
  }
  function forceRefresh() { revision += 1; }
  function getVisibleBlocks() { return chunkStore.entriesForChunks(Array.from(loaded.values())); }
  return { tick, forceRefresh, getVisibleBlocks, getRevision() { return revision; }, getState() { return { center, radius, loadedChunks: loaded.size, revision, recentlyUnloaded: recentlyUnloaded.slice(-12), loadedSample: Array.from(loaded.keys()).slice(0, 16) }; } };
}''')

    upsert("src/world/chunkStore.js", '''import { heightAt, biomeAt, hash2 } from "./noise.js";
export function createChunkStore({ chunkSize = 16, radius = 4, verticalPadding = 8 } = {}) {
  const overrides = new Map(); const dirtyChunks = new Set(); const generatedChunkCache = new Map();
  const key = (x, y, z) => `${x},${y},${z}`; const chunkKey = (cx, cz) => `${cx},${cz}`; const chunkOf = (value) => Math.floor(value / chunkSize);
  function generatedBlock(x, y, z) { const h = heightAt(x, z); if (y < 0 || y > h + verticalPadding) return 0; if (y === h) { const biome = biomeAt(x, z); if (biome === "dunes") return 6; if (biome === "glass-ridge") return 5; if (biome === "stonefield") return 3; return 1; } if (y > h - 3) return 2; return 3; }
  function treeBlock(x, y, z) { const h = heightAt(x, z); const trunk = hash2(x, z) > 0.986 && biomeAt(x, z) === "moss"; if (!trunk) return 0; if (y > h && y <= h + 4) return 4; if (y > h + 4 && y <= h + 6 && Math.abs((x % 3 + 3) % 3 - 1) <= 1 && Math.abs((z % 3 + 3) % 3 - 1) <= 1) return 7; return 0; }
  function getBlock(x, y, z) { const override = overrides.get(key(x, y, z)); if (override !== undefined) return override; return treeBlock(x, y, z) || generatedBlock(x, y, z); }
  function setBlock(x, y, z, blockId) { overrides.set(key(x, y, z), blockId); dirtyChunks.add(chunkKey(chunkOf(x), chunkOf(z))); }
  function getSurfaceY(x, z) { for (let y = heightAt(x, z) + verticalPadding; y >= 0; y -= 1) if (getBlock(x, y, z)) return y; return heightAt(x, z); }
  function chunkDescriptor(cx, cz) { const k = chunkKey(cx, cz); if (!generatedChunkCache.has(k)) generatedChunkCache.set(k, { key: k, cx, cz, createdAt: performance.now?.() ?? Date.now(), biome: biomeAt(cx * chunkSize, cz * chunkSize) }); return generatedChunkCache.get(k); }
  function entriesForChunks(chunks) { const blocks = []; for (const chunk of chunks) { const cx = chunk.cx; const cz = chunk.cz; for (let lx = 0; lx < chunkSize; lx += 1) for (let lz = 0; lz < chunkSize; lz += 1) { const x = cx * chunkSize + lx; const z = cz * chunkSize + lz; const h = heightAt(x, z); for (let y = Math.max(0, h - 2); y <= h + verticalPadding; y += 1) { const blockId = getBlock(x, y, z); if (!blockId) continue; const exposed = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]].some(([a,b,c]) => !getBlock(x+a, y+b, z+c)); if (exposed) blocks.push({ x, y, z, blockId }); } } } return blocks; }
  function entriesNear(px, pz, viewRadius = radius) { const pcx = chunkOf(Math.round(px)); const pcz = chunkOf(Math.round(pz)); const chunks = []; for (let cx = pcx - viewRadius; cx <= pcx + viewRadius; cx += 1) for (let cz = pcz - viewRadius; cz <= pcz + viewRadius; cz += 1) chunks.push(chunkDescriptor(cx, cz)); return entriesForChunks(chunks); }
  return { getBlock, setBlock, entriesNear, entriesForChunks, key, chunkKey, chunkOf, chunkDescriptor, getSurfaceY, heightAt, biomeAt, getState() { return { overrides: overrides.size, dirtyChunks: Array.from(dirtyChunks).slice(-32), generatedChunks: generatedChunkCache.size, chunkSize, radius }; } };
}''')

    upsert("src/domains/movementDomain.js", '''export function createMovementDomain({ events, chunkStore, spawnPoint }) {
  const state = { player: { ...(spawnPoint ?? { x: 0, y: 12, z: 0, yaw: 0, pitch: -0.12, fly: false }) }, inputIntent: { forward: 0, strafe: 0, rise: 0, turn: 0, pitch: 0 }, movementTrace: [] };
  function clampPitch(value) { return Math.max(-1.25, Math.min(1.1, value)); }
  function groundY() { return chunkStore.getSurfaceY(Math.round(state.player.x), Math.round(state.player.z)) + 2.15; }
  return {
    requestInput(intent, commandId) { state.inputIntent = { ...state.inputIntent, ...intent }; const event = events.emit("movement.input.accepted", { commandId, intent: state.inputIntent }); state.movementTrace.push(event); if (state.movementTrace.length > 32) state.movementTrace.shift(); },
    rotate(dx, dy, commandId) { state.player.yaw -= dx * 0.0028; state.player.pitch = clampPitch(state.player.pitch - dy * 0.0022); events.emit("camera.look.updated", { commandId, yaw: state.player.yaw, pitch: state.player.pitch }); },
    toggleFly(commandId) { state.player.fly = !state.player.fly; if (!state.player.fly) state.player.y = groundY(); events.emit("movement.mode.changed", { commandId, fly: state.player.fly }); },
    tick(dt) { const p = state.player; const speed = p.fly ? 15 : 8; p.yaw += state.inputIntent.turn * dt * 1.8; p.pitch = clampPitch(p.pitch + state.inputIntent.pitch * dt); p.x += Math.sin(p.yaw) * state.inputIntent.forward * dt * speed + Math.cos(p.yaw) * state.inputIntent.strafe * dt * speed; p.z += -Math.cos(p.yaw) * state.inputIntent.forward * dt * speed + Math.sin(p.yaw) * state.inputIntent.strafe * dt * speed; if (p.fly) p.y += state.inputIntent.rise * dt * speed; else { const gy = groundY(); p.y += (gy - p.y) * Math.min(1, dt * 12); } },
    getPlayer() { return state.player; },
    getState() { return { ...state, biome: chunkStore.biomeAt(Math.round(state.player.x), Math.round(state.player.z)), surfaceY: chunkStore.getSurfaceY(Math.round(state.player.x), Math.round(state.player.z)), movementTrace: state.movementTrace.slice(-12) }; }
  };
}''')

    upsert("src/renderer/threeRenderer.js", '''import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";
import { createMaterials } from "./materials.js";
import { createCameraRig } from "./cameraRig.js";
export function createThreeRenderer({ canvas, worldLoader, movement }) {
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0x9dd3ff); scene.fog = new THREE.Fog(0x9dd3ff, 48, 170);
  const camera = new THREE.PerspectiveCamera(72, innerWidth / innerHeight, 0.1, 480);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true }); renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2)); renderer.setSize(innerWidth, innerHeight);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x3b6740, 1.35)); const sun = new THREE.DirectionalLight(0xffffff, 1.65); sun.position.set(32, 60, 20); scene.add(sun);
  const geometry = new THREE.BoxGeometry(1, 1, 1); const materials = createMaterials(THREE); const group = new THREE.Group(); scene.add(group); const rig = createCameraRig(camera); let lastRevision = -1; let visibleBlocks = 0;
  function rebuild(force = false) { const revision = worldLoader.getRevision(); if (!force && revision === lastRevision) return; lastRevision = revision; group.clear(); const buckets = new Map(); for (const block of worldLoader.getVisibleBlocks()) { if (!buckets.has(block.blockId)) buckets.set(block.blockId, []); buckets.get(block.blockId).push(block); } visibleBlocks = 0; for (const [blockId, blocks] of buckets) { visibleBlocks += blocks.length; const mesh = new THREE.InstancedMesh(geometry, materials[blockId], blocks.length); const helper = new THREE.Object3D(); blocks.forEach((block, index) => { helper.position.set(block.x, block.y, block.z); helper.updateMatrix(); mesh.setMatrixAt(index, helper.matrix); }); group.add(mesh); } }
  function draw() { rig.update(movement.getPlayer()); renderer.render(scene, camera); }
  function resize() { camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); renderer.setSize(innerWidth, innerHeight); }
  function getForwardTarget(distance = 5) { const p = movement.getPlayer(); const horiz = Math.cos(p.pitch); const x = Math.round(p.x + Math.sin(p.yaw) * horiz * distance); const z = Math.round(p.z - Math.cos(p.yaw) * horiz * distance); const y = Math.max(0, Math.round(p.y + Math.sin(-p.pitch) * distance - 2)); return { x, y, z }; }
  addEventListener("resize", resize);
  return { draw, rebuild, resize, getForwardTarget, getState() { return { visibleGroups: group.children.length, visibleBlocks, lastRevision, fog: true }; } };
}''')

    upsert("src/host/gameHost.js", '''export function installGameHost(parts) {
  window.GameHost = {
    getState() { return { clock: parts.clock.getState(), movement: parts.movement.getState(), inventory: parts.inventory.getState(), buildBreak: parts.buildBreak.getState(), sequence: parts.sequence.getState(), world: parts.chunkStore.getState(), worldLoader: parts.worldLoader.getState(), renderer: parts.renderer.getState(), input: parts.input.getState(), events: parts.events.recent(24), debug: { candidate: "repo-aware-voxel-domain-lab", moduleCount: 23, spawn: parts.spawnPoint } }; },
    tick: parts.tick,
    rebuild: () => { parts.worldLoader.forceRefresh(); parts.renderer.rebuild(true); },
    issueCommand(command) { if (command.type === "build.place.request") return parts.buildBreak.requestPlace(command.x, command.y, command.z, command.blockId, command.commandId); if (command.type === "block.break.request") return parts.buildBreak.requestBreak(command.x, command.y, command.z, command.commandId); return null; }
  };
}''')

    upsert("src/main.js", '''import { createCommandQueue } from "./runtime/commandQueue.js";
import { createEventBus } from "./runtime/eventBus.js";
import { createClock } from "./runtime/clock.js";
import { createChunkStore } from "./world/chunkStore.js";
import { createSpawnPoint } from "./world/spawn.js";
import { createWorldLoader } from "./world/worldLoader.js";
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
  const commandQueue = createCommandQueue(); const events = createEventBus(); const clock = createClock(); const chunkStore = createChunkStore({ chunkSize: 16, radius: 4 }); const spawnPoint = createSpawnPoint(chunkStore, { x: 0, z: 0 });
  const worldLoader = createWorldLoader({ chunkStore, radius: 4 }); const inventory = createInventoryDomain({ events }); const movement = createMovementDomain({ events, chunkStore, spawnPoint }); const buildBreak = createBuildBreakDomain({ chunkStore, inventory, events, commandQueue }); const sequence = createObjectiveSequence({ movement, events });
  worldLoader.tick(movement.getPlayer()); const renderer = createThreeRenderer({ canvas, worldLoader, movement }); renderer.rebuild(true); const input = createInputAdapter({ canvas, movement, inventory, buildBreak, renderer }); const hud = createHud({ status, inventoryEl, inputEl });
  function tick(dt = 1 / 60) { const time = clock.tick(dt); input.flush(); movement.tick(time.dt); const movedChunk = worldLoader.tick(movement.getPlayer()); buildBreak.tick(); sequence.observeBuildBreak(buildBreak); sequence.tick(); if (movedChunk) renderer.rebuild(true); else renderer.rebuild(); renderer.draw(); hud.draw(window.GameHost.getState()); }
  installGameHost({ clock, events, chunkStore, worldLoader, inventory, movement, buildBreak, sequence, renderer, input, spawnPoint, tick });
  let last = performance.now(); function frame(now) { const dt = Math.min(1 / 30, (now - last) / 1000 || 1 / 60); last = now; tick(dt); requestAnimationFrame(frame); }
  status.textContent = "Repo-aware voxel domain lab ready"; requestAnimationFrame(frame);
} catch (error) { showFatal(error); }''')

    upsert("tests/smoke.mjs", '''import assert from "node:assert/strict";
import { createCommandQueue } from "../src/runtime/commandQueue.js";
import { createChunkStore } from "../src/world/chunkStore.js";
import { createSpawnPoint } from "../src/world/spawn.js";
const queue = createCommandQueue();
assert.equal(queue.markApplied("cmd-1"), true);
assert.equal(queue.markApplied("cmd-1"), false);
const world = createChunkStore({ chunkSize: 16, radius: 2 });
const spawn = createSpawnPoint(world, { x: 0, z: 0 });
assert.ok(spawn.y > world.getSurfaceY(0, 0));
console.log("smoke passed");''', "test")

    return list(by_path.values())
