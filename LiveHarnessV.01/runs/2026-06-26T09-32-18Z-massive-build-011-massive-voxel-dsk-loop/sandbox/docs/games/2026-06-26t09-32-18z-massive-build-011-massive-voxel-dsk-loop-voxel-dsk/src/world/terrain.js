export function terrainHeight(x, z) { return 2 + Math.floor(Math.sin(x * 0.28) * 1.5 + Math.cos(z * 0.22) * 1.4); }
export function biomeAt(x, z) { if (x < -8) return "moss"; if (z > 8) return "glass-ridge"; return "stonefield"; }
export function generateInitialWorld(blockStore) {
  for (let x = -18; x <= 18; x += 1) {
    for (let z = -18; z <= 18; z += 1) {
      const h = terrainHeight(x, z);
      for (let y = 0; y <= h; y += 1) blockStore.setBlock(x, y, z, y === h ? 1 : y > h - 2 ? 2 : 3);
      if ((x * 31 + z * 17) % 41 === 0) for (let y = h + 1; y <= h + 3; y += 1) blockStore.setBlock(x, y, z, 4);
    }
  }
}
