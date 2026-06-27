export function createClock() {
  let frame = 0;
  let elapsed = 0;
  return {
    tick(dt) { const safeDt = Math.max(0, Math.min(1 / 20, Number(dt) || 1 / 60)); frame += 1; elapsed += safeDt; return { frame, dt: safeDt, elapsed }; },
    getState() { return { frame, elapsed }; }
  };
}
