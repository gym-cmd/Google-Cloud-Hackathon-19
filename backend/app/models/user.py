from sqlalchemy import JSON, Column, Enum, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # Firebase UID
    email = Column(String, nullable=True)
    name = Column(String, nullable=False)
    experience_level = Column(
        Enum("beginner", "intermediate", "advanced", name="experience_level"),
        nullable=False,
    )
    learning_goal = Column(Text, nullable=False)

    # Filled after assessment completes
    assessment_status = Column(
        Enum("pending", "in_progress", "completed", name="assessment_status"),
        default="pending",
    )
    # Stores the chat history as a list of {role, content} dicts
    assessment_history = Column(JSON, default=list)
    # Structured context extracted after assessment completes
    user_context = Column(JSON, nullable=True)

    curriculum = relationship("Curriculum", back_populates="user", uselist=False)
