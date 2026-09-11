HOST-TOOLS IMPORT REHEARSAL ON preflight-fa4b346 BASE — 2026-09-11 UTC
======================================================================
Agent: CUR-GRADER-ENG / import support. Disposable rehearsal: no merge into
INT, no tag, no measurement authorized, no theorem claimed.

THREE IDENTITIES (keep distinct)
--------------------------------
implementation source: e904cfaf3a4f6ae159889eebb33b144b1b22e6be
  tree 467ced801792adc1132f0131043fa2c9917112ed
import harness:        2b8b10d7b36da781c55436332dc2d6b08d138bae (hardened; on this lane)
destination base:      fa4b3465fdfdb137614fe5851e92a33d6f667044
  tree bfc69edc9efa9901496bbe7f480ac203036ffad3
  tag refs/tags/preflight-fa4b346 (tag object 93338193e575241a441e78db0e2b24ddd478b192)
  subject: "Preflight item 4: both shards run, 295 pass / 6 fail / 4 open"
  Tools absent on the base (allowlist paths resolve to nothing there).

COMMANDS (exact)
----------------
python3 tools/tests/cur_import/run.py \
  --repo /home/user/cat_theo_machine \
  --tool-source e904cfaf3a4f6ae159889eebb33b144b1b22e6be \
  --runtime-base fa4b346 \
  --out verification/2026-09-11-cur-import-int
  -> HARNESS EXIT = 0, ok: True, stage: done

python3 tools/tests/cur_import/run.py --verify verification/2026-09-11-cur-import-int
  -> ACCEPT: attempt complete and intact

Selftests (same harness, same identities, --selftest into this dir):
  -> 17/17 harness selftests pass (see harness-selftests.txt)

Manual reconstruction (outside the harness): fresh worktree at fa4b346,
`git apply --check import.patch` clean, applied, then the five suites run
directly in that tree (see below). Worktree removed afterwards.

RESULT
------
paths imported: 73 (all mode 100644; 0 collisions; 0 allow-replace used)
identity preservation: ok — extractor_digest matches the imported file;
  contract_ref_commit / rubric_ref_commit keep source-pinned values
  (c10011bfabc73b55c7a3de80c4ff14a78234f17b /
  70271007ba5292e782c223bca1474dce8ced8168), not relabeled to the base.
  (Source is e904cfa, so the recorded extractor digest is the pre-F-5
  value ef7f3183...; the F-5 follow-up 31306e1 is a separate commit.)

harness source (e904cfa) and destination (fa4b346 + import) suite counts:
  tools/tests/cur_grader/run.py              56/56 PASS both sides
  tools/tests/cur_extractor/run.py           30/30 PASS both sides
  tools/tests/cur_schema/run.py              13/13 PASS both sides
  tools/tests/cur_pipeline/run.py            12/12 PASS both sides
  tools/tests/cur_pipeline/hardening.py      12/12 PASS both sides

manually reconstructed destination (patch applied to fresh fa4b346):
  tools/tests/cur_grader/run.py              exit=0 56/56 fail=0
  tools/tests/cur_extractor/run.py           exit=0 30/30 fail=0
  tools/tests/cur_schema/run.py              exit=0 13/13 pass, 0 fail
  tools/tests/cur_pipeline/run.py            exit=0 12/12 pass, 0 fail
  tools/tests/cur_pipeline/hardening.py      exit=0 12/12 pass, 0 fail
  byte/mode check of the 73 files there: 73 checked, 0 mismatched.

no existing failures; no source-only pass; portability demonstrated.

FILES
-----
completion.json          written last; consumer gate (see --verify)
input-manifest.json      identities, allowlist, suites, rows, identity check
import-paths.txt         73 paths with mode + sha256
source-results.txt       raw source-side evidence
destination-results.txt  raw destination-side evidence
import.patch             279582 bytes, applies cleanly to fresh fa4b346
harness-selftests.txt    17/17 (run after the rehearsal, same harness commit)
README.txt               this file

NOTE FOR INT
------------
Run the harness itself against the live tip (procedure in the ratified
f1aa963 README); this directory is the dated artifact for the fa4b346
base. Keep evidence commits as artifacts; do not merge them wholesale.
Classification: host-tools import, non-semantic for machine execution.
Machine tag: not required by this import alone.
Merge/tag performed: none. Machine code changed: no.
Ready for INT import: yes.
