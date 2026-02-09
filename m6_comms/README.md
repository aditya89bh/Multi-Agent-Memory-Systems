# M6 – Communication Memory (Dialogue as a First-Class Memory)

This module treats communication as **structured memory**, not just transient messages.

In multi-agent systems, coordination fails when:
- commitments are forgotten
- questions go unanswered
- decisions lose rationale
- conversations loop

M6 stores dialogue in a way that supports:
- tracking open loops
- enforcing follow-ups
- preventing repeated questions
- maintaining shared commitments

---

## Why This Module Exists

After M1–M5, you can store shared memory, enforce permissions, manage conflicts,
route role-specific context, and package experience into episodes.

But teams still suffer from a classic failure mode:

> Communication is not stored in a usable form.

Chat logs are not coordination memory.

They do not explicitly represent:
- who promised what
- what is still pending
- what is blocked by whom
- what question was answered (and by which evidence)

---

## Core Idea

> Dialogue should produce state.

M6 treats communication as a set of **stateful objects**:

- **Message** (utterance)
- **Question** (needs answer)
- **Answer** (resolves a question)
- **Commitment** (promise to do something)
- **Request** (ask another agent to act)
- **Decision** (commitment with rationale)
- **Thread** (groups related dialogue into a track)

---

## What This Module Provides

### 1. Structured Dialogue Store
Stores messages and links them into threads.

Each message is annotated with:
- speaker (agent + role)
- timestamp
- thread id
- intent tags

---

### 2. Open-Loop Tracker
Explicitly tracks:
- unanswered questions
- unfulfilled commitments
- pending requests

This makes coordination failures visible.

---

### 3. Commitment Memory
A commitment has:
- owner (who promised)
- target (what they promised)
- due time (optional)
- status (open / done / dropped)
- evidence of completion

---

### 4. Anti-Looping Recall
When a new question appears, M6 can:
- detect if it was asked before
- retrieve the most relevant prior answer
- avoid repeating conversation cycles

---

## What This Module Does NOT Do

This module intentionally does **not**:
- enforce permissions (M2 does that)
- resolve truth (M3 does that)
- create planning policies (M4/M5 feed into planning)
- assign credit (M9 does that)

M6 only structures communication into memory objects.

---

## How This Builds on Previous Modules

- Stores dialogue objects as M1 artifacts + events
- Can enforce access via M2 SecureBlackboard
- Can route comms by role via M4 (planner vs executor vs critic)
- Can be packaged into episodes by M5

---

## Mental Model

Think of M6 as:
- a “ticketing system” for agent communication
- a shared inbox of open loops
- commitments + questions made explicit

The goal is simple:
**reduce coordination drift** and **stop repeated conversations**.
