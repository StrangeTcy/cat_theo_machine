# Distribution: five tracks, one integrator

INT-owned index for the multi-agent programme. Written against
`5361a87b60159cd295ce622a72dd4ee3c9c3f9fe`, six commits past the frozen tag
`experiment-4-frozen` → `06c0e52ffd5a9206125ccdb207bffc4a14185636`.
It supersedes the draft of this file written at `06c0e52`, which described a
tree that was one commit behind and had no `explanation.py` and no `protocol/`.

Standing constraints (§0 of the v1 charter) are unchanged and apply to every
worker named here.

## RESOLVED — one integration branch

The previous report confirmed `arena/01a06274-cat-theo-machine` and pushed
`[SHARED]` commits to `arena/01a06542-cat-theo-machine`, a strict descendant
of it (`5361a87` → `bdf1822` → `e691c67` → `50042a5` → `0f15929` →
`cc8f803` → `7e11745`). Two names for one role is not survivable, so the
operator picked one.

**Integration branch: `arena/01a06542-cat-theo-machine`.** Agents branch from
its tip, push to their own arena branch, and file a merge request in their
report. `01a06274` is retired as a name for the role; do not branch from it.
Anyone who already did, rebases onto this tip before their next push.

---

## 0. Inventory at the integration tip

Measured from the tree, not assumed:

| Fact | Value |
|---|---|
| integration tip | `5361a87`, **untagged**, 6 commits past `experiment-4-frozen` |
| frozen tag | `experiment-4-frozen` → `06c0e52` |
| `explanation.py` | exists, 1,012 lines; 6 tests registered at `testsuite.py:17912–17926` |
| `research.py` / `provenance.py` | 4,021 / 1,518 lines |
| `research_protocol.md` | 119 lines; the cross-track index |
| `protocol/` | `README.md` + `S.md`, `E.md`, `F.md`, `G.md`, `I.md`, all stubs |
| `labels.py` | 3,174 lines; partition blocks at 3,158–3,171 |
| `testsuite.py` | 18,407 lines; class blocks at 16,249–16,262; registration blocks at 18,389–18,402; `install_default_tests` at 16,264 |
| `main.py` / `persistence.py` | 5,062 / 2,106 lines; **no partition blocks in either** |
| shard cursor | 295 `TestShardAccept` guards, 295 registrations; `learned_memory_checkpoint_test` sits at cursor index 218 → shard 0 |
| cursor-pinning sentinel | **not landed.** Both `[SHARED]` blocks in `testsuite.py` are empty; no shard or cursor test exists in the tree |
| pre-flight item 1 | closed at `da33a45`: the learned-memory checkpoint failure is nondeterministic under load — not contamination, not volume |
| subset test runner | absent. No name-based selection anywhere in the tree |
| checkpoints | `snapshots/library-only-control.json`, `snapshots/set-b-cumulative.json`, both named in `research_protocol.md` |
| checkpoint verbs | none. No `save checkpoint` / `load checkpoint`, no content-addressed ids |

Withdrawn from the `06c0e52` draft: T2 ("E has no home module") and the claim
that S and E must share one engineer. Both were artifacts of the stale tip.

---

## 1. The integrator rule

**One integration branch. Every worker branches from its tip, pushes to its own
arena branch, and files a merge request in its report. Only the integrator
merges, re-runs the two-shard suite, and cuts tags.**

Integration branch, confirmed by the operator: **`arena/01a06274-cat-theo-machine`**.
It is the furthest ahead, it carries the partition blocks and the pre-flight
closure, and the suite baseline is being run against it. Workers branch from
its tip, push to their own arena branch, and file a merge request in their
report. Only the integrator merges, re-baselines, and cuts tags.

Consequences that follow from the rule and bind today:

- **Workers never cut tags.** That includes the `experiment-5` naming question:
  it is decided at integration, after the suite number, not in a worker's plan
  document. This file names no future tag.
