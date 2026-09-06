#!/usr/bin/env bash
# tools/suite_collect.sh — assemble a baseline EVIDENCE report from completed
# shard attempts. INT-SUPPORT host tooling; the collector decides nothing.
#
# Usage:
#   tools/suite_collect.sh [--out <evidence-file>] <attempt-dir>...
# An attempt dir is logs/suite-attempts/<run-id>/shard-<n> (as produced by
# tools/suite_attempt.sh).
#
# Refusals (specific external-tool errors, exit 3, NO evidence file):
#   E_MISSING_META / E_NO_COMPLETION   interrupted or metadata-less attempt
#   E_CHILD_EXIT_NONZERO               child terminated abnormally
#   E_DIGEST_MISMATCH                  raw log altered after completion
#   E_REPORT_TRUNCATED                 no final report block in raw log
#   E_ABORT_IN_REPORT                  child crashed mid-run
#   E_COMMIT_MISMATCH / E_TREE_MISMATCH / E_PYVERS_MISMATCH /
#   E_SHARD_COUNT_MISMATCH             incompatible attempts
#   E_SHARD_SET_INCOMPLETE             indices do not cover 0..count-1
#
# On success the evidence file contains, per shard: completion status, exit,
# raw-log digest, report-completeness, the FULL final report text, and every
# failed-test name (no head/tail window). Summary states failures and marks
# the admission decision PENDING — only INT admits a baseline. Zero exit
# codes are never read as an all-green suite.
set -u

OUT=""
DIRS=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --out) OUT="${2:-}"; shift 2 ;;
    *)   DIRS+=("$1"); shift ;;
  esac
done
[ "${#DIRS[@]}" -ge 1 ] || { echo "suite_collect: need at least one attempt dir" >&2; exit 2; }

SUITE_COLLECT_OUT="$OUT" python3 - "${DIRS[@]}" <<'PYEOF'
import hashlib, json, os, re, sys
from datetime import datetime, timezone

err = lambda code, msg: (sys.stderr.write("suite_collect: %s: %s\n" % (code, msg)), sys.exit(3))

def kv(path):
    d = {}
    with open(path) as f:
        for line in f:
            line = line.rstrip("\n")
            if "=" in line:
                k, v = line.split("=", 1)
                d[k] = v
    return d

dirs = sys.argv[1:]
records = []
for d in dirs:
    meta_p = os.path.join(d, "meta.env")
    comp_p = os.path.join(d, "completion.json")
    sha_p = os.path.join(d, "completion.json.sha")
    raw_p = os.path.join(d, "raw.log")
    if not os.path.isfile(meta_p):
        err("E_MISSING_META", d)
    if not os.path.isfile(comp_p) or not os.path.isfile(sha_p):
        err("E_NO_COMPLETION", d + " (no completion record: interrupted evidence cannot become a baseline)")
    meta = kv(meta_p)
    with open(comp_p) as f:
        comp = json.load(f)
    if comp.get("child_exit_status") != 0:
        err("E_CHILD_EXIT_NONZERO", "%s exit=%s" % (d, comp.get("child_exit_status")))
    want = open(sha_p).read().split()[0]
    got = hashlib.sha256(open(raw_p, "rb").read()).hexdigest()
    if want != got:
        err("E_DIGEST_MISMATCH", "%s want=%s got=%s" % (d, want[:12], got[:12]))
    text = open(raw_p, errors="replace").read()
    idx = meta.get("SHARD_INDEX")
    m = None
    for m2 in re.finditer(r"(?m)^SHARD %s elapsed [0-9.]+\s*$" % re.escape(str(idx)), text):
        m = m2  # keep the LAST elapsed marker: an old marker + truncated rerun truncates to nothing
    if m is None:
        err("E_REPORT_TRUNCATED", "%s has no final report block" % d)
    report = text[m.end():].strip()
    if not report:
        err("E_REPORT_TRUNCATED", "%s elapsed marker is last line; report block missing" % d)
    if "Traceback (most recent call last)" in report:
        err("E_ABORT_IN_REPORT", "%s child crashed; abort is a finding, not a baseline" % d)
    records.append((meta, comp, report, d))

def same(field):
    vals = {r[0].get(field) for r in records}
    return len(vals) == 1, sorted(vals)

