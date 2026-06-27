export function createObjectiveSequence({ movement, events }) {
  const state = { current: "sample three biomes and place a marker block", visitedBiomes: [], placedBlocks: 0, completed: false };
  return {
    observeBuildBreak(buildBreak) { const placed = buildBreak.getState().domainTrace.filter((event) => event.type === "build.block.placed").length; state.placedBlocks = placed; },
    tick() { const biome = movement.getState().biome; if (!state.visitedBiomes.includes(biome)) { state.visitedBiomes.push(biome); events.emit("sequence.objective.updated", { biome, visitedBiomes: state.visitedBiomes.slice() }); } if (state.visitedBiomes.length >= 3 && state.placedBlocks >= 1 && !state.completed) { state.completed = true; events.emit("sequence.completed", { objective: state.current }); } },
    getState() { return { ...state }; }
  };
}
