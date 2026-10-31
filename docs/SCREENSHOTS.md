# Screenshot Log

All screenshots live in [`docs/screenshots/`](screenshots/). How to take each one: [RUNBOOK.md](RUNBOOK.md).
Status: ✅ captured · ⬜ pending · ➖ not taken (Azure part not deployed: no Azure subscription; the code is in the repo and validated in CI).

| # | File | Phase | What it proves | Runbook step | Status |
|---|------|-------|----------------|---|---|
| 1 | `phase0-tool-versions.png` | 0 Prerequisites | All tools installed (Python, Git, Docker, kubectl, minikube, Helm, Terraform, az, gh) | 0.5 | ✅ |
| 2 | `phase1-model-comparison.png` | 1 ML fixes | 6 models compared with GridSearchCV + ShuffleSplit; Ridge best, test R² 0.845 | 0.6 | ✅ |
| 3 | `phase1-pytest-passing.png` | 1 ML fixes | 31 tests pass (cleaning, unknown location, non-negative, R² gate, API, UI) | 0.6 | ✅ |
| 4 | `phase1-notebook-clean-run.png` | 1 ML fixes | Notebook runs top to bottom: 0 errors, 0 warnings | 0.6 | ✅ |
| 5 | `phase1-notebook-comparison.png` | 1 ML fixes | Comparison table in notebook, 0 negative predictions, unknown location OK | 0.6 | ⬜ |
| 6 | `phase2-fastapi-docs.png` | 2 API/UI | FastAPI Swagger UI with all endpoints | 1.4 | ✅ |
| 7 | `phase2-predict-call.png` | 2 API/UI | Successful `POST /predict` (200, price in lakhs + ₹ format) | 1.4 | ✅ |
| 8 | `phase2-streamlit-home.png` | 2 API/UI | Streamlit UI with model info sidebar | 1.4 | ✅ |
| 9 | `phase2-streamlit-prediction.png` | 2 API/UI | Prediction result card + price-vs-sqft chart | 1.4 | ✅ |
| 10 | `phase2-metrics.png` | 2 API/UI | `/metrics` exposes custom Prometheus metrics | 1.4 | ✅ |
| 10b | `phase3-branch-protection.png` | 3 Git | Branch protection rule on `main` (changes only via PR) | 2.6 | ✅ |
| 11 | `phase3-github-repo.png` | 3 Git | Public GitHub repo with README + CI badge | 2.10 | ✅ |
| 12 | `phase3-commit-history.png` | 3 Git | Conventional commit history | 2.10 | ✅ |
| 13 | `phase3-branches.png` | 3 Git | `main` (protected) + `dev` branches | 2.10 | ✅ |
| 14 | `phase3-pull-request.png` | 3 Git | Feature branch → PR → merge workflow | 2.8 | ✅ |
| 14b | `phase3-branch-protection.png` | 3 Git | Branch protection rule on `main` (changes only via PR) | 2.6 | ✅ |
| 15 | `phase3-tags-releases.png` | 3 Git | Semantic version tag / release v1.0.0 | 2.10 | ✅ |
| 16 | `phase4-docker-images.png` | 4 Docker | `house-price-api` and `house-price-frontend` images built | 3.2 | ✅ |
| 17 | `phase4-compose-ps.png` | 4 Docker | 4 containers running, API healthy | 3.4 | ✅ |
| 18 | `phase4-app-in-docker.png` | 4 Docker | App working from containers | 3.5 | ✅ |
| 19 | `phase7-prometheus-targets-local.png` | 7 Monitoring | Prometheus scrapes the API (UP) | 4.2 | ✅ |
| 20 | `phase7-promql-query.png` | 7 Monitoring | PromQL query result (top-10 locations) | 4.3 | ✅ |
| 21 | `phase7-grafana-local.png` | 7 Monitoring | Grafana dashboard with live data (docker-compose) | 4.4 | ✅ |
| 22 | `phase6-get-all.png` | 6 Kubernetes | `kubectl get all` on minikube | 5.3 | ✅ |
| 23 | `phase6-describe-pod.png` | 6 Kubernetes | Pod details: probes, resource limits, events | 5.3 | ✅ |
| 24 | `phase6-logs.png` | 6 Kubernetes | `kubectl logs` of the API | 5.3 | ✅ |
| 25 | `phase6-scale.png` | 6 Kubernetes | Manual scaling to 3 replicas | 5.3 | ✅ |
| 26 | `phase6-hpa.png` | 6 Kubernetes | HPA (CPU 70 %, min 2 / max 5) | 5.3 | ✅ |
| 27 | `phase6-rolling-update.png` | 6 Kubernetes | Rolling update to 1.0.1 + rollout status/history | 5.4 | ✅ |
| 28 | `phase6-rollout-undo.png` | 6 Kubernetes | Rollback with `rollout undo` | 5.4 | ✅ |
| 29 | `phase6-app-minikube.png` | 6 Kubernetes | App served from minikube | 5.5 | ✅ |
| 30 | `phase5-terraform-plan.png` | 5 Terraform | `terraform plan`: 8 to add | 6.4 | ➖ no Azure subscription |
| 31 | `phase5-terraform-apply.png` | 5 Terraform | `Apply complete! Resources: 8 added` | 6.5 | ➖ no Azure subscription |
| 32 | `phase5-terraform-output.png` | 5 Terraform | Outputs: ACR, AKS, RG, get-credentials command | 6.6 | ➖ no Azure subscription |
| 33 | `phase5-azure-portal-rg.png` | 5 Terraform | Resource group with ACR + AKS in Azure Portal | 6.7 | ➖ no Azure subscription |
| 34 | `phase6-aks-get-all.png` | 6 Kubernetes | Deployment running on AKS | 7.2 | ➖ no Azure subscription |
| 35 | `phase6-aks-app-live.png` | 6/9 Deploy | App via AKS LoadBalancer public IP (Azure deployment) | 7.3 | ➖ no Azure subscription |
| 36 | `phase7-prometheus-targets-aks.png` | 7 Monitoring | ServiceMonitor target UP on AKS | 8.3 | ➖ no Azure subscription |
| 37 | `phase7-grafana-aks.png` | 7 Monitoring | Grafana on AKS with live data under load | 8.5 | ➖ no Azure subscription |
| 38 | `phase7-hpa-scaling.png` | 7 Monitoring | HPA scaling under load (if it happens) | 8.5 | ➖ no Azure subscription |
| 39 | `phase8-ci-green.png` | 8 CI/CD | Green CI run in the Actions tab | 2.10 | ✅ |
| 40 | `phase8-ci-job-steps.png` | 8 CI/CD | CI steps: lint, tests, train, R² gate | 2.10 | ✅ |
| 41 | `phase8-cd-run.png` | 8 CI/CD | CD run: build → push → deploy → smoke test | 9.3 | ➖ no Azure subscription |
| 42 | `phase8-acr-tags.png` | 8 CI/CD | ACR images tagged v1.0.0, v1.1.0, latest | 9.3 | ➖ no Azure subscription |
| 43 | `phase8-app-new-version.png` | 8 CI/CD | App on AKS shows version 1.1.0 after CD | 9.3 | ➖ no Azure subscription |
| 44 | `phase9-streamlit-cloud.png` | 9 Deploy | Public Streamlit Community Cloud app working (standalone mode, version 1.0.0) | 10 | ✅ |

## Requirement checklist

| Requirement | Files | Screenshots | Status |
|---|---|---|---|
| Git versioning | `.gitignore`, branches `main`/`dev`/feature, PRs, tags | 10b–15 | ✅ Done |
| GitHub Actions CI/CD | `.github/workflows/ci.yml`, `cd.yml` | 39–40 (41–43 need Azure) | ✅ CI · ⚠️ CD written, skipped without Azure |
| Docker | `docker/`, `docker-compose.yml`, `.dockerignore` | 16–18 | ✅ Done |
| Kubernetes | `k8s/` | 22–29 (34–35 need Azure) | ✅ Done on minikube · AKS overlay ready |
| Terraform | `infra/terraform/` | — (30–33 need Azure) | ⚠️ Written + `validate` passes in CI, not applied |
| Prometheus / Grafana | `monitoring/`, `k8s/monitoring/`, `api/main.py` | 10, 19–21 (36–38 need Azure) | ✅ Done locally |
| Streamlit / Azure deploy | `frontend/app.py` | 44 (35, 43 need Azure) | ✅ Streamlit Cloud live · Azure not deployed |