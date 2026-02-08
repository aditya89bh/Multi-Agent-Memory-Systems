from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from mam.m1_blackboard.blackboard import Blackboard, Provenance, EventType


class Scope(str, Enum):
    """
    Access scope for artifacts stored in shared memory.

    PRIVATE: only the owner agent can read/write
    TEAM: members of a specified team can read/write
    ORG: members of a specified org can read/write
    PUBLIC: anyone can read; writes are restricted
    """
    PRIVATE = "private"
    TEAM = "team"
    ORG = "org"
    PUBLIC = "public"


class Action(str, Enum):
    """Logical actions enforced by the access policy."""
    READ = "read"
    WRITE = "write"
    REDACT = "redact"


@dataclass(frozen=True)
class Membership:
    """
    Membership record for an agent.

    Fields:
        org_id: Optional organization id.
        team_ids: Teams the agent belongs to.
    """
    org_id: Optional[str] = None
    team_ids: Tuple[str, ...] = tuple()


@dataclass
class AccessPolicy:
    """
    Minimal rule-based access control.

    This is intentionally simple and easy to evolve.
    Later versions can be replaced with RBAC/ABAC, signed tokens, etc.

    Stored state:
        memberships: agent_id -> Membership
        trust: optional trust weights (used later in M3/M7/M9)
    """
    memberships: Dict[str, Membership] = field(default_factory=dict)
    trust: Dict[str, float] = field(default_factory=dict)

    def set_membership(self, agent_id: str, *, org_id: Optional[str], team_ids: List[str]) -> None:
        """Set or update membership for an agent."""
        self.memberships[agent_id] = Membership(org_id=org_id, team_ids=tuple(team_ids))

    def can(
        self,
        actor: Provenance,
        action: Action,
        *,
        scope: Scope,
        owner_agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        org_id: Optional[str] = None,
    ) -> bool:
        """
        Permission check.

        Current rule set:
        - PRIVATE: only owner can read/write/redact
        - TEAM: team members can read/write; redact only by owner
        - ORG: org members can read/write; redact only by owner
        - PUBLIC:
            - READ: anyone
            - WRITE: only if actor has tag 'publisher' OR role == 'admin'
            - REDACT: only role == 'admin'
        """
        m = self.memberships.get(actor.agent_id, Membership())

        if scope == Scope.PRIVATE:
            return owner_agent_id is not None and actor.agent_id == owner_agent_id

        if scope == Scope.TEAM:
            if not team_id:
                return False
            if action in (Action.READ, Action.WRITE):
                return team_id in set(m.team_ids)
            if action == Action.REDACT:
                return owner_agent_id is not None and actor.agent_id == owner_agent_id

        if scope == Scope.ORG:
            if not org_id:
                return False
            if action in (Action.READ, Action.WRITE):
                return (m.org_id is not None) and (m.org_id == org_id)
            if action == Action.REDACT:
                return owner_agent_id is not None and actor.agent_id == owner_agent_id

        if scope == Scope.PUBLIC:
            if action == Action.READ:
                return True
            if action == Action.WRITE:
                tags = set(actor.tags or ())
                return ("publisher" in tags) or (actor.role == "admin")
            if action == Action.REDACT:
                return actor.role == "admin"

        return False


class PermissionError(Exception):
    """Raised when an access policy denies an operation."""
    pass


class SecureBlackboard:
    """
    Permission-enforcing wrapper around the M1 Blackboard.

    Behavior:
    - All writes/reads pass through AccessPolicy
    - Access metadata is stored inside artifact payload under `_access`
    - All reads/writes are logged back into M1 as MEMORY_READ / MEMORY_WRITE events

    This keeps M1 neutral and makes permission behavior auditable and replayable.
    """

    def __init__(self, blackboard: Blackboard, policy: AccessPolicy):
        self.bb = blackboard
        self.policy = policy

    def put_artifact(
        self,
        actor: Provenance,
        *,
        kind: str,
        payload: Dict[str, Any],
        scope: Scope,
        owner_agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        org_id: Optional[str] = None,
        index_if_embedding: bool = True,
    ) -> str:
        """
        Store an artifact with access control.

        Raises:
            PermissionError: if WRITE is denied.
        """
        owner_agent_id = owner_agent_id or actor.agent_id

        if not self.policy.can(
            actor,
            Action.WRITE,
            scope=scope,
            owner_agent_id=owner_agent_id,
            team_id=team_id,
            org_id=org_id,
        ):
            raise PermissionError(f"WRITE denied: scope={scope.value} actor={actor.agent_id}")

        access_meta = {
            "_access": {
                "scope": scope.value,
                "owner_agent_id": owner_agent_id,
                "team_id": team_id,
                "org_id": org_id,
            }
        }

        merged = dict(payload)
        merged.update(access_meta)

        art_id = self.bb.put_artifact(
            actor,
            kind=kind,
            payload=merged,
            index_if_embedding=index_if_embedding,
        )

        # Audit trail
        self.bb.post_event(
            EventType.MEMORY_WRITE,
            actor,
            text=f"artifact stored ({kind}) scope={scope.value}",
            data={"scope": scope.value, "owner_agent_id": owner_agent_id, "team_id": team_id, "org_id": org_id},
            artifact_id=art_id,
        )

        return art_id

    def read_artifact(self, actor: Provenance, artifact_id: str) -> Dict[str, Any]:
        """
        Read an artifact with access control.

        Raises:
            KeyError: if artifact does not exist.
            PermissionError: if READ is denied.
        """
        art = self.bb.get_artifact(artifact_id)
        if not art:
            raise KeyError(f"artifact not found: {artifact_id}")

        access = (art.payload or {}).get("_access", {})
        scope = Scope(access.get("scope", Scope.PUBLIC.value))
        owner_agent_id = access.get("owner_agent_id")
        team_id = access.get("team_id")
        org_id = access.get("org_id")

        if not self.policy.can(
            actor,
            Action.READ,
            scope=scope,
            owner_agent_id=owner_agent_id,
            team_id=team_id,
            org_id=org_id,
        ):
            raise PermissionError(f"READ denied: scope={scope.value} actor={actor.agent_id}")

        # Audit trail
        self.bb.post_event(
            EventType.MEMORY_READ,
            actor,
            text=f"artifact read scope={scope.value}",
            data={"scope": scope.value, "artifact_id": artifact_id},
            artifact_id=artifact_id,
        )

        return art.payload
