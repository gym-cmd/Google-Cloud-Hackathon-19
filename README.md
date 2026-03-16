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
2. **Curriculum Generation** — `curriculum_agent` uses that context to build a step-by-step curriculum with curated resources.
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
```

```bash
# 2. Authenticate and configure GCP
gcloud auth login
gcloud auth application-default login
```

```bash
# 3. Set environment variables (edit values for your project)
export GOOGLE_CLOUD_PROJECT="qwiklabs-asl-03-35787841388f"
export GOOGLE_CLOUD_LOCATION="europe-west1"
export AGENT_ENGINE_RESOURCE_ID="your-agent-engine-resource-id"
```

```bash
# 4. Run the ADK web UI
uv run adk web src
```

The agent uses Vertex AI via application default credentials — no API key needed. The GCP project and region are configured in `src/learning_agent/.env`.

Open `http://localhost:8000` in your browser — it redirects to the ADK dev UI at `/dev-ui/`. Select `learning_agent` from the agent dropdown and start chatting.

## Troubleshooting

**Port 8000 already in use**

If you see `[Errno 48] Address already in use`, kill the stale process and restart:

```bash
lsof -ti:8000 | xargs kill -9
```

## Deploy to Vertex AI Agent Engine

```bash
cd src

uv run adk deploy agent_engine \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --display_name="Learning Tutor Agent" \
  --otel_to_cloud \
  learning_agent
```

> Uses the same `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` env vars from step 3 above.

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
├── tests/                                  # Unit and integration tests
└── src/
    ├── main.py                             # Vertex AI Agent Engine client script
    └── learning_agent/
        ├── __init__.py
        ├── .env                            # GCP project & region config
        ├── agent.py                        # All agent definitions (root + 3 sub-agents)
        ├── agent_engine_app.py             # Vertex AI Agent Engine wrapper
        └── tools/
            └── __init__.py
```

### Key Files

| File | Purpose |
|---|---|
| `agent.py` | Defines the root `learning_tutor` agent and its three sub-agents. All prompts, model config, and orchestration logic live here. |
| `agent_engine_app.py` | Thin wrapper that initializes Vertex AI and creates an `AdkApp` for cloud deployment. Not used during local dev. |

## Agent Details

### Model

All agents use `gemini-2.5-flash`. Change the `MODEL` constant in `agent.py` to switch.

### Assessment Agent
- Asks 3–5 clarifying questions about the user's goals and existing knowledge
- Outputs a structured JSON `user_context` with: name, level, goal, prior knowledge, confirmed focus
- Does **not** teach — only assesses

### Curriculum Agent
- Takes assessment context and generates 4–6 ordered learning steps
- Each step includes a title, overview paragraph, and 2–3 resource links
- Returns structured JSON

### Quiz Agent
- Generates exactly 3 MCQs per step (4 options each, one correct)
- Evaluates submitted answers against correct indices
- Pass threshold: 2/3 correct
- On failure: provides targeted revision hints

## Specs

All feature work starts with a spec. Before writing code, a spec must exist in `specs/`.

Each spec includes: problem statement, proposed solution, acceptance criteria, and out-of-scope items. See `specs/_template.md` for the format.
