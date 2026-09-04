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
| integration tip | `aed9c0e` |
| frozen tag | `experiment-5-frozen` → `aed9c0e` (annotated tag `5defc8d`) |
| previous tag | `experiment-4-frozen` → `06c0e52`, 27 commits below the new one |
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

**The three identity contracts at a boundary.** The earlier wording here
was too broad — "anything crossing a boundary loses identity unless it is
re-interned on arrival" — and the breadth is what sent the first attempt
looking for a payload test. A persistence boundary carries three different
contracts, and only one of them was broken:

1. *Sharing inside one serialized graph.* Two fields that referenced one
   object before capture reference one restored object afterwards. Restore
   has always done this.
2. *Named singleton identity.* `EmptyList`, `truth_value`, the labels, and
   the named Nats resolve to the existing runtime singleton. Restore has
   always done this too, and it is why a label chain survived while a Nat
   did not.
3. *Canonical-family identity.* An interned value resolves through its
   family's canonical index. This is the one restore skipped.

Arbitrary value-bearing atoms are not interned. Two unrelated atoms carrying
the same payload stay distinct. So D3 is specifically:

> Snapshot boot violated the canonical-family invariant for Nats.

It is not "all restored value atoms should preserve host identity". The
shard-queue sentinel is the same lesson one layer up and stays recorded:
compare by text or structure at a boundary, never by identity.

**D3 is closed. Fixed in `[SHARED]` commit bf5a2c7.** The class (b) choice
offered last turn was a false choice, and the answer was neither: preserve
Nat-ness explicitly in the snapshot representation, then canonicalize only
records known to have been Nats. The encoder knows which objects are Nats
before capture — `NatRepOf`, or the `SuccLabel` constructor when the rep is
gone — and that fact now travels in the record as a canonical-family
marker. Nothing infers Nat-ness from a payload, so a GMPRep carrier holding
2 and a Char carrying "2" are never asked whether they are numbers.

The boot is staged, because the order is the fix:

```text
1. decode records, carrying the canonical-family marker
2. restore named singletons and generic graph objects
3. activate: rebuild roots and constructor context
4. map each marked restored record -> canonical live Nat
5. rewrite every graph-owned root through that mapping
6. rebuild nat_value_index from the canonicalised graph
7. replace the context roots
8. validated by the eight tests below
```

Canonical authority is the live runtime: a named symbol when there is one,
otherwise `NatFromRep`, which is the interning entry point and registers what
it has to build. Restored copies are inputs to the mapping, not competing
canonical objects.

Measured, before and after, with `tools/repro_d3_interning.py`:

```text
pass disabled: visited 16696 terms, nats checked 5, mismatched 5
pass active:   visited 16696 terms, nats checked 5, mismatched 0
```

Both published checkpoints boot on the production path:
`library-only-control` in 4.8 s and `set-b-cumulative` in 3.7 s, no
duplicated numeric value in either, and the Set B value index comes back
fact-identical across two independent boots.

**Two live-machine findings the attempt turned up, both recorded and not
fixed here.** They were discovered because the obvious membership test kept
failing. The first is not a persistence defect at all — it is live in a
fresh process with no snapshot involved — so it is filed below as **D6**
rather than left as a footnote to D3:

- `TreeLookup` on the *live* `nat_value_index` returns `EmptyList` for every
  value, so `NatFromRep` builds and re-registers rather than finding. The
  pre-built small Nats are in the index but not findable through it.
- Consequently `NatFromRep(2)` is not `M.two`, and `Succ(Succ(Zero))` is not
  `M.two` either. The live machine carries two objects for the number two:
  the named singleton and the one interning returns. `NatEq` hides it
  because it compares values. This is a live canonicality split, not a
  restore defect, and it is why the canonical resolution prefers the named
  symbol and then rebuilds the index to agree with it.

**One comparison contract left open, filed as D7 and routed to E-track.**
`Compare(live ExplanationPlan, restored ExplanationPlan)` is false at the
root while every child position compares equal. If every child agrees and
the root does not, the root is being compared on something beyond its
children — an identity check on the root atom itself, or a cached value
that did not survive restore. The plan test asserts what the boot owes —
the plan survives, keeps its Preserves obligation, and renders with its
law — and leaves the `Compare` contract to its own defect.

**Both shards, measured against the pre-D3 tree.** The same two shards were
run on a worktree of `92e61f2` so the failure sets could be compared rather
than remembered.

```text
                     baseline 92e61f2        with the D3 fix
shard 0              143 passed  3 failed    147 passed  3 failed
shard 1              141 passed  5 failed    145 passed  5 failed
failure set          identical in both columns
suite-wide open      5                       4
```

