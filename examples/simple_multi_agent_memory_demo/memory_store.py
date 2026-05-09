import json
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path(__file__).parent / "sample_memory.json"


def load_memory():
    if not MEMORY_FILE.exists():
        return {
            "shared_memory": {
                "episodic_memory": [],
                "coordination_memory": [],
                "event_memory": []
            },
            "private_memory": {
                "research_agent": [],
                "planner_agent": [],
                "critic_agent": []
            }
        }

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def add_event(event_type, payload):
    memory = load_memory()

    memory["shared_memory"]["event_memory"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "payload": payload
    })

    save_memory(memory)


def add_episode(agent, event, outcome, salience=1, private=False):
    memory = load_memory()

    memory_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent,
        "event": event,
        "outcome": outcome,
        "salience": salience,
        "retrieval_count": 0
    }

    if private:
        memory["private_memory"][agent].append(memory_entry)
    else:
        memory["shared_memory"]["episodic_memory"].append(memory_entry)

    save_memory(memory)


def retrieve_relevant_memories(keyword=None, agent=None):
    memory = load_memory()

    shared = memory["shared_memory"]["episodic_memory"]

    private = []
    if agent:
        private = memory["private_memory"].get(agent, [])

    memories = shared + private

    if keyword:
        memories = [
            m for m in memories
            if keyword.lower() in m["event"].lower()
            or keyword.lower() in m["outcome"].lower()
        ]

    for item in memories:
        item["retrieval_count"] += 1
        item["salience"] += 1

    save_memory(memory)

    return sorted(memories, key=lambda x: x["salience"], reverse=True)


def decay_memories():
    memory = load_memory()

    updated_shared = []

    for item in memory["shared_memory"]["episodic_memory"]:
        item["salience"] -= 1

        if item["salience"] > 0:
            updated_shared.append(item)

    memory["shared_memory"]["episodic_memory"] = updated_shared

    save_memory(memory)


def update_coordination(task, status, owner):
    memory = load_memory()

    memory["shared_memory"]["coordination_memory"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "task": task,
        "status": status,
        "owner": owner
    })

    save_memory(memory)


def print_memory():
    memory = load_memory()

    print("\n=== Shared Episodic Memory ===")
    for item in memory["shared_memory"]["episodic_memory"]:
        print(item)

    print("\n=== Coordination Memory ===")
    for item in memory["shared_memory"]["coordination_memory"]:
        print(item)

    print("\n=== Event Memory ===")
    for item in memory["shared_memory"]["event_memory"]:
        print(item)

    print("\n=== Private Memory ===")
    for agent, items in memory["private_memory"].items():
        print(f"\n[{agent}]")
        for item in items:
            print(item)
