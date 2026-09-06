# Unified Arena-Agent Charter v2: Five Tracks, One Instrument

Tracks: **S** self-improvement · **E** explanation · **F** FLT · **G** Engel strategies · **I** IMO problems.

Everything in v1 (§0 constraints, §1 pre-flight, freeze discipline, report format) stands unchanged. This document adds G and I and rewires the couplings, because the two new tracks are where the other three finally pay rent together.

## 1. Why five tracks are one program

```text
G  teaches the machine reusable proof METHODS (invariance, extremal, pigeonhole, ...)
I  supplies held-out PROBLEMS on which those methods must pay rent
S  compresses repeated method applications into induced laws and learned policies
E  explains solved I-problems and adopted S-laws in student-level language
F  is the hardest I-problem, run once, under the strictest blind protocol
```

Engel is the trainer’s curriculum. IMO is the exam. S measures whether the machine got faster by itself. E measures whether it understood. F measures whether the whole apparatus can characterize what it lacks on a problem nobody has taught it.

No track may claim success in isolation from at least one other. A strategy the machine never applies to an unseen IMO problem is decoration. An IMO solve whose derivation carries no strategy certificate is a lucky search. An induced law that never shortens an IMO proof is noise.

## 2. Track isolation (extended)

| Track | Touches | Must not touch |
|---|---|---|
| S | mining, schemas, provenance, tests | talk dispatch, packs, explanation, problem packs |
| E | `explanation.py`, render laws, fixtures | mining, residual compiler, packs |
| F | checkpoint tooling, grading script, protocol | generators, packs, parser branches |
| **G** | planner methods/alternatives, strategy-obligation terms, `engel-strategies.pack.yaml`, tests | mining internals, residual compiler, any FLT-adjacent content |
| **I** | `TrainingRecord`s, `imo-*.pack.yaml`, record loader fixes only | any solver code, any strategy code, any generator |

Hard rules for the two new tracks:

- **G adds methods as planner data, never as `Knowledge` facts.** No `EvaluateProblem`, no `UsesStrategy` in the fact store. A method is a `PlannerAlternative` that spawns ordinary obligations discharged by the existing prove/search path.
- **I adds zero solver code.** If an IMO problem needs a mechanism the machine lacks, I records a `Blocked(problem, missing_capability)` term and hands it to G (if it is a method), to F-style live teaching (if it is a theorem), or to the operator (if it is a new concept). I never writes the mechanism.
- **G and I share nothing with F’s blind session.** Any Engel example or IMO problem that is FLT-shaped (variable-exponent Diophantine impossibility) is quarantined from G and I until Experiment 4 has been spent.

## 3. Track G — Engel strategies as planner methods

**G1 — method terms.** Add only:

```text
Invariance(observable, moveset)
Extremal(family, measure, direction, variation)
Pigeonhole(domain, codomain, assignment)
Divide(parts, combine, rank)
Symmetry(transformation, domain)
```

as `PlannerAlternative` payloads. Each expands into a fixed obligation skeleton discharged by ordinary search. `Symmetry` v1 uses declared transformations only; no automorphism computation.

**G2 — one worked Engel example per method, hand-curated.** E2 blackboard parity (Invariance), longest-path-gives-cycle (Extremal), n+1 integers two congruent mod n (Pigeonhole), binary words with no adjacent ones (Divide), one rotation-invariant coloring (Symmetry). Each becomes a `TrainingRecord` with the method supplied as `strategy_hint`. Acceptance: derivation contains the method’s obligation skeleton and every obligation is discharged by existing laws; ablating the method makes the record fail.

**G3 — recognition as learned policy, not hardcoded dispatch.** Do not add `if goal contains "repeated process" then Invariance`. Recognition enters only through S’s intervention-episode machinery: after ≥2 episodes where a trainer-supplied method succeeded on structurally similar problem shapes, S may propose a `LearnedMethodPolicy(residual_pattern, method)`. The policy suggests; it never selects silently; it obeys disable/enable/reset.

**G4 — negative control.** For each method, one decoy problem whose surface shape resembles the method’s trigger but whose solution needs a different method. The learned policy must not fire, or must fire and fail the rent test and be recorded as such. A method that “solves” its decoy by producing an unsound derivation is defect, not success.

**G5 — second example per method, held out.** The method is taught; the problem is not. Acceptance: the planner alternative closes the held-out problem with the method’s certificate in the derivation.

**Stop:** no Engel chapters beyond the five methods; no automatic strategy discovery from prose; no strategy-to-`Knowledge` leakage.

## 4. Track I — IMO problems as the exam

**I1 — problem format.** Every problem is a `TrainingRecord` with: surface statement, formal goal, givens, optional `strategy_hint` (empty for exam problems), expected outcome, and a `Tier`:

