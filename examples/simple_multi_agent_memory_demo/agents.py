from memory_store import add_episode, update_coordination


class ResearchAgent:
    def run(self):
        finding = "Users prefer concise technical summaries"

        add_episode(
            "research_agent",
            "Collected user communication preference",
            finding
        )

        update_coordination(
            "research_phase",
            "complete",
            "research_agent"
        )

        return finding


class PlannerAgent:
    def run(self, research):
        plan = f"Generate concise outreach strategy using insight: {research}"

        add_episode(
            "planner_agent",
            "Created outreach strategy",
            plan
        )

        update_coordination(
            "planning_phase",
            "complete",
            "planner_agent"
        )

        return plan


class CriticAgent:
    def run(self, plan):
        critique = "Plan approved. Maintain concise tone and avoid aggressive language."

        add_episode(
            "critic_agent",
            "Reviewed outreach strategy",
            critique
        )

        update_coordination(
            "review_phase",
            "complete",
            "critic_agent"
        )

        return critique
