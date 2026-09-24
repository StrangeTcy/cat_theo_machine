# Researcher-v0 — G1 (Domain gate) report

Status: **domain built, nothing certified**. G1 delivers the inert token-count
domain and the ruleset-content fingerprint required by A1.2 / A2.2, plus the
operational replay procedure required by A2.1. No invariant was proved, no
certificate was minted, no search ran, no live path was touched.

## 1. Run identity

```text
agent:        Researcher-v0
branch:       arena/01a0d2fb-cat-theo-machine
base:         8094c461d7efa142b32a375c3db8a1ac23290436  (= HEAD at start)
              "Amend Researcher-v0 brief (A2, blocking for G1) ..."
              (commit 305b017 is NOT an object in this checkout; G0's
               inspection.md was already present in the base commit)
Python:       3.11.2
gmpy2:        2.3.1  (installed during G1; it was absent, so
              cat_theo_machine.gmprep / machine / graph / proof / invariance
              / math.peano / prettyprinting were unimportable. Restored to the
              version G0 inspected. Nothing in the repository was changed by
              this; no environment.yml edit.)
PYTHONPATH:   empty; the repository's parent (/home/user) must be on sys.path
              and imports are package-relative (`cat_theo_machine.*`)
Import order: machine-first, as G0 records (machine.py imports math.peano)
budget:       single session, single process, no background jobs
workers:      none (no worker pool is used in G1)
seed:         none needed; every construction is deterministic
artifacts:    researcher_v0/ only
live activation: none
```

## 2. What G1 built

| File | Contents |
|---|---|
| `researcher_v0/token_domain.py` | structural Peano numerals, the two-fact state, `R_even` / `R_plus` rule content, the inert applier, the move-record layout, reporting helpers |
| `researcher_v0/ruleset_digest.py` | the A1.2/A2.2 content fingerprint, the declared semantic/display partition, the inertness guards |
| `researcher_v0/chains.py` | chain operations (`Pair` chains, no Python containers): length, append, join, membership, index, drop, sorted insert, sort, emptiness |
| `researcher_v0/tests/test_g1_domain.py` | 23 tests as `Edge` classes |
| `researcher_v0/tests/run_g1_tests.py` | runner (exit 0 / 1, prints failing names) |
| `researcher_v0/g1_replay_procedure.md` | the A2.1 operational replay a later checker must perform |
| `researcher_v0/inspection.md` | G0 report, unchanged — read, not rewritten |

House idiom throughout: states, rules, records and test results are terms;
`Compare` / `IdentityCompare` / `Match` / `Instantiate` / `MergeBindings` /
`Knowledge` are the substrates used; no Python container, no `isinstance`,
`hasattr`, `type`, `__class__`, `lambda`, `global`, `__new__`, no helper
function and no module-level mutable state appears in the new code (each
operation is an `Edge` class with a `result`; every call site reads
`Class(args)()`). `core.py` was not edited; nothing was monkeypatched. The
only non-substrate imports are `hashlib` (used by the rest of the repository
in `programme_c/*`) and `os.path` (test file reading).

### Comparison discipline (corrected before this commit was accepted)

```text
terms            compared with machine.Compare, and for emptiness/identity of
                 EmptyList with machine.IdentityCompare — the same predicate
                 machine.py and proof.py use at every emptiness site.
predicate results compared by identity to machine.truth_value / false_value,
                 which is the substrate's own convention for the singletons
                 its predicates return.
Python identity  NOT used on terms. `term is M.EmptyList` and
                 `X is not M.EmptyList` appeared in a first draft and are
                 removed: they state a fact about one interpreter's object
                 graph rather than about the term, they bypass the identity
                 the substrate assigns, and they silently accept a non-atom
                 such as an index.
indices/counts   never occupy a term slot. Where a search reports "found at
                 position i", the position rides inside a term
                 (`Pair(position, EmptyList)`) or the search is split into a
                 hits-only and a misses-only test, so an emptiness question
                 never receives an int. `ruleset_digest.VarIndex`,
                 `token_domain.FirstPremiseWithoutMatch`,
                 `token_domain.RuleMovesCount` / `RuleMissesAt` were
                 restructured for exactly this.
payload tests    `atom() is None` and `payload == payload` are payload-level
                 facts (the fingerprint's refusal of payload-less atoms and
                 the text sort order), not term identity.
```

The ruleset digests are unchanged by that correction, since the encoding
reads `Head` of the wrapped index rather than the wrapper.

## 3. The domain

