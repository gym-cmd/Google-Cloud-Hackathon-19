import os
from unittest.mock import patch, MagicMock

import pytest


class TestAgentEngineApp:
    def test_imports_and_initializes(self):
        """Verify agent_engine_app can be imported and creates an AdkApp."""
        mock_vertexai = MagicMock()
        mock_adk_app_cls = MagicMock()

        with patch.dict(os.environ, {
            "GOOGLE_CLOUD_PROJECT": "test-project",
            "GOOGLE_CLOUD_LOCATION": "europe-west1",
        }):
            with patch.dict("sys.modules", {
                "vertexai": mock_vertexai,
                "vertexai.agent_engines": MagicMock(AdkApp=mock_adk_app_cls),
            }):
                # Force re-import
                import importlib
                import sys

                # Remove cached module so it re-executes
                sys.modules.pop("learning_agent.agent_engine_app", None)
                import learning_agent.agent_engine_app  # noqa: F811

                mock_vertexai.init.assert_called_once_with(
                    project="test-project",
                    location="europe-west1",
                )
                mock_adk_app_cls.assert_called_once()

    def test_uses_env_vars_for_project_and_location(self):
        """Verify it reads GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION."""
        mock_vertexai = MagicMock()
        mock_adk_app_cls = MagicMock()

        with patch.dict(os.environ, {
            "GOOGLE_CLOUD_PROJECT": "my-custom-project",
            "GOOGLE_CLOUD_LOCATION": "us-central1",
        }):
            with patch.dict("sys.modules", {
                "vertexai": mock_vertexai,
                "vertexai.agent_engines": MagicMock(AdkApp=mock_adk_app_cls),
            }):
                import importlib
                import sys

                sys.modules.pop("learning_agent.agent_engine_app", None)
                import learning_agent.agent_engine_app  # noqa: F811

                mock_vertexai.init.assert_called_once_with(
                    project="my-custom-project",
                    location="us-central1",
                )
