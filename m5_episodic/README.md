# M5 – Team Episodic Memory (Coordination Trace)

This module implements **team episodic memory**: a structured record of how a group of agents
coordinated over time to achieve (or fail at) a task.

Unlike raw logs, an episode captures:
- context
- roles
- decisions
- actions
- outcomes
- what worked vs what didn’t

M5 turns multi-agent work into **reusable experience**.

---

## Why This Module Exists

After M1–M4, agents can:
- store shared memory (M1)
- control access (M2)
- handle conflicting beliefs (M3)
- retrieve role-appropriate context (M4)

But teams still lack:
- a clean representation of “what happened”
- a reusable trace for future planning
- a postmortem-friendly artifact

Without episodic memory:
- teams repeat the same failure modes
- learnings stay trapped in unstructured logs
- coordination improvements don’t compound

---

## Core Idea

> A team should remember work the way humans remember projects.

M5 groups events and artifacts into **episodes**:
- an episode is a unit of coordinated work
- it has a start, evolution, and closure
- it can be replayed, summarized, and reused

---

## What This Module Provides

### 1. Episode Structure
An episode contains:
- `episode_id`
- `task_id`
- participants + roles
- timeline of key events
- decisions and rationales
- action sequences
- outcomes and metrics
- unresolved threads

---

### 2. Coordination Trace Builder
M5 can build episodes from M1 events by:
- filtering by task/session tags
- detecting “phase boundaries” (plan/execute/review)
- collecting relevant artifacts

---

### 3. Episode Summaries
Each episode can produce:
- a short summary (for routing / quick recall)
- a structured summary (for reuse)
- a postmortem view (what failed, why)

---

### 4. Reuse Hooks
Episodes can be queried by:
- task similarity (via embeddings in M1)
- participant composition
- outcome quality

This creates a path toward:
- case-based planning
- reusable playbooks
- organizational learning (M10)

---

## What This Module Does NOT Do

This module intentionally does **not**:
- decide truth (M3 does that)
- enforce permissions (M2 does that)
- route memory (M4 does that)
- implement RL credit assignment (M9 does that)

M5 only packages experience into replayable units.

---

## How This Builds on Previous Modules

- Uses M1 event log + artifacts as raw material
- Respects M2 access scope when retrieving artifacts
- Can include M3 conflicts and resolutions in the trace
- Can leverage M4 routing metadata to structure phases

---

## Mental Model

Think of M5 as:
- “project memory” for agent teams
- a reusable postmortem + playbook generator
- a coordination trace, not a chat log

It turns teamwork into **compounding learning**.
