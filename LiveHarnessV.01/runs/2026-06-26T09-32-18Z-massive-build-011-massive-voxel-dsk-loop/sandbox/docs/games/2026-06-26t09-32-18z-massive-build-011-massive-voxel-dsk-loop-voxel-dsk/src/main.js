import { createCommandQueue } from "./runtime/commandQueue.js";
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
} catch (error) { showFatal(error); }
