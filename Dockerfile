FROM python:3.14-slim-bookworm

WORKDIR /app

# Match venv Python 3.14 that loads sklearn==1.7.2 pickle.
# LightGBM needs libgomp; slim image does not ship it.
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Slim runtime: unpickle needs sklearn 1.7.2 + xgboost + lightgbm.
# Do not pip install full repo requirements (winotify is Windows-only; no duckdb).
COPY requirements-api.txt /app/requirements-api.txt
RUN pip install --no-cache-dir -r /app/requirements-api.txt

COPY api/ /app/api/
COPY model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.pkl /app/model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.pkl
COPY model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.json /app/model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.json
COPY model/artifacts/team_features.json /app/model/artifacts/team_features.json

ENV PORT=8080
ENV MODEL_PATH=/app/model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.pkl
ENV FEATURES_PATH=/app/model/artifacts/team_features.json
ENV TEAM_FEATURES_PATH=/app/api/team_features.json
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["sh", "-c", "uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
