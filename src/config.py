"""Central configuration: paths, constants and the model version."""

import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = Path(os.getenv("DATA_PATH", ROOT_DIR / "data" / "raw" / "Bengaluru_House.csv"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", ROOT_DIR / "models"))
MODEL_PATH = MODELS_DIR / "model.joblib"
COLUMNS_PATH = MODELS_DIR / "columns.json"
METRICS_PATH = MODELS_DIR / "metrics.json"

# Reproducibility
RANDOM_STATE = 0             # CV splits and model seeds
TEST_SPLIT_RANDOM_STATE = 10  # same hold-out split as the original notebook
TEST_SIZE = 0.2
CV_SPLITS = 5

# Cleaning rules (same as the notebook)
LOCATION_MIN_COUNT = 10      # locations with <= this many listings become "other"
MIN_SQFT_PER_BHK = 300
BASELINE_LOCATION = "other"  # dropped dummy column = all location dummies are 0

# Quality gate used by tests and CI
MIN_TEST_R2 = 0.80


def get_model_version() -> str:
    """Model version: $MODEL_VERSION, else the latest git tag, else a dev version."""
    env_version = os.getenv("MODEL_VERSION")
    if env_version:
        return env_version.lstrip("v")
    try:
        tag = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=ROOT_DIR, capture_output=True, text=True, check=True, timeout=5,
        ).stdout.strip()
        if tag:
            return tag.lstrip("v")
    except (OSError, subprocess.SubprocessError):
        pass
    return "1.0.0-dev"
