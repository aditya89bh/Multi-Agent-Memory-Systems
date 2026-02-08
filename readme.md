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

