# D11-PORT — first shipped content port

Commit 2 of the D11 repair. The capability (commit 1, `e0853a9`) is untouched;
this is content: one pack, one label, one proven probe.

```text
pack:         packs/arithmetic.pack.yaml
surface map:  ExprEqLabel -> eq        (one label; constructor heads only)
probe G:      (eq (pow t 6) (pow (pow t 2) 3))      non-FLT
matches:      before 0   after 1   ablation 0
```

## Acceptance sentence, met

> A non-FLT probe goal that previously had partial matches 0 under
> library-only cold start gets partial matches ≥ 1 after an opt-in `surface:`
> port of the minimal pack that owns that probe's relation head — and returns
> to 0 when those `surface:` declarations are removed.

## Numbers

| run | state | cost | partial matches | matched rule | origin |
| --- | --- | --- | --- | --- | --- |
| before | no pack declares `surface:` | 334 | **0** | — | — |
| after | `arithmetic` declares `ExprEqLabel: eq` | 334 | **1** | `arithmetic/arithmetic_equation_is_symmetric` | primitive (pack rule) |
| ablation | `arithmetic` reverted to HEAD | 334 | **0** | — | — |

Fresh process and cold boot each time. Logs:
`logs/d11-port-arithmetic-{before,after,ablation}.log`.

The winning rule is the pack's own equation-symmetry law:

```text
arithmetic_equation_is_symmetric
  pattern      eq(?left ?right)
  replacement  eq(?right ?left)
```

Both arguments are variables, so only the **head** had to be mapped. That is
why the port is one label: the argument positions bind as they are, and
mapping them would have been content work the probe never asked for.

## Why this pack, and why not the one previously recommended

Discovery overturned the earlier recommendation. `number-theory` was proposed
on the strength of `DividesLabel -> divides` being attested in the goal
vocabulary — but **all eight of its rules conclude `list`**, not a `divides`
application, so no rule there can ever be a candidate for a `(divides …)` goal
no matter what the header says. Mapping `DividesLabel` there would have mapped
premise heads and produced zero candidates: a port that looks successful and
measures nothing.

The port was then picked by measurement against rules whose **conclusion**
head has an attested goal name (`protocol/D11-PORT-CANDIDATES.md`). Of the
candidates, `arithmetic` / `ExprEqLabel -> eq` is the smallest: one pack, one
label, and a conclusion whose arguments are variables, so the probe needs no
argument mapping and no new vocabulary.

## Scope held

```text
ported:        arithmetic only (1 pack, 1 label)
not ported:    the other 12 packs — digests byte-identical
rewritten:     no rule body; only the pack header
search:        untouched
matcher:       untouched
planner:       untouched
parser:        untouched
global table:  none; the mapping is pack-local and opt-in
FLT words:     zero occurrences of fermat/flt/nosolutions/wiles/frey
               in any pack declaring surface: (gate P4)
```

## Gate

`python3 tools/d11_gate.py` — **8/8**:

```text
1. unported packs unchanged; ported pack drifted as intended    PASS
2. {sym:} heads, no header                          -> 0        PASS
3. {sym:} + surface: header                         -> 1        PASS
4. unrelated goal                                   -> 0        PASS
5. char-form fixture         DIAGNOSTIC ONLY, never cited
P1. ported probe -> >=1, attributed to the port                 PASS
P2. ablation (surface: stripped) -> matches return to 0         PASS
P3. no unported pack digest drift                               PASS
P4. no FLT vocabulary in any ported pack                        PASS
```

Condition 1 changed shape and needs saying plainly: it used to assert that the
shipped-167 digest equals its pre-change baseline. After the port that cannot
hold — the ported pack's rules are *supposed* to recompile. Condition 1 now
asserts the stronger, per-pack claim: **every unported pack keeps its pre-port
digest, and the ported pack is expected to drift and does.** Per-pack digests
live in `protocol/d11-spike/shipped-pack-digests.txt`, recorded before the
port. The global shipped-167 digest recorded at the same time was
`786cff5c…`, identical to the pre-capability baseline, which is the evidence
that the capability commit alone changed nothing.

Pins 305/218/0 PASS. The four pack-booting tests pass on the ported tree.

## Classification

**SEMANTIC.** Match behaviour changes: a library rule is now a candidate for a
goal it previously could not see. This commit does not cut a tag — INT does —
and after it lands the sequence is: full two-shard suite, cut the next tag,
classify the port as semantic, operators re-baseline, then blank controls
before any F measurement counts.

## Deliberately not done

```text
bulk port of the 167        no -- one pack only, per §3.1
Expr* family beyond eq      no -- per-symbol ruling needed (see candidates doc)
forall/implies decomposition no -- file a NEW defect only if a post-port probe
                                  with a correctly surfaced head still shows 0
nosolutions introduction    no -- pre-flight item 2 stays blocked until matches
                                  work at all; this commit is the first "work"
FLT / decoy / target probes no -- non-goal by instruction
tag cut                     no -- INT cuts tags
```


## Scope limit (verified by degenerate and discriminating probes)

This port demonstrates **head-vocabulary alignment only**. The probe
`(eq (pow t 6) (pow (pow t 2) 3))` exercises none of its arithmetic
content: the matching rule is `arithmetic/arithmetic_equation_is_symmetric`,
whose conclusion is `eq(?right ?left)`, and it is a candidate for any `eq`
goal whose arguments are structured terms.

Measured in the ported state, fresh process and cold boot each run:

| probe | partial matches |
|---|---|
| `(eq (pow t 6) (pow (pow t 2) 3))` — the accepted probe | 1 |
| `(eq (pow s 6) (pow (pow s 2) 3))` — variable renamed | 1 |
| `(eq (plus a b) (plus b a))` — different structure | 1 |
| `(eq (pow t 5) (pow (pow t 2) 3))` — **false** identity | 1 |
| `(eq 1 2)` — Nat-literal arguments | 0 |
| `(eq 0 0)` — Nat-literal arguments | 0 |

The false-identity probe is the load-bearing control: the match does not
depend on the exponent identity being true, so the probe's exponent
content is not exercised. Goals whose arguments are evaluated Nat literals
never reach the rule-candidate path, which is why `(eq 1 2)` reads 0 and
why a literal-only goal is not a valid degeneracy control for this port.

Evidence: `logs/d11-port-degenerate-control.log`.

## Note on the preflight "expected zero" check

The D11 content-port brief expects zero shipped packs declaring `surface:`
before port work begins. That expectation is stale on this branch: the
completed port arrived by fast-forward from `arena/01a06542` as `768ea6f`
(StrangeTcy, 2026-09-05T02:18:57Z). A later session running preflight will
find one pack already declaring `surface:`; that is the completed port,
not drift. Confirm with `git log -- packs/<pack>.pack.yaml` before
escalating it. Update the brief rather than relitigating the finding.
