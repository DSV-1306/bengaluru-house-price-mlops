"""Data cleaning, outlier removal and feature encoding (ported from the notebook).

Every step is deterministic: no random sampling, groupby keys are sorted and the
one-hot columns are produced in sorted order.
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src import config

DROP_COLUMNS = ["area_type", "society", "balcony", "availability"]


def load_raw(path: Path | str = config.DATA_PATH) -> pd.DataFrame:
    return pd.read_csv(path)


def is_float(x) -> bool:
    try:
        float(x)
    except (TypeError, ValueError):
        return False
    return True


def convert_sqft_to_num(x):
    """'1056' -> 1056.0, '2100 - 2850' -> 2475.0 (range midpoint), '34.46Sq. Meter' -> None."""
    tokens = str(x).split("-")
    if len(tokens) == 2:
        try:
            return (float(tokens[0]) + float(tokens[1])) / 2
        except ValueError:
            return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def clean_data(df: pd.DataFrame, min_count: int = config.LOCATION_MIN_COUNT) -> pd.DataFrame:
    """Drop unused columns/NaNs, parse BHK and sqft, add price_per_sqft, group rare locations."""
    df = df.drop(columns=DROP_COLUMNS).dropna().copy()
    df["BHK"] = df["size"].apply(lambda x: int(str(x).split(" ")[0]))
    df["total_sqft"] = df["total_sqft"].apply(convert_sqft_to_num)
    df["price_per_sqft"] = df["price"] * 100000 / df["total_sqft"]

    # Location counts include rows with unparseable sqft, exactly as in the notebook
    df["location"] = df["location"].str.strip()
    location_counts = df["location"].value_counts()
    rare = set(location_counts[location_counts <= min_count].index)
    df.loc[df["location"].isin(rare), "location"] = config.BASELINE_LOCATION

    df = df.dropna(subset=["total_sqft"])
    # Each bedroom needs at least MIN_SQFT_PER_BHK sqft, otherwise it's a data error
    df = df[df["total_sqft"] / df["BHK"] >= config.MIN_SQFT_PER_BHK].copy()
    return df


def remove_pps_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Per location, keep rows whose price_per_sqft is within mean +/- 1 std."""
    parts = []
    for _, subdf in df.groupby("location", sort=True):
        m = np.mean(subdf.price_per_sqft)
        std = np.std(subdf.price_per_sqft)
        parts.append(subdf[(subdf.price_per_sqft > (m - std)) & (subdf.price_per_sqft <= (m + std))])
    return pd.concat(parts, ignore_index=True)


def remove_bhk_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Drop n-BHK flats that are cheaper per sqft than the mean (n-1)-BHK flat in the same location."""
    exclude_indices = []
    for _, location_df in df.groupby("location", sort=True):
        bhk_stats = {}
        for bhk, bhk_df in location_df.groupby("BHK"):
            bhk_stats[bhk] = {
                "mean": np.mean(bhk_df.price_per_sqft),
                "std": np.std(bhk_df.price_per_sqft),
                "count": bhk_df.shape[0],
            }
        for bhk, bhk_df in location_df.groupby("BHK"):
            stats = bhk_stats.get(bhk - 1)
            if stats and stats["count"] > 5:
                exclude_indices.extend(bhk_df[bhk_df.price_per_sqft < stats["mean"]].index.values)
    return df.drop(index=exclude_indices)


def remove_bath_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Keep listings with fewer than BHK + 2 bathrooms."""
    return df[df.bath < df.BHK + 2].copy()


def encode_features(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """One-hot encode location (dropping the 'other' baseline) and split into X, y."""
    df = df.drop(columns=["size", "price_per_sqft"])
    dummies = pd.get_dummies(df["location"]).astype(int)
    dummies = dummies.drop(columns=[config.BASELINE_LOCATION], errors="ignore")
    dummies = dummies[sorted(dummies.columns)]
    X = pd.concat([df[["total_sqft", "bath", "BHK"]], dummies], axis="columns")
    y = df["price"]
    return X, y


def log_sqft(X: pd.DataFrame) -> pd.DataFrame:
    """log1p(total_sqft) so linear models fit log(price) ~ log(sqft) (a log-log model).

    Lives here (not in train.py) so the pickled model references src.data_processing.log_sqft,
    which can be imported by the API/tests, instead of __main__.log_sqft.
    """
    X = X.copy()
    X["total_sqft"] = np.log1p(X["total_sqft"])
    return X


def prepare_dataset(path: Path | str = config.DATA_PATH) -> tuple[pd.DataFrame, pd.Series]:
    """Full pipeline: raw CSV -> (X, y) ready for training."""
    df = clean_data(load_raw(path))
    df = remove_pps_outliers(df)
    df = remove_bhk_outliers(df)
    df = remove_bath_outliers(df)
    return encode_features(df)
