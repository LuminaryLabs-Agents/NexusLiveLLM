export function createWorldLoader({ chunkStore, radius = 4, unloadMargin = 2 } = {}) {
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
}
