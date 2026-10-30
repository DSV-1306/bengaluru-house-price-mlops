"""Generate monitoring/grafana/dashboards/house-price.json (run: python scripts/build_dashboard.py).

Queries work both in docker-compose and on AKS (kube-prometheus-stack): the API job is called
"house-price-api" in both, and process_* metrics are used for CPU/memory.
"""

import json
from pathlib import Path

DS = {"type": "prometheus", "uid": "prometheus"}
JOB = 'job="house-price-api"'
OUT = Path(__file__).resolve().parent.parent / "monitoring" / "grafana" / "dashboards" / "house-price.json"


def target(expr, legend="", ref="A", instant=False, fmt="time_series"):
    return {"datasource": DS, "expr": expr, "legendFormat": legend, "refId": ref,
            "instant": instant, "range": not instant, "format": fmt}


def panel(pid, title, ptype, targets, x, y, w=12, h=8, unit="short", options=None, description=""):
    return {
        "id": pid, "title": title, "type": ptype, "datasource": DS, "description": description,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "fieldConfig": {"defaults": {"unit": unit}, "overrides": []},
        "options": options or {},
        "targets": targets,
    }


STAT = {"colorMode": "value", "graphMode": "area", "reduceOptions": {"calcs": ["lastNotNull"]}}
REPLICAS = ('max(kube_deployment_status_replicas_available{namespace="house-price",deployment="house-price-api"})'
            f" or count(up{{{JOB}}} == 1)")


def latency(q, window):
    return f"histogram_quantile({q}, sum by (le) (rate(prediction_latency_seconds_bucket{{{JOB}}}[{window}])))"


panels = [
    panel(1, "Total predictions", "stat", [target(f"sum(predictions_total{{{JOB}}})", "predictions")],
          0, 0, w=6, h=5, options=STAT),
    panel(2, "API replicas", "stat", [target(REPLICAS, "replicas")], 6, 0, w=6, h=5, options=STAT,
          description="Available replicas on Kubernetes; number of scraped API instances in docker-compose"),
    panel(3, "Prediction error rate", "stat",
          [target(f"sum(rate(prediction_errors_total{{{JOB}}}[5m])) / "
                  f"clamp_min(sum(rate(http_requests_total{{{JOB},handler=\"/predict\"}}[5m])), 1e-9)", "error ratio")],
          12, 0, w=6, h=5, unit="percentunit", options=STAT),
    panel(4, "p95 prediction latency", "stat", [target(latency(0.95, "5m"), "p95")],
          18, 0, w=6, h=5, unit="s", options=STAT),

    panel(5, "Request rate by endpoint", "timeseries",
          [target(f'sum by (handler) (rate(http_requests_total{{{JOB},handler!="/metrics"}}[1m]))', "{{handler}}")],
          0, 5, unit="reqps"),
    panel(6, "Prediction latency p50 / p95", "timeseries",
          [target(latency(0.50, "1m"), "p50"), target(latency(0.95, "1m"), "p95", "B")],
          12, 5, unit="s"),

    panel(7, "Errors per second", "timeseries",
          [target(f"sum(rate(prediction_errors_total{{{JOB}}}[1m]))", "prediction errors"),
           target(f'sum(rate(http_requests_total{{{JOB},status=~"4xx|5xx"}}[1m]))', "HTTP 4xx/5xx", "B")],
          0, 13, unit="reqps"),
    panel(8, "Predictions by location (top 10)", "bargauge",
          [target(f"topk(10, sum by (location) (predictions_total{{{JOB}}}))", "{{location}}", instant=True)],
          12, 13, options={"orientation": "horizontal", "displayMode": "gradient",
                           "reduceOptions": {"calcs": ["lastNotNull"]}}),

    panel(9, "Predicted price distribution (lakhs)", "bargauge",
          [target(f"sum by (le) (predicted_price_lakhs_bucket{{{JOB}}})", "{{le}}", instant=True, fmt="heatmap")],
          0, 21, options={"orientation": "vertical", "displayMode": "basic",
                          "reduceOptions": {"calcs": ["lastNotNull"]}},
          description="Number of predictions per price bucket (upper bound, in lakhs)"),
    panel(10, "Replica count over time", "timeseries", [target(REPLICAS, "API replicas")], 12, 21),

    panel(11, "API CPU usage (per pod / container)", "timeseries",
          [target(f"rate(process_cpu_seconds_total{{{JOB}}}[1m])", "{{instance}}")],
          0, 29, unit="percentunit", description="CPU cores used per API process"),
    panel(12, "API memory usage (per pod / container)", "timeseries",
          [target(f"process_resident_memory_bytes{{{JOB}}}", "{{instance}}")],
          12, 29, unit="bytes"),
]

dashboard = {
    "uid": "house-price",
    "title": "Bengaluru House Price API",
    "tags": ["mlops", "house-price"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "10s",
    "time": {"from": "now-30m", "to": "now"},
    "panels": panels,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {OUT} ({len(panels)} panels)")
