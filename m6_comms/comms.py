from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from mam.m1_blackboard.blackboard import Blackboard, Provenance, EventType


# -----------------------------
# Core Types
# -----------------------------

def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def _now_ms() -> int:
    return int(time.time() * 1000)


class MessageIntent(str, Enum):
    """
    High-level intent tags for communication memory.
    """
    MESSAGE = "message"
    QUESTION = "question"
    ANSWER = "answer"
    REQUEST = "request"
    COMMITMENT = "commitment"
    DECISION = "decision"
    NOTE = "note"


class CommitmentStatus(str, Enum):
    OPEN = "open"
    DONE = "done"
    DROPPED = "dropped"


@dataclass(frozen=True)
class Message:
    """
    A single utterance in a thread.
    """
    message_id: str
    thread_id: str
    intent: MessageIntent
    text: str
    provenance: Provenance
    created_ms: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Question:
    """
    A question is a message that creates an open loop.
    """
    question_id: str
    thread_id: str
    text: str
    provenance: Provenance
    created_ms: int
    tags: Tuple[str, ...] = tuple()


@dataclass(frozen=True)
class Answer:
    """
    An answer resolves a question.
    """
    answer_id: str
    thread_id: str
    question_id: str
    text: str
    provenance: Provenance
    created_ms: int
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Commitment:
    """
    A commitment is an explicit promise.

    Example:
        owner: agent_A promises to deliver "draft proposal" by tomorrow
    """
    commitment_id: str
    thread_id: str
    owner_agent_id: str
    text: str
    created_ms: int
    due_ms: Optional[int] = None
    status: CommitmentStatus = CommitmentStatus.OPEN
    completion_evidence: Dict[str, Any] = field(default_factory=dict)


# -----------------------------
# Communication Memory Store
# -----------------------------

