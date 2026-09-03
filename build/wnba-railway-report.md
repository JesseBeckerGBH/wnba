# WNBA Railway report

Date: 2026-09-03 13:55 PT

## Orientation

**orientation OK: --home is P(home win); model disagrees with market.**

- CLI `--home` is the home team. `home_win_prob = model.predict_proba(X)[0][1]` = P(class=1) = P(home win). Training target in `stack_train.py` is `home_win`. Features are home-minus-away diffs plus `home_advantage=1.0`.
- Market: Aces 1.65 favorite vs Liberty 2.30. Model with Aces at home: **26.7% / 73.3%**. Swapped (Liberty home, odds swapped so Aces keep 1.65): Liberty **79.3%**, Aces **20.7%**. Home-court bump is ~6pp; Liberty is the model favorite in both orientations. **Did not invert predict.py.**
- sklearn InconsistentVersionWarning gone after pin to 1.7.2. Residual XGBoost pickle warning only (not pinned; no re-save).

## sklearn choice

Pinned **scikit-learn==1.7.2** in `requirements.txt` and `requirements-api.txt` (pickle trained on 1.7.2). Local venv `D:\WNBA\venv\Scripts\python.exe` is CPython 3.14.5; pip confirmed sklearn 1.7.2. Did **not** re-save pickle. Pickle loads as `CalibratedClassifierCV` with classes `[0, 1]`.

## Image

- Dockerfile: **python:3.12-slim-bookworm**. Task allows 3.12 or 3.14. Local venv that loads the pickle is 3.14; Railway image is 3.12 so manylinux sklearn/xgboost/lightgbm wheels install cleanly. Live Railway unpickle succeeded on 3.12.
- `libgomp1` installed for LightGBM.
- Slim API deps only (`requirements-api.txt`): sklearn 1.7.2, numpy, joblib, xgboost, lightgbm, fastapi, uvicorn, pydantic. Not full repo requirements (winotify is Windows-only; no DuckDB/nba_api on boot).
- COPY pickle `model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.pkl` + json sidecar + `api/` + `model/artifacts/team_features.json`.
- ENV PORT, MODEL_PATH, FEATURES_PATH, TEAM_FEATURES_PATH. CMD: `uvicorn api.app:app --host 0.0.0.0 --port $PORT`.

## Files added / changed (deploy)

- `api/app.py`, `api/__init__.py`, `api/team_features.json` (pickle-only FastAPI: GET /health, POST /predict)
- `Dockerfile`, `.dockerignore`, `requirements-api.txt`
- `requirements.txt` sklearn==1.7.2 + fastapi/uvicorn
- `.env.example` names only: PORT, MODEL_PATH, FEATURES_PATH, TEAM_FEATURES_PATH
- moneyline pickle+json + team_features.json (gitignore `model/artifacts/*` with negations)
- `build/wnba-sample/orientation-check.txt`
- `build/wnba-sample/railway-predict.json`
- `build/wnba-railway-report.md`

Not committed: `scripts/odds_client.py`, `scripts/todays_bets.py`, `scripts/capture_closing_lines.py`.

## Local smoke

uvicorn on 127.0.0.1:8090 (venv 3.14, sklearn 1.7.2). GET /health 200. POST /predict Aces home vs Liberty: home_win_prob 0.26677 (26.7%). No duckdb in sys.modules on boot.

## Git

Branch `run/wnba-v1` (PR #5, **not merged**).

- a899b86 feat: pickle-only FastAPI predict API and sklearn 1.7.2 pin
- d09a337 fix: install libgomp1 so LightGBM can unpickle in Docker
- b8442f2 feat: export team features JSON and pickle-only FEATURES_PATH API
- 71fdb4f5d20b7e4fc9f6ff0f785e6b2b28ed34bc Use Python 3.14 in Docker to match sklearn 1.7.2 pickle load (later kept 3.12 for Railway linux wheels)

## Railway

Logged in as Jesse Becker (jessebecker2021@gmail.com).

- Project **wnba** (did not touch other sports / Stripe / domain / dashboard / retrain / merge).
- Project: https://railway.com/project/0d878d4d-7d20-4150-9502-c706ea9e3772
- Service URL: **https://wnba-production-de94.up.railway.app**
- Status: Online (sfo), service ID 52d9e1b6-d7ed-4d68-8335-bd75e2102302
- GET /health 200
- POST /predict Aces/Liberty 200 - home_win_prob 0.26677 (26.7%), away 0.73323 (73.3%), matches CLI orientation.

## Curl

Health:

```
curl -sS https://wnba-production-de94.up.railway.app/health
```

Predict:

```
curl -sS -H "Content-Type: application/json" -d "{\"home\":\"Las Vegas Aces\",\"away\":\"New York Liberty\",\"ml_home\":1.65,\"ml_away\":2.30,\"total_line\":162.5,\"over_odds\":1.91,\"under_odds\":1.91}" https://wnba-production-de94.up.railway.app/predict
```

Full payloads: `build/wnba-sample/railway-predict.json`.
