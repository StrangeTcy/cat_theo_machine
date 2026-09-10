#!/usr/bin/env python3
"""run.py — selftests for tools/cur_artifact_schema.py.

Exercises the schema checker, the two emitters, and the identity drift test:

  * every current valid extractor fixture is schema-valid (exit 0), and matches the
    extractor's own accept/reject decision on the malformed set
  * schema rejection cases: duplicate ids, unknown contract, malformed collections,
    non-array citations, invalid numeric domains, E4 d/s-vs-e_in/e_out contradiction,
    E7 sequence-shorter-than-window, missing required structure
  * missing optional evidence remains schema-valid
  * the same schema-valid fixture still produces CANNOT_DETERMINE downstream (so schema
    validity is not mistaken for a verdict)
  * emit-json and emit-markdown are deterministic (byte-identical across runs)
  * foreign working directory
  * two concurrent schema checks
  * drift test: the schema module's pinned constants/identities match the extractor and
    grader they are bound to

Exit 0 if all pass; nonzero otherwise. Never edits the extractor or grader.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SCHEMA_CMD = os.path.join(REPO, "tools", "cur_artifact_schema.py")
EXTRACTOR = os.path.join(REPO, "tools", "cur_extract_evidence.py")
GRADER = os.path.join(REPO, "tools", "cur_grade_artifact.py")
EXTRACTOR_FIXDIR = os.path.join(REPO, "tools", "tests", "cur_extractor", "fixtures")
SCHEMA_FIXDIR = os.path.join(HERE, "fixtures")


def _run_argv(argv, cwd=None, env=None, timeout=60):
    merged = dict(os.environ)
    if env:
        merged.update(env)
    return subprocess.run([sys.executable] + argv, capture_output=True, text=True,
                          cwd=cwd, env=merged, timeout=timeout)


def _schema_check(bundle_path, cwd=None):
    p = _run_argv([SCHEMA_CMD, "check", bundle_path], cwd=cwd)
    report = {}
    if p.stdout:
        try:
            report = json.loads(p.stdout)
        except ValueError:
            pass
    return p.returncode, report


def _schema_valid(bundle_path):
    rc, report = _schema_check(bundle_path)
    return rc == 0 and bool(report.get("schema_valid"))


def _write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def main():
    scratch = tempfile.mkdtemp(prefix="cur_schema_selftest_")
    failures = []
    total = 0
    ok = 0

    def check(label, cond, detail=""):
        nonlocal total, ok
        total += 1
        if cond:
            ok += 1
            print("  %-52s OK" % (label,))
        else:
            failures.append((label, detail))
            print("  %-52s FAIL  %s" % (label, detail))

    try:
        print("=" * 78)
        print("SCHEMA SELFTEST — tools/tests/cur_schema/run.py")
        print("=" * 78)

        # ---- 1. every current valid extractor fixture is schema-valid.
        # The malformed trio (duplicate-id / nonarray-cites / unsupported-contract) is the
        # extractor-reject set and is asserted separately in test #2; exclude it here.
        malformed_set = ("malformed-duplicate-id.json", "malformed-nonarray-cites.json",
                         "unsupported-contract.json")
        extractor_fixtures = sorted(
            f for f in os.listdir(EXTRACTOR_FIXDIR)
            if f.endswith(".json") and f not in malformed_set)
        valid_ct = 0
        mismatch = []
        for fn in extractor_fixtures:
            path = os.path.join(EXTRACTOR_FIXDIR, fn)
            rc, report = _schema_check(path)
            if rc == 0 and report.get("schema_valid"):
                valid_ct += 1
            else:
                mismatch.append(fn)
        check("all current valid fixture families schema-valid (%d accepted)" % valid_ct,
              valid_ct == len(extractor_fixtures) and len(mismatch) == 0,
              "accepted=%s total=%s mismatch=%s" % (valid_ct, len(extractor_fixtures), mismatch))

        # ---- 2. the malformed set is rejected by BOTH schema checker and extractor.
        malformed_agree = True
        for fn in ("malformed-duplicate-id.json", "malformed-nonarray-cites.json",
                   "unsupported-contract.json"):
            path = os.path.join(EXTRACTOR_FIXDIR, fn)
            sc_rc, _ = _schema_check(path)
            ext = _run_argv([EXTRACTOR, path, "--out", os.path.join(scratch, "x.json")])
            if not (sc_rc == 2 and ext.returncode == 2):
                malformed_agree = False
        check("malformed set rejected by schema checker AND extractor", malformed_agree)

        # ---- 3. schema rejection fixtures.
        reject_cases = [
            "duplicate-node-id.json",
            "unknown-contract.json",
            "malformed-collections.json",
            "nonarray-cites.json",
            "invalid-numeric-domain.json",
            "e4-dual-form-contradiction.json",
            "e7-width-short-sequence.json",
            "missing-required-structure.json",
        ]
        rej_all = True
        for fn in reject_cases:
            rc, report = _schema_check(os.path.join(SCHEMA_FIXDIR, fn))
            if not (rc == 2 and not report.get("schema_valid")):
                rej_all = False
        check("rejection fixtures each exit 2 (schema-invalid)", rej_all)

        # ---- 4. missing optional evidence stays schema-valid.
        opt_ok = _schema_valid(os.path.join(SCHEMA_FIXDIR, "missing-optional-evidence.json"))
        check("missing optional evidence remains schema-valid", opt_ok)

        # ---- 5. canonical alternate forms: E4 d/s that agrees is accepted.
        dual_ok = _schema_valid(os.path.join(SCHEMA_FIXDIR, "e4-valid-dual-form.json"))
        check("E4 d/s alternate form (consistent) is schema-valid", dual_ok)

        # ---- 6. schema-valid payload still produces CANNOT_DETERMINE downstream.
        # e7-params-only is schema-valid, but the grader derives no evidence bits.
        cd_path = os.path.join(SCHEMA_FIXDIR, "e7-params-only.json")
        cd_schema_rc, cd_report = _schema_check(cd_path)
        man_path = os.path.join(scratch, "cd_manifest.json")
        ext = _run_argv([EXTRACTOR, cd_path, "--out", man_path])
        grad = _run_argv([GRADER, man_path])
        grad_out = {}
        if grad.stdout:
            try:
                grad_out = json.loads(grad.stdout)
            except ValueError:
                pass
        cd_downstream = (cd_schema_rc == 0 and grad.returncode == 3
                         and grad_out.get("final") == "CANNOT_DETERMINE")
        check("schema-valid payload still yields CANNOT_DETERMINE downstream", cd_downstream,
              "schema_rc=%s grader_rc=%s final=%s" % (cd_schema_rc, grad.returncode, grad_out.get("final")))

        # ---- 7. determinism of emit-json.
        a = _run_argv([SCHEMA_CMD, "emit-json"])
        b = _run_argv([SCHEMA_CMD, "emit-json"])
        check("emit-json deterministic", a.returncode == 0 and b.returncode == 0 and a.stdout == b.stdout)

        # ---- 8. determinism of emit-markdown.
        md1 = _run_argv([SCHEMA_CMD, "emit-markdown"])
        md2 = _run_argv([SCHEMA_CMD, "emit-markdown"])
        check("emit-markdown deterministic", md1.returncode == 0 and md2.returncode == 0
              and md1.stdout == md2.stdout)

        # ---- 9. emitted markdown carries no timestamp/date literal.
        has_date = False
        for line in md1.stdout.splitlines():
            for tok in ("20", "19"):
                if len(line) >= 10 and line.strip().startswith(tok):
                    has_date = True
        # A date literal looks like YYYY-MM-DD; scan for the pattern.
        import re
        has_date = bool(re.search(r"\b(?:20|19)\d{2}-\d{2}-\d{2}\b", md1.stdout))
        check("emit-markdown contains no timestamp/date literal", not has_date)

        # ---- 10. foreign working directory.
        extcwd = os.path.join(scratch, "outside")
        os.makedirs(extcwd, exist_ok=True)
        fwd_rc, fd_report = _schema_check(os.path.join(SCHEMA_FIXDIR, "e7-params-only.json"), cwd=extcwd)
        check("foreign working directory", fwd_rc == 0 and bool(fd_report.get("schema_valid")))

        # ---- 11. two concurrent schema checks.
        # Both children are LAUNCHED before either is awaited. The previous version called
        # the blocking helper twice in sequence, so the "concurrent" label described two
        # sequential runs. Overlap is now observed, not assumed: both handles are checked
        # for liveness after both have been started.
        cmd1 = [sys.executable, SCHEMA_CMD, "check",
                os.path.join(SCHEMA_FIXDIR, "e7-params-only.json")]
        cmd2 = [sys.executable, SCHEMA_CMD, "check",
                os.path.join(SCHEMA_FIXDIR, "missing-optional-evidence.json")]
        proc1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        proc2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        overlapped = (proc1.poll() is None) and (proc2.poll() is None)
        out1, _ = proc1.communicate(timeout=180)
        out2, _ = proc2.communicate(timeout=180)
        concurrent_ok = False
        try:
            r1 = json.loads(out1)
            r2 = json.loads(out2)
            concurrent_ok = (overlapped and proc1.returncode == 0 and proc2.returncode == 0
                             and bool(r1.get("schema_valid")) and bool(r2.get("schema_valid")))
        except ValueError:
            concurrent_ok = False
        check("two concurrent schema checks", concurrent_ok,
              "overlapped=%s rc=%s,%s" % (overlapped, proc1.returncode, proc2.returncode))

        # ---- 12. drift test: schema-module pinned constants/identities match extractor+grader.
        drift_ok = _run_drift_test()
        test_path = os.path.join(REPO, "tools", "cur_artifact_schema.py")
        drift_ok = drift_ok and _drift_by_import(test_path)
        check("drift test: schema pins match extractor/grader", drift_ok)

        # ---- 13. unknown command rejected.
        unk = _run_argv([SCHEMA_CMD, "bogus"])
        check("unknown schema command rejected (exit 2)", unk.returncode == 2)

    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    print("=" * 78)
    print("SUMMARY: %d/%d pass, %d fail" % (ok, total, len(failures)))
    for label, detail in failures:
        print("    - %s: %s" % (label, detail))
    print("=" * 78)
    return 0 if len(failures) == 0 else 1


def _run_drift_test():
    """Structural drift: re-import the schema module and compare to extractor/grader in-process."""
    try:
        sys.path.insert(0, os.path.join(REPO, "tools"))
        import importlib
        schema = importlib.import_module("cur_artifact_schema")
        extractor = importlib.import_module("cur_extract_evidence")
        grader = importlib.import_module("cur_grade_artifact")
        checks = [
            schema.SCHEMA_VERSION == grader.SCHEMA_VERSION,
            schema.RULESET_ID == grader.RULESET_ID,
            schema.BUNDLE_SCHEMA == extractor.BUNDLE_SCHEMA,
            schema.E3_N == extractor.E3_N,
            schema.E3_ODD_N == extractor.E3_ODD_N,
            schema.E4_TWO_HOUSES == extractor.E4_TWO_HOUSES,
            schema.E4_MAX_DEGREE == extractor.E4_MAX_DEGREE,
            schema.E7_WINDOW == extractor.E7_WINDOW,
            schema.E7_MODULUS == extractor.E7_MODULUS,
            schema.E7_ODD_WINDOW == extractor.E7_ODD_WINDOW,
            schema.PINNED_RUBRIC_REF == grader.PINNED_RUBRIC_REF,
            schema.PINNED_CONTRACT_REFS == grader.PINNED_CONTRACT_REFS,
            schema.PINNED_CONTRACT_COMMITS == extractor.PINNED_CONTRACT_COMMITS,
            schema.PINNED_CONTRACT_DIGESTS == extractor.PINNED_CONTRACT_DIGESTS,
            schema.PINNED_CONTRACT_IN_TREE == extractor.PINNED_CONTRACT_IN_TREE,
        ]
        return all(checks)
    except Exception as e:  # noqa: BLE001 host-tool test; re-raised by caller logic only
        print("    drift test import error: %s" % e)
        return False


def _drift_by_import(module_path):
    """Verify the module's own exports stay consistent with what emit-json surfaces."""
    try:
        with open(module_path, "r", encoding="utf-8") as f:
            src = f.read()
        # The drift test already uses in-process imports; here assert the source is not
        # broken by emitting json and rebasing fields it references.
        js = _run_argv([SCHEMA_CMD, "emit-json"])
        if js.returncode != 0:
            return False
        data = json.loads(js.stdout)
        # regenerate via the real module to confirm the JSON matches its FIELD_TABLE length.
        sys.path.insert(0, os.path.join(REPO, "tools"))
        import importlib
        schema = importlib.import_module("cur_artifact_schema")
        return len(data.get("fields", [])) == len(schema.FIELD_TABLE) and \
               data["bundle_schema"] == schema.BUNDLE_SCHEMA
    except Exception as e:  # noqa: BLE001
        print("    schema source drift error: %s" % e)
        return False


if __name__ == "__main__":
    sys.exit(main())
