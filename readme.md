# Multi-Agent Memory Systems

A modular research and engineering project exploring **memory as the organizing primitive for multi-agent intelligence**.

This repository builds a **shared memory stack** that allows multiple agents to:
- coordinate over time
- resolve conflicting beliefs
- learn from collective experience
- develop stable roles, norms, and culture

Unlike single-agent memory (chat history, vector recall), this project treats memory as a **social system**.

---

## Why This Project Exists

Most multi-agent systems today:
- communicate via messages
- coordinate via prompts
- fail silently due to misalignment, repetition, or contradiction

What’s missing is **memory that belongs to the group**, not just individuals.

This repo explores questions like:
- How do agents share memory without chaos?
- Who owns a memory?
- What happens when agents disagree?
- How does a team learn, not just individuals?
- Can agents develop norms, trust, and institutional knowledge?

The answer is not a single model.
It is a **memory architecture**.

---

## Core Idea

> **All coordination failures are memory failures.**

This project implements memory as:
- events, not just text
- artifacts with provenance
- beliefs with confidence
- episodes with outcomes
- norms with enforcement

Everything is grounded in **time, ownership, and accountability**.

---

## Architecture Overview

The system is built as **10 composable layers**, each introducing a new capability.

Each layer is:
- independently usable
- incrementally more powerful
- grounded in real coordination problems

Lower layers are engineering-focused.  
Upper layers move into research territory.

---

## Project Structure

```
multi_agent_memory/
├── src/
│ └── mam/
│ ├── m1_blackboard/
│ ├── m2_permissions/
│ ├── m3_conflicts/
│ ├── m4_routing/
│ ├── m5_episodic/
│ ├── m6_comms/
│ ├── m7_partner_models/
│ ├── m8_belief_fusion/
│ ├── m9_credit/
│ └── m10_culture/

```

Each `Mx` folder corresponds to a sub-project described below.

---

## Sub-Projects

### M1 – Shared Memory Bus (Blackboard)
**Problem:** Agents need a shared place to think without stepping on each other.

**What it does:**
- Append-only event log
- Shared artifact store
- Optional vector similarity search
- Provenance attached to every write

**Key idea:**  
Memory is not chat history. It is a **public surface** with traceability.

---

### M2 – Memory Ownership and Permissions
**Problem:** Not all memory should be globally writable or readable.

**What it does:**
- Private vs team vs organizational memory
- Read/write permissions
- Publish vs whisper semantics
- TTLs and redaction rules

**Key idea:**  
Memory without ownership leads to corruption.

---

### M3 – Multi-Agent Salience and Conflict Resolution
**Problem:** Agents disagree. Naively overwriting memory destroys information.

**What it does:**
- Stores competing beliefs
- Tracks contradictions explicitly
- Resolves via policy (trust, confidence, recency)
- Preserves minority opinions

**Key idea:**  
Conflict is data, not an error.

---

### M4 – Role-Based Memory Routing
**Problem:** Different agents need different memories.

**What it does:**
- Role-aware memory indices
- Planner vs executor vs critic views
- Task-conditioned retrieval
- Write routing based on responsibility

**Key idea:**  
Memory access is a design decision.

---

### M5 – Team Episodic Memory (Coordination Trace)
**Problem:** Teams repeat the same mistakes.

**What it does:**
- Stores shared episodes: context → decision → action → outcome
- Enables automatic postmortems
- Allows similarity search over past team experiences

**Key idea:**  
Teams should remember *what happened*, not just *what was said*.

---

### M6 – Communication Memory (Dialogue as Memory)
**Problem:** Agents repeat questions, forget commitments, and drop threads.

**What it does:**
- Tracks promises, questions, answers, and open loops
- Prevents repeated communication
- Compresses long conversations into actionable state

**Key idea:**  
Communication is memory with social consequences.

---

## Advanced / Research Tier

These layers move beyond coordination into **collective intelligence**.

---

### M7 – Partner Models (Theory of Mind Memory)
**Problem:** Agents treat all teammates as identical.

**What it does:**
- Learns reliability, strengths, and biases of other agents
- Maintains trust and calibration scores
- Improves delegation and planning

**Key idea:**  
Effective teams model each other.

---

### M8 – Shared World State Estimation (Belief Fusion)
**Problem:** Agents observe different parts of the world.

**What it does:**
- Maintains probabilistic beliefs
- Fuses observations with uncertainty
- Handles stale or conflicting information

**Key idea:**  
Truth is a distribution, not a fact.

---

### M9 – Multi-Agent Credit Assignment
**Problem:** Teams don’t know who helped or hurt outcomes.

**What it does:**
- Attributes success and failure across agents
- Tracks contribution over episodes
- Enables role and policy adaptation

**Key idea:**  
Learning requires accountability without blame.

---

### M10 – Organizational Memory and Culture Layer
**Problem:** Systems drift without norms.

**What it does:**
- Stores norms, rules, and playbooks
- Enforces cultural constraints
- Allows norms to evolve via evidence

**Key idea:**  
Culture is memory that shapes behavior.

---

## What This Is (and Is Not)

**This is:**
- a systems-level exploration of memory
- model-agnostic
- compatible with LLMs, planners, simulators, and embodied agents

**This is not:**
- a chatbot framework
- a prompt library
- a single monolithic agent

---

## Intended Use Cases

- Multi-agent research
- Agent orchestration platforms
- Simulation and world-modeling
- Organizational AI systems
- Long-running autonomous teams

---

## Status

This repository is:
- under active development
- built incrementally in public
- intended as both research artifact and engineering foundation

Each sub-project can be used independently or composed into a full stack.

---

## Philosophy

> Memory is not storage.  
> Memory is **structure, power, and responsibility over time**.

This project treats memory as the missing substrate for scalable multi-agent intelligence.

