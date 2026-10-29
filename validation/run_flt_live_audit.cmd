@echo off
call C:\Users\hatgu\anaconda3\Scripts\activate.bat hyge
if errorlevel 1 exit /b %errorlevel%
set PYTHONPATH=X:\
set HYGE_FLT_AUDIT_SNAPSHOT=X:\hyge\verification\live-flt-audit-%RANDOM%-%RANDOM%.json
cd /d X:\hyge\verification
python -B -u -m hyge.main live --live-snapshot %HYGE_FLT_AUDIT_SNAPSHOT% < X:\hyge\verification\live-flt-audit-input-2026-10-28.txt > X:\hyge\verification\live-flt-audit-2026-10-28.log 2>&1
if errorlevel 1 exit /b %errorlevel%
python -B -u -m hyge.main live --live-snapshot %HYGE_FLT_AUDIT_SNAPSHOT% < X:\hyge\verification\live-flt-audit-resume-input-2026-10-28.txt > X:\hyge\verification\live-flt-audit-resume-2026-10-28.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Live audit and restart completed. Inspect both logs for the pending FLT scope.
echo Snapshot: %HYGE_FLT_AUDIT_SNAPSHOT%
