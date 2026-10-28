@echo off
call C:\Users\hatgu\anaconda3\Scripts\activate.bat hyge
if errorlevel 1 exit /b %errorlevel%
set PYTHONPATH=X:\
set HYGE_LIVE_CHECK_SNAPSHOT=X:\hyge\verification\live-learning-%RANDOM%-%RANDOM%.json
cd /d X:\hyge\verification
python -B -u -m hyge.main live --live-snapshot %HYGE_LIVE_CHECK_SNAPSHOT% < X:\hyge\verification\live-learning-input-2026-10-28.txt > X:\hyge\verification\live-learning-2026-10-28.log 2>&1
if errorlevel 1 exit /b %errorlevel%
python -B -u -m hyge.main live --live-snapshot %HYGE_LIVE_CHECK_SNAPSHOT% < X:\hyge\verification\live-learning-resume-input-2026-10-28.txt > X:\hyge\verification\live-learning-resume-2026-10-28.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Live session commands completed. Inspect the saved transcripts for proof and scope evidence.
