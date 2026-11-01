@echo off
call C:\Users\hatgu\anaconda3\Scripts\activate.bat hyge
if errorlevel 1 exit /b %errorlevel%
cd /d X:\
python -B -u -m hyge.validation.live_proof_evidence_regressions > X:\hyge\verification\live-proof-evidence-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Live proof evidence checks passed.
