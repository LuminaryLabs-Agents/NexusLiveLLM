import { PLACEABLE_BLOCKS, BLOCK_BY_ID } from "../data/blocks.js";
export function createInventoryDomain({ events }) {
  const state = { selectedBlockId: PLACEABLE_BLOCKS[0].id, palette: PLACEABLE_BLOCKS, counts: Object.fromEntries(PLACEABLE_BLOCKS.map((block) => [block.id, 999])), inventoryLedger: [] };
  return {
    select(blockId, commandId = `inventory.select:${blockId}`) { const found = state.palette.find((block) => block.id === Number(blockId)); if (!found) { events.emit("inventory.command.rejected", { commandId, reason: "unknown block" }); return state; } state.selectedBlockId = found.id; state.inventoryLedger.push(commandId); events.emit("inventory.selected", { commandId, blockId: found.id, blockName: found.name }); return state; },
    consume(blockId, commandId) { if ((state.counts[blockId] ?? 0) <= 0) { events.emit("inventory.command.rejected", { commandId, reason: "empty stack" }); return false; } state.counts[blockId] -= 1; events.emit("inventory.consumed", { commandId, blockId }); return true; },
    getSelectedBlock() { return state.selectedBlockId; },
    getSelectedName() { return BLOCK_BY_ID[state.selectedBlockId]?.name ?? "block"; },
    getState() { return { ...state, selectedName: this.getSelectedName(), inventoryLedger: state.inventoryLedger.slice(-24) }; }
  };
}
