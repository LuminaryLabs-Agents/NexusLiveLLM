export function createBuildBreakDomain({ chunkStore, inventory, events, commandQueue }) {
  const domainTrace = [];
  function record(event) { domainTrace.push(event); if (domainTrace.length > 64) domainTrace.shift(); }
  function accept(command) { if (!command.commandId || !commandQueue.markApplied(command.commandId)) return { ok: false, duplicate: true }; if (Math.abs(command.y) > 80) { const rejected = events.emit("build.command.rejected", { commandId: command.commandId, reason: "outside vertical build limit" }); record(rejected); return { ok: false, rejected }; } if (command.type === "build.place.request") { const blockId = command.blockId ?? inventory.getSelectedBlock(); chunkStore.setBlock(command.x, command.y, command.z, blockId); const event = events.emit("build.block.placed", { commandId: command.commandId, x: command.x, y: command.y, z: command.z, blockId }); record(event); return { ok: true, event }; } if (command.type === "block.break.request") { chunkStore.setBlock(command.x, command.y, command.z, 0); const event = events.emit("build.block.removed", { commandId: command.commandId, x: command.x, y: command.y, z: command.z }); record(event); return { ok: true, event }; } return { ok: false }; }
  return {
    requestPlace(x, y, z, blockId, commandId) { return commandQueue.push({ type: "build.place.request", commandId, x, y, z, blockId }); },
    requestBreak(x, y, z, commandId) { return commandQueue.push({ type: "block.break.request", commandId, x, y, z }); },
    tick() { for (const command of commandQueue.drain("build.place.request")) accept(command); for (const command of commandQueue.drain("block.break.request")) accept(command); },
    getState() { return { domain: "build-break-domain-service-kit", commands: ["build.place.request", "block.break.request"], events: events.recent(16), domainTrace: domainTrace.slice(), appliedCommandIds: commandQueue.getState().appliedCommandIds }; }
  };
}
