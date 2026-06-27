# Game Idea Inbox

Drop short Markdown idea files here to trigger a 10-game GameSpec batch.

## Format

Use a numbered file name so newest ideas sort clearly:

```txt
0001-rpc-voxel-world.md
0002-sky-civilization-builder.md
0003-cavern-survival-network.md
```

Each idea can be short:

```md
# Idea: Sky Civilization Builder

Make 10 voxel games about building connected sky islands, airships, bridges, wind currents, and resource towers.

Must include:
- procedural floating islands
- RPC build commands
- inventory/tool selection
- GameHost state
- kit-aware integration diagnostics
```

## Flow

```txt
game-ideas/*.md
→ idea intake
→ normalized theme prompt
→ GameSpec-Harness
→ 10 generated prompts
→ LiveHarness child builds
→ launcher entries
```
