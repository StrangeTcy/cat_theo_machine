@echo off
rem Run ONLY from the already-open project Anaconda Prompt.
rem No interpreter discovery, activation, checkout changes, or shared state.
setlocal
set "HYGE_SNAPSHOT_DIR=%TEMP%\hyge-ingress-%RANDOM%-%RANDOM%"
if exist "%HYGE_SNAPSHOT_DIR%" exit /b 2
mkdir "%HYGE_SNAPSHOT_DIR%"
if errorlevel 1 exit /b 2
pushd "%~dp0.."
for %%I in ("%CD%") do set "HYGE_TEST_PACKAGE=%%~nxI"
cd ..
python -m %HYGE_TEST_PACKAGE%.ingress_tests > "%HYGE_SNAPSHOT_DIR%\regressions.txt" 2>&1
set "HYGE_TEST_EXIT=%ERRORLEVEL%"
popd
if not "%HYGE_TEST_EXIT%"=="0" (
  type "%HYGE_SNAPSHOT_DIR%\regressions.txt"
  echo Regression failure. Evidence retained at %HYGE_SNAPSHOT_DIR%
  exit /b 1
)
python "%~dp0..\main.py" live --workers 1 < "%~dp0live-proof-ingress.inputs.txt" > "%HYGE_SNAPSHOT_DIR%\after-live.txt" 2>&1
set "HYGE_TEST_EXIT=%ERRORLEVEL%"
echo Raw transcripts and isolated state: %HYGE_SNAPSHOT_DIR%
if not "%HYGE_TEST_EXIT%"=="0" exit /b 1
findstr /c:"semantic-clarification at input span" "%HYGE_SNAPSHOT_DIR%\after-live.txt" > nul
if errorlevel 1 exit /b 1
findstr /c:"parse-failure at input span" "%HYGE_SNAPSHOT_DIR%\after-live.txt" > nul
if errorlevel 1 exit /b 1
findstr /c:"submitting parsed goal to foreground prover" "%HYGE_SNAPSHOT_DIR%\after-live.txt" > nul
if errorlevel 1 exit /b 1
findstr /c:"parsed goal: forall(n, implies" "%HYGE_SNAPSHOT_DIR%\after-live.txt" > nul
if errorlevel 1 exit /b 1
findstr /c:"parsed goal: forall(k, implies" "%HYGE_SNAPSHOT_DIR%\after-live.txt" > nul
if errorlevel 1 exit /b 1
for /f %%N in ('find /c "submitting parsed goal to foreground prover" ^< "%HYGE_SNAPSHOT_DIR%\after-live.txt"') do if not "%%N"=="3" exit /b 1
findstr /c:"there is nothing to explain" "%HYGE_SNAPSHOT_DIR%\after-live.txt" > nul
if errorlevel 1 exit /b 1
findstr /c:"hyge> four" "%HYGE_SNAPSHOT_DIR%\after-live.txt" > nul
if errorlevel 1 exit /b 1
findstr /c:"Traceback" /c:"expected-left-parenthesis" /c:"Use Predicate(constant)" "%HYGE_SNAPSHOT_DIR%\after-live.txt" > nul
if not errorlevel 1 exit /b 1
echo PASS: live ingress fixture completed; inspect the retained raw transcript for proof-search outcomes.
exit /b 0
