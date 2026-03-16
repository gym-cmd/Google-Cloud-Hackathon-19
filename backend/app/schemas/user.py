from typing import Literal

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    name: str
    experience_level: Literal["beginner", "intermediate", "advanced"]
    learning_goal: str


class UserContext(BaseModel):
    name: str
    experience_level: str
    learning_goal: str
    key_prior_knowledge: list[str]
    confirmed_focus: str


class ProfileResponse(BaseModel):
    id: str
    email: str | None = None
    name: str
    experience_level: str
    learning_goal: str
    assessment_status: str
    user_context: UserContext | None = None

    model_config = {"from_attributes": True}


class AssessmentMessage(BaseModel):
    message: str


class AssessmentResponse(BaseModel):
    reply: str
    status: str  # "in_progress" | "completed"
    turn_number: int
    user_context: UserContext | None = None


class AssessmentStatus(BaseModel):
    status: str
    turn_number: int
