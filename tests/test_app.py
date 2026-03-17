"""Tests for the FastAPI app (src/app.py)."""

import pathlib
import re

import pytest

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


class TestQuizFlow:
    """Quiz should evaluate answers locally and persist results."""

    TEMPLATE_DIR = pathlib.Path(__file__).parent.parent / "src" / "templates"

    def test_quiz_has_local_question_set(self):
        src = (self.TEMPLATE_DIR / "quiz.html").read_text()
        assert "defaultQuestions" in src
        assert "correctIndex" in src

    def test_quiz_persists_result(self):
        src = (self.TEMPLATE_DIR / "quiz.html").read_text()
        assert "eduai.quizResult" in src

    def test_results_read_local_quiz_state(self):
        src = (self.TEMPLATE_DIR / "quiz_results.html").read_text()
        assert "loadQuizResult" in src
        assert "answer-review" in src


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
