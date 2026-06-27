import { resolveByAlias, summarizeResolved } from "./kitResolver.js";
import { createLocalRuntime } from "../runtime/localRuntime.js";
export async function resolveAllKits() {
  const runtime = await resolveByAlias("runtime", "@nexus/core", createLocalRuntime());
  const input = await resolveByAlias("input", "@protokits/action-input", { surface: "local input adapter" });
  const domainService = await resolveByAlias("domainService", "@nexus/core", { surface: "local DSK-shaped domains" });
  const kits = { runtime, input, domainService, worldLoader: { id: "worldLoader", provider: "local-fallback" }, terrain: { id: "terrain", provider: "local-fallback" } };
  return { ...kits, getState() { return summarizeResolved(kits); } };
}
