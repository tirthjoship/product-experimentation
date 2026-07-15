# Deploying the dashboard to Streamlit Community Cloud

The dashboard is **deploy-ready**: it renders only committed `reports/*.json`, needs no
secrets, no database, and no Olist raw data. This guide is the last 5% — the final
"click deploy" requires *your* GitHub/Streamlit login, so it can't be automated.

---

## What's already prepared in the repo

| Item | File | Purpose |
|------|------|---------|
| Entry point | `dashboard/app.py` | Streamlit script (5 tabs) |
| Runtime deps (pinned) | `requirements.txt` | `streamlit`, `plotly`, `numpy`, `scipy` — exactly what render time needs |
| Theme + headless | `.streamlit/config.toml` | Light/oxblood theme; `server.headless = true` |
| Data | `reports/*.json` (committed) | All 5 JSONs the app loads are tracked in git |

Verified on 2026-06-26: `AppTest.from_file('dashboard/app.py')` boots with **0 exceptions, 0 section errors, 5 tabs**.

---

## Steps (≈ 3 minutes)

1. **Push the repo to GitHub** (public, or grant Streamlit access to a private repo).
   Make sure this branch with `requirements.txt` + `.streamlit/config.toml` is on the
   branch you'll deploy (e.g. `main`).

2. Go to **https://share.streamlit.io** → sign in with GitHub → **"Create app"** →
   **"Deploy a public app from GitHub"**.

3. Fill the form:
   - **Repository:** `tirthjoship/product-experimentation-analytics` (your repo)
   - **Branch:** `main`
   - **Main file path:** `dashboard/app.py`
   - **Advanced settings → Python version:** `3.12`

4. Click **Deploy**. First build installs `requirements.txt` (~1–2 min). The app boots
   at a URL like `https://<your-subdomain>.streamlit.app`.

5. **Copy the live URL** and paste it into the two `<APP_URL>` placeholders:
   - `README.md` — the *"Open the live dashboard ↗"* link (Dashboard section)
   - `README.md` — the **Status** line at the top (`set <APP_URL>`)

   Then update the Status line to drop "remaining: deploy …" and commit.

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
| `ModuleNotFoundError: src` or `dashboard` | Cloud puts `dashboard/` (script dir) on `sys.path`, not the repo root. `dashboard/app.py` must bootstrap the repo root onto `sys.path` before local imports (already done). Confirm **Main file path** is `dashboard/app.py` and branch is repo root. |
| A single tab shows a red "Section … schema error" | A `reports/*.json` is stale/missing on the deployed branch. Regenerate locally (`make experiment` / `scenarios` / `motivation` / `did-feasibility`) and push. Other tabs are isolated and keep working. |
| Build fails on a dependency | Confirm **Python version = 3.12** in Advanced settings (Cloud may default to a newer runtime). Pins in `requirements.txt` were verified on 3.12. |
| Want a custom subdomain | Streamlit Cloud → app settings → rename; then re-update the `<APP_URL>` links. |

---

## After deploy — résumé/portfolio hook

Once live, the project README's `<APP_URL>` resolves to a one-click demo. Pair it with the
honest-rejection narrative (the DiD natural-experiment tab) — that combination (shipped
dashboard **+** documented "we did not ship because the gate failed") is the differentiated
story for product-DS interviews.
