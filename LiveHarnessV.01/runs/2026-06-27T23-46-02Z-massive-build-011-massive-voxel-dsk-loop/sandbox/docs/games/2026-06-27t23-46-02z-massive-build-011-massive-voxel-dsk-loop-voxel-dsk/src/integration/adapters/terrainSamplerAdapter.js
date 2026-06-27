export const terrainSamplerAdapter = {
  kit: "protokit.terrain-sampler-kit",
  expectedState: ["surfaceY", "biome"],
  fallback: "src/world/chunkStore.js",
  proof(state) { return state?.movement?.biome && Number.isFinite(state?.movement?.surfaceY); }
};
