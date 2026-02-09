# M3 – Salience & Conflict Resolution

This module introduces **explicit handling of conflicting memory** in multi-agent systems.

Instead of overwriting or deleting information, M3 treats disagreement as
**first-class data**.

It answers the question:
> What should the system do when agents write incompatible beliefs?

---

## Why This Module Exists

After M1 and M2, agents can:
- write shared memory
- respect ownership and access boundaries

But a new problem emerges:

- agents disagree
- observations conflict
- plans compete
- “truth” becomes ambiguous

Naively overwriting memory destroys information and hides uncertainty.

M3 solves this by **preserving conflict instead of erasing it**.

---

## Core Idea

> Conflict is information, not an error.

M3 treats memory entries as **claims**, not facts.

Each claim carries:
- content
- provenance (who said it)
- confidence
- timestamp

Conflicting claims can coexist until the system has enough evidence to resolve them.

---

## What This Module Provides

### 1. Claim-Based Memory
Instead of a single value, memory stores:
- multiple competing claims
- each with its own provenance and confidence

Example:
- Agent A: “Task will take 2 days” (confidence 0.7)
- Agent B: “Task will take 5 days” (confidence 0.8)

Both are preserved.

---

### 2. Explicit Conflict Detection
M3 detects:
- contradictory values
- incompatible ranges
- mutually exclusive assertions

Conflicts are recorded, not hidden.

---

### 3. Salience Scoring
When multiple claims exist, M3 can rank them using:
- confidence
- recency
- trust in the source agent
- relevance to current context

This is where **priority begins to emerge**.

---

### 4. Policy-Based Resolution
Conflicts can be handled via policies such as:
- trust-weighted selection
- recency-weighted selection
- consensus / majority
- “keep all and escalate”

Resolution is **configurable**, not hardcoded.

---

## What This Module Does NOT Do

This module intentionally does **not**:
- delete minority opinions
- enforce a single global truth
- assume perfect information
- require immediate resolution

Uncertainty is allowed to exist.

---

## How This Builds on Previous Modules

- Uses **M1** for storing claims and conflict records
- Respects **M2** ownership and access rules
- Consumes provenance metadata to reason about trust and reliability

M3 is the first module that reasons about **meaning and disagreement**.

---

## Why This Matters for Multi-Agent Systems

Without conflict handling:
- agents overwrite each other
- systems oscillate between states
- failures are hard to diagnose
- learning is brittle

With M3:
- uncertainty is explicit
- disagreement becomes actionable
- decisions can be justified

---

## Mental Model

Think of M3 as:
- version control for beliefs
- a debate table, not a verdict machine
- a memory system that can say “we’re not sure yet”

Truth becomes something the system **approaches**, not assumes.
