# Delegation Pack — Swarm Workers

These briefs dispatch the open workers from `SWARM_EVOLUTION_DAG.md` §8. Each brief is
self-contained: paste it into a **fresh Arena session** on this repository. The session
is pinned to its own branch, works there, and reports back. The coordinator imports the
result — see *Reporting back* below.

W1–W20 are done or closed as partial (DAG §4, §6.9). Their briefs stay in this directory
as history; **do not re-execute them.** W21–W27 have landed; W29 is closed as a precise negative; W33 has landed. Remaining dispatchable work is W28 and W30–W32 (subject to their gates), plus USER/COORD.

Index (open workers only):

| Brief | Worker | Dimension | Phase | Prereqs | Suite slot |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `W21-witness-introduction.md` | Existential witness introduction — **done**, see DAG §4 W21 | Substrate / 1 | 4 | none | `test33` ✅ |
| `W22-algebraic-rewriting.md` | Grid identities → **done via Checker-B-verified grid proofs**; symbolic normalisation remains open (DAG §4) | Substrate / 1 | 4 | none; do not re-dispatch | `test34` ✅ |
| `W23-factorisation-natless.md` | **Done:** subtraction, gcd cofactors & schema-derived `NatLess` (DAG §4) | Substrate / 1 | 4 | none; do not re-dispatch | `test35` ✅ |
| `W24-residue-divisibility-wiring.md` | Residue / divisibility schema wiring (was W9(c)) — **done**, see DAG §4 W24 | 2 | 4b | W9 ✅ | `test36` ✅ |
| `W25-curriculum-loader.md` | Curriculum card loader — **done**: 24 cards parse, 2 compile (held-out solved, decoy refused), 22 refused with reasons, 48 Ground 1 gaps reported; DAG §4 W25 | 2/3/4 | 4b | none | `test37` ✅ |
| `W26-geometry-remainder.md` | Cyclic-quad / chord-angle + receipts — **done**: three constant-free schemas + antipode construction, Checker-B verified, ledger promoted, four ablations; DAG §4 W26 | 2 | 4b | W8 ✅ W4 ✅ | `test38` ✅ |
| `W27-engel-remainder.md` | Engel remainder — **done**: two unnamed instances closed, observable mined (ablation separates nothing), strategy proposals fire in `PlannerRun` with supplied obligations discharged; root closure inside search pinned open; DAG §4 W27 | 3 | 4b | W10 ✅; do not re-dispatch | `test39` ✅ |
| `W28-flt-n3-ufd-descent.md` | Eisenstein UFD + cubic descent | 1 | 5 | W21–W23 ✅, W7 `[~]` — **ready** | `test40` |
| `W29-flt-n4-everystate.md` | **Closed, precise negative:** EveryStateMoves still open (DAG §4) | 1 | 5 | do not re-dispatch unchanged | `test41` 61/61 |
| `W30-domain-promotion-loop.md` | Domain packs through Checker B + ledger | 4 | 6 | W12 ✅ + a Phase 4b receipt — **gated** | `test42` |
| `W31-dialogue-beyond-arithmetic.md` | Tutor/story beyond arithmetic | 5 | 6 | W15 ✅ W14 ✅ | `test43` |
| `W32-swarm-boot-cost.md` | Swarm unit-boot cost | Infra | 7 | W16 ✅ — **start now** | `test44` |
| `W33-mesh-reconnect-accounting.md` | **Done:** severed links are suspect for `reconnect_grace` before they are losses; transient reconnects charge no attempt (DAG §4) | Infra | 7 | done; do not re-dispatch | `test45` ✅ |

Supplemental follow-up: [`constrained-nat-witnesses.md`](constrained-nat-witnesses.md)
records bounded numeric witness search (`test46`, 185/185) and independent
assignment re-evaluation. A second unbriefed supplemental landed 2026-10-22
(machine-native playground projections + REPL auto lemma suggestion,
`test47` 27/27, DAG §4/§6.11). Latest full gate: **43/43 green** after the
f42b3f12 integration (2026-10-22, DAG §6.11). W29's finite fixture
now yields numeric parameters, but EveryStateMoves and the promotion gate remain
open; this is not parametrisation completeness or an existential proof rule.

USER-1 (laptop ⇄ Colab WAN trial) and USER-2 (real Neo4j dump decode) are not Arena
briefs — see DAG §8. COORD merges this line to `master`.

