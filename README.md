# Personalized Learning Tutor — Google Cloud Hackathon 19

An AI-powered software development tutor built with [Google ADK](https://google.github.io/adk-docs/) (Agent Development Kit). A root agent orchestrates three specialized sub-agents to deliver a guided learning experience through conversational AI.

## How It Works

```
User ←→ learning_tutor (root)
              │
              ├── assessment_agent    — 3–5 turn chat to clarify goals & prior knowledge
              ├── curriculum_agent    — generates 4–6 step learning path with resources
              └── quiz_agent          — creates MCQ quizzes, evaluates answers, gives hints
```

1. **Profile & Assessment** — The root agent greets the user, collects their name/level/goal, then hands off to `assessment_agent` for a short diagnostic conversation. The assessment produces a structured JSON context.
2. **Curriculum Generation** — `curriculum_agent` uses that context to build a step-by-step curriculum. It can call `fetch_webpage_content` to verify that resource URLs are live.
3. **Quiz & Progression** — When the user finishes a step, `quiz_agent` generates 3 MCQs. Pass (≥2/3) → next step. Fail → revision hints + retry.

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.11 – 3.13 |
| [uv](https://docs.astral.sh/uv/) | latest |
| [gcloud CLI](https://cloud.google.com/sdk/docs/install) | latest |
| GCP project with Vertex AI API enabled | — |

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd Google-Cloud-Hackathon-19
uv sync


```bash 
gcloud auth login
gcloud auth application-default login
gcloud config set project qwiklabs-asl-03-35787841388f
```
# 3. Run the ADK web UI
uv run adk web src
```

The agent uses Vertex AI via application default credentials — no API key needed. The GCP project and region are configured in `src/learning_agent/.env`.

Open the URL printed in the terminal (usually `http://localhost:8000`). Select `learning_agent` from the agent dropdown and start chatting.

## Troubleshooting

**Port 8000 already in use**

If you see `[Errno 48] Address already in use`, kill the stale process and restart:

```bash
lsof -ti:8000 | xargs kill -9
```

## Deploy to Vertex AI Agent Engine

```bash
cd src

export PROJECT_ID="your-gcp-project-id"
export LOCATION_ID="europe-west1"

uv run adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=$LOCATION_ID \
  --display_name="Learning Tutor Agent" \
  --otel_to_cloud \
  learning_agent
```

> Requires GCP project with Vertex AI API enabled and appropriate IAM permissions.

## Project Structure

```
.
├── pyproject.toml                          # uv project config + Python dependencies
├── uv.lock                                 # Pinned dependency lockfile
├── specs/                                  # Feature specifications (read before coding)
│   ├── _template.md
│   ├── 01-user-profile-and-assessment.md
│   ├── 02-curriculum-generation-and-content.md
│   └── 03-quiz-and-adaptive-progression.md
└── src/
    └── learning_agent/
        ├── __init__.py
        ├── agent.py                        # All agent definitions (root + 3 sub-agents)
        ├── agent_engine_app.py             # Vertex AI Agent Engine wrapper
        ├── requirements.txt                # Deploy-time dependencies (Vertex only)
        └── tools/
            ├── __init__.py
            └── web_fetcher.py              # HTTP fetch + HTML text extraction
```

### Key Files

| File | Purpose |
|---|---|
| `agent.py` | Defines the root `learning_tutor` agent and its three sub-agents. All prompts, model config, and orchestration logic live here. |
| `tools/web_fetcher.py` | Async tool that fetches a URL, strips HTML boilerplate, and returns clean text. Used by `curriculum_agent` to verify resource links. Includes URL validation and SSRF protection. |
| `agent_engine_app.py` | Thin wrapper that initializes Vertex AI and creates an `AdkApp` for cloud deployment. Not used during local dev. |
| `requirements.txt` | Dependencies installed on Vertex AI at deploy time (separate from `pyproject.toml` which is for local dev). |

## Agent Details

### Model

All agents use `gemini-3-flash-preview`. Change the `MODEL` constant in `agent.py` to switch.

### Assessment Agent
- Asks 3–5 clarifying questions about the user's goals and existing knowledge
- Outputs a structured JSON `user_context` with: name, level, goal, prior knowledge, confirmed focus
- Does **not** teach — only assesses

### Curriculum Agent
- Takes assessment context and generates 4–6 ordered learning steps
- Each step includes a title, overview paragraph, and 2–3 resource links
- Uses `fetch_webpage_content` tool to verify URLs are accessible
- Returns structured JSON

### Quiz Agent
- Generates exactly 3 MCQs per step (4 options each, one correct)
- Evaluates submitted answers against correct indices
- Pass threshold: 2/3 correct
- On failure: provides targeted revision hints

## Specs

All feature work starts with a spec. Before writing code, a spec must exist in `specs/`.

Each spec includes: problem statement, proposed solution, acceptance criteria, and out-of-scope items. See `specs/_template.md` for the format.
