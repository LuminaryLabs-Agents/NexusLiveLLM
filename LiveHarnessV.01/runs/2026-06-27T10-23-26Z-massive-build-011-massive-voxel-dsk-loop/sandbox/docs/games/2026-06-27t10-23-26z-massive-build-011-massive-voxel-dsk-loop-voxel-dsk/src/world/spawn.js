export function createSpawnPoint(chunkStore, preferred = { x: 0, z: 0 }) {
  const x = Math.round(preferred.x ?? 0);
  const z = Math.round(preferred.z ?? 0);
  const surfaceY = chunkStore.getSurfaceY ? chunkStore.getSurfaceY(x, z) : chunkStore.heightAt(x, z);
  return { x, y: surfaceY + 2.15, z, yaw: 0, pitch: -0.12, fly: false };
}
