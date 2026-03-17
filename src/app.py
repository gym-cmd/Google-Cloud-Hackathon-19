from contextlib import asynccontextmanager
import importlib
import re
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
STRUCTURED_STATE_KEYS = ("assessment_complete", "steps", "questions")


def _get_user_id(request: Request) -> str:
    """Return a stable user id from a cookie, or generate one."""
    return request.cookies.get("eduai_uid", "")


def _read_event_field(value, field: str):
    if value is None:
        return None
    if isinstance(value, dict):
        return value.get(field)
    return getattr(value, field, None)


def _get_event_label(event) -> str | None:
    labels = _read_event_field(event, "logging.googleapis.com/labels")
    if isinstance(labels, dict):
        label = labels.get("event.name")
        if isinstance(label, str):
            return label
    return None


def _extract_content_text(content) -> str:
    if not content:
        return ""

    parts = _read_event_field(content, "parts") or []
    text_parts: list[str] = []
    for part in parts:
        text = _read_event_field(part, "text")
        if isinstance(text, str) and text.strip():
            text_parts.append(text)

    return "".join(text_parts)


def _parse_structured_state(text: str) -> dict | None:
    if not text:
        return None

    candidates: list[str] = []
    fenced_match = re.search(
        r"```json\s*([\s\S]*?)```",
        text,
        re.IGNORECASE,
    )
    if fenced_match:
        candidates.append(fenced_match.group(1).strip())

    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        candidates.append(stripped)

    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if any(key in parsed for key in STRUCTURED_STATE_KEYS):
            return parsed

    return None


def _remove_structured_state_text(text: str) -> str:
    if not text:
        return ""

    cleaned_text = re.sub(
        r"```json\s*[\s\S]*?```",
        "",
        text,
        flags=re.IGNORECASE,
    ).strip()
    parsed = _parse_structured_state(cleaned_text)
    if parsed and cleaned_text.startswith("{") and cleaned_text.endswith("}"):
        return ""
    return cleaned_text.strip()


def _fallback_text_for_state(state: dict) -> str:
    if state.get("assessment_complete"):
        return (
            "I have enough information to create a focused "
            "learning path for you."
        )
    if isinstance(state.get("steps"), list):
        return (
            "I created a personalized curriculum for you. "
            "Open the roadmap or resources to continue."
        )
    if isinstance(state.get("questions"), list):
        return (
            "I generated a knowledge check for your current "
            "step. Open the quiz to begin."
        )
    return ""


def _is_visible_chat_event(event) -> bool:
    event_label = _get_event_label(event)
    if event_label in {"gen_ai.system.message", "gen_ai.user.message"}:
        return False

    content = _read_event_field(event, "content")
    role = _read_event_field(content, "role")
    if role == "user":
        return False

    author = _read_event_field(event, "author")
    if author == "user":
        return False

    return True


def _compute_text_delta(
    next_text: str,
    accumulated_text: str,
) -> tuple[str, str]:
    cleaned_text = next_text.strip()
    if not cleaned_text:
        return "", accumulated_text

    if not accumulated_text:
        return cleaned_text, cleaned_text

    if cleaned_text == accumulated_text:
        return "", accumulated_text

    if cleaned_text.startswith(accumulated_text):
        return cleaned_text[len(accumulated_text):], cleaned_text

    if accumulated_text.startswith(cleaned_text):
        return "", accumulated_text

    separator = "\n\n" if not accumulated_text.endswith("\n") else "\n"
    merged_text = f"{accumulated_text}{separator}{cleaned_text}"
    return f"{separator}{cleaned_text}", merged_text


def _extract_event_text(event) -> str:
    if (
        isinstance(event, dict)
        and event.get("error")
        and isinstance(event.get("text"), str)
    ):
        return event["text"]

    if not _is_visible_chat_event(event):
        return ""

    content_text = _extract_content_text(_read_event_field(event, "content"))
    if content_text.strip():
        return content_text

    raw_text = _read_event_field(event, "text")
    if isinstance(raw_text, str) and raw_text.strip():
        return raw_text

    error_message = _read_event_field(event, "error_message")
    if isinstance(error_message, str) and error_message.strip():
        return f"Sorry, I encountered an error: {error_message}"

    actions = _read_event_field(event, "actions")
    if _read_event_field(actions, "transfer_to_agent"):
        return ""

    return ""


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
        accumulated_text = ""
        emitted_states: set[str] = set()
        try:
            async for event in adk_app.async_stream_query(
                user_id=user_id,
                session_id=session_id,
                message=chat_msg.message,
            ):
                text = _extract_event_text(event)
                if text:
                    state = _parse_structured_state(text)
                    visible_text = _remove_structured_state_text(text)
                    delta_text, accumulated_text = _compute_text_delta(
                        visible_text,
                        accumulated_text,
                    )
                    payload: dict[str, object] = {}
                    if delta_text:
                        payload["text"] = delta_text

                    if state:
                        state_key = json.dumps(state, sort_keys=True)
                        if state_key not in emitted_states:
                            emitted_states.add(state_key)
                            payload["state"] = state

                    if not payload and state and not accumulated_text:
                        fallback_text = _fallback_text_for_state(state)
                        if fallback_text:
                            payload["text"] = fallback_text
                            accumulated_text = fallback_text

                    if payload:
                        yield f"data: {json.dumps(payload)}\n\n"
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
