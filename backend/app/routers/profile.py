from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.schemas.user import ProfileCreate, ProfileResponse
from app.services.user_service import create_user, get_user

router = APIRouter()


@router.post("", response_model=ProfileResponse, status_code=201)
def create_profile(
    profile: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    existing = get_user(db, current_user["uid"])
    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")
    user = create_user(
        db, profile,
        firebase_uid=current_user["uid"],
        email=current_user.get("email"),
    )
    return user


@router.get("/me", response_model=ProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = get_user(db, current_user["uid"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
