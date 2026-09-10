CUR HOST-TOOLS IMPORT REHEARSAL — RESULT SUMMARY
================================================
date (UTC):   2026-09-10
role:         CUR-GRADER-ENG / import support
harness:      tools/tests/cur_import/run.py
permitted branch: arena/01a066cf-cat-theo-machine
status:       disposable rehearsal. No merge into INT, no tag, no measurement,
              no theorem claim.

IDENTITIES
  tool source   : e904cfaf3a4f6ae159889eebb33b144b1b22e6be
                  tree 467ced801792adc1132f0131043fa2c9917112ed
  runtime base  : bfd4bd28de5765adbdabd1d152200fa67f11e5a2
                  tree c30a29ae51b77791a1b557244d5f24821c09fffc

RESULT
  imported files : 73
  collisions     : 0
  source suites  : 5/5 PASS
  destination    : 5/5 PASS
  harness selftests: 10/10 pass
  patch          : applies cleanly to a fresh bfd4bd2; 73/73 imported files
                   reproduce the source blobs byte-for-byte

  per-suite counts (identical in both locations)
    tools/tests/cur_grader/run.py          56 assertions, 0 fail
    tools/tests/cur_extractor/run.py       30 assertions, 0 fail
    tools/tests/cur_schema/run.py          13/13 pass, 0 fail
    tools/tests/cur_pipeline/run.py        12/12 pass, 0 fail
    tools/tests/cur_pipeline/hardening.py  12/12 pass, 0 fail

CLASSIFICATION (per the brief's three-way split)
  works on source and destination : all five suites. Portability demonstrated for
                                    each, on this destination.
  works on source, fails on dest  : none.
  fails in both                   : none.

COLLISION DETERMINATION
  Collisions are reported as 0 from the PATH-LEVEL import against bfd4bd2, not
  inferred from absence in a summary. Absence of the tools on the runtime base is
  an import REQUIREMENT; it is not a conflict. No shared-file conflict exists for
  this allowlist.

DEPENDENCY CHECK
  The four imported tools import stdlib only (hashlib, importlib, json, os, sys,
  fractions, subprocess, tempfile). None imports a machine module (core.py,
  labels.py, packs) or anything from the runtime. No additional path was needed
  beyond the brief's starting allowlist.

SOURCE IDENTITY PRESERVATION
  The import does not relabel the tools' recorded identities. The destination
  extractor reports contract_ref_commit c10011bfabc73b55c7a3de80c4ff14a78234f17b
  and rubric_ref_commit 70271007ba5292e782c223bca1474dce8ced8168 — the values
  pinned in the source — and never the runtime commit. extractor_digest equals
  the sha256 of the imported file and of the source blob.

SUPPLEMENTARY REHEARSALS (same harness, same destination logic)
  cur-import-fixed-test/ : source = code commit carrying the corrected
                           concurrency test -> bfd4bd2. PASS, cur_schema 13/13 in
                           both locations, so the revised test travels.
  cur-import-int-tip/    : source = code commit -> 13cd338 (the CURRENT INT tip,
                           not bfd4bd2). PASS, all five suites in both locations.

FINDINGS

  F-1  HARNESS DEFECT FOUND BY ITS OWN NEGATIVE TESTS (summary parsing).
       The first run reported cur_grader and cur_extractor as NO_SUMMARY in BOTH
       locations. That was a parser defect, not a suite failure: those two suites
       print a different summary shape ("SUMMARY" / "assertions run:" / "ok:" /
       "fail:") than the other three ("SUMMARY: n/n pass, k fail"). Both shapes
       are now recognized. A missing summary remains a failure, never a pass.

  F-2  HARNESS DEFECT FOUND BY ITS OWN NEGATIVE TESTS (racy invariant).
       A worktree-integrity check compared the whole worktree list before and
       after. That is not concurrency-safe: two concurrent rehearsals each saw the
       other's worktrees and reported a false "not removed". The invariant is now
       ownership-scoped — an invocation must not leave ITS OWN worktrees behind.
       This was caught by negative case 6 after the check was added.

  F-3  FALSE POSITIVE CORRECTED (repository-state comparison).
       Comparing `git status --porcelain` before and after flagged a change when
       the artifact directory is inside the repository, which is the intended
       arrangement. Tracked-only comparison is the correct semantics; the harness
       now uses `-uno` and additionally asserts its own worktrees are released.

  F-4  CONCURRENCY LABEL CORRECTED IN A SUITE (coverage change only).
       tools/tests/cur_schema/run.py case 11 called two blocking helpers in
       sequence while labeling them "concurrent". Both children are now launched
       before either is awaited, and overlap is observed rather than assumed. No
       expected grade and no grading semantics changed. The other suites' claims
       were checked: cur_grader CHECK 8, cur_extractor CHECKs 16 and 18, and
       cur_pipeline/hardening case 12 already launch before awaiting.

  F-5  CHARTER-HYGIENE HIT, PRE-EXISTING, NOT INTRODUCED HERE, NOT REPAIRED.
       One of the six banned tokens occurs in committed source at
       tools/cur_extract_evidence.py lines 73 and 850 (both in comments, from an
       earlier commit), and therefore appears in the captured raw output and in
       import.patch. It is not authored prose in this change. It is NOT repaired
       here on purpose: editing those bytes changes the extractor file and with it
       extractor_digest, which the identity block pins. Repair is an owner
       decision that re-pins an identity, so it belongs in its own reviewed change,
       not in an import rehearsal.

  F-6  DELIBERATE EXCLUSION.
       The harness itself (tools/tests/cur_import/) is NOT part of the import
       payload. It is the mechanism that performs and verifies the import, not a
       CUR evaluator tool that INT needs on the runtime line.

ARTIFACTS
  input-manifest.json     identities, allowlist, per-file hashes, results, identity check
  import-paths.txt        every imported path with mode and sha256
  source-results.txt      source-location suite output + raw command records
  destination-results.txt destination suite output + raw command records
  harness-selftests.txt   the 10 negative cases and their outcomes
  import.patch            generated from the reconstructed candidate's changes
