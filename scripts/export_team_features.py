#!/usr/bin/env python3
"""One-shot DuckDB -> JSON export of team features and H2H helpers.

The Railway API must not open DuckDB / nba_api / ingest on boot.
Run this locally, then ship model/artifacts/team_features.json.
"""
from __future__ import annotations

import json
import os
import pathlib
from datetime import date

import duckdb
from dotenv import load_dotenv

_ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")

DB_PATH = os.getenv("WNBA_DB_PATH", str(_ROOT / "db" / "wnba.duckdb"))
OUT_PATH = _ROOT / "model" / "artifacts" / "team_features.json"

FEATURE_KEYS = [
    "rolling_win_rate",
    "rolling_pts_for",
    "rolling_pts_against",
    "rolling_net_pts",
    "rolling_fg_pct",
    "rolling_fg3_pct",
    "rolling_ft_pct",
    "rolling_tov_rate",
    "rolling_reb_margin",
    "pace",
    "off_rating",
    "def_rating",
    "net_rating",
    "days_rest",
    "b2b",
    "elo_pre",
    "sentiment_score",
]


def _league_avg(conn) -> dict:
    row = conn.execute(
        """
        SELECT
            AVG(rolling_win_rate), AVG(rolling_pts_for), AVG(rolling_pts_against),
            AVG(rolling_net_pts), AVG(rolling_fg_pct), AVG(rolling_fg3_pct),
            AVG(rolling_ft_pct), AVG(rolling_tov_rate), AVG(rolling_reb_margin),
            AVG(pace), AVG(off_rating), AVG(def_rating), AVG(net_rating),
            5.0 AS days_rest, 0 AS b2b, 1500.0 AS elo_pre, 0.0 AS sentiment
        FROM game_features
        WHERE game_date >= (CURRENT_DATE - INTERVAL '60 days')
        """
    ).fetchone()
    vals = row or [0.5] * len(FEATURE_KEYS)
    return dict(zip(FEATURE_KEYS, [None if v is None else float(v) for v in vals]))


def _team_features(conn, team_id: str, as_of: date) -> dict:
    row = conn.execute(
        """
        SELECT
            rolling_win_rate, rolling_pts_for, rolling_pts_against, rolling_net_pts,
            rolling_fg_pct, rolling_fg3_pct, rolling_ft_pct,
            rolling_tov_rate, rolling_reb_margin,
            pace, off_rating, def_rating, net_rating,
            days_rest, b2b, elo_pre, sentiment_score
        FROM game_features
        WHERE team_id = ? AND game_date < ?
        ORDER BY game_date DESC
        LIMIT 1
        """,
        [team_id, as_of],
    ).fetchone()
    if not row:
        return _league_avg(conn)
    out = {}
    for k, v in zip(FEATURE_KEYS, row):
        if v is None:
            out[k] = None
        elif k == "b2b":
            out[k] = int(v)
        else:
            out[k] = float(v)
    return out


def _h2h(conn, home_name: str, away_name: str) -> tuple[float, int]:
    row = conn.execute(
        """
        SELECT
            COUNT(*)                                        AS meetings,
            SUM(CASE WHEN g.home_win THEN 1.0 ELSE 0.0 END) AS home_wins
        FROM games g
        JOIN teams th ON th.team_id = g.home_team_id
        JOIN teams ta ON ta.team_id = g.away_team_id
        WHERE (LOWER(th.team_name) LIKE LOWER(?) OR LOWER(th.team_abbrev) LIKE LOWER(?))
          AND (LOWER(ta.team_name) LIKE LOWER(?) OR LOWER(ta.team_abbrev) LIKE LOWER(?))
          AND g.home_score IS NOT NULL
          AND g.game_date >= (CURRENT_DATE - INTERVAL '730 days')
        """,
        [f"%{home_name}%", f"%{home_name}%", f"%{away_name}%", f"%{away_name}%"],
    ).fetchone()
    if row and row[0] > 0:
        return float(row[1] / row[0]), int(row[0])
    return 0.5, 0


def main() -> None:
    as_of = date.today()
    conn = duckdb.connect(DB_PATH, read_only=True)
    try:
        teams_rows = conn.execute(
            "SELECT team_id, team_name, team_abbrev FROM teams ORDER BY team_name"
        ).fetchall()
        teams: dict = {}
        identities = []
        for team_id, name, abbrev in teams_rows:
            feats = _team_features(conn, team_id, as_of)
            if name:
                teams[name] = feats
            if abbrev:
                teams[abbrev] = feats
            identities.append((name, abbrev))

        h2h: dict = {}
        for home_name, home_abbr in identities:
            for away_name, away_abbr in identities:
                if home_name == away_name:
                    continue
                rate, meetings = _h2h(conn, home_name, away_name)
                for hk in (home_name, home_abbr):
                    for ak in (away_name, away_abbr):
                        if hk and ak:
                            h2h[f"{hk}||{ak}"] = [rate, meetings]
        payload = {
            "as_of": as_of.isoformat(),
            "n_teams": len(identities),
            "teams": teams,
            "h2h": h2h,
        }
    finally:
        conn.close()

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    # Convenience copy next to the API module (already shipped in prior commit).
    api_copy = _ROOT / "api" / "team_features.json"
    api_copy.parent.mkdir(parents=True, exist_ok=True)
    api_copy.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"wrote {OUT_PATH} teams={len(identities)} team_keys={len(teams)} h2h={len(h2h)}")
    print(f"wrote {api_copy}")


if __name__ == "__main__":
    main()
