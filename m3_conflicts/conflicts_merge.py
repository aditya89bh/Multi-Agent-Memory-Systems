from __future__ import annotations

import time
import math
import uuid
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from mam.m1_blackboard.blackboard import Blackboard, Provenance, EventType


# -----------------------------
# Core types
# -----------------------------

class ClaimValueType(str, Enum):
    """A small type system to make conflict detection predictable."""
    TEXT = "text"
    NUMBER = "number"
    BOOL = "bool"
    JSON = "json"


class ResolutionPolicy(str, Enum):
    """
    How to resolve conflicts when multiple claims exist.

    KEEP_ALL: do not decide; return ranked claims
    BEST_SALIENCE: pick the highest salience claim
    TRUST_WEIGHTED: salience emphasizes trust weight more heavily
    RECENCY_WEIGHTED: salience emphasizes recency more heavily
    CONSENSUS_MAJORITY: pick the most common value across claims (ties -> best salience)
    """
    KEEP_ALL = "keep_all"
    BEST_SALIENCE = "best_salience"
    TRUST_WEIGHTED = "trust_weighted"
    RECENCY_WEIGHTED = "recency_weighted"
    CONSENSUS_MAJORITY = "consensus_majority"


@dataclass(frozen=True)
class Claim:
    """
    A claim is a statement about a memory key that may be contested.

    Fields:
        claim_id: Unique id for the claim.
        key: Logical memory key (e.g., "eta_days", "customer_priority").
        value: The claimed value (JSON-serializable).
        value_type: Helps conflict detection behave consistently.
        confidence: Writer-reported confidence in [0, 1].
        provenance: Who/when said it.
        context: Optional extra fields (task_id, object_id, etc.)
    """
    claim_id: str
    key: str
    value: Any
    value_type: ClaimValueType
    confidence: float
    provenance: Provenance
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Conflict:
    """
    A record that two claims are incompatible.

    Fields:
        conflict_id: Unique id.
        key: Memory key under dispute.
        claim_a: Claim id.
        claim_b: Claim id.
        reason: Human-readable conflict reason.
        created_ms: Timestamp.
        metadata: Extra diagnostic info.
    """
    conflict_id: str
    key: str
    claim_a: str
    claim_b: str
    reason: str
    created_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)


# -----------------------------
# Helpers
# -----------------------------

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

def _is_number(x: Any) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)

def _normalize_value_for_vote(value: Any) -> str:
    # Stable stringification for majority voting
    return str(value)

def _age_ms(prov: Provenance, now_ms: int) -> int:
    return max(0, now_ms - int(prov.timestamp_ms))


# -----------------------------
# Conflict detection
# -----------------------------

def detect_conflict(
    a: Claim,
    b: Claim,
    *,
    numeric_tolerance: float = 0.0,
    min_confidence: float = 0.0,
) -> Optional[str]:
    """
    Decide whether two claims conflict.

    Returns:
        None if compatible / no conflict, else a string reason.

    Notes:
    - This is intentionally conservative: only flags conflict when "meaningfully different".
    - Later you can expand with domain-aware validators (ranges, constraints, units).
    """
    if a.key != b.key:
        return None

    if a.confidence < min_confidence or b.confidence < min_confidence:
        return None

    # If types differ, treat as conflict unless one is JSON and the other is TEXT (could be encoding)
    if a.value_type != b.value_type:
        return f"type_mismatch({a.value_type.value} vs {b.value_type.value})"

    vt = a.value_type

    if vt == ClaimValueType.BOOL:
        if bool(a.value) != bool(b.value):
            return "bool_mismatch"
        return None

    if vt == ClaimValueType.NUMBER:
        if not _is_number(a.value) or not _is_number(b.value):
            return "number_type_error"
        diff = abs(float(a.value) - float(b.value))
        if diff > float(numeric_tolerance):
            return f"number_mismatch(diff={diff})"
        return None

    if vt == ClaimValueType.TEXT:
        if str(a.value).strip().lower() != str(b.value).strip().lower():
            return "text_mismatch"
        return None

    # JSON: shallow compare as string. Conservative.
    if vt == ClaimValueType.JSON:
        if _normalize_value_for_vote(a.value) != _normalize_value_for_vote(b.value):
            return "json_mismatch"
        return None

    # Default: if values differ, call it a conflict
    if a.value != b.value:
        return "value_mismatch"
    return None


# -----------------------------
# Salience scoring
# -----------------------------

@dataclass(frozen=True)
class SalienceWeights:
    """
    Weights for salience scoring.

    confidence_weight: emphasize writer confidence
    recency_weight: emphasize freshness
    trust_weight: emphasize trust score per agent_id
    half_life_ms: recency decay half-life (default 2 hours)
    """
    confidence_weight: float = 0.55
    recency_weight: float = 0.25
    trust_weight: float = 0.20
    half_life_ms: int = 2 * 60 * 60 * 1000  # 2 hours


