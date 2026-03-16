from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext

ASSESSMENT_INSTRUCTION = """You are a learning advisor conducting a brief onboarding assessment.

The user has submitted a profile form with their name, experience level, and learning goal.
Your job is to have a SHORT conversation (3–5 turns total) to:
1. Ask one focused clarifying question about their goal
2. Understand their existing knowledge relevant to the goal
3. Confirm a specific learning focus

Rules:
- Ask only ONE question per turn
- Keep responses concise (2–3 sentences max)
- After 3–5 turns, call save_user_context to finalise the assessment
- Never ask more than 4 follow-up questions

When calling save_user_context, synthesise everything you learned:
- name: from the profile form
- level: from the profile form (beginner / intermediate / advanced)
- goal: a refined, specific version of their stated goal
- key_knowledge: list of relevant things they already know (empty list if none mentioned)
- confirmed_focus: one clear, actionable sentence describing exactly what they will learn
"""


def save_user_context(
    name: str,
    level: str,
    goal: str,
    key_knowledge: list[str],
    confirmed_focus: str,
    tool_context: ToolContext,
) -> str:
    """Finalise the assessment by saving the structured user context.

    Call this after 3-5 conversation turns when you have enough information
    to define a clear learning focus.

    Args:
        name: User's name from the profile form.
        level: Experience level — beginner, intermediate, or advanced.
        goal: Refined, specific version of the user's learning goal.
        key_knowledge: List of relevant things the user already knows.
        confirmed_focus: One clear sentence describing exactly what they will learn.
        tool_context: Injected by ADK — do not pass manually.
    """
    tool_context.state["user_context"] = {
        "name": name,
        "level": level,
        "goal": goal,
        "key_knowledge": key_knowledge,
        "confirmed_focus": confirmed_focus,
    }
    tool_context.state["assessment_complete"] = True
    return f"Assessment complete. Confirmed learning focus: {confirmed_focus}"


assessment_agent = LlmAgent(
    name="assessment_agent",
    model="gemini-2.5-flash",
    instruction=ASSESSMENT_INSTRUCTION,
    tools=[save_user_context],
)
