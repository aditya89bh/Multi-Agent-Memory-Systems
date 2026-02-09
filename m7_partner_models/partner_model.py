from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Tuple

from mam.m1_blackboard.blackboard import Blackboard, Provenance, EventType


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _now_ms() -> int:
    return int(time.time() * 1000)


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


@dataclass
class PartnerProfile:
    """
    A lightweight theory-of-mind profile for another agent.

    Scores are all in [0, 1] and are meant to be updated over time.

    Fields:
        partner_agent_id: The agent being modeled.
        trust: "Do I believe this agent's claims/actions are useful/accurate?"
        calibration: "Does their confidence match reality?" (overconfidence -> lower)
        reliability: "Do they follow through and deliver?"
        responsiveness: "How quickly do they respond / act when asked?"
        domains: Skill tags with weights (e.g. {"debugging": 0.8, "planning": 0.6})
        notes: Freeform short notes for humans/agents.
        updated_ms: Last update time.
        history: small rolling log of updates (debuggable).
    """
    partner_agent_id: str
    trust: float = 0.5
    calibration: float = 0.5
    reliability: float = 0.5
    responsiveness: float = 0.5
    domains: Dict[str, float] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)
    updated_ms: int = field(default_factory=_now_ms)
    history: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class InteractionSignal:
    """
    A normalized signal used to update partner models.

    Fields:
        partner_agent_id: agent being updated
        kind: one of:
            - "claim_correct"
            - "claim_incorrect"
            - "commitment_done"
            - "commitment_missed"
            - "helped"
            - "hurt"
            - "fast_response"
            - "slow_response"
        strength: [0, 1] how strong the signal is
        domain: optional domain tag (e.g., "planning", "debugging")
        metadata: optional extra fields (evidence ids, episode id, etc.)
    """
    partner_agent_id: str
    kind: str
    strength: float = 1.0
    domain: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PartnerModelStore:
    """
    Stores and updates PartnerProfiles, and optionally persists them into M1.

    This module is deliberately simple:
    - small state
    - interpretable update rules
    - easy to replace with learned models later

    Persistence strategy:
    - store profile snapshots as JSON artifacts in M1
    - log updates as NOTE events for audit/debug
    """

    def __init__(self, blackboard: Blackboard):
        self.bb = blackboard
        self._profiles: Dict[str, PartnerProfile] = {}

    # -------------------------
    # CRUD
    # -------------------------

    def get(self, partner_agent_id: str) -> PartnerProfile:
        """
        Get a profile. If missing, create a default one.
        """
        if partner_agent_id not in self._profiles:
            self._profiles[partner_agent_id] = PartnerProfile(partner_agent_id=partner_agent_id)
        return self._profiles[partner_agent_id]

    def all_profiles(self) -> List[PartnerProfile]:
        """
        Return all known partner profiles.
        """
        return list(self._profiles.values())

    # -------------------------
    # Update rules
    # -------------------------

    def apply_signal(self, actor: Provenance, signal: InteractionSignal) -> PartnerProfile:
        """
        Apply a signal to update the partner profile.

        Args:
            actor: provenance of who is performing the update (the observer)
            signal: normalized signal about the partner

        Returns:
            Updated PartnerProfile
        """
        p = self.get(signal.partner_agent_id)

        s = _clamp01(float(signal.strength))

        # Interpretable rule-based updates (small deltas)
        # You can tune these easily.
        if signal.kind == "claim_correct":
            p.trust = _clamp01(p.trust + 0.08 * s)
            p.calibration = _clamp01(p.calibration + 0.05 * s)

        elif signal.kind == "claim_incorrect":
            p.trust = _clamp01(p.trust - 0.10 * s)
            # incorrect claims, especially confident ones, imply miscalibration
            p.calibration = _clamp01(p.calibration - 0.08 * s)

        elif signal.kind == "commitment_done":
            p.reliability = _clamp01(p.reliability + 0.10 * s)

        elif signal.kind == "commitment_missed":
            p.reliability = _clamp01(p.reliability - 0.12 * s)

        elif signal.kind == "helped":
            p.trust = _clamp01(p.trust + 0.06 * s)

        elif signal.kind == "hurt":
            p.trust = _clamp01(p.trust - 0.08 * s)

        elif signal.kind == "fast_response":
            p.responsiveness = _clamp01(p.responsiveness + 0.08 * s)

        elif signal.kind == "slow_response":
            p.responsiveness = _clamp01(p.responsiveness - 0.08 * s)

        # Domain skill update
        if signal.domain:
            cur = float(p.domains.get(signal.domain, 0.5))
            # Reward/punish based on kind. Keep it bounded.
            if signal.kind in ("claim_correct", "commitment_done", "helped"):
                cur = _clamp01(cur + 0.07 * s)
            elif signal.kind in ("claim_incorrect", "commitment_missed", "hurt"):
                cur = _clamp01(cur - 0.07 * s)
            p.domains[signal.domain] = cur

        p.updated_ms = _now_ms()
        p.history.append(
            {
                "at_ms": p.updated_ms,
                "observer_agent_id": actor.agent_id,
                "kind": signal.kind,
                "strength": s,
                "domain": signal.domain,
                "metadata": signal.metadata,
                "snapshot": {
                    "trust": p.trust,
                    "calibration": p.calibration,
                    "reliability": p.reliability,
                    "responsiveness": p.responsiveness,
                },
            }
        )

        # Keep history small
        if len(p.history) > 50:
            p.history = p.history[-50:]

        # Persist snapshot
        self._persist_profile(actor, p, reason=f"signal:{signal.kind}")

        return p

    # -------------------------
    # Delegation hints
    # -------------------------

    def suggest_partners(
        self,
        *,
        domain: Optional[str] = None,
        min_trust: float = 0.0,
        limit: int = 5,
    ) -> List[Tuple[float, PartnerProfile]]:
        """
        Suggest best partners for a domain.

        Score combines:
        - trust
        - reliability
        - domain score (if provided)

        Returns:
            list of (score, profile) descending
        """
        scored: List[Tuple[float, PartnerProfile]] = []

        for p in self._profiles.values():
            if p.trust < min_trust:
                continue
            dom = float(p.domains.get(domain, 0.5)) if domain else 0.5
            score = (0.45 * p.trust) + (0.30 * p.reliability) + (0.25 * dom)
            scored.append((score, p))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[: max(1, limit)]

    # -------------------------
    # Persistence
    # -------------------------

    def _persist_profile(self, actor: Provenance, profile: PartnerProfile, *, reason: str) -> str:
        """
        Persist a profile snapshot into M1 for audit/debug.

        Returns:
            artifact_id
        """
        payload = {
            "partner_profile": {
                "partner_agent_id": profile.partner_agent_id,
                "trust": profile.trust,
                "calibration": profile.calibration,
                "reliability": profile.reliability,
                "responsiveness": profile.responsiveness,
                "domains": profile.domains,
                "notes": profile.notes,
                "updated_ms": profile.updated_ms,
                "history_tail": profile.history[-5:],  # keep payload light
            },
            "meta": {"reason": reason},
        }

        art_id = self.bb.put_artifact(actor, kind="json", payload=payload)
        self.bb.post_event(
            EventType.NOTE,
            actor,
            text=f"partner_profile_updated partner={profile.partner_agent_id} reason={reason}",
            data={"partner_agent_id": profile.partner_agent_id, "reason": reason, "artifact_id": art_id},
            artifact_id=art_id,
        )
        return art_id
