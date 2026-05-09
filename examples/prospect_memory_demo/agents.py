from prospect_memory import update_prospect, get_prospect


class ProspectResearchAgent:
    def run(self, name, goal):
        note = (
            f"{name} may be relevant for {goal}. "
            f"Focus on applied AI and robotics outcomes."
        )

        update_prospect(name, {"notes": note})

        return note


class OutreachPlannerAgent:
    def run(self, name):
        memory = get_prospect(name)

        previous_angles = memory.get("angles", [])

        if previous_angles:
            angle = previous_angles[-1]
        else:
            angle = (
                "Pitch practical AI workshop using Orangewood deployments "
                "and real-world robotics experience."
            )

        update_prospect(name, {"angles": angle})

        return angle


class MessageCriticAgent:
    def run(self, name, angle):
        message = (
            f"Hi, I work on applied AI and robotics systems at Orangewood. "
            f"I think {name} students could benefit from practical workshops "
            f"around AI agents, memory systems, and robotics workflows."
        )

        critique = (
            "Keep the message concise and outcome-oriented. "
            "Avoid generic AI buzzwords."
        )

        update_prospect(name, {"messages": message})
        update_prospect(name, {"notes": critique})

        return message, critique


class FollowUpAgent:
    def run(self, name):
        next_step = (
            "Find dean, HoD, or innovation lead and prepare personalized outreach."
        )

        update_prospect(name, {"next_steps": next_step})

        return next_step
