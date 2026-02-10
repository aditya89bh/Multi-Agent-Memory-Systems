"""
M9 – Multi-Agent Credit Assignment

This module assigns credit and blame signals to agents based on outcomes
and propagates them into partner models for learning and trust calibration.

Public API:
- ContributionType
- Contribution
- CreditAssigner
"""

from .credit import (
    ContributionType,
    Contribution,
    CreditAssigner,
)
