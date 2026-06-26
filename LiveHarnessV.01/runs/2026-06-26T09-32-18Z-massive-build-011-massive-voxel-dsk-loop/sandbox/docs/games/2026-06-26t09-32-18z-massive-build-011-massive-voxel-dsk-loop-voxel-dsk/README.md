# Massive Voxel DSK Loop Lab

Build a multi-file Three.js voxel world experiment that validates NexusRealtime domain-service boundaries through sandbox-first build loops.

This candidate is generated through the massive sandbox-first LiveHarness build loop. The public game demonstrates Runtime/Kits/Sequences boundaries using a voxel experiment:

- Runtime modules own command queues, events, and clock.
- Domain modules own movement, inventory, build/break, and objective meaning.
- Renderer modules present block state with Three.js.
- Host modules map input into domain requests and expose `window.GameHost.getState()`.