Dispatch order: two independent sessions can start in parallel (W28,
W32) with disjoint file ownership except append-only `labels.py`. (The two
post-W22 heads were integrated on 2026-10-21, DAG §6.10, so
W21–W27 are all on this tree.) W29 has reported a precise negative; do not
re-dispatch it until its named generic/proof gaps change. W30's
receipt gate is met by W24/W26 — its full scope is richer now that W27 has landed.
W31 can start on existing arithmetic/Engel-pack goals; it is richer after
W30.

Suite slots are **append-only** and pre-allocated above (`test33`–`test45`). Do not
reuse a number. Historical collisions (15/16, 22, 27) are recorded in DAG §6. The
supplementals `test46` and `test47` are taken (above); the next unoccupied allocated slot is
`test40` (W28) and the next never-allocated number is `test48`.

---

## Shared invariants (binding on every brief)

From `SWARM_EVOLUTION_DAG.md` §5, restated so no brief has to repeat them:

1. **Branch**: work only on the branch your session is pinned to. Never touch another
   session's branch. **Do not open a pull request** — commit to your branch and report.
2. **Machine representation purity** — binding in the kernel and in any code that
   constructs or consumes machine terms:
   - Never edit `core.py`.
   - Build and inspect machine values with `Pair`, `EmptyList`, `truth_value`,
     `false_value`, `Atom`, `Char`, and native labels — not Python lists, dicts, or bools.
   - Do not reach into a machine value with `isinstance`, `hasattr`, `type`, `__class__`,
     or `__new__`; use the machine's own predicates (`IsPair`, `IsTree`, `Compare`,
     `IdentityCompare`). A fresh `M.Char("name")` is **not** identical to an interned one,
     so `IdentityCompare` silently fails there — use `Compare`, or read `.symbol` in a
     harness.
   - Counting and arithmetic over machine quantities go through Peano `Zero`, `SuccLabel`,
     `GMPRep`.

   **Host-layer exception (read this before "fixing" anything).** The kernel — `core.py`,
   `machine.py`, `context.py`, `labels.py`, `proof.py`, `trees.py`, `graph.py`,
   `matching.py` — has zero forbidden constructs and must stay that way. Outside it
   (`main.py`, `persistence.py`, `packs.py`, `runtime.py`, `search/`, `testsuite.py`,
   `validation/`, `probes/`), Python natives are permitted where there is no machine
   analogue, and 46 such sites already exist in verified, shipped code. Sanctioned and not
   up for re-litigation: `persistence.py`'s `_ids_by_pyid` / `_name_by_objid` identity index,
   keyed on Python `id()`, because object identity has no machine analogue and an anonymous
   `Atom` has no term-derived key — it buys capture ~620 → ~16,000 objects/s. Python ints for
   measurement and reporting in harnesses are fine too.

   **The exception is conjunctive: both halves must hold.** Your code is host-layer, *and*
   there is no machine analogue for what it does. Being in a harness or a probe is not by
   itself a licence — if the machine can already answer the question (`Compare`, `IsAtom`,
   `IsPair`, `IsTree`), then reaching into a payload with `getattr`, `type`, or `.symbol` is a
   violation wherever it sits, and it will be sent back. Do not spend your session on an
   unscoped purity refactor, and do not cite this rule to reject working host-layer code — but
   do not cite the host layer to excuse bypassing a predicate the machine already provides.
3. **No domain-specific hardcoding**: no problem targets, no named lemmas, no fixed
   heuristics baked into search or mining modules. This is the rule that got the
   hand-authored FLT quartic pack withdrawn (DAG §4, W6). Write generic machinery and let
   the machine discover the instance; if you must author a pack, it may carry *ontology*
   (sorts, constructors, generic schemas) but not the conclusion of the problem.
4. **Verification**: every deliverable ships an automated suite in `validation/` at your
   pre-allocated slot, 100% green, plus the existing suites (`test1`–`test32` as of
   2026-10-15, plus any `test33+` already on the tree) still green.
5. **Snapshot roots**: any state that must survive a cold resume is registered in
   `SnapshotCodec.capture()` and restored in `activate()`. State left in a Python
   attribute evaporates on reload.

## Environment (verified facts, do not rediscover)

- Repo root `/home/user/cat_theo_machine`; the package is imported as
  `cat_theo_machine.*`, so run everything with `PYTHONPATH=/home/user`.
- No `java`, no `docker`, no `7z`, no `zstd`. Outbound network is restricted to
  github.com, api.github.com, registry.npmjs.org, pypi.org, files.pythonhosted.org.
  Anything needing a JVM, a container, or an arbitrary host is out of scope by
  construction — design around it (loopback sockets are fine).
- 2 vCPU, ~3.8 GiB RAM, ~20 GB disk. Large snapshots are RAM-bound at ~1–2 M objects.
- Recreate the venv if `.venv/` is missing (it is not committed):
  `python3 -m venv .venv && .venv/bin/pip install -q gmpy2 pyyaml`.
