from datetime import datetime
from memory_store import load_memory, save_memory


def add_memory_edge(source, target, relationship):
    memory = load_memory()

    if "graph_memory" not in memory["shared_memory"]:
        memory["shared_memory"]["graph_memory"] = []

    edge = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": source,
        "target": target,
        "relationship": relationship
    }

    memory["shared_memory"]["graph_memory"].append(edge)
    save_memory(memory)

    return edge


def get_memory_graph():
    memory = load_memory()
    return memory["shared_memory"].get("graph_memory", [])


def print_memory_graph():
    graph = get_memory_graph()

    print("\n=== Graph Memory Relationships ===")

    if not graph:
        print("No graph relationships found.")
        return

    for edge in graph:
        print(
            f"{edge['source']} --[{edge['relationship']}]--> {edge['target']}"
        )
