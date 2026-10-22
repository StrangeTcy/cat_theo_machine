# blank-controls-post-D11.spec

Docs deliverable. Not a session. Not run on this base. F-op runs it
in a fresh process after `experiment-5-frozen-r2` is cut.

## ritual

```text
1. fresh process, tag experiment-5-frozen-r2 only
2. research mode on
3. load theorem packs
4. audit knowledge
     packs loaded, taught 0, episodes 0, policies none
     loaded-class list present
5. three probe goals, one process, no teaching between them
```

## probes

```text
probe 1 — pre-D11 zero-partial-match goal
  attempt goal: (anglesum euclideantriangle straight)
  pre-D11: cost=0, partial=0, zero-successor-root  (packs off)
           or the packs-on sibling if packs are loaded

probe 2 — goal that used a taught conclusion-rule in an A/B log
  attempt goal: (tag a)
  with axioms only if the original toy session's axioms are restated
  as DOMAIN_AXIOM in this script; otherwise skip restating and use
  the library-closed sentence INT names at cut time
  expected on r2: partial-match count >= 1, otherwise D11 is a null

probe 3 — goal never before attempted
  attempt goal: (zorblewidget x y)
  parser success is not evidence; record cost, partial-match, residual
```

Probe 2's concrete sentence is a placeholder. INT substitutes the
library-closed sentence at cut time. F-op does not invent a teach to
make probe 2 fire.

## expected on r2

```text
partial-match counts change from 0 to >= 1 for at least probe 2
otherwise D11 fix is a null
```

## emitted artifact

```text
logs/blank-controls-r2-<operator>.log
```

Then F3-batch the r2 blank log against SILENCE-0 and SILENCE-334.
Leaving those classes is the measurement that D11 paid rent.
