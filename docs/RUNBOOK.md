# Runbook — exact steps, in order

Project folder: `C:\Users\Dhruva\OneDrive\Documents\Desktop\Projects\bengaluru-house-price-mlops`

Every command below is typed into **Claude's terminal** (PowerShell). Do the parts **in order** — later parts
use things created earlier (images, the GitHub repo, Azure resources).

## How to take every screenshot (same 3 steps each time)

1. `cls` (clears the screen), then run the command / open the page.
2. Press **Win + Shift + S**, drag a box over the output or browser window (it is now on the clipboard).
3. Run the save command shown with a 📸, e.g.
   ```powershell
   powershell -STA -File scripts\save-screenshot.ps1 phase2-fastapi-docs
   ```
   It saves `docs\screenshots\phase2-fastapi-docs.png`. If it says *No image on the clipboard*, snip again.

Browser pages: open them in Chrome (or any browser), snip with Win + Shift + S, then run the save command in the terminal.

## Every time you open a NEW terminal tab, run these 3 lines first

```powershell
cd C:\Users\Dhruva\OneDrive\Documents\Desktop\Projects\bengaluru-house-price-mlops
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

---

## Part 0 — Before you start

**0.1 Stop your other Streamlit app.** You have another project running from `D:\Downloads\bengaluru-mlops`
(`streamlit run src/app.py`) on port 8501. Go to the terminal where it runs and press **Ctrl + C**,
otherwise ports clash.

**0.2 Free disk space — move Docker and minikube to D:** (your C: had only 2.5 GB free; Docker needs ~4 GB
for this project's images and minikube ~6 GB more. D: has 130+ GB free.)

1. Open **Docker Desktop** → ⚙️ **Settings** → **Resources** → **Advanced** → **Disk image location** →
   **Browse** → create/select `D:\DockerData` → **Apply & restart**. Docker moves its disk (and the images
   already built) to D:. This takes a few minutes.
2. Keep minikube's files on D: too — run once, then **close and reopen the terminal**:
   ```powershell
   [Environment]::SetEnvironmentVariable("MINIKUBE_HOME", "D:\minikube", "User")
   ```
3. Check free space (C: should not be the drive filling up any more):
   ```powershell
   Get-PSDrive C, D | Select-Object Name, @{n="FreeGB";e={[math]::Round($_.Free/1GB,1)}}
   ```

**0.3 Start Docker Desktop** from the Start menu. Accept any terms/sign-in screen and wait until it says
**Engine running**. Check:
```powershell
docker info --format "Docker engine: {{.ServerVersion}}"
```
*If Docker Desktop shows an error and closes* (log says `dockerInference ... The file cannot be accessed by the system`):
quit Docker Desktop completely, run the line below (renames a folder of stale socket files; Docker recreates it), then start Docker Desktop again:
```powershell
Rename-Item "$env:LOCALAPPDATA\Docker\run" "run.old-$(Get-Date -Format yyyyMMddHHmm)"
```
*If `docker` commands answer `500 Internal Server Error`*: the disk is full or the engine is stuck — do 0.2, then
right-click the Docker whale icon in the taskbar → **Restart**.

**0.4 Install GitHub CLI** (the only tool still missing), then **close and reopen the terminal** and run the 3 lines above:
```powershell
winget install -e --id GitHub.cli
```

**0.5 All versions** (📸 Phase 0):
```powershell
cls
python --version; git --version; docker --version; docker compose version; kubectl version --client; minikube version --short; helm version --short; terraform version; az version --output table; gh --version
```
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase0-tool-versions`

**0.6 Phase 1 screenshots** (model training / tests / notebook) — if not done yet, follow the "Screenshot 1–4"
instructions from earlier; commands are in the README section *Run locally*.

---

## Part 1 — Run the API and the Streamlit UI locally (no Docker)

**1.1 Train the model** (≈4 min; creates `models\model.joblib`, `columns.json`, `metrics.json`):
```powershell
python -m src.train
```

