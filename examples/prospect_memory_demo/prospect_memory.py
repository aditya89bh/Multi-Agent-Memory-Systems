import json
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path(__file__).parent / "prospect_memory.json"


def default_memory():
    return {
        "prospects": {},
        "events": []
    }


def load_memory():
    if not MEMORY_FILE.exists():
        return default_memory()

    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)


def get_prospect(name):
    memory = load_memory()
    return memory["prospects"].get(name, {})


def update_prospect(name, update):
    memory = load_memory()

    if name not in memory["prospects"]:
        memory["prospects"][name] = {
            "created_at": datetime.utcnow().isoformat(),
            "touches": 0,
            "notes": [],
            "angles": [],
            "messages": [],
            "next_steps": []
        }

    prospect = memory["prospects"][name]
    prospect["touches"] += 1
    prospect["updated_at"] = datetime.utcnow().isoformat()

    for key, value in update.items():
        if key in ["notes", "angles", "messages", "next_steps"]:
            prospect[key].append(value)
        else:
            prospect[key] = value

    memory["events"].append({
        "timestamp": datetime.utcnow().isoformat(),
        "prospect": name,
        "update": update
    })

    save_memory(memory)
    return prospect


def print_prospect_memory(name):
    prospect = get_prospect(name)

    print("\n=== Prospect Memory ===")

    if not prospect:
        print("No memory found for this prospect yet.")
        return

    print(f"Touches: {prospect.get('touches', 0)}")

    for section in ["notes", "angles", "messages", "next_steps"]:
        print(f"\n{section.upper()}:")
        items = prospect.get(section, [])
        if not items:
            print("- None")
        for item in items[-3:]:
            print(f"- {item}")
