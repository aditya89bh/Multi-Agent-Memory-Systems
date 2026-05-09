# Simple Multi-Agent Memory Demo

This example demonstrates a minimal memory-enabled multi-agent workflow.

The goal is not production capability.

The goal is to show how agents coordinate through shared memory.

## Demo Flow

```text
Research Agent
↓
Planner Agent
↓
Critic Agent
↓
Shared memory updated
```

The system stores:

- Episodic memory
- Coordination state

## Files

| File | Purpose |
|---|---|
| memory_store.py | Shared memory layer |
| agents.py | Agent definitions |
| run_demo.py | Main execution loop |
| sample_memory.json | Persistent memory state |

## Run The Demo

```bash
python run_demo.py
```

## Example Output

```text
=== Multi-Agent Memory Demo ===

[Research Agent]
Users prefer concise technical summaries

[Planner Agent]
Generate concise outreach strategy

[Critic Agent]
Plan approved
```

## What This Demonstrates

This demo shows:

- Shared memory writes
- Coordination updates
- Persistent memory state
- Sequential multi-agent workflows

## Future Improvements

Planned upgrades:

- Retrieval-based memory reuse
- Salience scoring
- Temporal decay
- Conflict resolution
- Shared vs private memory
- Memory compression
- Event-driven coordination
- Multi-agent arbitration
