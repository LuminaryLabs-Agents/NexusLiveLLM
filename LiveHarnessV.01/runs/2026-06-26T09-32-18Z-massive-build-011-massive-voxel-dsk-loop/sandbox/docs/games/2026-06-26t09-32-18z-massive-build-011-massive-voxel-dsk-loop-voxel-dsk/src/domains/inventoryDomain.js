import { PLACEABLE_BLOCKS } from "../data/blocks.js";
export function createInventoryDomain({ events }) {
  const state = { selectedBlockId: PLACEABLE_BLOCKS[0].id, palette: PLACEABLE_BLOCKS, ledger: [] };
  return {
    select(blockId, commandId = `inventory.select:${blockId}`) { const found = state.palette.find((block) => block.id === Number(blockId)); if (!found) { events.emit("inventory.command.rejected", { commandId, reason: "unknown block" }); return state; } state.selectedBlockId = found.id; state.ledger.push(commandId); events.emit("inventory.selected", { commandId, blockId: found.id }); return state; },
    getSelectedBlock() { return state.selectedBlockId; },
    getState() { return { ...state, ledger: state.ledger.slice(-12) }; }
  };
}
