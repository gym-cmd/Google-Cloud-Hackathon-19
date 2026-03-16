import json

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from sqlalchemy.orm import Session

from app.agents.assessment_agent import create_assessment_agent
from app.models.user import User
from app.schemas.user import ProfileCreate, UserContext

# In-memory session service for ADK agent conversations
_session_service = InMemorySessionService()


def create_user(db: Session, profile: ProfileCreate, firebase_uid: str, email: str | None = None) -> User:
    user = User(
        id=firebase_uid,
        email=email,
        name=profile.name,
        experience_level=profile.experience_level,
        learning_goal=profile.learning_goal,
        assessment_status="pending",
        assessment_history=[],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


async def run_assessment_turn(db: Session, user: User, user_message: str) -> dict:
    """Run one turn of the assessment conversation."""
    history = user.assessment_history or []
    turn_number = len([m for m in history if m["role"] == "user"]) + 1

    agent = create_assessment_agent(
        name=user.name,
        experience_level=user.experience_level,
        learning_goal=user.learning_goal,
    )

    runner = Runner(
        agent=agent,
        app_name="learning_platform",
        session_service=_session_service,
    )

    # Get or create ADK session for this user
    session_id = f"assess-{user.id}"
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

    user_content = Content(
        role="user", parts=[Part(text=user_message)]
    )

    # Run the agent
    response_text = ""
    async for event in runner.run_async(
        user_id=user.id,
        session_id=session_id,
        new_message=user_content,
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    # Update history
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": response_text})

    # Check if assessment is complete (look for JSON block)
    user_context = None
    status = "in_progress"

    if "assessment_complete" in response_text and turn_number >= 3:
        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                parsed = json.loads(response_text[json_start:json_end])
                if parsed.get("assessment_complete"):
                    user_context = parsed["user_context"]
                    status = "completed"
        except (json.JSONDecodeError, KeyError):
            pass  # Not yet complete, continue conversation

    # Force completion after 5 turns
    if turn_number >= 5 and status != "completed":
        status = "completed"
        if user_context is None:
            user_context = {
                "name": user.name,
                "experience_level": user.experience_level,
                "learning_goal": user.learning_goal,
                "key_prior_knowledge": [],
                "confirmed_focus": user.learning_goal,
            }

    user.assessment_history = history
    user.assessment_status = status
    if user_context:
        user.user_context = user_context

    db.commit()
    db.refresh(user)

    return {
        "reply": response_text,
        "status": status,
        "turn_number": turn_number,
        "user_context": UserContext(**user_context) if user_context else None,
    }
