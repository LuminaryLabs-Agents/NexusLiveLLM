export function createCommandQueue() {
  const queue = [];
  const appliedCommandIds = new Set();
  return {
    push(command) { queue.push({ ...command }); return command; },
    drain(type) { const picked = queue.filter((command) => command.type === type); for (const command of picked) queue.splice(queue.indexOf(command), 1); return picked; },
    markApplied(commandId) { if (!commandId || appliedCommandIds.has(commandId)) return false; appliedCommandIds.add(commandId); return true; },
    hasApplied(commandId) { return appliedCommandIds.has(commandId); },
    getState() { return { pending: queue.slice(), appliedCommandIds: Array.from(appliedCommandIds).slice(-48) }; }
  };
}
