# Bugs & Issues

## 2026-03-17 Frontend Validation Log

### BUG-31: Chat SSE parser dropped streamed bot replies

**Files:** `src/templates/chat.html`
**Severity:** High
**Status:** Resolved

The client parsed each SSE chunk as if it contained complete JSON events. When the stream split an event across reads, the parser failed silently and left the user with a sent message and no bot response.

### BUG-32: Prompt chip leaked icon text into chat input

**Files:** `src/templates/chat.html`
**Severity:** Medium
**Status:** Resolved

The chip buttons used `textContent.trim()`, so the Material icon name was included in the submitted prompt. That is why the UI showed text like `casino Surprise Topic`.

### BUG-33: Quiz screen started mid-journey

**Files:** `src/templates/quiz.html`
**Severity:** Medium
**Status:** Resolved

The quiz view was hard-coded to `Step 3 of 5` and preselected the first answer, which made the quiz appear half-finished before the learner started.

### BUG-34: Profile page exposed a non-product action

**Files:** `src/templates/profile.html`
**Severity:** Medium
**Status:** Resolved

The UI offered `New Profile`, but the underlying product is conversational and session-based. The action conflicted with the intended flow and has been replaced with a restart-from-beginning action.

### BUG-35: Code navigation pointed to a missing experience

**Files:** `src/templates/resources.html`, `src/app.py`
**Severity:** High
**Status:** Resolved

The `Code` button did not open a code workspace because no `/code` route or template existed. A dedicated code lab page has been added and linked.

### BUG-36: Theme toggle location mismatched product requirement

**Files:** `src/templates/*.html`
**Severity:** Low
**Status:** Resolved

The theme control was positioned top-right. It has been moved to the bottom-left across all frontend pages.

### BUG-37: Chat attachment control was still a placeholder button

**Files:** `src/templates/chat.html`
**Severity:** Medium
**Status:** Resolved

The attachment button only displayed a placeholder alert, which meant the control was not operational. It now opens the file picker, captures the selected filename, and folds that context into the outgoing tutor message.

### BUG-38: Frontend assumed a static profile instead of conversation state

**Files:** `src/templates/chat.html`, `src/templates/profile.html`, `src/app.py`
**Severity:** High
**Status:** Resolved

The frontend treated the learner as a pre-existing persona with a profile and static progress, which conflicted with the agent architecture. The app is now chat-first, exposes a learning context view, and persists assessment state from the agent response.

### BUG-39: Quiz always behaved like a fake success flow

**Files:** `src/templates/quiz.html`, `src/templates/quiz_results.html`
**Severity:** High
**Status:** Resolved

The previous quiz flow posted the chosen answer to chat and always redirected to a celebratory results page, even when the learner answered incorrectly. The quiz now evaluates answers locally, stores real result state, and renders pass/fail results with answer review.

No open frontend bugs remain from this validation pass.
