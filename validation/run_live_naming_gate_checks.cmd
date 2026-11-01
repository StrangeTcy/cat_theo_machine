@echo off
call C:\Users\hatgu\anaconda3\Scripts\activate.bat hyge
if errorlevel 1 exit /b %errorlevel%
set PYTHONPATH=X:\
cd /d X:\
python -B -u -m hyge.validation.live_naming_gate_regressions > X:\hyge\verification\live-naming-gate-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Live naming gate checks passed.
