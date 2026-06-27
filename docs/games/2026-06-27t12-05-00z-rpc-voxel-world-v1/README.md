# RPC Voxel World V1

A browser-playable voxel world where every game action is routed through a small local RPC command bus before mutating world/domain state.

## Controls

- Click the canvas to lock the pointer.
- WASD moves.
- Mouse looks.
- Space rises when fly is on.
- Shift descends when fly is on.
- F toggles fly.
- 1-8 selects a block.
- Left click clears the targeted block.
- Right click places the selected block.
- R reseeds the world.

## Architecture

- Client input emits RPC calls.
- RPC server validates command IDs and applies mutations.
- World loader maintains an active chunk window around the player.
- Terrain is procedural and reloads as the player moves.
- GameHost exposes player, worldLoader, inventory, RPC trace, and domain state.
