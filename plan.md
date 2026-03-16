# Project Plan — Personalized Learning Platform

## Tech Stack
- **Runtime**: Python 3.11
- **API Framework**: FastAPI
- **AI/Agent Framework**: Google ADK (Agent Development Kit)
- **Model**: Gemini 3
- **Database**: SQLite (upgrade path to Firestore/CloudSQL later)
- **Authentication**: Firebase Auth (ID token verification via firebase-admin SDK)
- **Deployment**: Local dev (deployment target TBD)

## Architecture

### Agents (3 max)
| Agent | Responsibility |
|---|---|
| **Assessment Agent** | Drives the 3–5 turn onboarding chat to clarify the user's goal, surface prior knowledge, and produce a structured user context object |
| **Curriculum Agent** | Takes the user context and generates a 4–6 step structured curriculum with resources |
| **Quiz Agent** | Generates 3 MCQ questions per step, evaluates answers, and produces revision hints on failure |

### Tools
| Tool | Description |
|---|---|
| **Web Fetcher** | Fetches and extracts content from webpages relevant to the user's learning topic, used by the Curriculum Agent to provide curated resources |

### API Design (REST)
All endpoints except `/health` require a Firebase ID token in the `Authorization: Bearer <token>` header.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/profile` | Create user profile (name, level, goal) |
| `GET` | `/api/profile/me` | Get current user's profile |
| `POST` | `/api/assess` | Send a message in the assessment chat; returns AI response |
| `GET` | `/api/assess/status` | Get assessment status (in-progress / completed) |
| `POST` | `/api/curriculum` | Generate curriculum from completed assessment |
| `GET` | `/api/curriculum` | Get the generated curriculum |
| `POST` | `/api/quiz/step/{step_id}` | Generate quiz for a curriculum step |
| `POST` | `/api/quiz/step/{step_id}/submit` | Submit quiz answers; returns score + pass/fail + hint |

### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, CORS, lifespan
│   ├── auth.py                 # Firebase token verification dependency
│   ├── config.py               # Settings via pydantic-settings
│   ├── database.py             # SQLite engine + session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User + UserContext tables
│   │   ├── curriculum.py       # Curriculum + Step tables
│   │   └── quiz.py             # Quiz + QuizAttempt tables
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py             # Request/response schemas
│   │   ├── curriculum.py
│   │   └── quiz.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── profile.py
│   │   ├── assessment.py
│   │   ├── curriculum.py
│   │   └── quiz.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── assessment_agent.py
│   │   ├── curriculum_agent.py
│   │   └── quiz_agent.py
│   ├── tools/
│   │   ├── __init__.py
│   │   └── web_fetcher.py
│   └── services/
│       ├── __init__.py
│       ├── user_service.py
│       ├── curriculum_service.py
│       └── quiz_service.py
├── requirements.txt
├── .env.example
└── README.md
```

## Implementation Phases

### Phase 1 — Spec 01: User Profile & Assessment
- Profile CRUD (create, read)
- Assessment Agent with 3–5 turn conversation
- User context extraction and persistence

### Phase 2 — Spec 02: Curriculum Generation & Content
- Curriculum Agent with structured JSON output
- Web Fetcher tool for resource curation
- Step locking/unlocking logic

### Phase 3 — Spec 03: Quiz & Adaptive Progression
- Quiz Agent with MCQ generation
- Answer evaluation and scoring
- Revision hint generation on failure
- Step progression on pass

## Future Work
- [x] **Authentication & accounts** — Firebase Auth with ID token verification
- [ ] **Deployment** — Cloud Run / GKE containerized deployment
- [ ] **Database migration** — SQLite → Firestore or Cloud SQL
- [ ] **Progress persistence** — survive page refreshes / server restarts (partially covered by SQLite)
- [ ] **Profile editing/deletion**
- [ ] **Multiple concurrent learning goals**
- [ ] **Quiz attempt history tracking**
- [ ] **Spaced repetition scheduling**
- [ ] **Mobile-responsive frontend**