for code, field in (("E_COMMIT_MISMATCH", "TESTED_COMMIT"), ("E_TREE_MISMATCH", "TESTED_TREE"),
                    ("E_PYVERS_MISMATCH", "PYVERS"), ("E_SHARD_COUNT_MISMATCH", "SHARD_COUNT")):
    ok, vals = same(field)
    if not ok:
        err(code, "%s differs across attempts: %s" % (field, vals))

counts = {int(r[0]["SHARD_COUNT"]) for r in records}
count = counts.pop()
if len(records) != count and os.environ.get("SUITE_COLLECT_ALLOW_PARTIAL_SET") != "1":
    err("E_SHARD_SET_INCOMPLETE", "have %d shards, count=%d; partial runs are never stitched into a full-suite claim" % (len(records), count))
idxs = sorted(int(r[0]["SHARD_INDEX"]) for r in records)
if idxs != list(range(count)) and os.environ.get("SUITE_COLLECT_ALLOW_PARTIAL_SET") != "1":
    err("E_SHARD_SET_INCOMPLETE", "indices %s do not cover 0..%d" % (idxs, count - 1))

failed_total = 0
blocks = []
for meta, comp, report, d in records:
    if report == "All the tests have passed.":
        names = []
    else:
        names = [ln.strip() for ln in report.splitlines() if ln.strip() and not ln.startswith("SHARD")]
    failed_total += len(names)
    blocks.append(
        "==== attempt %s ====\n"
        "dir: %s\n"
        "run-id: %s\n"
        "tested-commit: %s\ntested-tree: %s\nworktree-dirty-at-launch: %s\n"
        "shard: %s of %s\n"
        "command: %s\ncwd: %s\nenv: %s | python %s | PYTHONPATH=%s\n"
        "started-utc: %s  finished-utc: %s  duration-s: %s\n"
        "process-completed: yes (completion record present)\n"
        "child-exit-status: %s\n"
        "suite-report-complete: yes (final report block present)\n"
        "raw-log-sha256: %s\n"
        "---- FULL final report ----\n%s\n"
        "---- failed-test names (%d) ----\n%s\n"
        % (meta.get("RUN_ID"), d, meta.get("RUN_ID"),
           meta.get("TESTED_COMMIT"), meta.get("TESTED_TREE"), meta.get("WORKTREE_DIRTY"),
           meta.get("SHARD_INDEX"), meta.get("SHARD_COUNT"),
           meta.get("COMMAND"), meta.get("CWD"), meta.get("PYVERS"),
           meta.get("PYEXEC"), meta.get("PYTHONPATH"),
           meta.get("STARTED_UTC"), comp.get("finished_utc"), comp.get("duration_seconds"),
           comp.get("child_exit_status"),
           open(os.path.join(d, "completion.json.sha")).read().split()[0],
           report, len(names), "\n".join(names) if names else "(none listed)")
    )

synthetic = any(r[0].get("TESTED_COMMIT") in ("", "unknown") or r[0].get("SYNTHETIC") == "yes" for r in records)
out = os.environ.get("SUITE_COLLECT_OUT") or ""
lines = []
lines.append("SUITE EVIDENCE REPORT — SYNTHETIC (fixture runs; not a machine-suite result)" if synthetic
             else "SUITE EVIDENCE REPORT")
lines.append("assembled-utc: %s" % datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
lines.append("collector: tools/suite_collect.sh")
lines.append("tested-commit: %s" % records[0][0].get("TESTED_COMMIT"))
lines.append("tested-tree: %s" % records[0][0].get("TESTED_TREE"))
lines.append("shards: %d of %s" % (len(records), count))
lines.append("process-completed: yes")
lines.append("suite-report-complete: yes")
lines.append("tests-failed: %s" % ("yes (%d names across shards)" % failed_total if failed_total else "none listed"))
lines.append("baseline-admission-decision: PENDING (INT decides; exit 0 means the collector was satisfied, nothing more)")
lines.append("")
lines.extend(blocks)
report_text = "\n".join(lines) + "\n"
if out:
    tmp = out + ".part"
    with open(tmp, "w") as f:
        f.write(report_text)
    os.replace(tmp, out)
print(report_text, end="")
sys.exit(0)
PYEOF
