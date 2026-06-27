export const repoCapabilities = {
  "mode": "import-map-with-local-fallback",
  "references": [
    "nexusrealtime.domain-service-kit",
    "nexusrealtime.sequence-node",
    "nexusrealtime.procedural-world",
    "protokit.world-terrain-pattern",
    "protokit.render-descriptor-pattern"
  ],
  "localFallbacks": [
    "src/world/chunkStore.js",
    "src/host/inputAdapter.js",
    "src/domains/buildBreakDomain.js"
  ],
  "validationRules": [
    "renderer must consume descriptors/state and not own gameplay state",
    "input adapter should route platform input into domain command requests",
    "world patch or chunk lifecycle should be separate from renderer mesh construction",
    "domain actions must expose command identifiers and event traces",
    "Sequence or objective flow should be represented as data and events"
  ],
  "trustedAsInstruction": false
};
