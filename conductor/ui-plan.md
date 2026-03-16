# UI Implementation Plan

## Objective
Integrate the provided HTML mockups from the `UI-mockups/` directory into a fully functional web application powered by the existing Google ADK-based AI tutor backend (`src/learning_agent`).

## Scope & Impact
- Serve the static UI files using a robust backend framework.
- Connect the frontend chat interface to the `adk_app.async_stream_query` agent backend.
- Ensure the user flow between the profile, dashboard, and tutor interface is functional.
- Adhere to Python and web development best practices.

## Proposed Solution
1. **Framework Setup**: 
   - Add `fastapi` and `uvicorn` to `pyproject.toml`.
   - Setup a FastAPI application in `src/app.py` to serve both HTML templates and an API layer.
2. **UI Restructuring**:
   - Create a standard `src/templates` directory.
   - Move and consolidate the HTML files from `UI-mockups` into Jinja2 templates or static files, linking CSS/JS correctly.
3. **Backend Integration**:
   - Create an API route (e.g., `/api/chat`) in FastAPI that accepts user input, maintains a session ID, and yields Server-Sent Events (SSE) using the `adk_app.async_stream_query` generator.
4. **Frontend Wiring**:
   - Modify the chat interface's Javascript (`ai_tutor_chat_interface/code.html`) to intercept form submissions, send the message to `/api/chat`, and dynamically append the streaming text from the AI to the DOM.
5. **Testing & Review**:
   - Start the uvicorn server, navigate through the mockups, and ensure the chat streams correctly and UI elements look identical to the mockups.

## Implementation Steps
- [ ] Add FastAPI dependencies.
- [ ] Create FastAPI setup and API routes for the ADK integration.
- [ ] Migrate `UI-mockups` to `src/templates` and `src/static`.
- [ ] Connect the AI Tutor chat UI to the backend streaming endpoint.
- [ ] Perform manual end-to-end testing and review.

## Alternatives Considered
- *Streamlit / Gradio*: Dropped because we specifically need to use the bespoke Tailwind HTML mockups provided by the user.
- *Node.js Backend*: Dropped because the AI agent logic is already written in Python using Google ADK. FastAPI provides the most seamless bridging layer.

## Verification
1. Run `uv run uvicorn src.app:app --reload`.
2. Load the application in a browser.
3. Open the AI Tutor Chat Interface, type a message, and observe the AI responding dynamically via the streaming engine.
