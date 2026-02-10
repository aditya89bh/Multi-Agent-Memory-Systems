"""
M8 – Shared World State Estimation (Belief Fusion)

This module maintains a shared belief state by fusing observations
from multiple agents, optionally weighted by partner trust.

Public API:
- Evidence
- Belief
- BeliefStore
"""

from .belief_store import (
    Evidence,
    Belief,
    BeliefStore,
)
