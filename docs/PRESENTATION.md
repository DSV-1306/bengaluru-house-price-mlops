# Presenting the project to your mentor

A 10–15 minute walkthrough: what to open, what to say, and where each task lives.

## Before the meeting: open these tabs

| # | Tab | URL / how to open |
|---|---|---|
| 1 | GitHub repo | https://github.com/DSV-1306/bengaluru-house-price-mlops |
| 2 | Live app (Streamlit Cloud) | https://bengaluru-house-price-dsv.streamlit.app |
| 3 | GitHub Actions | https://github.com/DSV-1306/bengaluru-house-price-mlops/actions |
| 4 | Screenshot log | `docs/SCREENSHOTS.md` on GitHub (every screenshot + what it proves) |
| 5 | VS Code | the project folder `C:\Users\Dhruva\OneDrive\Documents\Desktop\Projects\bengaluru-house-price-mlops` |

Open the live app 5 minutes early: Streamlit Cloud apps sleep when unused and take ~1 minute to wake up.

If the internet is slow during the meeting, use the screenshots in `docs/screenshots/` — every step is recorded there.

---

## The one-minute summary (say this first)

> "I took my Jupyter notebook that predicts Bengaluru house prices and turned it into a production-style MLOps project.
> First I fixed the ML problems — a syntax error, a crash on unknown locations, negative price predictions — and compared
> six models instead of one. Then I packaged it as a FastAPI service and a Streamlit web app, versioned everything on
> GitHub with branches, pull requests and release tags, added automatic testing with GitHub Actions, containerised it
> with Docker, ran it on Kubernetes with autoscaling and rolling updates, monitored it with Prometheus and Grafana, and
> deployed the app publicly on Streamlit Community Cloud. The Azure infrastructure is written as Terraform code and is
> validated automatically, but I didn't deploy it because I don't have an active Azure subscription."

---

## Task by task: where it is, how it works, the proof

### 0. The ML model (the starting point)

- **Where:** `notebooks/J073_Project_SSDI.ipynb` (fixed notebook) → turned into `src/` (`data_processing.py`, `train.py`, `predict.py`).
- **What I fixed:** syntax error in the outlier function; `predict_price` crashed on unknown locations (now falls back to
  "other"); 53 negative price predictions (now 0, by training on `log(price)` with a log-log model); `SettingWithCopyWarning`;
  only one model tried → 6 models compared with GridSearchCV + 5-fold ShuffleSplit.
- **Result:** Ridge regression, **test R² = 0.845**, MAE 13.9 lakhs. Same accuracy as the original, but safe and reproducible.
- **Proof:** `phase1-model-comparison.png`, `phase1-pytest-passing.png` (31 tests), `phase1-notebook-clean-run.png`.

### 1. GitHub versioning ✅

- **Where:** the GitHub repo → **Branches** (`main`, `dev`), **Pull requests** (*Closed* tab), **Releases** (`v1.0.0`, `v1.1.0`).
- **How it works:**
  - `main` = production, **protected** (Settings → Branches): changes can only arrive through a Pull Request.
  - `dev` = integration branch. Each change is made on a `feature/...` or `docs/...` branch → PR into `dev` → CI tests it → merge.
  - A release = PR `dev` → `main`, then a **semantic version tag** (`v1.0.0`, `v1.1.0`).
  - Commits follow **conventional commits** (`feat:`, `fix:`, `docs:`), so history is readable.
  - **The git tag is the version everywhere:** it is written into the model's `metrics.json` and shown in the app's
    sidebar ("Version 1.0.0"), and CD would tag the Docker images with it.
- **Show:** repo → *Commits*, *Branches* (shield icon on `main`), *Pull requests → Closed*, *Releases*.
- **Proof:** `phase3-*.png`.

### 2. GitHub Actions CI/CD ✅ CI · ⚠️ CD written, not run (needs Azure)

- **Where:** `.github/workflows/ci.yml` and `.github/workflows/cd.yml`; results in the **Actions** tab.
- **CI (runs on every push and PR to `main`/`dev`):**
  1. `ruff` lint → 2. `pytest` (31 tests, coverage) → 3. train all 6 models → 4. upload `metrics.json` →
  5. **quality gate: the build fails if test R² < 0.80** → 6. build both Docker images → 7. `terraform fmt` + `validate`.
- **CD (on a version tag):** log in to Azure with OIDC (no stored password) → build & push images to Azure Container
  Registry → deploy to AKS → wait for rollout → smoke-test `/health` → automatic rollback if it fails.
  It is set to **skip itself** until Azure exists, which is why the CD runs show "skipped".
- **Show:** Actions tab → a green CI run → the 3 jobs (*Lint, test, train, quality gate* → *Build Docker images*, *Terraform*).
- **Proof:** `phase8-ci-green.png`, `phase8-ci-job-steps.png`.

### 3. Docker ✅

- **Where:** `docker/Dockerfile.api`, `docker/Dockerfile.frontend`, `docker-compose.yml`.
- **How it works:** the API image is **multi-stage** — stage 1 installs packages and **trains the model during the build**;
  stage 2 copies only what's needed into a slim image. It runs as a **non-root user** and has a **HEALTHCHECK**.
  `docker compose up` starts 4 containers: API, Streamlit UI, Prometheus, Grafana.
