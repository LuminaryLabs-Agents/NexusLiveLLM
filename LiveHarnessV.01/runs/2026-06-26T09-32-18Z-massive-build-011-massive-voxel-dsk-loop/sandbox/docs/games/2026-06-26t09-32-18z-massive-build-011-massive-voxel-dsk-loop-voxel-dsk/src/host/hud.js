import { BLOCK_BY_ID } from "../data/blocks.js";
export function createHud({ status }) { return { draw(snapshot) { const block = BLOCK_BY_ID[snapshot.inventory.selectedBlockId]?.name ?? "block"; status.textContent = `Biome samples ${snapshot.sequence.visitedBiomes.length}/3 · Block ${block} · Domain events ${snapshot.buildBreak.domainTrace.length}`; } }; }
