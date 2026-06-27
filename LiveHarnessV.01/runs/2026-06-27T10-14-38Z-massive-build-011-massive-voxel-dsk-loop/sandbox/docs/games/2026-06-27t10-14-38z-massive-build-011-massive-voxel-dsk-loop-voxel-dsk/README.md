# Massive Voxel DSK Loop Lab

Build a multi-file Three.js voxel world experiment that validates NexusRealtime domain-service boundaries through sandbox-first build loops.

A browser-playable NexusRealtime block-world testbed with procedural terrain, top-of-world spawn, world loading, HUD, inventory, input proof surface, and repeat-safe domain commands.

## Play

- WASD: move
- Mouse: look after clicking the canvas
- Left click: clear block
- Right click: place selected block
- 1-7: select inventory block
- F: toggle fly mode

`window.GameHost.getState()` exposes player, world, worldLoader, inventory, buildBreak, domainTrace, events, input, sequence, renderer diagnostics, and debug state.
