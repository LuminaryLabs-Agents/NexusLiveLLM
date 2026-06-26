export function installGameHost(parts) {
  window.GameHost = {
    getState() { return { clock: parts.clock.getState(), movement: parts.movement.getState(), inventory: parts.inventory.getState(), buildBreak: parts.buildBreak.getState(), sequence: parts.sequence.getState(), world: parts.blockStore.getState(), events: parts.events.recent(16) }; },
    tick: parts.tick,
    rebuild: parts.renderer.rebuild
  };
}
