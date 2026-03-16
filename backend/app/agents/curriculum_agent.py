from google.adk.agents import Agent

from app.config import settings
from app.tools.web_fetcher import fetch_webpage_content

CURRICULUM_SYSTEM_PROMPT = """You are an expert curriculum designer for a software development tutoring platform.

Given the user context below, generate a structured learning curriculum.

User Context:
- Name: {name}
- Experience Level: {experience_level}
- Learning Goal: {learning_goal}
- Prior Knowledge: {prior_knowledge}
- Confirmed Focus: {confirmed_focus}

Requirements:
- Generate 4–6 ordered learning steps
- Each step must have a title and a one-paragraph overview
- For each step, suggest 2–3 curated resources (articles, videos, or documentation)
- Use the fetch_webpage_content tool to verify that resource URLs are real and accessible
- Tailor difficulty to the user's experience level

You MUST respond with valid JSON in this exact format:
```json
{{
  "steps": [
    {{
      "order": 1,
      "title": "Step title",
      "overview": "One paragraph overview of what this step covers and why.",
      "resources": [
        {{
          "title": "Resource title",
          "url": "https://example.com/resource",
          "description": "One-line description of the resource."
        }}
      ]
    }}
  ]
}}
```

Respond ONLY with the JSON block, no additional text."""


def create_curriculum_agent(
    name: str,
    experience_level: str,
    learning_goal: str,
    prior_knowledge: list[str],
    confirmed_focus: str,
) -> Agent:
    """Create a curriculum generation agent configured for a specific user context."""
    return Agent(
        name="curriculum_agent",
        model=settings.gemini_model,
        instruction=CURRICULUM_SYSTEM_PROMPT.format(
            name=name,
            experience_level=experience_level,
            learning_goal=learning_goal,
            prior_knowledge=", ".join(prior_knowledge) if prior_knowledge else "None",
            confirmed_focus=confirmed_focus,
        ),
        description="Generates a structured learning curriculum with curated resources.",
        tools=[fetch_webpage_content],
    )