- **No operator session may run on the integration tip as it stands.** It is
  six commits past the frozen tag and untagged, and `research_protocol.md`
  makes a log spanning two tags inadmissible. Sessions run on a cut, after the
  integrator re-cuts and re-baselines.
- **A worker's branch is disposable.** Push every green step; a sandbox reset
  costs the unpushed commit and nothing else.

---

## 2. Where a worker may write

The partition that landed covers the two files that were fought over. It covers
one of the four registration points a new label needs.

| Registration point | File | Partitioned | Rule for a worker |
|---|---|---|---|
| label class definition | `labels.py` (E's are at 3,055+) | no | append at the tail of the class region, before the singleton region |
| label singleton | `labels.py` 3,158–3,171 | **yes** | append inside your own track block only |
| `sync_from_namespace` tuple | `labels.py` 2,473+ | no | **unmarked shared append point** — see D1 |
| `SNAPSHOT_SYMBOL_NAMES` | `persistence.py` 202+ | no | **unmarked shared append point, different file** — see D1 |
| test class | `testsuite.py` 16,249–16,262 | **yes** | your block only |
| test registration | `testsuite.py` 18,389–18,402 | **yes** | your block only, guard every registration |
| talk verb dispatch | `main.py` | no | adjacent-line hazard; request a `[SHARED]` verb table |
| track ledger | `protocol/<T>.md` | **yes** | one file per track; never edit another track's ledger |
| cross-track claims | `research_protocol.md` | integrator | a claim spanning tracks is written once, in the index |

Unpartitioned points are not free-for-all: they are `[SHARED]` requests to the
integrator, never local forks.

---

## 3. Defects

**D1 — label registration is unenforced, and the omission is currently inert.**
Measured, not inferred. Of the 526 leaf label classes declared in `labels.py`,
40 are missing from `sync_from_namespace`, 198 are missing from
`SNAPSHOT_SYMBOL_NAMES`, and 18 are missing from both: the thirteen added with
`explanation.py`, plus five that predate it (`ContextResearchAttemptsLabel`,
`GenDependencyRequestFromResidualLabel`, `GraphVersionLabel`, `KObligationLabel`,
`ReasonStaleLabel`). Four label families from four tracks are in that state, so
this is the fifth appearance of the class: a registration point is added, the
new family skips it, and nothing notices. The partition blocks make the
omission visible, not impossible — they cover one of the four sites.

The round-trip question is settled, and the answer is that the omission does
not currently bite. `tools/repro_label_roundtrip.py` puts one registered label
and one unregistered label in the same term, captures it, and restores it:
both atoms come back identity-identical, and all thirteen E labels do the same
in nested position. Capture does not consult `SNAPSHOT_SYMBOL_NAMES` to name
symbols, and restore resolves names through the runtime namespace. So this is
`D1_INERT`: cleanup debt, not urgent-before-checkpoint-work.

It stays a tracked defect because the debt is one commit away from being live.
`label_registration_completeness_test` (`[SHARED]`, registered after every
existing test so the shard cursor is untouched) walks every leaf class, asks
which tables each name is missing from, and pins the counts at 40 / 198 and
the eighteen names. A new omission moves a count and fails the suite; a repair
also fails until the pins are deliberately tightened, so paying the debt is a
recorded act. Tightening to the strict form — every leaf class in both tables
— is a one-line change once the integrator decides to clean up.

The pins are a record of the current gap, not a claim that registration is
complete. The target is `0 / 0 / 0`, the pin moves only downward, and a commit
that registers part of the debt updates the three constants in the same
commit. A passing run of this test means "no drift", never "complete".

Suggested `[SHARED]` fix, integrator's call: partition `sync_from_namespace`
and `SNAPSHOT_SYMBOL_NAMES` the way the singletons are partitioned — per-track
tuples concatenated at one point each — so a label added in a track block
cannot be omitted from the other two lists.

**D2 — the cursor-pinning sentinel.** Built as `test_shard_cursor_pin_test`
in the `[SHARED]` block: it walks `install_default_tests`, ticks a cursor at
every `TestShardAccept` guard, and pins the count, the index
`learned_memory_checkpoint_test` occupies, and its shard — 298 guards, index
218, shard 0. The walk starts at the function so that the pinned name in the
docstring is not counted. Pins verified statically against the tree without
booting the machine. The runner filter is unblocked by this and is verified
against it in both modes.

**The pin splits in two, one test, two answers.** The index and the shard are a
*hard* pin: `learned_memory_checkpoint_test` moving means a registration landed
before it, which is the partition rule breaking, so the test returns
`CURSOR_PIN_MOVED` and an integrator has to re-baseline the whole suite. The
guard count is a *soft* pin: it moves whenever anyone adds a test, and that is
intended, so the test returns `GUARD_COUNT_STALE` and the commit that adds the
registration updates the constant. A single pin taught workers to bump whichever
number failed, and the first time someone bumped the index the partition would
break silently. A failing test now names what it returned, so the two are told
apart in the runner output instead of only in the docstring.

**D3 — restored value atoms are not equal to their originals. Global scope,
not data loss.** Found while running the D1 repro, and settled this turn by
`tools/repro_d3_scope.py`.

Scope is global, not E-specific. In one capture, with a chain of registered
labels surviving as the passing control and the explanation obligation failing
as the failing control:

```text
zero (M.Zero)              survives
Succ(Zero), Succ(Succ(..))  LOST
GMPRep("42"), GMPRep("7")   LOST
taught MultiRule            LOST
numeral-bearing term        LOST
registered-label chain      survives   <- control
explanation obligation      LOST       <- control
```

Both stages on real state agree: after a save and boot, `all_rules` and
`rule_order` differ on a graph booted from packs, and ten of nineteen roots
differ on the Set B cumulative checkpoint, including `intervention_episodes`,
`dependency_requests`, `dependency_graph`, `derivations` and `last_proof`.

The nature of it is not what the first report said. The values survive:
`NatEq(restored two, fresh two)` is true and `NatEq(restored two, fresh
three)` is false, while `TermEqual(restored two, fresh two)` and
`IdentityCompare` are both false. Restore builds a new atom object per record,
and only named symbols get interned back to their singletons — so a label
chain survives `TermEqual` and a value-bearing chain does not, even though the
value is intact by the machine's own arithmetic.

Two consequences for the ledgers. Earlier "checkpoint round-trip PASS"
entries stand: they check non-emptiness and provenance, not `TermEqual`, and
the non-emptiness checks are unaffected. Any *future* round-trip test must not
assert `TermEqual` across a restore on value-bearing state — it has to compare
with a value-aware predicate, or compare named-symbol structure only. E-eng in
particular cannot write its round-trip tests the obvious way until this is
fixed or the convention is set.

**The mechanism, narrowed this turn.** Two freshly constructed Nats are the
same object: `IdentityCompare(nat 2, nat 2)` is true, and so is `TermEqual`.
Nats are interned at construction. Restore does not go through that interning
— it fabricates a fresh atom per record — so a restored two is not the
interned two. That is D3 in one line: restore bypasses Nat interning, and
every equality check over restored value-bearing state is false while the
value itself is intact.

GMPRep numerals are deliberately excluded. Two freshly constructed GMPReps are
already unequal, so their behaviour across a restore is not a restore defect;
folding them in would send whoever fixes this to the wrong place.

`snapshot_value_atom_identity_test` pins it: restore a Nat through the real
codec and compare with the interned Nat. It returns
`VALUE_ATOM_IDENTITY_OPEN` while the defect is open, and that sentinel is the
registered expectation, so the suite stays green and the gap is reported
rather than hidden — the same convention as the milestone checks. Fixing
restore flips the result to `truth_value` and fails against the expectation
until it is deliberately updated. Verified by running the test: it returns the
sentinel today.

The operator's call at step 3 is to fix before the tag, so this is the next
`[SHARED]` item: make restore resolve decoded atoms through the constructor
registry's interning rather than fabricating them.

**The fix is designed and not yet made.** The mechanism is interning on
restore: a decoded atom that represents an interned value has to resolve to the
machine's own atom for that value through the existing registry lookup path,
never a fabricated one. Reading `math/peano.py` to find that path turned up
what makes the obvious implementation wrong, and it is recorded here so the
commit starts from it rather than rediscovering it:

- `NatRepOf` accepts anything whose cached value stringifies. A restored `Char`
  carrying `"a"` returns `"a"` as if it were a numeral rep, so "call
  `NatRepOf` on every restored atom and intern what comes back" would try to
  intern Chars and raise inside the codec — on every snapshot, not on one. A
  rep is a rep only when it comes from a Nat-shaped record.
- `NatFromRep._discover` walks every registry entry and computes `NatRepOf` for
  each until it finds a match. Called once per restored Nat that is O(n²) over
  a checkpoint that already costs minutes to boot. It is reached only when
  `NatValueIndex` is missing or empty: `_from_value` looks the value up in
  `M.NatValueIndex` first and returns in one `TreeLookup`. The cost of the fix
  is therefore decided by whether the index is wired before the pass runs.
- and the ordering constraint, which is where the two meet. `M.NatValueIndex`
  is set in `Graph._sync_from_context`, so it points at the restored index
  only after `activate` has rebuilt the roots — not while `load_snapshot` is
  creating atoms, and not while `nat_value_index` is still in its pre-upgrade
  chain form. The pass belongs at the end of `activate`: walk
  `state.id_to_obj`, resolve each Nat-shaped atom through `NatFromRep` against
  the restored registry, substitute the fields that pointed at the fabricated
  atom, then re-point the roots through the mapping, because a root that *is*
  a Nat has no field to substitute. Interning earlier either scans the
  registry or, for values ≤ 256, builds a fresh chain from `Zero` and
  installs a second `2` into a graph that already has one.
- the Nat-shaped test has to be "the cached value is a decimal numeral", not
  "`NatRepOf` did not return `EmptyList`", for the reason above: a Char is not
  a Nat, and the codec has to be told so in a form it can check.

Scope of the commit, agreed: interning on restore, applied to every interned
family and not assumed to be Nats alone — labels through the namespace,
`Zero`/`One`/`Two`, any `Char` interning, anything identity-compared live. The
`__new__` and base-`Edge` Gate-B debt in `persistence.py` stays out: one
commit, one mechanism. The commit flips `snapshot_value_atom_identity_test` to
`truth_value` and updates the expectation in the same commit, which is what
takes the open count to zero, and re-runs `learned_memory_checkpoint_test` —
measured green before the fix (3.4 s, passes), so green afterwards is a
finding and changed is a finding that D3 and that failure are not independent.

**D3b — `PrettyTerm` does not terminate on a restored value atom.** A printer
that hangs is itself the diagnostic: the restored atom has a shape the
printer's Nat/Pair walk cannot exit, so the atom restore produces is not one
the printer can read. Filed separately from D3 because it is a printer
defect with its own reproduction, and because it removes the obvious tool for
inspecting D3: walk the two atoms with `IdentityCompare` and structural
comparison, and report the first position where comparison diverges. Do not
call `PrettyTerm` on a restored atom.

**D3c — `graph.add_node` parks nothing the codec sees.** `SnapshotCodec`
serializes the named roots in its capture table and nothing else, so a term
added with `graph.add_node` never reaches a snapshot — a registered control
atom vanished identically. Any future repro that "adds a control term" has to
place it under a named root, either a field the codec captures or an
`extra_roots` entry.

**D5 — GMPRep carriers are not interned.** Filed separately from D3, under Nat
calibration, because it was first recorded as an *exclusion* from D3 and that
was the wrong shape: the exclusion said "do not look here", and the right
statement is "this is broken here". Two freshly constructed `GMPRep("42")` are
already unequal before any snapshot is involved, so their behaviour across a
restore is not a restore defect — but `IdentityCompare` on a GMPRep carrier is
unsound in the live machine too, and nothing in the code says so. Every
comparison of a numeral has to go through `NatEq` or the structural Nat. It is
live, it is not D3, and it does not go in the D3 commit.

**D4 — root debris** (T0, below).

---

## 4. Roster

S and E are separable now: separate home modules (`research.py` +
`provenance.py` versus `explanation.py`), separate test blocks, separate
ledgers. What keeps them from colliding is the partition, not a shared
engineer.

| Worker | Kind | Owns | Blind to | Starts when |
|---|---|---|---|---|
| **INT** | integrator | merges, two-shard suite, tag cuts, `research_protocol.md`, this file, `[SHARED]` primitives, D1/D2 | nothing | now |
| **G-eng** | engineer | `planner.py` alternatives, strategy-obligation terms, `packs/engel-*.pack.yaml`, `[G]` blocks, `protocol/G.md` | F content, S mining internals | after the operator names the integration branch |
| **S-eng** | engineer | `research.py` mining/schema, `provenance.py`, `[S]` blocks, `protocol/S.md` | F content | same |
| **E-eng** | engineer | `explanation.py`, render laws, `[E]` blocks, `protocol/E.md` | F content | same |
| **G/I-op** | operator | authors `TrainingRecord`s, curriculum sessions, held-out exam sessions, `protocol/I.md` | F content, the sealed exam list until reveal | after G-eng lands one method |
| **F-op** | operator | decoy control, the one-shot, teaching only on concrete residuals, `protocol/F.md` | everything (§6) | after the decoy and a re-cut |

---

## 5. Staffing order

```text
INT: name integration branch, re-cut, re-baseline
        |
        ├─ G-eng methods ──── G/I-op curriculum records ──┐
        │                                                 ├─► exam sessions
        ├─ S-eng: unblocked now (research.py, provenance, │        │
        │   mining verbs, learned policies all live)      │        ▼
        │                                          derivation volume
        ├─ E-eng: unblocked now (explanation.py Phases 1–3,├──► S rent
        │   six pinned tests) but fixture-starved         └──► E fixtures
        │
        └─ F-op: decoy ──► one-shot   (independent chain, isolated)
```

- **G-eng is on the critical path.** Every derivation S mines and every proof
  E explains comes from a G method closing an I problem.
- **S-eng and E-eng both have real work today** and neither needs the other's
  output, which is the whole argument for separating them.
- **E-eng is starved of fixtures, not of work.** Six tests exist; a held-out
  proof to explain does not. The Phase 4 transfer test waits on G/I-op.

---

## 6. Session parallelism and the F firewall

**Parallel-safe** — different workers, different sandboxes, same cut, each from
its own cold declared checkpoint, each with a contamination-ledger header and a
pre-declared prediction: G/I curriculum sessions; S and E mining, rent, and
explanation-transfer sessions; the F decoy.

**Serial by nature** — cumulative episodes (Regime C), and the IMO exam after
the curriculum completes. One operator, in order, cumulative checkpoint named
in each audit.

**Isolated** — the F one-shot. Blindness is built, not promised: a redacted
clone of the cut, rebuilt per cut.

```bash
git clone --no-local --branch <cut-tag> <remote> f-blind
cd f-blind
rm -rf packs/engel-*.pack.yaml training_records/ logs/ protocol/
rm -f snapshots/set-b-cumulative.json
git commit -am "F-blind: curriculum, records, other-track ledgers, Set-B removed"
git tag f-blind-<cut-tag>
```

Only `snapshots/library-only-control.json` survives. When the one-shot is done,
INT ports `protocol/F.md` back and nothing else. Checkpoints are read-only
published artifacts; two operators never write the same one.

---

## 7. Open items

**T0 — root debris.** `graph.py.txt` (748 KB), `firing.py.txt` (76 KB),
`mining.py.txt`, `language.py.txt`, `deduction.py.txt`, `grammar.py.txt`,
`session.txt`, and `hyge.py`. Five agents grepping this tree will open
`mining.py.txt` and edit a dead file. Move them to `archive/`, do not delete:
they are the Aug 25 uploads and may be the only record of a divergent stack.
`hyge.py` is the string-rewrite session engine from the sieve demo, not
production runtime — quarantine it in `archive/` with a README line saying so,
and leave deletion to the operator. One commit, integration branch, before a
third worker is staffed.

**Runner gap — no name-based test selection.** Still the top throughput item:
every worker pays a full suite run to verify one class. Constraint on the fix,
as specified by the integrator: a name filter must bypass the cursor for
targeted runs while leaving the full-suite cursor path byte-identical, and the
cursor-pinning sentinel must pass in both modes. A filter that perturbs
registration order invalidates the baseline it was meant to speed up. The
sentinel exists now (D2), so the runner is unblocked and is the next
`[SHARED]` item after the branch decision.

**Sandbox resets — the wrong-base failure, six times.** A reset keeps the
working tree and drops git objects, so a session can wake up with a full tree
and a `HEAD` that no longer descends from the integration tip. The next commit
then goes in against the old base and shows up as 190 files and 359k lines;
only the rejected push catches it. Two fixes are in, both `[SHARED]`:
`tools/recover.sh` makes the check and the recovery one command (fetch,
`merge-base --is-ancestor` against the tip, save the diff and reset if it
fails, rebuild the venv, re-run the pin check), and `.gitignore` takes the
bytecode, search-compare scratch and cold-debug logs so a bad base diffs small
instead of enormous. The rule it encodes is the standing one and is not new:
**HEAD descends from the integration tip before the first commit of a
session.** Verify it before writing anything, not after the push is rejected.
It happened again this turn — the working tree was intact at `7acaf4c` while
`HEAD` sat at `41e8078` — and recovery took four commands instead of the
morning it took the first time.

**F1 — no `save checkpoint` / `load checkpoint`, no content-addressed ids.**
Noted only. It is F-tooling, owned by whoever takes F.

**Ordering, fixed by the integrator and not negotiable by a worker.**

```text
0. operator: one integration branch          DONE (arena/01a06542)
1. D2 sentinel                               DONE (298 / 218 / 0, split
                                             hard index+shard / soft count)
2. D3 scope run                              DONE (global; restore bypasses
                                             Nat interning)
2b. runner reports OPEN apart from PASS       DONE (three-way tally, both
                                             runners; D3's flip is visible)
3. D3 fix: restore resolves decoded atoms     NEXT [SHARED], blocks the tag
   through the registry's interning
   -- snapshot_value_atom_identity_test is the executable target
   -- design and two wrong-implementation traps recorded under D3
4. full two-shard suite on the integration tip
5. cut experiment-5-frozen; rerun manifest; rerun blank controls
6. T0 (archive .txt, quarantine hyge.py)
7. runner filter, verified against the sentinel in both modes
8. D1 cleanup toward 0 / 0 / 0, pins updated in the same commit
9. staff S-eng, E-eng, G-eng from the new tag
```

Operators stay blocked through step 5. T0 and the runner have not been
started.

---

## 8. Worker report block

Every worker ends every turn with:

```text
agent: <name>
branch: <own arena branch> @ <hash>   branched from: <integration tip> @ <hash>
touched: <files, with the block or module named>
tests: <block/module> N/N green; full suite: run by INT / not run
ready to merge: yes/no   blocked on: <none | SHARED: X | worker Y | re-cut>
measurement produced: none / <session id, classification>
merge request: <files> -> <integration branch>
```

A track with no cross-track flow in either direction for two consecutive turns
is reported as stalled, with the reason.
