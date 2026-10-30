import numpy as np
import pandas as pd
import pytest

from src import config
from src.data_processing import (
    clean_data,
    convert_sqft_to_num,
    is_float,
    prepare_dataset,
    remove_bath_outliers,
    remove_bhk_outliers,
    remove_pps_outliers,
)


@pytest.mark.parametrize("raw, expected", [
    ("1056", 1056.0),
    ("2100 - 2850", 2475.0),
    ("34.46Sq. Meter", None),
    ("abc", None),
])
def test_convert_sqft_to_num(raw, expected):
    assert convert_sqft_to_num(raw) == expected


def test_is_float():
    assert is_float("12.5")
    assert not is_float("1133 - 1384")
    assert not is_float(None)


def _raw(rows):
    cols = ["area_type", "availability", "location", "size", "society", "total_sqft", "bath", "balcony", "price"]
    return pd.DataFrame(rows, columns=cols)


def test_clean_data_parses_and_filters():
    rows = [["A", "Ready", " Whitefield ", "2 BHK", "S", "1200", 2, 1, 60.0]] * 12
    rows += [
        ["A", "Ready", "Tiny Place", "3 Bedroom", "S", "1500 - 1700", 3, 1, 90.0],  # rare -> other
        ["A", "Ready", "Whitefield", "6 Bedroom", "S", "1020", 6, 1, 370.0],       # < 300 sqft/BHK -> dropped
        ["A", "Ready", "Whitefield", "2 BHK", "S", "34.46Sq. Meter", 2, 1, 40.0],   # bad sqft -> dropped
        ["A", "Ready", None, "2 BHK", "S", "1000", 2, 1, 50.0],                      # NaN -> dropped
    ]
    out = clean_data(_raw(rows))

    assert len(out) == 13
    assert set(out.location) == {"Whitefield", config.BASELINE_LOCATION}  # stripped + rare grouped
    assert out.loc[out.location == "other", "total_sqft"].iloc[0] == 1600.0
    assert out.loc[out.location == "other", "BHK"].iloc[0] == 3
    assert (out.total_sqft / out.BHK >= config.MIN_SQFT_PER_BHK).all()
    assert out.isna().sum().sum() == 0
    np.testing.assert_allclose(out.price_per_sqft, out.price * 100000 / out.total_sqft)


def test_remove_pps_outliers_drops_extremes():
    df = pd.DataFrame({"location": ["X"] * 6, "price_per_sqft": [5000, 5100, 4900, 5050, 4950, 50000]})
    out = remove_pps_outliers(df)
    assert 50000 not in out.price_per_sqft.values
    assert len(out) == 5


def test_remove_bhk_outliers_drops_cheaper_bigger_flats():
    two_bhk = [{"location": "X", "BHK": 2, "price_per_sqft": 6000}] * 6
    three_bhk = [{"location": "X", "BHK": 3, "price_per_sqft": 4000},  # cheaper than 2BHK mean -> drop
                 {"location": "X", "BHK": 3, "price_per_sqft": 7000}]
    out = remove_bhk_outliers(pd.DataFrame(two_bhk + three_bhk))
    assert len(out) == 7
    assert 4000 not in out.price_per_sqft.values


def test_remove_bath_outliers():
    df = pd.DataFrame({"BHK": [2, 2, 3], "bath": [2, 5, 4]})
    assert remove_bath_outliers(df).bath.tolist() == [2, 4]


def test_prepare_dataset_shape_and_determinism():
    X1, y1 = prepare_dataset()
    X2, y2 = prepare_dataset()
    assert X1.shape == (7251, 244)  # same as the original notebook
    assert list(X1.columns[:3]) == ["total_sqft", "bath", "BHK"]
    assert config.BASELINE_LOCATION not in X1.columns
    pd.testing.assert_frame_equal(X1, X2)
    pd.testing.assert_series_equal(y1, y2)
