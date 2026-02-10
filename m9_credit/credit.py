from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Optional

from mam.m1_blackboard.blackboard import Blackboard, Provenance, EventType
from mam.m5_episodic.episode import Episode
from mam.m7_partner_models.partner_model import (
    PartnerModelStore,
    InteractionSignal,
)


# -----------------------------
# Helpers
# -----------------------------

def _now_ms() -> int:
    return int(time.time() * 1000)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


# -----------------------------
# Core Types
# -----------------------------

class ContributionType(str, Enum):
    HELPED = "helped"
    HURT = "hurt"


@dataclass
class Contribution:
    """
    A single credit/blame attribution.

    Fields:
        contribution_id: unique id
        agent_id: who is being credited/blamed
        contribution_type: helped / hurt
        strength: [0,1]
        reason: short explanation
        episode_id: optional episode link
        evidence: optional structured evidence
        created_ms: timestamp
    """
    contribution_id: str
    agent_id: str
    contribution_type: ContributionType
    strength: float
    reason: str
    episode_id: Optional[str]
    evidence: Dict[str, Any]
    created_ms: int


# -----------------------------
# Credit Assigner
# -----------------------------

class CreditAssigner:
    """
    Assigns credit/blame signals based on episode outcomes
    and propagates them into partner models.

    This is intentionally simple and interpretable.
    """

    def __init__(
        self,
        blackboard: Blackboard,
        *,
        partner_models: Optional[PartnerModelStore] = None,
    ):
        self.bb = blackboard
        self.partner_models = partner_models

    # -------------------------
    # Main API
    # -------------------------

    def assign_from_episode(
        self,
        *,
        episode: Episode,
        outcome_score: float,
        reason: str,
        actor: Provenance,
    ) -> List[Contribution]:
        """
        Assign credit/blame to participants based on an episode outcome.

        Args:
            episode: Episode from M5
            outcome_score:
                > 0.5 => success
                < 0.5 => failure
                exactly 0.5 => neutral
            reason: human-readable explanation
            actor: provenance of the assessor

        Returns:
            list of Contribution records
        """
        score = _clamp01(float(outcome_score))
        contributions: List[Contribution] = []

        if not episode.participants:
            return contributions

        # Simple equal-split policy for now
        per_agent_strength = abs(score - 0.5) * 2.0
        per_agent_strength = _clamp01(per_agent_strength)

        helped = score > 0.5
        ctype = ContributionType.HELPED if helped else ContributionType.HURT

        for agent_id, role in episode.participants.items():
            c = Contribution(
                contribution_id=_new_id("cr"),
                agent_id=agent_id,
                contribution_type=ctype,
                strength=per_agent_strength,
                reason=reason,
                episode_id=episode.episode_id,
                evidence={
                    "role": role,
                    "outcome_score": score,
                },
                created_ms=_now_ms(),
            )

            self._persist_contribution(actor, c)
            contributions.append(c)

            # Propagate into partner models (if enabled)
            if self.partner_models:
                signal_kind = "helped" if helped else "hurt"
                signal = InteractionSignal(
                    partner_agent_id=agent_id,
                    kind=signal_kind,
                    strength=per_agent_strength,
                    metadata={
                        "episode_id": episode.episode_id,
                        "reason": reason,
                    },
                )
                self.partner_models.apply_signal(actor, signal)

        return contributions

    # -------------------------
    # Persistence
    # -------------------------

    def _persist_contribution(self, actor: Provenance, c: Contribution) -> str:
        """
        Persist contribution into M1 for audit/debug.
        """
        payload = {
            "contribution": asdict(c),
        }

        art_id = self.bb.put_artifact(actor, kind="json", payload=payload)
        self.bb.post_event(
            EventType.NOTE,
            actor,
            text=f"credit_assigned agent={c.agent_id} type={c.contribution_type.value}",
            data={
                "agent_id": c.agent_id,
                "contribution_type": c.contribution_type.value,
                "strength": c.strength,
                "episode_id": c.episode_id,
                "artifact_id": art_id,
            },
            artifact_id=art_id,
        )
        return art_id
