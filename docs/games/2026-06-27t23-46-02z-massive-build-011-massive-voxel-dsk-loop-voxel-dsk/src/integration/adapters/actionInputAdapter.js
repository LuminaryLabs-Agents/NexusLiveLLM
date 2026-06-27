export const actionInputAdapter = {
  kit: "protokit.action-input-kit",
  expectedHostInput: ["keydown", "keyup", "pointer"],
  semanticEvents: ["movement.input.request", "inventory.select.request"],
  fallback: "src/host/inputAdapter.js",
  proof(state) { return Boolean(state?.input && state?.movement); }
};
