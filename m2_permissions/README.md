# M2 – Memory Ownership & Permissions

This module introduces **ownership and access control** on top of the shared
memory bus implemented in M1.

Without permissions, shared memory quickly becomes unusable in multi-agent
systems due to leakage, overwrites, and ambiguity around responsibility.

M2 ensures that memory remains **safe, interpretable, and socially usable**.

---

## Why This Module Exists

M1 allows all agents to write to shared memory.

In practice, this causes problems:
- private thoughts leak into team memory
- agents overwrite each other’s state
- sensitive information becomes globally visible
- debugging becomes impossible due to unclear intent

M2 introduces **explicit ownership and scope** so shared memory can scale beyond
toy systems.

---

## Core Idea

> Memory without ownership becomes corruption.

M2 treats access control as **first-class memory metadata**, not a prompt rule.

Every artifact is written with:
- an owner
- an access scope
- optional team or organization boundaries

All access decisions are enforced in code.

---

## What This Module Provides

### 1. Memory Scopes

Each artifact is stored with one of the following scopes:

- **PRIVATE** – visible only to the owning agent  
- **TEAM** – visible to members of a specific team  
- **ORG** – visible to members of an organization  
- **PUBLIC** – readable by anyone, restricted writes  

---

### 2. Membership Model

A minimal membership system tracks:
- which organization an agent belongs to
- which teams an agent is part of

This enables permission checks without relying on model behavior.

---

### 3. Enforcement Wrapper

M2 does **not** modify M1 internals.

Instead, it wraps the M1 `Blackboard` with a `SecureBlackboard` that:
- enforces permissions on reads and writes
- attaches access metadata to artifacts
- logs all reads and writes back into M1 as events

This keeps the system composable and auditable.

---

### 4. Audit Trail

Every successful access generates an event in M1:
- `MEMORY_WRITE`
- `MEMORY_READ`

This allows:
- debugging of access violations
- future credit assignment (M9)
- trust calibration (M7)

---

## What This Module Does NOT Do

This module intentionally does **not**:
- resolve conflicting beliefs (M3)
- route memory by role (M4)
- interpret content semantics
- enforce encryption or cryptographic access

It focuses only on **who is allowed to see or modify what**.

---

## Public API (High Level)

- `AccessPolicy.set_membership(...)`
- `SecureBlackboard.put_artifact(...)`
- `SecureBlackboard.read_artifact(...)`

See `permissions.py` docstrings for full API details.

---

## Design Principles

- Permissions are enforced in code, not prompts
- Ownership is explicit and persistent
- No silent failures or implicit access
- M1 remains neutral and reusable
- All access is auditable

---

## How This Builds on M1

- Uses M1 as the shared memory substrate
- Stores access metadata inside artifact payloads
- Logs access events into M1’s event log

M2 is the foundation for all higher-level coordination logic.

---

## Mental Model

Think of this as:
- file permissions for agent memory
- access control for shared cognition
- social boundaries for machine memory

Memory is now **owned**, not just shared.
