from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from mam.m1_blackboard.blackboard import Blackboard, EventType, MemoryEvent, Provenance
from mam.m2_permissions.permissions import SecureBlackboard, PermissionError
from mam.m3_conflicts.merge import (
    Claim,
    ConflictManager,
    ClaimValueType,
    ResolutionPolicy,
    ResolutionResult,
)


class Role(str, Enum):
    """
    Canonical agent roles for routing.

    You can extend this, but keep it stable because it becomes part of memory metadata.
    """
    PLANNER = "planner"
    EXECUTOR = "executor"
    CRITIC = "critic"
    OBSERVER = "observer"
    GENERAL = "general"


class Channel(str, Enum):
    """
    High-level memory channels.

    A channel is not a permission scope.
    It's a routing label: who should see what type of memory.
    """
    PLAN = "plan"
    EXECUTION = "execution"
    RISK = "risk"
    OBSERVATION = "observation"
    DECISION = "decision"
    OUTCOME = "outcome"
    NOTE = "note"
    CLAIM = "claim"


@dataclass(frozen=True)
class TaskContext:
    """
    Context used for routing decisions.

    Keep this small and serializable.
    """
    task_id: str = "default"
    goal: str = ""
    stage: str = "default"  # e.g. "draft", "execute", "review"
    tags: Tuple[str, ...] = tuple()


@dataclass
class RoleView:
    """
    Defines what a role should retrieve from shared memory.

    Fields:
        include_event_types: Which M1 event types matter for this role.
        include_channels: Which routing channels to include.
        require_tags: Tags that must exist in provenance.tags for events to be eligible.
        exclude_tags: Tags to exclude.
        prefer_resolved_claims: If True, use M3 resolution outputs when available.
        max_items: Default cap for retrieved items.
    """
    include_event_types: List[EventType] = field(default_factory=list)
    include_channels: List[Channel] = field(default_factory=list)
    require_tags: List[str] = field(default_factory=list)
    exclude_tags: List[str] = field(default_factory=list)
    prefer_resolved_claims: bool = True
    max_items: int = 25


def default_role_views() -> Dict[Role, RoleView]:
    """
    Default routing configuration.

    You can change this freely; it's a starting point.
    """
    return {
        Role.PLANNER: RoleView(
            include_event_types=[EventType.OBSERVATION, EventType.DECISION, EventType.NOTE, EventType.OUTCOME],
            include_channels=[Channel.PLAN, Channel.DECISION, Channel.OUTCOME, Channel.NOTE, Channel.CLAIM],
            require_tags=[],
            exclude_tags=["private_only"],
            prefer_resolved_claims=True,
            max_items=30,
        ),
        Role.EXECUTOR: RoleView(
            include_event_types=[EventType.ACTION, EventType.DECISION, EventType.NOTE, EventType.OUTCOME],
            include_channels=[Channel.EXECUTION, Channel.DECISION, Channel.OUTCOME, Channel.NOTE],
            require_tags=[],
            exclude_tags=["private_only"],
            prefer_resolved_claims=False,
            max_items=25,
        ),
        Role.CRITIC: RoleView(
            include_event_types=[EventType.OBSERVATION, EventType.DECISION, EventType.NOTE, EventType.OUTCOME],
            include_channels=[Channel.RISK, Channel.DECISION, Channel.OUTCOME, Channel.NOTE, Channel.CLAIM],
            require_tags=[],
            exclude_tags=[],
            prefer_resolved_claims=False,  # critics often want raw claims
            max_items=35,
        ),
        Role.OBSERVER: RoleView(
            include_event_types=[EventType.OBSERVATION, EventType.MESSAGE, EventType.NOTE],
            include_channels=[Channel.OBSERVATION, Channel.NOTE],
            require_tags=[],
            exclude_tags=[],
            prefer_resolved_claims=False,
            max_items=25,
        ),
        Role.GENERAL: RoleView(
            include_event_types=[EventType.OBSERVATION, EventType.MESSAGE, EventType.DECISION, EventType.ACTION, EventType.OUTCOME, EventType.NOTE],
            include_channels=[Channel.PLAN, Channel.EXECUTION, Channel.RISK, Channel.OBSERVATION, Channel.DECISION, Channel.OUTCOME, Channel.NOTE, Channel.CLAIM],
            require_tags=[],
            exclude_tags=[],
            prefer_resolved_claims=True,
            max_items=40,
        ),
    }


