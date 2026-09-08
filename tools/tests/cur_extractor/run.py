#!/usr/bin/env python3
"""run.py — selftest for tools/cur_extract_evidence.py (frozen artifact -> evidence -> grader).

Runs the END-TO-END path for every frozen-style fixture:
    frozen G-ENG-style bundle -> cur_extract_evidence.py -> evidence manifest
    -> cur_grade_artifact.py -> C1..C6 verdicts

It also asserts the extractor's evidence discipline (every true bit cited; broken refs turn into
absent evidence + diagnostics), that it never reads oracle.json, that decorative labels are
ignored, that concurrent runs isolate, and that foreign working directories work.

Exit 0 if all pass; non-zero otherwise. This harness never reads the grader's oracle.json; the
only JSON it reads are the fixtures it owns and the manifests it produces.
"""

import concurrent.futures
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EXTRACTOR = os.path.join(REPO, "tools", "cur_extract_evidence.py")
GRADER = os.path.join(REPO, "tools", "cur_grade_artifact.py")
FIXDIR = os.path.join(HERE, "fixtures")

# Expected end-to-end outcomes per fixture key.
EXPECT = {
    "frozen-e3-pass": {"extractor_exit": 0, "grader_exit": 0, "grader_final": "PASS"},
    "frozen-decorative-label": {"extractor_exit": 0, "grader_exit": 0, "grader_final": "PASS"},
    "frozen-e4-missing-degree-bound": {"extractor_exit": 0, "grader_exit": 3, "grader_final": "CANNOT_DETERMINE"},
    "frozen-e7-broken-ref": {"extractor_exit": 1, "grader_exit": 3, "grader_final": "CANNOT_DETERMINE"},
    "frozen-e4-contradictory": {"extractor_exit": 0, "grader_exit": 2, "grader_final": "MALFORMED"},
    "frozen-unsupported-contract": {"extractor_exit": 2, "grader_run": False},
}


def extract(bundle_path, out_path, cwd=REPO):
    cmd = [sys.executable, EXTRACTOR, bundle_path, "--out", out_path]
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def write_manifest(bundle_path, out_path, block=True, cwd=REPO):
    """Run the extractor subprocess (optionally in a worker) writing a manifest file."""
    return extract(bundle_path, out_path, cwd)


def run_grader(manifest_path, cwd=REPO):
    p = subprocess.run([sys.executable, GRADER, manifest_path], cwd=cwd, capture_output=True, text=True)
    try:
        parsed = json.loads(p.stdout.strip())
    except ValueError:
        parsed = {"error": p.stdout.strip(), "stderr": p.stderr.strip()}
    return p.returncode, parsed


