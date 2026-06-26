# LiveHarness Massive Build Loop

The massive build workflow runs a full internal build/revise/validate loop inside one GitHub Actions job and commits once at the end.

## Flow

```txt
prompt
→ product brief membrane
→ master interpretation
→ goal AST
→ 16 bounded swarm workers
→ slot validation
→ reconciled multi-file write-set
→ sandbox apply
→ file-filter validation
→ self-alignment
→ promote sandbox to docs only if gates pass
→ final public validation
→ one commit
→ Pages deploy
```

## Public ownership

`docs/` is owned by `.github/workflows/LiveHarness-Massive-Build.yml`.

Legacy prompt-run and NVIDIA builder workflows are manual-only and must not write public launcher output on push.

## Swarm model

Workers write only into `LiveHarnessV.01/runs/<run-id>/swarm/worker-*`.

Workers never write `docs/` directly. The reconciler produces a write-set, and the harness applies that write-set first to `runs/<run-id>/sandbox/`.

## Validation

The sandbox candidate must pass:

- path filter
- public-output membrane
- file size/count filter
- required file filter
- module graph filter
- DSK boundary filter
- renderer boundary filter
- GameHost filter
- JS syntax filter
- run artifact completeness filter

## Endpoint mode

By default, the workflow uses deterministic fallback worker outputs for reliability.

To allow model-backed workers, set:

```txt
LIVEHARNESS_USE_MODEL_SWARM=true
```

The dispatcher still writes request, raw response, parsed response, status, and self-review artifacts for every worker.
