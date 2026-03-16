from pydantic import BaseModel


class Resource(BaseModel):
    title: str
    url: str
    description: str


class StepResponse(BaseModel):
    id: str
    order: int
    title: str
    overview: str
    resources: list[Resource]
    is_unlocked: bool
    is_completed: bool

    model_config = {"from_attributes": True}


class CurriculumResponse(BaseModel):
    id: str
    user_id: str
    steps: list[StepResponse]

    model_config = {"from_attributes": True}
