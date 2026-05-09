import json
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path(__file__).parent / "sample_memory.json"


DECAY_THRESHOLD = 3


def load_memory():
    if not MEMORY_FILE.exists():
        return {
            "episodic_memory": [],
            "coordination_memory": []
        }

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def add_episode(agent, event, outcome, salience=1):
    memory = load_memory()

    memory["episodic_memory"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent,
        "event": event,
        "outcome": outcome,
        "salience": salience,
        "retrieval_count": 0
    })

    save_memory(memory)


def retrieve_relevant_memories(keyword=None):
    memory = load_memory()

    memories = memory["episodic_memory"]

    if keyword:
        memories = [
            m for m in memories
            if keyword.lower() in m["outcome"].lower()
            or keyword.lower() in m["event"].lower()
        ]

    for item in memories:
        item["retrieval_count"] += 1
        item["salience"] += 1

    save_memory(memory)

    return sorted(
        memories,
        key=lambda x: x["salience"],
        reverse=True
    )


def decay_memories():
    memory = load_memory()

    updated = []

    for item in memory["episodic_memory"]:
        item["salience"] -= 1

        if item["salience"] > 0:
            updated.append(item)

    memory["episodic_memory"] = updated

    save_memory(memory)


def update_coordination(task, status, owner):
    memory = load_memory()

    memory["coordination_memory"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "task": task,
        "status": status,
        "owner": owner
    })

    save_memory(memory)


def print_memory():
    memory = load_memory()

    print("\n=== Episodic Memory ===")
    for item in memory["episodic_memory"]:
        print(item)

    print("\n=== Coordination Memory ===")
    for item in memory["coordination_memory"]:
        print(item)
