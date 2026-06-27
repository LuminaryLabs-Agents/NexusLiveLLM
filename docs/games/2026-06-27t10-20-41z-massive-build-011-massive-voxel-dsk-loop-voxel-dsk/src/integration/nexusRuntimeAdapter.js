import * as nexusCore from "@nexus/core";
import * as actionInput from "@protokits/action-input";
import { resolveStaticKit, summarizeResolved } from "./kitResolver.js";
import { createLocalRuntime } from "../runtime/localRuntime.js";
export async function resolveAllKits() {
  const runtime = await resolveStaticKit("runtime", nexusCore, createLocalRuntime());
  const input = await resolveStaticKit("input", actionInput, { surface: "local input adapter" });
  const domainService = await resolveStaticKit("domainService", nexusCore, { surface: "local DSK-shaped domains" });
  const kits = { runtime, input, domainService, worldLoader: { id: "worldLoader", provider: "local-fallback" }, terrain: { id: "terrain", provider: "local-fallback" } };
  return { ...kits, getState() { return summarizeResolved(kits); } };
}
