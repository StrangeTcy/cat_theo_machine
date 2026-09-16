#!/usr/bin/env python3
"""run.py — selftest for tools/cur_pipeline.py (bundle -> evidence -> verdict, one command).

Asserts the one-command entrypoint maps each fixture family to the expected grader exit and
transcript content, and that the extractor-reject path returns 2 without grading. Unique scratch
dirs keep concurrent invocations isolated. Exit 0 if all pass; non-zero otherwise.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PIPELINE = os.path.join(REPO, "tools", "cur_pipeline.py")
FIXDIR = os.path.join(REPO, "tools", "tests", "cur_extractor", "fixtures")

# fixture -> expected pipeline exit / final.
EXPECT = {
    "e3-pass": 0,
    "e4-pass": 0,
    "e7-pass": 0,
    "e3-role-only-negative-control": 3,
    "e7-no-samples": 3,
    "e4-degree4-move": 1,
    "e7-preservation-fails": 1,
    "e3-not-in-kernel": 2,
    "malformed-duplicate-id": 2,
    "unsupported-contract": 2,
}


def run_pipeline(bundle, scratch):
    mpath = os.path.join(scratch, "m.json")
    tpath = os.path.join(scratch, "t.txt")
    p = subprocess.run([sys.executable, PIPELINE, bundle, "--out", mpath, "--transcript", tpath],
                       capture_output=True, text=True)
    transcript = ""
    if os.path.exists(tpath):
        with open(tpath, "r", encoding="utf-8") as f:
            transcript = f.read()
    return p.returncode, transcript, mpath


def main():
    scratch = tempfile.mkdtemp(prefix="cur_pipeline_selftest_")
    failures = []
    total = 0
    ok = 0

    print("=" * 78)
    print("PIPELINE SELFTEST — tools/tests/cur_pipeline/run.py")
    print("=" * 78)

    for key, expected_exit in EXPECT.items():
        total += 1
        bpath = os.path.join(FIXDIR, key + ".json")
        rc, transcript, _ = run_pipeline(bpath, scratch)
        passed = (rc == expected_exit)
        # Reject fixtures (extractor exit 2, no manifest) are NOT graded: transcript must NOT
        # contain a grader line and MUST note "not grading". Ambiguous/contradictory exits (exit 2
        # after grading) DO contain a grader line. Non-reject fixtures must contain a grader line.
        has_grader = "[grader]" in transcript
        has_pipeline_exit = "PIPELINE_EXIT=" in transcript
        is_reject = key in ("malformed-duplicate-id", "unsupported-contract")
        if is_reject:
            passed = passed and (not has_grader) and ("not grading" in transcript)
        else:
            passed = passed and has_grader and has_pipeline_exit
        if passed:
            ok += 1
            status = "OK"
        else:
            failures.append((key, "exit=%s expected=%s grader=%s pexit=%s" % (rc, expected_exit, has_grader, has_pipeline_exit)))
            status = "FAIL"
        print("  %-32s exit=%s expected=%s (%s)" % (key, rc, expected_exit, status))

    # ---- reject path: extractor exit 2 -> pipeline exit 2 and transcript notes "not grading".
    total += 1
    bpath = os.path.join(FIXDIR, "malformed-duplicate-id.json")
    rc, transcript, _ = run_pipeline(bpath, scratch)
    reject_ok = (rc == 2) and ("not grading" in transcript)
    if reject_ok:
        ok += 1
    else:
        failures.append(("reject-path", "exit=%s not_grading=%s" % (rc, "not grading" in transcript)))
    print("  %-32s exit=%s expect 2, not-grading note present (%s)" % ("reject-path", rc, "OK" if reject_ok else "FAIL"))

    # ---- foreign working directory.
    total += 1
    extcwd = os.path.join(scratch, "outside")
    os.makedirs(extcwd, exist_ok=True)
    bpath = os.path.join(FIXDIR, "e3-pass.json")
    mpath = os.path.join(extcwd, "m.json")
    tpath = os.path.join(extcwd, "t.txt")
    p = subprocess.run([sys.executable, PIPELINE, bpath, "--out", mpath, "--transcript", tpath],
                       cwd=extcwd, capture_output=True, text=True)
    foreign_ok = (p.returncode == 0) and os.path.exists(mpath)
    if foreign_ok:
        ok += 1
    else:
        failures.append(("foreign-cwd", "exit=%s manifest=%s" % (p.returncode, os.path.exists(mpath))))
    print("  %-32s exit=%s (foreign cwd) (%s)" % ("foreign-cwd", p.returncode, "OK" if foreign_ok else "FAIL"))

    import shutil
    shutil.rmtree(scratch, ignore_errors=True)

    print("=" * 78)
    print("SUMMARY: %d/%d pass, %d fail" % (ok, total, len(failures)))
    if failures:
        for label, detail in failures:
            print("    - %s: %s" % (label, detail))
    print("=" * 78)
    return 0 if len(failures) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
