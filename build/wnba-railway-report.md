# WNBA Railway report

Date: 2026-09-03 13:51 PT

## Orientation

**orientation OK: --home is P(home win); model disagrees with market.**

- CLI `--home` is the home team name. `predict()` returns `home_win_prob = model.predict_proba(X)[0][1]`, which is P(class=1) = P(home win). Training target in `stack_train.py` is `home_win`. Features are home-minus-away diffs plus `home_advantage=1.0`.
- Market: Aces 1.65 favorite vs Liberty 2.30. Model with Aces at home: **26.7% / 73.3%**. Swapped (Liberty home, odds swapped so Aces keep 1.65): Liberty **79.3%**, Aces **20.7%**. Home-court bump is ~6pp; Liberty is the model favorite in both orientations. **Did not invert predict.py.**
- sklearn InconsistentVersionWarning gone after pin to 1.7.2. Residual XGBoost pickle warning only (not pinned; no re-save).

## sklearn choice

Pinned **scikit-learn==1.7.2** in `requirements.txt` and `requirements-api.txt` (pickle trained on 1.7.2). Local venv Python 3.14: installed 1.7.2 (cp314 win_amd64 wheel). Did **not** re-save pickle.

## Image

- Dockerfile: **python:3.12-slim-bookworm** (task allows 3.12 or 3.14). Live Railway build used 3.12. sklearn==1.7.2 manylinux cp312 wheel. `libgomp1` installed for LightGBM.
- Slim API deps only (`requirements-api.txt`): sklearn 1.7.2, numpy, joblib, xgboost, lightgbm, fastapi, uvicorn, pydantic. Not full repo requirements (winotify is Windows-only; no DuckDB/nba_api on boot).
- COPY pickle `model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.pkl` + json sidecar + `api/` + `model/predict.py`.
- ENV PORT, MODEL_PATH. CMD: `uvicorn api.app:app --host 0.0.0.0 --port $PORT`.

## Files added

- `api/app.py`, `api/__init__.py`, `api/team_features.json`
- `Dockerfile`, `.dockerignore`, `requirements-api.txt`
- `.env.example` names: PORT, MODEL_PATH, TEAM_FEATURES_PATH
- moneyline pickle+json force-added (gitignore now `model/artifacts/*` with negations)
- `build/wnba-sample/orientation-check.txt`

## predict.py change summary

Smallest import fix only: lazy-import `duckdb` and `model.stack_train` inside `predict()` so `import model.predict` does not need DuckDB at import. CLI `--home` help and a comment document orientation. **No probability inversion.**

## Git

Branch `run/wnba-v1` (PR #5, not merged).

- a899b86 feat: pickle-only FastAPI predict API and sklearn 1.7.2 pin
- d09a337 fix: install libgomp1 so LightGBM can unpickle in Docker
- b8442f236a49eb408bf451a91b659d1f95c1da58 feat: export team features JSON and pickle-only FEATURES_PATH API

Report commit will land on top of HEAD.

## Railway

Logged in as Jesse Becker (jessebecker2021@gmail.com).

- Created project **wnba** (did not touch existing UFC projects or `wnba-ensemble`).
- Project: https://railway.com/project/0d878d4d-7d20-4150-9502-c706ea9e3772
- Service URL: **https://wnba-production-de94.up.railway.app**
- GET /health 200 `{"status":"ok",...}`
- POST /predict Aces/Liberty 200 — home_win_prob 0.26677 (26.7%), away 0.73323 (73.3%), matches CLI.

No custom domain / Stripe / dashboard deploy.

## Curl result

See `build/wnba-sample/railway-predict.json`.
