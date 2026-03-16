from contextlib import asynccontextmanager
from typing import AsyncGenerator
import json
import os
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Load environment variables
load_dotenv("src/learning_agent/.env")

# Try to import the local agent app
from src.learning_agent.agent_engine_app import adk_app

app = FastAPI(title="EduAI Studio UI")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="src/static"), name="static")
templates = Jinja2Templates(directory="src/templates")

# Mock user id for now
USER_ID = "user-123"
SESSION_ID = None

@app.on_event("startup")
async def startup_event():
    global SESSION_ID
    # Create a session on startup
    session = await adk_app.async_create_session(user_id=USER_ID)
    SESSION_ID = session.id
    print(f"Created session: {SESSION_ID}")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@app.get("/roadmap", response_class=HTMLResponse)
async def roadmap(request: Request):
    return templates.TemplateResponse("roadmap.html", {"request": request})

@app.get("/resources", response_class=HTMLResponse)
async def resources(request: Request):
    return templates.TemplateResponse("resources.html", {"request": request})

@app.get("/quiz", response_class=HTMLResponse)
async def quiz(request: Request):
    return templates.TemplateResponse("quiz.html", {"request": request})

@app.get("/quiz-results", response_class=HTMLResponse)
async def quiz_results(request: Request):
    return templates.TemplateResponse("quiz_results.html", {"request": request})

class ChatMessage(BaseModel):
    message: str

@app.post("/api/chat")
async def chat_api(chat_msg: ChatMessage):
    async def event_stream() -> AsyncGenerator[str, None]:
        async for event in adk_app.async_stream_query(
            user_id=USER_ID,
            session_id=SESSION_ID,
            message=chat_msg.message,
        ):
            # Parse the event depending on what AdkApp yields
            # It usually yields a dict or an object with text
            if isinstance(event, dict):
                yield f"data: {json.dumps(event)}\n\n"
            elif hasattr(event, "model_dump_json"):
                yield f"data: {event.model_dump_json()}\n\n"
            else:
                yield f"data: {json.dumps({'text': str(event)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
