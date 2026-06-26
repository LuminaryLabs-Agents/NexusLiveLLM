export function createBlockStore() {
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
}
