export function installGameHost(parts) {
  window.GameHost = {
    getState() {
      return { clock: parts.clock.getState(), movement: parts.movement.getState(), inventory: parts.inventory.getState(), buildBreak: parts.buildBreak.getState(), sequence: parts.sequence.getState(), world: parts.chunkStore.getState(), worldLoader: parts.worldLoader.getState(), renderer: parts.renderer.getState(), input: parts.input.getState(), events: parts.events.recent(24), integration: window.__KitResolution || { mode: "local-fallback" }, debug: { candidate: "composition-host-v4", spawn: parts.spawnPoint } };
    },
    tick: parts.tick,
    rebuild: () => { parts.worldLoader.forceRefresh(); parts.renderer.rebuild(true); },
    issueCommand(command) { if (command.type === "build.place.request") return parts.buildBreak.requestPlace(command.x, command.y, command.z, command.blockId, command.commandId); if (command.type === "block.break.request") return parts.buildBreak.requestBreak(command.x, command.y, command.z, command.commandId); return null; }
  };
}
