# M10 – Organizational Memory & Culture Layer

This module implements **organizational memory**: persistent norms, patterns, and heuristics
that emerge from repeated multi-agent episodes.

M10 turns raw experience (M5) and feedback signals (M9) into:
- team rules of thumb
- operating principles
- playbooks
- anti-pattern warnings
- default behaviors (culture)

It answers:

> What does this team “learn” over time about how it should work?

---

## Why This Module Exists

After M1–M9, you can build a functioning multi-agent team:
- shared memory
- permissions
- conflict handling
- role routing
- episodic traces
- communication tracking
- partner models
- shared belief fusion
- credit assignment

But the team still lacks **long-term compounding improvement**:

- successful coordination patterns are not preserved
- failures repeat across projects
- “how we work here” is not encoded

M10 creates stable, reusable “organizational knowledge”.

---

## Core Idea

> Culture is compressed experience.

M10 stores **culture artifacts**:
- norms (“always log assumptions before execution”)
- playbooks (“if uncertain, gather evidence from observer first”)
- heuristics (“prefer agent B for debugging tasks”)
- anti-patterns (“avoid planning without world-state check”)
- escalation rules (“if conflicts persist, ask critic to arbitrate”)

These artifacts evolve over time based on episode outcomes and credit signals.

---

## What This Module Provides

### 1. Culture Artifacts
A culture artifact contains:
- statement (the norm / heuristic)
- confidence (how strongly the org believes it)
- evidence links (episodes, outcomes)
- tags (planning, execution, safety, comms)
- last updated timestamp

---

### 2. Pattern Mining (Lightweight)
M10 can derive candidate norms from repeated signals such as:
- frequent failure causes in episodes
- repeated open-loop communication failures (M6)
- trust changes and credit signals (M7/M9)
- repeated conflict types (M3)

This is not heavy ML.
It is interpretable “pattern counting + scoring”.

---

### 3. Culture Query Interface
Agents can ask:
- “what are our norms for planning?”
- “what are common failure modes?”
- “what should I do first in this situation?”
- “what playbook applies to this task?”

---

### 4. Culture-Aware Routing Hook
M10 can feed M4 routing with:
- reminders / checklists
- role-specific norms
- task-stage heuristics

This is how culture becomes behavior.

---

## What This Module Does NOT Do

This module intentionally does **not**:
- enforce hard rules like a compiler
- punish agents
- replace planning logic

Culture is advisory memory:
strong suggestions, not absolute law.

---

## How This Builds on Previous Modules

- Consumes episodes from M5
- Consumes communication patterns from M6
- Consumes partner model trends from M7
- Consumes belief uncertainty from M8
- Consumes credit signals from M9
- Persists norms back into M1 as artifacts and events

---

## Mental Model

Think of M10 as:
- “how we do things here” for agents
- an evolving playbook library
- a memory layer that turns repetition into norms

It converts a multi-agent team into a multi-agent organization.
