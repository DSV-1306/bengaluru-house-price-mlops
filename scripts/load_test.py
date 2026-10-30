"""Send prediction traffic to the API so Prometheus/Grafana (and the HPA) have data.

Usage:  python scripts/load_test.py --url http://localhost:8000 --requests 2000 --workers 20
"""

import argparse
import random
import time
from concurrent.futures import ThreadPoolExecutor

import requests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=2000)
    parser.add_argument("--workers", type=int, default=20)
    parser.add_argument("--error-rate", type=float, default=0.05, help="share of deliberately invalid requests")
    args = parser.parse_args()

    url = args.url.rstrip("/")
    locations = requests.get(f"{url}/locations", timeout=10).json()["locations"]
    rng = random.Random(0)

    def payload():
        bhk = rng.randint(1, 4)
        if rng.random() < args.error_rate:
            return {"location": rng.choice(locations), "sqft": 100 * bhk, "bath": 1, "bhk": bhk}  # invalid
        return {"location": rng.choice(locations[:30] + locations), "sqft": rng.randint(350 * bhk, 900 * bhk),
                "bath": rng.randint(1, bhk + 1), "bhk": bhk}

    payloads = [payload() for _ in range(args.requests)]
    session = requests.Session()

    def send(p):
        try:
            return session.post(f"{url}/predict", json=p, timeout=10).status_code
        except requests.RequestException:
            return 0

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        codes = list(pool.map(send, payloads))
    elapsed = time.perf_counter() - start

    print(f"Sent {len(codes)} requests in {elapsed:.1f}s ({len(codes) / elapsed:.0f} req/s)")
    for code in sorted(set(codes)):
        print(f"  HTTP {code or 'connection error'}: {codes.count(code)}")


if __name__ == "__main__":
    main()
