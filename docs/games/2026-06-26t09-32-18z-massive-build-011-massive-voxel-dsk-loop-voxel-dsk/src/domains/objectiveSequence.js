import { biomeAt } from "../world/terrain.js";
export function createObjectiveSequence({ movement, events }) {
  const state = { current: "sample three biomes", visitedBiomes: [], completed: false };
  return {
    tick() { const p = movement.getPlayer(); const biome = biomeAt(Math.round(p.x), Math.round(p.z)); if (!state.visitedBiomes.includes(biome)) { state.visitedBiomes.push(biome); events.emit("sequence.objective.updated", { biome, visitedBiomes: state.visitedBiomes.slice() }); } if (state.visitedBiomes.length >= 3 && !state.completed) { state.completed = true; events.emit("sequence.completed", { objective: state.current }); } },
    getState() { return { ...state }; }
  };
}
