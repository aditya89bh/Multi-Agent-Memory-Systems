import sys

from agents import (
    ProspectResearchAgent,
    OutreachPlannerAgent,
    MessageCriticAgent,
    FollowUpAgent
)

from prospect_memory import print_prospect_memory


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python run_prospect_demo.py <prospect_name> <goal>"
        )
        return

    prospect_name = sys.argv[1]
    goal = sys.argv[2]

    researcher = ProspectResearchAgent()
    planner = OutreachPlannerAgent()
    critic = MessageCriticAgent()
    followup = FollowUpAgent()

    print("\n=== Prospect Memory Demo ===")

    research = researcher.run(prospect_name, goal)
    print(f"\n[Research Agent]\n{research}")

    angle = planner.run(prospect_name)
    print(f"\n[Outreach Planner]\n{angle}")

    message, critique = critic.run(prospect_name, angle)

    print(f"\n[Generated Message]\n{message}")
    print(f"\n[Critique]\n{critique}")

    next_step = followup.run(prospect_name)
    print(f"\n[Next Step]\n{next_step}")

    print_prospect_memory(prospect_name)


if __name__ == "__main__":
    main()
