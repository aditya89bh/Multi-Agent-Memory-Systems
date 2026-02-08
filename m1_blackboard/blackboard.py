from __future__ import annotations

import json
import math
import os
import time
import uuid
import threading
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class EventType(str, Enum):
    """
    Canonical event types stored in the shared event log.
    """
    OBSERVATION = "observation"
    MESSAGE = "message"
    DECISION = "decision"
    ACTION = "action"
    OUTCOME = "outcome"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    NOTE = "note"


@dataclass(frozen=True)
class Provenance:
    """
    Attribution metadata attached to every event and artifact.
    """
    agent_id: str
    role: str = "unknown"
    session_id: str = "default"
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    confidence: float = 1.0
    source: str = "runtime"
    tags: Tuple[str, ...] = tuple()


@dataclass(frozen=True)
class MemoryEvent:
    """
    A single entry in the append-only event log.
    """
    event_id: str
    event_type: EventType
    provenance: Provenance
    text: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    artifact_id: Optional[str] = None


@dataclass(frozen=True)
class Artifact:
    """
    Immutable memory object stored in the artifact store.
    """
    artifact_id: str
    provenance: Provenance
    kind: str
    payload: Dict[str, Any]
    created_ms: int = field(default_factory=lambda: int(time.time() * 1000))


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


def _safe_json(obj: Any) -> Any:
    if isinstance(obj, Enum):
        return obj.value
    if hasattr(obj, "__dataclass_fields__"):
        return _safe_json(asdict(obj))
    if isinstance(obj, dict):
        return {str(k): _safe_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_json(x) for x in obj]
    return obj


@dataclass
class VectorItem:
    artifact_id: str
    provenance: Provenance
    embedding: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


class SimpleVectorIndex:
    """
    Minimal in-memory vector index using cosine similarity.
    """

    def __init__(self):
        self._items: List[VectorItem] = []
        self._lock = threading.Lock()

    def add(self, item: VectorItem) -> None:
        with self._lock:
            self._items.append(item)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_tags: Optional[List[str]] = None,
        filter_agent_ids: Optional[List[str]] = None,
        min_score: float = 0.0,
    ) -> List[Tuple[float, VectorItem]]:
        filter_tags = filter_tags or []
        filter_agent_ids = filter_agent_ids or []

        scored: List[Tuple[float, VectorItem]] = []
        with self._lock:
            for item in self._items:
                if filter_agent_ids and item.provenance.agent_id not in filter_agent_ids:
                    continue
                if filter_tags:
                    item_tags = set(item.provenance.tags or ())
                    if not set(filter_tags).issubset(item_tags):
                        continue

                s = _cosine(query_embedding, item.embedding)
                if s >= min_score:
                    scored.append((s, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored[: max(1, top_k)]


class Blackboard:
    """
    Shared Memory Bus for multi-agent systems.

    Provides:
    - append-only event log
    - artifact store
    - optional embedding similarity search
    - optional JSONL persistence
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self._events: List[MemoryEvent] = []
        self._artifacts: Dict[str, Artifact] = {}
        self._vector = SimpleVectorIndex()
        self._lock = threading.Lock()

        self.persist_dir = persist_dir
        if self.persist_dir:
            os.makedirs(self.persist_dir, exist_ok=True)
            self._events_path = os.path.join(self.persist_dir, "events.jsonl")
            self._artifacts_path = os.path.join(self.persist_dir, "artifacts.jsonl")
            self._load_from_disk()
        else:
            self._events_path = None
            self._artifacts_path = None

    def _append_jsonl(self, path: Optional[str], obj: Any) -> None:
        if not path:
            return
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(_safe_json(obj), ensure_ascii=False) + "\n")

    def _load_from_disk(self) -> None:
        if self._events_path and os.path.exists(self._events_path):
            with open(self._events_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        prov = Provenance(**obj["provenance"])
                        self._events.append(
                            MemoryEvent(
                                event_id=obj["event_id"],
                                event_type=EventType(obj["event_type"]),
                                provenance=prov,
                                text=obj.get("text", ""),
                                data=obj.get("data", {}),
                                artifact_id=obj.get("artifact_id"),
                            )
                        )
                    except Exception:
                        continue

        if self._artifacts_path and os.path.exists(self._artifacts_path):
            with open(self._artifacts_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                        prov = Provenance(**obj["provenance"])
                        art = Artifact(
                            artifact_id=obj["artifact_id"],
                            provenance=prov,
                            kind=obj["kind"],
                            payload=obj["payload"],
                            created_ms=obj["created_ms"],
                        )
                        self._artifacts[art.artifact_id] = art
                        if art.kind == "embedding" and "embedding" in art.payload:
                            self._vector.add(
                                VectorItem(
                                    artifact_id=art.artifact_id,
                                    provenance=art.provenance,
                                    embedding=list(art.payload["embedding"]),
                                    metadata=art.payload.get("metadata", {}),
                                )
                            )
                    except Exception:
                        continue

    def put_artifact(
        self,
        provenance: Provenance,
        kind: str,
        payload: Dict[str, Any],
        *,
        index_if_embedding: bool = True,
    ) -> str:
        art_id = _new_id("art")
        art = Artifact(art_id, provenance, kind, payload)
        with self._lock:
            self._artifacts[art_id] = art
            self._append_jsonl(self._artifacts_path, art)
            if index_if_embedding and kind == "embedding" and "embedding" in payload:
                self._vector.add(
                    VectorItem(
                        artifact_id=art_id,
                        provenance=provenance,
                        embedding=list(payload["embedding"]),
                        metadata=payload.get("metadata", {}),
                    )
                )
        return art_id

    def post_event(
        self,
        event_type: EventType,
        provenance: Provenance,
        text: str = "",
        data: Optional[Dict[str, Any]] = None,
        artifact_id: Optional[str] = None,
    ) -> str:
        ev_id = _new_id("ev")
        ev = MemoryEvent(ev_id, event_type, provenance, text, data or {}, artifact_id)
        with self._lock:
            self._events.append(ev)
            self._append_jsonl(self._events_path, ev)
        return ev_id

    def query_events(self, limit: int = 50) -> List[MemoryEvent]:
        with self._lock:
            return list(self._events[-limit:])

    def search_embeddings(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Tuple[float, Artifact]]:
        results = self._vector.search(query_embedding, top_k=top_k)
        with self._lock:
            return [
                (score, self._artifacts[item.artifact_id])
                for score, item in results
                if item.artifact_id in self._artifacts
            ]
