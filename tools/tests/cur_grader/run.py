#!/usr/bin/env python3
"""run.py — selftest for tools/cur_grade_artifact.py.

Runs every fixture through the grader as a subprocess and asserts the emitted
result, discrepancy label and exit status match the SEPARATE oracle (oracle.json).
The oracle is read ONLY here; the grader never reads it.

Hardening (post-571c9d1) coverage:
  * every fixture -> expected final/discrepancy/exit (subprocess);
  * changing a fixture's decorative expected-label field does NOT change the result;
  * removing required evidence changes PASS -> CANNOT_DETERMINE;
  * contradictory evidence exits 2;
  * each failing fixture emits EXACTLY one discrepancy label;
  * multi-taxonomy ambiguity (E4 C1+C3, E7 C2+C3) exits 2;
  * string "false", numeric 1, array, object evidence -> exit 2;
  * unknown evidence key -> exit 2 (must not silently become CANNOT_DETERMINE);
  * ruleset_id mismatch -> exit 2;
  * missing evidence (CD) remains CANNOT_DETERMINE, exit 3;
  * two grader processes concurrently -> identical COMPLETE JSON (exit+final+discrepancy+checks);
  * running from a cwd outside the repository.

Exit 0 if all pass; non-zero (count of failures) otherwise.
"""

import json
import os
import subprocess
import sys
import concurrent.futures

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GRADER = os.path.join(REPO, "tools", "cur_grade_artifact.py")
FIXDIR = os.path.join(HERE, "fixtures")
ORACLE = os.path.join(HERE, "oracle.json")


def load_oracle():
    with open(ORACLE, "r", encoding="utf-8") as f:
        return json.load(f)


def run_grader(path, cwd=None):
    """Run the grader subprocess on a fixture; return (exit, parsed_json, raw)."""
    cmd = [sys.executable, GRADER, path]
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    raw = p.stdout.strip()
    try:
        parsed = json.loads(raw)
    except ValueError:
        parsed = {"error": raw, "stderr": p.stderr.strip()}
    return p.returncode, parsed, raw