def main():
    failures = []
    summary = {"checks": 0, "ok": 0}

    def record(label, ok, detail=""):
        summary["checks"] += 1
        if ok:
            summary["ok"] += 1
        else:
            failures.append((label, detail))

    print("=" * 78)
    print("EXTRACTOR SELFTEST — tools/tests/cur_extractor/run.py")
    print("=" * 78)

    manifest_dir = tempfile.mkdtemp(prefix="cur_extractor_manifests_")

    # ---- CHECK 1: end-to-end per fixture (extractor -> grader), matching expected outcome.
    print("CHECK 1 — end-to-end extractor -> grader for each fixture")
    for key, exp in EXPECT.items():
        bpath = os.path.join(FIXDIR, key + ".json")
        mpath = os.path.join(manifest_dir, key + ".manifest.json")
        xrc, _, _ = extract(bpath, mpath)
        if exp.get("grader_run", True) is False:
            # extractor rejected -> no manifest, no grading.
            record("check1 " + key, xrc == exp["extractor_exit"] and not os.path.exists(mpath),
                   "extractor_exit=%s" % xrc)
            print("  %-32s extractor_exit=%s (%s)" % (key, xrc, "OK" if xrc == exp["extractor_exit"] else "FAIL"))
            continue
        grc, gparsed = run_grader(mpath)
        ok = (xrc == exp["extractor_exit"]) and (grc == exp["grader_exit"]) \
             and (gparsed.get("final") == exp["grader_final"])
        record("check1 " + key, ok,
               "extractor_exit=%s grader_exit=%s final=%s" % (xrc, grc, gparsed.get("final")))
        print("  %-32s extractor_exit=%s grader_exit=%s final=%s (%s)" % (
            key, xrc, grc, gparsed.get("final"), "OK" if ok else "FAIL"))
    print("")

    # ---- CHECK 2: manifest validates against grader ruleset identity.
    print("CHECK 2 — emitted manifest carries matching schema_version / ruleset_id")
    spec = importlib.util.spec_from_file_location("cur_grade_artifact", GRADER)
    grader_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(grader_mod)
    for key in ["frozen-e3-pass", "frozen-e4-missing-degree-bound"]:
        mpath = os.path.join(manifest_dir, key + ".manifest.json")
        with open(mpath, "r", encoding="utf-8") as f:
            m = json.load(f)
        ok = (m.get("schema_version") == grader_mod.SCHEMA_VERSION) \
             and (m.get("ruleset_id") == grader_mod.RULESET_ID) \
             and (m.get("contract_ref") in (None, grader_mod.PINNED_CONTRACT_REFS.get(m.get("contract"))))
        record("check2 " + key, ok, "manifest has ruleset_id=%s" % m.get("ruleset_id"))
        print("  %s: ruleset_id match=%s" % (key, "OK" if ok else "FAIL"))
    print("")

    # ---- CHECK 3: broken ref -> evidence bit absent + extractor diagnostic (E7 C2 CD).
    print("CHECK 3 — broken node ref produces absent evidence + diagnostic")
    bpath = os.path.join(FIXDIR, "frozen-e7-broken-ref.json")
    mpath = os.path.join(manifest_dir, "frozen-e7-broken-ref.manifest.json")
    xrc, _, _ = extract(bpath, mpath)
    with open(mpath, "r", encoding="utf-8") as f:
        m = json.load(f)
    diags = m.get("extractor_diagnostics", [])
    c2 = m["evidence"].get("C2", {})
    has_diag = any("unresolved ref" in d for d in diags)
    bit_absent = "shows_even_window_delta" not in c2
    ok3 = (xrc == 1) and has_diag and bit_absent
    record("check3", ok3, "xrc=%s diag=%s c2_absent=%s" % (xrc, has_diag, bit_absent))
    print("  xrc=%s diagnostic_present=%s C2_bit_absent=%s (%s)" % (xrc, has_diag, bit_absent, "OK" if ok3 else "FAIL"))
    print("")

    # ---- CHECK 4: contradictory cited records -> grader rejects exit 2.
    print("CHECK 4 — contradictory cited records rejected by grader (exit 2)")
    bpath = os.path.join(FIXDIR, "frozen-e4-contradictory.json")
    mpath = os.path.join(manifest_dir, "frozen-e4-contradictory.manifest.json")
    xrc, _, _ = extract(bpath, mpath)
    grc, gparsed = run_grader(mpath)
    ok4 = (grc == 2) and (gparsed.get("final") == "MALFORMED")
    record("check4", ok4, "grader_exit=%s final=%s" % (grc, gparsed.get("final")))
    print("  grader_exit=%s final=%s (%s)" % (grc, gparsed.get("final"), "OK" if ok4 else "FAIL"))
    print("")

    # ---- CHECK 5: decorative expected-label field does not affect extraction.
    print("CHECK 5 — decorative expected-label field is ignored")
    def manifest_for(key):
        bpath = os.path.join(FIXDIR, key + ".json")
        mpath = os.path.join(manifest_dir, key + ".manifest.json")
        extract(bpath, mpath)
        with open(mpath, "r", encoding="utf-8") as f:
            return json.load(f)
    ma = manifest_for("frozen-e3-pass")
    mb = manifest_for("frozen-decorative-label")
    ok5 = (ma["evidence"] == mb["evidence"]) and (ma["citations"] == mb["citations"])
    record("check5", ok5, "evidence/citations unchanged" if ok5 else "CHANGED")
    print("  evidence+citations identical: %s" % ("OK" if ok5 else "FAIL"))
    print("")

    # ---- CHECK 6: concurrent extractions isolate outputs.
    print("CHECK 6 — concurrent extractions isolate outputs")
    conc = ["frozen-e3-pass", "frozen-e7-broken-ref"]
    def one(key):
        bpath = os.path.join(FIXDIR, key + ".json")
        mpath = os.path.join(manifest_dir, key + ".concurrent.manifest.json")
        extract(bpath, mpath)
        with open(mpath, "r", encoding="utf-8") as f:
            return key, json.load(f)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(one, key) for key in conc]
        results = [fut.result() for fut in futs]
    got = dict(results)
    isolated = True
    for key in conc:
        ref = manifest_for(key)
        cur = got[key]
        if ref["evidence"] != cur["evidence"] or ref["citations"] != cur["citations"]:
            isolated = False
    record("check6", isolated, "concurrent matches serial" if isolated else "DIFFERS")
    print("  isolated: %s" % ("OK" if isolated else "FAIL"))
    print("")

    # ---- CHECK 7: foreign working directory works end-to-end.
    print("CHECK 7 — end-to-end from a working directory outside the repository")
    extcwd = os.path.join(os.path.dirname(REPO), "cur_extractor_outside")
    os.makedirs(extcwd, exist_ok=True)
    bpath = os.path.join(FIXDIR, "frozen-e3-pass.json")
    mpath = os.path.join(extcwd, "e3.manifest.json")
    xrc, _, _ = extract(bpath, mpath, cwd=extcwd)
    grc, gparsed = run_grader(mpath, cwd=extcwd)
    ok7 = (xrc == 0) and (grc == 0) and (gparsed.get("final") == "PASS")
    record("check7", ok7, "extractor_exit=%s grader_exit=%s" % (xrc, grc))
    print("  cwd=%s: extractor_exit=%s grader_exit=%s (%s)" % (extcwd, xrc, grc, "OK" if ok7 else "FAIL"))
    os.unlink(mpath)
    os.rmdir(extcwd)
    print("")

    # ---- CHECK 8: extractor source does not reference oracle/labels.
    print("CHECK 8 — extractor does not import/read oracle.json or any expected-label")
    with open(EXTRACTOR, "r", encoding="utf-8") as f:
        src = f.read()
    no_oracle = "oracle" not in src
    no_expected = "expected_label" not in src
    ok8 = no_oracle and no_expected
    record("check8", ok8, "oracle_text=%s expected_label_text=%s" % (no_oracle, no_expected))
    print("  no 'oracle' in source: %s ; no 'expected_label' in source: %s" % (no_oracle, no_expected))
    print("")

    # ---- summary
    shutil.rmtree(manifest_dir, ignore_errors=True)
    print("=" * 78)
    print("SUMMARY")
    print("  assertions run: %d" % summary["checks"])
    print("  ok             : %d" % summary["ok"])
    print("  fail           : %d" % len(failures))
    if failures:
        for label, detail in failures:
            print("    - %s: %s" % (label, detail))
    print("=" * 78)
    return 0 if len(failures) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
