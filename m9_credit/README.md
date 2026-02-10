# M9 – Multi-Agent Credit Assignment (Who Helped, Who Hurt)

This module assigns **credit and blame signals** across agents based on outcomes.

In multi-agent systems, outcomes often emerge from:
- multiple decisions
- multiple actions
- multiple communications
- partial contributions

M9 builds a structured layer that answers:

> Who contributed positively or negatively to this outcome, and why?

This enables:
- learning from success/failure
- trust calibration (M7)
- better routing and delegation (M4)
- organizational improvement (M10)

---

## Why This Module Exists

After M1–M8, you can:
- store shared memory
- enforce permissions
- handle conflicting beliefs
- route memory by role
- store episodes
- track communication commitments
- maintain partner models
- maintain a fused shared world state

But the team still lacks a critical mechanism:

> Feedback loops per agent.

Without credit assignment:
- the system cannot learn who is useful for what
- trust never updates in a grounded way
- repeated failure patterns have no owner
- delegation stays random

---

## Core Idea

> Outcomes should propagate back as structured signals.

M9 defines a standardized credit signal:

- agent_id
- contribution_type (helped/hurt)
- strength (0..1)
- justification / evidence
- linked episode/outcome ids

Credit is not moral judgment.
It is **learning metadata**.

---

## What This Module Provides

### 1. Contribution Records
A contribution record links:
- an agent
- an action/decision/claim
- an outcome
- an estimated effect sign (+/-)

---

### 2. Credit Policies
Different projects need different rules.

M9 supports policies such as:
- recency-weighted attribution
- role-weighted attribution (planner vs executor)
- evidence-based (commitment completion, conflict resolution quality)
- episode-based (M5 trace attribution)

---

### 3. Feedback Integration Hooks
M9 produces standardized output that can update:
- partner trust and calibration (M7)
- conflict weighting (M3)
- belief fusion weighting (M8)

---

### 4. Auditability
All credit assignments are stored as:
- artifacts (structured records)
- events (human-readable logs)

So you can debug:
- why a partner’s trust dropped
- why an agent stopped being asked
- what pattern caused repeated failure

---

## What This Module Does NOT Do

This module intentionally does **not**:
- enforce punishment
- delete agents
- create hierarchy or authority
- assume perfect causal inference

Credit assignment is always an approximation.
The goal is useful feedback, not perfect truth.

---

## How This Builds on Previous Modules

- Uses M5 episodes as the main attribution substrate
- Uses M6 commitments as strong evidence signals
- Can use M3 conflicts to penalize wrong confident claims
- Updates M7 partner models as downstream effect
- Improves M8 belief fusion by learning trust weights over time

---

## Mental Model

Think of M9 as:
- “learning signals for teams”
- postmortems that update trust automatically
- the difference between logging and improving

It helps the system answer:
**who should we rely on next time, and why?**
