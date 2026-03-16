# Spec: Curriculum Generation & Content

## Problem Statement
Once we know the user's goal and level, we need to give them a concrete, step-by-step learning path with actionable resources — not just a list of topics.

## Proposed Solution
Using the user context object from assessment, call the Gemini API once to generate a structured curriculum:

- **Roadmap**: 4–6 ordered learning steps, each with a title and one-paragraph overview
- **Resources**: for each step, 2–3 curated resource suggestions (article, video, or documentation) provided as titled links with a one-line description

The response is requested as JSON and validated before rendering. The user sees a visual roadmap (numbered cards) and can expand any step to read its overview and resources. Steps are marked "locked" until the previous step's quiz is passed (see spec 03).

## Acceptance Criteria
- [ ] Given a valid user context, the app calls Gemini and receives a structured curriculum in JSON
- [ ] The curriculum is displayed as an ordered list of step cards
- [ ] Each card shows a title, overview paragraph, and resource links
- [ ] The first step is unlocked; all others are locked on initial load
- [ ] A step unlocks when the previous step's quiz is passed
- [ ] If the API call fails, an error message is shown and the user can retry

## Out of Scope
- Editing or regenerating individual steps
- Saving curricula to a database (in-memory only for MVP)
- Video embeds or content previews
- Progress persistence across page refreshes
