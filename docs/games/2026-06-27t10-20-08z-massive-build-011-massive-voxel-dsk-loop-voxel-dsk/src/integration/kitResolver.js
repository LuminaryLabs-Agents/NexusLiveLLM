export async function resolveStaticKit(id, module, fallback) {
  return module ? { id, provider: "remote-kit", module, ok: true, error: null } : { id, provider: "local-fallback", module: fallback, ok: false, error: "module unavailable" };
}
export function summarizeResolved(kits) {
  const resolved = {}; const failures = [];
  for (const [key, value] of Object.entries(kits)) { if (value?.provider) { resolved[key] = value.provider; if (value.error) failures.push({ id: key, error: value.error }); } }
  return { mode: "import-map-with-local-fallback", resolved, failures };
}
