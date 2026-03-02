@echo off
:: ─────────────────────────────────────────────────────────────────────────────
:: WNBA daily data refresh — run via Windows Task Scheduler at 06:00 daily
:: (WNBA season is May–October; on off-season days this completes quickly)
:: ─────────────────────────────────────────────────────────────────────────────

cd /d D:\WNBA
set LOG=D:\WNBA\logs\daily_ingest.log

echo. >> %LOG%
echo ============================================================ >> %LOG%
echo [%date% %time%] Starting WNBA daily ingest >> %LOG%

:: 1. Fetch latest game results (current season)
py -3.13 data\ingest_wnba.py --seasons 2026 >> %LOG% 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: ingest_wnba.py failed >> %LOG%
    exit /b 1
)

:: 2. Rebuild features
py -3.13 data\build_features.py --season 2026 >> %LOG% 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: build_features.py failed >> %LOG%
    exit /b 1
)

:: 3. Retrain model on latest data
py -3.13 model\stack_train.py >> %LOG% 2>&1
if %errorlevel% neq 0 (
    echo [%date% %time%] ERROR: stack_train.py failed >> %LOG%
    exit /b 1
)

:: 4. Refresh odds (The Odds API)
py -3.13 scripts\odds_client.py --upcoming --save >> %LOG% 2>&1

:: 5. Enrich upcoming games with Reddit sentiment
py -3.13 sentiment\reddit_monitor.py --all-upcoming >> %LOG% 2>&1

echo [%date% %time%] Daily ingest complete >> %LOG%