```text
numerals   Zero  = Pair(ZeroLabel, EmptyList)
           Succ(n) = Pair(SuccLabel, Pair(n, EmptyList))
           structural throughout; Compare gives exact identity
           (Compare(Zero, Succ(Zero)) is false)
state      Knowledge([Tokens(k), Parity(d)]), d in {Even, Odd}
           count = d + 2k tokens; k counts PAIRS
           the carried Parity fact is derived, and derived truthfully:
           parity = count mod 2 holds in every built state and after every
           applied rule (tested, not asserted)
rules      R_even = Add2, Remove2, Swap
           R_plus = R_even + Add1Even, Add1Odd
           every rule is a real proof.MultiRule term; the legality
           precondition lives in the premise (Remove2 matches only a
           Tokens(Succ(k)) fact, i.e. only states holding >= 2 tokens)
applier    matches premises against distinct facts, merges bindings with
           MergeBindings, instantiates the replacement with Instantiate,
           rebuilds Knowledge; the transition relation is derived from rule
           CONTENT, so the fingerprint covers exactly what executes
statuses   APPLIED | MISS   (this vocabulary has no third member)
```

`MISS` is an inapplicable move: not a crash, not a refutation, and not an
unreachability result. The only statuses the domain can emit are `APPLIED` and
`MISS`; `MoveVocabularyIsInert` asserts this over every (state, rule) pair of
both rulesets.

## 4. Fingerprint (A1.2 / A2.2)

Declared partition, in full:

```text
HASHED (semantic)
  - the Pair skeleton: premise count and order, replacement shape, arity;
  - every payload-carrying atom by its payload text, length-prefixed;
  - every declared value-less singleton by declared name (EmptyList, Truth,
    False, VarTag, ZeroLabel, SuccLabel) -- the whitelist is part of the spec;
  - variable SHARING, encoded as first-encounter traversal index, in ONE
    context spanning premises and replacement (machine.FindBinding compares
    the variable atom by identity, so sharing changes the successor state);
  - rule order is NOT hashed: the version is taken over SORTED per-rule
    digests, so permuting a ruleset is equivalent by construction.

NOT HASHED (display-only)
  - the `display` slot of a rule spec: it lives outside the content term,
    is unreachable from it by identity, and no display payload appears in the
    canonical content text (both checked);
  - variable NAME payloads: machine.Match._is_var_pattern reads only the
    VarTag head and the one-element tail, never the name slot.
```

`prettyprinting.PrettyTerm` is not used anywhere: its output is display text
and must not enter a content digest (inspection §3b).

Digests observed (blake2b-256, hex; the version is the digest of the
domain-tagged document over the sorted per-rule digests):

```text
R_even   15f5467c985c4dd9710e87b59b69788f3e2b23fb25f5320015589da844d2d68f
R_plus   533cb46bd134cd0c1bcaf87d03ba6b4a1a5395c331f1ba0f391921ed500d2b8d

Add2      4e8bab14763ca7a0127462d3a895f55b6f80ceea0e292f3837b1710218118927
Remove2   a81cea09bb3caa6574cbe2e77db2188dbb78383dfe44fd40bc82765990010a17
Swap      c285feb09b58c48b97f5681de9f7bc1eaa4a509c80a07c22e2190d7741041bd8
Add1Even  c62c54aa2d80c231f16b9b8b6276114c83cb54a4e7f624f4e3f5f6f838b1ac69
Add1Odd   681c31b5d7a7ea8930a493f28af0f95e562e3cd714aa14071b5e06c7db73f582
```

Sensitivity, each case a test:

| Change | Digest |
|---|---|
| rule order reversed | unchanged |
| display names replaced (`Add2` -> `display-0`, ...) | unchanged |
| variable names renamed (`k` -> `first`, sharing kept) | unchanged |
| `Add2` replaced by `Add1` shape | changed |
| `Remove2` precondition strengthened to two pairs | changed |
| semantic constant renamed (`Tokens` -> `Token`) | changed |
| `Add1Even` constant changed (Even premise -> Odd) | changed |
| replacement variable not shared with the premise | changed |
| ruleset `R_plus` (Add1 added) | changed |

Deliberate refusal: a value-less atom outside the declared singleton list
raises `UnsupportedTermContent` instead of being hashed by object identity. A
fingerprint that cannot be reproduced in another process must fail loudly.

## 5. Replay procedure (A2.1) — documented, not exercised

`researcher_v0/g1_replay_procedure.md` states the seven steps in order: digest
and scope check first; recompute `Preserves` per rule over exact rule content;
verify the recomputed result names the requested observer and ruleset; require
`PhiHolds(start)` AND `PhiHolds(goal)` with non-missing readings; compare the
readings; bind the record to (observer, start, goal, digest, checker version);
classify every failure as `OPEN_RESIDUAL` / `BUDGET_EXHAUSTED` /
`EXECUTION_FAILURE` / `UNSUPPORTED`.

