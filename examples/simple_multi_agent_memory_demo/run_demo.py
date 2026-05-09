from agents import ResearchAgent, PlannerAgent, CriticAgent
from memory_store import print_memory


def main():
    print("\n=== Multi-Agent Memory Demo ===")

    researcher = ResearchAgent()
    planner = PlannerAgent()
    critic = CriticAgent()

    research = researcher.run()
    print(f"\n[Research Agent]\n{research}")

    plan = planner.run(research)
    print(f"\n[Planner Agent]\n{plan}")

    review = critic.run(plan)
    print(f"\n[Critic Agent]\n{review}")

    print_memory()


if __name__ == "__main__":
    main()
