#!/usr/bin/env python3
"""hardening.py — regression tests for tools/cur_pipeline.py gate hardening.

Exercises the execution-error / publication / concurrency behaviors that the baseline
selftest (run.py) does not cover:

  * successful fixture -> 0 GRADED
  * valid FAIL fixture  -> 1 GRADED
  * valid CANNOT_DETERMINE fixture -> 3 GRADED
  * extractor prints plausible output then exits 7 -> 2 EXECUTION_ERROR (never graded)
  * stale --out manifest present -> replaced only with a validated fresh manifest
  * extractor times out -> 2 EXECUTION_ERROR
  * extractor killed by signal -> 2 EXECUTION_ERROR
  * grader exits without a verdict -> 2 EXECUTION_ERROR
  * unwritable transcript -> 2 (output-write failure, no partial verdict)
  * malformed input -> 2 REJECTED (never graded)
  * foreign working directory
  * two complete pipeline invocations concurrently

Exit 0 if all pass; 1 otherwise. Uses only subprocess + tempfile; never edits the
extractor or grader source and never mutates the fixture tree.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PIPELINE = os.path.join(REPO, "tools", "cur_pipeline.py")
FIXDIR = os.path.join(REPO, "tools", "tests", "cur_extractor", "fixtures")


def _sha(text):
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run(scratch, bundle, *extra, env=None, cwd=None, timeout=30):
    out = os.path.join(scratch, "out.json")
    trans = os.path.join(scratch, "t.txt")
    cmd = [sys.executable, PIPELINE, bundle, "--out", out, "--transcript", trans] + list(extra)
    merged = dict(os.environ)
    if env:
        merged.update(env)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd, env=merged)
    transcript = ""
    if os.path.exists(trans):
        with open(trans, "r", encoding="utf-8") as f:
            transcript = f.read()
    return p.returncode, transcript, out, p.stderr


def _bundle_digest(path):
    with open(path, "r", encoding="utf-8") as f:
        b = json.load(f)
    return _sha(json.dumps(b, sort_keys=True, separators=(",", ":")))


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    scratch = tempfile.mkdtemp(prefix="cur_pipeline_hardening_")
    failures = []
    total = 0
    ok = 0

    def check(label, cond, detail=""):
        nonlocal total, ok
        total += 1
        if cond:
            ok += 1
            print("  %-46s OK" % (label,))
        else:
            failures.append((label, detail))
            print("  %-46s FAIL  %s" % (label, detail))

    try:
        print("=" * 78)
        print("PIPELINE HARDENING — tools/tests/cur_pipeline/hardening.py")
        print("=" * 78)
        fx = os.path.join(FIXDIR, "e3-pass.json")

        # 1. successful fixture.
        rc, trans, out, _ = _run(scratch, fx)
        check("successful fixture -> 0", rc == 0 and "PIPELINE_STATUS=GRADED" in trans,
              "rc=%s" % rc)

        # 2. valid FAIL.
        failb = os.path.join(FIXDIR, "e4-degree4-move.json")
        rc, trans, _, _ = _run(scratch, failb)
        check("valid FAIL -> 1", rc == 1 and "PIPELINE_STATUS=GRADED" in trans,
              "rc=%s" % rc)

        # 3. valid CANNOT_DETERMINE.
        cdb = os.path.join(FIXDIR, "e3-role-only-negative-control.json")
        rc, trans, _, _ = _run(scratch, cdb)
        check("valid CANNOT_DETERMINE -> 3", rc == 3 and "PIPELINE_STATUS=GRADED" in trans,
              "rc=%s" % rc)

        # 4. extractor prints plausible output then exits 7 -> never graded.
        eb = os.path.join(scratch, "ex7_extractor.py")
        _write(eb, (
            "import json, sys\n"
            "json.dump({'schema_version': 1, 'evidence': {}, 'identity': {}}, sys.stdout)\n"
            "sys.exit(7)\n"
        ))
        rc, trans, _, _ = _run(scratch, fx, env={"CUR_PIPELINE_EXTRACTOR": eb})
        check("extractor exits 7 -> 2 EXECUTION_ERROR",
              rc == 2 and "PIPELINE_STATUS=EXECUTION_ERROR" in trans
              and "[grader]" not in trans and "[pipeline] unexpected extractor exit 7" in trans,
              "rc=%s" % rc)

        # 5. stale --out manifest present -> replaced with a validated fresh manifest.
        stale = os.path.join(scratch, "stale_out.json")
        _write(stale, json.dumps({"stale": True, "identity": {"bundle_digest": "deadbeef"}}))
        cmd = [sys.executable, PIPELINE, fx, "--out", stale,
               "--transcript", os.path.join(scratch, "stale_t.txt")]
        sp = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        matched = False
        if os.path.exists(stale):
            with open(stale, "r", encoding="utf-8") as f:
                try:
                    m = json.load(f)
                    matched = (m.get("identity", {}).get("bundle_digest") == _bundle_digest(fx))
                except ValueError:
                    matched = False
        check("stale --out replaced by validated manifest",
              sp.returncode == 0 and matched, "rc=%s matched=%s" % (sp.returncode, matched))

        # 6. extractor times out.
        tb = os.path.join(scratch, "hang_extractor.py")
        _write(tb, "import time\ntime.sleep(30)\n")
        rc, trans, _, _ = _run(scratch, fx, "--timeout", "1",
                               env={"CUR_PIPELINE_EXTRACTOR": tb}, timeout=15)
        check("extractor timeout -> 2 EXECUTION_ERROR",
              rc == 2 and "PIPELINE_STATUS=EXECUTION_ERROR" in trans
              and "[grader]" not in trans, "rc=%s" % rc)

        # 7. extractor killed by signal (negative returncode).
        kb = os.path.join(scratch, "kill_extractor.py")
        _write(kb, "import os, signal\nos.kill(os.getpid(), signal.SIGKILL)\n")
        rc, trans, _, _ = _run(scratch, fx, env={"CUR_PIPELINE_EXTRACTOR": kb})
        check("extractor killed -> 2 EXECUTION_ERROR",
              rc == 2 and "PIPELINE_STATUS=EXECUTION_ERROR" in trans,
              "rc=%s trans_has_status=%s" % (rc, "PIPELINE_STATUS=EXECUTION_ERROR" in trans))

        # 8. grader exits without a verdict.
        gb = os.path.join(scratch, "bad_grader.py")
        _write(gb, "import sys\nprint('not a verdict')\nsys.exit(2)\n")
        rc, trans, _, _ = _run(scratch, fx, env={"CUR_PIPELINE_GRADER": gb})
        check("grader no verdict -> 2 EXECUTION_ERROR",
              rc == 2 and "PIPELINE_STATUS=EXECUTION_ERROR" in trans,
              "rc=%s" % rc)

        # 9. unwritable transcript (parent path is a file).
        blocker = os.path.join(scratch, "blockfile")
        _write(blocker, "not a directory\n")
        bad_trans = os.path.join(blocker, "x.txt")
        cmd = [sys.executable, PIPELINE, fx, "--out", os.path.join(scratch, "uo_out.json"),
               "--transcript", bad_trans]
        up = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        check("unwritable transcript -> 2 (no partial verdict)",
              up.returncode == 2 and "cannot write transcript" in up.stderr, "rc=%s" % up.returncode)

        # 10. malformed input -> 2 REJECTED / never graded.
        mb = os.path.join(FIXDIR, "malformed-duplicate-id.json")
        rc, trans, _, _ = _run(scratch, mb)
        check("malformed input -> 2 REJECTED",
              rc == 2 and "PIPELINE_STATUS=REJECTED" in trans and "[grader]" not in trans,
              "rc=%s status=%s" % (rc, "PIPELINE_STATUS=" + ("REJECTED" if "REJECTED" in trans else "?")))

        # 11. foreign working directory.
        extcwd = os.path.join(scratch, "foreign")
        os.makedirs(extcwd, exist_ok=True)
        rc, trans, out, _ = _run(scratch, fx, cwd=extcwd)
        check("foreign working directory", rc == 0 and os.path.exists(out), "rc=%s" % rc)

        # 12. two complete pipeline invocations concurrently.
        b1 = os.path.join(FIXDIR, "e3-pass.json")
        b2 = os.path.join(FIXDIR, "e4-pass.json")
        o1 = os.path.join(scratch, "c1_out.json")
        o2 = os.path.join(scratch, "c2_out.json")
        t1 = os.path.join(scratch, "c1_t.txt")
        t2 = os.path.join(scratch, "c2_t.txt")
        p1 = subprocess.Popen([sys.executable, PIPELINE, b1, "--out", o1, "--transcript", t1],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        p2 = subprocess.Popen([sys.executable, PIPELINE, b2, "--out", o2, "--transcript", t2],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        r1 = p1.wait(timeout=30)
        r2 = p2.wait(timeout=30)
        c1_ok = r1 == 0 and os.path.exists(o1) and os.path.exists(t1)
        c2_ok = r2 == 0 and os.path.exists(o2) and os.path.exists(t2)
        check("two concurrent invocations", c1_ok and c2_ok, "r1=%s r2=%s" % (r1, r2))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print("=" * 78)
    print("SUMMARY: %d/%d pass, %d fail" % (ok, total, len(failures)))
    for label, detail in failures:
        print("    - %s: %s" % (label, detail))
    print("=" * 78)
    return 0 if len(failures) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
