from pathlib import Path

import pytest

from src import config


@pytest.fixture(scope="session")
def models_dir(tmp_path_factory) -> str:
    """Use models/ if a trained model exists, otherwise train a quick model into a temp dir."""
    if config.MODEL_PATH.exists() and config.COLUMNS_PATH.exists() and config.METRICS_PATH.exists():
        return str(config.MODELS_DIR)
    from src.train import main

    out: Path = tmp_path_factory.mktemp("models")
    main(out, quick=True)
    return str(out)
