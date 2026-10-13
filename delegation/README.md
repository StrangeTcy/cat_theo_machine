# Delegation Pack — Swarm Workers

These briefs dispatch the open workers from `SWARM_EVOLUTION_DAG.md`. Each brief is
self-contained: paste it into a **fresh Arena session** on this repository. The session
is pinned to its own branch, works there, and reports back. The coordinator imports the
result — see *Reporting back* below.

Index (open workers only; everything marked `[x]` in the DAG is already done and verified):

| Brief | Worker | Dimension | Phase | Prereqs (all met?) | Suite slot |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `W06-flt-n4-descent.md` | W6 remainder: Pythagorean parametrization descent | 1 | 1 | W3 ✅ | `test26` |
| `W07-flt-n3-eisenstein.md` | W7: FLT $n=3$ Eisenstein UFD factorization — **partial `[~]`**, see DAG §4 (obstruction + norm landed; UFD/descent open) | 1 | 1 | W3 ✅ | `test20` ✅ |
| `W08-imo-geometry.md` | W8: IMO geometry & auxiliary construction — **done**, see DAG §4 | 2 | 1 | W4 ✅ | `test21` ✅ |
| `W09-imo-combinatorics-funceq.md` | W9: IMO combinatorics, functional equations, NT — **done**, see DAG §4 (two deliverables) | 2 | 1 | W4 ✅ | `test22` ✅, `test29` ✅ |
| `W10-engel-strategies.md` | W10: Engel monovariants, extremal, box, colouring — **done**, see DAG §4 | 3 | 1 | W3 ✅ W4 ✅ | `test23` ✅ |
| `W15-socratic-tutor.md` | W15: conversational Socratic tutor | 5 | 2 | W5 ✅ W12 ✅ | `test24` |
| `W02-rpc-mtls-mesh.md` | W2: RPC / mTLS mesh — **done**, see DAG §4 | Infra | 0 (late) | none | `test25` |
| `W16-distributed-prover-swarm.md` | W16: distributed prover swarm — **in progress `[~]`**, see DAG §4 (engine + CLI + mesh runner landed; suite missing) | Swarm | 3 | W2 ✅ W13 ✅ | `test27` ⬜ |
| `W17-byzantine-ledger-consensus.md` | W17: Byzantine ledger consensus | Swarm | 3 | W2 ✅ W12 ✅ W1 ✅ | `test28` |

Dispatch order that respects the gates: the five Phase-1 briefs (W6–W10) and W15 are
independent and can all run in parallel. W2 is the only Phase-3 prerequisite and its
brief is now executed and green (`validation/test25_rpc_mtls_mesh.py`, 48/48, ~100 s),
so W16 and
W17 are unblocked — their `Prereqs` columns still name W2 ⬜ because they were written
before it landed; read that as W2 ✅.

Suite slots are **append-only** and pre-allocated above. Do not reuse a number: two
lineages already collided on slots 15 and 16, which is recorded in DAG §6, and two W9
sessions then collided on slot 22 (DAG §6.2) — the second suite now lives at `test29`,
so **the next free slot is `test30`**.

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
   pre-allocated slot, 100% green, plus the existing 19 suites still green.
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
- Run a suite: `PYTHONPATH=/home/user .venv/bin/python -u validation/testNN_name.py`.
  Suites are standalone scripts, not pytest. Run them with `-u` or you lose output on a
  timeout.
- If you spawn multiprocessing in a harness, guard it with
  `if __name__ == "__main__":`. The codec's registry restore uses `spawn`, so an
  unguarded harness re-executes at import and fails as
  `registry shard N/M failed: no output produced`. That error is always the missing guard.

## Pitfalls already paid for

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
