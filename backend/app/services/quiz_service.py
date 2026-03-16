import json

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from sqlalchemy.orm import Session

from app.agents.quiz_agent import create_quiz_agent, create_revision_agent
from app.models.curriculum import Step
from app.models.quiz import Quiz
from app.services.curriculum_service import get_curriculum, unlock_next_step

_session_service = InMemorySessionService()


async def generate_quiz(db: Session, step: Step) -> Quiz:
    """Generate a quiz for a curriculum step using the Quiz Agent."""
    agent = create_quiz_agent(
        step_title=step.title,
        step_overview=step.overview,
    )

    runner = Runner(
        agent=agent,
        app_name="learning_platform",
        session_service=_session_service,
    )

    session_id = f"quiz-{step.id}"
    await _session_service.create_session(
        app_name="learning_platform",
        user_id="system",
        session_id=session_id,
    )

    prompt = Content(
        role="user",
        parts=[Part(text="Generate the quiz now.")],
    )

    response_text = ""
    async for event in runner.run_async(
        user_id="system",
        session_id=session_id,
        new_message=prompt,
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    # Parse JSON
    json_start = response_text.find("{")
    json_end = response_text.rfind("}") + 1
    if json_start == -1 or json_end <= json_start:
        raise ValueError("Failed to parse quiz JSON from agent response")

    data = json.loads(response_text[json_start:json_end])

    quiz = Quiz(
        step_id=step.id,
        questions=data["questions"],
    )
    db.add(quiz)
    db.commit()
    db.refresh(quiz)
    return quiz


async def submit_quiz(
    db: Session, quiz: Quiz, answers: list[int], user_id: str
) -> dict:
    """Evaluate quiz answers and handle pass/fail logic."""
    questions = quiz.questions
    correct_count = 0
    wrong_questions = []

    for i, q in enumerate(questions):
        if i < len(answers) and answers[i] == q["correct_index"]:
            correct_count += 1
        else:
            wrong_questions.append(q["question"])

    score = correct_count / len(questions)
    passed = score >= 2 / 3  # pass threshold: 2/3 correct

    revision_hint = None
    if not passed and wrong_questions:
        step = db.query(Step).filter(Step.id == quiz.step_id).first()
        revision_hint = await _generate_revision_hint(
            step.title, step.overview, wrong_questions
        )

    # Update quiz record
    quiz.score = score
    quiz.passed = passed
    quiz.revision_hint = revision_hint

    # If passed, unlock next step
    if passed:
        step = db.query(Step).filter(Step.id == quiz.step_id).first()
        curriculum = get_curriculum(db, user_id)
        if curriculum:
            unlock_next_step(db, curriculum, step.order)

    db.commit()
    db.refresh(quiz)

    return {
        "quiz_id": quiz.id,
        "score": score,
        "passed": passed,
        "revision_hint": revision_hint,
    }


async def _generate_revision_hint(
    step_title: str, step_overview: str, wrong_questions: list[str]
) -> str:
    """Generate a revision hint for wrong answers."""
    agent = create_revision_agent(
        step_title=step_title,
        step_overview=step_overview,
        wrong_questions="\n".join(f"- {q}" for q in wrong_questions),
    )

    runner = Runner(
        agent=agent,
        app_name="learning_platform",
        session_service=_session_service,
    )

    session_id = "revision-hint"
    await _session_service.create_session(
        app_name="learning_platform",
        user_id="system",
        session_id=session_id,
    )

    prompt = Content(
        role="user",
        parts=[Part(text="Generate the revision hint.")],
    )

    response_text = ""
    async for event in runner.run_async(
        user_id="system",
        session_id=session_id,
        new_message=prompt,
    ):
        if event.is_final_response():
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    return response_text.strip()
