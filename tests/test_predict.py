import itertools

import pytest

from src.predict import load_artifacts, predict_price, resolve_location


def test_known_location_prediction_is_positive(models_dir):
    price = predict_price("1st Phase JP Nagar", 1000, 2, 2, models_dir=models_dir)
    assert price > 0


def test_location_matching_ignores_case_and_spaces(models_dir):
    a = predict_price("1st Phase JP Nagar", 1200, 2, 2, models_dir=models_dir)
    b = predict_price("  1st   phase jp NAGAR ", 1200, 2, 2, models_dir=models_dir)
    assert a == b


def test_unknown_location_does_not_crash_and_uses_baseline(models_dir):
    unknown = predict_price("Atlantis Layout", 1200, 2, 2, models_dir=models_dir)
    other = predict_price("other", 1200, 2, 2, models_dir=models_dir)
    assert unknown == other
    assert unknown >= 0


def test_resolve_location(models_dir):
    _, columns, _ = load_artifacts(models_dir)
    assert resolve_location("whitefield", columns["locations"]) == "Whitefield"
    assert resolve_location("Nowhere", columns["locations"]) == "other"


@pytest.mark.parametrize("sqft, bath, bhk", [
    (500, 1, 2),    # 250 sqft/BHK
    (1000, 0, 2),   # no bathroom
    (1000, 2, 0),   # zero BHK
    (-100, 1, 1),   # negative area
])
def test_invalid_inputs_raise(models_dir, sqft, bath, bhk):
    with pytest.raises(ValueError):
        predict_price("Whitefield", sqft, bath, bhk, models_dir=models_dir)


def test_predictions_are_never_negative(models_dir):
    _, columns, _ = load_artifacts(models_dir)
    locations = columns["locations"][:20] + ["unknown place"]
    for loc, bhk, bath in itertools.product(locations, [1, 2, 4], [1, 3]):
        for sqft in (300 * bhk, 1500, 10000):
            assert predict_price(loc, sqft, bath, bhk, models_dir=models_dir) >= 0
