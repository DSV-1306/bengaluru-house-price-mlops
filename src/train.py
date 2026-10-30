"""Train and compare regressors, then save the best model and its metadata.

Run with:  python -m src.train
"""

import argparse
import json
import time
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, ShuffleSplit, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.tree import DecisionTreeRegressor

from src import config
from src.data_processing import log_sqft, prepare_dataset

RS = config.RANDOM_STATE

# Each model is wrapped so it learns log1p(price) and predicts expm1(...) back in lakhs.
# Grid keys are prefixed "regressor__model__" (TransformedTargetRegressor -> Pipeline step "model").
MODEL_GRIDS = {
    "LinearRegression": (LinearRegression(), {"regressor__model__fit_intercept": [True, False]}),
    "Lasso": (Lasso(max_iter=20000, random_state=RS), {"regressor__model__alpha": [0.0001, 0.001, 0.01]}),
    "Ridge": (Ridge(random_state=RS), {"regressor__model__alpha": [0.1, 1.0, 10.0]}),
    "DecisionTree": (
        DecisionTreeRegressor(random_state=RS),
        {"regressor__model__max_depth": [10, 20, None], "regressor__model__min_samples_split": [2, 10]},
    ),
    "RandomForest": (
        RandomForestRegressor(random_state=RS, n_jobs=-1),
        {"regressor__model__n_estimators": [100, 300], "regressor__model__max_depth": [20, None]},
    ),
    "GradientBoosting": (
        GradientBoostingRegressor(random_state=RS),
        {"regressor__model__n_estimators": [300, 600], "regressor__model__learning_rate": [0.05, 0.1]},
    ),
}


def log_target(estimator):
    """sqft -> log1p(sqft), then fit on log1p(price) and invert predictions with expm1."""
    pipeline = Pipeline([
        ("log_sqft", FunctionTransformer(log_sqft, feature_names_out="one-to-one")),
        ("model", estimator),
    ])
    return TransformedTargetRegressor(regressor=pipeline, func=np.log1p, inverse_func=np.expm1)


def evaluate(model, X, y) -> dict:
    pred = np.clip(model.predict(X), 0, None)
    return {
        "r2": float(r2_score(y, pred)),
        "mae": float(mean_absolute_error(y, pred)),
        "rmse": float(np.sqrt(mean_squared_error(y, pred))),
    }


def split_data(X, y):
    return train_test_split(X, y, test_size=config.TEST_SIZE, random_state=config.TEST_SPLIT_RANDOM_STATE)


def compare_models(X_train, y_train, X_test, y_test, grids=MODEL_GRIDS):
    """GridSearchCV each model on the training set; return (results table, fitted searches)."""
    cv = ShuffleSplit(n_splits=config.CV_SPLITS, test_size=0.2, random_state=RS)
    rows, searches = [], {}
    for name, (estimator, grid) in grids.items():
        start = time.perf_counter()
        search = GridSearchCV(log_target(estimator), grid, cv=cv, scoring="r2", n_jobs=-1)
        search.fit(X_train, y_train)
        test_metrics = evaluate(search.best_estimator_, X_test, y_test)
        rows.append({
            "model": name,
            "cv_r2": float(search.best_score_),
            "test_r2": test_metrics["r2"],
            "test_mae": test_metrics["mae"],
            "test_rmse": test_metrics["rmse"],
            "best_params": {k.replace("regressor__model__", ""): v for k, v in search.best_params_.items()},
            "fit_seconds": round(time.perf_counter() - start, 1),
        })
        searches[name] = search
        print(f"  {name:<17} CV R2={search.best_score_:.4f}  ({rows[-1]['fit_seconds']}s)")
    table = pd.DataFrame(rows).sort_values("cv_r2", ascending=False).reset_index(drop=True)
    return table, searches


QUICK_MODELS = ("LinearRegression", "Ridge")


def main(models_dir: Path = config.MODELS_DIR, quick: bool = False) -> dict:
    """Train, compare and save artifacts to models_dir. quick=True only tries the fast linear models."""
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    grids = {k: v for k, v in MODEL_GRIDS.items() if k in QUICK_MODELS} if quick else MODEL_GRIDS

    X, y = prepare_dataset()
    X_train, X_test, y_train, y_test = split_data(X, y)
    print(f"Dataset: {X.shape[0]} rows, {X.shape[1]} features | train={len(X_train)} test={len(X_test)}")
    print("Grid-searching models (target = log1p(price), CV = ShuffleSplit x5)...")

    table, searches = compare_models(X_train, y_train, X_test, y_test, grids)
    best_name = table.iloc[0]["model"]
    best_row = table.iloc[0]
    best_model = searches[best_name].best_estimator_

    locations = [c for c in X.columns if c not in ("total_sqft", "bath", "BHK")]
    metrics = {
        "model_name": best_name,
        "version": config.get_model_version(),
        "train_date": datetime.now(UTC).isoformat(timespec="seconds"),
        "target_transform": "log1p",
        "best_params": best_row["best_params"],
        "cv_r2": round(float(best_row["cv_r2"]), 4),
        "r2": round(float(best_row["test_r2"]), 4),
        "mae": round(float(best_row["test_mae"]), 4),
        "rmse": round(float(best_row["test_rmse"]), 4),
        "n_train": len(X_train),
        "n_test": len(X_test),
        "comparison": [
            {k: (round(v, 4) if isinstance(v, float) else v) for k, v in row.items()}
            for row in table.to_dict(orient="records")
        ],
    }

    joblib.dump(best_model, models_dir / "model.joblib")
    (models_dir / "columns.json").write_text(json.dumps({
        "feature_columns": list(X.columns),
        "locations": locations,
        "baseline_location": config.BASELINE_LOCATION,
    }, indent=2))
    (models_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))

    display = table.drop(columns=["best_params"]).copy()
    display.columns = ["Model", "CV R2", "Test R2", "MAE (lakhs)", "RMSE (lakhs)", "Fit time (s)"]
    print("\n=== Model comparison (sorted by CV R2) ===")
    print(display.to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(f"\nBest model: {best_name}  params={best_row['best_params']}")
    print(f"Test R2={metrics['r2']}  MAE={metrics['mae']}  RMSE={metrics['rmse']}  version={metrics['version']}")
    print(f"Saved: model.joblib, columns.json, metrics.json -> {models_dir}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and compare house price models.")
    parser.add_argument("--models-dir", default=str(config.MODELS_DIR), help="where to save artifacts")
    parser.add_argument("--quick", action="store_true", help="only LinearRegression and Ridge (fast)")
    args = parser.parse_args()
    main(Path(args.models_dir), quick=args.quick)
