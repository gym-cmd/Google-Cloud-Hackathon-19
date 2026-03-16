from pydantic import BaseModel


class QuestionResponse(BaseModel):
    question: str
    options: list[str]


class QuizResponse(BaseModel):
    id: str
    step_id: str
    questions: list[QuestionResponse]


class QuizSubmit(BaseModel):
    quiz_id: str
    answers: list[int]  # index of selected option per question


class QuizResult(BaseModel):
    quiz_id: str
    score: float
    passed: bool
    revision_hint: str | None = None
