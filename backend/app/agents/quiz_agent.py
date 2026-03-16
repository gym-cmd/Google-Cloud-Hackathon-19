from google.adk.agents import Agent

from app.config import settings

QUIZ_GENERATION_PROMPT = """You are a quiz generator for a software development tutoring platform.

Generate a short quiz to assess the user's understanding of the following learning step.

Step Title: {step_title}
Step Overview: {step_overview}

Requirements:
- Generate exactly 3 multiple-choice questions
- Each question must have exactly 4 options
- Exactly one option per question must be correct
- Questions should test comprehension, not memorization
- Vary difficulty: one easy, one medium, one slightly challenging

You MUST respond with valid JSON in this exact format:
```json
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_index": 0
    }}
  ]
}}
```

Respond ONLY with the JSON block, no additional text."""


REVISION_HINT_PROMPT = """You are a helpful tutor. The user just failed a quiz on the following topic.

Step Title: {step_title}
Step Overview: {step_overview}

The user got the following questions wrong:
{wrong_questions}

Generate a short revision hint (1–2 sentences) that targets the user's weakest area and helps them understand what to revisit.

Respond with plain text only, no JSON."""


def create_quiz_agent(step_title: str, step_overview: str) -> Agent:
    """Create a quiz generation agent for a specific curriculum step."""
    return Agent(
        name="quiz_agent",
        model=settings.gemini_model,
        instruction=QUIZ_GENERATION_PROMPT.format(
            step_title=step_title,
            step_overview=step_overview,
        ),
        description="Generates multiple-choice quiz questions for a learning step.",
    )


def create_revision_agent(
    step_title: str, step_overview: str, wrong_questions: str
) -> Agent:
    """Create an agent that generates revision hints for failed quiz attempts."""
    return Agent(
        name="revision_agent",
        model=settings.gemini_model,
        instruction=REVISION_HINT_PROMPT.format(
            step_title=step_title,
            step_overview=step_overview,
            wrong_questions=wrong_questions,
        ),
        description="Generates revision hints for failed quiz questions.",
    )
