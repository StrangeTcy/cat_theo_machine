@echo off
call C:\Users\hatgu\anaconda3\Scripts\activate.bat hyge
if errorlevel 1 exit /b %errorlevel%
set PYTHONPATH=X:\
cd /d X:\
python -B -u -m hyge.validation.graph_mapping_regressions > X:\hyge\verification\continuation-graph_mapping_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo graph_mapping_regressions passed.
python -B -u -m hyge.validation.graph_surgery_regressions > X:\hyge\verification\continuation-graph_surgery_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo graph_surgery_regressions passed.
python -B -u -m hyge.validation.graph_rewriting_integration > X:\hyge\verification\continuation-graph_rewriting_integration-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo graph_rewriting_integration passed.
python -B -u -m hyge.validation.defined_operation_regressions > X:\hyge\verification\continuation-defined_operation_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo defined_operation_regressions passed.
python -B -u -m hyge.validation.discovery_catalog_regressions > X:\hyge\verification\continuation-discovery_catalog_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo discovery_catalog_regressions passed.
python -B -u -m hyge.validation.discovery_tensor_axes_regressions > X:\hyge\verification\continuation-discovery_tensor_axes_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo discovery_tensor_axes_regressions passed.
python -B -u -m hyge.validation.finite_template_matching_regressions > X:\hyge\verification\continuation-finite_template_matching_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo finite_template_matching_regressions passed.
python -B -u -m hyge.validation.test48_named_discovered_laws > X:\hyge\verification\continuation-test48_named_discovered_laws-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo test48_named_discovered_laws passed.
python -B -u -m hyge.validation.live_proof_regressions > X:\hyge\verification\continuation-live_proof_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo live_proof_regressions passed.
python -B -u -m hyge.validation.graph_edge_dependencies_regressions > X:\hyge\verification\continuation-graph_edge_dependencies_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo graph_edge_dependencies_regressions passed.
python -B -u -m hyge.validation.defined_composition_regressions > X:\hyge\verification\continuation-defined_composition_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo defined_composition_regressions passed.
python -B -u -m hyge.validation.finite_structure_matching_regressions > X:\hyge\verification\continuation-finite_structure_matching_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo finite_structure_matching_regressions passed.
python -B -u -m hyge.validation.defined_discovery_integration > X:\hyge\verification\continuation-defined_discovery_integration-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo defined_discovery_integration passed.
python -B -u -m hyge.validation.observed_witness_regressions > X:\hyge\verification\continuation-observed_witness_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo observed_witness_regressions passed.
python -B -u -m hyge.validation.live_naming_gate_regressions > X:\hyge\verification\continuation-live_naming_gate_regressions-2026-10-30.log 2>&1
if errorlevel 1 exit /b %errorlevel%
echo live_naming_gate_regressions passed.
echo All fifteen machine continuation suites passed.

