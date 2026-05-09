from datetime import datetime
from memory_store import load_memory, save_memory


class Arbitrator:
    def detect_conflict(self, memory_a, memory_b):
        return memory_a["outcome"] != memory_b["outcome"]

    def resolve_conflict(self, memory_a, memory_b):
        chosen = memory_a

        if memory_b["salience"] > memory_a["salience"]:
            chosen = memory_b

        memory = load_memory()

        conflict_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "memory_a": memory_a,
            "memory_b": memory_b
        }

        arbitration_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "chosen_memory": chosen,
            "reason": "Higher salience selected"
        }

        memory["shared_memory"]["conflict_memory"].append(conflict_record)
        memory["shared_memory"]["arbitration_memory"].append(arbitration_record)

        save_memory(memory)

        return chosen
