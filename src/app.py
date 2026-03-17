from contextlib import asynccontextmanager
import importlib
from pathlib import Path
from typing import AsyncGenerator
import json
import sys
import uuid
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Resolve paths relative to this file (src/)
BASE_DIR = Path(__file__).resolve().parent

# Ensure src/ is on the Python path so learning_agent is importable
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load environment variables
load_dotenv(BASE_DIR / "learning_agent" / ".env")

adk_app = importlib.import_module("learning_agent.agent_engine_app").adk_app

# In-memory session store: user_id -> session_id
_sessions: dict[str, str] = {}


def _get_user_id(request: Request) -> str:
    """Return a stable user id from a cookie, or generate one."""
    return request.cookies.get("eduai_uid", "")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="EduAI Studio UI", lifespan=lifespan)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/chat", status_code=302)


@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/context", response_class=HTMLResponse)
async def context_view(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})


@app.get("/roadmap", response_class=HTMLResponse)
async def roadmap(request: Request):
    return templates.TemplateResponse("roadmap.html", {"request": request})


@app.get("/resources", response_class=HTMLResponse)
async def resources(request: Request):
    return templates.TemplateResponse("resources.html", {"request": request})


@app.get("/code", response_class=HTMLResponse)
async def code_lab(request: Request):
    return templates.TemplateResponse("code.html", {"request": request})


@app.get("/quiz", response_class=HTMLResponse)
async def quiz(request: Request):
    return templates.TemplateResponse("quiz.html", {"request": request})


@app.get("/quiz-results", response_class=HTMLResponse)
async def quiz_results(request: Request):
    return templates.TemplateResponse(
        "quiz_results.html",
        {"request": request},
    )


class ChatMessage(BaseModel):
    message: str


@app.post("/api/chat")
async def chat_api(request: Request, chat_msg: ChatMessage):
    user_id = _get_user_id(request) or str(uuid.uuid4())
    # Lazily create a session for this user
    if user_id not in _sessions:
        session = await adk_app.async_create_session(user_id=user_id)
        _sessions[user_id] = session.id

    session_id = _sessions[user_id]

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            async for event in adk_app.async_stream_query(
                user_id=user_id,
                session_id=session_id,
                message=chat_msg.message,
            ):
                if isinstance(event, dict):
                    yield f"data: {json.dumps(event)}\n\n"
                elif hasattr(event, "model_dump_json"):
                    yield f"data: {event.model_dump_json()}\n\n"
                else:
                    yield f"data: {json.dumps({'text': str(event)})}\n\n"
        except Exception as e:
            # Yield error event explicitly so client sees what happened
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            yield f"data: {json.dumps({'text': error_msg, 'error': True})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    response = StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
    )
    # Set a cookie so the same browser gets the same session
    if not _get_user_id(request):
        response.set_cookie(
            "eduai_uid",
            user_id,
            httponly=True,
            samesite="lax",
        )
    return response


@app.post("/api/new-profile")
async def new_profile(request: Request):
    """Clear session and cookie to start fresh."""
    user_id = _get_user_id(request)
    if user_id and user_id in _sessions:
        del _sessions[user_id]
    response = JSONResponse({"status": "ok"})
    response.delete_cookie("eduai_uid")
    return response


@app.post("/api/reset-progression")
async def reset_progression(request: Request):
    """Reset learning progression by clearing the session."""
    user_id = _get_user_id(request)
    if user_id and user_id in _sessions:
        del _sessions[user_id]
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
