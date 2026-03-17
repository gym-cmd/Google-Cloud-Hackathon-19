from contextlib import asynccontextmanager
import asyncio
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import AsyncGenerator
import json
import sys
import uuid
from dotenv import load_dotenv

import vertexai
from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Resolve paths relative to this file (src/)
BASE_DIR = Path(__file__).resolve().parent

# Ensure src/ is on the Python path so learning_agent is importable
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Load environment variables
load_dotenv(BASE_DIR / "learning_agent" / ".env")

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")
AGENT_ENGINE_RESOURCE_ID = "6536033677174898688"

client = vertexai.Client(
    project=PROJECT,
    location=LOCATION,
)
adk_app = client.agent_engines.get(
    name=f"projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{AGENT_ENGINE_RESOURCE_ID}"
)
# In-memory session store: user_id -> session_id
_sessions: dict[str, str] = {}
# In-memory quiz answer store: user_id -> list of correct_index values
_quiz_answers: dict[str, list[int]] = {}
STRUCTURED_STATE_KEYS = ("assessment_complete", "steps", "questions", "resources", "score")


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


def _extract_all_content_text(content) -> str:
    """Like _extract_content_text but also reads function_response results."""
    if not content:
        return ""

    parts = _read_event_field(content, "parts") or []
    text_parts: list[str] = []
    for part in parts:
        text = _read_event_field(part, "text")
        if isinstance(text, str) and text.strip():
            text_parts.append(text)
        func_resp = _read_event_field(part, "function_response")
        if func_resp:
            response = _read_event_field(func_resp, "response")
            result = _read_event_field(response, "result")
            if isinstance(result, str) and result.strip():
                text_parts.append(result)
            elif isinstance(result, dict):
                text_parts.append(json.dumps(result))

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


async def _stream_with_timeout(
    stream,
    timeout: float = 30.0,
):
    """Wrap an async generator with a per-iteration idle timeout.

    If no event arrives within *timeout* seconds, the stream ends
    gracefully instead of hanging forever.
    """
    ait = stream.__aiter__()
    while True:
        try:
            event = await asyncio.wait_for(
                ait.__anext__(),
                timeout=timeout,
            )
            yield event
        except StopAsyncIteration:
            return
        except asyncio.TimeoutError:
            return


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

# Serve static assets (JS, CSS, images)
static_dir = BASE_DIR / "static"
if static_dir.is_dir():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


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
        _sessions[user_id] = session["id"] if isinstance(session, dict) else session.id

    session_id = _sessions[user_id]

    async def event_stream() -> AsyncGenerator[str, None]:
        accumulated_text = ""
        emitted_states: set[str] = set()
        try:
            async for event in _stream_with_timeout(
                adk_app.async_stream_query(
                    user_id=user_id,
                    session_id=session_id,
                    message=chat_msg.message,
                ),
                timeout=30.0,
            ):
                # Check hidden events (sub-agent tool responses that
                # _extract_event_text would skip) for structured state.
                if not _is_visible_chat_event(event):
                    hidden_text = _extract_all_content_text(
                        _read_event_field(event, "content")
                    )
                    if hidden_text:
                        hidden_state = _parse_structured_state(hidden_text)
                        if hidden_state:
                            state_key = json.dumps(
                                hidden_state, sort_keys=True,
                            )
                            if state_key not in emitted_states:
                                emitted_states.add(state_key)
                                hidden_payload: dict[str, object] = {
                                    "state": hidden_state,
                                }
                                fb = _fallback_text_for_state(hidden_state)
                                if fb and not accumulated_text:
                                    hidden_payload["text"] = fb
                                    accumulated_text = fb
                                yield (
                                    f"data: {json.dumps(hidden_payload)}\n\n"
                                )

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


# ---------------------------------------------------------------------------
# New dedicated API endpoints
# ---------------------------------------------------------------------------

class CurriculumRequest(BaseModel):
    user_context: dict


class ResourcesRequest(BaseModel):
    topic: str
    step_title: str


class QuizGenerateRequest(BaseModel):
    step_title: str
    step_overview: str


class QuizEvaluateRequest(BaseModel):
    questions: list[dict]
    answers: list[int]


_CODE_MAX_LENGTH = 10_000
_CODE_TIMEOUT_SECONDS = 5
_OUTPUT_MAX_BYTES = 50_000
_ALLOWED_LANGUAGES = {"python", "javascript"}
_LANGUAGE_COMMANDS: dict[str, list[str]] = {
    "python": ["python3", "-c"],
    "javascript": ["node", "-e"],
}