class CommunicationMemory:
    """
    Stores dialogue as structured memory objects and tracks open loops.

    Persistence strategy:
    - store all objects as JSON artifacts in M1 Blackboard
    - log summary events into M1 for easy retrieval/debug
    """

    def __init__(self, blackboard: Blackboard):
        self.bb = blackboard

        # In-memory indexes (lightweight; replay can be built later if needed)
        self._threads: Dict[str, List[str]] = {}          # thread_id -> message_ids
        self._questions: Dict[str, Question] = {}         # question_id -> Question
        self._answers: Dict[str, Answer] = {}             # answer_id -> Answer
        self._commitments: Dict[str, Commitment] = {}     # commitment_id -> Commitment
        self._question_to_answer_ids: Dict[str, List[str]] = {}  # question_id -> [answer_id]

    # -------------------------
    # Threads + Messages
    # -------------------------

    def new_thread(self, title: str = "", *, provenance: Optional[Provenance] = None) -> str:
        """
        Create a new thread.

        Args:
            title: optional human label
            provenance: optional provenance (if omitted, a synthetic one is used)

        Returns:
            thread_id
        """
        thread_id = _new_id("th")
        self._threads[thread_id] = []

        prov = provenance or Provenance(agent_id="system", role="system")
        art_id = self.bb.put_artifact(prov, kind="json", payload={"thread": {"thread_id": thread_id, "title": title}})
        self.bb.post_event(EventType.NOTE, prov, text=f"thread_created {thread_id}", data={"title": title}, artifact_id=art_id)

        return thread_id

    def post_message(
        self,
        thread_id: str,
        intent: MessageIntent,
        text: str,
        provenance: Provenance,
        *,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> Message:
        """
        Post a message into a thread and persist it.

        Returns:
            Message
        """
        if thread_id not in self._threads:
            self._threads[thread_id] = []

        msg = Message(
            message_id=_new_id("msg"),
            thread_id=thread_id,
            intent=intent,
            text=text,
            provenance=provenance,
            created_ms=_now_ms(),
            metadata=metadata or {},
        )

        art_id = self.bb.put_artifact(provenance, kind="json", payload={"message": asdict(msg)})
        self.bb.post_event(
            EventType.MESSAGE,
            provenance,
            text=f"{intent.value}: {text}",
            data={"thread_id": thread_id, "intent": intent.value, "tags": tags or []},
            artifact_id=art_id,
        )

        self._threads[thread_id].append(msg.message_id)
        return msg

    # -------------------------
    # Questions + Answers (Open Loops)
    # -------------------------

    def ask(
        self,
        thread_id: str,
        text: str,
        provenance: Provenance,
        *,
        tags: Optional[List[str]] = None,
    ) -> Question:
        """
        Create a Question (open loop) and persist it.

        Returns:
            Question
        """
        q = Question(
            question_id=_new_id("q"),
            thread_id=thread_id,
            text=text,
            provenance=provenance,
            created_ms=_now_ms(),
            tags=tuple(tags or []),
        )

        art_id = self.bb.put_artifact(provenance, kind="json", payload={"question": asdict(q)})
        self.bb.post_event(
            EventType.NOTE,
            provenance,
            text=f"question_opened: {text}",
            data={"thread_id": thread_id, "question_id": q.question_id, "tags": list(q.tags)},
            artifact_id=art_id,
        )

        self._questions[q.question_id] = q
        self._question_to_answer_ids.setdefault(q.question_id, [])
        return q

    def answer(
        self,
        thread_id: str,
        question_id: str,
        text: str,
        provenance: Provenance,
        *,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Answer:
        """
        Record an answer to a question and persist it.

        Returns:
            Answer
        """
        if question_id not in self._questions:
            raise KeyError(f"unknown question_id: {question_id}")

        a = Answer(
            answer_id=_new_id("a"),
            thread_id=thread_id,
            question_id=question_id,
            text=text,
            provenance=provenance,
            created_ms=_now_ms(),
            evidence=evidence or {},
        )

        art_id = self.bb.put_artifact(provenance, kind="json", payload={"answer": asdict(a)})
        self.bb.post_event(
            EventType.NOTE,
            provenance,
            text=f"question_answered: {question_id}",
            data={"thread_id": thread_id, "question_id": question_id, "answer_id": a.answer_id},
            artifact_id=art_id,
        )

        self._answers[a.answer_id] = a
        self._question_to_answer_ids.setdefault(question_id, []).append(a.answer_id)
        return a

    def open_questions(self) -> List[Question]:
        """
        Return all questions that do not yet have any answers.
        """
        out: List[Question] = []
        for qid, q in self._questions.items():
            answers = self._question_to_answer_ids.get(qid, [])
            if not answers:
                out.append(q)
        out.sort(key=lambda x: x.created_ms)
        return out

    # -------------------------
    # Commitments
    # -------------------------

    def commit(
        self,
        thread_id: str,
        text: str,
        provenance: Provenance,
        *,
        due_ms: Optional[int] = None,
    ) -> Commitment:
        """
        Create a commitment (promise) owned by provenance.agent_id.
        """
        c = Commitment(
            commitment_id=_new_id("c"),
            thread_id=thread_id,
            owner_agent_id=provenance.agent_id,
            text=text,
            created_ms=_now_ms(),
            due_ms=due_ms,
            status=CommitmentStatus.OPEN,
        )

        art_id = self.bb.put_artifact(provenance, kind="json", payload={"commitment": asdict(c)})
        self.bb.post_event(
            EventType.NOTE,
            provenance,
            text=f"commitment_opened: {text}",
            data={"thread_id": thread_id, "commitment_id": c.commitment_id, "due_ms": due_ms},
            artifact_id=art_id,
        )

        self._commitments[c.commitment_id] = c
        return c

    def mark_commitment_done(
        self,
        commitment_id: str,
        provenance: Provenance,
        *,
        evidence: Optional[Dict[str, Any]] = None,
    ) -> Commitment:
        """
        Mark a commitment as DONE.
        """
        if commitment_id not in self._commitments:
            raise KeyError(f"unknown commitment_id: {commitment_id}")

        c = self._commitments[commitment_id]
        c.status = CommitmentStatus.DONE
        c.completion_evidence = evidence or {}

        art_id = self.bb.put_artifact(provenance, kind="json", payload={"commitment_update": asdict(c)})
        self.bb.post_event(
            EventType.NOTE,
            provenance,
            text=f"commitment_done: {commitment_id}",
            data={"commitment_id": commitment_id},
            artifact_id=art_id,
        )

        return c

    def open_commitments(self, *, owner_agent_id: Optional[str] = None) -> List[Commitment]:
        """
        List commitments still OPEN.

        Args:
            owner_agent_id: optionally filter by owner.
        """
        out = [c for c in self._commitments.values() if c.status == CommitmentStatus.OPEN]
        if owner_agent_id:
            out = [c for c in out if c.owner_agent_id == owner_agent_id]
        out.sort(key=lambda x: x.created_ms)
        return out

    # -------------------------
    # Anti-looping helper
    # -------------------------

    def find_previous_answers(self, query_text: str, *, limit: int = 3) -> List[Answer]:
        """
        Naive anti-looping helper: returns answers whose text contains the query terms.

        Later upgrades (optional):
        - use embeddings (M1 vector index)
        - use thread-aware retrieval
        """
        q = query_text.strip().lower()
        hits: List[Answer] = []
        for a in self._answers.values():
            if q and q in (a.text or "").lower():
                hits.append(a)
        hits.sort(key=lambda x: x.created_ms, reverse=True)
        return hits[: max(1, limit)]
