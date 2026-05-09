import json
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path(__file__).parent / "sample_memory.json"


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


def add_episode(agent, event, outcome):
    memory = load_memory()

    memory["episodic_memory"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent,
        "event": event,
        "outcome": outcome
    })

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
