"""Tests for the FastAPI app (src/app.py)."""
import pathlib
import re

import pytest
from fastapi.testclient import TestClient

import app as app_module

APP_SRC = (pathlib.Path(__file__).parent.parent / "src" / "app.py").read_text()


class TestAppStructure:
    """Static analysis tests for app.py."""

    def test_uses_lifespan(self):
        assert "lifespan" in APP_SRC
        assert "on_event" not in APP_SRC

    def test_all_page_routes_exist(self):
        routes = (
            "/",
            "/chat",
            "/profile",
            "/context",
            "/roadmap",
            "/resources",
            "/code",
            "/quiz",
            "/quiz-results",
        )
        for route in routes:
            assert f'"{route}"' in APP_SRC, f"Missing route {route}"

    def test_api_chat_endpoint(self):
        assert '"/api/chat"' in APP_SRC

    def test_api_new_profile_endpoint(self):
        assert '"/api/new-profile"' in APP_SRC

    def test_api_reset_progression_endpoint(self):
        assert '"/api/reset-progression"' in APP_SRC

    def test_cookie_based_sessions(self):
        assert "eduai_uid" in APP_SRC
        assert "httponly=True" in APP_SRC

    def test_no_global_user_session_constants(self):
        assert "USER_ID" not in APP_SRC
        assert "SESSION_ID" not in APP_SRC

    def test_relative_paths(self):
        assert "Path(__file__)" in APP_SRC

    def test_json_response_import(self):
        assert "JSONResponse" in APP_SRC

    def test_new_profile_deletes_cookie(self):
        assert "delete_cookie" in APP_SRC

    def test_reset_clears_session(self):
        # The reset endpoint should remove from _sessions
        assert "_sessions" in APP_SRC

    def test_chat_stream_extracts_only_text_parts(self):
        assert "_extract_event_text" in APP_SRC
        assert '_read_event_field(event, "content")' in APP_SRC
        assert 'payload["text"] = delta_text' in APP_SRC

    def test_chat_stream_ignores_transfer_metadata(self):
        assert "transfer_to_agent" in APP_SRC

    def test_chat_stream_filters_user_and_system_events(self):
        assert "gen_ai.system.message" in APP_SRC
        assert 'role == "user"' in APP_SRC

    def test_chat_stream_computes_text_deltas(self):
        assert "_compute_text_delta" in APP_SRC
        assert "cleaned_text.startswith(accumulated_text)" in APP_SRC

    def test_chat_stream_extracts_structured_state(self):
        assert "_parse_structured_state" in APP_SRC
        assert 'payload["state"] = state' in APP_SRC
        assert "_fallback_text_for_state" in APP_SRC


class TestTemplatesExist:
    """Verify all referenced templates exist on disk."""

    TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "src" / "templates"

    @pytest.mark.parametrize(
        "name",
        [
            "dashboard.html",
            "chat.html",
            "profile.html",
            "roadmap.html",
            "resources.html",
            "code.html",
            "quiz.html",
            "quiz_results.html",
        ],
    )
    def test_template_file_exists(self, name):
        assert (self.TEMPLATE_DIR / name).is_file(), f"Missing template {name}"


class TestTemplateFOUC:
    """All templates should include the FOUC fix."""

    TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "src" / "templates"
    TEMPLATES = [
        "dashboard.html",
        "chat.html",
        "profile.html",
        "roadmap.html",
        "resources.html",
        "code.html",
        "quiz.html",
        "quiz_results.html",
    ]

    @pytest.mark.parametrize("name", TEMPLATES)
    def test_body_starts_hidden(self, name):
        src = (self.TEMPLATE_DIR / name).read_text()
        assert "opacity: 0" in src

    @pytest.mark.parametrize("name", TEMPLATES)
    def test_has_reveal_script(self, name):
        src = (self.TEMPLATE_DIR / name).read_text()
        assert "document.body.style.opacity" in src


