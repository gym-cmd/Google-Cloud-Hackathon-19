from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.schemas.curriculum import CurriculumResponse
from app.services.curriculum_service import generate_curriculum, get_curriculum
from app.services.user_service import get_user

router = APIRouter()


@router.post("", response_model=CurriculumResponse, status_code=201)
async def create_curriculum(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["uid"]
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.assessment_status != "completed":
        raise HTTPException(
            status_code=400, detail="Assessment must be completed before generating curriculum"
        )
    existing = get_curriculum(db, user_id)
    if existing:
        raise HTTPException(status_code=400, detail="Curriculum already exists for this user")

    curriculum = await generate_curriculum(db, user)
    return curriculum


@router.get("", response_model=CurriculumResponse)
def read_curriculum(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    curriculum = get_curriculum(db, current_user["uid"])
    if not curriculum:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    return curriculum