- **Demo (optional, on your laptop):** `docker compose start` → http://localhost:8501.
- **Proof:** `phase4-docker-images.png`, `phase4-compose-ps.png` (API "healthy"), `phase4-app-in-docker.png`.

### 4. Kubernetes ✅ on minikube (local cluster)

- **Where:** `k8s/base/` (namespace, configmap, 2 deployments, 2 services, HPA) + Kustomize overlays `k8s/overlays/local` and `k8s/overlays/aks`.
- **How it works:** the API runs as **2 replicas** with CPU/memory limits and **health probes** (`/health`); a
  **HorizontalPodAutoscaler** scales it 2→5 pods when CPU > 70 %; the UI is exposed through a LoadBalancer service.
- **What I demonstrated:** `kubectl get all`, `describe pod`, `logs`, manual `scale` to 3 (the HPA then scaled it back
  to 2 — correct behaviour), a **rolling update** to version 1.0.1 with zero downtime, and a **rollback** with
  `kubectl rollout undo` (verified the version inside the pods: 1.0.1 → 1.0.0).
- **Proof:** `phase6-*.png`.

### 5. Terraform ⚠️ code ready and validated, not applied

- **Where:** `infra/terraform/` (`providers.tf`, `variables.tf`, `main.tf`, `outputs.tf`, `terraform.tfvars.example`).
- **What it creates:** resource group, Azure Container Registry (Basic), AKS cluster (1 small node), the `AcrPull` role
  so AKS can pull images, and a managed identity + GitHub OIDC credential for CD.
- **Status:** `terraform validate` passes locally and in every CI run. Not applied because my college account
  (NMIMS) has no Azure subscription. With one, it's `terraform plan` → `terraform apply` (steps in `docs/RUNBOOK.md`, Part 6).

### 6. Prometheus + Grafana ✅ (local)

- **Where:** `api/main.py` (metrics), `monitoring/prometheus.yml`, `monitoring/grafana/` (auto-provisioned data source + dashboard).
- **How it works:** the API exposes `/metrics` with HTTP metrics plus custom ones: `predictions_total` (per location),
  `prediction_latency_seconds`, `predicted_price_lakhs`, `prediction_errors_total`. Prometheus scrapes it every 10 s;
  Grafana shows a 12-panel dashboard. I generated 3,000 requests with `scripts/load_test.py` to fill it with data.
- **Proof:** `phase2-metrics.png`, `phase7-prometheus-targets-local.png` (target UP), `phase7-promql-query.png`,
  `phase7-grafana-local.png`.

### 7. Deployment ✅ Streamlit Community Cloud

- **Where:** https://bengaluru-house-price-dsv.streamlit.app — deployed from the `main` branch, file `frontend/app.py`.
- **How it works:** the same `app.py` has two modes. With `API_URL` set (Docker/Kubernetes) it calls the FastAPI service;
  without it (Streamlit Cloud) it runs **standalone** and trains/loads the model itself. The sidebar shows which mode.
- **Demo:** pick a location, set sqft/BHK/bath → **Predict price** → result + price-vs-area chart. Point at the sidebar:
  model Ridge, R² 0.845, **Version** = the git tag.
- **Proof:** `phase9-streamlit-cloud.png`.

---

## Suggested live demo order (10 minutes)

1. **Live app** (2 min) — make a prediction, show the sidebar version.
2. **GitHub** (3 min) — README → Branches → a Pull Request (show "All checks have passed") → Releases.
3. **Actions** (2 min) — a green CI run, the quality gate step.
4. **Code tour in VS Code** (2 min) — `src/predict.py` (safe prediction), `docker/Dockerfile.api`, `k8s/base/hpa.yaml`, `infra/terraform/main.tf`.
5. **Screenshots** (1 min) — `docs/SCREENSHOTS.md`: Grafana dashboard, Kubernetes rolling update/rollback.

---

## Questions your mentor may ask

**Why log-transform the price?** Prices are skewed and a plain linear model predicted negative prices for 53 flats.
Training on `log(price)` (and `log(sqft)`) keeps predictions positive and handles the skew; we convert back with `exp`.

**Why Ridge and not Random Forest?** Ridge had the best cross-validation R² (0.837) and test R² (0.845), trains in ~1 s
and is easy to explain. The tree models were slower and slightly worse.

**What happens if someone enters a location the model hasn't seen?** It's treated as "other" (the baseline), so it
never crashes — there's a test for it.

**How do you stop a bad model from being deployed?** The CI quality gate: if test R² drops below 0.80, the pipeline
fails and the PR can't be merged with a green check.

**How is the version tracked?** One number: the git tag. It's passed into training (`metrics.json`), shown in the app,
and used as the Docker image tag.

**Where are secrets kept?** Nowhere in git: `.env` and `terraform.tfvars` are git-ignored; CD uses OIDC so no Azure
password is stored; the Grafana password on Kubernetes lives in a Kubernetes Secret.

**What does the HPA do?** Adds API pods (up to 5) when average CPU goes above 70 %, and removes them when load drops.

**Why isn't it on Azure?** The Terraform, Kubernetes AKS overlay and CD pipeline are written and validated in CI, but my
college account has no Azure subscription. Running `terraform apply` with a subscription would create it; the steps are in the runbook.
