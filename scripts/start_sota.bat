@echo off
title WNBA SOTA Scanner (Background Process)
echo ==============================================
echo       WNBA SOTA Scanner (arXiv)
echo ==============================================
echo.
echo Starting the schedule scanner (runs every Monday at 10:00 AM)
echo Keep this window open or minimize it to run continuously in the background.
echo Check d:\WNBA\scripts\sota_log.txt for outputs!
echo.
python d:\WNBA\scripts\sota_scanner.py
pause
