export const worldPatchAdapter = {
  kit: "protokit.world-patch-kit",
  expectedState: ["loadedChunks", "recentlyUnloaded", "revision"],
  fallback: "src/world/worldLoader.js",
  proof(state) { return Number.isFinite(state?.worldLoader?.loadedChunks) && Number.isFinite(state?.worldLoader?.revision); }
};
