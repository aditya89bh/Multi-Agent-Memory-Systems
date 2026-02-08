# M1 – Shared Memory Bus (Blackboard)

This module implements the **foundational shared memory layer** for multi-agent systems.

It provides a common surface where multiple agents can:
- write observations, decisions, and outcomes
- store artifacts with provenance
- read shared context without direct message passing

All higher-level memory systems in this repository build on top of this layer.

---

## Why This Project Exists

Most multi-agent systems coordinate through:
- messages
- prompts
- implicit context in the model

This breaks down quickly because:
- context is overwritten
- agents repeat work
- there is no shared ground truth
- past decisions disappear

The Blackboard solves this by introducing a **persistent, shared memory substrate** that exists independently of any single agent.

---

## Core Idea

> Memory should be **public, structured, and traceable**.

The Blackboard treats memory as:
- events, not chat history
- artifacts, not strings
- shared state, not private context

Every write includes **provenance**:
- who wrote it
- when
- in what role
- with what confidence

---

## What This Module Implements

### 1. Shared Event Log
An append-only log of:
- observations
- messages
- decisions
- actions
- outcomes

This allows agents to reconstruct what happened over time.

---

### 2. Artifact Store
A shared store for structured memory objects such as:
- text notes
- JSON state
- embeddings
- references to external files

Artifacts are immutable and addressable.

---

### 3. Provenance Tracking
Every event and artifact includes metadata:
- agent identity
- role
- session
- timestamp
- confidence
- tags

This enables trust, debugging, and later conflict resolution.

---

### 4. Optional Vector Index
Embeddings can be indexed for:
- similarity search
- semantic recall
- memory reuse across agents

The vector layer is deliberately lightweight and model-agnostic.

---

## What This Module Does NOT Do

This module does **not**:
- enforce permissions (handled in M2)
- resolve conflicts (handled in M3)
- route memory by role (handled in M4)
- interpret meaning or intent

It is intentionally minimal and neutral.

---

## Design Principles

- Append-only, never overwrite
- No hidden state
- No agent-specific assumptions
- Debuggable via logs
- Serializable and replayable

---

## How Other Modules Build on This

- **M2** adds ownership and access control
- **M3** adds belief conflict tracking
- **M4** adds role-based routing
- **M5** builds episodic memory on top of events
- **M6+** treat this as the shared substrate for collective intelligence

---

## Status

This module is stable enough to be used on its own as:
- a shared scratchpad for agents
- a coordination log
- a debugging surface for multi-agent runs

All future modules assume the presence of this Blackboard.

---

## Mental Model

Think of this as:
- a blackboard in a research lab
- a shared notebook for agents
- a memory bus, not a brain

It does not think.  
It remembers.
