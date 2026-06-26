export function createMovementDomain({ events }) {
  const state = { player: { x: 0, y: 7, z: 10, yaw: 0, pitch: -0.12 }, inputIntent: { forward: 0, strafe: 0, turn: 0 }, movementTrace: [] };
  return {
    requestInput(intent, commandId) { state.inputIntent = { ...state.inputIntent, ...intent }; const event = events.emit("movement.input.accepted", { commandId, intent: state.inputIntent }); state.movementTrace.push(event); if (state.movementTrace.length > 20) state.movementTrace.shift(); },
    tick(dt) { const p = state.player; p.yaw += state.inputIntent.turn * dt * 1.8; p.x += Math.sin(p.yaw) * state.inputIntent.forward * dt * 6 + Math.cos(p.yaw) * state.inputIntent.strafe * dt * 6; p.z += -Math.cos(p.yaw) * state.inputIntent.forward * dt * 6 + Math.sin(p.yaw) * state.inputIntent.strafe * dt * 6; },
    getPlayer() { return state.player; },
    getState() { return { ...state, movementTrace: state.movementTrace.slice(-8) }; }
  };
}
