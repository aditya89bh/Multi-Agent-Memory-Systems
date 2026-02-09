"""
M3 – Salience & Conflict Resolution

This module handles disagreement in shared memory by treating
conflicting statements as first-class data.

Public API:
- Claim
- Conflict
- ConflictManager
- ClaimValueType
- ResolutionPolicy
- ResolutionResult
"""

from .merge import (
    Claim,
    Conflict,
    ConflictManager,
    ClaimValueType,
    ResolutionPolicy,
    ResolutionResult,
)
