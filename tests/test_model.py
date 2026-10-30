import numpy as np
from sklearn.metrics import r2_score

from src import config
from src.data_processing import prepare_dataset
from src.predict import load_artifacts
from src.train import split_data


def test_model_r2_on_test_set_meets_quality_gate(models_dir):
    model, columns, _ = load_artifacts(models_dir)
    X, y = prepare_dataset()
    _, X_test, _, y_test = split_data(X, y)
    pred = np.clip(model.predict(X_test[columns["feature_columns"]]), 0, None)
    assert r2_score(y_test, pred) >= config.MIN_TEST_R2


def test_metrics_and_columns_files(models_dir):
    _, columns, metrics = load_artifacts(models_dir)
    for key in ("model_name", "version", "r2", "mae", "rmse", "train_date", "comparison"):
        assert key in metrics
    assert metrics["r2"] >= config.MIN_TEST_R2
    assert columns["feature_columns"][:3] == ["total_sqft", "bath", "BHK"]
    assert len(columns["locations"]) == len(columns["feature_columns"]) - 3
