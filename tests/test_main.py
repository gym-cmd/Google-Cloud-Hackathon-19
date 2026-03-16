import os

import pytest


class TestMainConfig:
    def test_requires_google_cloud_project(self):
        """main.py should fail if GOOGLE_CLOUD_PROJECT is not set."""
        env = os.environ.copy()
        env.pop("GOOGLE_CLOUD_PROJECT", None)
        env.pop("AGENT_ENGINE_RESOURCE_ID", None)

        import subprocess
        result = subprocess.run(
            ["python", "-c", "import src.main"],
            capture_output=True,
            text=True,
            env=env,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )
        assert result.returncode != 0

    def test_requires_agent_engine_resource_id(self):
        """main.py should fail if AGENT_ENGINE_RESOURCE_ID is not set."""
        env = os.environ.copy()
        env["GOOGLE_CLOUD_PROJECT"] = "test-project"
        env.pop("AGENT_ENGINE_RESOURCE_ID", None)

        import subprocess
        result = subprocess.run(
            ["python", "-c", "import src.main"],
            capture_output=True,
            text=True,
            env=env,
            cwd=os.path.dirname(os.path.dirname(__file__)),
        )
        assert result.returncode != 0

    def test_location_defaults_to_europe_west1(self):
        """GOOGLE_CLOUD_LOCATION should default to europe-west1."""
        import pathlib
        main_py = pathlib.Path(__file__).parent.parent / "src" / "main.py"
        source = main_py.read_text()
        assert 'os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1")' in source

    def test_no_hardcoded_project_id(self):
        """main.py should not contain hardcoded project IDs."""
        import pathlib
        main_py = pathlib.Path(__file__).parent.parent / "src" / "main.py"
        source = main_py.read_text()
        assert "qwiklabs" not in source

    def test_no_hardcoded_resource_id(self):
        """main.py should not contain hardcoded resource IDs."""
        import pathlib
        main_py = pathlib.Path(__file__).parent.parent / "src" / "main.py"
        source = main_py.read_text()
        assert "1982331503949905920" not in source

    def test_has_main_guard(self):
        """main.py should use if __name__ == '__main__' guard."""
        import pathlib
        main_py = pathlib.Path(__file__).parent.parent / "src" / "main.py"
        source = main_py.read_text()
        assert '__name__' in source
        assert '__main__' in source
