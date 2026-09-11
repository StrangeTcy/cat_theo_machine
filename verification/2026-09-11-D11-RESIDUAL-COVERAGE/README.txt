D11-SHELL RESIDUAL COVERAGE — EXTRACTOR/GRADER FINDING — 2026-09-11 UTC
======================================================================
Agent: CUR-GRADER-ENG. Lane: arena/01a066cf-cat-theo-machine.
Evaluator maintenance: no contract change, no machine-code change, no
foreign-branch edit. Finding only; the extension is scoped, not built.

VERDICT
-------
The existing extractor and grader do NOT recognize shell residual terms.
A faithfully encoded Need* residual is silently ignored (all checks
CANNOT_DETERMINE); the nearest existing role reuse misgrades in both
directions. Exact missing mapping below.

PATCH SOURCE (routing correction recorded)
------------------------------------------
The task note said to fetch arena/01a06da9, but the residual terms occur
nowhere on that lane's tip (b776d74: zero hits). They live on
arena/01a06923 tip f21460c, carried as a patch artifact (not live code —
zero *.py hits at f21460c):
  f21460c:verification/2026-09-10-d11-shell-phase2.patch (81138 bytes)
Code core of that patch: labels.py (+4 labels), main.py (+1 pack path),
packs/shell-characterization.pack.yaml (+77 lines, the two rules),
tools/d11_gate.py, plus protocol + probe logs.

THE TWO RESIDUAL TERM SHAPES (from the pack + probe logs)
---------------------------------------------------------
Rule nosolutions_introduction_characterization, unmatched premise:
  (NeedContradictionFromArbitrarySolution d u q)
  concrete: (NeedContradictionFromArbitrarySolution positive-integers
             (unknowns x) (eq (plus x 1) x))
Rule forall_implies_decomposition_characterization, unmatched premise:
  (NeedBinderSafeImplication n p q)
  concrete: (NeedBinderSafeImplication n (greater n 1)
             (eq (plus a a) (plus a a)))
REPL rendering: `residual: missing (<term>) (rule origin primitive)`.
Both rules are designed never to fire: the premises name missing
capabilities, so any goal carrying them stays unclosed.

BUNDLE-ENCODING STATUS (both sides)
-----------------------------------
The machine never writes geng-bundle/v2: at fa4b346, neither
persistence.py nor main.py contains a "candidate"/"nodes" bundle writer
(git grep, empty). So no machine-defined bundle shape exists for these
residuals. The fixture in this directory PROPOSES the convention:
  node role "residual", kind "derived", cites the claim,
  payload {head, args, origin "unmatched-premise", rule, disposition "missing"}.
It is faithful to the pack + REPL shapes above; it is not machine output.

EXPERIMENTS (2026-09-11, this lane's tools at 5cb168a)
------------------------------------------------------
A. faithful (fixture-residual-faithful.json, E7 contract):
     extract exit=0; evidence C1..C6 all {}; citations {}; diagnostics null
     grade: all six CANNOT_DETERMINE, final CANNOT_DETERMINE, exit=3
     = silently ignored; a characterized stall is indistinguishable from an
       empty bundle. No crash, no misgrade, no recognition.
B1. residuals recast as role "observable" + provenance "derived"
     (+ params window_width 4):
     C1 derived_from_flip_sign=True, C6 observable_derived=True;
     grade C1 PASS, C6 PASS, final CANNOT_DETERMINE, exit=3
     = FALSE PASS signals minted from MISSING premises.
B2. residuals recast as role "observable" without derived provenance:
     C1 invented_without_move_set=True;
     grade C1 FAIL, final FAIL exit=1, discrepancy "derivation-absent"
     = FALSE FAIL: a characterized unclosed goal is not an invented
       observable.
Schema checker on fixture A: schema_valid true, errors [], but
checkable_content false for all six checks (role accepted, content void).

ROOT CAUSE (exact)
------------------
1. tools/cur_extract_evidence.py reads 18 fixed roles
   (bound/control/generation/hypothesis/measure/monovariant/moves/
   observable/odd-control/params/rejected/samples/separate/separation/
   start/terminal/terminus/weights/wellfounded). "residual" is absent;
   no handler inspects symbolic term heads or a disposition field.
2. tools/cur_grade_artifact.py, tools/cur_artifact_schema.py,
   tools/cur_pipeline.py contain zero residual handling (git grep empty).
3. The E7 "derived observable" bits trust payload.provenance on the
   "observable" role, which is why role reuse (B1/B2) moves contract bits
   on unfaithful encodings instead of staying silent.

GRADER-EXTENSION ITEM (scoped, not implemented)
----------------------------------------------
E-RES-1: bundle convention — adopt role "residual" with payload
  {head, args, origin, rule, disposition} as proposed by the fixture.
E-RES-2: extractor — recognize role "residual" in a contract-independent
  pre-pass (shell residuals are cross-contract, not E3/E4/E7 content):
  emit a dedicated evidence field (proposal: "unclosed_characterized"
  with head/rule/disposition citations) plus a diagnostic naming the
  missing capability. Must NOT set any contract C-bit.
E-RES-3: grader — add a verdict class separating "unclosed with
  characterized residual" from CANNOT_DETERMINE and FAIL, with its own
  exit code; document it in the rubric map.
E-RES-4: negative controls — fixtures proving (i) a residual never moves
  a C-bit, (ii) observable-role reuse of a residual is rejected or
  quarantined, (iii) head/args survive byte-identical into the manifest.
Out of scope for the extension: machine-side bundle writer (INT/machine
lane owns the freeze path); teaching/closure semantics of the Need*
premises (shell lane owns them; gate S6 holds them undischargeable).

FILES
-----
fixture-residual-faithful.json                 experiment A input
fixture-residual-as-observable-derived.json    experiment B1 input
fixture-residual-as-observable-missing.json    experiment B2 input
README.txt                                     this finding
Reproduce: python3 tools/cur_extract_evidence.py <fixture> --out /tmp/m.json
           python3 tools/cur_grade_artifact.py /tmp/m.json
           python3 tools/cur_artifact_schema.py check <fixture>

Merge/tag performed: none. Machine code changed: no.