class TestTemplateButtons:
    """All interactive buttons should have onclick or href handlers."""

    TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "src" / "templates"

    def _read(self, name):
        return (self.TEMPLATE_DIR / name).read_text()

    def test_chat_attach_has_handler(self):
        src = self._read("chat.html")
        assert "attach_file" in src
        assert "openFilePicker()" in src
        assert 'id="chat-file-input"' in src

    def test_chat_more_vert_has_handler(self):
        src = self._read("chat.html")
        assert re.search(
            r'onclick=.*more_vert|more_vert.*onclick',
            src,
            re.DOTALL,
        )

    def test_chat_stream_sanitizes_transport_noise(self):
        src = self._read("chat.html")
        assert "sanitizeStreamText" in src
        assert "transfer_to_agent" in src
        assert "A-Za-z0-9+/" in src

    def test_chat_hides_structured_state_from_bubble(self):
        src = self._read("chat.html")
        assert "extractStructuredState" in src
        assert "removeStructuredStateText" in src
        assert "finalizeAssistantMessage" in src
        assert "fallbackMessageForState" in src

    def test_quiz_lightbulb_has_handler(self):
        src = self._read("quiz.html")
        assert re.search(
            r'lightbulb.*onclick|onclick.*lightbulb',
            src,
            re.DOTALL,
        )

    def test_quiz_settings_has_handler(self):
        src = self._read("quiz.html")
        assert re.search(
            r'assignment_ind.*onclick|onclick.*assignment_ind',
            src,
            re.DOTALL,
        )

    def test_quiz_results_notifications_has_handler(self):
        src = self._read("quiz_results.html")
        assert re.search(
            r'notifications.*onclick|onclick.*notifications',
            src,
            re.DOTALL,
        )

    def test_resources_more_horiz_has_handler(self):
        src = self._read("resources.html")
        assert re.search(
            r'more_horiz.*onclick|onclick.*more_horiz',
            src,
            re.DOTALL,
        )

    def test_resources_code_button_has_real_route(self):
        src = self._read("resources.html")
        assert 'href="/code"' in src

    def test_context_route_is_used_in_templates(self):
        names = (
            "chat.html",
            "roadmap.html",
            "resources.html",
            "code.html",
            "quiz.html",
            "quiz_results.html",
        )
        for name in names:
            src = self._read(name)
            assert "/context" in src


class TestProfileActions:
    """Context page should align with the conversational product flow."""

    TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "src" / "templates"

    def _read(self):
        return (self.TEMPLATE_DIR / "profile.html").read_text()

    def test_has_start_from_beginning_button(self):
        src = self._read()
        assert "startFromBeginning" in src

    def test_does_not_offer_new_profile_button(self):
        src = self._read()
        assert "New Profile" not in src
        assert "person_add" not in src

    def test_is_renamed_to_learning_context(self):
        src = self._read()
        assert "Learning Context" in src

    def test_reset_calls_api(self):
        src = self._read()
        assert "/api/reset-progression" in src

    def test_uses_chat_for_goal_refinement(self):
        src = self._read()
        assert "Refine Learning Goals" in src
        assert 'href="/chat"' in src

    def test_restart_action_has_confirmation(self):
        src = self._read()
        assert src.count("confirm(") >= 1

    def test_context_parsing_is_guarded(self):
        src = self._read()
        assert "loadStoredJson" in src
        assert "localStorage.removeItem(key)" in src
        assert "shareContext()" in src


class TestQuizFlow:
    """Quiz should evaluate answers locally and persist results."""

    TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "src" / "templates"

    def test_quiz_has_local_question_set(self):
        src = (self.TEMPLATE_DIR / "quiz.html").read_text()
        assert "/api/quiz/generate" in src
        assert "/api/quiz/evaluate" in src

    def test_quiz_persists_result(self):
        src = (self.TEMPLATE_DIR / "quiz.html").read_text()
        assert "eduai.quizResult" in src

    def test_results_read_local_quiz_state(self):
        src = (self.TEMPLATE_DIR / "quiz_results.html").read_text()
        assert "loadQuizResult" in src
        assert "answer-review" in src

    def test_quiz_escapes_dynamic_options(self):
        src = (self.TEMPLATE_DIR / "quiz.html").read_text()
        assert "escapeHtml(option)" in src

    def test_results_guard_and_escape_browser_state(self):
        src = (self.TEMPLATE_DIR / "quiz_results.html").read_text()
        assert "loadStoredJson('eduai.quizResult'" in src
        assert "escapeHtml(answer.question)" in src
        assert "shareQuizResult()" in src

    def test_server_side_quiz_scoring(self):
        """Evaluate endpoint scores deterministically with stored answers."""
        assert "_quiz_answers" in APP_SRC
        assert "correct_indices" in APP_SRC
        assert "score >= 2" in APP_SRC

    def test_quiz_generate_stores_correct_answers(self):
        """Generate endpoint must persist correct_index in _quiz_answers."""
        assert '_quiz_answers[user_id]' in APP_SRC
        assert 'q.get("correct_index"' in APP_SRC

    def test_quiz_step_unlocking(self):
        """Quiz step picker and resources enforce step unlocking."""
        quiz_src = (self.TEMPLATE_DIR / "quiz.html").read_text()
        assert "isUnlocked" in quiz_src
        assert "lock" in quiz_src
        resources_src = (self.TEMPLATE_DIR / "resources.html").read_text()
        assert "isUnlocked" in resources_src

    def test_take_quiz_navigates_to_quiz_page(self):
        """Chat sticker 'Take a Quiz' should be a link to /quiz."""
        chat_src = (self.TEMPLATE_DIR / "chat.html").read_text()
        assert 'href="/quiz"' in chat_src
        assert "Take a Quiz" in chat_src


