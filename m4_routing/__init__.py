"""
M4 – Role-Based Memory Routing

This module routes memory reads and writes based on agent role
and task context.

Public API:
- Role
- Channel
- TaskContext
- RoleView
- MemoryRouter
"""

from .router import (
    Role,
    Channel,
    TaskContext,
    RoleView,
    MemoryRouter,
)
