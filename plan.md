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

frontend/
├── public/
│   ├── index.html
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── Profile/              # Spec 01: User Profile & Interests Setup
│   │   ├── Assessment/           # Spec 01: AI Tutor Chat Interface
│   │   ├── Curriculum/           # Spec 02: Personalized Curriculum Roadmap
│   │   ├── Resources/            # Spec 02: Learning Module Resources
│   │   ├── Quiz/                 # Spec 03: Interactive Knowledge Quiz
│   │   └── Results/              # Spec 03: Quiz Results & Feedback
│   ├── pages/
│   │   ├── Home.jsx
│   │   ├── Onboarding.jsx
│   │   ├── Dashboard.jsx
│   │   ├── Learning.jsx
│   │   └── NotFound.jsx
│   ├── services/
│   │   └── api.js                # API client for backend endpoints
│   ├── hooks/
│   │   └── useAuth.js            # Firebase Auth integration
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── package.json
├── vite.config.js                # Build config (Vite recommended)
├── .env.example
└── README.md

UI-mockups/
├── user_profile_interests_setup/        # Spec 01: Profile creation
├── ai_tutor_chat_interface/             # Spec 01: Assessment chat
├── personalized_curriculum_roadmap/     # Spec 02: Curriculum display
├── learning_module_resources/           # Spec 02: Resource viewing
├── interactive_knowledge_quiz/          # Spec 03: Quiz interface
└── quiz_results_feedback/               # Spec 03: Results & feedback
```

### UI Mockups — Created in Stitch
All UI mockups have been created using **Stitch** and are available in the `UI-mockups/` directory. Each mockup includes:
- `screen.png` — Visual design screenshot
- `code.html` — Interactive prototype/reference HTML code

| Mockup | Spec | Purpose |
|---|---|---|
| **User Profile & Interests Setup** | 01 | Initial onboarding: name, level, learning goal |
| **AI Tutor Chat Interface** | 01 | Multi-turn assessment conversation with the Assessment Agent |
| **Personalized Curriculum Roadmap** | 02 | Display of generated 4–6 step curriculum with progress tracking |
| **Learning Module Resources** | 02 | Resource cards: articles, videos, documentation for each step |
| **Interactive Knowledge Quiz** | 03 | MCQ quiz presentation with answer selection |
| **Quiz Results & Feedback** | 03 | Score display, pass/fail indication, and revision hints |

**Implementation Plan:**
- Phase 1: Build profile creation and assessment chat UI based on Spec 01 mockups
- Phase 2: Build curriculum roadmap and resources UI based on Spec 02 mockups
- Phase 3: Build quiz and results UI based on Spec 03 mockups
- Post-launch: Consider Stitch designs as reference for responsive frontend framework (React/Vue)

## Implementation Phases

### Phase 1 — Spec 01: User Profile & Assessment
**Backend:**
- Profile CRUD (create, read)
- Assessment Agent with 3–5 turn conversation
- User context extraction and persistence

**Frontend:**
- Build Profile component (name, level, goal selection)
- Build Assessment chat interface (message display, input, bot responses)
- Firebase Auth integration (login, signup, ID token handling)
- Navigation/routing setup

### Phase 2 — Spec 02: Curriculum Generation & Content
**Backend:**
- Curriculum Agent with structured JSON output
- Web Fetcher tool for resource curation
- Step locking/unlocking logic

**Frontend:**
- Build Curriculum component (step list, progress tracking)
- Build Resources component (resource cards, links, descriptions)
- Step navigation and conditional rendering based on lock status
- Dashboard layout to tie Phase 1 & 2 together

### Phase 3 — Spec 03: Quiz & Adaptive Progression
**Backend:**
- Quiz Agent with MCQ generation
- Answer evaluation and scoring
- Revision hint generation on failure
- Step progression on pass

**Frontend:**
- Build Quiz component (MCQ presentation, answer selection, submission)
- Build Results component (score display, pass/fail indication, hints)
- Quiz flow integration with curriculum progression
- Learning dashboard updates on step completion

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
