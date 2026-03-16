# Spec: User Profile & Assessment

## Problem Statement
Before generating a learning plan, the system needs to understand who the user is and what they want to learn. Without this context, any generated curriculum will be generic and unhelpful.

## Proposed Solution
A two-step onboarding flow:

1. **Profile form** — user fills in name, current experience level (beginner / intermediate / advanced), and a free-text field for their learning goal (e.g. "learn Python for data analysis").
2. **Assessment chat** — a short AI-driven conversation (3–5 turns) that clarifies the goal, surfaces existing knowledge, and confirms the learning focus. The chat is powered by a single Gemini API call per turn with a system prompt that keeps the conversation on-track and structured.

At the end of assessment, a structured user context object is saved (name, level, goal, key prior knowledge) and passed to curriculum generation.

## Acceptance Criteria
- [ ] User can submit a profile form with name, experience level, and learning goal
- [ ] After form submission, a chat interface opens and the AI asks a clarifying question
- [ ] The conversation ends after at most 5 turns with a summary of confirmed learning focus
- [ ] A user context object is persisted (in-memory or local storage for MVP) and available to subsequent steps
- [ ] The UI is usable on desktop (mobile not required for MVP)

## Out of Scope
- User authentication / accounts
- Editing or deleting a saved profile
- Multiple concurrent learning goals
