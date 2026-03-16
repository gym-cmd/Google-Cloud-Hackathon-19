import uuid
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from pydantic import BaseModel

from .agent import assessment_agent

load_dotenv()

APP_NAME = "learning_platform"
_session_service = InMemorySessionService()
_runner = Runner(
    agent=assessment_agent,
    app_name=APP_NAME,
    session_service=_session_service,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Learning Platform", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ---------- request / response models ----------


class ProfileRequest(BaseModel):
    name: str
    level: str  # beginner / intermediate / advanced
    goal: str


class ProfileResponse(BaseModel):
    session_id: str
    message: str


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    assessment_complete: bool
    user_context: dict | None = None


# ---------- routes ----------


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/profile", response_model=ProfileResponse)
async def create_profile(profile: ProfileRequest):
    """Create a session from the profile form and start the assessment."""
    session_id = str(uuid.uuid4())

    await _session_service.create_session(
        app_name=APP_NAME,
        user_id=session_id,
        session_id=session_id,
        state={
            "profile": profile.model_dump(),
            "assessment_complete": False,
        },
    )

    # Kick off the assessment with the profile details as the first message.
    initial_text = (
        f"Profile submitted — "
        f"Name: {profile.name}, "
        f"Experience level: {profile.level}, "
        f"Learning goal: {profile.goal}. "
        "Please begin the assessment."
    )
    content = Content(role="user", parts=[Part.from_text(text=initial_text)])

    response_text = await _run_agent(session_id, content)
    return ProfileResponse(session_id=session_id, message=response_text)


@app.post("/api/chat/{session_id}", response_model=ChatResponse)
async def chat(session_id: str, request: ChatRequest):
    """Send a user message and get the next agent response."""
    session = await _session_service.get_session(
        app_name=APP_NAME, user_id=session_id, session_id=session_id
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    content = Content(role="user", parts=[Part.from_text(text=request.message)])
    response_text = await _run_agent(session_id, content)

    # Re-fetch session so we see any state written by tools.
    session = await _session_service.get_session(
        app_name=APP_NAME, user_id=session_id, session_id=session_id
    )
    complete = session.state.get("assessment_complete", False)
    user_context = session.state.get("user_context") if complete else None

    return ChatResponse(
        message=response_text,
        assessment_complete=complete,
        user_context=user_context,
    )


@app.get("/api/context/{session_id}")
async def get_context(session_id: str):
    """Return the saved user context once the assessment is complete."""
    session = await _session_service.get_session(
        app_name=APP_NAME, user_id=session_id, session_id=session_id
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    user_context = session.state.get("user_context")
    if not user_context:
        raise HTTPException(status_code=404, detail="Assessment not complete yet")

    return user_context


# ---------- helpers ----------


async def _run_agent(session_id: str, content: Content) -> str:
    response_text = ""
    async for event in _runner.run_async(
        user_id=session_id,
        session_id=session_id,
        new_message=content,
    ):
        if event.is_final_response() and event.content and event.content.parts:
            response_text = event.content.parts[0].text
    return response_text


def start():
    uvicorn.run("learning_platform.main:app", host="0.0.0.0", port=8000, reload=True)
