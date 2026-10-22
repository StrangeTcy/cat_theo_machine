# CUR-E-ENG — Wave 1 instruction block (E0 build + E1 held-out transfer test)

Provenance: authored on lane `arena/01a066cf-cat-theo-machine`. This is program context, not a
role assignment: CUR-ORACLE authors it; the human owns one-time setup and agent spawning. It is a
**division of work**, not a prerequisite gate. Docs-only; no implementation, no tag.

Amendment note (successor commit): the first draft conflated **proof transfer** with
**explanation transfer** and let a missing prerequisite halt the whole wave. This revision
corrects both — it labels the three roles, assigns E0 implementation to E-eng, and makes the
corrected E1 the evaluator's responsibility.

---

## Role split

```text
E-eng:
  Inspect the INT-assigned engineering base.
  If E0 is absent there, implement E0 within the authorized E surfaces.
  Run focused development tests.
  Request live-command dispatch through INT.
  Do NOT run the held-out operator measurement.

S/E-op or designated E evaluator:
  Run E1 against a frozen cut carrying E0 and its invocation path.
  Do NOT modify the implementation.

CUR:
  Maintain the source specification and evaluator-side expectations.
  Do NOT implement E0, and do NOT claim clean-room blindness after seeing the oracle.
```

Keep any substrate-absence finding **scoped to the inspected ref** (initial observation at
`43369fd`: no module defining the explanation constructors was present on that lane). Re-inspect
on the INT-assigned engineering base before treating it as current — the absence has not been
confirmed there.

---

## E-eng: build E0 on the authorized base

E0 is the **explanation substrate implementation** (`E-CODE-EXPLAIN-FROM-PLAN` and its
constructors). G/I contributes proof artifacts that E consumes; it does **not** supply the
explanation implementation, so E-eng owns building E0.

Work:

1. Inspect the INT-assigned engineering base; record the base ref.
2. If E0 is absent there, implement the substrate within the authorized E surfaces:
   - `ExplanationPlan(audience, goal, spine, core_idea, key_invariant)`
   - `ExplanationSpine(goal, steps, baseline_cost)`
   - `CoreIdea(goal, idea)`, `KeyInvariant(problem, invariant)`
   - `RepresentationShift(source, target, reason)`
   - `BridgeLemma(lemma, role)`, `NaiveFailure(goal, obstacle)`
   - `SpineStep(rule, verdict, fanout)`, `AudienceLevel(...)`
3. Ground against the E2 target in `CUR-EXPLAIN-E2.md`. **Preserve these checks** (do not drop
   them on revision):
   - valid zero-step successful proof → valid plan with zero steps;
   - non-closing plan → explicit refusal, not an empty-silent `EmptyList`;
   - `RenderPlan` → at least one sentence;
   - **no call into `evaluated_search`** on the explanation path.
4. Run focused development tests (development suite, not the held-out operator measurement).
5. Request live-command dispatch through INT.

Do NOT run the held-out operator measurement. Do NOT edit `CUR`-authored specs.

---

## E evaluator: execute the corrected E1 test when its inputs exist

E1 acceptance is **explanation transfer**, not proof transfer. Proof replay validates the input;
explanation checks validate the output. Neither substitutes for the other.

```text
E1 — explanation transfer

Input:
  A saved, checker-replayed invariant proof withheld from explanation
  development, plus a separately maintained explanation oracle.

Execution:
  Invoke the explanation entry point on that proof.
  Do NOT launch a new proof search to manufacture the explanation.

Check:
  1. KeyInvariant identifies the correct observable and preservation claim.
  2. RepresentationShift identifies the correct source and target
     representations, with supporting evidence.
  3. Every rendered sentence maps to an existing derivation or explanation
     node, and its assertion is supported by that node.
  4. An out-of-library proof receives an explicit machine refusal.
  5. Existing explanation fixtures do not regress.

Record:
  Frozen tag and commit; proof artifact; oracle artifact; invocation;
  rendered output; sentence-to-node support map; exact failure set.
```

Note on observables: the coin pack supplies `HeadsCountParity` as its `phi` and preserves that
term in its rules, so it can support an explanation fixture. Using it does **not** demonstrate
**discovery** of the observable. Record what was withheld **from explanation development** rather
than calling the whole coin problem unseen.

---

## Failure handling (a missing prerequisite does NOT stop the wave)

```text
Missing substrate:
  E1 NOT RUN — prerequisite absent.
  Route the implementation item to E-eng.

Explanation acceptance failure:
  Preserve the failed artifact and report the specific criterion.
  Do NOT tune the implementation against an exposed held-out fixture and
  reuse that fixture as fresh transfer evidence.

Other authorized engineering, tooling, curriculum, and audit work continues.
```

Absence is not evidence that a functioning substrate merely summarizes.

---

## Report block

```text
  lane  : arena/01a066cf-cat-theo-machine
  base  : <E-eng inspected engineering base ref>
  e0    : present | implemented by E-eng (base ref) | absent
  e1    : NOT RUN (prerequisite absent) | RUN (frozen cut carrying e0)
  e1    : pass | fail — criterion <n>, artifact <path>
  preserved-checks: zero-step valid | explicit refusal | RenderPlan sentence |
                    no evaluated_search on the explain path
  classification: NON-SEMANTIC (E-eng/E-evaluator work, docs-only here)
```