class TestQuizApiFallback:
    def test_generate_quiz_falls_back_when_agent_returns_invalid_payload(
        self,
        monkeypatch,
    ):
        async def fake_collect_agent_response(user_id: str, message: str):
            return "", None, '{"questions": [{"question": "Incomplete"}]}'

        app_module._quiz_answers.clear()
        monkeypatch.setattr(
            app_module,
            "_collect_agent_response",
            fake_collect_agent_response,
        )

        client = TestClient(app_module.app)
        client.cookies.set("eduai_uid", "fallback-user")
        response = client.post(
            "/api/quiz/generate",
            json={
                "step_title": "Intro to HTML",
                "step_overview": (
                    "Learn how HTML structures simple webpages with "
                    "headings, paragraphs, and links."
                ),
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["fallback"] is True
        assert len(payload["questions"]) == 3
        assert app_module._quiz_answers["fallback-user"] == [1, 0, 2]
        assert all(
            "correct_index" not in question
            for question in payload["questions"]
        )

    def test_generate_quiz_falls_back_when_agent_raises(self, monkeypatch):
        async def fake_collect_agent_response(user_id: str, message: str):
            raise RuntimeError("upstream timeout")

        app_module._quiz_answers.clear()
        monkeypatch.setattr(
            app_module,
            "_collect_agent_response",
            fake_collect_agent_response,
        )

        client = TestClient(app_module.app)
        client.cookies.set("eduai_uid", "error-user")
        response = client.post(
            "/api/quiz/generate",
            json={
                "step_title": "CSS basics",
                "step_overview": (
                    "Practice selectors and layout so you can style a "
                    "simple webpage clearly."
                ),
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["fallback"] is True
        assert payload["warning"] == "upstream timeout"
        assert len(payload["questions"]) == 3


class TestThemeToggle:
    """All templates should include theme detection and toggle."""

    TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "src" / "templates"
    TEMPLATES = [
        "dashboard.html",
        "chat.html",
        "profile.html",
        "roadmap.html",
        "resources.html",
        "code.html",
        "quiz.html",
        "quiz_results.html",
    ]

    @pytest.mark.parametrize("name", TEMPLATES)
    def test_has_early_theme_detection(self, name):
        src = (self.TEMPLATE_DIR / name).read_text()
        assert "localStorage.getItem('theme')" in src

    @pytest.mark.parametrize("name", TEMPLATES)
    def test_has_theme_toggle_button(self, name):
        src = (self.TEMPLATE_DIR / name).read_text()
        assert "cycleTheme()" in src

    @pytest.mark.parametrize("name", TEMPLATES)
    def test_theme_toggle_is_bottom_left(self, name):
        src = (self.TEMPLATE_DIR / name).read_text()
        assert "bottom:1.5rem;left:1.5rem" in src

    @pytest.mark.parametrize("name", TEMPLATES)
    def test_supports_three_modes(self, name):
        src = (self.TEMPLATE_DIR / name).read_text()
        assert "'light','dark','system'" in src

    @pytest.mark.parametrize("name", TEMPLATES)
    def test_has_system_media_query_listener(self, name):
        src = (self.TEMPLATE_DIR / name).read_text()
        assert "prefers-color-scheme" in src

    @pytest.mark.parametrize("name", TEMPLATES)
    def test_darkmode_class_config(self, name):
        src = (self.TEMPLATE_DIR / name).read_text()
        assert 'darkMode' in src or 'dark:' in src
