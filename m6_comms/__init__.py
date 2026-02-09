"""
M6 – Communication Memory

This module treats dialogue, questions, answers, and commitments
as first-class memory objects in multi-agent systems.

Public API:
- MessageIntent
- CommitmentStatus
- Message
- Question
- Answer
- Commitment
- CommunicationMemory
"""

from .comms import (
    MessageIntent,
    CommitmentStatus,
    Message,
    Question,
    Answer,
    Commitment,
    CommunicationMemory,
)
