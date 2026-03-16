from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.curriculum import Step
from app.models.quiz import Quiz
from app.schemas.quiz import QuizResponse, QuizResult, QuizSubmit
from app.services.quiz_service import generate_quiz, submit_quiz

router = APIRouter()


@router.post("/step/{step_id}", response_model=QuizResponse, status_code=201)
async def create_quiz(
    step_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    step = db.query(Step).filter(Step.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    if not step.is_unlocked:
        raise HTTPException(status_code=400, detail="Step is locked")

    quiz = await generate_quiz(db, step)
    # Strip correct_index from response (don't leak answers to frontend)
    questions_safe = [
        {"question": q["question"], "options": q["options"]}
        for q in quiz.questions
    ]
    return QuizResponse(id=quiz.id, step_id=quiz.step_id, questions=questions_safe)


@router.post("/step/{step_id}/submit", response_model=QuizResult)
async def submit_quiz_answers(
    step_id: str,
    submission: QuizSubmit,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    quiz = db.query(Quiz).filter(Quiz.id == submission.quiz_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    if quiz.step_id != step_id:
        raise HTTPException(status_code=400, detail="Quiz does not belong to this step")
    if quiz.passed is not None:
        raise HTTPException(status_code=400, detail="Quiz already submitted")

    result = await submit_quiz(db, quiz, submission.answers, current_user["uid"])
    return result
