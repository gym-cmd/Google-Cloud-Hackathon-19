# Spec: Quiz & Adaptive Progression

## Problem Statement
Reading material alone doesn't confirm understanding. We need a lightweight feedback loop that checks comprehension after each step and decides whether the user is ready to advance or should revisit the material.

## Proposed Solution
After a user marks a step as "done reading", the app generates a short quiz for that step via the Gemini API:

- **Quiz format**: 3 multiple-choice questions, each with 4 options and one correct answer
- **Scoring**: pass threshold is 2/3 correct
- **Adaptive logic**:
  - **Pass** → the next curriculum step unlocks; a brief congratulatory message is shown
  - **Fail** → a short AI-generated revision hint is shown (1–2 sentences targeting the weakest answer), and the user is prompted to re-read before retrying the quiz

The quiz and its result are generated/evaluated client-side from the JSON response — no separate backend scoring service needed.

## Acceptance Criteria
- [ ] A "Take Quiz" button appears when the user finishes reading a step
- [ ] Clicking it calls Gemini and renders 3 multiple-choice questions
- [ ] The user can select one answer per question and submit
- [ ] Score is calculated and pass/fail is shown immediately after submission
- [ ] On pass, the next step card unlocks
- [ ] On fail, a revision hint is displayed and the user can retake the quiz (regenerated each attempt)
- [ ] If the API call fails, an error is shown with a retry option

## Out of Scope
- Free-text or coding-exercise question types
- Tracking quiz attempt history
- Spaced repetition scheduling
- Adjusting curriculum difficulty based on quiz results