The open count is **suite-wide, not per shard**, and a shard table that
shows `open: 0` is wrong: the four remaining opens are distributed across
the two shards and each shard's own tally shows its share of them. What
D3 closes is exactly one sentinel:

```text
suite-wide OPEN   before D3: 5   after D3: 4
closed by D3:     snapshot_value_atom_identity_test
                  (VALUE_ATOM_IDENTITY_OPEN -> truth_value)
still open:       test_milestone_m1_cycles_without_refusal
                  test_milestone_m2_handle_lifecycle
                  test_milestone_m3_meta_handle_reorders
                  test_milestone_m4_policy_loosen_then_tighten
```

Report shard results as `passed / failed / open` per shard plus a suite
total, never as passed/failed alone and never with a fabricated `0` in the
open column.

Harvested from the runner's own output at `aed9c0e`, not summarised:

```text
SHARD 0 elapsed 2909.5627086162567
passed: 147   failed: 3   open: 2 (test_milestone_m1_cycles_without_refusal, test_milestone_m3_meta_handle_reorders)
learned_memory_checkpoint_test
tree_insert_deep_pair_lookup_avoids_recursion_test
compare_search_modes_fill_warms_resident_pool_before_root_wave_test
open: test_milestone_m3_meta_handle_reorders, test_milestone_m1_cycles_without_refusal

SHARD 1 elapsed 3446.673872947693
passed: 145   failed: 5   open: 2 (test_milestone_m2_handle_lifecycle, test_milestone_m4_policy_loosen_then_tighten)
heuristic_canonical_knowledge_agreement_test
dependency_graph_checkpoint_test
curator_report_test
cold_e2_reaches_snapshot_save_test
compare_search_modes_finds_reusable_worker_snapshot_dir_test
open: test_milestone_m4_policy_loosen_then_tighten, test_milestone_m2_handle_lifecycle
```

which totals 292 passed, 8 failed, 4 open across 304 tests. The baseline
column's per-shard open split was not recorded, so only the suite-wide 5
is claimed for it.

The eight failures are the same eight, test for test, before and after:

```text
learned_memory_checkpoint_test                              (both trees)
tree_insert_deep_pair_lookup_avoids_recursion_test          (both trees)
compare_search_modes_fill_warms_resident_pool_before_root_wave_test
compare_search_modes_finds_reusable_worker_snapshot_dir_test
heuristic_canonical_knowledge_agreement_test
dependency_graph_checkpoint_test
curator_report_test
cold_e2_reaches_snapshot_save_test
```

So D3 adds eight passing tests, four per shard, removes its own sentinel from
the open count, and moves nothing else. `learned_memory_checkpoint_test` —
the one the gate asked to be recorded either way — fails in the shard on
*both* trees and passes standalone on both, which is the "unchanged" finding:
D3 and that failure are independent, and it is a suite-context failure of its
own.

**A pre-existing fragility the suite run exposed.** The baseline shard 0 did
not finish: it died with `AttributeError: 'Hypergraph' object has no
attribute 'id'` inside the capture walk, from the *old* pinned D3 probe,
which captured the live suite graph. Any test that saves the live graph can
hit it, because the suite builds hypergraph objects into that graph and a
hypergraph carries no `.id`. The new probes capture a graph of their own
instead, which is why both shards complete with the fix. The fragility is not
fixed here and is not D3's.

