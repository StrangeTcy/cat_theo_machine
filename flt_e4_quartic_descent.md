# W6 — FLT n = 4 quartic descent

Fermat's last theorem at exponent four: no positive integers `x, y, z` satisfy
`x^4 + y^4 = z^4`. The pack is `packs/flt-quartic.pack.yaml` and its suite is
`validation/test15_flt_quartic_descent.py`.

Nothing in this encoding searches for a solution, enumerates a descent chain, or writes a
witness value into a rule. There are two machine-native facts, and each is checked
separately.

## The parity obstruction is the sweep's, not the pack's

Modulo 4, a square is `0` or `1`, so a fourth power is `0` or `1`; a sum of two odd fourth
powers is `2`. The two images are disjoint. That statement is not asserted anywhere in this
work: it is what the W3 Cartesian sweep discovers on its own. Running
`RunPlaygroundCartesianSweep` over the domain `[0, 11)` with modulus `4` yields

```
1-ary Image Projection:   f([x])     = x^2 mod 4        -> {0, 1}
2-ary Image Projection:   g([x, y])  = (x^2 + y^2) mod 4, odd subdomain -> {2}
Disjoint Image Regularity: {0, 1} /\ {2} = empty
```

`test15` re-runs that sweep and then asserts the linkage in both directions: the pack's
start reading `ParityMod4Invariant(one)` is a residue the sweep produces, and the goal
reading `ParityMod4Invariant(two)` is the odd-sum residue, outside the square image. The
pack cites the discovery; it does not restate it.

The pack's `phi` is `ParityMod4Invariant(?p)`. `quartic_residue_is_invariant` rewrites
`x^4 + y^4 = z^4` into `(x^2)^2 + (y^2)^2 = (z^2)^2` and carries the reading `p` through
untouched. With that rule in hand `ReachabilityPrune` refuses the goal outright:

* `IsInvariant` holds, `PhiHolds` holds on the start, and the two readings differ (`1` vs `2`),
* `SearchWithInvariant` reports `Unreachable` with `expanded == 0` — the obligation is
  discharged without a single expansion,
* `Prove(start, goal, rules, heuristic, registry, phi)` returns the same unreachability record
  in under a second,
* a goal whose reading *equals* the start reading is **not** pruned, which is the negative
  control for the whole mechanism.

## The descent

`x^4 + y^4 = z^4`, primitive, `x` odd, `y` even. Then `(x^2, y^2, z^2)` is a primitive
Pythagorean triple with odd leg `x^2`, so with coprime `m > n` of opposite parity,

```
x^2 = m^2 - n^2        y^2 = 2mn        z^2 = m^2 + n^2
```

`m - n` and `m + n` are coprime (`gcd(m-n, m+n)` divides `2m` and `2n`, and both factors are
odd), and their product is the square `x^2`, so each is a square: `m + n = r^2`,
`m - n = s^2`. With `n = 2v^2`, re-parametrizing the triple `(s, 2v, r)` gives `u` with
`u^2 = p^4 + q^4`, and `z = u^4 + 4 p^4 q^4` is strictly above `u`. A smaller solution of the
same equation, from a solution assumed minimal. Peano `NatLess` is well founded, so the chain
cannot start: hence `NoSolution`.

Five rules carry that, in order:

| rule | consumes | produces |
| --- | --- | --- |
| `quartic_solution_is_primitive_triple` | the solution, coprimality, leg parities | `PrimitiveTriple(x^2, y^2, z^2)` and the parities of the squared legs |
| `primitive_triple_parametrization` | the triple, odd leg, even leg | `Parametrizes(m, n, a, b, c)`, `Coprime(m, n)`, opposite parities, the three equations |
| `coprime_factor_of_square_is_square` | the square identity, coprimality, parities | `m + n = r^2`, `m - n = s^2` |
| `quartic_descent_relapse` | minimality, the coprime squares, the hypotenuse identity | the smaller solution, `NatLess(u, z)`, `DescentStep(z, u)` |
| `no_infinite_descent` | minimality, the smaller solution, the strict decrease | `NoSolution(Four)` |

Every witness (`m`, `n`, `r`, `s`, `p`, `q`, `u`) is a **Skolem seed** of the lemma that
introduces it — `ParamMSeed(a, b, c)`, `SquareRSeed(m, n)`, `RelapseUSeed(m, n)`. No rule
invents a variable it does not bind from its premises, and no rule re-fires: each one
consumes at least one fact it does not write back, which is what keeps the replay
deterministic. The derivation is five steps, replayed by `BuildDerivation`, and its end
state covers `NoSolution(Four)`. The last step is required to cite `NoInfiniteDescent` and
`NatLess` among its premises; the suite checks that structurally rather than by trusting the
goal.

## What the machine checks about the algebra

The named lemmas are not taken on faith. `test15` instantiates them and hands every identity
to the machine's own arithmetic:

* `(m - n)(m + n) = m^2 - n^2`, `a^2 + b^2 = c^2` for the parametrized `a, b, c`, and
  `IsCoprime(m - n, m + n)` by machine GCD — on `(m, n) = (2, 1), (3, 2), (6, 1)`,
* `r^2 + s^2 = 2(p^4 + q^4)`, `r^2 = s^2 + 4p^2q^2`, and `NatLess(p^4 + q^4, u^4 + 4p^4q^4)`
  — on `(p, q) = (2, 1), (3, 2), (7, 2)`,
* `u < u^2` for `u = 2, 3, 4`, which is what turns a decrease in the square into a decrease
  in the witness,
* squares mod 4 in `{0, 1}` for `x = 0, 1, 2, 3` and odd fourth powers `= 1 mod 16` for
  `x = 1, 3, 5, 7`.

The two things that are *not* computed are exactly the two that cannot be: the
well-foundedness of `NatLess` (cited as `NoInfiniteDescent`, the same way the Engel E2 pack
cites the arithmetic sum `1 + 2 + ... + 2n = n(2n+1)`) and the lemma that a coprime factor of
a square is a square (cited by `coprime_factor_of_square_is_square`, whose hypotheses *are*
machine checked as above).

## Purity and negative controls

The descent start state names no numeral at all — six facts, all labels and names. The suite
checks every argument slot of those six facts against `IsNat` and pins each argument chain
length, so nothing in the start state can hide a numeral; the goal and the one-argument
`NoSolution` shape are checked the same way. There is no solution
constant and no board to enumerate. Two negative controls guard the conclusions:

* drop `MinimalSolution(z)` and the descent produces no plan,
* ask for a residue the sweep already has, and `ReachabilityPrune` refuses to prune.

## Wiring

The pack is loaded by `main.py` at boot. The theorem agenda reaches it under the filters
`flt`, `flt-quartic`, `fermat`, `e4`, `dimension1`, `dim1`, and the parity obstruction case
also under `all`. The descent case is deliberately gated to the FLT filters: `Prove`'s
planner walks it breadth-first and takes minutes, while the rewrite engine replays the same
five steps in about four seconds, which is the route `test15` exercises.

## Repairs made along the way

`core.py` needed no change, but `labels.py` gained fifteen labels
(`QuarticSolutionLabel`, `MinimalSolutionLabel`, `PythagoreanTripleLabel`,
`PrimitiveTripleLabel`, `ParametrizesLabel`, the seven seed labels, `DescentStepLabel`,
`NoSolutionLabel`, `NoInfiniteDescentLabel`), all registered in `sync_from_namespace` so
surface and story code can see them. `ParityMod4InvariantLabel` and `DisjointImageLabel`
were already present, added by W3, and this pack is their first consumer.
