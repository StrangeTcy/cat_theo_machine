@echo off
call C:\Users\hatgu\anaconda3\Scripts\activate.bat hyge
if errorlevel 1 exit /b %errorlevel%
cd /d X:\
python -B -u -m hyge.validation.graph_mapping_regressions > X:\hyge\verification\graph-repair-mapping-2026-10-29.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Mapping checks passed.
python -B -u -m hyge.validation.graph_surgery_regressions > X:\hyge\verification\graph-repair-surgery-2026-10-29.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Surgery checks passed.
python -B -u -m hyge.validation.graph_rewriting_integration > X:\hyge\verification\graph-repair-integration-2026-10-29.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Graph integration checks passed.
python -B -u -m hyge.validation.defined_operation_regressions > X:\hyge\verification\defined-operation-2026-10-29.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Defined operation checks passed.
python -B -u -m hyge.validation.discovery_catalog_regressions > X:\hyge\verification\graph-repair-catalog-2026-10-29.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Operation catalog checks passed.
python -B -u -m hyge.validation.discovery_tensor_axes_regressions > X:\hyge\verification\graph-repair-tensor-2026-10-29.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Tensor checks passed.
python -B -u -m hyge.validation.finite_template_matching_regressions > X:\hyge\verification\graph-repair-template-2026-10-29.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Finite template checks passed.
python -B -u -m hyge.validation.test48_named_discovered_laws > X:\hyge\verification\graph-repair-named-laws-2026-10-29.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Named law checks passed.
python -B -u -m hyge.validation.live_proof_regressions > X:\hyge\verification\graph-repair-live-proof-2026-10-29.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo Live proof checks passed.
echo All machine repair checks passed.
