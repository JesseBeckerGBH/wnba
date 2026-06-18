-- bet_record_schema.sql
-- THE RECORD — the single source of truth the two-model team is judged on.
-- See docs/MASTER_COORDINATION.md §3. One row PER GAME PER MARKET, logged whether
-- or not we bet (divergences are data too). CLV is the truth-meter, not ROI.
--
-- Apply:  duckdb db/wnba.duckdb < db/bet_record_schema.sql

CREATE TABLE IF NOT EXISTS bet_record (
    bet_id           VARCHAR PRIMARY KEY,      -- uuid
    game_id          VARCHAR NOT NULL,
    game_date        DATE    NOT NULL,
    season_year      INTEGER,
    market           VARCHAR NOT NULL,         -- 'moneyline' | 'totals'
    side             VARCHAR,                  -- 'home'/'away' | 'over'/'under' (the agreed pick; NULL if diverged/no-bet)

    -- ── The two independent reads (the heart of it) ──────────────────────────
    p_model1         DOUBLE,                   -- Model 1 (honest stack) P(side)
    p_model2         DOUBLE,                   -- Model 2 (syndicate consensus) P(side) — MUST be a different method
    model1_version   VARCHAR,
    model2_version   VARCHAR,
    agree            BOOLEAN,                  -- same side AND both clear thresholds
    agreement_delta  DOUBLE,                   -- abs(p_model1 - p_model2): small = strong agreement
    consensus_p      DOUBLE,                   -- blended probability used for sizing when agree

    -- ── Sizing (bounded Kelly — never full; see §2) ──────────────────────────
    kelly_fraction   DOUBLE,                   -- fraction actually used (target 0.25–0.50)
    stake_units      DOUBLE,                   -- 0 if no bet
    bankroll_before  DOUBLE,

    -- ── CLV: the leading indicator of +EV (truth-meter) ──────────────────────
    open_odds        DOUBLE,                   -- decimal odds at bet time
    close_odds       DOUBLE,                   -- decimal odds at market close
    clv_pct          DOUBLE,                   -- open_odds/close_odds - 1  (>0 = beat the close)
    beat_close       BOOLEAN,                  -- open_odds > close_odds

    -- ── Outcome ──────────────────────────────────────────────────────────────
    outcome          VARCHAR,                  -- 'win' | 'loss' | 'push' | 'no_bet'
    pnl_units        DOUBLE,
    roi              DOUBLE,

    book             VARCHAR,                  -- 'theodds' | 'sportradar' | ...
    placed_at        TIMESTAMP,
    settled_at       TIMESTAMP
);

-- Performance split by agreement state — the first place the pattern shows up.
-- CLV is ranked above ROI on purpose (it stabilises far faster).
CREATE OR REPLACE VIEW agreement_performance AS
SELECT
    market,
    agree,
    COUNT(*)                                   AS n,
    ROUND(AVG(clv_pct), 4)                     AS avg_clv,          -- watch this first
    ROUND(AVG(CASE WHEN beat_close THEN 1 ELSE 0 END), 4) AS pct_beat_close,
    SUM(CASE WHEN outcome IN ('win','loss','push') THEN 1 ELSE 0 END) AS bets_settled,
    ROUND(AVG(CASE WHEN outcome='win' THEN 1.0
                   WHEN outcome='loss' THEN 0.0 END), 4)            AS win_rate,
    ROUND(SUM(pnl_units), 2)                   AS total_pnl,
    ROUND(AVG(roi), 4)                         AS avg_roi
FROM bet_record
GROUP BY market, agree
ORDER BY market, agree DESC;
