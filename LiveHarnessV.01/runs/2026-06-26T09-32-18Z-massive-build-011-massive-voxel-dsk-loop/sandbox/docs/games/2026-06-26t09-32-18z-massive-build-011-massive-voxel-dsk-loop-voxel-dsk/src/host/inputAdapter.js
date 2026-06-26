export function createInputAdapter({ canvas, movement, inventory, buildBreak, renderer }) {
  const keys = new Set(); let frame = 0;
  addEventListener("keydown", (event) => { keys.add(event.key.toLowerCase()); const number = Number(event.key); if (number >= 1 && number <= 5) inventory.select(number, `inventory.select:${frame}:${number}`); });
  addEventListener("keyup", (event) => keys.delete(event.key.toLowerCase())); addEventListener("blur", () => keys.clear());
  canvas.addEventListener("contextmenu", (event) => event.preventDefault());
  canvas.addEventListener("pointerdown", (event) => { const target = renderer.getForwardTarget(4); if (event.button === 2) buildBreak.requestPlace(target.x, target.y, target.z, inventory.getSelectedBlock(), `place:${frame}:${target.x}:${target.y}:${target.z}`); else buildBreak.requestBreak(target.x, target.y, target.z, `break:${frame}:${target.x}:${target.y}:${target.z}`); });
  return { flush() { frame += 1; movement.requestInput({ forward: (keys.has("w") || keys.has("arrowup") ? 1 : 0) - (keys.has("s") || keys.has("arrowdown") ? 1 : 0), strafe: (keys.has("d") ? 1 : 0) - (keys.has("a") ? 1 : 0), turn: (keys.has("arrowleft") ? 1 : 0) - (keys.has("arrowright") ? 1 : 0) }, `movement.input:${frame}`); } };
}
