
"""Pickle-only WNBA moneyline HTTP API. No DuckDB/nba_api/ingest on boot."""
from __future__ import annotations

import json
import os
import pathlib
from typing import Optional

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_PKL = (
    _ROOT
    / "model"
    / "artifacts"
    / "wnba_moneyline_v_20260617_172452_moneyline.pkl"
)
MODEL_PATH = pathlib.Path(os.getenv("MODEL_PATH", str(_DEFAULT_PKL)))
CACHE_PATH = pathlib.Path(
    os.getenv("TEAM_FEATURES_PATH", str(_ROOT / "api" / "team_features.json"))
)

# Orientation: home_win_prob is P(home win) == predict_proba[:, 1]
# against training target home_win. --home is the home team, not "favorite".
ORIENTATION = (
    "orientation OK: --home is P(home win); model disagrees with market"
)


def _load_moneyline():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"MODEL_PATH not found: {MODEL_PATH}")
    model = joblib.load(MODEL_PATH)
    meta_path = MODEL_PATH.with_suffix(".json")
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    feature_cols = meta.get("feature_cols") or [
        "rolling_win_rate_diff",
        "rolling_pts_diff",
        "rolling_net_pts_diff",
        "rolling_fg_pct_diff",
        "rolling_fg3_pct_diff",
        "rolling_tov_rate_diff",
        "rolling_reb_margin_diff",
        "net_rating_diff",
        "pace_diff",
        "days_rest_diff",
        "b2b_diff",
        "elo_diff",
        "h2h_win_rate",
        "h2h_meetings",
        "home_advantage",
        "sentiment_diff",
    ]
    medians = np.array(
        meta.get("col_medians") or [0.0] * len(feature_cols), dtype=np.float32
    )
    return model, meta, feature_cols, medians


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
    return {"teams": {}, "h2h": {}}


ML_MODEL, ML_META, FEATURE_COLS, MEDIANS = _load_moneyline()
TEAM_CACHE = _load_cache()

app = FastAPI(title="WNBA pickle-only predict", version="1.0")


class PredictIn(BaseModel):
    home: str
    away: str
    ml_home: Optional[float] = None
    ml_away: Optional[float] = None
    total_line: Optional[float] = None
    over_odds: Optional[float] = None
    under_odds: Optional[float] = None


def _lookup_team(name: str) -> dict:
    teams = TEAM_CACHE.get("teams") or {}
    if name in teams:
        return teams[name]
    needle = name.lower()
    for key, feats in teams.items():
        k = key.lower()
        if needle in k or k in needle:
            return feats
    return {}


def _h2h(home: str, away: str) -> tuple[float, int]:
    h2h = TEAM_CACHE.get("h2h") or {}
    direct = h2h.get(f"{home}||{away}")
    if direct:
        return float(direct[0]), int(direct[1])
    needle_h, needle_a = home.lower(), away.lower()
    for key, val in h2h.items():
        a, b = key.split("||", 1)
        if needle_h in a.lower() and needle_a in b.lower():
            return float(val[0]), int(val[1])
    return 0.5, 0


def _ml_vec(home_f: dict, away_f: dict, h2h_rate: float, h2h_count: int) -> dict:
    def d(key: str) -> float:
        h = home_f.get(key)
        a = away_f.get(key)
        return float(h or 0.0) - float(a or 0.0)

    return {
        "rolling_win_rate_diff": d("rolling_win_rate"),
        "rolling_pts_diff": d("rolling_pts_for"),
        "rolling_net_pts_diff": d("rolling_net_pts"),
        "rolling_fg_pct_diff": d("rolling_fg_pct"),
        "rolling_fg3_pct_diff": d("rolling_fg3_pct"),
        "rolling_tov_rate_diff": d("rolling_tov_rate"),
        "rolling_reb_margin_diff": d("rolling_reb_margin"),
        "net_rating_diff": d("net_rating"),
        "pace_diff": d("pace"),
        "days_rest_diff": d("days_rest"),
        "b2b_diff": float(home_f.get("b2b") or 0) - float(away_f.get("b2b") or 0),
        "elo_diff": float(home_f.get("elo_pre") or 1500)
        - float(away_f.get("elo_pre") or 1500),
        "h2h_win_rate": float(h2h_rate),
        "h2h_meetings": float(h2h_count),
        "home_advantage": 1.0,
        "sentiment_diff": float(home_f.get("sentiment_score") or 0)
        - float(away_f.get("sentiment_score") or 0),
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict_endpoint(body: PredictIn):
    home_f = _lookup_team(body.home)
    away_f = _lookup_team(body.away)
    if not home_f:
        raise HTTPException(status_code=400, detail=f"unknown home team: {body.home}")
    if not away_f:
        raise HTTPException(status_code=400, detail=f"unknown away team: {body.away}")

    h2h_rate, h2h_count = _h2h(body.home, body.away)
    vec = _ml_vec(home_f, away_f, h2h_rate, h2h_count)
    X = np.array([[vec.get(c, 0.0) for c in FEATURE_COLS]], dtype=np.float32)
    X = np.where(np.isnan(X), MEDIANS, X)
    home_win_prob = float(ML_MODEL.predict_proba(X)[0][1])
    away_win_prob = 1.0 - home_win_prob

    out = {
        "home": body.home,
        "away": body.away,
        "home_win_prob": home_win_prob,
        "away_win_prob": away_win_prob,
        "ml_version": ML_META.get("version", MODEL_PATH.name),
        "ml_auc": ML_META.get("auc_test"),
        "orientation": ORIENTATION,
    }
    if body.ml_home:
        impl_home = 1.0 / body.ml_home
        out["impl_home"] = impl_home
        out["ml_edge_home"] = home_win_prob - impl_home
        out["ml_home"] = body.ml_home
    if body.ml_away:
        impl_away = 1.0 / body.ml_away
        out["impl_away"] = impl_away
        out["ml_edge_away"] = away_win_prob - impl_away
        out["ml_away"] = body.ml_away
    if body.total_line is not None:
        out["total_line"] = body.total_line
        out["note_totals"] = "totals pickle not scored in pickle-only moneyline app"
        if body.over_odds is not None:
            out["over_odds"] = body.over_odds
        if body.under_odds is not None:
            out["under_odds"] = body.under_odds
    return out
