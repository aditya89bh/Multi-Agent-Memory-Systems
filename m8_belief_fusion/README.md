# M8 – Shared World State Estimation (Belief Fusion)

This module maintains a **shared probabilistic world state** by fusing observations
from multiple agents.

In multi-agent systems, different agents often perceive:
- different slices of reality
- noisy or partial signals
- contradictory measurements

M8 turns these scattered observations into a **belief store**:
- a set of hypotheses about the world
- each with confidence and uncertainty
- updated over time as evidence arrives

---

## Why This Module Exists

After M1–M7, agents can coordinate memory and teamwork, but they still lack
a unified answer to:

> What does the team currently believe about the world?

Without a shared world state:
- planning becomes inconsistent
- agents act on mismatched assumptions
- conflicts become frequent and unproductive
- coordination drifts

M8 creates a consistent, queryable layer of “current belief”.

---

## Core Idea

> The shared world state is a belief distribution, not a single fact table.

M8 represents world state as **belief items**:
- a key (e.g., "object_pose:box_3", "door_open", "ETA")
- a value (number/bool/text/json)
- uncertainty and confidence
- evidence history (who observed what, when)

Beliefs can be:
- merged (fusion)
- decayed (stale beliefs weaken)
- disputed (multiple hypotheses can coexist)

---

## What This Module Provides

### 1. Belief Store
A typed store of belief items:
- mean/value
- confidence
- uncertainty (variance or interval)
- last updated time
- evidence trace

---

### 2. Belief Fusion Rules
Combines observations from different agents using simple, interpretable rules:
- confidence-weighted averaging (numbers)
- majority voting with confidence (bool/text)
- trust-weighted fusion (optionally from M7)
- stale observation decay

---

### 3. Multi-Hypothesis Support
For ambiguous state, M8 can store:
- multiple competing hypotheses
- each with a probability mass

This avoids forcing premature “truth”.

---

### 4. Query Interface for Planning
Agents can ask:
- “what do we currently believe?”
- “how certain are we?”
- “what evidence supports this?”
- “who disagrees?”

This becomes critical input for:
- hierarchical planning (M4/M5)
- risk-aware action selection (E3/E7 style)
- credit assignment later (M9)

---

## What This Module Does NOT Do

This module intentionally does **not**:
- enforce permissions (M2 does that)
- resolve semantic conflicts (M3 does that)
- plan actions (M4/M5 do that)
- assign credit (M9 does that)

M8 focuses only on **state estimation**.

---

## How This Builds on Previous Modules

- Uses M1 to store belief updates as events/artifacts
- Can use M7 partner trust scores to weight evidence
- Works well with M3 conflict tracking when beliefs disagree
- Feeds planners via M4 routing and episodes via M5

---

## Mental Model

Think of M8 as:
- a shared Kalman-filter-like layer (but simpler and modular)
- a “team belief database”
- a living world model state for multi-agent cognition

It answers: **what does the team believe right now, and why?**
