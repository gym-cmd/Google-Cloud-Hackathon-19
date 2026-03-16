import uuid

from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, JSON, String, Text

from app.database import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    step_id = Column(String, ForeignKey("steps.id"), nullable=False)
    # [{question, options: [str], correct_index: int}]
    questions = Column(JSON, nullable=False)
    score = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    revision_hint = Column(Text, nullable=True)
