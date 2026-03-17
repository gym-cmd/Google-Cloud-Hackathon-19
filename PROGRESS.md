# Progress Tracker

## Status Key
- ⬜ Not started
- 🔧 In progress
- ✅ Completed

---

## Infrastructure

| Task | Status | Notes |
|---|---|---|
| Project scaffolding (uv + pyproject.toml) | ✅ | Dependencies pinned |
| ADK agent structure (src/learning_agent/) | ✅ | |
| Vertex AI deploy config (agent_engine_app.py) | ✅ | |

## Phase 1 — User Profile & Assessment (Spec 01)

| Task | Status | Notes |
|---|---|---|
| Root agent (greeting + profile collection) | ✅ | |
| Assessment sub-agent (3–5 turn chat) | ✅ | |
| User context extraction (structured JSON) | ✅ | |

## Phase 2 — Curriculum Generation & Content (Spec 02)

| Task | Status | Notes |
|---|---|---|
| Curriculum sub-agent | ✅ | |
| Structured curriculum JSON output | ✅ | |

## Phase 3 — Quiz & Adaptive Progression (Spec 03)

| Task | Status | Notes |
|---|---|---|
| Quiz sub-agent (generate + evaluate) | ✅ | |
| Pass/fail logic (2/3 threshold) | ✅ | In agent instructions |
| Revision hint generation | ✅ | |

## Phase 4 — Web UI

| Task | Status | Notes |
|---|---|---|
| FastAPI app (src/app.py) | ✅ | Serves 7 HTML pages + 3 API endpoints |
| Jinja2 templates (7 pages) | ✅ | Dashboard, chat, profile, roadmap, resources, quiz, quiz results |
| SSE streaming chat (/api/chat) | ✅ | Per-user cookie-based sessions |
| New profile / reset endpoints | ✅ | /api/new-profile, /api/reset-progression |
| FOUC fix (all templates) | ✅ | opacity:0 until DOMContentLoaded |
| All buttons wired | ✅ | Every interactive element operational |

## Phase 5 — Testing

| Task | Status | Notes |
|---|---|---|
| Agent definition tests (27) | ✅ | test_agent.py |
| Engine wrapper tests (2) | ✅ | test_agent_engine_app.py |
| App & template tests (43) | ✅ | test_app.py |
| CLI client tests (6) | ✅ | test_main.py |
| **Total: 78 tests passing** | ✅ | |

## Deployment

| Task | Status | Notes |
|---|---|---|
| Vertex AI Agent Engine deploy | ⬜ | Config ready, needs deploy |
| Authentication | ⬜ | Deferred |
| Persistent state / DB | ⬜ | Deferred |

---

*Last updated: 2026-03-17*
