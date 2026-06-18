# WNBA Two-Model Syndicate — Master Coordination

**This document is the single source of truth.** Claude (coordinator) owns it and updates it on every change. If a decision isn't written here, it isn't locked.

Last updated: 2026-06-17.

---

## 0. The Thesis (why this is the edge)
We run **two genuinely independent WNBA models as a team** and bet only when they agree. The edge is not in either model alone — it's in the **record of their agreement/divergence**, measured against the closing line (CLV). That record is a learnable, tradeable signal. Almost nobody mines it.

The discipline that makes it real (and the traps we explicitly reject):
- ❌ A deliberately-wrong model "validates" nothing. On a ~50/50 market, reliably-wrong = reliably-right-inverted (doesn't exist); merely-bad = noise. Noise validates nothing.
- ✅ **Independence is everything.** Two *independent* reads that agree raise true confidence; their *divergence pattern* (vs CLV/outcome) is itself a signal.

---

## 1. The Two Models — and the ONE rule that can't be broken

| | Model 1 — "Honest" | Model 2 — "Syndicate" |
|---|---|---|
| Repo | `JesseBeckerGBH/wnba` (private) | `JesseBeckerGBH/wnba-ensemble` (public) → Railway `disciplined-ambition/wnba-ensemble` |
| Method | Calibrated stack: LR + XGB + LGB → LR meta, isotonic-calibrated | **5-agent stochastic consensus** (`node_consensus`): parallel agents → mode/median "true odds" |
| Role | Steady, point-in-time-correct baseline | Slightly-less-polished but **methodologically different** read |

> 🔒 **HARD RULE — INDEPENDENCE.** Model 2's WNBA prediction MUST come from the stochastic-consensus engine (or another distinct method), **never** from re-running Model 1's stack. The day Model 2 becomes a copy of the stack, the team collapses into a mirror and all "agreement" becomes false confidence. The coordinator enforces this.

---

## 2. The Agreement Gate + Bounded Kelly (the safety rule)
- **Bet only when both models agree** on side AND both clear their own thresholds (min prob, AUC gate).
- **Size up on agreement — but bounded.** Confidence rises with agreement, so stake rises — but capped at **¼–½ Kelly**, never full. Full Kelly on *estimated* edges ruins winning models via variance. Same aggression, survives the run.
- Divergence → **no bet**, but **log it** (it's data, see §3).

---

## 3. THE RECORD (what the hound dog hunts)
Every game produces a row in `bet_record` (schema: [`db/bet_record_schema.sql`](../db/bet_record_schema.sql)) whether or not we bet — including divergences. Core fields: both models' probs + versions, agreement state, stake/Kelly used, **opening line, closing line, CLV, beat_close**, outcome, PnL/ROI.

**Measurement priority:** **CLV first, ROI second.** ROI lies in small samples; if our bets consistently beat the closing line, we're +EV before the money proves it. We track CLV *per model* and *per agreement-state*.

---

## 4. The Hound Dog (pattern mining) + the AI research swarm
Once the record has volume, a **meta-learner** trains on it to find the exploitable pattern in agree/diverge × CLV × outcome. Feeding it:
- **Grok** — weekly math search across ~100 top-university math sources (the Beast v2 "SOTA search" pattern, extended).
- **Perplexity** — broader "math that finds matches" search.
- **Claude (coordinator)** — integrates, *vets before any math touches real money*, translates findings into the meta-learner, keeps this doc current.

**Honest note on "self-annealing":** the LLMs don't get smarter on their own between sessions. The **system** anneals — the record grows, searches feed new methods, the meta-learner retrains, weak edges get pruned. Build the loop right and it compounds regardless. That loop is the creature people will study.

---

## 5. Data feed evolution
1. **Now:** synthetic odds (Elo-derived ML / flat 0.5 totals) — placeholder, ROI is NOT real edge.
2. **Next:** The Odds API (renewed) — live picks + historical backfill (2020+, premium) → enables real CLV.
3. **Production:** **SportRadar** (official WNBA data partner, gold standard) — when we go full-blast live + public.

---

## 6. Deploy rule
**The two models deploy together or not at all.** Neither ships solo. No Whop / public offering until real odds confirm the agreement-gated edge survives the vig. (Per Jesse.)

---

## 7. Current status & critical path
- ✅ Model 1 refreshed to 2019–2026 (1,616 games), leak-free backtest verified, pushed.
- ✅ Model 2 located + understood (syndicate); WNBA node == Model 1 code (March snapshot) → **needs its consensus method wired as the independent read.**
- ⚠️ Odds API key deactivated → renewing (Jesse). BetsAPI token rotating (Jesse).
- 🚨 Secret leak: `.env` inside `node_wnba_engine.zip` in public repo → neutralized by rotation; full repo scrub folded into the planned unzip-restructure.
- ⛔ Railway `wnba-ensemble` build fails (wants nonexistent `docker/Dockerfile.rust`; engine is zipped). Fix when we prep deploy-together.

**Critical path to the edge:** renew odds → log real CLV into `bet_record` → accumulate record (agree + diverge) → meta-learn the pattern. No record, no scent.

Open issues: [#1 real odds](https://github.com/JesseBeckerGBH/wnba/issues/1) · [#2 weak totals](https://github.com/JesseBeckerGBH/wnba/issues/2) · [#3 BoxScore V3](https://github.com/JesseBeckerGBH/wnba/issues/3) · [#4 sentiment](https://github.com/JesseBeckerGBH/wnba/issues/4)
