# Backend — Personalized Learning Platform

## Setup

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file from the example:
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
# Set FIREBASE_CREDENTIALS_PATH to your service account JSON
```

### Firebase Setup
1. Create a Firebase project at https://console.firebase.google.com
2. Enable Authentication and your preferred sign-in providers (e.g., Google, Email/Password)
3. Download the service account key JSON from Project Settings → Service Accounts
4. Set `FIREBASE_CREDENTIALS_PATH` in `.env` to the path of that JSON file

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.  
Interactive docs at `http://localhost:8000/docs`.

---

## Authentication

All endpoints except `/health` require a Firebase ID token in the `Authorization` header:

```
Authorization: Bearer <firebase-id-token>
```

The frontend obtains this token after the user signs in with Firebase Auth (client SDK). The backend verifies it using `firebase-admin`.

---

## API Endpoints

### Health Check
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Returns `{"status": "ok"}` (no auth required) |

### Profile
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/profile` | Create a user profile |
| `GET` | `/api/profile/me` | Get current user's profile |

**POST /api/profile** — Request body:
```json
{
  "name": "Alice",
  "experience_level": "beginner",
  "learning_goal": "Learn Python for data analysis"
}
```

### Assessment
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/assess` | Send a message in the assessment chat |
| `GET` | `/api/assess/status` | Get assessment status and turn count |

**POST /api/assess** — Request body:
```json
{
  "message": "I've used Excel for basic data work but never Python"
}
```

Response includes `status` (`in_progress` or `completed`), `reply`, `turn_number`, and optionally `user_context` when assessment completes.

### Curriculum
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/curriculum` | Generate curriculum (requires completed assessment) |
| `GET` | `/api/curriculum` | Get the generated curriculum |

The curriculum response contains ordered steps, each with `title`, `overview`, `resources`, `is_unlocked`, and `is_completed`.

### Quiz
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/quiz/step/{step_id}` | Generate a quiz for a step |
| `POST` | `/api/quiz/step/{step_id}/submit` | Submit quiz answers |

**POST /api/quiz/step/{step_id}/submit** — Request body:
```json
{
  "quiz_id": "<quiz-uuid>",
  "answers": [0, 2, 1]
}
```

Response includes `score`, `passed` (bool), and `revision_hint` (string, only on failure).

---

## Architecture

- **FastAPI** — HTTP API layer
- **Firebase Auth** — Authentication via ID token verification (firebase-admin SDK)
- **Google ADK** — Agent orchestration (Assessment, Curriculum, Quiz agents)
- **SQLite** — Persistence via SQLAlchemy
- **Gemini 3** — LLM model for all AI interactions
