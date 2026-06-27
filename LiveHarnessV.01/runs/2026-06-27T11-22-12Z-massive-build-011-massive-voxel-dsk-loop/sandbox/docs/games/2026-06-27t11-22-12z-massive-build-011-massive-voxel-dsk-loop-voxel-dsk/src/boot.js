import { resolveAllKits } from "./integration/nexusRuntimeAdapter.js";
const errorPanel = document.querySelector("#errorPanel");
function showFatal(error) { if (errorPanel) { errorPanel.hidden = false; errorPanel.textContent = String(error?.stack ?? error?.message ?? error); } }
resolveAllKits().then((kits) => {
  window.__KitResolution = kits.getState ? kits.getState() : { mode: "local-fallback" };
  return import("./main.js");
}).catch(showFatal);
