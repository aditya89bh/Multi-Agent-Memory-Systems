from memory_store import load_memory
from graph_memory import print_memory_graph


class MemoryVisualizer:
    def __init__(self):
        self.memory = load_memory()

    def print_summary(self):
        shared = self.memory["shared_memory"]

        print("\n=== Memory System Summary ===")
        print(
            f"Episodic memories: {len(shared.get('episodic_memory', []))}"
        )
        print(
            f"Coordination states: {len(shared.get('coordination_memory', []))}"
        )
        print(
            f"Events: {len(shared.get('event_memory', []))}"
        )
        print(
            f"Conflicts: {len(shared.get('conflict_memory', []))}"
        )
        print(
            f"Arbitrations: {len(shared.get('arbitration_memory', []))}"
        )

        graph_edges = shared.get('graph_memory', [])
        print(f"Graph relationships: {len(graph_edges)}")

    def print_private_memory_summary(self):
        print("\n=== Private Memory Summary ===")

        private = self.memory["private_memory"]

        for agent, memories in private.items():
            print(f"{agent}: {len(memories)} memories")

    def visualize(self):
        self.print_summary()
        self.print_private_memory_summary()
        print_memory_graph()


if __name__ == "__main__":
    visualizer = MemoryVisualizer()
    visualizer.visualize()
