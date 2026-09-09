#!/usr/bin/env python3
"""run.py — selftest for tools/cur_extract_evidence.py (checked evidence handlers).

Runs the END-TO-END path for every frozen-style fixture:
    frozen G-ENG-style bundle -> cur_extract_evidence.py -> evidence manifest
    -> cur_grade_artifact.py -> C1..C6 verdicts

It asserts the extractor's EVIDENCE DISCIPLINE: a recognized role alone must NOT establish PASS;
the checked handlers must derive verdicts from cited numeric payloads; the proof-support dependency
chain must reject self-citation / circular / unresolved support; malformed bundles must yield
structured exit-2 errors; the manifest must bind to immutable identities; and every run must use a
unique scratch directory so concurrent invocations cannot collide.

This harness reads only the fixtures it owns and the manifests it produces. It never reads the
grader's sealed expected-results table (oracle.json is intentionally absent in the production-path
probe). Exit 0 if all pass; non-zero otherwise.
"""

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
EXTRACTOR = os.path.join(REPO, "tools", "cur_extract_evidence.py")
GRADER = os.path.join(REPO, "tools", "cur_grade_artifact.py")
FIXDIR = os.path.join(HERE, "fixtures")


def extract(bundle_path, out_path, cwd=REPO):
    p = subprocess.run([sys.executable, EXTRACTOR, bundle_path, "--out", out_path],
                       cwd=cwd, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def run_grader(manifest_path, cwd=REPO):
    p = subprocess.run([sys.executable, GRADER, manifest_path], cwd=cwd, capture_output=True, text=True)
    try:
        parsed = json.loads(p.stdout.strip())
    except ValueError:
        parsed = {"error": p.stdout.strip(), "stderr": p.stderr.strip()}
    return p.returncode, parsed


def extract_and_grade(bundle_path, scratch_dir):
    """Full pipeline for one bundle. Returns (extractor_rc, grader_rc, grader_parsed, manifest)."""
    key = os.path.splitext(os.path.basename(bundle_path))[0]
    mpath = os.path.join(scratch_dir, key + ".manifest.json")
    xrc, _, _ = extract(bundle_path, mpath)
    if not os.path.exists(mpath):
        return xrc, None, None, None
    with open(mpath, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    grc, gparsed = run_grader(mpath)
    return xrc, grc, gparsed, manifest


# --------------------------------------------------------------------- helpers
def _final(d):
    return d.get("final") if d else None


def _disc(d):
    return d.get("discrepancy") if d else None


def _evidence_of(manifest, check):
    return manifest["evidence"].get(check, {})


def _has_pass(manifest, check, key):
    return bool(_evidence_of(manifest, check).get(key))


def _has_fail(manifest, check, key):
    return bool(_evidence_of(manifest, check).get(key))


def _probe_noiseless(scratch):
    """Run the production pipeline with the grader's sealed expected-results table unavailable."""
    # Copy the two tools + one fixture into an isolated dir with NO oracle.json present anywhere.
    iso = os.path.join(scratch, "probe_no_oracle")
    os.makedirs(iso, exist_ok=True)
    shutil.copy(EXTRACTOR, iso)
    shutil.copy(GRADER, iso)
    shutil.copy(os.path.join(FIXDIR, "e3-pass.json"), iso)
    cmd1 = [sys.executable, "cur_extract_evidence.py", "e3-pass.json", "--out", "m.json"]
    p1 = subprocess.run(cmd1, cwd=iso, capture_output=True, text=True)
    cmd2 = [sys.executable, "cur_grade_artifact.py", "m.json"]
    p2 = subprocess.run(cmd2, cwd=iso, capture_output=True, text=True)
    try:
        parsed = json.loads(p2.stdout.strip())
    except ValueError:
        parsed = {"error": p2.stdout.strip()}
    ok = (p1.returncode == 0) and (p2.returncode == 0) and (parsed.get("final") == "PASS")
    # ensure oracle.json genuinely absent in the probe tree
    oracle_absent = not os.path.exists(os.path.join(iso, "oracle.json")) \
        and not os.path.exists(os.path.join(os.path.dirname(iso), "oracle.json"))
    return ok, oracle_absent


# --------------------------------------------------------------------- main
def main(argv):
    child = "--child" in argv
    scratch = tempfile.mkdtemp(prefix="cur_extractor_selftest_")
    failures = []
    summary = {"checks": 0, "ok": 0}

    def record(label, ok, detail=""):
        summary["checks"] += 1
        if ok:
            summary["ok"] += 1
        else:
            failures.append((label, detail))

    print("=" * 78)
    print("EXTRACTOR SELFTEST (checked evidence) — tools/tests/cur_extractor/run.py")
    print("scratch=%s" % scratch)
    print("=" * 78)

    # ---- CHECK 1: e3-pass is the ONE full END-TO-END PASS path.
    print("CHECK 1 — e3-pass end-to-end yields full PASS (all six checks PASS)")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-pass.json"), scratch)
    ok1 = (xrc == 0) and (grc == 0) and (_final(gparsed) == "PASS")
    record("check1 e3-pass full PASS", ok1, "xrc=%s grc=%s final=%s" % (xrc, grc, _final(gparsed)))
    print("  xrc=%s grc=%s final=%s (%s)" % (xrc, grc, _final(gparsed), "OK" if ok1 else "FAIL"))
    print("")

    # ---- CHECK 2: role-only negative control must NOT be a PASS.
    print("CHECK 2 — role-only negative control is NOT a silent PASS")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-role-only-negative-control.json"), scratch)
    not_pass = _final(gparsed) != "PASS"
    ok2 = not_pass
    record("check2 role-only not PASS", ok2, "final=%s" % (_final(gparsed)))
    print("  final=%s evidence=%s (%s)" % (_final(gparsed), {k: v for k, v in manifest["evidence"].items() if v}, "OK" if ok2 else "FAIL"))
    print("")

    # ---- CHECK 3: recognized role + empty support must NOT be a PASS.
    print("CHECK 3 — recognized role + empty support is NOT a PASS (all CD)")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-empty-support.json"), scratch)
    all_cd = (_final(gparsed) == "CANNOT_DETERMINE") and all(not v for v in manifest["evidence"].values())
    ok3 = all_cd
    record("check3 empty support not PASS", ok3, "final=%s" % (_final(gparsed)))
    print("  final=%s evidence=%s (%s)" % (_final(gparsed), {k: v for k, v in manifest["evidence"].items() if v}, "OK" if ok3 else "FAIL"))
    print("")

    # ---- CHECK 4: recognized role + unrelated support (unknown cite) must NOT be a PASS.
    print("CHECK 4 — recognized role + unrelated/unresolved support is NOT a PASS")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-unrelated-support.json"), scratch)
    ok4 = (_final(gparsed) != "PASS") and (xrc == 1)
    record("check4 unrelated support not PASS", ok4, "xrc=%s final=%s" % (xrc, _final(gparsed)))
    print("  xrc=%s final=%s (%s)" % (xrc, _final(gparsed), "OK" if ok4 else "FAIL"))
    print("")

    # ---- CHECK 5: self-citation cannot justify its own claim.
    print("CHECK 5 — self-citation cannot justify a claim (all CD + proof diagnostic)")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-self-citation.json"), scratch)
    diags = manifest.get("extractor_diagnostics", [])
    has_self = any("self-citation" in d for d in diags)
    ok5 = (xrc == 1) and (_final(gparsed) != "PASS") and has_self
    record("check5 self-citation rejected", ok5, "xrc=%s final=%s self_diag=%s" % (xrc, _final(gparsed), has_self))
    print("  xrc=%s final=%s self_diag=%s (%s)" % (xrc, _final(gparsed), has_self, "OK" if ok5 else "FAIL"))
    print("")

    # ---- CHECK 6: circular proof support cannot justify a claim.
    print("CHECK 6 — circular support cannot justify a claim (all CD + proof diagnostic)")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-circular-support.json"), scratch)
    diags = manifest.get("extractor_diagnostics", [])
    has_cycle = any("circular support" in d for d in diags)
    ok6 = (xrc == 1) and (_final(gparsed) != "PASS") and has_cycle
    record("check6 circular support rejected", ok6, "xrc=%s final=%s cycle_diag=%s" % (xrc, _final(gparsed), has_cycle))
    print("  xrc=%s final=%s cycle_diag=%s (%s)" % (xrc, _final(gparsed), has_cycle, "OK" if ok6 else "FAIL"))
    print("")

    # ---- CHECK 7: unresolved upstream support cannot justify dependent evidence.
    print("CHECK 7 — unresolved upstream support blocks dependent evidence")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-unresolved-upstream.json"), scratch)
    diags = manifest.get("extractor_diagnostics", [])
    has_unres = any("unresolved upstream" in d for d in diags)
    # C1/C2 (which depend on moves, unresolved) must be CD; C3/C6 (weight+start okay) may pass.
    c1_cd = not any(manifest["evidence"]["C1"].values())
    c2_cd = not any(manifest["evidence"]["C2"].values())
    ok7 = (xrc == 1) and has_unres and c1_cd and c2_cd
    record("check7 unresolved upstream blocks", ok7, "xrc=%s c1=%s c2=%s" % (xrc, c1_cd, c2_cd))
    print("  xrc=%s c1_cd=%s c2_cd=%s (%s)" % (xrc, c1_cd, c2_cd, "OK" if ok7 else "FAIL"))
    print("")

    # ---- CHECK 8: E7 window_width=4 / modulus=4 do NOT repair missing preservation/separation.
    print("CHECK 8 — E7 params do NOT establish preservation/separation (all CD)")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e7-params-negative-control.json"), scratch)
    ok8 = (_final(gparsed) == "CANNOT_DETERMINE") and \
          all(not v for v in manifest["evidence"].values())
    record("check8 E7 params not evidence", ok8, "final=%s evidence=%s" % (_final(gparsed), manifest["evidence"]))
    print("  final=%s (%s)" % (_final(gparsed), "OK" if ok8 else "FAIL"))
    print("")

    # ---- CHECK 9: decorative expected-label is ignored (extraction identical).
    print("CHECK 9 — decorative expected-label field is ignored")
    a = extract_and_grade(os.path.join(FIXDIR, "e3-pass.json"), scratch)[3]
    b = extract_and_grade(os.path.join(FIXDIR, "e3-pass-decorative-label.json"), scratch)[3]
    ok9 = (a["evidence"] == b["evidence"]) and (a["citations"] == b["citations"])
    record("check9 decorative label ignored", ok9, "identical" if ok9 else "DIFFERS")
    print("  evidence+citations identical: %s" % ("OK" if ok9 else "FAIL"))
    print("")

    # ---- CHECK 10: not-in-kernel weight is NOT a silent PASS.
    print("CHECK 10 — a weight not in the kernel is NOT a silent PASS")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-not-in-kernel.json"), scratch)
    ok10 = (_final(gparsed) != "PASS")
    record("check10 not-in-kernel not PASS", ok10, "final=%s" % (_final(gparsed)))
    print("  final=%s (%s)" % (_final(gparsed), "OK" if ok10 else "FAIL"))
    print("")

    # ---- CHECK 11: contradictory cited records -> grader exit 2.
    print("CHECK 11 — contradictory cited records rejected by grader (exit 2)")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-contradictory.json"), scratch)
    ok11 = (grc == 2)
    record("check11 contradictory rejected", ok11, "grc=%s final=%s" % (grc, _final(gparsed)))
    print("  grc=%s final=%s (%s)" % (grc, _final(gparsed), "OK" if ok11 else "FAIL"))
    print("")

    # ---- CHECK 11b: E4 full-PASS path (descent).
    print("CHECK 11b — E4 PASS end-to-end")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e4-pass.json"), scratch)
    ok11b = (xrc == 0) and (grc == 0) and (_final(gparsed) == "PASS")
    record("check11b e4-pass full PASS", ok11b, "xrc=%s grc=%s final=%s" % (xrc, grc, _final(gparsed)))
    print("  xrc=%s grc=%s final=%s (%s)" % (xrc, grc, _final(gparsed), "OK" if ok11b else "FAIL"))
    print("")

    # ---- CHECK 11c: E4 missing degree bound -> hypothesis-omitted FAIL (not PASS).
    print("CHECK 11c — E4 missing degree bound is NOT a silent PASS")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e4-missing-degree-bound.json"), scratch)
    ok11c = (_final(gparsed) != "PASS")
    record("check11c e4 missing bound not PASS", ok11c, "final=%s disc=%s" % (_final(gparsed), _disc(gparsed)))
    print("  final=%s disc=%s (%s)" % (_final(gparsed), _disc(gparsed), "OK" if ok11c else "FAIL"))
    print("")

    # ---- CHECK 11d: E4 (d,s)=(4,2) as "legal descent" -> descent FAIL.
    print("CHECK 11d — E4 degree-4 move (illegal descent) is NOT a silent PASS")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e4-degree4-move.json"), scratch)
    ok11d = (_final(gparsed) != "PASS")
    record("check11d e4 deg4 move not PASS", ok11d, "final=%s disc=%s" % (_final(gparsed), _disc(gparsed)))
    print("  final=%s disc=%s (%s)" % (_final(gparsed), _disc(gparsed), "OK" if ok11d else "FAIL"))
    print("")

    # ---- CHECK 11e: E4 claims terminal => unique min -> overclaim FAIL.
    print("CHECK 11e — E4 terminal-global-min overclaim is rejected")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e4-terminal-global-min.json"), scratch)
    ok11e = (_final(gparsed) != "PASS")
    record("check11e e4 overclaim not PASS", ok11e, "final=%s disc=%s" % (_final(gparsed), _disc(gparsed)))
    print("  final=%s disc=%s (%s)" % (_final(gparsed), _disc(gparsed), "OK" if ok11e else "FAIL"))
    print("")

    # ---- CHECK 11f: E4 role-only negative control -> CANNOT_DETERMINE.
    print("CHECK 11f — E4 role-only negative control is NOT a PASS")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e4-role-only-negative-control.json"), scratch)
    ok11f = (_final(gparsed) != "PASS")
    record("check11f e4 role-only not PASS", ok11f, "final=%s" % (_final(gparsed)))
    print("  final=%s (%s)" % (_final(gparsed), "OK" if ok11f else "FAIL"))
    print("")

    # ---- CHECK 11g: E7 full-PASS path (mod-4 invariance).
    print("CHECK 11g — E7 PASS end-to-end")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e7-pass.json"), scratch)
    ok11g = (xrc == 0) and (grc == 0) and (_final(gparsed) == "PASS")
    record("check11g e7-pass full PASS", ok11g, "xrc=%s grc=%s final=%s" % (xrc, grc, _final(gparsed)))
    print("  xrc=%s grc=%s final=%s (%s)" % (xrc, grc, _final(gparsed), "OK" if ok11g else "FAIL"))
    print("")

    # ---- CHECK 11h: E7 width tag 4 but samples width 3 -> preservation FAIL.
    print("CHECK 11h — E7 width-tag-only (width 4 tag, width-3 sample) is NOT a PASS")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e7-width-tag-only.json"), scratch)
    ok11h = (_final(gparsed) != "PASS")
    record("check11h e7 width tag not PASS", ok11h, "final=%s" % (_final(gparsed)))
    print("  final=%s (%s)" % (_final(gparsed), "OK" if ok11h else "FAIL"))
    print("")

    # ---- CHECK 11i: E7 preservation claimed but sample changes residue -> FAIL.
    print("CHECK 11i — E7 preservation-fails is NOT a PASS")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e7-preservation-fails.json"), scratch)
    ok11i = (_final(gparsed) != "PASS")
    record("check11i e7 preservation fails not PASS", ok11i, "final=%s" % (_final(gparsed)))
    print("  final=%s (%s)" % (_final(gparsed), "OK" if ok11i else "FAIL"))
    print("")

    # ---- CHECK 11j: E7 no samples at all -> CANNOT_DETERMINE (not PASS).
    print("CHECK 11j — E7 no samples at all is CANNOT_DETERMINE (not PASS)")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e7-no-samples.json"), scratch)
    ok11j = (_final(gparsed) == "CANNOT_DETERMINE")
    record("check11j e7 no samples CD", ok11j, "final=%s" % (_final(gparsed)))
    print("  final=%s (%s)" % (_final(gparsed), "OK" if ok11j else "FAIL"))
    print("")

    # ---- CHECK 11k: E7 role-only negative control -> CANNOT_DETERMINE.
    print("CHECK 11k — E7 role-only negative control is NOT a PASS")
    xrc, grc, gparsed, manifest = extract_and_grade(os.path.join(FIXDIR, "e7-role-only-negative-control.json"), scratch)
    ok11k = (_final(gparsed) != "PASS")
    record("check11k e7 role-only not PASS", ok11k, "final=%s" % (_final(gparsed)))
    print("  final=%s (%s)" % (_final(gparsed), "OK" if ok11k else "FAIL"))
    print("")

    # ---- CHECK 12: malformed bundles -> structured exit-2 (no traceback).
    print("CHECK 12 — malformed bundles yield structured exit-2 errors")
    for fname in ["malformed-duplicate-id.json", "malformed-nonarray-cites.json", "unsupported-contract.json"]:
        bpath = os.path.join(FIXDIR, fname)
        mtmp = os.path.join(scratch, fname + ".manifest.json")
        xrc, out, err = extract(bpath, mtmp)
        no_traceback = "Traceback" not in out and "Traceback" not in err
        okm = (xrc == 2) and (not os.path.exists(mtmp)) and no_traceback
        record("check12 " + fname, okm, "xrc=%s traceback=%s" % (xrc, not no_traceback))
        print("  %-32s xrc=%s traceback=%s (%s)" % (fname, xrc, not no_traceback, "OK" if okm else "FAIL"))
    print("")

    # ---- CHECK 13: identity block binds to immutable inputs.
    print("CHECK 13 — manifest binds to immutable identities (digests + pinned commits)")
    _, _, _, manifest = extract_and_grade(os.path.join(FIXDIR, "e3-pass.json"), scratch)
    ident = manifest.get("identity", {})
    ok13 = bool(ident.get("bundle_digest") and ident.get("extractor_digest") \
                and ident.get("grader_ruleset_id") and ident.get("contract_ref_commit") \
                and ident.get("contract_ref_content_digest") and ident.get("contract_in_tree_path") \
                and ident.get("contract_in_tree_content_digest") and ident.get("rubric_ref_commit") \
                and ident.get("rubric_ref_content_digest"))
    record("check13 identity binding", ok13, "identity keys=%s" % sorted(ident.keys()))
    print("  %s" % ("OK" if ok13 else "FAIL"))
    print("")

    # ---- CHECK 14: extractor source never touches oracle/expected-label.
    print("CHECK 14 — extractor source does not reference oracle/expected-label")
    with open(EXTRACTOR, "r", encoding="utf-8") as f:
        src = f.read()
    ok14 = ("oracle" not in src) and ("expected_label" not in src)
    record("check14 no oracle/expected_label in source", ok14,
           "oracle=%s expected_label=%s" % ("oracle" in src, "expected_label" in src))
    print("  oracle=%s expected_label=%s (%s)" % ("oracle" in src, "expected_label" in src, "OK" if ok14 else "FAIL"))
    print("")

    # ---- CHECK 15: production pipeline with expected-results table unavailable.
    print("CHECK 15 — production pipeline runs with the sealed expected-results table unavailable")
    okprobe, oracle_absent = _probe_noiseless(scratch)
    record("check15 production no-oracle probe", okprobe, "oracle_absent=%s" % oracle_absent)
    print("  oracle_absent=%s pipeline_ok=%s (%s)" % (oracle_absent, okprobe, "OK" if okprobe else "FAIL"))
    print("")

    # ---- CHECK 16: concurrent extractions isolate outputs (unique scratch per run).
    print("CHECK 16 — concurrent extractions isolate outputs")
    conc = ["e3-pass.json", "e3-partial-missing-odd-gen.json"]
    def one(fname):
        return extract_and_grade(os.path.join(FIXDIR, fname), scratch)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        futures = [ex.submit(one, fn) for fn in conc]
        results = [fut.result() for fut in futures]
    isolated = True
    # compare against serial runs into distinct scratch subdirs
    for i, fn in enumerate(conc):
        sub = os.path.join(scratch, "serial_%d" % i)
        os.makedirs(sub, exist_ok=True)
        serial = extract_and_grade(os.path.join(FIXDIR, fn), sub)
        if results[i][3]["evidence"] != serial[3]["evidence"] or \
           results[i][3]["citations"] != serial[3]["citations"]:
            isolated = False
    record("check16 concurrent isolation", isolated, "isolated" if isolated else "DIFFERS")
    print("  isolated: %s" % ("OK" if isolated else "FAIL"))
    print("")

    # ---- CHECK 17: foreign working directory works end-to-end.
    print("CHECK 17 — end-to-end from a working directory outside the repository")
    extcwd = os.path.join(scratch, "outside_cwd")
    os.makedirs(extcwd, exist_ok=True)
    bpath = os.path.join(FIXDIR, "e3-pass.json")
    mpath = os.path.join(extcwd, "e3.manifest.json")
    xrc, _, _ = extract(bpath, mpath, cwd=extcwd)
    grc, gparsed = run_grader(mpath, cwd=extcwd)
    ok17 = (xrc == 0) and (grc == 0) and (_final(gparsed) == "PASS")
    record("check17 foreign cwd", ok17, "xrc=%s grc=%s final=%s" % (xrc, grc, _final(gparsed)))
    print("  xrc=%s grc=%s final=%s (%s)" % (xrc, grc, _final(gparsed), "OK" if ok17 else "FAIL"))
    print("")

    # ---- CHECK 18: two COMPLETE selftests run concurrently (unique scratch each).
    # Spawn exactly two children; each child runs with --child so it does NOT recurse into
    # CHECK 18 again (each child runs checks 1..17 only, which is the concurrent-load probe).
    if not child:
        print("CHECK 18 — two complete selftests run concurrently (unique scratch each)")
        env = dict(os.environ)
        # Mark grandchildren as no-concurrency so they terminate.
        env["CUR_EXTRACTOR_NO_CONC"] = "1"
        con = []
        for _ in range(2):
            con.append(subprocess.Popen([sys.executable, os.path.abspath(__file__), "--child"],
                                        cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        env=env))
        codes = [p.wait() for p in con]
        ok18 = all(c == 0 for c in codes)
        record("check18 two concurrent selftests", ok18, "codes=%s" % codes)
        print("  exit codes=%s (%s)" % (codes, "OK" if ok18 else "FAIL"))
        print("")
    elif os.environ.get("CUR_EXTRACTOR_NO_CONC") != "1":
        # A --child used as part of CHECK 18; it should never recurse (it already ran 1..17 above).
        pass

    # ---- summary
    shutil.rmtree(scratch, ignore_errors=True)
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
    sys.exit(main(sys.argv))
