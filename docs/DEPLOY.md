# Deploying the dashboard to Streamlit Community Cloud

**Live app:** [product-experimentation-analytics.streamlit.app](https://product-experimentation-analytics.streamlit.app/)

The dashboard renders only committed `reports/*.json` — no secrets, no database, and no Olist
raw data. Use this guide to redeploy, fork, or troubleshoot.

---

## What's in the repo

| Item | File | Purpose |
|------|------|---------|
| Entry point | `dashboard/app.py` | Streamlit script (5 tabs) |
| Runtime deps (pinned) | `requirements.txt` | `streamlit`, `plotly`, `numpy`, `scipy` — exactly what render time needs |
| Theme + headless | `.streamlit/config.toml` | Light/oxblood theme; `server.headless = true` |
| Data | `reports/*.json` (committed) | All 5 JSONs the app loads are tracked in git |
| Import bootstrap | `dashboard/app.py` (top) | Inserts repo root on `sys.path` for Cloud |

Verified: `AppTest.from_file('dashboard/app.py')` boots with **0 exceptions, 0 section errors, 5 tabs**.

---

## Deploy or redeploy (≈ 3 minutes)

1. **Push the repo to GitHub** (public, or grant Streamlit access to a private repo).

2. Go to **https://share.streamlit.io** → sign in with GitHub → **"Create app"** →
   **"Deploy a public app from GitHub"**.

3. Fill the form:
   - **Repository:** `tirthjoship/product-experimentation-analytics`
   - **Branch:** `main`
   - **Main file path:** `dashboard/app.py`
   - **Advanced settings → Python version:** `3.12`

4. Click **Deploy**. First build installs `requirements.txt` (~1–2 min).

---

## Why these deps and not the full pipeline

The offline analysis pipeline (`src/`) uses pandas, duckdb, statsmodels, matplotlib to
*generate* the reports. The deployed dashboard never recomputes — it reads the committed
JSON — so it only needs:

- `streamlit`, `plotly` — UI + charts
- `numpy`, `scipy` — pulled in by `src.experiment.power` (the analytical MDE calculator tab)

Keeping `requirements.txt` minimal makes the Cloud build fast and avoids resolver conflicts.

---

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `ModuleNotFoundError: src` or `dashboard` | Cloud puts `dashboard/` (script dir) on `sys.path`, not the repo root. `dashboard/app.py` bootstraps the repo root before local imports (already on `main`). Confirm **Main file path** is `dashboard/app.py`. |
| A single tab shows a red "Section … schema error" | A `reports/*.json` is stale/missing on the deployed branch. Regenerate locally (`make experiment` / `scenarios` / `motivation` / `did-feasibility`) and push. Other tabs are isolated and keep working. |
| Build fails on a dependency | Confirm **Python version = 3.12** in Advanced settings (Cloud may default to a newer runtime). Pins in `requirements.txt` were verified on 3.12. |
| Want a custom subdomain | Streamlit Cloud → app settings → rename; then update the dashboard link in `README.md`. |

---

## Portfolio hook

Pair the live dashboard with the honest-rejection narrative (DiD natural-experiment tab) —
shipped dashboard **plus** documented "we did not ship because the gate failed" is the
differentiated story for product analytics interviews.
