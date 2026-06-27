export function createMovementDomain({ events, chunkStore, spawnPoint }) {
  const state = { player: { ...(spawnPoint ?? { x: 0, y: 12, z: 0, yaw: 0, pitch: -0.12, fly: false }) }, inputIntent: { forward: 0, strafe: 0, rise: 0, turn: 0, pitch: 0 }, movementTrace: [] };
  function clampPitch(value) { return Math.max(-1.25, Math.min(1.1, value)); }
  function groundY() { return chunkStore.getSurfaceY(Math.round(state.player.x), Math.round(state.player.z)) + 2.15; }
  return {
    requestInput(intent, commandId) { state.inputIntent = { ...state.inputIntent, ...intent }; const event = events.emit("movement.input.accepted", { commandId, intent: state.inputIntent }); state.movementTrace.push(event); if (state.movementTrace.length > 32) state.movementTrace.shift(); },
    rotate(dx, dy, commandId) { state.player.yaw -= dx * 0.0028; state.player.pitch = clampPitch(state.player.pitch - dy * 0.0022); events.emit("camera.look.updated", { commandId, yaw: state.player.yaw, pitch: state.player.pitch }); },
    toggleFly(commandId) { state.player.fly = !state.player.fly; if (!state.player.fly) state.player.y = groundY(); events.emit("movement.mode.changed", { commandId, fly: state.player.fly }); },
    tick(dt) { const p = state.player; const speed = p.fly ? 15 : 8; p.yaw += state.inputIntent.turn * dt * 1.8; p.pitch = clampPitch(p.pitch + state.inputIntent.pitch * dt); p.x += Math.sin(p.yaw) * state.inputIntent.forward * dt * speed + Math.cos(p.yaw) * state.inputIntent.strafe * dt * speed; p.z += -Math.cos(p.yaw) * state.inputIntent.forward * dt * speed + Math.sin(p.yaw) * state.inputIntent.strafe * dt * speed; if (p.fly) p.y += state.inputIntent.rise * dt * speed; else { const gy = groundY(); p.y += (gy - p.y) * Math.min(1, dt * 12); } },
    getPlayer() { return state.player; },
    getState() { return { ...state, biome: chunkStore.biomeAt(Math.round(state.player.x), Math.round(state.player.z)), surfaceY: chunkStore.getSurfaceY(Math.round(state.player.x), Math.round(state.player.z)), movementTrace: state.movementTrace.slice(-12) }; }
  };
}