def salience_score(
    claim: Claim,
    *,
    now_ms: Optional[int] = None,
    trust_by_agent: Optional[Dict[str, float]] = None,
    weights: Optional[SalienceWeights] = None,
) -> float:
    """
    Compute a salience score in [0, 1] for ranking claims.

    Salience combines:
    - confidence (self-reported)
    - recency (exponential decay)
    - trust (external score for the agent)

    Returns:
        float in [0, 1]
    """
    weights = weights or SalienceWeights()
    trust_by_agent = trust_by_agent or {}
    now_ms = now_ms if now_ms is not None else _now_ms()

    c = _clamp01(float(claim.confidence))

    age = _age_ms(claim.provenance, now_ms)
    # exp decay where score halves every half_life_ms
    # score = 0.5^(age/half_life)
    if weights.half_life_ms <= 0:
        r = 1.0
    else:
        r = math.pow(0.5, age / float(weights.half_life_ms))

    t = _clamp01(float(trust_by_agent.get(claim.provenance.agent_id, 0.5)))

    score = (
        weights.confidence_weight * c +
        weights.recency_weight * r +
        weights.trust_weight * t
    )
    return _clamp01(score)


def rank_claims(
    claims: List[Claim],
    *,
    trust_by_agent: Optional[Dict[str, float]] = None,
    policy: ResolutionPolicy = ResolutionPolicy.BEST_SALIENCE,
) -> List[Tuple[float, Claim]]:
    """
    Rank claims from most to least salient.

    Different policies adjust weights:
    - TRUST_WEIGHTED: trust dominates
    - RECENCY_WEIGHTED: recency dominates
    """
    trust_by_agent = trust_by_agent or {}
    base = SalienceWeights()

    if policy == ResolutionPolicy.TRUST_WEIGHTED:
        weights = SalienceWeights(confidence_weight=0.35, recency_weight=0.15, trust_weight=0.50, half_life_ms=base.half_life_ms)
    elif policy == ResolutionPolicy.RECENCY_WEIGHTED:
        weights = SalienceWeights(confidence_weight=0.35, recency_weight=0.50, trust_weight=0.15, half_life_ms=base.half_life_ms)
    else:
        weights = base

    now_ms = _now_ms()
    scored = [(salience_score(c, now_ms=now_ms, trust_by_agent=trust_by_agent, weights=weights), c) for c in claims]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


# -----------------------------
# Resolution
# -----------------------------

@dataclass(frozen=True)
class ResolutionResult:
    """
    Output of resolving a set of claims for a key.

    Fields:
        key: Memory key.
        policy: Resolution policy used.
        chosen: Chosen claim (if any).
        ranked: Ranked claims (always returned).
        conflicts: Conflict records detected among claims.
    """
    key: str
    policy: ResolutionPolicy
    chosen: Optional[Claim]
    ranked: List[Tuple[float, Claim]]
    conflicts: List[Conflict]


def resolve_claims(
    key: str,
    claims: List[Claim],
    *,
    policy: ResolutionPolicy = ResolutionPolicy.BEST_SALIENCE,
    trust_by_agent: Optional[Dict[str, float]] = None,
    numeric_tolerance: float = 0.0,
    min_confidence_for_conflict: float = 0.0,
) -> ResolutionResult:
    """
    Resolve claims for a given key.

    Always:
    - ranks claims by salience
    - detects conflicts between incompatible claim pairs

    Policy behaviors:
    - KEEP_ALL: no chosen claim
    - BEST_SALIENCE/TRUST_WEIGHTED/RECENCY_WEIGHTED: choose highest-ranked
    - CONSENSUS_MAJORITY: choose most common value; break ties by salience
    """
    trust_by_agent = trust_by_agent or {}

    # Only claims matching this key
    pool = [c for c in claims if c.key == key]
    ranked = rank_claims(pool, trust_by_agent=trust_by_agent, policy=policy)

    # Detect conflicts (pairwise)
    conflicts: List[Conflict] = []
    for i in range(len(pool)):
        for j in range(i + 1, len(pool)):
            reason = detect_conflict(
                pool[i], pool[j],
                numeric_tolerance=numeric_tolerance,
                min_confidence=min_confidence_for_conflict,
            )
            if reason:
                conflicts.append(
                    Conflict(
                        conflict_id=_new_id("conf"),
                        key=key,
                        claim_a=pool[i].claim_id,
                        claim_b=pool[j].claim_id,
                        reason=reason,
                        created_ms=_now_ms(),
                        metadata={
                            "a_value": pool[i].value,
                            "b_value": pool[j].value,
                            "a_agent": pool[i].provenance.agent_id,
                            "b_agent": pool[j].provenance.agent_id,
                        },
                    )
                )

    chosen: Optional[Claim] = None

    if policy == ResolutionPolicy.KEEP_ALL:
        chosen = None

    elif policy in (
        ResolutionPolicy.BEST_SALIENCE,
        ResolutionPolicy.TRUST_WEIGHTED,
        ResolutionPolicy.RECENCY_WEIGHTED,
    ):
        chosen = ranked[0][1] if ranked else None

    elif policy == ResolutionPolicy.CONSENSUS_MAJORITY:
        if not pool:
            chosen = None
        else:
            # Vote on normalized value
            counts: Dict[str, int] = {}
            for c in pool:
                k = _normalize_value_for_vote(c.value)
                counts[k] = counts.get(k, 0) + 1
            max_votes = max(counts.values()) if counts else 0
            winners = {val for val, ct in counts.items() if ct == max_votes}

            # Among winners, choose best salience
            if not ranked:
                chosen = None
            else:
                for _, c in ranked:
                    if _normalize_value_for_vote(c.value) in winners:
                        chosen = c
                        break

    return ResolutionResult(
        key=key,
        policy=policy,
        chosen=chosen,
        ranked=ranked,
        conflicts=conflicts,
    )


