# Self-Healing ML Reliability Platform (SHMLRP)

A production-grade reference implementation of an end-to-end ML reliability system that detects data and performance issues, analyzes root causes, and self-heals through automated retraining and safe canary rollouts.

## Highlights
- Data contracts and quality gates with actionable failures
- Drift detection with PSI-based feature scoring
- Root-cause analysis via discriminative drift classifiers
- Automated retraining with performance and risk checks
- Canary rollout decisioning and promotion guardrails
- Incident automation, metrics logging, and lineage tracking
- API and CLI for orchestrated runs

## Architecture (High-Level)
- Data Ingestion -> Data Contracts -> Quality Gates
- Drift Detection -> Root Cause Analysis
- Baseline Training -> Performance Monitoring
- Auto-Retrain -> Canary Rollout -> Promotion or Rollback
- Observability: Metrics, Incidents, Lineage

## Quick Start

### 1) Install
```
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
```

### 2) Run the full pipeline
```
python -m shmlrp run --drift-prob 0.6 --sample-size 2000
```

### 3) Start the API
```
python -m shmlrp api --host 0.0.0.0 --port 8000
```

### 4) Open the UI dashboard
Navigate to:
```
http://127.0.0.1:8000/ui
```

The dashboard includes trend charts and run history derived from stored metrics.

### 5) Run tests
```
pytest -q
```

## Free deployment (Render)

This repo ships with a ready-to-use Render configuration in [render.yaml](self_healing_ml_reliability_platform/render.yaml).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/USERNAME/REPO)

1) Push this repository to GitHub.
2) Create a free Render account.
3) New > Web Service > Connect the repo.
4) Render will auto-detect `render.yaml` and build with:
  - `pip install -r requirements.txt && pip install -e .`
  - `python -m shmlrp api --host 0.0.0.0 --port $PORT`
5) After deploy, open `https://<your-service>.onrender.com/ui`.

Note: Render free instances sleep on inactivity. The first request may take a few seconds to wake.

## Separate frontend and backend deployment

This project supports deploying the backend and UI separately.

### Backend (Render)
Use the existing [render.yaml](self_healing_ml_reliability_platform/render.yaml). After deploy, copy the backend URL:
```
https://<your-service>.onrender.com
```

Set CORS to allow your frontend domain by adding an environment variable on Render:
```
SHMLRP_ALLOWED_ORIGINS=https://<your-frontend-domain>
```

### Frontend (Netlify / Vercel / GitHub Pages)
Deploy the static UI from:
```
src/shmlrp/web
```

Before deploying, edit [src/shmlrp/web/config.js](self_healing_ml_reliability_platform/src/shmlrp/web/config.js)
and set your backend URL:
```
window.SHMLRP_API_BASE = "https://<your-service>.onrender.com";
```

Then open:
```
https://<your-frontend-domain>
```

## CI (GitHub Actions)

Continuous integration runs on every push and pull request using the workflow in
[.github/workflows/ci.yml](self_healing_ml_reliability_platform/.github/workflows/ci.yml).

## Outputs
Artifacts are stored in `artifacts/` and include:
- Data snapshots
- Model artifacts and metadata
- Pipeline reports
- Metrics, incidents, and lineage logs

## Project Layout
```
src/shmlrp/
  api/
  causal/
  data/
  drift/
  incident/
  model/
  monitoring/
  orchestration/
  rollout/
  logging_config.py
  config.py
  utils.py
```

## Notes
- The pipeline uses synthetic data by default to support reproducible end-to-end testing.
- The root-cause analysis is a proxy based on discriminative feature importance.
