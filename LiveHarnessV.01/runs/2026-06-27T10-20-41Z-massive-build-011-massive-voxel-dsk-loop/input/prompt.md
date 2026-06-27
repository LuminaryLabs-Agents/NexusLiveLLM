---
mode: kit-builder
public_title: Massive Voxel DSK Loop Lab
public_goal: Build a multi-file Three.js voxel world experiment that validates NexusRealtime domain-service boundaries through sandbox-first build loops.
private_harness_notes:
  - run the massive one-commit workflow
  - use sandbox-first writes
  - validate file filters before public promotion
---

# Product Requirements

Create a browser-playable voxel experiment with:

- Runtime modules for command queue, event bus, and tick clock
- BuildBreakDSK with build.place.request and block.break.request commands
- InventoryDSK with selected block palette state
- MovementControl domain with state-scoped movement intent
- Sequence objective state that guides biome sampling
- Three.js renderer that presents state only
- window.GameHost.getState() exposing player, world, inventory, domainTrace, events, and sequence state
- concise public HUD and controls

The game must promote from sandbox only after public-output, module graph, DSK boundary, renderer boundary, GameHost, and syntax filters pass.
