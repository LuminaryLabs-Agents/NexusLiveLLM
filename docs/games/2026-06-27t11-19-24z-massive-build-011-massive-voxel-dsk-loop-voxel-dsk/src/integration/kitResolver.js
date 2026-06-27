export async function resolveByAlias(id, alias, fallback) {
  try {
    const module = await import(alias);
    return { id, provider: "remote-kit", module, ok: true, error: null };
  } catch (error) {
    return { id, provider: "local-fallback", module: fallback, ok: false, error: String(error?.message ?? error) };
  }
}
export function summarizeResolved(kits) {
  const resolved = {}; const failures = [];
  for (const [key, value] of Object.entries(kits)) { if (value?.provider) { resolved[key] = value.provider; if (value.error) failures.push({ id: key, error: value.error }); } }
  return { mode: "import-map-with-local-fallback", resolved, failures };
}
