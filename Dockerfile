FROM python:3.12-slim-bookworm

WORKDIR /app

# Slim runtime: unpickle needs sklearn 1.7.2 + xgboost + lightgbm.
# Do not pip install the full repo requirements (winotify is Windows-only).
COPY requirements-api.txt /app/requirements-api.txt
RUN pip install --no-cache-dir -r /app/requirements-api.txt

COPY api/ /app/api/
COPY model/predict.py /app/model/predict.py
COPY model/stack_train.py /app/model/stack_train.py
COPY model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.pkl /app/model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.pkl
COPY model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.json /app/model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.json

ENV PORT=8080
ENV MODEL_PATH=/app/model/artifacts/wnba_moneyline_v_20260617_172452_moneyline.pkl
ENV TEAM_FEATURES_PATH=/app/api/team_features.json
ENV PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["sh", "-c", "uvicorn api.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
