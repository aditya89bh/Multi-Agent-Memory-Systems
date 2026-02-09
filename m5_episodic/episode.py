from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

from mam.m1_blackboard.blackboard import Blackboard, MemoryEvent, Provenance, EventType


# -----------------------------
# Core Episode Types
# -----------------------------

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


@dataclass(frozen=True)
class EpisodeEvent:
    """
    A lightweight projection of a MemoryEvent inside an episode timeline.
    """
    event_id: str
    event_type: str
    text: str
    data: Dict[str, Any]
    provenance: Provenance
    timestamp_ms: int


@dataclass
class Episode:
    """
    A structured record of coordinated multi-agent work.

    An episode is intended to be:
    - replayable
    - summarizable
    - reusable for future planning
    """
    episode_id: str
    task_id: str
    participants: Dict[str, str]  # agent_id -> role
    started_ms: int
    ended_ms: Optional[int] = None
    timeline: List[EpisodeEvent] = field(default_factory=list)
    outcomes: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def duration_ms(self) -> Optional[int]:
        if self.ended_ms is None:
            return None
        return max(0, self.ended_ms - self.started_ms)

    def is_closed(self) -> bool:
        return self.ended_ms is not None


# -----------------------------
# Episode Builder
# -----------------------------

class EpisodeBuilder:
    """
    Builds team episodes from the M1 event log.

    This class does not mutate M1.
    It projects events into structured episodes.
    """

    def __init__(self, blackboard: Blackboard):
        self.bb = blackboard

    def build_episode(
        self,
        *,
        task_id: str,
        session_id: Optional[str] = None,
        since_ms: Optional[int] = None,
        until_ms: Optional[int] = None,
        close_on_outcome: bool = True,
    ) -> Episode:
        """
        Build a single episode by filtering events.

        Args:
            task_id: Logical task identifier.
            session_id: Optional session filter.
            since_ms: Lower bound timestamp.
            until_ms: Upper bound timestamp.
            close_on_outcome: If True, close episode at last OUTCOME event.

        Returns:
            Episode
        """
        events = self._collect_events(
            task_id=task_id,
            session_id=session_id,
            since_ms=since_ms,
            until_ms=until_ms,
        )

        if not events:
            raise ValueError(f"No events found for task_id={task_id}")

        started_ms = events[0].provenance.timestamp_ms
        ended_ms = None

        timeline: List[EpisodeEvent] = []
        participants: Dict[str, str] = {}

        for ev in events:
            prov = ev.provenance
            participants.setdefault(prov.agent_id, prov.role)

            timeline.append(
                EpisodeEvent(
                    event_id=ev.event_id,
                    event_type=ev.event_type.value,
                    text=ev.text,
                    data=ev.data,
                    provenance=prov,
                    timestamp_ms=prov.timestamp_ms,
                )
            )

            if close_on_outcome and ev.event_type == EventType.OUTCOME:
                ended_ms = prov.timestamp_ms

        if ended_ms is None:
            ended_ms = events[-1].provenance.timestamp_ms

        return Episode(
            episode_id=_new_id("ep"),
            task_id=task_id,
            participants=participants,
            started_ms=started_ms,
            ended_ms=ended_ms,
            timeline=timeline,
        )

    # -------------------------
    # Helpers
    # -------------------------

    def _collect_events(
        self,
        *,
        task_id: str,
        session_id: Optional[str],
        since_ms: Optional[int],
        until_ms: Optional[int],
    ) -> List[MemoryEvent]:
        """
        Collect relevant events from the Blackboard.

        We rely on convention:
        - task_id should appear in event.data["task_id"]
        """
        raw = self.bb.query_events(limit=1000)

        out: List[MemoryEvent] = []
        for ev in raw:
            d = ev.data or {}
            if d.get("task_id") != task_id:
                continue
            if session_id and ev.provenance.session_id != session_id:
                continue
            ts = ev.provenance.timestamp_ms
            if since_ms is not None and ts < since_ms:
                continue
            if until_ms is not None and ts > until_ms:
                continue
            out.append(ev)

        # chronological order
        out.sort(key=lambda e: e.provenance.timestamp_ms)
        return out


# -----------------------------
# Persistence Helpers
# -----------------------------

class EpisodeStore:
    """
    Persists episodes back into M1 as structured artifacts.

    This allows:
    - replay
    - routing (M4)
    - organizational learning (M10)
    """

    def __init__(self, blackboard: Blackboard):
        self.bb = blackboard

    def persist(self, episode: Episode, provenance: Provenance) -> str:
        """
        Store an episode as a JSON artifact in M1.

        Returns:
            artifact_id
        """
        payload = {
            "episode": {
                "episode_id": episode.episode_id,
                "task_id": episode.task_id,
                "participants": episode.participants,
                "started_ms": episode.started_ms,
                "ended_ms": episode.ended_ms,
                "duration_ms": episode.duration_ms(),
                "timeline": [asdict(e) for e in episode.timeline],
                "outcomes": episode.outcomes,
                "notes": episode.notes,
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
            text=f"episode persisted task_id={episode.task_id}",
            data={"episode_id": episode.episode_id, "artifact_id": art_id},
            artifact_id=art_id,
        )

        return art_id
