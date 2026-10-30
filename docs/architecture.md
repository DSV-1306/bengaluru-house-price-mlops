# Architecture

## Flow

1. **Code & data** live in GitHub. `main` is protected; work happens on `feature/*` → PR → `dev` → PR → `main`.
2. **CI** runs on every push/PR: lint, tests (incl. API + frontend), full model training, an R² ≥ 0.80
   quality gate, Docker builds and Terraform validation.
3. **Terraform** (`infra/terraform`) creates the Azure resource group, Container Registry, AKS cluster,
   the AcrPull role for AKS, and a managed identity with a GitHub OIDC federated credential for CD.
4. **CD** runs on a version tag: logs in to Azure with OIDC, builds both images (the API image trains the
   model at build time with `MODEL_VERSION=<tag>`), pushes them to ACR, applies the Kustomize `aks` overlay,
   waits for the rollout, smoke-tests `/health`, and rolls back on failure.
5. **AKS** runs the API (2–5 replicas, HPA on 70 % CPU, liveness/readiness probes) behind a ClusterIP
   service, and the Streamlit frontend behind a public LoadBalancer.
6. **Monitoring**: kube-prometheus-stack (Helm) scrapes the API's `/metrics` via a ServiceMonitor; Grafana
   shows the provisioned dashboard. Locally the same dashboard runs in docker-compose.
7. **Streamlit Community Cloud** runs `frontend/app.py` in standalone mode (no API; loads/trains the model).

## Components

| Component | Tech | Files |
|---|---|---|
| ML pipeline | pandas, scikit-learn (Ridge, log-log) | `src/` |
| API | FastAPI, Pydantic, prometheus-fastapi-instrumentator | `api/main.py` |
| UI | Streamlit | `frontend/app.py` |
| Containers | Docker (multi-stage, non-root, HEALTHCHECK) | `docker/`, `docker-compose.yml` |
| Orchestration | Kubernetes + Kustomize overlays | `k8s/` |
| Infrastructure | Terraform (azurerm) | `infra/terraform/` |
| CI/CD | GitHub Actions + OIDC | `.github/workflows/` |
| Monitoring | Prometheus, Grafana | `monitoring/`, `k8s/monitoring/` |

## Secrets

No secret is committed. `.env` (Grafana password), `terraform.tfvars` and Terraform state are git-ignored;
CD uses OIDC (only IDs are stored as GitHub secrets); AKS pulls from ACR via a role assignment (no registry
password); the Grafana admin password on AKS lives in the `monitoring-grafana` Kubernetes Secret.
