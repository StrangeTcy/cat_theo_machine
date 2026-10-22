# D11 diagnostic-isolation recovery attempt — 2026-09-12

- Recovery code commit: `95d248872cff4f4f65cbd635827cad9c6b83aa66`
- Reconstruction parent: `99ab2f02c29e03410319f98bd40f2b167aecea2e`
- Reported prior isolation commit: `eedcd4f` (object unavailable after sandbox reset)
- Source: survivor archive preserved before reconstruction.
- Scope: rerun the documented D11 gate, adversarial safety probe, live ingress probe, ingress regression, and syntax compilation. No target session or logical checker run.

Raw outputs are stored alongside this file. Results are filled from their corresponding commands rather than copied from the prior attempt.

## Actual rerun results

- `tools/d11_gate.py`: 23/23 gated conditions passed.
- `tools/d11_gate.py --safety-probe`: all eight ordinary-fact, taught, restored-fact, and replayed-taught B/C spoof cases stayed unclosed with zero proof candidates.
- `tools/d11_gate.py --live-ingress-probe`: passed; parsed, submitted, and worker-received goals match, with a diagnostic and empty derivation.
- `python -m cat_theo_machine.ingress_tests`: passed.
- `python -m py_compile packs.py runtime.py main.py tools/d11_gate.py`: passed.

`RESULTS.txt` contains the corresponding exit statuses; the named transcript files contain each raw command output. These results validate behavior of the recovery commit, but do not establish byte equivalence to the unavailable `eedcd4f` object.
