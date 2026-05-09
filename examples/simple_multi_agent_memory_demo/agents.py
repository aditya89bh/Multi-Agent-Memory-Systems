from memory_store import (
    add_episode,
    update_coordination,
    retrieve_relevant_memories
)


class ResearchAgent:
    def run(self):
        finding = "Users prefer concise technical summaries"

        add_episode(
            "research_agent",
            "Collected user communication preference",
            finding,
            salience=2
        )

        update_coordination(
            "research_phase",
            "complete",
            "research_agent"
        )

        return finding


class PlannerAgent:
    def run(self, research):
        previous_memories = retrieve_relevant_memories("concise")

        if previous_memories:
            memory_hint = previous_memories[0]["outcome"]
        else:
            memory_hint = "No previous preference memory found"

        plan = (
            f"Generate concise outreach strategy using insight: {research}. "
            f"Retrieved memory: {memory_hint}"
        )

        add_episode(
            "planner_agent",
            "Created outreach strategy",
            plan,
            salience=3
        )

        update_coordination(
            "planning_phase",
            "complete",
            "planner_agent"
        )

        return plan


class CriticAgent:
    def run(self, plan):
        critique = (
            "Plan approved. Maintain concise tone and avoid aggressive language."
        )

        add_episode(
            "critic_agent",
            "Reviewed outreach strategy",
            critique,
            salience=2
        )

        update_coordination(
            "review_phase",
            "complete",
            "critic_agent"
        )

        return critique
