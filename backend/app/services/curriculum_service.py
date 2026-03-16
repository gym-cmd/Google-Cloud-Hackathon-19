import json

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from sqlalchemy.orm import Session

from app.agents.curriculum_agent import create_curriculum_agent
from app.models.curriculum import Curriculum, Step
from app.models.user import User

_session_service = InMemorySessionService()


async def generate_curriculum(db: Session, user: User) -> Curriculum:
    """Generate a curriculum using the Curriculum Agent."""
    ctx = user.user_context
    agent = create_curriculum_agent(
        name=ctx["name"],
        experience_level=ctx["experience_level"],
        learning_goal=ctx["learning_goal"],
        prior_knowledge=ctx.get("key_prior_knowledge", []),
        confirmed_focus=ctx["confirmed_focus"],
    )

    runner = Runner(
        agent=agent,
        app_name="learning_platform",
        session_service=_session_service,
    )

    session_id = f"curriculum-{user.id}"
    session = await _session_service.get_session(
        app_name="learning_platform",
        user_id=user.id,
        session_id=session_id,
    )
    if session is None:
        session = await _session_service.create_session(
            app_name="learning_platform",
            user_id=user.id,
            session_id=session_id,
        )

    prompt = Content(
        role="user",
        parts=[Part(text="Generate the curriculum now.")],
    )

    response_text = ""
    async for event in runner.run_async(
        user_id=user.id,
        session_id=session_id,
        new_message=prompt,
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    # Parse JSON from response
    json_start = response_text.find("{")
    json_end = response_text.rfind("}") + 1
    if json_start == -1 or json_end <= json_start:
        raise ValueError("Failed to parse curriculum JSON from agent response")

    data = json.loads(response_text[json_start:json_end])

    # Persist curriculum and steps
    curriculum = Curriculum(user_id=user.id)
    db.add(curriculum)
    db.flush()

    for step_data in data["steps"]:
        step = Step(
            curriculum_id=curriculum.id,
            order=step_data["order"],
            title=step_data["title"],
            overview=step_data["overview"],
            resources=step_data.get("resources", []),
            is_unlocked=(step_data["order"] == 1),  # first step unlocked
            is_completed=False,
        )
        db.add(step)

    db.commit()
    db.refresh(curriculum)
    return curriculum


def get_curriculum(db: Session, user_id: str) -> Curriculum | None:
    return db.query(Curriculum).filter(Curriculum.user_id == user_id).first()


def unlock_next_step(db: Session, curriculum: Curriculum, completed_step_order: int):
    """Unlock the next step after the current one is completed."""
    for step in curriculum.steps:
        if step.order == completed_step_order:
            step.is_completed = True
        if step.order == completed_step_order + 1:
            step.is_unlocked = True
    db.commit()
