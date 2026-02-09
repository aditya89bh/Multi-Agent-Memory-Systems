# M4 – Role-Based Memory Routing

This module introduces **role-aware memory views and routing** for multi-agent systems.

After M1–M3, the system can:
- store shared memory (M1)
- enforce who can access it (M2)
- preserve and rank conflicting beliefs (M3)

But a new problem appears:

> Even if memory is correct, the wrong agent can retrieve the wrong thing.

M4 solves this by routing memory reads/writes based on **role** and **task context**.

---

## Why This Module Exists

In real multi-agent teams, different roles should not see the same memory slice:

- Planners need goals, constraints, assumptions, tradeoffs
- Executors need step-by-step actionable instructions
- Critics need risks, inconsistencies, missing evidence
- Observers need raw signals and environment state

If everyone retrieves from the same pool, systems suffer from:
- irrelevant recall
- brittle decisions
- duplicated work
- confusion between "plan" vs "execution" vs "critique"

---

## Core Idea

> Memory access is a design decision.

M4 treats retrieval as a **router**, not a global search.

It introduces:
- role-specific memory channels
- task-conditioned retrieval filters
- write routing rules (who writes what, where)

---

## What This Module Provides

### 1. Role-Based Views
Each role gets a configurable view over memory:
- which event types matter
- which tags to include/exclude
- which scopes are relevant
- whether to prefer resolved claims (M3) or raw claims

---

### 2. Read Routing
Given:
- agent role
- task context (task_id, goal, stage)

M4 decides:
- which memory sources to query
- what to retrieve
- how to rank results

---

### 3. Write Routing
When an agent writes memory, M4 can attach routing metadata such as:
- intended audience role(s)
- memory channel (plan/execution/risk/etc.)
- lifecycle (draft vs final)

This reduces later confusion and improves retrieval precision.

---

### 4. Composability With M2 + M3
M4 does not replace:
- permissions (M2)
- conflict handling (M3)

It composes with both:
- only retrieve what the agent is allowed to see
- optionally prefer resolved outputs when conflicts exist

---

## What This Module Does NOT Do

This module intentionally does **not**:
- implement a full planner
- enforce role assignment logic
- decide truth (M3 does that)
- store long-term team episodes (M5 does that)

It only routes memory.

---

## Mental Model

Think of M4 as:
- an inbox system for memory
- role-based filters in an organization
- "who should see what" for agent cognition

It ensures agents retrieve the **right memory at the right time**.