**What that does to the baseline.** The old probe has captured the live
graph since `8c7039d` ("Pin D3: a restored value atom is not the interned
atom", nine commits below the integration tip), so *no shard-0 run taken
since then has ever completed cleanly*: every shard-0 number from that
window is either a partial result out of a crashed run or a run with the
probe neutered. The honest pre-D3 baseline for shard 0 is therefore "three
failures plus a crash", not "three failures and a completed run", and the
D3 commit is what makes shard 0 completable again. The comparison table
above survives that correction because both of its columns were produced
the same way, with the same neutered probe; what changes is how clean the
old numbers were, not the failure set.

**The eight tests, in the `[SHARED]` block**, in the order the boot
establishes the contract:

```text
raw_snapshot_nat_fidelity_test            payload and sharing survive raw
                                           load; no external identity claim
boot_snapshot_nat_canonicality_test       nested Nat is canonical
boot_snapshot_nat_root_canonicality_test  a captured root that IS a Nat
boot_snapshot_nat_index_canonicality_test index values canonical, no
                                           duplicate indexed
non_nat_value_carrier_not_interned_test   Char "2" and GMPRep 2 are not
                                           canonicalized to Nat 2
large_nat_canonicality_test               past the prebuilt range, no second
                                           successor chain
explanation_plan_snapshot_round_trip_test obligation-bearing plan survives
snapshot_value_atom_identity_test         whole restored payload, production
                                           boot path; OPEN -> truth_value
```

The last one replaced a probe that called `capture` and `load_snapshot` and
stopped there. Activate is the step that rebuilds the roots and wires the
index, so a fix placed after activation was invisible to it — which is why
the prototype could run and the test could still hold its sentinel.

Guard count moved 298 -> 305 with the new tests, in the same commit. The
cursor index (218) and shard (0) are unchanged, because the `[SHARED]` block
sits after the pinned test.

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

**D6 — the live machine already carries two objects for the number two.**
Filed out of the D3 work and deliberately *not* fixed there: this is a
construction-time interning gap in the live runtime, and it reproduces in a
fresh process with no snapshot anywhere in it.

```text
IdentityCompare(NatFromRep(2), M.two)       false_value
IdentityCompare(Succ(Succ(Zero)), M.two)    false_value
NatEq(NatFromRep(2), M.two)                 truth_value
```

Two facts, one consequence:

- `TreeLookup` on the *live* `nat_value_index` returns `EmptyList` for
  every value. The index is populated — the prebuilt small Nats are in it —
  but it is not queryable, so `NatFromRep._from_value` never hits and
  `NatFromRep` builds and re-registers instead of finding.
- So a Nat reached through `NatFromRep`, or built by applying `Succ` to
  `Zero`, is a different object from the named singleton for the same
  number. Nothing fails today because `NatEq` compares values and
  structural comparison compares shape; both hide the split.

The contract that is violated is the identity one, and it is violated at
construction, not at restore: **every site that calls `IdentityCompare` on a
Nat it did not take from the named symbol is silently wrong.** Until D6 is
fixed, compare Nats with `NatEq`, or take them from the named symbol.

D3 canonicalizes *toward* the named symbol and rebuilds `nat_value_index`
to agree with it, so a restored Nat is now the same object as `M.two`.
The fixed state is therefore strictly more canonical than the live machine
it restores into, which is the right direction to leave it. Repairing the
live index is D6's work, in `math/peano.py`, and it does not go in the D3
commit.

**D7 — `Compare` disagrees at a constructed root while every child
position agrees.** Routed to E-track, filed from the D3 plan test: the
disagreement is in how `Compare` treats the constructor of a constructed
term, not in the payload, so the fault is in a comparison primitive that
E-track owns. Not blocking, and not investigated further here.

**D8 — the reset recovery: the gate was right and was not run; the repair
was the wrong tool.** Filed from two consecutive sandbox resets, each of
which replaced `.git` with a fresh clone and destroyed local commits while
leaving the working tree intact. **Corrected after the first write-up got
the mechanism backwards**, which is recorded here because the wrong
version is what sends the next worker to the wrong place.

The first write-up said the descent gate passed in the reset state. It
does not. `git merge-base --is-ancestor A B` asks "is A an ancestor of
B", the script's gate is `--is-ancestor TIP HEAD`, and in the reset state
(`HEAD` `41e8078`, tip `0212ca7`) that is **false** — the script prints
`descent: BROKEN` and 189 phantom paths, loudly. What misled the write-up
is that the opposite statement is comfortably true: `HEAD` *is* an
ancestor of the tip, which is the same thing said in the direction that
sounds like success. Anyone reading "HEAD descends from the tip" has to
know which way `merge-base` points.

So the two real defects are elsewhere:

1. **The gate was never run.** The standing rule — verify `HEAD` before
   the first commit of a session — is manual. `tools/recover.sh` would
   have caught both losses; it was not invoked at the start of either
   turn, and the session worked on an unverified base until the push was
   rejected. The fix is procedural, not code: run it first, every turn.
2. **The repair for the reset case was the wrong tool.** "Behind the tip"
   and "divergent" both printed `descent: BROKEN` and took the same path:
   `git reset --hard` to the tip, then `git apply` the saved diff. For a
   divergent branch that is right. For the reset — the case that actually
   happens — it deletes the surviving files and trusts a patch to put
   them back, when `reset --mixed` moves `HEAD` and the index and leaves
   the tree alone.

Fixed in `[SHARED]` commit 9904d57 (below): three named states instead of
a direction that reads two ways — `clean` (`HEAD` == tip), `behind`
(`HEAD` is an ancestor of the tip: the reset), `divergent` (neither
ancestor of the other). `behind` repairs with `reset --mixed` and prints
how many paths survived, which is the number that says whether the tree
came through: four is the work, tens is a tree that is not the tip's
content. `divergent` keeps the patch-carry repair and its 20k-line
refusal. The header comment states the direction of `merge-base`
explicitly, because that ambiguity is what produced the wrong write-up.


The warning the script prints for the `behind` state, and the recovery it
now performs:

```text
BEHIND THE TIP - reset signature
local checkout is a stale ancestor of the integration tip
files may contain recovered work from a newer tree
do not commit before moving HEAD to the tip
```

```text
HEAD moved to the tip; the working tree was not touched.
surviving work, measured against the tip: N paths
```

Read that number. Four paths is the surviving work; 48 files and 359k
lines is the signature of a wrong base, which is what `.gitignore` and the
20k-line refusal are for. All three states were exercised before the fix
landed — clean, behind (`reset --mixed`, tree intact, pins re-derived
PASS) and divergent (patch carried, edit survives, and the 190-file case
still refuses).

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

**`sh tools/recover.sh --check` is the first command of every agent turn.**
No exceptions. It names the base state and exits non-zero unless `HEAD` is
the integration tip, and it is the only thing standing between a reset and
a turn of work committed against a base that no longer exists. The rule
was already standing ("verify `HEAD` before the first commit of a
session"); it is now a single command, and a worker who skips it is
repeating the failure that cost six commits in three turns.

**Sandbox resets — the wrong-base failure, six times.** A reset keeps the
working tree and drops git objects, so a session can wake up with a full tree
and a `HEAD` that sits *below* the integration tip. The next commit then goes
in against the old base and shows up as 190 files and 359k lines; only the
rejected push catches it. Two fixes are in, both `[SHARED]`:
`tools/recover.sh` makes the check and the recovery one command (fetch,
`merge-base --is-ancestor` against the tip, save the diff and reset if it
fails, rebuild the venv, re-run the pin check), and `.gitignore` takes the
bytecode, search-compare scratch and cold-debug logs so a bad base diffs small
instead of enormous. The rule it encodes is the standing one and is not new:
**HEAD is the integration tip before the first commit of a session** — not
merely an ancestor of it, which is exactly what a reset leaves behind and
exactly the state that reads as "descends from" if you say it loosely (D8).
Verify it before writing anything, not after the push is rejected.
It happened again this turn — the working tree was intact at `7acaf4c` while
`HEAD` sat at `41e8078` — and recovery took four commands instead of the
morning it took the first time.

**The variant, corrected.** It happened again the turn after that, and
again at the start of the turn after *that* — three turns running, six
commits lost. The first account of it here said the descent gate passed
the reset through. **That was wrong, and it is struck out:** the gate is
`--is-ancestor TIP HEAD`, which is false in the reset state, so
`recover.sh` reports `descent: BROKEN` and 189 phantom paths. It was never
silent — it was never *run*. What is true is that the reset state is
`behind` the tip, which is the one state the old script repaired with
`reset --hard` and a patch, deleting the surviving files to restore them.
Both halves are **D8** below, with the fix.

```text
sh tools/recover.sh --check        # names the state; exits 1 unless clean
sh tools/recover.sh                # behind -> reset --mixed, tree untouched

# by hand, which is what the script now does:
git fetch origin <integration branch>
git merge-base --is-ancestor TIP HEAD    # false: HEAD is not past the tip
git merge-base --is-ancestor HEAD TIP    # true:  HEAD is behind the tip
git reset --mixed FETCH_HEAD             # move HEAD and the index, keep the tree
git diff --stat                          # small => the work is still in the tree
```

After moving to the tip the diff *is* the surviving work — four files this
time (`persistence.py`, `testsuite.py`, `tools/repro_d3_interning.py`,
`protocol/DISTRIBUTION.md`) — where against the wrong base it is 48 files
and 359k lines, which is the number `recover.sh` already refuses on. So the
post-reset diff size is the signal that the tree survived, and the currency
gate belongs ahead of the descent gate in `recover.sh`. Not changed here:
recovery tooling is `[SHARED]` and is not tested in this commit. What is
recovered is recoverable because the tree was intact — the three lost
commits were re-made from it, and their content is byte-identical to what
was measured, verified by re-running the pins (305 / 218 / 0 PASS), the D3
repro (mismatched 5 disabled, 0 active), both checkpoints (4.0 s / 3.4 s,
index canonical, Set B identical across two boots) and the nine targeted
tests (9 passed, 0 failed, 0 open). It recurred a second time at the start
of the next turn, and the currency check caught it in the first command;
it is filed as **D8** below and the fix is queued behind the push.

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
3. D3 fix: typed canonical Nat references at   DONE (bf5a2c7); measured
   capture, canonicalized at boot              5 -> 0 mismatched Nats
4. full two-shard suite on the integration tip DONE at aed9c0e against a
                                               worktree of 92e61f2
5. cut experiment-5-frozen; rerun manifest     DONE: tag -> aed9c0e,
                                               manifest re-run on it.
                                               Blank controls not re-run.
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
