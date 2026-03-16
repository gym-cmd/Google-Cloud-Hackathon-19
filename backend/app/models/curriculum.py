import uuid

from sqlalchemy import Boolean, Column, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Curriculum(Base):
    __tablename__ = "curricula"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)

    user = relationship("User", back_populates="curriculum")
    steps = relationship(
        "Step", back_populates="curriculum", order_by="Step.order"
    )


class Step(Base):
    __tablename__ = "steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    curriculum_id = Column(
        String, ForeignKey("curricula.id"), nullable=False
    )
    order = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    overview = Column(Text, nullable=False)
    resources = Column(JSON, default=list)  # [{title, url, description}]
    is_unlocked = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)

    curriculum = relationship("Curriculum", back_populates="steps")