```text
Tier0  Engel warm-ups (G’s own examples; never held out)
Tier1  easy IMO/shortlist reformulations solvable by one method
Tier2  two-method compositions
Tier3  problems requiring a concept the machine lacks (recorded as Blocked)
```

**I2 — curation order.** Tier1 first, minimum ten problems, ≥2 per method, hand-formalized by the operator. Every formalization checked the way pre-flight checked A1: does the goal compile, does at least one existing rule partially match. Parsing is not evidence.

**I3 — exam protocol.** Held-out Tier1 problems run with `strategy_hint` empty. Three outcomes per problem:

```text
Solved(problem, method_used, derivation, cost)
Blocked(problem, missing_capability)       -- concrete residual, per F’s residual standard
UncharacterizedStall(problem)              -- honest ignorance
```

`Blocked` is a routing term: method gap → G; theorem gap → live teaching per F protocol; concept gap → operator. A `Blocked` with a fabricated capability name is a defect.

**I4 — rent measurement across tracks.** For every solved problem, record whether an S-induced law fired (step count with/without under ablation) and whether a G learned-policy suggested the method. These two numbers are the cross-track rent ledger: they are the only evidence that S and G pay rent outside their own fixtures.

**I5 — Tier2 only after Tier1 solve rate is stable across two cuts.** Tier3 problems are logged, never attempted as solves; their `Blocked` terms drive the concept curriculum.

**Stop:** no Tier3 mechanism-building inside I; no FLT-shaped problems; no solve claimed without a derivation the proof checker replays.

## 5. Couplings (mandatory, checked every turn)

| From → To | What flows | Check |
|---|---|---|
| G → I | methods as planner alternatives | held-out Tier1 solved with method certificate |
| I → G | `Blocked(problem, method_gap)` | new method scoped and added only if ≥2 problems block on it |
| I → S | solved derivations become traces | S mines them; induced laws must pay rent on later I problems |
| S → I | induced laws, learned method policies | ablation on I problems shows speedup vanishes on reset |
| I → E | solved problems become fixtures | held-out explanation names the method and invariant |
| G → E | method obligation skeletons | E renders “why this method” from `NeededFor`/`BridgeLemma` |
| I → F | grading script and residual standard reused | `Blocked` terms graded by the same role table |
| F → I | live-teaching discipline | any theorem taught to unblock an I problem is provenance-tagged and residual-justified |

A track with no flow in either direction for two consecutive turns is stalled; report it as such.

## 6. Interleaving schedule (per turn)

1. **F audit** of any new operator transcript.
2. **I exam** on any newly curated held-out problems (cheap; produces `Solved`/`Blocked` routing for everything below).
3. **G** one phase, prioritized by I’s `Blocked(method_gap)` count.
4. **S** one phase; mine any new I derivations first.
5. **E** one phase; explain the newest I solve or S adoption.
6. **F tooling** one item.
7. Suite, commits per track, tag re-cut only if code changed.

## 7. Report format (extended)

```text
remote tip before/after, tag, sandbox resets this turn + artifacts re-derived
pre-flight: exception mechanism = <named> | open
[S] phase, tests, suite delta
[E] phase, held-out result, fixtures
[F] tooling item; audits by regime
[G] phase; methods live; negative-control results; held-out solves
[I] problems curated (tier); exam: Solved/Blocked/Stall per problem;
    cross-track rent: S-law fired (y/n, steps ±), G-policy suggested (y/n)
couplings active this turn: <list>; stalled tracks: <list>
defects found by running: numbered, with locus
not built (deliberate): list
blocked on operator: list
```

## 8. Acceptance sentences

- **S:** a held-out proof closes in fewer steps by a machine-written law; speedup vanishes on reset, returns on restore.
- **E:** a held-out proof’s explanation names the right invariant and representation shift, every sentence traceable; an out-of-library proof is declined, not summarized.
- **F:** a blind session yields a discovery-eligible request with measured unlock, zero computable requests, residuals distinct from the decoy.
- **G:** a held-out problem closes through a trainer-supplied method’s obligation skeleton, the method certificate is in the derivation, ablating the method breaks the solve, and the decoy does not fire.
- **I:** Tier1 solve rate on held-out problems is reported honestly with `Blocked`/`Stall` counts; at least one solve is shortened by an S-induced law and at least one method was suggested by a G learned policy — both confirmed by ablation.

## 9. Operator obligations

The agent builds and audits; the operator supplies mathematics and runs blind sessions. For the two new tracks the operator owes:

- hand-formalized Tier1 IMO problems, ten minimum, checked for compile-and-partial-match before hand-off;
- the five Engel worked examples in `TrainingRecord` form;
- approval or rejection of every learned method policy S proposes;
- the decision, when an I problem returns `Blocked(concept_gap)`, of whether to open a concept session or park the problem in Tier3.

The single rule governing all five tracks remains the one from the start: nothing counts until it appears and disappears with the structure claimed to produce it.
