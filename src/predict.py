"""Safe inference: input validation, unknown-location fallback and non-negative output."""

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from src import config


@lru_cache(maxsize=4)
def load_artifacts(models_dir: str = str(config.MODELS_DIR)):
    """Load (model, columns metadata, metrics) once and cache them."""
    models_dir = Path(models_dir)
    model = joblib.load(models_dir / "model.joblib")
    columns = json.loads((models_dir / "columns.json").read_text())
    metrics = json.loads((models_dir / "metrics.json").read_text())
    return model, columns, metrics


def _normalize(text: str) -> str:
    return " ".join(str(text).split()).lower()


def resolve_location(location: str, known_locations: list[str]) -> str:
    """Map user input to a trained location column (case/whitespace-insensitive).

    Unknown locations fall back to the baseline 'other' (all location dummies = 0).
    """
    lookup = {_normalize(loc): loc for loc in known_locations}
    return lookup.get(_normalize(location), config.BASELINE_LOCATION)


def validate_inputs(sqft: float, bath: int, bhk: int) -> None:
    if bhk is None or bhk < 1:
        raise ValueError("BHK must be at least 1")
    if bath is None or bath < 1:
        raise ValueError("bath must be at least 1")
    if sqft is None or sqft <= 0:
        raise ValueError("sqft must be positive")
    if sqft / bhk < config.MIN_SQFT_PER_BHK:
        raise ValueError(f"sqft must be at least {config.MIN_SQFT_PER_BHK} per BHK "
                         f"({config.MIN_SQFT_PER_BHK * bhk} for {bhk} BHK)")


def build_features(location: str, sqft: float, bath: int, bhk: int, feature_columns: list[str]) -> pd.DataFrame:
    """One-row DataFrame with the exact training column names and order."""
    row = pd.DataFrame(np.zeros((1, len(feature_columns))), columns=feature_columns)
    row.loc[0, ["total_sqft", "bath", "BHK"]] = [float(sqft), float(bath), float(bhk)]
    if location in feature_columns:
        row.loc[0, location] = 1.0
    return row


def predict_price(location: str, sqft: float, bath: int, bhk: int, models_dir: str = str(config.MODELS_DIR)) -> float:
    """Predicted price in lakhs (never negative). Raises ValueError on invalid inputs."""
    validate_inputs(sqft, bath, bhk)
    model, columns, _ = load_artifacts(models_dir)
    resolved = resolve_location(location, columns["locations"])
    features = build_features(resolved, sqft, bath, bhk, columns["feature_columns"])
    return float(max(0.0, model.predict(features)[0]))
