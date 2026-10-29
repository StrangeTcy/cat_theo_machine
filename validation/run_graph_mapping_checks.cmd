@echo off
call C:\Users\hatgu\anaconda3\Scripts\activate.bat hyge
if errorlevel 1 exit /b %errorlevel%
cd /d X:\
python -B -u -m hyge.validation.graph_mapping_regressions
exit /b %errorlevel%
