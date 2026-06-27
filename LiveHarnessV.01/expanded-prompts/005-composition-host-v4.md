---
mode: kit-builder
public_title: Composition Host Voxel Lab V4
public_goal: Build a browser playable block-world domain lab with a bounded HTML shell, import map, boot module, NexusRealtime and ProtoKit composition attempts, local fallbacks, top-of-world spawn, world loading, HUD, inventory, input surface, and GameHost integration diagnostics.
---

# Product Requirements

Create a composition-first voxel/domain testbed that works immediately in the browser.

Required shell:

- index.html must be a thin bounded host shell
- include an import map for NexusRealtime core, ProtoKits action input, and Three.js
- load only src/boot.js as the boot module
- no gameplay logic in HTML

Required kit composition:

- boot module resolves NexusRealtime and ProtoKit capability surfaces first
- local fallbacks remain available when a remote module is unavailable
- GameHost exposes integration mode, selected providers, and any fallback failures

Required gameplay:

- player spawns on top of the generated world
- procedural world loading around the player
- HUD, inventory, input surface, movement, place and clear block commands
- DSK-shaped command trace with command IDs
- renderer presents state only
