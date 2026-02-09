# M7 – Partner Models (Theory of Mind Memory)

This module implements **partner models**: memory structures that represent
other agents as learned, evolving entities.

In multi-agent teams, coordination improves dramatically when agents remember:
- who is reliable on what
- who tends to be overconfident vs cautious
- who prefers which style of tasks
- how accurate their estimates are
- how they react under uncertainty

M7 makes those patterns explicit and queryable.

---

## Why This Module Exists

After M1–M6, agents can:
- share memory (M1)
- enforce ownership (M2)
- track conflicting beliefs (M3)
- route memory by role (M4)
- store team episodes (M5)
- track communication commitments (M6)

But teams still fail at a deeper level:

> Agents treat each other as interchangeable.

Real teams work because members learn:
- trust calibration
- delegation strategies
- communication styles
- competence boundaries

Without partner models:
- delegation is random
- trust never updates
- the team repeats the same coordination mistakes

---

## Core Idea

> Every agent should maintain an evolving model of other agents.

M7 represents each partner as a set of estimated attributes:
- reliability (does this agent usually help?)
- calibration (is confidence aligned with correctness?)
- specialization (what tasks are they good at?)
- latency (how fast do they respond?)
- communication style (concise vs verbose, direct vs exploratory)

These models are not “truth”.
They are **learned hypotheses**, updated from experience.

---

## What This Module Provides

### 1. Partner Profiles
A profile is a memory object keyed by `partner_agent_id`.

It stores:
- trust score
- calibration score
- competence tags
- preferred role assignments
- recent interactions

---

### 2. Update Rules From Experience
Partner models update using signals from:
- episode outcomes (M5)
- conflict history (M3)
- commitment completion (M6)
- credit assignment (M9 later)

Example updates:
- repeated incorrect claims → lower trust for that domain
- consistent on-time delivery → higher reliability score
- overconfident wrong answers → calibration penalty

---

### 3. Delegation Hints
Given a task context, M7 can suggest:
- who to ask
- who to trust
- who to double-check
- who to avoid for a given domain

---

### 4. Queryable “Team Topology”
M7 enables questions like:
- “who is best for debugging?”
- “who tends to inflate timelines?”
- “who is the best critic?”
- “who should validate safety risks?”

---

## What This Module Does NOT Do

This module intentionally does **not**:
- assign final blame/credit (M9 does that)
- enforce authority hierarchy
- assume partner models are correct
- decide truth (M3 does that)

It only maintains **useful hypotheses** about partners.

---

## How This Builds on Previous Modules

- Uses provenance from M1 to attribute claims and actions
- Can incorporate conflicts from M3 to calibrate trust
- Can incorporate episodic outcomes from M5 to update competence beliefs
- Can incorporate commitment follow-through from M6 to update reliability

M7 becomes far more powerful once M9 (credit) is added.

---

## Mental Model

Think of M7 as:
- “contact memory” for agents
- trust + calibration + specialization
- a lightweight theory-of-mind layer

It turns a multi-agent system from a crowd into a team.