@dataclass(frozen=True)
class RoutedItem:
    """
    A single memory item returned by the router.

    Fields:
        kind: "event" | "artifact" | "resolution"
        summary: text for display
        data: structured payload
        provenance: provenance of the source event/claim
    """
    kind: str
    summary: str
    data: Dict[str, Any]
    provenance: Provenance


class MemoryRouter:
    """
    Role-based retrieval router that composes M1 + M2 + M3.

    - Reads events from M1 (always)
    - Reads artifacts through M2 SecureBlackboard when provided (optional)
    - Optionally prefers resolved claims from M3 for planner/general views
    """

    def __init__(
        self,
        *,
        bb: Blackboard,
        secure_bb: Optional[SecureBlackboard] = None,
        conflict_mgr: Optional[ConflictManager] = None,
        views: Optional[Dict[Role, RoleView]] = None,
    ):
        self.bb = bb
        self.secure_bb = secure_bb
        self.conflict_mgr = conflict_mgr
        self.views = views or default_role_views()

    # -------------------------
    # Write helpers
    # -------------------------

    def post_routed_event(
        self,
        event_type: EventType,
        provenance: Provenance,
        *,
        text: str = "",
        data: Optional[Dict[str, Any]] = None,
        channel: Channel = Channel.NOTE,
        audience_roles: Optional[List[Role]] = None,
    ) -> str:
        """
        Post an M1 event with routing metadata.

        Routing metadata lives inside data under `_route`.
        """
        payload = dict(data or {})
        payload["_route"] = {
            "channel": channel.value,
            "audience_roles": [r.value for r in (audience_roles or [])],
        }
        return self.bb.post_event(event_type, provenance, text=text, data=payload)

    def add_claim(
        self,
        key: str,
        value: Any,
        value_type: ClaimValueType,
        confidence: float,
        provenance: Provenance,
        *,
        context: Optional[Dict[str, Any]] = None,
        channel: Channel = Channel.CLAIM,
        audience_roles: Optional[List[Role]] = None,
    ) -> Claim:
        """
        Add a claim through M3 ConflictManager and also log a routed event for discoverability.
        """
        if not self.conflict_mgr:
            raise RuntimeError("ConflictManager is required to add_claim(). Provide conflict_mgr=...")

        claim = self.conflict_mgr.add_claim(
            key=key,
            value=value,
            value_type=value_type,
            confidence=confidence,
            provenance=provenance,
            context=context or {},
        )

        # Log a routed note event so retrieval can surface "claim created" in context
        self.post_routed_event(
            EventType.NOTE,
            provenance,
            text=f"claim recorded: {key}",
            data={"key": key, "claim_id": claim.claim_id},
            channel=channel,
            audience_roles=audience_roles,
        )
        return claim

    # -------------------------
    # Read routing
    # -------------------------

    def retrieve(
        self,
        *,
        actor: Provenance,
        role: Role,
        context: Optional[TaskContext] = None,
        limit: Optional[int] = None,
        include_claim_resolutions: Optional[bool] = None,
        resolution_policy: ResolutionPolicy = ResolutionPolicy.BEST_SALIENCE,
    ) -> List[RoutedItem]:
        """
        Retrieve a role-appropriate memory bundle.

        This is the main entrypoint for M4.

        Args:
            actor: requesting agent provenance (used for permissions if secure_bb is set)
            role: requesting agent role
            context: task context (optional)
            limit: override for max items
            include_claim_resolutions: override view preference for resolved claims
            resolution_policy: how M3 resolves competing claims when used

        Returns:
            List of RoutedItem suitable to feed into an agent prompt or planner.
        """
        context = context or TaskContext()
        view = self.views.get(role, self.views[Role.GENERAL])
        max_items = int(limit or view.max_items)

        use_resolutions = view.prefer_resolved_claims if include_claim_resolutions is None else include_claim_resolutions

        # 1) Pull events from M1
        events = self.bb.query_events(limit=max_items * 4)  # pull extra, then filter down

        eligible: List[MemoryEvent] = []
        for ev in events:
            # Filter event types
            if view.include_event_types and ev.event_type not in view.include_event_types:
                continue

            # Tag filters (from provenance)
            ev_tags = set(ev.provenance.tags or ())
            if view.require_tags and not set(view.require_tags).issubset(ev_tags):
                continue
            if view.exclude_tags and set(view.exclude_tags).intersection(ev_tags):
                continue

            # Channel filters (from data._route.channel)
            route = (ev.data or {}).get("_route", {})
            ch = route.get("channel")
            if view.include_channels:
                if ch is None:
                    continue
                if ch not in {c.value for c in view.include_channels}:
                    continue

            # Audience role filters (optional)
            audience = route.get("audience_roles") or []
            if audience and role.value not in set(audience):
                continue

            eligible.append(ev)

        # Keep most recent first, then cut down
        eligible = eligible[-max_items:]

        out: List[RoutedItem] = []

        # 2) Convert events into RoutedItems
        for ev in eligible:
            out.append(
                RoutedItem(
                    kind="event",
                    summary=f"{ev.event_type.value}: {ev.text}".strip(),
                    data={"event": {"id": ev.event_id, "type": ev.event_type.value, "text": ev.text, "data": ev.data}},
                    provenance=ev.provenance,
                )
            )

        # 3) Optionally add resolved claims (M3)
        if use_resolutions and self.conflict_mgr:
            # Gather claim artifacts from event log
            claim_keys = self._infer_claim_keys_from_events(eligible)
            for key in claim_keys:
                # Pull claims by scanning artifacts via events: we stored claims as artifacts with payload["claim"]
                claims = self._load_claims_for_key(key)
                if not claims:
                    continue

                res = self.conflict_mgr.resolve(
                    key=key,
                    claims=claims,
                    policy=resolution_policy,
                )

                if res.chosen:
                    out.append(
                        RoutedItem(
                            kind="resolution",
                            summary=f"resolved claim {key} -> {res.chosen.value}",
                            data={
                                "resolution": {
                                    "key": key,
                                    "policy": res.policy.value,
                                    "chosen": {
                                        "claim_id": res.chosen.claim_id,
                                        "value": res.chosen.value,
                                        "confidence": res.chosen.confidence,
                                        "agent_id": res.chosen.provenance.agent_id,
                                    },
                                    "conflicts": [c.reason for c in res.conflicts],
                                }
                            },
                            provenance=res.chosen.provenance,
                        )
                    )

        # 4) If SecureBlackboard is available, expand artifact references when readable
        if self.secure_bb:
            out = self._expand_readable_artifacts(actor, out)

        # Final: trim
        return out[-max_items:]

    # -------------------------
    # Internals
    # -------------------------

    def _infer_claim_keys_from_events(self, events: List[MemoryEvent]) -> List[str]:
        keys = []
        for ev in events:
            d = ev.data or {}
            if "key" in d and isinstance(d["key"], str):
                keys.append(d["key"])
            # claim events may also include {"claim_id": "...", "key": "..."}
        # uniq preserve order
        seen = set()
        out = []
        for k in keys:
            if k not in seen:
                out.append(k)
                seen.add(k)
        return out

    def _load_claims_for_key(self, key: str) -> List[Claim]:
        # Claims are stored as artifacts with payload {"claim": <asdict(claim)>}
        # We don't have an index yet, so we scan recent artifacts by reading events
        claims: List[Claim] = []

        # Scan recent events and look for artifacts that include claim
        events = self.bb.query_events(limit=200)
        for ev in events:
            if not ev.artifact_id:
                continue
            art = self.bb.get_artifact(ev.artifact_id)
            if not art:
                continue
            payload = art.payload or {}
            if "claim" not in payload:
                continue
            c = payload["claim"]
            if not isinstance(c, dict):
                continue
            if c.get("key") != key:
                continue

            try:
                claims.append(
                    Claim(
                        claim_id=c["claim_id"],
                        key=c["key"],
                        value=c["value"],
                        value_type=ClaimValueType(c["value_type"]),
                        confidence=float(c["confidence"]),
                        provenance=Provenance(**c["provenance"]),
                        context=c.get("context", {}) or {},
                    )
                )
            except Exception:
                continue

        return claims

    def _expand_readable_artifacts(self, actor: Provenance, items: List[RoutedItem]) -> List[RoutedItem]:
        expanded: List[RoutedItem] = []
        for item in items:
            expanded.append(item)

            # If the event references an artifact, attempt to read it through SecureBlackboard
            if item.kind != "event":
                continue
            ev = item.data.get("event", {})
            data = ev.get("data", {}) or {}
            # artifact id might be inside event payload
            artifact_id = ev.get("artifact_id") or data.get("artifact_id")
            if not artifact_id:
                continue

            try:
                payload = self.secure_bb.read_artifact(actor, artifact_id)
                expanded.append(
                    RoutedItem(
                        kind="artifact",
                        summary=f"artifact({artifact_id}) readable",
                        data={"artifact_id": artifact_id, "payload": payload},
                        provenance=item.provenance,
                    )
                )
            except PermissionError:
                # silently ignore; not readable for this actor
                continue
            except KeyError:
                continue

        return expanded
