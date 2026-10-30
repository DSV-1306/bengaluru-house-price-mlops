"""FastAPI service for Bengaluru house price predictions.

Run locally:  uvicorn api.main:app --reload
"""

import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

from src import config
from src.predict import load_artifacts, predict_price, resolve_location

# ---- Custom Prometheus metrics ------------------------------------------------
PREDICTIONS = Counter("predictions_total", "Number of successful predictions", ["location"])
PREDICTION_ERRORS = Counter("prediction_errors_total", "Number of failed prediction requests")
PREDICTION_LATENCY = Histogram(
    "prediction_latency_seconds", "Time spent computing a prediction",
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)
PREDICTED_PRICE = Histogram(
    "predicted_price_lakhs", "Distribution of predicted prices (lakhs)",
    buckets=(25, 50, 75, 100, 150, 200, 300, 500, 1000),
)


def models_dir() -> str:
    return os.getenv("MODELS_DIR", str(config.MODELS_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the model once at startup; fail fast if artifacts are missing
    load_artifacts(models_dir())
    yield


app = FastAPI(
    title="Bengaluru House Price API",
    description="Predicts Bengaluru house prices (in lakhs) from location, area, bathrooms and BHK.",
    version=os.getenv("MODEL_VERSION", "1.0.0"),
    lifespan=lifespan,
)
Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)


class PredictRequest(BaseModel):
    location: str = Field(..., min_length=1, examples=["Whitefield"])
    sqft: float = Field(..., gt=0, description="Total area in square feet", examples=[1200])
    bath: int = Field(..., ge=1, le=20, examples=[2])
    bhk: int = Field(..., ge=1, le=20, examples=[2])


class PredictResponse(BaseModel):
    location: str
    location_used: str
    price_lakhs: float
    price_formatted: str
    model_version: str


def format_price(lakhs: float) -> str:
    if lakhs >= 100:
        return f"₹{lakhs / 100:,.2f} Cr ({lakhs:,.2f} Lakhs)"
    return f"₹{lakhs:,.2f} Lakhs"


@app.get("/health")
def health():
    _, _, metrics = load_artifacts(models_dir())
    return {"status": "ok", "model_loaded": True, "model_version": metrics["version"]}


@app.get("/locations")
def locations():
    _, columns, _ = load_artifacts(models_dir())
    return {"locations": sorted(columns["locations"]), "baseline_location": columns["baseline_location"]}


@app.get("/model-info")
def model_info():
    _, _, metrics = load_artifacts(models_dir())
    return metrics


@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    start = time.perf_counter()
    try:
        _, columns, metrics = load_artifacts(models_dir())
        price = predict_price(req.location, req.sqft, req.bath, req.bhk, models_dir=models_dir())
    except ValueError as exc:
        PREDICTION_ERRORS.inc()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        PREDICTION_ERRORS.inc()
        raise HTTPException(status_code=500, detail="prediction failed") from exc

    used = resolve_location(req.location, columns["locations"])
    PREDICTION_LATENCY.observe(time.perf_counter() - start)
    PREDICTIONS.labels(location=used).inc()
    PREDICTED_PRICE.observe(price)
    return PredictResponse(
        location=req.location,
        location_used=used,
        price_lakhs=round(price, 2),
        price_formatted=format_price(price),
        model_version=metrics["version"],
    )
