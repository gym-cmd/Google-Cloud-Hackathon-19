# EduAI Studio — Personalized Learning Tutor

An AI-powered software development tutor built with [Google ADK](https://google.github.io/adk-docs/) (Agent Development Kit) and served through a FastAPI + Jinja2 web interface. A root agent orchestrates three specialized sub-agents to deliver a guided learning experience through conversational AI.

## How It Works

```
Browser ←→ FastAPI (src/app.py) ←→ AdkApp ←→ learning_tutor (root)
                                                    │
                                                    ├── assessment_agent
                                                    ├── curriculum_agent
                                                    └── quiz_agent
```

1. **Profile & Assessment** — The root agent greets the user, collects their name/level/goal, then hands off to `assessment_agent` for a 3–5 turn diagnostic conversation. The assessment produces a structured JSON context.
2. **Curriculum Generation** — `curriculum_agent` uses that context to build a 4–6 step curriculum with curated resources.
3. **Quiz & Progression** — When the user finishes a step, `quiz_agent` generates 3 MCQs. Pass (≥ 2/3) → next step. Fail → revision hints + retry.

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 – 3.13 |
| [uv](https://docs.astral.sh/uv/) | latest |
| [gcloud CLI](https://cloud.google.com/sdk/docs/install) | latest |
| GCP project with Vertex AI API enabled | — |

## Quick Start

### 1. Clone and install dependencies

```bash
git clone <repo-url> && cd Google-Cloud-Hackathon-19
uv sync
```

### 2. Authenticate with GCP

```bash
gcloud auth login
gcloud auth application-default login
```

### 3. Configure environment

Copy the example `.env` and fill in your project ID:

```bash
cp src/learning_agent/.env.example src/learning_agent/.env
```

Edit `src/learning_agent/.env`:

```dotenv
GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
GOOGLE_CLOUD_LOCATION="europe-west1"
GOOGLE_GENAI_USE_VERTEXAI="True"
```

### 4. Run the web UI

```bash
uv run python src/app.py
```

Open **http://localhost:8000** in your browser. This serves the EduAI Studio dashboard with all pages (chat, roadmap, quiz, profile, resources).

### 5. (Alternative) Run the ADK dev UI

For agent debugging without the custom frontend:

```bash
uv run adk web src
```

Opens the ADK built-in interface at `http://localhost:8000/dev-ui/`. Select **learning_agent** from the agent dropdown.

## Running Tests

```bash
uv run pytest tests/ -v
```

All tests run without additional configuration — `conftest.py` handles the Python path.

## Project Structure

```
.
├── pyproject.toml                          # Dependencies and project metadata
├── uv.lock                                 # Pinned dependency lockfile
├── tests/                                  # Unit tests (78 total)
│   ├── conftest.py                         # Pytest path configuration
│   ├── test_agent.py                       # Agent definition tests (27 tests)
│   ├── test_agent_engine_app.py            # Engine wrapper tests (2 tests)
│   ├── test_app.py                         # FastAPI app & template tests (43 tests)
│   └── test_main.py                        # CLI client tests (6 tests)
├── specs/                                  # Feature specifications
│   ├── 01-user-profile-and-assessment.md
│   ├── 02-curriculum-generation-and-content.md
│   └── 03-quiz-and-adaptive-progression.md
├── bugs.md                                 # Known issues tracker
├── PROGRESS.md                             # Development progress tracker
└── src/
    ├── app.py                              # FastAPI web server (serves the UI)
    ├── main.py                             # CLI client for deployed Agent Engine
    ├── static/                             # Static assets (reserved for future use)
    ├── templates/                          # Jinja2 HTML templates
    │   ├── dashboard.html                  # Landing page (/)
    │   ├── chat.html                       # AI tutor chat (/chat)
    │   ├── profile.html                    # User profile (/profile)
    │   ├── roadmap.html                    # Curriculum roadmap (/roadmap)
    │   ├── resources.html                  # Learning resources (/resources)
    │   ├── quiz.html                       # Quiz interface (/quiz)
    │   └── quiz_results.html               # Quiz results (/quiz-results)
    └── learning_agent/
        ├── __init__.py
        ├── .env                            # GCP config (gitignored — copy .env.example)
        ├── .env.example                    # Template for .env
        ├── agent.py                        # Agent definitions (root + 3 sub-agents)
        ├── agent_engine_app.py             # Vertex AI AdkApp wrapper
        └── tools/                          # Reserved for future agent tools
```

## Key Files

| File | Purpose |
|---|---|
| [src/app.py](src/app.py) | FastAPI server. Serves all HTML pages and the `/api/chat` SSE endpoint. Per-user cookie-based sessions, created lazily on first chat message. |
| [src/learning_agent/agent.py](src/learning_agent/agent.py) | Defines the root `learning_tutor` agent and its three sub-agents (`assessment_agent`, `curriculum_agent`, `quiz_agent`). All prompts, model config (`gemini-2.5-flash`), and orchestration logic. |
| [src/learning_agent/agent_engine_app.py](src/learning_agent/agent_engine_app.py) | Initializes Vertex AI and wraps the root agent in an `AdkApp` for both local and cloud use. |
| [src/main.py](src/main.py) | CLI script to interact with a **deployed** Agent Engine instance. Not used during local development. |

## Routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Student dashboard |
| `/chat` | GET | AI tutor chat interface |
| `/profile` | GET | User profile and interests |
| `/roadmap` | GET | Curriculum skill tree |
| `/resources` | GET | Learning module resources |
| `/quiz` | GET | Interactive quiz |
| `/quiz-results` | GET | Quiz results and feedback |
| `/api/chat` | POST | Chat endpoint (SSE streaming) |
| `/api/new-profile` | POST | Clear session & cookie, start fresh |
| `/api/reset-progression` | POST | Reset learning progression (clear session) |

## Agent Details

| Agent | Model | Role |
|---|---|---|
| `learning_tutor` | gemini-2.5-flash | Root orchestrator — routes to sub-agents |
| `assessment_agent` | gemini-2.5-flash | 3–5 turn assessment → JSON user context |
| `curriculum_agent` | gemini-2.5-flash | Generates 4–6 step curriculum with resources |
| `quiz_agent` | gemini-2.5-flash | MCQ generation + evaluation (2/3 pass threshold) |

## Deploy to Vertex AI Agent Engine

Set environment variables, then deploy:

```bash
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
export GOOGLE_CLOUD_LOCATION="europe-west1"

cd src
uv run adk deploy agent_engine \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --display_name="Learning Tutor Agent" \
  --otel_to_cloud \
  learning_agent
```

After deployment, use `src/main.py` to interact with the deployed agent:

```bash
export AGENT_ENGINE_RESOURCE_ID="<resource-id-from-deploy-output>"
uv run python src/main.py
```

## Troubleshooting

**Port 8000 already in use**

```bash
lsof -ti:8000 | xargs kill -9
```

**Missing `.env` file**

If you see `ModuleNotFoundError` or the agent doesn't initialize, ensure you've created `src/learning_agent/.env` from the example:

```bash
cp src/learning_agent/.env.example src/learning_agent/.env
```

**Authentication errors**

Ensure you've run both:

```bash
gcloud auth login
gcloud auth application-default login
```

**Tests fail with import errors**

Ensure you're running tests from the project root:

```bash
cd Google-Cloud-Hackathon-19
uv run pytest tests/ -v
```

