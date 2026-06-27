from __future__ import annotations

from .voxel_world_files_v3 import build_voxel_world_files


def build_voxel_composition_files(candidate_id: str, title: str, summary: str) -> list[dict[str, str]]:
    files = build_voxel_world_files(candidate_id, title, summary)
    base = f"docs/games/{candidate_id}/"
    by_path = {item["path"]: dict(item) for item in files}

    def upsert(path: str, content: str, kind: str = "source") -> None:
        by_path[base + path] = {"path": base + path, "kind": kind, "content": content.rstrip() + "\n"}

    upsert("index.html", f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{title}</title>
  <link rel="stylesheet" href="./style.css" />
  <script type="importmap">
  {{
    "imports": {{
      "@nexus/core": "https://cdn.jsdelivr.net/gh/LuminaryLabs-Dev/NexusRealtime@main/src/index.js",
      "@protokits/action-input": "https://cdn.jsdelivr.net/gh/LuminaryLabs-Agents/NexusRealtime-ProtoKits@main/protokits/action-input-kit/index.js",
      "three": "https://unpkg.com/three@0.160.0/build/three.module.js"
    }}
  }}
  </script>
</head>
<body>
  <main id="app">
    <canvas id="game"></canvas>
    <section id="hud"></section>
    <section id="inventory"></section>
    <section id="inputSurface"></section>
    <section id="errorPanel" hidden></section>
  </main>
  <script type="module" src="./src/boot.js"></script>
</body>
</html>''', "html")

    upsert("src/main.js", 'import "./boot.js";')
    upsert("src/boot.js", '''import { bootGame } from "./game/bootGame.js";
import { resolveAllKits } from "./integration/nexusRuntimeAdapter.js";
const kits = await resolveAllKits();
await bootGame({ kits });''')
    upsert("src/integration/kitResolver.js", '''export async function resolveStaticKit(id, module, fallback) {
  return module ? { id, provider: "remote-kit", module, ok: true, error: null } : { id, provider: "local-fallback", module: fallback, ok: false, error: "module unavailable" };
}
export function summarizeResolved(kits) {
  const resolved = {}; const failures = [];
  for (const [key, value] of Object.entries(kits)) { if (value?.provider) { resolved[key] = value.provider; if (value.error) failures.push({ id: key, error: value.error }); } }
  return { mode: "import-map-with-local-fallback", resolved, failures };
}''')
    upsert("src/integration/nexusRuntimeAdapter.js", '''import * as nexusCore from "@nexus/core";
import * as actionInput from "@protokits/action-input";
import { resolveStaticKit, summarizeResolved } from "./kitResolver.js";
import { createLocalRuntime } from "../runtime/localRuntime.js";
export async function resolveAllKits() {
  const runtime = await resolveStaticKit("runtime", nexusCore, createLocalRuntime());
  const input = await resolveStaticKit("input", actionInput, { surface: "local input adapter" });
  const domainService = await resolveStaticKit("domainService", nexusCore, { surface: "local DSK-shaped domains" });
  const kits = { runtime, input, domainService, worldLoader: { id: "worldLoader", provider: "local-fallback" }, terrain: { id: "terrain", provider: "local-fallback" } };
  return { ...kits, getState() { return summarizeResolved(kits); } };
}''')
    upsert("src/integration/protokitAdapter.js", '''export const protokitAdapter = { mode: "static-import-with-local-fallback" };''')
    upsert("src/runtime/localRuntime.js", '''export function createLocalRuntime() { return { surface: "local runtime fallback" }; }''')
    upsert("src/game/bootGame.js", '''import "../main.js"; export async function bootGame() {}''')
    return list(by_path.values())
