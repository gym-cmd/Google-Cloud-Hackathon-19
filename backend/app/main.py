from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth import init_firebase
from app.database import init_db
from app.routers import assessment, curriculum, profile, quiz


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_firebase()
    init_db()
    yield


app = FastAPI(
    title="Personalized Learning Platform",
    description="AI-powered software development tutor using Google ADK",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile.router, prefix="/api/profile", tags=["Profile"])
app.include_router(assessment.router, prefix="/api/assess", tags=["Assessment"])
app.include_router(curriculum.router, prefix="/api/curriculum", tags=["Curriculum"])
app.include_router(quiz.router, prefix="/api/quiz", tags=["Quiz"])


@app.get("/health")
async def health():
    return {"status": "ok"}