class CodeExecuteRequest(BaseModel):
    language: str
    code: str


async def _collect_agent_response(
    user_id: str,
    message: str,
) -> tuple[str, dict | None, str]:
    """Send a message to the agent and collect the full response.

    Returns (visible_text, parsed_structured_state_or_None, raw_text).
    """
    if user_id not in _sessions:
        session = await adk_app.async_create_session(user_id=user_id)
        _sessions[user_id] = session["id"] if isinstance(session, dict) else session.id

    session_id = _sessions[user_id]
    accumulated_text = ""
    raw_text = ""
    last_state: dict | None = None

    async for event in _stream_with_timeout(
        adk_app.async_stream_query(
            user_id=user_id,
            session_id=session_id,
            message=message,
        ),
        timeout=30.0,
    ):
        # Scan hidden events (sub-agent responses) for structured state
        if not _is_visible_chat_event(event):
            hidden_text = _extract_all_content_text(
                _read_event_field(event, "content")
            )
            if hidden_text:
                hidden_state = _parse_structured_state(hidden_text)
                if hidden_state:
                    last_state = hidden_state
                raw_text += hidden_text

        text = _extract_event_text(event)
        if text:
            raw_text += text
            state = _parse_structured_state(text)
            if state:
                last_state = state
            visible = _remove_structured_state_text(text)
            _, accumulated_text = _compute_text_delta(visible, accumulated_text)

    return accumulated_text, last_state, raw_text


def _ensure_user_id(request: Request) -> str:
    uid = _get_user_id(request)
    return uid if uid else str(uuid.uuid4())