**1.2 Start the API** — leave this terminal running:
```powershell
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

**1.3 Open a NEW terminal tab** (+ the 3 setup lines), then start the UI.
Use `127.0.0.1`, not `localhost` (on Windows `localhost` adds a 2-second delay per request):
```powershell
$env:API_URL = "http://127.0.0.1:8000"
streamlit run frontend/app.py --server.port 8501
```

**1.4 Screenshots in the browser:**

| Open this | Do this | 📸 save command |
|---|---|---|
| http://127.0.0.1:8000/docs | page with the 5 endpoints | `powershell -STA -File scripts\save-screenshot.ps1 phase2-fastapi-docs` |
| same page | open **POST /predict** → *Try it out* → *Execute* → snip the 200 response | `powershell -STA -File scripts\save-screenshot.ps1 phase2-predict-call` |
| http://127.0.0.1:8501 | home page (sidebar shows Ridge, R² 0.845) | `powershell -STA -File scripts\save-screenshot.ps1 phase2-streamlit-home` |
| same page | click **Predict price**, scroll so result + chart show | `powershell -STA -File scripts\save-screenshot.ps1 phase2-streamlit-prediction` |
| http://127.0.0.1:8000/metrics | scroll to `predictions_total` lines | `powershell -STA -File scripts\save-screenshot.ps1 phase2-metrics` |

**1.5 Stop both servers:** press **Ctrl + C** in each of the two terminals.

---

## Part 2 — Git & GitHub versioning

**2.1 Tell git who you are** (only once per laptop; use your own name/email):
```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

**2.2 Log in to GitHub** (opens the browser; choose GitHub.com → HTTPS → login with browser):
```powershell
gh auth login --hostname github.com --git-protocol https --web --scopes workflow
```

**2.3 Create the local repo and the first commit:**
```powershell
git init -b main
git add .
git status
git commit -m "feat: production-style MLOps project for Bengaluru house prices"
```
Check that `git status` did **not** list `.venv`, `models/*.joblib`, `.env`, `terraform.tfvars` (they are git-ignored).

**2.4 Create the GitHub repo and push** (CI starts automatically on this push):
```powershell
gh repo create bengaluru-house-price-mlops --public --source . --remote origin --push
```

**2.5 Save your GitHub username in a variable** (used below):
```powershell
$GH_USER = gh api user --jq .login
$GH_USER
```

**2.6 Protect `main`** (changes must come through a Pull Request):
```powershell
'{"required_status_checks":null,"enforce_admins":false,"required_pull_request_reviews":{"required_approving_review_count":0},"restrictions":null}' | Out-File -Encoding ascii protection.json
gh api -X PUT "repos/$GH_USER/bengaluru-house-price-mlops/branches/main/protection" --input protection.json
Remove-Item protection.json
```

**2.7 Create the `dev` branch:**
```powershell
git checkout -b dev
git push -u origin dev
```

**2.8 Feature branch → PR → merge** (the small change = put your username into the README badges):
```powershell
git checkout -b feature/readme-badges
(Get-Content README.md -Encoding UTF8) -replace 'YOUR_GITHUB_USERNAME', $GH_USER | Set-Content README.md -Encoding UTF8
git add README.md
git commit -m "docs: add CI badge and repo links to README"
git push -u origin feature/readme-badges
gh pr create --base dev --head feature/readme-badges --title "docs: add CI badge and repo links" --body "Adds the CI status badge and repository links."
gh pr merge feature/readme-badges --merge --delete-branch
```
📸 Before merging you can open the PR page: `gh pr view feature/readme-badges --web` (snip it →
`powershell -STA -File scripts\save-screenshot.ps1 phase3-pull-request`). If already merged, the PR page still shows "Merged" — that's fine.

