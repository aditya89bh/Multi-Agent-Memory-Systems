from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

from mam.m1_blackboard.blackboard import Blackboard, Provenance, EventType
from mam.m5_episodic.episode import Episode
from mam.m9_credit.credit import Contribution, ContributionType


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
# Culture Types
# -----------------------------

@dataclass
class CultureArtifact:
    """
    A persistent organizational norm / heuristic.

    Examples:
    - "Always check world-state uncertainty before executing"
    - "Prefer critic review when conflicts persist"
    - "Avoid late planning changes without consensus"
    """
    artifact_id: str
    statement: str
    confidence: float
    tags: List[str]
    evidence_ids: List[str]
    created_ms: int
    updated_ms: int


# -----------------------------
# Culture Store
# -----------------------------

class CultureStore:
    """
    Maintains organizational memory and evolving norms.

    Design principles:
    - slow-changing
    - interpretable
    - evidence-backed
    """

    def __init__(self, blackboard: Blackboard):
        self.bb = blackboard
        self._artifacts: Dict[str, CultureArtifact] = {}

    # -------------------------
    # CRUD
    # -------------------------

    def all_artifacts(self) -> List[CultureArtifact]:
        return list(self._artifacts.values())

    def add_or_update(
        self,
        *,
        statement: str,
        delta_confidence: float,
        tags: Optional[List[str]],
        evidence_ids: List[str],
        actor: Provenance,
    ) -> CultureArtifact:
        """
        Create or update a culture artifact.

        If a similar statement exists, confidence is updated.
        """
        # naive similarity: exact statement match
        existing = None
        for art in self._artifacts.values():
            if art.statement == statement:
                existing = art
                break

        now = _now_ms()
        if existing:
            existing.confidence = _clamp01(existing.confidence + delta_confidence)
            existing.updated_ms = now
            existing.evidence_ids.extend(evidence_ids)
            art = existing
            reason = "updated"
        else:
            art = CultureArtifact(
                artifact_id=_new_id("cult"),
                statement=statement,
                confidence=_clamp01(delta_confidence),
                tags=tags or [],
                evidence_ids=list(evidence_ids),
                created_ms=now,
                updated_ms=now,
            )
            self._artifacts[art.artifact_id] = art
            reason = "created"

        self._persist(actor, art, reason=reason)
        return art

    # -------------------------
    # Pattern Extraction (Lightweight)
    # -------------------------

    def ingest_episode(
        self,
        *,
        episode: Episode,
        outcome_score: float,
        contributions: List[Contribution],
        actor: Provenance,
    ) -> None:
        """
        Update culture based on episode + credit signals.

        This is intentionally heuristic-based and interpretable.
        """
        score = _clamp01(outcome_score)

        # Success patterns
        if score > 0.7:
            stmt = "Reusing clear plans and role separation improves outcomes"
            self.add_or_update(
                statement=stmt,
                delta_confidence=0.05,
                tags=["planning", "roles"],
                evidence_ids=[episode.episode_id],
                actor=actor,
            )

        # Failure patterns
        if score < 0.3:
            stmt = "Poor coordination and unclear ownership lead to failure"
            self.add_or_update(
                statement=stmt,
                delta_confidence=0.06,
                tags=["coordination", "ownership"],
                evidence_ids=[episode.episode_id],
                actor=actor,
            )

        # Credit-driven norms
        for c in contributions:
            if c.contribution_type == ContributionType.HURT and c.strength > 0.5:
                stmt = "Escalate review when strong negative contributions appear"
                self.add_or_update(
                    statement=stmt,
                    delta_confidence=0.04,
                    tags=["review", "risk"],
                    evidence_ids=[c.contribution_id],
                    actor=actor,
                )

    # -------------------------
    # Query
    # -------------------------

    def query(
        self,
        *,
        tag: Optional[str] = None,
        min_confidence: float = 0.3,
        limit: int = 5,
    ) -> List[CultureArtifact]:
        """
        Query culture artifacts by tag and confidence.
        """
        arts = [
            a for a in self._artifacts.values()
            if a.confidence >= min_confidence and (tag is None or tag in a.tags)
        ]
        arts.sort(key=lambda x: x.confidence, reverse=True)
        return arts[: max(1, limit)]

    # -------------------------
    # Persistence
    # -------------------------

    def _persist(self, actor: Provenance, art: CultureArtifact, *, reason: str) -> str:
        payload = {
            "culture_artifact": asdict(art),
            "meta": {"reason": reason},
        }

        art_id = self.bb.put_artifact(actor, kind="json", payload=payload)
        self.bb.post_event(
            EventType.NOTE,
            actor,
            text=f"culture_{reason}: {art.statement}",
            data={
                "culture_artifact_id": art.artifact_id,
                "confidence": art.confidence,
                "artifact_id": art_id,
            },
            artifact_id=art_id,
        )
        return art_id
