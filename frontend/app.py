"""Streamlit UI for the Bengaluru house price model.

Two modes:
* API mode        - env var API_URL is set (Docker / Kubernetes): calls the FastAPI backend.
* Standalone mode - API_URL not set (Streamlit Community Cloud): loads the model directly,
                    training a quick model on first start if models/ is empty.

Run locally:  streamlit run frontend/app.py
"""

import os
import sys
from pathlib import Path

import pandas as pd
import requests
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:  # so "src" is importable when Streamlit runs this file directly
    sys.path.insert(0, str(ROOT))

API_URL = os.getenv("API_URL", "").rstrip("/")
MODE = "API" if API_URL else "Standalone"

st.set_page_config(page_title="Bengaluru House Price Predictor", page_icon="🏠", layout="wide")


# ---- Backend access (API or local model) --------------------------------------
@st.cache_resource
def http() -> requests.Session:
    """One keep-alive session, so the chart's ~15 calls reuse a single connection."""
    return requests.Session()


@st.cache_resource(show_spinner="Loading model (first start may train a quick model, ~30s)...")
def local_artifacts():
    from src import config
    from src.predict import load_artifacts

    if not config.MODEL_PATH.exists():
        from src.train import main as train_main

        train_main(config.MODELS_DIR, quick=True)
    return load_artifacts(str(config.MODELS_DIR))


@st.cache_data(ttl=300)
def get_locations() -> list[str]:
    if API_URL:
        r = http().get(f"{API_URL}/locations", timeout=10)
        r.raise_for_status()
        return r.json()["locations"]
    _, columns, _ = local_artifacts()
    return sorted(columns["locations"])


@st.cache_data(ttl=60)
def get_model_info() -> dict:
    if API_URL:
        r = http().get(f"{API_URL}/model-info", timeout=10)
        r.raise_for_status()
        return r.json()
    return local_artifacts()[2]


def predict(location: str, sqft: float, bath: int, bhk: int) -> float:
    if API_URL:
        r = http().post(f"{API_URL}/predict",
                          json={"location": location, "sqft": sqft, "bath": bath, "bhk": bhk}, timeout=10)
        if r.status_code == 422:
            detail = r.json().get("detail")
            raise ValueError(detail if isinstance(detail, str) else "Invalid input")
        r.raise_for_status()
        return r.json()["price_lakhs"]
    from src.predict import predict_price

    local_artifacts()
    return predict_price(location, sqft, bath, bhk)


def format_price(lakhs: float) -> str:
    return f"₹{lakhs / 100:,.2f} Cr" if lakhs >= 100 else f"₹{lakhs:,.2f} Lakhs"


# ---- UI -------------------------------------------------------------------------
try:
    locations = get_locations()
    info = get_model_info()
except requests.RequestException as exc:
    st.error(f"Cannot reach the API at {API_URL}: {exc}")
    st.stop()

with st.sidebar:
    st.header("ℹ️ Model info")
    st.metric("Model", info.get("model_name", "?"))
    st.metric("Test R²", f"{info.get('r2', 0):.3f}")
    st.metric("Version", info.get("version", "?"))
    st.caption(f"MAE: {info.get('mae', 0):.2f} lakhs · RMSE: {info.get('rmse', 0):.2f} lakhs")
    st.caption(f"Trained: {info.get('train_date', '?')}")
    st.caption(f"Mode: **{MODE}**" + (f" · `{API_URL}`" if API_URL else ""))

st.title("🏠 Bengaluru House Price Predictor")
st.write("Estimate the price of a flat in Bengaluru from its location, area, bedrooms and bathrooms.")

col1, col2 = st.columns(2)
with col1:
    default_idx = locations.index("Whitefield") if "Whitefield" in locations else 0
    location = st.selectbox("📍 Location (type to search)", locations, index=default_idx)
    sqft = st.number_input("📐 Total area (sqft)", min_value=300, max_value=30000, value=1200, step=50)
with col2:
    bhk = st.slider("🛏️ BHK", min_value=1, max_value=10, value=2)
    bath = st.slider("🛁 Bathrooms", min_value=1, max_value=10, value=2)

if st.button("Predict price", type="primary", use_container_width=True):
    try:
        price = predict(location, float(sqft), int(bath), int(bhk))
    except ValueError as exc:
        st.error(f"⚠️ {exc}")
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
    else:
        st.success(f"### Estimated price: {format_price(price)}")
        st.caption(f"{bhk} BHK · {bath} bath · {sqft:,} sqft · {location} · ≈ ₹{price * 100000 / sqft:,.0f} per sqft")

        # Price vs area curve for the chosen location and BHK
        min_sqft = 300 * bhk
        points = sorted({int(min_sqft + i * (max(sqft * 2, min_sqft + 1000) - min_sqft) / 14) for i in range(15)})
        curve = pd.DataFrame({"sqft": points, "price (lakhs)": [predict(location, s, bath, bhk) for s in points]})
        st.subheader(f"Predicted price vs area — {location}, {bhk} BHK")
        st.line_chart(curve, x="sqft", y="price (lakhs)")
