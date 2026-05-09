# Agent Coordination in Memory-Enabled Systems

This document explores how agents coordinate through structured memory.

Most current multi-agent systems coordinate through:

- Message passing
- Prompt chaining
- Shared task queues
- Tool invocation

These mechanisms are useful.

But by themselves, they often create fragile systems with weak continuity.

This repository proposes a different approach:

Agents coordinate through memory.

## The Core Coordination Problem

As more agents are added, coordination complexity increases rapidly.

Without stable shared state:

- Agents duplicate work
- Responsibilities become unclear
- Failures propagate silently
- System state becomes inconsistent
- Context drifts over time

Coordination is not only communication.

Coordination is continuity.

## Coordination Through Shared Memory

Instead of relying only on transient messages, agents interact through structured memory.

Each agent:

1. Reads system state
2. Performs reasoning
3. Writes updates into memory
4. Updates coordination state
5. Signals task transitions

This creates persistent operational continuity.

## Example Coordination Flow

```text
Research Agent
↓
Collects sources
↓
Writes findings into shared memory
↓
Planner Agent retrieves findings
↓
Builds execution plan
↓
Critic Agent reviews plan
↓
Executor Agent performs action
↓
Recovery Agent handles failures
↓
Memory system stores outcomes
```

Each step updates shared memory.

The system evolves over time instead of resetting every run.

## Core Coordination Components

| Component | Purpose |
|---|---|
| Shared Task State | Tracks active workflows |
| Ownership Tracking | Determines agent responsibility |
| Dependency Tracking | Tracks blocked or waiting states |
| Event Logs | Stores operational history |
| Decision Records | Stores important decisions |
| Failure Tracking | Stores breakdowns and recoveries |
| Temporal State | Tracks freshness and validity |

## Shared Task State

The system should maintain explicit task state.

Example:

```json
{
  "task": "Generate outreach strategy",
  "status": "waiting_for_review",
  "owner": "critic_agent",
  "dependencies": ["research_complete"],
  "updated_at": "2026-05-09"
}
```

This reduces ambiguity across agents.

## Ownership Tracking

Every major task should have a clear owner.

Without ownership:

- Multiple agents may repeat work
- Responsibility becomes unclear
- Recovery becomes difficult

Ownership memory enables:

- Accountability
- Task continuity
- Better debugging
- Recovery coordination

## Dependency Tracking

Complex workflows require dependency management.

Example:

```text
Executor Agent cannot proceed until:
- Planner Agent finalizes strategy
- Critic Agent approves constraints
```

Memory should store these relationships explicitly.

## Decision Memory

Important decisions should persist beyond one run.

Example:

```text
Decision:
Do not use aggressive outreach tone.
Reason:
Previous campaigns showed negative response rates.
```

Without decision memory, systems repeat past mistakes.

## Temporal Coordination

Coordination state changes over time.

Important concepts:

| Concept | Meaning |
|---|---|
| Freshness | Is information still valid? |
| Expiration | Should memory be ignored now? |
| Reinforcement | Frequently reused state becomes stronger |
| Decay | Unused coordination state weakens |
| Conflict | Multiple agents disagree about system state |

A useful coordination system must manage these dynamics continuously.

## Conflict Resolution

Agents may disagree.

Examples:

- Planner Agent recommends speed
- Critic Agent recommends safety
- Retrieval Agent surfaces contradictory memories

The system needs mechanisms for:

- Arbitration
- Priority rules
- Trust scoring
- Voting systems
- Human escalation

Without conflict handling, memory becomes unstable.

## Shared vs Local Coordination

Not all coordination should be global.

### Shared Coordination

Visible to all agents.

Examples:

- Global task state
- Project goals
- Final decisions

### Local Coordination

Restricted to small groups of agents.

Examples:

- Experimental workflows
- Temporary hypotheses
- Internal planning traces

This separation helps reduce coordination noise.

## Failure Recovery Coordination

Recovery systems should also use memory.

Example:

```text
Executor failed due to missing dependency.
Recovery Agent retries after dependency validation.
```

The system should remember:

- What failed
- Why it failed
- Which recovery strategy succeeded

Otherwise the system loops endlessly.

## Coordination Patterns

### Sequential Coordination

Agents execute in ordered stages.

Example:

```text
Research → Planning → Review → Execution
```

### Parallel Coordination

Multiple agents work simultaneously.

Example:

```text
Three research agents gather different sources simultaneously.
```

### Hierarchical Coordination

Coordinator agents manage lower-level workers.

Example:

```text
Manager Agent delegates work to specialist agents.
```

### Event-Driven Coordination

Agents react to memory updates.

Example:

```text
Critic Agent activates when Planner writes new proposal.
```

## Long-Term Vision

The long-term goal is not simply to build larger agent pipelines.

The goal is to build systems that:

- Maintain continuity
- Learn collectively
- Coordinate reliably
- Recover from failure
- Improve over time

Memory is the operational substrate that enables this.