# -----------------------------
# Optional: persistence helpers (store claims/conflicts in M1)
# -----------------------------

class ConflictManager:
    """
    Helper to persist claims and conflicts into the shared Blackboard.

    This does not enforce permissions itself.
    If you want enforcement, call this through M2's SecureBlackboard to write artifacts.

    Usage:
        mgr = ConflictManager(bb, trust_by_agent={"agent_A": 0.7})
        claim_id = mgr.add_claim(...)
        result = mgr.resolve(key="eta_days", policy=..., ...)
        mgr.persist_resolution(result)
    """

    def __init__(self, blackboard: Blackboard, trust_by_agent: Optional[Dict[str, float]] = None):
        self.bb = blackboard
        self.trust_by_agent = trust_by_agent or {}

    def add_claim(
        self,
        key: str,
        value: Any,
        value_type: ClaimValueType,
        confidence: float,
        provenance: Provenance,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Claim:
        """
        Create a Claim and persist it as an artifact + event in M1.

        Returns:
            Claim object
        """
        claim = Claim(
            claim_id=_new_id("claim"),
            key=key,
            value=value,
            value_type=value_type,
            confidence=_clamp01(confidence),
            provenance=provenance,
            context=context or {},
        )

        art_id = self.bb.put_artifact(
            provenance,
            kind="json",
            payload={"claim": asdict(claim)},
        )

        self.bb.post_event(
            EventType.NOTE,
            provenance,
            text=f"claim_added key={key}",
            data={"key": key, "claim_id": claim.claim_id, "artifact_id": art_id},
            artifact_id=art_id,
        )
        return claim

    def resolve(
        self,
        key: str,
        claims: List[Claim],
        *,
        policy: ResolutionPolicy = ResolutionPolicy.BEST_SALIENCE,
        numeric_tolerance: float = 0.0,
        min_confidence_for_conflict: float = 0.0,
    ) -> ResolutionResult:
        """Resolve claims for a key using the configured trust map."""
        return resolve_claims(
            key=key,
            claims=claims,
            policy=policy,
            trust_by_agent=self.trust_by_agent,
            numeric_tolerance=numeric_tolerance,
            min_confidence_for_conflict=min_confidence_for_conflict,
        )

    def persist_resolution(self, provenance: Provenance, result: ResolutionResult) -> str:
        """
        Persist a ResolutionResult into M1 for audit/debug.

        Stores:
        - chosen claim (if any)
        - ranked list with salience scores
        - conflict records

        Returns:
            artifact_id of the resolution artifact
        """
        payload = {
            "resolution": {
                "key": result.key,
                "policy": result.policy.value,
                "chosen_claim_id": result.chosen.claim_id if result.chosen else None,
                "ranked": [
                    {"score": float(score), "claim_id": claim.claim_id}
                    for score, claim in result.ranked
                ],
                "conflicts": [asdict(c) for c in result.conflicts],
            }
        }

        art_id = self.bb.put_artifact(
            provenance,
            kind="json",
            payload=payload,
        )

        self.bb.post_event(
            EventType.NOTE,
            provenance,
            text=f"claims_resolved key={result.key} policy={result.policy.value}",
            data={"key": result.key, "artifact_id": art_id},
            artifact_id=art_id,
        )

        return art_id
