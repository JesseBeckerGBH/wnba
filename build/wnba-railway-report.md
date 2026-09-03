# WNBA Railway preview report

Date: 2026-09-03 13:52 PT
Branch: `run/wnba-v1` (PR #5, **not merged**)

## Commit SHA

Latest preview commit: `b8442f236a49eb408bf451a91b659d1f95c1da58`

Follow-ups on the same branch:
- `d09a337` libgomp1 for LightGBM
- `71fdb4f` attempted python:3.14 image (working tree + this report keep **python:3.12-slim-bookworm**, which is what Railway actually built)
- `5beee62` earlier docs note

HEAD at report write: see `git log -1` on `origin/run/wnba-v1` after this commit.

## Orientation (do not flip)

**`--home` is P(home win).** `predict_proba[:, 1]` matches training target `home_win`. Labels are not favorites.

- Aces @ home vs Liberty: **26.7%** home win / 73.3% away
- Liberty @ home vs Aces: **79.3%** home win / 20.7% away

## Files (this preview)

Committed for Railway (pickle + JSON only at boot; no DuckDB/nba_api/ingest):

- `requirements.txt` — `scikit-learn==1.7.2`, fastapi, uvicorn
- `requirements-api.txt` — slim deploy deps, sklearn==1.7.2
- `api/app.py` — FastAPI GET `/health`, POST `/predict`; joblib.load pickle; rebuilds `ml_vec` from JSON
- `api/team_features.json` — convenience copy
- `model/artifacts/team_features.json` — 15 teams / 30 name+abbrev keys / 840 h2h pairs
- `model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.pkl` + `.json`
- `scripts/export_team_features.py` — one-shot DuckDB export
- `Dockerfile` — `python:3.12-slim-bookworm`, libgomp1, COPY api + artifacts pkl/json, PORT, MODEL_PATH, FEATURES_PATH
- `.dockerignore` — venv, __pycache__, .env, db/*.duckdb, .git
- `.env.example` — PORT=, MODEL_PATH=, FEATURES_PATH= (names only)
- `build/smoke-health.json`
- `build/smoke-predict-aces-home.json`
- `build/smoke-predict-liberty-home.json`

Not committed (per job): `scripts/odds_client.py`, `scripts/todays_bets.py`, `scripts/capture_closing_lines.py`.

## Railway

`railway whoami`: Logged in as Jesse Becker (jessebecker2021@gmail.com). **Not blocked.**

- Project: https://railway.com/project/0d878d4d-7d20-4150-9502-c706ea9e3772
- Public HTTPS: **https://wnba-production-de94.up.railway.app**
- Live `/health` `features_path`: `/app/model/artifacts/team_features.json`

## Sample JSON (live POST /predict)

Aces @ home vs Liberty:

```json
{"home":"Aces","away":"Liberty","home_win_prob":0.2667741763716996,"away_win_prob":0.7332258236283005,"ml_version":"v_20260617_172452_moneyline","ml_auc":0.7523,"orientation":"orientation OK: --home is P(home win); model disagrees with market","impl_home":0.27027027027027023,"ml_edge_home":-0.0034960938985706402,"ml_home":3.7,"impl_away":0.7692307692307692,"ml_edge_away":-0.036004945602468696,"ml_away":1.3,"total_line":162.5,"note_totals":"totals pickle not scored in pickle-only moneyline app","over_odds":1.91,"under_odds":1.91}
```

Liberty @ home vs Aces: `home_win_prob` 0.7929250466066644 (79.3%).

## Local smoke

uvicorn :8000 matched live: Aces@home 26.7%, Liberty@home 79.3%. sklearn 1.7.2 in venv. API does not import duckdb.
