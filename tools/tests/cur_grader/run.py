#!/usr/bin/env python3
"""run.py — selftest for tools/cur_grade_artifact.py.

Runs every fixture through the grader as a subprocess and asserts the emitted
result, discrepancy label and exit status match the SEPARATE oracle (oracle.json).
The oracle is read ONLY here; the grader never reads it.

Eight checks:
  1. every fixture -> expected final/discrepancy/exit (via subprocess);
  2. changing a fixture's decorative expected-label field does NOT change the result;
  3. removing required evidence changes PASS -> CANNOT_DETERMINE;
  4. contradictory evidence exits 2;
  5. each failing fixture emits EXACTLY one discrepancy label;
  6. two grader processes concurrently -> isolated outputs;
  7. run from a working directory OUTSIDE the repository;
  8. full per-fixture run captured (direct invocation once).

Exit 0 if all pass; non-zero (count of failures) otherwise.
"""

import json
import os
import subprocess
import sys
import concurrent.futures

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))   # repo root (3 up from cur_grader)
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
    except Exception:
        parsed = {"error": raw, "stderr": p.stderr.strip()}
    return p.returncode, parsed, raw


def main():
    oracle = load_oracle()
    failures = []
    summary = {"fixtures_run": 0, "ok": 0, "fail": 0}

    # ---------------------------------------------------------------- fixture list
    fixtures = sorted(
        f for f in os.listdir(FIXDIR)
        if f.endswith(".json") and f != "oracle.json"
        and not f.startswith("_")
    )

    def record(label, ok, detail=""):
        summary["fixtures_run"] += 1
        if ok:
            summary["ok"] += 1
        else:
            summary["fail"] += 1
            failures.append((label, detail))

    # ---- CHECK 1 & 8: run every fixture through the grader as subprocess, compare to oracle.
    print("=" * 78)
    print("GRADER SELFTEST — tools/tests/cur_grader/run.py")
    print("=" * 78)
    print(f"{'fixture':<20}{'exit':<6}{'final':<20}{'discrepancy':<24}{'ok'}")
    print("-" * 78)

    for f in fixtures:
        path = os.path.join(FIXDIR, f)
        fid = f[:-5]  # strip .json
        exp = oracle.get(fid)
        if exp is None:
            record(f"expected result missing for {fid}", False, "no oracle entry")
            print(f"{fid:<20}{'?':<6}{'-':<20}{'-':<24}{'NO-ORACLE'}")
            continue
        rc, parsed, raw = run_grader(path, cwd=REPO)
        final = parsed.get("final", "?")
        disc = parsed.get("discrepancy", "?")
        ok = (rc == exp["exit"]) and (final == exp["final"]) and (disc == exp["discrepancy"])
        record(f"check1 {fid}", ok,
               f"got exit={rc} final={final} disc={disc} want exit={exp['exit']} final={exp['final']} disc={exp['discrepancy']}")
        print(f"{fid:<20}{str(rc):<6}{final:<20}{disc:<24}{'Y' if ok else 'N'}")

    print("-" * 78)
    print(f"check1/8 fixtures graded: {summary['ok']} ok, {summary['fail']} fail")
    print("")

    # ---- CHECK 2: changing a decorative expected-label field does NOT change result.
    # The fixtures carry an expected_label? They don't currently; to prove the grader ignores any
    # provided label, inject a decorative field into a copy and confirm identical output.
    print("CHECK 2 — decorative expected-label field is ignored")
    import tempfile
    label_mutations = 0
    for f in ["E4-M1.json", "E7-M5.json", "PASS-E3.json"]:
        src = os.path.join(FIXDIR, f)
        with open(src, "r", encoding="utf-8") as fh:
            art = json.load(fh)
        art["expected_label"] = "DO_NOT_TRUST_THIS_LABEL"  # decorative, must be ignored
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(art, tf)
            mutpath = tf.name
        rc0, base, _ = run_grader(src, cwd=REPO)
        rc1, mutated, _ = run_grader(mutpath, cwd=REPO)
        os.unlink(mutpath)
        same = (rc0 == rc1) and (base.get("final") == mutated.get("final")) \
               and (base.get("discrepancy") == mutated.get("discrepancy"))
        record("check2 decorative label", same, f"{f}: {'unchanged' if same else 'CHANGED!'}")
        print(f"  {f}: {('unchanged' if same else 'CHANGED')}")
        if same:
            label_mutations += 1
    print("")

    # ---- CHECK 3: removing required evidence changes PASS -> CANNOT_DETERMINE.
    print("CHECK 3 — removing required evidence turns PASS to CANNOT_DETERMINE")
    for f, contract in [("PASS-E3.json", "E3"), ("PASS-E4.json", "E4"), ("PASS-E7.json", "E7")]:
        src = os.path.join(FIXDIR, f)
        with open(src, "r", encoding="utf-8") as fh:
            art = json.load(fh)
        # Strip all pass evidence (set every pass key False) but keep structure.
        for c in art["evidence"]:
            for k in list(art["evidence"][c].keys()):
                # set every evidence key to False -> no pass evidence -> CANNOT_DETERMINE
                art["evidence"][c][k] = False
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as tf:
            json.dump(art, tf)
            stripped = tf.name
        rc, parsed, _ = run_grader(stripped, cwd=REPO)
        os.unlink(stripped)
        became_cd = (parsed.get("final") == "CANNOT_DETERMINE")
        record("check3 evidence-removal->CD", became_cd, f"{f}: final={parsed.get('final')}")
        print(f"  {f}: final={parsed.get('final')} {'OK' if became_cd else 'FAIL'}")
    print("")

    # ---- CHECK 4: contradictory evidence exits 2.
    print("CHECK 4 — contradictory evidence exits 2")
    src = os.path.join(FIXDIR, "contradictory_1.json")
    rc, parsed, _ = run_grader(src, cwd=REPO)
    ok4 = (rc == 2)
    record("check4 contradictory", ok4, f"exit={rc} (want 2)")
    print(f"  contradictory_1: exit={rc} {'OK' if ok4 else 'FAIL'}")
    print("")

    # ---- CHECK 5: each failing fixture emits EXACTLY one discrepancy label.
    print("CHECK 5 — each failing fixture emits exactly one discrepancy label")
    failing = [f[:-5] for f in fixtures if oracle.get(f[:-5], {}).get("final") == "FAIL"]
    debug_overlap = []
    for fid in failing:
        path = os.path.join(FIXDIR, fid + ".json")
        rc, parsed, _ = run_grader(path, cwd=REPO)
        disc = parsed.get("discrepancy", "none")
        # single label means it's a known label, not 'none' and not ambiguous (we assert one string)
        single = isinstance(disc, str) and disc != "none" and disc != "ambiguous"
        record("check5 single-label", single, f"{fid}: disc={disc!r}")
        if not single:
            debug_overlap.append(fid)
        print(f"  {fid}: disc={disc} {'OK' if single else 'FAIL'}")
    print("")

    # ---- CHECK 6: two grader processes concurrently -> isolated outputs.
    print("CHECK 6 — concurrent grader processes stay isolated")
    conc_pairs = [("E4-M1.json", "hypothesis-omitted"), ("E7-M6.json", "constant-injection")]
    isolated = True
    def one(fn):
        path = os.path.join(FIXDIR, fn)
        rc, parsed, raw = run_grader(path, cwd=REPO)
        return fn, rc, parsed
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futs = [ex.submit(one, fn) for fn, _ in conc_pairs]
        results = [fut.result() for fut in futs]
    got = dict((fn, (rc, parsed)) for fn, rc, parsed in results)
    for fn, want_disc in conc_pairs:
        rc, parsed = got[fn]
        if parsed.get("discrepancy") != want_disc:
            isolated = False
    record("check6 concurrent-isolation", isolated,
           ";" .join(f"{fn}:{got[fn][1].get('discrepancy')}" for fn, _ in conc_pairs))
    print(f"  isolated: {'OK' if isolated else 'FAIL'}")
    print("")

    # ---- CHECK 7: run from a working directory OUTSIDE the repository.
    print("CHECK 7 — run from a working directory outside the repository")
    extcwd = os.path.join(os.path.dirname(REPO), "grader_selftest_outside")  # /home/user/grader_selftest_outside
    os.makedirs(extcwd, exist_ok=True)
    src = os.path.join(FIXDIR, "PASS-E4.json")
    rc, parsed, _ = run_grader(src, cwd=extcwd)
    ok7 = (rc == 0) and (parsed.get("final") == "PASS")
    record("check7 foreign-cwd", ok7, f"exit={rc} final={parsed.get('final')} cwd={extcwd}")
    print(f"  cwd={extcwd}: exit={rc} final={parsed.get('final')} {'OK' if ok7 else 'FAIL'}")
    print("")

    # ---- summary
    print("=" * 78)
    print("SUMMARY")
    print(f"  fixtures/checks run     : {summary['fixtures_run']}")
    print(f"  ok                      : {summary['ok']}")
    print(f"  fail                    : {summary['fail']}")
    if failures:
        print("  FAILURES:")
        for label, detail in failures:
            print(f"    - {label}: {detail}")
    print("=" * 78)
    return 0 if summary["fail"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