def main():
    oracle = load_oracle()
    failures = []
    summary = {"checks": 0, "ok": 0, "fail": 0}

    def record(label, ok, detail=""):
        summary["checks"] += 1
        if ok:
            summary["ok"] += 1
        else:
            summary["fail"] += 1
            failures.append((label, detail))

    fixtures = sorted(f for f in os.listdir(FIXDIR) if f.endswith(".json"))

    print("=" * 78)
    print("GRADER SELFTEST (hardened) — tools/tests/cur_grader/run.py")
    print("=" * 78)

    # ---- CHECK 1: run every fixture, compare to oracle.
    print(f"{'fixture':<20}{'exit':<6}{'final':<24}{'discrepancy':<24}{'ok'}")
    print("-" * 78)
    for f in fixtures:
        path = os.path.join(FIXDIR, f)
        fid = f[:-5]
        exp = oracle.get(fid)
        if exp is None:
            record("oracle-missing " + fid, False, "no oracle entry")
            print(f"{fid:<20}{'?':<6}{'-':<24}{'-':<24}{'NO-ORACLE'}")
            continue
        rc, parsed, _ = run_grader(path, cwd=REPO)
        final = parsed.get("final", "?")
        disc = parsed.get("discrepancy", "?")
        ok = (rc == exp["exit"]) and (final == exp["final"]) and (disc == exp["discrepancy"])
        record("check1 " + fid, ok,
               "got exit=%s final=%s disc=%s want exit=%s final=%s disc=%s" % (
                   rc, final, disc, exp["exit"], exp["final"], exp["discrepancy"]))
        print(f"{fid:<20}{str(rc):<6}{final:<24}{disc:<24}{'Y' if ok else 'N'}")

    print("-" * 78)
    check1_fail = sum(1 for lbl, _ in failures if lbl.startswith("check1 "))
    print("check1 fixtures graded: %d ok, %d fail" % (len(fixtures) - check1_fail, check1_fail))
    print("")

    # ---- CHECK 2: decorative expected-label field is ignored.
    print("CHECK 2 — decorative expected-label field is ignored")
    import tempfile
    for f in ["E4-M1.json", "E7-M5.json", "PASS-E3.json"]:
        src = os.path.join(FIXDIR, f)
        with open(src, "r", encoding="utf-8") as fh:
            art = json.load(fh)
        art["expected_label"] = "DO_NOT_TRUST_THIS_LABEL"
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(art, tf)
            mutpath = tf.name
        rc0, base, _ = run_grader(src, cwd=REPO)
        rc1, mutated, _ = run_grader(mutpath, cwd=REPO)
        os.unlink(mutpath)
        same = (rc0 == rc1) and (base.get("final") == mutated.get("final")) \
               and (base.get("discrepancy") == mutated.get("discrepancy"))
        record("check2 " + f, same, "unchanged" if same else "CHANGED!")
        print("  %s: %s" % (f, "unchanged" if same else "CHANGED"))
    print("")

    # ---- CHECK 3: removing required evidence -> CANNOT_DETERMINE.
    print("CHECK 3 — removing required evidence turns PASS to CANNOT_DETERMINE")
    for f in ["PASS-E3.json", "PASS-E4.json", "PASS-E7.json"]:
        src = os.path.join(FIXDIR, f)
        with open(src, "r", encoding="utf-8") as fh:
            art = json.load(fh)
        for c in art["evidence"]:
            for k in list(art["evidence"][c].keys()):
                art["evidence"][c][k] = False
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(art, tf)
            stripped = tf.name
        rc, parsed, _ = run_grader(stripped, cwd=REPO)
        os.unlink(stripped)
        became_cd = (parsed.get("final") == "CANNOT_DETERMINE")
        record("check3 " + f, became_cd, "final=%s" % parsed.get("final"))
        print("  %s: final=%s %s" % (f, parsed.get("final"), "OK" if became_cd else "FAIL"))
    print("")

    # ---- CHECK 4: contradictory evidence exits 2.
    print("CHECK 4 — contradictory evidence exits 2")
    rc, parsed, _ = run_grader(os.path.join(FIXDIR, "contradictory_1.json"), cwd=REPO)
    ok4 = (rc == 2)
    record("check4", ok4, "exit=%s" % rc)
    print("  contradictory_1: exit=%s %s" % (rc, "OK" if ok4 else "FAIL"))
    print("")

    # ---- CHECK 5: each failing fixture emits exactly one discrepancy label.
    print("CHECK 5 — each failing fixture emits exactly one discrepancy label")
    failing = [f[:-5] for f in fixtures if oracle.get(f[:-5], {}).get("final") == "FAIL"]
    for fid in failing:
        path = os.path.join(FIXDIR, fid + ".json")
        rc, parsed, _ = run_grader(path, cwd=REPO)
        disc = parsed.get("discrepancy")
        single = disc in (
            "hypothesis-omitted", "descent-unsupported", "overclaim",
            "constant-injection", "derivation-absent", "preservation-unsupported")
        record("check5 " + fid, single, "disc=%r" % disc)
        print("  %s: disc=%s %s" % (fid, disc, "OK" if single else "FAIL"))
    print("")

    # ---- CHECK 5b: multi-taxonomy ambiguity exits 2.
    print("CHECK 5b — multi-taxonomy failure is AMBIGUOUS (exit 2)")
    for fid in ["AMB-E4", "AMB-E7"]:
        rc, parsed, _ = run_grader(os.path.join(FIXDIR, fid + ".json"), cwd=REPO)
        ok = (rc == 2) and (parsed.get("final") == "AMBIGUOUS_DISCREPANCY")
        record("check5b " + fid, ok, "exit=%s final=%s" % (rc, parsed.get("final")))
        print("  %s: exit=%s final=%s %s" % (fid, rc, parsed.get("final"), "OK" if ok else "FAIL"))
    print("")

    # ---- CHECK 6: schema violations exit 2.
    print("CHECK 6 — schema violations (non-boolean / unknown key / ruleset) exit 2")
    for fid in ["BAD-BOOL-STR", "BAD-NUM", "BAD-ARR", "BAD-OBJ", "UNKNOWN-KEY", "RULESET-MISMATCH"]:
        rc, parsed, _ = run_grader(os.path.join(FIXDIR, fid + ".json"), cwd=REPO)
        ok = (rc == 2) and (parsed.get("final") == "MALFORMED")
        record("check6 " + fid, ok, "exit=%s final=%s" % (rc, parsed.get("final")))
        print("  %s: exit=%s final=%s %s" % (fid, rc, parsed.get("final"), "OK" if ok else "FAIL"))
    print("")

    # ---- CHECK 7: missing evidence remains CANNOT_DETERMINE, exit 3.
    print("CHECK 7 — missing evidence (CD) remains CANNOT_DETERMINE, exit 3")
    for fid in ["CD-E3", "CD-E4", "CD-E7"]:
        rc, parsed, _ = run_grader(os.path.join(FIXDIR, fid + ".json"), cwd=REPO)
        ok = (rc == 3) and (parsed.get("final") == "CANNOT_DETERMINE")
        record("check7 " + fid, ok, "exit=%s final=%s" % (rc, parsed.get("final")))
        print("  %s: exit=%s final=%s %s" % (fid, rc, parsed.get("final"), "OK" if ok else "FAIL"))
    print("")

    # ---- CHECK 8: concurrent graders -> identical COMPLETE JSON.
    print("CHECK 8 — concurrent grader processes -> identical complete JSON")
    conc_files = ["E4-M1.json", "E7-M6.json"]
    isolated = True
    def one(fn):
        path = os.path.join(FIXDIR, fn)
        rc, parsed, raw = run_grader(path, cwd=REPO)
        return fn, rc, parsed
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(one, fn) for fn in conc_files]
        results = [fut.result() for fut in futs]
    got = dict((fn, (rc, parsed)) for fn, rc, parsed in results)
    for fn in conc_files:
        rc, parsed = got[fn]
        # Compare against a FRESH serial run to guarantee the complete JSON matches.
        frc, fparsed, _ = run_grader(os.path.join(FIXDIR, fn), cwd=REPO)
        full_match = (rc == frc) and (json.dumps(parsed, sort_keys=True) == json.dumps(fparsed, sort_keys=True))
        if not full_match:
            isolated = False
    record("check8", isolated, "concurrent outputs identical")
    print("  isolated+identical: %s" % ("OK" if isolated else "FAIL"))
    print("")

    # ---- CHECK 9: run from a cwd outside the repository.
    print("CHECK 9 — run from a working directory outside the repository")
    extcwd = os.path.join(os.path.dirname(REPO), "grader_selftest_outside")
    os.makedirs(extcwd, exist_ok=True)
    rc, parsed, _ = run_grader(os.path.join(FIXDIR, "PASS-E4.json"), cwd=extcwd)
    ok9 = (rc == 0) and (parsed.get("final") == "PASS")
    record("check9", ok9, "exit=%s final=%s" % (rc, parsed.get("final")))
    print("  cwd=%s: exit=%s final=%s %s" % (extcwd, rc, parsed.get("final"), "OK" if ok9 else "FAIL"))
    os.rmdir(extcwd)
    print("")

    # ---- summary
    print("=" * 78)
    print("SUMMARY")
    print("  assertions run: %d" % summary["checks"])
    print("  ok             : %d" % summary["ok"])
    print("  fail           : %d" % summary["fail"])
    if failures:
        print("  FAILURES:")
        for label, detail in failures:
            print("    - %s: %s" % (label, detail))
    print("=" * 78)
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
