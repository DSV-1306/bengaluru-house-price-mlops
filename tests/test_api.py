import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(models_dir):
    mp = pytest.MonkeyPatch()
    mp.setenv("MODELS_DIR", models_dir)
    from api.main import app

    with TestClient(app) as c:
        yield c
    mp.undo()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_locations(client):
    r = client.get("/locations")
    assert r.status_code == 200
    locs = r.json()["locations"]
    assert "Whitefield" in locs
    assert locs == sorted(locs)


def test_model_info(client):
    body = client.get("/model-info").json()
    assert {"model_name", "version", "r2", "mae", "rmse"} <= body.keys()


def test_predict_success(client):
    r = client.post("/predict", json={"location": "Whitefield", "sqft": 1200, "bath": 2, "bhk": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["price_lakhs"] > 0
    assert body["location_used"] == "Whitefield"
    assert body["price_formatted"].startswith("₹")


def test_predict_unknown_location_uses_other(client):
    r = client.post("/predict", json={"location": "Atlantis", "sqft": 1200, "bath": 2, "bhk": 2})
    assert r.status_code == 200
    assert r.json()["location_used"] == "other"


@pytest.mark.parametrize("payload", [
    {"location": "Whitefield", "sqft": 400, "bath": 2, "bhk": 3},   # < 300 sqft per BHK
    {"location": "Whitefield", "sqft": 1200, "bath": 0, "bhk": 2},  # schema: bath >= 1
    {"location": "Whitefield", "sqft": -5, "bath": 1, "bhk": 1},    # schema: sqft > 0
])
def test_predict_invalid_input(client, payload):
    assert client.post("/predict", json=payload).status_code == 422


def test_metrics_endpoint(client):
    client.post("/predict", json={"location": "Whitefield", "sqft": 1200, "bath": 2, "bhk": 2})
    text = client.get("/metrics").text
    for name in ("predictions_total", "prediction_latency_seconds", "predicted_price_lakhs",
                 "prediction_errors_total", "http_requests_total"):
        assert name in text
