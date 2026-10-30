from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "frontend" / "app.py")


def test_frontend_standalone_mode_predicts(models_dir, monkeypatch):
    """No API_URL -> the app loads the model directly (Streamlit Community Cloud mode)."""
    monkeypatch.delenv("API_URL", raising=False)
    monkeypatch.setenv("MODELS_DIR", models_dir)
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    assert not at.exception
    assert at.sidebar.metric[0].value  # model name shown in the sidebar

    at.button[0].click().run()
    assert not at.exception
    assert "Estimated price" in at.success[0].value