@app.post("/api/curriculum/generate")
async def generate_curriculum(request: Request, body: CurriculumRequest):
    """Ask the curriculum agent to generate a learning path."""
    user_id = _ensure_user_id(request)
    prompt = (
        "Generate a curriculum for this learner. "
        f"User context: {json.dumps(body.user_context)}"
    )
    try:
        _, state, raw = await _collect_agent_response(user_id, prompt)
        if state and isinstance(state.get("steps"), list):
            return JSONResponse({"steps": state["steps"]})
        parsed = _try_parse_json_from_text(raw, "steps")
        if parsed and isinstance(parsed.get("steps"), list):
            return JSONResponse({"steps": parsed["steps"]})
        return JSONResponse(
            {"error": "Agent did not return a structured curriculum."},
            status_code=502,
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/resources")
async def get_resources(request: Request, body: ResourcesRequest):
    """Ask the agent for curated resources on a topic/step."""
    user_id = _ensure_user_id(request)
    prompt = (
        f"Suggest 3-5 learning resources for the following learning step.\n"
        f"Step title: {body.step_title}\n"
        f"Topic: {body.topic}\n"
        "Respond ONLY with a JSON block: "
        '{"resources": [{"title": "...", "url": "...", "description": "..."}]}'
    )
    try:
        full_text, state, raw = await _collect_agent_response(
            user_id, prompt,
        )
        if state and isinstance(state.get("resources"), list):
            return JSONResponse({"resources": state["resources"]})
        # Try parsing raw text as JSON if state parser didn't catch it
        parsed = _try_parse_json_from_text(
            raw or full_text, "resources",
        )
        if parsed:
            return JSONResponse(parsed)
        return JSONResponse(
            {"error": "Agent did not return structured resources."},
            status_code=502,
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/quiz/generate")
async def generate_quiz(request: Request, body: QuizGenerateRequest):
    """Ask the quiz agent to generate 3 MCQs for a step."""
    user_id = _ensure_user_id(request)
    prompt = (
        "Generate a quiz for this learning step.\n"
        f"Step title: {body.step_title}\n"
        f"Step overview: {body.step_overview}\n"
    )
    try:
        full_text, state, raw = await _collect_agent_response(
            user_id, prompt,
        )
        questions = None
        if state and isinstance(state.get("questions"), list):
            questions = state["questions"]
        else:
            parsed = _try_parse_json_from_text(
                raw or full_text, "questions",
            )
            if parsed and isinstance(parsed.get("questions"), list):
                questions = parsed["questions"]

        if questions:
            # Store correct answers server-side for deterministic scoring
            _quiz_answers[user_id] = [
                q.get("correct_index", 0) for q in questions
            ]
            # Strip correct_index before sending to client
            client_questions = [
                {"question": q.get("question", ""), "options": q.get("options", [])}
                for q in questions
            ]
            return JSONResponse({"questions": client_questions})
        return JSONResponse(
            {"error": "Agent did not return quiz questions."},
            status_code=502,
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.post("/api/quiz/evaluate")
async def evaluate_quiz(request: Request, body: QuizEvaluateRequest):
    """Score quiz answers deterministically using stored correct indices."""
    user_id = _ensure_user_id(request)
    total = len(body.questions)
    if total == 0:
        return JSONResponse({"error": "No questions provided."}, status_code=400)

    correct_indices = _quiz_answers.get(user_id)
    if not correct_indices or len(correct_indices) != total:
        return JSONResponse(
            {"error": "Quiz session expired. Please regenerate the quiz."},
            status_code=400,
        )

    score = 0
    wrong_questions: list[str] = []
    for i, q in enumerate(body.questions):
        user_answer = body.answers[i] if i < len(body.answers) else -1
        if user_answer == correct_indices[i]:
            score += 1
        else:
            wrong_questions.append(q.get("question", f"Question {i + 1}"))

    passed = score >= 2  # 2/3 threshold per spec
    result: dict = {
        "score": score,
        "total": total,
        "passed": passed,
        "feedback": (
            f"You got {score} out of {total} correct. "
            + ("Great job! You can move on to the next step."
               if passed else "Review the material and try again.")
        ),
    }

    # Generate revision hint via agent if failed
    if not passed and wrong_questions:
        try:
            hint_prompt = (
                "The user failed a quiz. They got these questions wrong:\n"
                + "\n".join(f"- {q}" for q in wrong_questions)
                + "\nProvide a 1-2 sentence revision hint targeting "
                "their weakest area. Respond with ONLY the hint text."
            )
            hint_text, _, _ = await _collect_agent_response(
                user_id, hint_prompt,
            )
            if hint_text and hint_text.strip():
                result["revision_hint"] = hint_text.strip()
        except Exception:
            pass
        if "revision_hint" not in result:
            result["revision_hint"] = (
                "Review the material focusing on the questions you "
                "missed, then try the quiz again."
            )

    return JSONResponse(result)


@app.post("/api/code/execute")
async def execute_code(request: Request, body: CodeExecuteRequest):
    """Execute user code in a sandboxed subprocess."""
    lang = body.language.lower().strip()
    if lang not in _ALLOWED_LANGUAGES:
        return JSONResponse(
            {"error": f"Unsupported language: {lang}. "
             f"Allowed: {', '.join(sorted(_ALLOWED_LANGUAGES))}"},
            status_code=400,
        )
    if len(body.code) > _CODE_MAX_LENGTH:
        return JSONResponse(
            {"error": f"Code too long. Max {_CODE_MAX_LENGTH} characters."},
            status_code=400,
        )
    if not body.code.strip():
        return JSONResponse(
            {"stdout": "", "stderr": "", "exit_code": 0, "timed_out": False},
        )

    cmd = _LANGUAGE_COMMANDS[lang]

    try:
        result = await asyncio.to_thread(
            _run_sandboxed, cmd, body.code,
        )
        return JSONResponse(result)
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


def _run_sandboxed(cmd: list[str], code: str) -> dict:
    """Run code in a subprocess with strict limits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": tmpdir,
            "TMPDIR": tmpdir,
            "LANG": "en_US.UTF-8",
        }
        try:
            proc = subprocess.run(
                [*cmd, code],
                capture_output=True,
                timeout=_CODE_TIMEOUT_SECONDS,
                cwd=tmpdir,
                env=env,
                text=True,
            )
            return {
                "stdout": proc.stdout[:_OUTPUT_MAX_BYTES],
                "stderr": proc.stderr[:_OUTPUT_MAX_BYTES],
                "exit_code": proc.returncode,
                "timed_out": False,
            }
        except subprocess.TimeoutExpired:
            return {
                "stdout": "",
                "stderr": "Execution timed out (5 second limit).",
                "exit_code": 1,
                "timed_out": True,
            }


def _try_parse_json_from_text(text: str, required_key: str) -> dict | None:
    """Attempt to extract a JSON object containing required_key from text."""
    if not text:
        return None
    # Try fenced JSON block
    match = re.search(r"```json\s*([\s\S]*?)```", text, re.IGNORECASE)
    if match:
        try:
            parsed = json.loads(match.group(1).strip())
            if required_key in parsed:
                return parsed
        except json.JSONDecodeError:
            pass
    # Try bare JSON
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            parsed = json.loads(stripped)
            if required_key in parsed:
                return parsed
        except json.JSONDecodeError:
            pass
    return None


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
