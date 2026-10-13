# Live proof ingress repair — evidence

## Scope statement

The acceptance sentence is the exact line

```
prove that for all n >= 2 a^n + b^n = c^n is not solvable for a,b,c which are natural numbers
```

The laptop checkout named in the handoff (`/media/veracrypt11/hyge`) is not
present in this environment, and the pasted transcript's commit was not
recorded, so the original failure is not replayed byte-for-byte. The fix is
verified against the failure class the handoff describes: the two published
grammar gaps (`>=`/`<=` splitting and the missing "is not solvable for … which
are …" production) plus the routing rule that a recognized `prove that`
envelope must stay an ingress diagnostic and never fall through to the
conversation path.

## Identified code

- Local base: `41e80785d4de090337a9dfc08439f2fcb45915dc`
- Tested commit: `507fc5a13cd508765361453bbc36bd1aafaff1e0` (this checkout's branch)
- Published ingress reference: `0d7e1b6` ("[INT3] admission evidence …"),
  reachable from `origin/arena/01a09270-cat-theo-machine` and
  `origin/arena/01a09396-cat-theo-machine`. Its `proof_ingress.py` handles
  only `=`, `<`, `>` and only "has no solutions in …".
- The base checkout has no ingress at all; the ingress is added here on top of
  the base and then repaired, rather than claiming to patch a revision that
  is not present.

## Changes

- `proof_ingress.py` (new): machine-native parser edges. `>=` and `<=` are
  read as single symbol tokens with half-open spans and produce `ge`/`le`
  heads that are distinct from strict `<`/`>`. `MathematicalSentence` accepts
  both no-solutions phrasings; the "is not solvable for <names> which are
  <domain>" form binds exactly the listed names and rejects omitted,
  duplicate, and non-occurring names. Natural-number domains return a
  semantic-clarification and never become a goal. `ProofCommandEnvelope`
  recognizes `prove that` without running the claim grammar.
- `main.py`: ingress dispatch by recognition at the top of `_respond`; prints
  `recognized proof command` before parsing, prints a parsed goal only after a
  complete parse, keeps failures as ingress diagnostics, and audits the
  coordinator goal via `runtime.last_foreground_goal`.
- `runtime.py`: `last_foreground_goal` recorded in `prove` and cleared in the
  constructor, for structural equality at the prover boundary.
- `heuristics.py`: quantified (`forall`-headed) goals are returned unchanged
  by `HeuristicCanonicalTerm`, matching the published lineage, so the scoped
  goal is not reordered across processes.

No theorem content is added. No proof is claimed: a goal that parses is
submitted once, and the foreground search reports "no derivation found".

## Regression results

Run through the real module entrypoint (isolated `hyge`-named checkout copy,
fresh snapshots directory, `python main.py live --workers 0`):

- `python -m <pkg>.ingress_tests` -> `PASS: proof ingress parser/dispatcher/scope regressions`
- Exact sentence -> `semantic-clarification` (natural-number domain), no submission
- `>=` vs `>` -> distinct goal terms (`ge(...)` vs `lt(...)`)
- `a^n+b^n=c^n` vs `a^n + b^n = c^n` -> equivalent goal terms
- Both no-solutions phrasings with positive-integer domains -> equivalent goal terms
- Explicit `a, b, c` binding -> `unknowns(a, b, c)`, quantified exponent `n` not bound by the domain
- Malformed quantifier -> precise span diagnostic, no submission, no stale goal
- Formal query `add ( two , two )` -> `four` (unchanged)
- Successful parse -> one submission; `foreground coordinator goal preserved
  (machine structural equality)`

Raw transcripts:

- `verification/live-proof-ingress-before-live.txt` (published parser; the
  exact sentence fails with `parse-failure … arithmetic atom`)
- `verification/live-proof-ingress-after-live.txt` (repaired parser; the exact
  sentence produces the clarification diagnostic)
- `verification/live-proof-ingress.inputs.txt` (the lines fed to live mode)
