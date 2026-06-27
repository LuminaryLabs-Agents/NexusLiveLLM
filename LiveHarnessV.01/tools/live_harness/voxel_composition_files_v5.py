from __future__ import annotations

from .voxel_composition_files_v4 import build_voxel_composition_files


def build_voxel_composition_files_v5(candidate_id: str, title: str, summary: str) -> list[dict[str, str]]:
    files = build_voxel_composition_files(candidate_id, title, summary)
    base = f"docs/games/{candidate_id}/"
    out = {item["path"]: dict(item) for item in files}
    out[base + "src/boot.js"] = {"path": base + "src/boot.js", "kind": "source", "content": '''import { resolveAllKits } from "./integration/nexusRuntimeAdapter.js";
const errorPanel = document.querySelector("#errorPanel");
function showFatal(error) { if (errorPanel) { errorPanel.hidden = false; errorPanel.textContent = String(error?.stack ?? error?.message ?? error); } }
resolveAllKits().then((kits) => {
  window.__KitResolution = kits.getState ? kits.getState() : { mode: "local-fallback" };
  return import("./game/bootGame.js");
}).catch(showFatal);
'''}
    out[base + "src/integration/kitResolver.js"] = {"path": base + "src/integration/kitResolver.js", "kind": "source", "content": '''export async function resolveByAlias(id, alias, fallback) {
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
'''}
    out[base + "src/integration/nexusRuntimeAdapter.js"] = {"path": base + "src/integration/nexusRuntimeAdapter.js", "kind": "source", "content": '''import { resolveByAlias, summarizeResolved } from "./kitResolver.js";
import { createLocalRuntime } from "../runtime/localRuntime.js";
export async function resolveAllKits() {
  const runtime = await resolveByAlias("runtime", "@nexus/core", createLocalRuntime());
  const input = await resolveByAlias("input", "@protokits/action-input", { surface: "local input adapter" });
  const domainService = await resolveByAlias("domainService", "@nexus/core", { surface: "local DSK-shaped domains" });
  const kits = { runtime, input, domainService, worldLoader: { id: "worldLoader", provider: "local-fallback" }, terrain: { id: "terrain", provider: "local-fallback" } };
  return { ...kits, getState() { return summarizeResolved(kits); } };
}
'''}
    return list(out.values())
