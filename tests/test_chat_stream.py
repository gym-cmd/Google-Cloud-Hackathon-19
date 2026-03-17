from app import _compute_text_delta, _extract_event_text


class TestExtractEventText:
    def test_skips_system_log_event(self):
        event = {
            "content": "system prompt",
            "logging.googleapis.com/labels": {
                "event.name": "gen_ai.system.message",
            },
        }

        assert _extract_event_text(event) == ""

    def test_skips_user_log_event(self):
        event = {
            "content": {
                "parts": [
                    {"text": "For context:"},
                    {
                        "text": (
                            "[learning_tutor] called tool "
                            "`transfer_to_agent`"
                        ),
                    },
                ],
                "role": "user",
            },
            "logging.googleapis.com/labels": {
                "event.name": "gen_ai.user.message",
            },
        }

        assert _extract_event_text(event) == ""

    def test_keeps_model_text_from_choice_event(self):
        event = {
            "content": {
                "parts": [
                    {
                        "text": (
                            "That is a strong starting point. "
                            "Let's narrow the basics."
                        ),
                        "thought_signature": "ABC123",
                    }
                ],
                "role": "model",
            },
            "logging.googleapis.com/labels": {
                "event.name": "gen_ai.choice",
            },
        }

        assert _extract_event_text(event) == (
            "That is a strong starting point. Let's narrow the basics."
        )

    def test_keeps_json_summary_from_model_event(self):
        event = {
            "content": {
                "parts": [
                    {
                        "text": (
                            "```json\n{\n"
                            '  "assessment_complete": true\n'
                            "}\n```"
                        ),
                    }
                ],
                "role": "model",
            },
        }

        assert _extract_event_text(event).startswith("```json")


class TestStructuredStateExtraction:
    def test_extracts_assessment_state(self):
        from app import _parse_structured_state

        text = (
            "Great, I have enough information.\n\n"
            "```json\n"
            '{"assessment_complete": true, "user_context": {"name": "Alex"}}\n'
            "```"
        )

        assert _parse_structured_state(text) == {
            "assessment_complete": True,
            "user_context": {"name": "Alex"},
        }

    def test_removes_json_from_visible_text(self):
        from app import _remove_structured_state_text

        text = (
            "Great, I have enough information to create a learning path.\n\n"
            "```json\n"
            '{"assessment_complete": true, "user_context": {"name": "Alex"}}\n'
            "```"
        )

        assert _remove_structured_state_text(text) == (
            "Great, I have enough information to create a learning path."
        )

    def test_fallback_text_for_assessment_state(self):
        from app import _fallback_text_for_state

        assert _fallback_text_for_state({"assessment_complete": True}) == (
            "I have enough information to create a focused learning path for you."
        )


class TestComputeTextDelta:
    def test_first_chunk_is_emitted(self):
        delta, merged = _compute_text_delta("Hello", "")

        assert delta == "Hello"
        assert merged == "Hello"

    def test_incremental_prefix_only_emits_suffix(self):
        delta, merged = _compute_text_delta("Hello world", "Hello")

        assert delta == " world"
        assert merged == "Hello world"

    def test_duplicate_chunk_is_skipped(self):
        delta, merged = _compute_text_delta("Hello world", "Hello world")

        assert delta == ""
        assert merged == "Hello world"

    def test_shorter_regression_chunk_is_skipped(self):
        delta, merged = _compute_text_delta("Hello", "Hello world")

        assert delta == ""
        assert merged == "Hello world"

    def test_distinct_message_is_separated(self):
        delta, merged = _compute_text_delta("Second answer", "First answer")

        assert delta == "\n\nSecond answer"
        assert merged == "First answer\n\nSecond answer"