**2.9 Release PR `dev` → `main`, then tag v1.0.0:**
```powershell
gh pr create --base main --head dev --title "release: v1.0.0" --body "First release: model, API, UI, Docker, K8s, Terraform, CI/CD."
gh pr merge dev --merge
git checkout main
git pull
git tag -a v1.0.0 -m "v1.0.0 - first release"
git push origin v1.0.0
gh release create v1.0.0 --title "v1.0.0" --notes "First release. Model: Ridge (log-log), test R2 0.845."
```
> **Versioning rule:** the git tag (`v1.0.0`) is THE version. CD builds the Docker images tagged `v1.0.0`
> and passes `MODEL_VERSION=1.0.0` into training, so `models/metrics.json` → `"version": "1.0.0"`,
> which the API (`/health`, `/model-info`) and the Streamlit sidebar show. One number everywhere.
>
> The tag also starts the **CD** workflow — it will show as **skipped** for now (Azure isn't set up yet). That's expected.

**2.10 Screenshots** (`gh repo view --web` opens the repo in the browser):

| Open | 📸 save command |
|---|---|
| repo home page (`gh repo view --web`) | `powershell -STA -File scripts\save-screenshot.ps1 phase3-github-repo` |
| *Commits* (click the "N commits" link) | `powershell -STA -File scripts\save-screenshot.ps1 phase3-commit-history` |
| *Branches* (click "branches") — shows main (protected) + dev | `powershell -STA -File scripts\save-screenshot.ps1 phase3-branches` |
| *Releases* / *Tags* (right sidebar → Releases) | `powershell -STA -File scripts\save-screenshot.ps1 phase3-tags-releases` |
| *Actions* tab → the green **CI** run | `powershell -STA -File scripts\save-screenshot.ps1 phase8-ci-green` |
| click into that CI run → the job **Lint, test, train, quality gate** with steps expanded | `powershell -STA -File scripts\save-screenshot.ps1 phase8-ci-job-steps` |

CI takes ~6–8 min. Watch it from the terminal: `gh run watch` (pick the CI run).

---

## Part 3 — Docker

**3.1 Build the images** (API build trains the model inside the image). Both images were already built
once on this laptop (`house-price-api:1.0.0`, `house-price-frontend:1.0.0`); running the commands again is
quick because Docker reuses its cache. On a slow connection a fresh build can take ~20 min.
```powershell
docker build -f docker/Dockerfile.api --build-arg MODEL_VERSION=1.0.0 -t house-price-api:1.0.0 .
docker build -f docker/Dockerfile.frontend -t house-price-frontend:1.0.0 .
```

**3.2 List them:**
```powershell
cls
docker images --filter "reference=house-price-*"
```
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase4-docker-images`

**3.3 Create `.env` with your Grafana password** (git-ignored — never committed):
```powershell
Copy-Item .env.example .env
notepad .env
```
Change `GRAFANA_ADMIN_PASSWORD=change-me` to a password of your choice, save, close Notepad.

**3.4 Start the whole stack** (API + UI + Prometheus + Grafana):
```powershell
docker compose up -d
cls
docker compose ps
```
Wait until `house-price-api` shows `(healthy)` (run `docker compose ps` again after ~30 s).
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase4-compose-ps`

**3.5 App from containers:** open http://localhost:8501 → click **Predict price**.
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase4-app-in-docker`

---

## Part 4 — Prometheus + Grafana (local, via docker compose)

**4.1 Generate traffic** so graphs have data:
```powershell
python scripts\load_test.py --url http://127.0.0.1:8000 --requests 3000 --workers 20
```

**4.2 Prometheus targets:** open http://localhost:9090/targets → `house-price-api` is **UP**.
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase7-prometheus-targets-local`

**4.3 A PromQL query:** open http://localhost:9090/graph → paste
`topk(10, sum by (location) (predictions_total))` → **Execute** → *Table* tab.
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase7-promql-query`

**4.4 Grafana:** open http://localhost:3000 → user `admin`, password = the one in your `.env` →
*Dashboards* → folder **House Price** → **Bengaluru House Price API**. Run 4.1 again while it is open so the graphs move.
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase7-grafana-local`

---

## Part 5 — Kubernetes on your laptop (minikube)

**5.1 Start minikube and enable metrics (needed for the HPA):**
```powershell
minikube start --driver=docker --cpus=2 --memory=4096
minikube addons enable metrics-server
```

**5.2 Copy the images into minikube and deploy:**
```powershell
minikube image load house-price-api:1.0.0
minikube image load house-price-frontend:1.0.0
kubectl apply -k k8s/overlays/local
kubectl -n house-price rollout status deployment/house-price-api
```

**5.3 Management commands — one screenshot each** (`cls` before each):

| Command | 📸 save command |
|---|---|
| `kubectl get all -n house-price` | `powershell -STA -File scripts\save-screenshot.ps1 phase6-get-all` |
| `kubectl describe pod -n house-price -l app=house-price-api` (snip the top: image, probes, limits, Events) | `powershell -STA -File scripts\save-screenshot.ps1 phase6-describe-pod` |
| `kubectl logs -n house-price deployment/house-price-api --tail=20` | `powershell -STA -File scripts\save-screenshot.ps1 phase6-logs` |
| `kubectl scale deployment house-price-api -n house-price --replicas=3` then `kubectl get pods -n house-price` | `powershell -STA -File scripts\save-screenshot.ps1 phase6-scale` |
| `kubectl get hpa -n house-price` (wait ~1 min until TARGETS shows a % instead of `<unknown>`) | `powershell -STA -File scripts\save-screenshot.ps1 phase6-hpa` |

(The HPA owns the replica count, so after a few minutes it brings 3 back to 2 — that's correct behaviour.)

**5.4 Rolling update and rollback** — build a v1.0.1 image, roll it out, then undo:
```powershell
docker build -f docker/Dockerfile.api --build-arg MODEL_VERSION=1.0.1 -t house-price-api:1.0.1 .
minikube image load house-price-api:1.0.1
cls
kubectl set image deployment/house-price-api api=house-price-api:1.0.1 -n house-price
kubectl rollout status deployment/house-price-api -n house-price
kubectl rollout history deployment/house-price-api -n house-price
```
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase6-rolling-update`
```powershell
cls
kubectl rollout undo deployment/house-price-api -n house-price
kubectl rollout status deployment/house-price-api -n house-price
kubectl get deployment house-price-api -n house-price -o wide
```
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase6-rollout-undo` (IMAGES column is back to `house-price-api:1.0.0`)

**5.5 Open the app from minikube** (opens the browser; keep the terminal open, Ctrl + C when done):
```powershell
minikube service house-price-frontend -n house-price
```
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase6-app-minikube`

---

## Part 6 — Terraform: create Azure infrastructure (costs money — read first)

**What gets created** (8 resources): resource group, Container Registry (Basic), AKS cluster (Free tier, 1 × Standard_B2s node),
AcrPull role (AKS → ACR), and for CD: a managed identity + GitHub OIDC federated credential + Contributor role on the resource group.

**Estimated cost** (pay-as-you-go, approximate): B2s node ≈ $1.0/day · AKS load balancer + public IPs ≈ $0.7/day ·
OS disk ≈ $0.2/day · ACR Basic ≈ $0.17/day → **≈ $2–2.5 per day (~₹200/day)** from your Azure for Students credit.
**Destroy it as soon as your evaluation is done** (Part 10). AKS control plane (Free tier) costs $0.

**6.1 Log in and pick the subscription:**
```powershell
az login
az account show --output table
```
If you have more than one subscription: `az account list --output table` then `az account set --subscription "<name>"`.

**6.2 Register the providers (one time, ~1–2 min) and check the VM size is allowed:**
```powershell
az provider register --namespace Microsoft.ContainerService --wait
az provider register --namespace Microsoft.ContainerRegistry --wait
az provider register --namespace Microsoft.ManagedIdentity --wait
az vm list-skus --location centralindia --size Standard_B2s --all --output table
```
The `Restrictions` column must say **None**. If it says `NotAvailableForSubscription`, use `Standard_B2ms`
or `Standard_D2s_v3` in step 6.3 (check those the same way).

**6.3 Create your `terraform.tfvars`** (git-ignored):
```powershell
cd infra\terraform
Copy-Item terraform.tfvars.example terraform.tfvars
az account show --query id -o tsv
notepad terraform.tfvars
```
In Notepad: paste the subscription ID that was printed into `subscription_id`, and replace `YOUR_GITHUB_USERNAME`
with your GitHub username (same as `$GH_USER`, exact upper/lower case). Save and close.

**6.4 Init, format, validate, plan:**
```powershell
terraform init
terraform fmt
terraform validate
cls
terraform plan -out tfplan
```
The last line must say **`Plan: 8 to add, 0 to change, 0 to destroy.`**
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase5-terraform-plan`

> **STOP here and decide.** Only continue if you accept the cost above.

**6.5 Apply** (≈5–10 min):
```powershell
terraform apply tfplan
```
📸 when it prints `Apply complete! Resources: 8 added` → `powershell -STA -File scripts\save-screenshot.ps1 phase5-terraform-apply`

If it fails with `RequestDisallowedByPolicy` (region not allowed for your subscription): change `location` in
`terraform.tfvars` to an allowed region (see `az policy assignment list --query "[].displayName" -o table`,
typical student regions: `southindia`, `eastus`, `westeurope`), then rerun 6.4 and 6.5.

**6.6 Outputs and cluster credentials:**
```powershell
cls
terraform output
```
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase5-terraform-output`
```powershell
$ACR = terraform output -raw acr_login_server
$ACR_NAME = terraform output -raw acr_name
$RG = terraform output -raw resource_group_name
$AKS = terraform output -raw aks_name
az aks get-credentials --resource-group $RG --name $AKS --overwrite-existing
kubectl get nodes
cd ..\..
```

**6.7 Azure Portal:** open https://portal.azure.com → *Resource groups* → `rg-hpmlops` (shows the ACR, AKS, identity).
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase5-azure-portal-rg`

---

## Part 7 — Deploy to AKS (Kubernetes on Azure)

`kubectl` now points at AKS (check: `kubectl config current-context` shows `aks-hpmlops`;
switch back to the laptop cluster any time with `kubectl config use-context minikube`).

**7.1 Push the v1.0.0 images to ACR:**
```powershell
az acr login --name $ACR_NAME
docker tag house-price-api:1.0.0 "$ACR/house-price-api:v1.0.0"
docker tag house-price-frontend:1.0.0 "$ACR/house-price-frontend:v1.0.0"
docker push "$ACR/house-price-api:v1.0.0"
docker push "$ACR/house-price-frontend:v1.0.0"
```

**7.2 Deploy the AKS overlay** (fills in your registry name and the tag):
```powershell
(kubectl kustomize k8s/overlays/aks) -replace 'ACR_LOGIN_SERVER', $ACR -replace 'IMAGE_TAG', 'v1.0.0' | kubectl apply -f -
kubectl -n house-price rollout status deployment/house-price-api --timeout=300s
cls
kubectl get all -n house-price
```
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase6-aks-get-all`

**7.3 Public URL:**
```powershell
kubectl get svc house-price-frontend -n house-price
```
Repeat until `EXTERNAL-IP` is an IP (1–3 min). Open `http://<EXTERNAL-IP>` in the browser → Predict.
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase6-aks-app-live`

---

## Part 8 — Prometheus + Grafana on AKS

**8.1 Install kube-prometheus-stack** (≈3–5 min):
```powershell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace -f monitoring/kube-prometheus-values.yaml --wait --timeout 10m
kubectl get pods -n monitoring
```

**8.2 Scrape the API + load the dashboard:**
```powershell
kubectl apply -f k8s/monitoring/servicemonitor.yaml
kubectl create configmap house-price-dashboard -n monitoring --from-file=house-price.json=monitoring/grafana/dashboards/house-price.json
kubectl label configmap house-price-dashboard -n monitoring grafana_dashboard=1
```

**8.3 Open Prometheus** — in a NEW terminal tab (+3 setup lines), leave running:
```powershell
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9091:9090
```
Open http://localhost:9091/targets → `serviceMonitor/monitoring/house-price-api/0` shows **2/2 up** (wait ~1 min).
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase7-prometheus-targets-aks`

**8.4 Grafana admin password** (read from the Kubernetes Secret — printed only on your screen, never saved):
```powershell
kubectl get secret -n monitoring monitoring-grafana -o jsonpath="{.data.admin-password}" | ForEach-Object { [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($_)) }
```
In another NEW terminal tab (+3 setup lines), leave running:
```powershell
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
```

**8.5 Load on AKS** — another NEW terminal tab (+3 setup lines), leave running:
```powershell
kubectl port-forward -n house-price svc/house-price-api 8001:8000
```
Back in the main terminal:
```powershell
python scripts\load_test.py --url http://127.0.0.1:8001 --requests 20000 --workers 40
```
While it runs: open http://localhost:3001 (user `admin`, password from 8.4) → *Dashboards* → **Bengaluru House Price API**.
📸 `powershell -STA -File scripts\save-screenshot.ps1 phase7-grafana-aks`

Also watch the HPA during the load:
```powershell
kubectl get hpa -n house-price
```
📸 if REPLICAS goes above 2: `powershell -STA -File scripts\save-screenshot.ps1 phase7-hpa-scaling`
(With one small node it may not scale — the spec says "if it happens"; screenshot whatever it shows.)

Stop the 3 port-forwards with **Ctrl + C** when done.

---

## Part 9 — GitHub Actions CD to AKS

Terraform already created the Azure identity + OIDC federated credential (no password is stored anywhere).
Show it:
```powershell
az identity federated-credential list --identity-name id-hpmlops-github-cd --resource-group rg-hpmlops --output table
```

**9.1 Put the IDs into GitHub** (secrets are encrypted; values are never printed):
```powershell
cd infra\terraform
gh secret set AZURE_CLIENT_ID --body (terraform output -raw github_cd_client_id)
gh secret set AZURE_TENANT_ID --body (terraform output -raw azure_tenant_id)
gh secret set AZURE_SUBSCRIPTION_ID --body (az account show --query id -o tsv)
gh variable set ACR_NAME --body (terraform output -raw acr_name)
gh variable set AKS_RESOURCE_GROUP --body (terraform output -raw resource_group_name)
gh variable set AKS_CLUSTER_NAME --body (terraform output -raw aks_name)
cd ..\..
gh secret list
gh variable list
```

**9.2 A change through the full workflow → release v1.1.0:**
```powershell
git checkout dev
git pull
git checkout -b feature/live-links
notepad README.md
```
In Notepad, in the **Live links** section replace `AKS_EXTERNAL_IP` with your EXTERNAL-IP from 7.3. Save, close.
```powershell
git add README.md
git commit -m "docs: add live AKS URL"
git push -u origin feature/live-links
gh pr create --base dev --head feature/live-links --title "docs: add live AKS URL" --body "Adds the public AKS URL."
gh pr checks feature/live-links --watch
gh pr merge feature/live-links --merge --delete-branch
gh pr create --base main --head dev --title "release: v1.1.0" --body "Release v1.1.0"
gh pr checks dev --watch
gh pr merge dev --merge
git checkout main
git pull
git tag -a v1.1.0 -m "v1.1.0"
git push origin v1.1.0
gh release create v1.1.0 --title "v1.1.0" --generate-notes
gh run list --workflow cd.yml
gh run watch
```
(`gh run watch` → choose the **CD** run. It builds, pushes, deploys and smoke-tests in ~6–8 min.)

**9.3 Screenshots:**

| Open | 📸 save command |
|---|---|
| GitHub → *Actions* → **CD** run (green, all steps) | `powershell -STA -File scripts\save-screenshot.ps1 phase8-cd-run` |
| terminal: `az acr repository show-tags --name $ACR_NAME --repository house-price-api --output table` (shows v1.0.0, v1.1.0, latest) — or Portal → Container registry → Repositories | `powershell -STA -File scripts\save-screenshot.ps1 phase8-acr-tags` |
| `http://<EXTERNAL-IP>` → sidebar **Version 1.1.0** | `powershell -STA -File scripts\save-screenshot.ps1 phase8-app-new-version` |

If a new terminal lost `$ACR_NAME`: `$ACR_NAME = terraform -chdir=infra/terraform output -raw acr_name`.

---

## Part 10 — Streamlit Community Cloud (public URL, free)

1. Open https://share.streamlit.io → **Sign in with GitHub**.
2. **Create app** → *Deploy a public app from GitHub*.
3. Repository: `YOUR_USERNAME/bengaluru-house-price-mlops` · Branch: `main` · Main file path: `frontend/app.py`.
4. **Advanced settings** → Python version **3.11** → Save. No secrets needed (no `API_URL` → standalone mode;
   it installs the root `requirements.txt` and trains a quick model on first start, ~1 min).
5. **Deploy**. When the app loads, click **Predict price**.

📸 `powershell -STA -File scripts\save-screenshot.ps1 phase9-streamlit-cloud`
Put the URL into README → *Live links* (same feature-branch → PR flow as 9.2, or edit on GitHub via a PR).

The Azure deployment is the AKS LoadBalancer URL from Part 7 (📸 `phase6-aks-app-live` / `phase8-app-new-version`).

---

## Part 11 — Teardown (do this after your evaluation!)

```powershell
cd C:\Users\Dhruva\OneDrive\Documents\Desktop\Projects\bengaluru-house-price-mlops\infra\terraform
terraform destroy
```
Type `yes`. Takes ~5–10 min and deletes **everything in Azure** (AKS, ACR, identity, resource group).
Check: `az group list --output table` must not list `rg-hpmlops`.

```powershell
cd ..\..
minikube delete
docker compose down -v
```
