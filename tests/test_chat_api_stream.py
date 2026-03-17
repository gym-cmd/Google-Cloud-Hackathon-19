import json
from types import SimpleNamespace

from fastapi.testclient import TestClient

import app as app_module


class MockAdkApp:
    async def async_create_session(self, user_id: str):
        return SimpleNamespace(id=f"session-for-{user_id}")

    async def async_stream_query(
        self,
        user_id: str,
        session_id: str,
        message: str,
    ):
        yield {
            "content": "system prompt",
            "logging.googleapis.com/labels": {
                "event.name": "gen_ai.system.message",
            },
        }
        yield {
            "content": {
                "parts": [
                    {
                        "text": (
                            "Great, an intermediate level in JavaScript "
                            "and React "
                            "is an excellent foundation!\n\n"
                            "I think I have enough information to create "
                            "a focused "
                            "learning path for you.\n\n"
                            "```json\n"
                            "{\n"
                            '  "assessment_complete": true,\n'
                            '  "user_context": {\n'
                            '    "name": "user",\n'
                            '    "experience_level": "intermediate"\n'
                            "  }\n"
                            "}\n"
                            "```"
                        )
                    }
                ],
                "role": "model",
            },
            "logging.googleapis.com/labels": {
                "event.name": "gen_ai.choice",
            },
        }


class TestChatApiStream:
    def test_assessment_json_is_not_emitted_as_visible_text(self, monkeypatch):
        app_module._sessions.clear()
        monkeypatch.setattr(app_module, "adk_app", MockAdkApp())

        client = TestClient(app_module.app)
        response = client.post(
            "/api/chat",
            json={"message": "Mid."},
        )

        assert response.status_code == 200
        events = []
        for chunk in response.text.split("\n\n"):
            if not chunk.startswith("data: "):
                continue
            payload = chunk[6:]
            if payload == "[DONE]":
                continue
            events.append(json.loads(payload))

        assert len(events) == 1
        assert events[0]["text"] == (
            "Great, an intermediate level in JavaScript and React "
            "is an excellent foundation!\n\n"
            "I think I have enough information to create a focused "
            "learning path for you."
        )
        assert events[0]["state"] == {
            "assessment_complete": True,
            "user_context": {
                "name": "user",
                "experience_level": "intermediate",
            },
        }
        assert "assessment_complete" not in events[0]["text"]
