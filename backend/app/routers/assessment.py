from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.schemas.user import AssessmentMessage, AssessmentResponse, AssessmentStatus
from app.services.user_service import get_user, run_assessment_turn

router = APIRouter()


@router.post("", response_model=AssessmentResponse)
async def assess(
    msg: AssessmentMessage,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = get_user(db, current_user["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Create a profile first.")
    if user.assessment_status == "completed":
        raise HTTPException(status_code=400, detail="Assessment already completed")

    result = await run_assessment_turn(db, user, msg.message)
    return result


@router.get("/status", response_model=AssessmentStatus)
def assessment_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = get_user(db, current_user["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    history = user.assessment_history or []
    turn_number = len([m for m in history if m["role"] == "user"])
    return AssessmentStatus(status=user.assessment_status, turn_number=turn_number)
