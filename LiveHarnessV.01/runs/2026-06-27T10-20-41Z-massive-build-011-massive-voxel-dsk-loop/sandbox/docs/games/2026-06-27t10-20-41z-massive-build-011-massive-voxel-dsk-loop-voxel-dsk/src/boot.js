import { resolveAllKits } from "./integration/nexusRuntimeAdapter.js";
const kits = await resolveAllKits();
window.__KitResolution = kits.getState ? kits.getState() : { mode: "local-fallback" };
await import("./game/bootGame.js");