G1 does not execute that procedure and does not claim a result from it.

## 6. Tests and results

```text
command:  cd /home/user && python3 -m cat_theo_machine.researcher_v0.tests.run_g1_tests
result:   passed: 23  failed: 0   (exit 0)
```

| # | Test | What it establishes |
|---|---|---|
| 1 | numerals: Zero..Three structural | Zero/One/Two/Three construct as structural numerals with counts 0..3 |
| 2 | numerals: pairwise distinct | `Compare` separates them; Zero is stable |
| 3 | states: no Python integers | every atom of every state and rule is a declared singleton or text payload — no `int`, no bool |
| 4 | states: count round-trip 0..7 | built count reports back, parity consistent |
| 5 | moves: Add2 n -> n+2 | applies at 0..3, count +2, state stays consistent |
| 6 | moves: Remove2 legal n -> n-2 | applies at 2, 3, 5; count -2 |
| 7 | moves: Remove2 illegal is a MISS | at 0 and 1: not applied, status MISS, reason `no_match`, no successor, no crash, no unreachability status |
| 8 | moves: Swap is identity | applies at 0..3 and returns a `Compare`-equal state |
| 9 | moves: parity carried truthfully | every applied successor of every R_even rule satisfies parity = count mod 2 |
| 10 | moves: Add1 perturbation | Add1Even applies exactly at even counts, Add1Odd exactly at odd counts; each adds one token and flips parity |
| 11 | moves: vocabulary is inert | every one of the 20 (state, rule) outcomes of R_plus has status APPLIED or MISS and nothing else |
| 12 | fingerprint: order independent | reversed spec chain, same version |
| 13 | fingerprint: display rename stable | all display names replaced, same version |
| 14 | fingerprint: variable rename stable | Add2 variable names renamed, same per-rule digest |
| 15 | fingerprint: deterministic | rebuilds agree, twice over, both rulesets |
| 16 | fingerprint: R_plus differs | adding Add1 changes the version |
| 17 | fingerprint: content sensitivity | Add2->Add1, stronger Remove2 precondition, renamed semantic constant, changed Add1Even constant, unshared variable — each changes a digest |
| 18 | fingerprint: 64 hex characters | digest shape, and one version per ruleset |
| 19 | partition: display outside content | no display atom is reachable from any rule content by identity |
| 20 | partition: display text not hashed | the display name is absent from that spec's canonical content text |
| 21 | checker shape: R_even preserves parity | `Preserves` succeeds for Add2, Remove2, Swap on the carried parity observer |
| 22 | checker shape: Add1 refutes parity | `Preserves` fails for both Add1 rules with a present reading on both sides |
| 23 | inertness: no unreachability vocabulary | the domain, digest and chain modules contain no `import invariance`, no `invariance.Preserves(`, no `ReachabilityPrune(`, no `IsUnreachable(`, no `UnreachableLabel` |

Tests 21 and 22 are statements about **rule content**: the domain is shaped so
a later checker can use it. They prove no invariant and issue no certificate.

## 7. Integrity

```text
core.py          untouched
Programme C      untouched, not imported (still unimportable: hyge_int_pkg)
Programme L      untouched
admission/rent/human hooks   not called, not imported
tags             not moved
live knowledge   not written
graph/search/machine/proof/invariance/prettyprinting   imported read-only,
                 never modified
files changed    researcher_v0/__init__.py, chains.py, ruleset_digest.py,
                 token_domain.py, tests/__init__.py, tests/run_g1_tests.py,
                 tests/test_g1_domain.py, g1_replay_procedure.md
files inside researcher_v0/ that G1 did NOT change: inspection.md
jobs run         none; no overnight job, no mining, no search, no admission
activation       none
```

Environment note, stated plainly because it is a real change to the sandbox
and not to the repository: `gmpy2` was missing, so the substrate was
unimportable. It was installed (2.3.1) to match G0's recorded environment.
No repository file was edited to work around its absence, and no module
imports it directly in the new code.

## 8. The distinction this report keeps

```text
domain built                 yes  -- numerals, states, rules, applier,
                                     fingerprint, partition, replay procedure
research result certified     no   -- no invariant proved, no certificate
                                     minted, no CHECKED_UNREACHABLE issued,
                                     expected baseline zero (A2.3) still zero
```

Passing the G1 tests is not evidence that an invariant exists, and it is not
reported as one.

## 9. Next bounded item

G2 (task generation) may build on `RulesetVersionOfSpecs`, `RuleFingerprintOfSpec`
and `TransitionTable`; it may not treat any G1 artifact as a research result.
