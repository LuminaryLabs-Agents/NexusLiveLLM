---
mode: kit-builder
public_title: Full Block World Domain Lab V3
public_goal: Build a full browser playable block-world survival-style testbed with repo-aware intake, top-of-world player spawn, infinite procedural world loading, HUD, inventory, input test surface, and repeat-safe domain service boundaries.
---

# Product Requirements

Create a full first-pass block-world game that works immediately in the browser and is not just a small terrain demo.

Required play surface:

- Player spawns on top of the generated world at a safe surface point
- Infinite procedural terrain loads around the player through a world loading system
- Chunk or patch lifecycle state exposes loaded chunks, unloaded chunks, visible blocks, and revision
- Three.js renderer with camera, fog, lighting, instanced block meshes, and visible chunk radius
- HUD with biome, objective, selected block, domain event count, loaded chunk count, and fly mode
- Inventory bar with selectable blocks
- Input testing surface that shows keys, mouse lock state, and last command
- WASD movement, mouse look, numbered inventory selection, left click clear block, right click place block, F toggle fly
- Place and clear actions routed through domain commands with command IDs
- GameHost state exposing player, world, worldLoader, inventory, domainTrace, events, input, sequence, renderer diagnostics, and debug state
- Objective sequence for biome exploration and block placement

Architecture requirements:

- Run source intake loops for NexusRealtime core, NexusRealtime ProtoKits, and KitBuilder03 local structure before the build swarm
- Runtime modules own command queue, event bus, and clock
- Movement domain owns input intent and player state
- Inventory domain owns selected block and block counts
- Build domain owns command trace, applied IDs, and world updates
- World loader owns active chunk windows and load/unload lifecycle
- Sequence domain owns objective state
- Renderer presents state only
- Host maps input into domain requests
