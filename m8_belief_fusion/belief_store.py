from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from mam.m1_blackboard.blackboard import Blackboard, Provenance, EventType
from mam.m7_partner_models.partner_model import PartnerModelStore


# -----------------------------
# Helpers
# -----------------------------

def _now_ms() -> int:
    return int(time.time() * 1000)


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# -----------------------------
# Core Belief Types
# -----------------------------

@dataclass
class Evidence:
    """
    A single piece of evidence supporting a belief.
    """
    evidence_id: str
    source_agent_id: str
    value: Any
    confidence: float
    timestamp_ms: int


@dataclass
class Belief:
    """
    A belief about the world.

    Fields:
        key: logical identifier (e.g. "door_open", "eta_delivery")
        value: fused value
        confidence: overall confidence in [0,1]
        uncertainty: optional measure (variance / interval width)
        updated_ms: last update time
        evidence: recent evidence items
    """
    key: str
    value: Any
    confidence: float
    uncertainty: Optional[float]
    updated_ms: int
    evidence: List[Evidence] = field(default_factory=list)


# -----------------------------
# Belief Store
# -----------------------------

class BeliefStore:
    """
    Maintains a shared, fused belief state for the team.

    Design principles:
    - interpretable
    - incremental updates
    - evidence-preserving
    - no forced single truth
    """

    def __init__(
        self,
        blackboard: Blackboard,
        *,
        partner_models: Optional[PartnerModelStore] = None,
        decay_half_life_ms: int = 5 * 60 * 1000,  # 5 minutes
    ):
        self.bb = blackboard
        self.partner_models = partner_models
        self.decay_half_life_ms = decay_half_life_ms
        self._beliefs: Dict[str, Belief] = {}

    # -------------------------
    # Public API
    # -------------------------

    def observe(
        self,
        *,
        key: str,
        value: Any,
        confidence: float,
        provenance: Provenance,
        uncertainty: Optional[float] = None,
    ) -> Belief:
        """
        Add a new observation and fuse it into the belief state.
        """
        conf = _clamp01(float(confidence))

        # Weight by partner trust if available
        if self.partner_models:
            profile = self.partner_models.get(provenance.agent_id)
            conf = _clamp01(conf * profile.trust)

        ev = Evidence(
            evidence_id=_new_id("ev"),
            source_agent_id=provenance.agent_id,
            value=value,
            confidence=conf,
            timestamp_ms=_now_ms(),
        )

        belief = self._beliefs.get(key)
        if belief is None:
            belief = Belief(
                key=key,
                value=value,
                confidence=conf,
                uncertainty=uncertainty,
                updated_ms=ev.timestamp_ms,
                evidence=[ev],
            )
        else:
            belief = self._fuse(belief, ev, uncertainty)

        self._beliefs[key] = belief
        self._persist_belief(provenance, belief, reason="observe")

        return belief

    def get(self, key: str) -> Optional[Belief]:
        """
        Retrieve a belief (after decay).
        """
        belief = self._beliefs.get(key)
        if not belief:
            return None
        return self._apply_decay(belief)

    def all_beliefs(self) -> List[Belief]:
        """
        Return all beliefs with decay applied.
        """
        out: List[Belief] = []
        for b in self._beliefs.values():
            out.append(self._apply_decay(b))
        return out

    # -------------------------
    # Fusion Logic
    # -------------------------

    def _fuse(
        self,
        belief: Belief,
        ev: Evidence,
        uncertainty: Optional[float],
    ) -> Belief:
        """
        Fuse a new evidence item into an existing belief.

        Fusion rules:
        - numeric values: confidence-weighted average
        - boolean / categorical: confidence-weighted vote
        """
        old_value = belief.value
        old_conf = belief.confidence

        # Numeric fusion
        if isinstance(old_value, (int, float)) and isinstance(ev.value, (int, float)):
            total = old_conf + ev.confidence
            if total > 0:
                new_value = (
                    (old_value * old_conf) + (ev.value * ev.confidence)
                ) / total
            else:
                new_value = ev.value
            new_conf = _clamp01((old_conf + ev.confidence) / 2)

        # Boolean or categorical fusion
        else:
            if ev.confidence >= old_conf:
                new_value = ev.value
                new_conf = ev.confidence
            else:
                new_value = old_value
                new_conf = old_conf

        belief.value = new_value
        belief.confidence = new_conf
        belief.updated_ms = ev.timestamp_ms
        belief.uncertainty = uncertainty if uncertainty is not None else belief.uncertainty
        belief.evidence.append(ev)

        # keep evidence tail short
        if len(belief.evidence) > 20:
            belief.evidence = belief.evidence[-20:]

        return belief

    # -------------------------
    # Decay
    # -------------------------

    def _apply_decay(self, belief: Belief) -> Belief:
        """
        Apply temporal decay to belief confidence.
        """
        age = _now_ms() - belief.updated_ms
        if age <= 0:
            return belief

        # exponential half-life decay
        decay_factor = 0.5 ** (age / self.decay_half_life_ms)
        belief.confidence = _clamp01(belief.confidence * decay_factor)
        return belief

    # -------------------------
    # Persistence
    # -------------------------

    def _persist_belief(self, actor: Provenance, belief: Belief, *, reason: str) -> str:
        """
        Persist belief snapshot into M1 for audit/debug.
        """
        payload = {
            "belief": {
                "key": belief.key,
                "value": belief.value,
                "confidence": belief.confidence,
                "uncertainty": belief.uncertainty,
                "updated_ms": belief.updated_ms,
                "evidence": [asdict(e) for e in belief.evidence[-5:]],
            },
            "meta": {"reason": reason},
        }

        art_id = self.bb.put_artifact(actor, kind="json", payload=payload)
        self.bb.post_event(
            EventType.NOTE,
            actor,
            text=f"belief_updated key={belief.key} reason={reason}",
            data={"belief_key": belief.key, "artifact_id": art_id},
            artifact_id=art_id,
        )
        return art_id
