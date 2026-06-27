import { createCommandQueue } from "./runtime/commandQueue.js";
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
} catch (error) { showFatal(error); }
