# Nexus Turn Agent Workflow

The workflow is intentionally small: the loop is the agent.

Each turn reads:

1. `.agent/goal.md`
2. `.agent/workflow.md`
3. `.agent/state.json`
4. recent `.agent/runs/` artifacts when present

Then it asks the model for exactly one tool decision.

## Allowed tool decisions

### THINK

Use when more planning or decomposition is needed before writing project files.

Required fields:

```txt
<decision>THINK</decision>
<summary>...</summary>
<next_state>{...}</next_state>
```

### WRITE_FILE

Use when one complete file should be created or replaced.

Required fields:

```txt
<decision>WRITE_FILE</decision>
<summary>...</summary>
<path>docs/example.html</path>
<content>
...
</content>
<next_state>{...}</next_state>
```

### APPEND_FILE

Use when a bounded note or artifact should be appended to an existing file.

Required fields:

```txt
<decision>APPEND_FILE</decision>
<summary>...</summary>
<path>.agent/notes.md</path>
<content>
...
</content>
<next_state>{...}</next_state>
```

### STOP

Use when the current run has reached a useful stopping point.

Required fields:

```txt
<decision>STOP</decision>
<summary>...</summary>
<next_state>{...}</next_state>
```

## Write boundaries

The loop may write only inside these prefixes unless the YAML harness is deliberately changed by a human:

- `.agent/`
- `docs/`
- `src/`
- `generated/`

It should not edit `.github/workflows/` from inside the turn loop.

## Building a larger game from a small loop

The turn agent should not try to create a whole complex game in one response.

It should build by layers:

1. document the current intent
2. add or refine one small runtime surface
3. add one reusable game system
4. add one playable scene or interaction
5. update launcher or manifest artifacts
6. stop when the run has produced a coherent checkpoint

This lets a small YAML harness grow a multilayered game repo over many bounded runs.
