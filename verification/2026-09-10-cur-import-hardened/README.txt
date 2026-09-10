HOST-TOOLS IMPORT REHEARSAL (HARDENED HARNESS) — 2026-09-10 UTC
===============================================================
Agent: CUR-GRADER-ENG / import support. Disposable rehearsal: no merge into
INT, no tag, no measurement authorized, no theorem claimed.

THREE IDENTITIES (keep distinct)
--------------------------------
implementation source: e904cfaf3a4f6ae159889eebb33b144b1b22e6be
  tree 467ced801792adc1132f0131043fa2c9917112ed
import harness:        2b8b10d7b36da781c55436332dc2d6b08d138bae
  tree 55cab5d0153ddd038a6752871ad407f7125ed70e
  (exact mode handling + atomic attempt publish; selftests 10 -> 17)
destination base:      13cd338c2b0063c3cc2cdcb61231670361a31355
  tree d481494ccc15ffbac38579f0cd88462dbef86e9b
  (origin/arena/01a06542-cat-theo-machine as pinned by a fresh fetch on
  2026-09-10 ~01:57 UTC; descendant of bfd4bd2. INT must re-pin live
  before importing; do not treat this base as current without a re-check.)

This evidence commit remains a dated supporting artifact. INT should run
the harness itself against its live base, not merge an evidence commit.

COMMANDS (exact)
----------------
python3 tools/tests/cur_import/run.py \
  --repo /home/user/cat_theo_machine \
  --tool-source e904cfaf3a4f6ae159889eebb33b144b1b22e6be \
  --runtime-base 13cd338c2b0063c3cc2cdcb61231670361a31355 \
  --out verification/2026-09-10-cur-import-hardened
  -> HARNESS EXIT = 0, ok: True, stage: done

python3 tools/tests/cur_import/run.py \
  --repo /home/user/cat_theo_machine \
  --tool-source e904cfaf3a4f6ae159889eebb33b144b1b22e6be \
  --runtime-base 13cd338c2b0063c3cc2cdcb61231670361a31355 \
  --out verification/2026-09-10-cur-import-hardened --selftest
  -> 17/17 harness selftests pass (see harness-selftests.txt)

python3 tools/tests/cur_import/run.py \
  --verify verification/2026-09-10-cur-import-hardened
  -> ACCEPT: attempt complete and intact

RESULT
------
paths imported: 73 (all mode 100644; 0 collisions; 0 allow-replace used)
non-allowlisted probe files unchanged: main.py core.py persistence.py
  training.py research.py (hashes in input-manifest.json)
identity preservation: ok — extractor_digest matches the imported file;
  contract_ref_commit / rubric_ref_commit keep source-pinned values
  (c10011bfabc73b55c7a3de80c4ff14a78234f17b /
  70271007ba5292e782c223bca1474dce8ced8168), not relabeled to the base.

source (e904cfa) and destination (13cd338 + import) suite counts:
  tools/tests/cur_grader/run.py              56/56 PASS both sides
  tools/tests/cur_extractor/run.py           30/30 PASS both sides
  tools/tests/cur_schema/run.py              13/13 PASS both sides
  tools/tests/cur_pipeline/run.py            12/12 PASS both sides
  tools/tests/cur_pipeline/hardening.py      12/12 PASS both sides
no existing failures; no source-only pass; portability demonstrated.

HARNESS SELFTESTS (17/17)
-------------------------
10 prior cases (baseline, missing path, collision refusal + explicit
resolution, missing grader + no foreign fallback, exit-7 rejection,
unrelated cwd, concurrent isolation, non-allowlisted unchanged) plus:
  symlink entry recreated as symlink (direct + end-to-end)   OK
  unsupported mode rejected explicitly (fabricated + gitlink) OK
  nonempty output directory -> refusal                        OK
  interruption before publish -> no completed output          OK
  two invocations, same output -> exactly one succeeds        OK
  completion manifest missing -> consumer refuses             OK
  tampered artifact -> consumer refuses                       OK

PATCH ROUND-TRIP (outside the harness)
--------------------------------------
Fresh worktree at 13cd338: `git apply --check import.patch` clean;
applied; all 73 paths match the e904cfa blobs byte-for-byte and the
filesystem modes match the source git modes (73 checked, 0 mismatched).
import.patch size: 279582 bytes.

FILES
-----
completion.json        written last; consumer gate (see --verify)
input-manifest.json    identities, allowlist, suites, rows, identity check
import-paths.txt       73 paths with mode + sha256
source-results.txt     416236 bytes raw source-side evidence
destination-results.txt 16152 bytes raw destination-side evidence
import.patch           279582 bytes, applies cleanly to fresh 13cd338
harness-selftests.txt  17/17 (run after the rehearsal, same harness commit)
README.txt             this file

CARRIED-FORWARD NOTE F-5
------------------------
tools/cur_extract_evidence.py (source-pinned bytes) contains a banned
comment token (spelled a-c-t-u-a-l-l-y) at lines 73 and 850; it therefore
also appears inside the captured raw output in source-results.txt. Left untouched: editing
those bytes would change extractor_digest and require an owner-reviewed
identity re-pin. Not a harness defect.

INT IMPORT INSTRUCTION
----------------------
1. Fetch exact e904cfa and harness 2b8b10d.
2. Pin the live arena/01a06542 tip (re-pin; do not reuse 13cd338 blindly).
3. Run the harness itself; do not apply a stale generated patch blindly.
4. Import only the 73 allowlisted tool/spec files.
5. Run the five host-tool suites on the resulting candidate.
6. Record exact source, harness, destination, and resulting tree identities.
7. Keep evidence commits as dated artifacts; do not import generated trees.

Classification: host-tools import, non-semantic for machine execution.
Machine tag: not required by this import alone.
Operator blank-control rerun: not required.
Merge/tag performed: none.
Ready for INT review: yes.
