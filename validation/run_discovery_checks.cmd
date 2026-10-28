@echo off
call C:\Users\hatgu\anaconda3\Scripts\activate.bat hyge
if errorlevel 1 exit /b %errorlevel%
cd /d X:\
python -B -u -m hyge.validation.discovery_catalog_regressions
if errorlevel 1 exit /b %errorlevel%
python -B -u -m hyge.validation.discovery_tensor_axes_regressions
if errorlevel 1 exit /b %errorlevel%
python -B -u -m hyge.validation.discovery_regressions
if errorlevel 1 exit /b %errorlevel%
python -B -u -m hyge.validation.discovery_miner_regressions
if errorlevel 1 exit /b %errorlevel%
python -B -u -m hyge.validation.test48_named_discovered_laws
if errorlevel 1 exit /b %errorlevel%
python -B -u -m hyge.validation.playground_edge_regressions
if errorlevel 1 exit /b %errorlevel%
echo All discovery checks passed.