- **Machine arithmetic is flat-rate now, but the rate is ~40–75 ms.** W18 (landed, DAG
  §6.7) removed the quadratic `NatValueIndex` lookup: interning is `O(key length)` and no
  longer degrades as entries accumulate (measured 0.064 s/call fresh, 0.065 s/call at 900
  interned nats; was 0.22 s → 1.47 s at 300 before the fix). The remaining constant is
  `core.py`'s per-allocation `uuid4()` and is out of scope. Budget sweeps by the constant:
  a hundred arithmetic ops ≈ 5–8 s. Compute a table once and test by membership for
  anything bigger, and do not “fix” it locally with a host-side cache — that is a
  forbidden construct in kernel code and a second source of truth beside the tree.
- Run a suite: `PYTHONPATH=/home/user .venv/bin/python -u validation/testNN_name.py`.
  Suites are standalone scripts, not pytest. Run them with `-u` or you lose output on a
  timeout.
- If you spawn multiprocessing in a harness, guard it with
  `if __name__ == "__main__":`. The codec's registry restore uses `spawn`, so an
  unguarded harness re-executes at import and fails as
  `registry shard N/M failed: no output produced`. That error is always the missing guard.

## Pitfalls already paid for

- **Stale bytecode after a sandbox restore.** Restored files carry untrustworthy mtimes, so
  Python can keep running an old `.pyc` after you edit a module (symptom: a print that never
  fires, `inspect.getsource` disagreeing with the file). `find . -name __pycache__ -type d
  -exec rm -rf {} +` and rerun. The legacy tracked `__pycache__` artifacts were removed
  from the repository on 2026-10-15; keep it that way.
- **Never commit conflict markers.** One branch committed `<<<<<<<`/`>>>>>>>` blocks inside
  `SWARM_EVOLUTION_DAG.md`; the integrator had to reconstruct the intent. Before committing
  a merge: `grep -rn '^<<<<<<<\|^>>>>>>>' --include=*.md --include=*.py .` must be empty.
- **One suite per slot.** If your slot's file already exists on the mainline when you
  rebase, the mainline suite wins unless yours asserts something it does not — say so in
  the DAG rather than shipping a second `testNN` under the same number (this happened with
  `test27`, see DAG §6.8).
- `M.IdentityCompare(x, M.Char("name"))()` compares **identity**, so it never matches a
  freshly constructed `Char`. To test a symbol, read its `.symbol` attribute or compare
  against the interned atom from the registry.
- Long strings go in **one** `Char` atom (`M.Char("whole sentence")`), which round-trips
  exactly and pretty-prints inline. Do not build char chains; that is only the pack
  string-table convention.
- Canonical shapes: a node is a `Char` (named entity) or `M.Thingy()` (anonymous handle);
  a hyperedge is `M.Pair(M.Char(relname), M.Pair(a, M.Pair(b, M.EmptyList)))`. Restored
  `Thingy` nodes come back as plain `Atom` — identity survives, class does not — so
  prefer named `Char` entities for anything you intend to query after a reload.
- Legacy snapshots with no `nodes`/`edges` root fall back to `EmptyList` and report 0/0.
  That is expected, not a failure.
- Booting a snapshot used to rewrite it in place, silently, because the codec's tree-currency
  check was dead code and judged every non-empty root legacy. That is fixed: current-format
  snapshots are no longer rewritten, and genuinely legacy ones announce the rewrite. For a
  guaranteed non-mutating load (inspection, bisecting, tests), set
  `HYGE_SNAPSHOT_UPGRADE_RESAVE=0`. Still worth a `git status snapshots/` before committing.
- The REPL command `run self-diagnostics` executes every suite in `validation/` as a
  subprocess and reports real pass/fail with timings. It is the full gate and takes ~4
  minutes; it used to count files and always claim success, so ignore any older note that
  says its suite count is hardcoded.

## Reporting back

Commit on your branch with a message that states what the machine now does that it could
not before, and what evidence proves it. Then report to the coordinator:

1. Branch name and commit sha.
2. Suite slot used, its final line, and the wall-clock time.
3. `19+N` suite status: your new suite plus all existing ones green, or the exact failure.
4. Files added/modified, and confirmation that `core.py` is untouched.
5. Anything you discovered that contradicts a DAG claim — the DAG is a living document and
   a wrong `[x]` is worse than an honest `[ ]`.
6. Known limitations. Say what is *not* derived rather than implying more than you proved;
   W6's `[~]` is the model for that.
