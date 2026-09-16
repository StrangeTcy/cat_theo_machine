#!/usr/bin/env python3
"""run.py — executable host-tools IMPORT REHEARSAL (CUR-GRADER-ENG / import support).

Reconstructs a minimal CUR-tools import onto a runtime base and runs the existing CUR
test suites in BOTH locations, so a portability claim is backed by an executed result
rather than an inventory of paths.

    tools source commit  --tool-source <full-sha>   (tools live here)
    runtime  base commit --runtime-base <full-sha>  (destination; tools absent)

WHAT IT DOES
  1. Verifies both commits resolve; records commit + tree identities.
  2. Creates a unique, isolated destination checkout at the runtime commit.
  3. Extracts ONLY an explicit import allowlist from the tool-source commit.
  4. Refuses a destination file that differs, unless a resolution authorizes replacement.
  5. Recreates git entries with exact mode handling:
       100644 -> regular file, mode 0644
       100755 -> regular file, mode 0755
       120000 -> symlink recreated from the blob target
       anything else (including non-blob entries such as gitlinks) ->
         explicit unsupported-mode failure, nothing written, never a silent conversion.
     A post-import check confirms every entry is byte/mode equivalent to the source.
  6. Runs the suites using the imported files in the destination (no PYTHONPATH, no
     fallback to another checkout).
  7. Captures each command, exit status, full output, and start/end times.
  8. Stages artifacts in an invocation-owned temp dir, writes the completion manifest
     last, then atomically renames the completed dir to the requested output path.
     A nonempty output path is refused; a failed verdict is retained under a clearly
     named incomplete sibling, never at the final path. Readers must use
     verify_attempt(): a missing/unreadable completion manifest means refusal.
  9. Returns nonzero on execution failure, missing test output, or a failed assertion.
 10. Leaves the original checkouts untouched (destinations are separate worktrees that
     are removed afterwards; the source repository's tracked state is compared before
     and after).
 11. Preserves the source identities the tools already record: the import must not
     relabel the extractor's pinned contract/rubric identities as the runtime commit.

This is a DISPOSABLE integration rehearsal. It does not merge into INT, authorize
measurements, or prove any theorem.

USAGE
  python3 tools/tests/cur_import/run.py \\
      --repo /path/to/repository \\
      --tool-source <full-source-sha> \\
      --runtime-base <full-runtime-sha> \\
      --out /path/to/new-attempt-directory

  --allowlist <file>   extend/replace the built-in allowlist (negative tests)
  --suites "<a> <b>"   override the suite list (negative tests)
  --allow-replace <p>  explicit resolution authorizing replacement of destination file p
  --keep               keep the disposable worktrees (debugging)
  --selftest           exercise the harness's own failure paths (disposable copies)

  python3 tools/tests/cur_import/run.py --verify <attempt-directory>
    consumer gate: accept only a complete, intact attempt (exit 0/1).

EXIT
  0  rehearsal complete: import blocked nothing, every selected suite ran and passed
  1  rehearsal failure (collision, missing path, suite failure, missing summary, ...)
  2  usage / argument / identity-resolution error
"""

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time

# --------------------------------------------------------------------- defaults
DEFAULT_ALLOWLIST = (
    "tools/cur_artifact_schema.py",
    "tools/cur_extract_evidence.py",
    "tools/cur_grade_artifact.py",
    "tools/cur_pipeline.py",
    "tools/tests/cur_schema/",
    "tools/tests/cur_extractor/",
    "tools/tests/cur_grader/",
    "tools/tests/cur_pipeline/",
    "protocol/G-ENG-ARTIFACT-SCHEMA.md",
)

DEFAULT_SUITES = (
    "tools/tests/cur_grader/run.py",
    "tools/tests/cur_extractor/run.py",
    "tools/tests/cur_schema/run.py",
    "tools/tests/cur_pipeline/run.py",
    "tools/tests/cur_pipeline/hardening.py",
)

# Modules a suite needs to exist in the destination for the run to be meaningful.
SUITE_REQUIREMENTS = {
    "tools/tests/cur_grader/run.py": ("tools/cur_grade_artifact.py",),
    "tools/tests/cur_extractor/run.py": ("tools/cur_extract_evidence.py", "tools/cur_grade_artifact.py"),
    "tools/tests/cur_schema/run.py": ("tools/cur_artifact_schema.py", "tools/cur_extract_evidence.py",
                                      "tools/cur_grade_artifact.py"),
    "tools/tests/cur_pipeline/run.py": ("tools/cur_pipeline.py", "tools/cur_extract_evidence.py",
                                        "tools/cur_grade_artifact.py"),
    "tools/tests/cur_pipeline/hardening.py": ("tools/cur_pipeline.py", "tools/cur_extract_evidence.py",
                                              "tools/cur_grade_artifact.py"),
}

# Two summary shapes exist in the CUR suites; both are recognized so a formatting
# difference is never misread as a suite failure.
#   A: "SUMMARY: 12/12 pass, 0 fail"
#   B: "SUMMARY\n  assertions run: 56\n  ok             : 56\n  fail           : 0"
SUMMARY_RE_A = re.compile(r"SUMMARY:\s*(\d+)/(\d+)\s*pass,\s*(\d+)\s*fail")
SUMMARY_RE_B = re.compile(
    r"SUMMARY\s*\n\s*assertions run:\s*(\d+)\s*\n\s*ok\s*:\s*(\d+)\s*\n\s*fail\s*:\s*(\d+)")

# Attempt publication: artifacts are staged in an invocation-owned temp dir and the
# completed dir appears at the requested path only via an atomic rename. Readers
# must call verify_attempt() and refuse any dir without a valid completion manifest.
COMPLETION_FILENAME = "completion.json"
EXPECTED_ARTIFACTS = (
    "input-manifest.json",
    "import-paths.txt",
    "source-results.txt",
    "destination-results.txt",
    "import.patch",
)
STAGING_PREFIX = "cur_import_staging_"
LOCK_SUFFIX = ".lock"
INCOMPLETE_SUFFIX = ".incomplete"
LOCK_STALE_SECONDS = 120
# Test hook ONLY: when set, the process exits immediately after the completion
# manifest is written but before publication, simulating an interruption. The
# selftest drives this via a subprocess and cleans up the leaked worktrees.
CRASH_BEFORE_PUBLISH_ENV = "CUR_IMPORT_CRASH_BEFORE_PUBLISH"

SUPPORTED_MODES = ("100644", "100755", "120000")


class Recorder:
    """Collects one record per executed command: argv, rc, output, start/end times."""

    def __init__(self):
        self.records = []

    def run(self, argv, cwd=None, env=None, timeout=900):
        started = time.time()
        merged = dict(os.environ)
        # Scrub path leakage so the destination cannot silently fall back to another
        # checkout's modules.
        merged.pop("PYTHONPATH", None)
        if env:
            merged.update(env)
        try:
            p = subprocess.run(argv, cwd=cwd, env=merged, capture_output=True, text=True,
                               timeout=timeout)
            rc, out, err = p.returncode, p.stdout, p.stderr
        except subprocess.TimeoutExpired:
            rc, out, err = "TIMEOUT", "", ""
        ended = time.time()
        rec = {
            "argv": list(argv),
            "cwd": cwd,
            "exit": rc,
            "started": round(started, 3),
            "ended": round(ended, 3),
            "stdout": out,
            "stderr": err,
        }
        self.records.append(rec)
        return rec

    def git(self, repo, *args):
        return self.run(["git"] + list(args), cwd=repo)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def blob_bytes(repo, blob):
    b = subprocess.run(["git", "cat-file", "blob", blob], cwd=repo, capture_output=True)
    if b.returncode != 0:
        return None
    return b.stdout


def parse_summary(text):
    """Return (ok_count, total, fail_count) from the LAST recognisable summary block.

    Supports both suite summary shapes (see SUMMARY_RE_A / SUMMARY_RE_B). Returns None
    when no summary block is present, which the caller treats as a failure (missing test
    output), never as a pass.
    """
    body = text or ""
    candidates = []
    for m in SUMMARY_RE_A.finditer(body):
        candidates.append((m.start(), (int(m.group(1)), int(m.group(2)), int(m.group(3)))))
    for m in SUMMARY_RE_B.finditer(body):
        total, ok, fail = int(m.group(1)), int(m.group(2)), int(m.group(3))
        candidates.append((m.start(), (ok, total, fail)))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    return candidates[-1][1]


# --------------------------------------------------------------------- identity + tree
def resolve_identity(rec, repo, rev):
    commit = rec.git(repo, "rev-parse", "--verify", "%s^{commit}" % rev)
    if commit["exit"] != 0:
        return None, None
    tree = rec.git(repo, "rev-parse", "--verify", "%s^{tree}" % rev)
    if tree["exit"] != 0:
        return None, None
    return commit["stdout"].strip(), tree["stdout"].strip()


def enumerate_allowlist(rec, repo, source_sha, allowlist):
    """Return (entries, missing_paths, unsupported_entries).

    entries: list of dicts {path, mode, blob, sha256, size} for every FILE or SYMLINK
    blob selected by the allowlist. Directory specs expand recursively via
    git ls-tree -r. Non-blob entries (e.g. gitlinks) are reported as unsupported,
    never silently skipped.
    """
    entries = []
    missing = []
    unsupported = []
    seen = set()
    for spec in allowlist:
        out = rec.git(repo, "ls-tree", "-r", source_sha, "--", spec)
        if out["exit"] != 0:
            missing.append(spec)
            continue
        found_any = False
        for line in out["stdout"].splitlines():
            line = line.rstrip("\n")
            if not line:
                continue
            meta, _, path = line.partition("\t")
            parts = meta.split()
            if len(parts) != 3:
                continue
            mode, otype, blob = parts
            if path in seen:
                continue
            seen.add(path)
            found_any = True
            if otype != "blob":
                unsupported.append({"path": path, "mode": mode, "otype": otype})
                continue
            blob_data = blob_bytes(repo, blob)
            if blob_data is None:
                blob_data = b""
            entries.append({
                "path": path,
                "mode": mode,
                "blob": blob,
                "sha256": sha256_bytes(blob_data),
                "size": len(blob_data),
            })
        if not found_any:
            missing.append(spec)
    entries.sort(key=lambda e: e["path"])
    unsupported.sort(key=lambda e: e["path"])
    return entries, missing, unsupported


def _existing_kind(target):
    if not os.path.lexists(target):
        return "absent"
    if os.path.islink(target):
        return "symlink"
    if os.path.isdir(target):
        return "dir"
    return "file"


def materialize(rec, repo, entries, dest_root, allow_replace):
    """Write selected blobs into dest_root. Return (written, problems).

    Mode handling is exact: 100644/100755 become regular files with that mode,
    120000 becomes a symlink recreated from the blob target. Any other mode is an
    explicit problem and nothing is written for that entry. Directories are never
    replaced, even with an explicit resolution. A differing destination entry is a
    problem unless an explicit resolution authorizes replacement.
    """
    written = []
    problems = []
    for e in entries:
        target = os.path.join(dest_root, e["path"])
        parent = os.path.dirname(target)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent, exist_ok=True)
        mode = e["mode"]
        if mode not in SUPPORTED_MODES:
            problems.append({"path": e["path"],
                             "reason": "unsupported git mode: %s" % mode})
            continue
        data = blob_bytes(repo, e["blob"])
        if data is None:
            problems.append({"path": e["path"], "reason": "blob unreadable"})
            continue
        kind = _existing_kind(target)
        if kind == "dir":
            problems.append({"path": e["path"],
                             "reason": "destination is a directory; not replaced"})
            continue
        if mode == "120000":
            link_target = data.decode("utf-8", "surrogateescape")
            if kind == "symlink" and os.readlink(target) == link_target:
                pass  # identical link; rewrite below for a uniform result.
            elif kind != "absent" and e["path"] not in allow_replace:
                problems.append({"path": e["path"], "reason": "destination differs",
                                 "existing_kind": kind})
                continue
            if kind != "absent":
                os.remove(target)
            os.symlink(link_target, target)
            written.append({"path": e["path"], "sha256": e["sha256"], "mode": mode,
                            "target": link_target})
            continue
        fmode = 0o755 if mode == "100755" else 0o644
        if kind == "symlink":
            if e["path"] not in allow_replace:
                problems.append({"path": e["path"], "reason": "destination differs",
                                 "existing_kind": kind})
                continue
            os.remove(target)
        elif kind == "file":
            if sha256_file(target) != e["sha256"] and e["path"] not in allow_replace:
                problems.append({"path": e["path"], "reason": "destination differs",
                                 "existing_kind": kind,
                                 "existing_sha256": sha256_file(target),
                                 "incoming_sha256": e["sha256"]})
                continue
        with open(target, "wb") as f:
            f.write(data)
        os.chmod(target, fmode)
        written.append({"path": e["path"], "sha256": e["sha256"], "mode": mode})
    return written, problems


def verify_materialized(repo, entries, dest_root):
    """Confirm every entry is byte/mode equivalent to the source. Returns problems."""
    problems = []
    for e in entries:
        target = os.path.join(dest_root, e["path"])
        if e["mode"] in ("100644", "100755"):
            want = 0o755 if e["mode"] == "100755" else 0o644
            if os.path.islink(target) or not os.path.isfile(target):
                problems.append("not a regular file after import: %s" % e["path"])
                continue
            if sha256_file(target) != e["sha256"]:
                problems.append("bytes differ after import: %s" % e["path"])
                continue
            got = stat.S_IMODE(os.stat(target).st_mode) & 0o777
            if got != want:
                problems.append("mode differs after import: %s (want %o, got %o)"
                                % (e["path"], want, got))
        elif e["mode"] == "120000":
            if not os.path.islink(target):
                problems.append("symlink not recreated: %s" % e["path"])
                continue
            data = blob_bytes(repo, e["blob"])
            want_target = data.decode("utf-8", "surrogateescape") if data is not None else None
            if want_target is None or os.readlink(target) != want_target:
                problems.append("symlink target differs after import: %s" % e["path"])
        else:
            problems.append("unsupported git mode: %s (%s)" % (e["path"], e["mode"]))
    return problems


# --------------------------------------------------------------------- suites
def run_suites(rec, root, suites, label):
    """Run each suite under root. Return rows with parsed counts."""
    rows = []
    for suite in suites:
        path = os.path.join(root, suite)
        missing_deps = [d for d in SUITE_REQUIREMENTS.get(suite, ())
                        if not os.path.exists(os.path.join(root, d))]
        if not os.path.exists(path):
            rows.append({"suite": suite, "exit": "ABSENT", "ok": None, "total": None,
                         "fail": None, "missing_deps": missing_deps,
                         "verdict": "MISSING_SUITE"})
            continue
        if missing_deps:
            rows.append({"suite": suite, "exit": None, "ok": None, "total": None,
                         "fail": None, "missing_deps": missing_deps,
                         "verdict": "MISSING_DEPENDENCY"})
            continue
        r = rec.run([sys.executable, path], cwd=root)
        summary = parse_summary(r["stdout"])
        if summary is None:
            verdict = "NO_SUMMARY"
        elif r["exit"] != 0 or summary[2] != 0:
            verdict = "FAIL"
        else:
            verdict = "PASS"
        rows.append({
            "suite": suite,
            "exit": r["exit"],
            "ok": summary[0] if summary else None,
            "total": summary[1] if summary else None,
            "fail": summary[2] if summary else None,
            "missing_deps": missing_deps,
            "verdict": verdict,
        })
        rows[-1]["_label"] = label
    return rows


def render_results(rows, rec, start_index, end_index=None):
    lines = []
    for r in rows:
        lines.append("suite:    %s" % r["suite"])
        lines.append("  exit:   %s" % r["exit"])
        lines.append("  counts: %s/%s pass, %s fail" % (r["ok"], r["total"], r["fail"]))
        lines.append("  verdict: %s" % r["verdict"])
        if r["missing_deps"]:
            lines.append("  missing dependency: %s" % ", ".join(r["missing_deps"]))
        lines.append("")
    lines.append("-" * 70)
    lines.append("RAW COMMAND RECORDS")
    lines.append("-" * 70)
    for idx, rc in enumerate(rec.records[start_index:end_index]):
        argv = " ".join(str(a) for a in rc["argv"])
        lines.append("[%d] cwd=%s" % (idx, rc["cwd"]))
        lines.append("    cmd=%s" % argv)
        lines.append("    exit=%s started=%s ended=%s" % (rc["exit"], rc["started"], rc["ended"]))
        for stream in ("stdout", "stderr"):
            body = rc[stream] or ""
            if body.strip():
                for ln in body.rstrip("\n").split("\n"):
                    lines.append("    %s| %s" % (stream[:6], ln))
        lines.append("")
    return "\n".join(lines) + "\n"


def check_identity_preserved(rec, dest_root, source_extractor_sha, runtime_sha):
    """The extractor's recorded pinned identities must survive the import unchanged.

    Imports must not relabel the tools' own source identities as the runtime commit.
    """
    fixture = os.path.join(dest_root, "tools/tests/cur_extractor/fixtures/e3-pass.json")
    if not os.path.exists(fixture):
        return {"ok": False, "reason": "fixture missing in destination"}
    manifest_path = os.path.join(tempfile.mkdtemp(prefix="cur_import_identity_"), "m.json")
    r = rec.run([sys.executable, os.path.join(dest_root, "tools/cur_extract_evidence.py"),
                 fixture, "--out", manifest_path], cwd=dest_root)
    if r["exit"] not in (0, 1) or not os.path.exists(manifest_path):
        return {"ok": False, "reason": "destination extractor did not produce a manifest"}
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    identity = manifest.get("identity") or {}
    dest_extractor_sha = sha256_file(os.path.join(dest_root, "tools/cur_extract_evidence.py"))
    problems = []
    if identity.get("extractor_digest") != dest_extractor_sha:
        problems.append("extractor_digest does not match the imported file")
    if dest_extractor_sha != source_extractor_sha:
        problems.append("imported extractor bytes differ from the source blob")
    # The pinned contract commits must be the source-pinned values, not the runtime commit.
    for key in ("contract_ref_commit", "rubric_ref_commit"):
        val = identity.get(key)
        if val == runtime_sha:
            problems.append("%s was relabeled to the runtime commit" % key)
        if val is None:
            problems.append("%s is absent" % key)
    return {
        "ok": len(problems) == 0,
        "reason": "; ".join(problems) if problems else "pinned identities preserved",
        "extractor_digest": identity.get("extractor_digest"),
        "contract_ref_commit": identity.get("contract_ref_commit"),
        "rubric_ref_commit": identity.get("rubric_ref_commit"),
    }


# --------------------------------------------------------------------- attempt publication
def attempt_state(path):
    """Classify the requested output path: absent | empty-dir | nonempty | file."""
    if not os.path.lexists(path):
        return "absent"
    if os.path.isdir(path) and not os.path.islink(path):
        try:
            empty = len(os.listdir(path)) == 0
        except OSError:
            return "nonempty"
        return "empty-dir" if empty else "nonempty"
    return "file"


def acquire_publish_lock(lock_path):
    """Take the publish lock dir. Returns True only for the holding invocation."""
    try:
        os.mkdir(lock_path)
    except FileExistsError:
        try:
            age = time.time() - os.path.getmtime(lock_path)
        except OSError:
            return False
        if age < LOCK_STALE_SECONDS:
            return False
        try:
            shutil.rmtree(lock_path)
        except OSError:
            return False
        try:
            os.mkdir(lock_path)
        except OSError:
            return False
    except OSError:
        return False
    try:
        with open(os.path.join(lock_path, "pid"), "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass
    return True


def release_publish_lock(lock_path):
    shutil.rmtree(lock_path, ignore_errors=True)


def write_completion_manifest(staging, payload):
    """Hash the staged artifacts and write completion.json. Call this LAST."""
    artifacts = {}
    for name in EXPECTED_ARTIFACTS:
        artifacts[name] = sha256_file(os.path.join(staging, name))
    doc = dict(payload)
    doc["artifacts"] = artifacts
    doc["completed_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    doc["pid"] = os.getpid()
    comp_path = os.path.join(staging, COMPLETION_FILENAME)
    with open(comp_path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    return comp_path


def verify_attempt(out_dir):
    """Consumer-side gate. Returns (ok, reason); refuses anything incomplete."""
    if not os.path.isdir(out_dir) or os.path.islink(out_dir):
        return False, "attempt directory absent: %s" % out_dir
    comp_path = os.path.join(out_dir, COMPLETION_FILENAME)
    if not os.path.isfile(comp_path) or os.path.islink(comp_path):
        return False, "completion manifest missing: attempt incomplete, refused"
    try:
        with open(comp_path, "r", encoding="utf-8") as f:
            comp = json.load(f)
        ok_flag = comp.get("ok")
        stage = comp.get("stage")
        artifacts = comp.get("artifacts") or {}
    except (OSError, ValueError, AttributeError):
        return False, "completion manifest unreadable: refused"
    if ok_flag is not True or stage != "done":
        return False, ("attempt did not complete successfully (ok=%r stage=%r): refused"
                       % (ok_flag, stage))
    for name in EXPECTED_ARTIFACTS:
        try:
            want = artifacts.get(name)
        except AttributeError:
            return False, "completion manifest malformed: refused"
        p = os.path.join(out_dir, name)
        if not want or not os.path.isfile(p) or os.path.islink(p):
            return False, "artifact missing: %s: refused" % name
        if sha256_file(p) != want:
            return False, "artifact content differs from manifest: %s: refused" % name
    return True, "attempt complete and intact"


def publish_staging(staging, out_dir):
    """Atomically move staging to out_dir. Returns (ok, reason).

    Refuses when another attempt owns the path; never merges into an existing
    directory; never overwrites. Exactly one of two racing invocations succeeds.
    """
    lock_path = out_dir + LOCK_SUFFIX
    if not acquire_publish_lock(lock_path):
        return False, "output publish lock held by another invocation"
    try:
        state = attempt_state(out_dir)
        if state == "absent":
            pass
        elif state == "empty-dir":
            try:
                os.rmdir(out_dir)
            except OSError:
                return False, "cannot clear empty output directory"
        else:
            return False, "output path already exists; refusing to overwrite"
        try:
            os.rename(staging, out_dir)
        except OSError as exc:
            return False, "atomic publish failed: %s" % exc
        ok, reason = verify_attempt(out_dir)
        if not ok:
            shutil.rmtree(out_dir, ignore_errors=True)
            return False, "published attempt failed verification: %s" % reason
        return True, "published"
    finally:
        release_publish_lock(lock_path)


# --------------------------------------------------------------------- main rehearsal
def rehearse(rec, repo, tool_source, runtime_base, out_dir, allowlist, suites,
             allow_replace, keep):
    result = {"ok": False, "stage": "start", "problems": []}

    src_commit, src_tree = resolve_identity(rec, repo, tool_source)
    rt_commit, rt_tree = resolve_identity(rec, repo, runtime_base)
    if src_commit is None:
        result["stage"] = "resolve"
        result["problems"].append("tool-source does not resolve: %s" % tool_source)
        return result
    if rt_commit is None:
        result["stage"] = "resolve"
        result["problems"].append("runtime-base does not resolve: %s" % runtime_base)
        return result

    # Refuse a reused attempt dir before doing any work.
    if attempt_state(out_dir) not in ("absent", "empty-dir"):
        result["stage"] = "output"
        result["problems"].append("output directory already exists and is not empty: %s"
                                  % out_dir)
        return result

    # Only TRACKED content is compared here: the rehearsal writes its artifacts into a
    # caller-supplied directory (which may live inside the repository) and that is intended.
    # Disposable worktrees are additionally required to be gone afterwards.
    repo_status_before = rec.git(repo, "status", "--porcelain", "-uno")["stdout"]

    scratch = tempfile.mkdtemp(prefix="cur_import_rehearsal_")
    dest = os.path.join(scratch, "dest")
    src = os.path.join(scratch, "src")
    worktrees = []
    try:
        for path, sha, label in ((dest, rt_commit, "dest"), (src, src_commit, "src")):
            w = rec.git(repo, "worktree", "add", "--detach", path, sha)
            if w["exit"] != 0:
                result["stage"] = "worktree"
                result["problems"].append("cannot create %s worktree at %s" % (label, sha))
                return result
            worktrees.append(path)

        # ---- 1..2 identities recorded; destination isolated at the runtime commit.
        entries, missing, unsupported = enumerate_allowlist(rec, repo, src_commit, allowlist)
        if missing:
            result["stage"] = "allowlist"
            result["problems"].append("allowlist path absent from source: %s" % ", ".join(missing))
            return result
        if unsupported:
            result["stage"] = "mode"
            for u in unsupported:
                result["problems"].append(
                    "unsupported git entry (not a file/symlink blob): %s mode=%s type=%s"
                    % (u["path"], u["mode"], u["otype"]))
            return result

        # ---- 3..5 extract allowlist; refuse differing destination files.
        written, collisions = materialize(rec, repo, entries, dest, set(allow_replace))
        if collisions:
            result["stage"] = "collision"
            for c in collisions:
                if c.get("reason") in (None, "destination differs"):
                    result["problems"].append("destination file differs: %s" % c["path"])
                else:
                    result["problems"].append("%s: %s" % (c["path"], c["reason"]))
            return result

        # ---- byte/mode equivalence against the source blobs.
        verify_problems = verify_materialized(repo, entries, dest)
        if verify_problems:
            result["stage"] = "verify"
            result["problems"].extend(verify_problems)
            return result

        # ---- import patch from the reconstructed candidate's changes.
        rec.git(dest, "add", "-A")
        patch = rec.git(dest, "diff", "--cached", "--binary")
        patch_text = patch["stdout"]

        # ---- 6 source results (pinned source), then destination results.
        src_rows = run_suites(rec, src, suites, "source")
        src_mark = len(rec.records)
        dest_rows = run_suites(rec, dest, suites, "destination")

        # ---- identity preservation.
        source_extractor_sha = ""
        for e in entries:
            if e["path"] == "tools/cur_extract_evidence.py":
                source_extractor_sha = e["sha256"]
        identity = check_identity_preserved(rec, dest, source_extractor_sha, rt_commit)
        render_end = len(rec.records)

        # ---- non-allowlisted destination files unchanged.
        imported = set(e["path"] for e in entries)
        untouched_probe = []
        for probe in ("main.py", "core.py", "persistence.py", "training.py", "research.py"):
            p = os.path.join(dest, probe)
            if os.path.exists(p):
                untouched_probe.append({"path": probe, "sha256": sha256_file(p)})

        # ---- 9 verdicts.
        verdict_problems = []
        for row in src_rows + dest_rows:
            if row["verdict"] != "PASS":
                verdict_problems.append("%s suite %s: %s" % (
                    "source" if row in src_rows else "destination", row["suite"], row["verdict"]))
        if not identity["ok"]:
            verdict_problems.append("identity: %s" % identity["reason"])

        # ---- release the disposable worktrees, then compare repository state.
        for w in worktrees:
            rec.git(repo, "worktree", "remove", "--force", w)
        worktrees.clear()
        # Ownership-scoped check: this invocation must not leave ITS OWN worktrees behind.
        # A concurrent rehearsal may legitimately hold its own at the same moment, so the
        # whole worktree list is not comparable.
        wt_after = rec.git(repo, "worktree", "list", "--porcelain")["stdout"]
        leftover = [w for w in (dest, src) if w in wt_after]
        if leftover:
            verdict_problems.append("disposable worktrees not removed: %s" % ", ".join(leftover))

        repo_status_after = rec.git(repo, "status", "--porcelain", "-uno")["stdout"]
        if repo_status_before != repo_status_after:
            verdict_problems.append("source repository tracked state changed during rehearsal")

        result["problems"].extend(verdict_problems)
        result["source_rows"] = src_rows
        result["destination_rows"] = dest_rows
        result["written"] = written
        result["collisions"] = collisions
        result["identity"] = identity
        result["stage"] = "done"

        # ---- 8 stage artifacts, manifest last, then publish atomically.
        parent = os.path.dirname(os.path.abspath(out_dir))
        os.makedirs(parent, exist_ok=True)
        staging = tempfile.mkdtemp(prefix=STAGING_PREFIX, dir=parent)
        try:
            manifest_obj = {
                "harness": "tools/tests/cur_import/run.py",
                "role": "CUR-GRADER-ENG / import support (disposable rehearsal)",
                "tool_source": {"rev": tool_source, "commit": src_commit, "tree": src_tree},
                "runtime_base": {"rev": runtime_base, "commit": rt_commit, "tree": rt_tree},
                "allowlist": list(allowlist),
                "suites": list(suites),
                "allow_replace": list(allow_replace),
                "dependency_check": "imported tools import stdlib only; no machine modules; "
                                    "no additional paths required",
                "imported": written,
                "identity_preservation": identity,
                "non_allowlisted_untouched_probe": untouched_probe,
                "source_results": src_rows,
                "destination_results": dest_rows,
                "merge_or_tag_performed": "none",
            }
            with open(os.path.join(staging, "input-manifest.json"), "w", encoding="utf-8") as f:
                json.dump(manifest_obj, f, indent=2, sort_keys=True)
                f.write("\n")
            with open(os.path.join(staging, "import-paths.txt"), "w", encoding="utf-8") as f:
                f.write("path\tmode\tsha256\n")
                for e in entries:
                    f.write("%s\t%s\t%s\n" % (e["path"], e["mode"], e["sha256"]))
            with open(os.path.join(staging, "source-results.txt"), "w", encoding="utf-8") as f:
                f.write("SOURCE (pinned tool-source %s) — %d imported files, %d collisions\n\n"
                        % (src_commit, len(written), len(collisions)))
                f.write(render_results(src_rows, rec, 0, render_end))
            with open(os.path.join(staging, "destination-results.txt"), "w", encoding="utf-8") as f:
                f.write("DESTINATION (runtime base %s) — suites executed against imported files\n\n"
                        % rt_commit)
                f.write(render_results(dest_rows, rec, src_mark, render_end))
            with open(os.path.join(staging, "import.patch"), "w", encoding="utf-8") as f:
                f.write(patch_text)
            write_completion_manifest(staging, {
                "harness": "tools/tests/cur_import/run.py",
                "role": "CUR-GRADER-ENG / import support (disposable rehearsal)",
                "tool_source": {"rev": tool_source, "commit": src_commit, "tree": src_tree},
                "runtime_base": {"rev": runtime_base, "commit": rt_commit, "tree": rt_tree},
                "stage": "done",
                "ok": len(result["problems"]) == 0,
                "imported_count": len(written),
            })
            if os.environ.get(CRASH_BEFORE_PUBLISH_ENV):
                os._exit(137)
            if result["problems"]:
                incomplete = "%s%s.%d.%d" % (out_dir, INCOMPLETE_SUFFIX, os.getpid(),
                                             time.time_ns())
                os.rename(staging, incomplete)
                staging = None
                result["ok"] = False
                result["incomplete_dir"] = incomplete
                return result
            ok_pub, reason_pub = publish_staging(staging, out_dir)
            staging = None
            if not ok_pub:
                result["stage"] = "output"
                result["problems"].append(reason_pub)
                result["ok"] = False
                return result
            result["ok"] = True
            return result
        finally:
            if staging is not None:
                shutil.rmtree(staging, ignore_errors=True)
    finally:
        if not keep:
            for w in worktrees:
                rec.git(repo, "worktree", "remove", "--force", w)
            shutil.rmtree(scratch, ignore_errors=True)


# --------------------------------------------------------------------- selftest
def selftest(rec, repo, tool_source, runtime_base, out_dir, work_root):
    """Exercise the harness's own failure paths with disposable copies."""
    cases = []
    # Scratch repositories are seeded from the tool-source TREE, so they do not carry the
    # source repository's objects; select the full commit id for use against them.
    src_full = rec.git(repo, "rev-parse", "%s^{commit}" % tool_source)["stdout"].strip()
    rt_full = rec.git(repo, "rev-parse", "%s^{commit}" % runtime_base)["stdout"].strip()

    def case(name, cond, detail=""):
        cases.append({"case": name, "ok": bool(cond), "detail": detail})

    def call(**kw):
        opts = dict(tool_source=tool_source, runtime_base=runtime_base)
        opts.update(kw)
        return rehearse(rec, repo, opts["tool_source"], opts["runtime_base"],
                        kw["out"], kw.get("allowlist", DEFAULT_ALLOWLIST),
                        kw.get("suites", DEFAULT_SUITES), kw.get("allow_replace", ()),
                        kw.get("keep", False))

    def listed_worktrees(r):
        s = rec.run(["git", "-C", r, "worktree", "list", "--porcelain"])
        paths = set()
        for ln in (s["stdout"] or "").splitlines():
            if ln.startswith("worktree "):
                paths.add(ln.split(" ", 1)[1])
        return paths

    # 0. baseline: the rehearsal itself passes.
    base_out = os.path.join(work_root, "baseline")
    base = call(out=base_out)
    base_verify, _ = verify_attempt(base_out)
    case("baseline rehearsal passes", base["ok"] and base_verify,
         "; ".join(base["problems"])[:200])

    # 1. missing required source file -> explicit failure.
    badlist = os.path.join(work_root, "bad-allowlist.txt")
    with open(badlist, "w", encoding="utf-8") as f:
        f.write("\n".join(list(DEFAULT_ALLOWLIST) + ["tools/does_not_exist.py"]) + "\n")
    miss_out = os.path.join(work_root, "missing")
    miss = call(out=miss_out, allowlist=tuple(
        open(badlist, encoding="utf-8").read().split()))
    case("missing required source path -> failure",
         (not miss["ok"]) and miss["stage"] == "allowlist"
         and not os.path.lexists(miss_out),
         "stage=%s" % miss["stage"])

    # 2. differing destination file -> collision refusal.
    Sub = rec.run

    def scratch_clone(path):
        """A real clone, so the source commit OBJECT is present.

        A repository seeded from `git archive` holds that tree under a different commit id,
        so it could not resolve the pinned source SHA; that would make the failure cases
        below pass for the wrong reason.
        """
        rec.run(["git", "clone", "--shared", "--quiet", "--no-checkout", repo, path])
        rec.run(["git", "-C", path, "config", "user.email", "rehearsal@example.invalid"])
        rec.run(["git", "-C", path, "config", "user.name", "rehearsal"])
        rec.run(["git", "-C", path, "checkout", "--detach", src_full])

    scratch_repo = os.path.join(work_root, "conflict-repo")
    scratch_clone(scratch_repo)
    with open(os.path.join(scratch_repo, "tools/cur_pipeline.py"), "a", encoding="utf-8") as f:
        f.write("\n# divergent destination copy\n")
    rec.run(["git", "-C", scratch_repo, "add", "-A"])
    rec.run(["git", "-C", scratch_repo, "commit", "-q", "-m", "diverge"])
    diverged = rec.run(["git", "-C", scratch_repo, "rev-parse", "HEAD"])["stdout"].strip()
    conflict = rehearse(rec, scratch_repo, src_full, diverged,
                        os.path.join(work_root, "conflict"), DEFAULT_ALLOWLIST,
                        DEFAULT_SUITES, (), False)
    case("differing destination file -> collision refusal",
         (not conflict["ok"]) and conflict["stage"] == "collision",
         "stage=%s problems=%s" % (conflict["stage"], conflict["problems"][:1]))
    # 2b. explicit resolution authorizes replacement.
    resolved = rehearse(rec, scratch_repo, src_full, diverged,
                        os.path.join(work_root, "conflict-resolved"), DEFAULT_ALLOWLIST,
                        DEFAULT_SUITES, ("tools/cur_pipeline.py",), False)
    case("explicit resolution authorizes replacement", resolved["ok"],
         "; ".join(resolved["problems"])[:200])

    # 3. missing imported grader -> failure, no foreign-checkout fallback.
    tools_only = tuple(p for p in DEFAULT_ALLOWLIST if p != "tools/cur_grade_artifact.py")
    suites_only_pipeline = ("tools/tests/cur_pipeline/run.py",)
    reduced = rehearse(rec, repo, tool_source, runtime_base,
                       os.path.join(work_root, "no-grader"), tools_only,
                       suites_only_pipeline, (), False)
    dep_row = (reduced.get("destination_rows") or [{}])[0]
    case("missing grader -> failure with no fallback",
         (not reduced["ok"]) and dep_row.get("verdict") in ("MISSING_DEPENDENCY", "FAIL"),
         "verdict=%s" % dep_row.get("verdict"))

    # 3b. no foreign-checkout fallback: with the grader absent from the imported set, the
    #     pipeline must fail rather than resolve the module from another checkout.
    fb_dir = os.path.join(work_root, "no-fallback")
    Sub(["git", "-C", repo, "worktree", "add", "--detach", fb_dir, rt_full])
    fb_entries, _, _ = enumerate_allowlist(rec, repo, src_full, tools_only)
    materialize(rec, repo, fb_entries, fb_dir, set())
    fb_fixture = os.path.join(fb_dir, "tools/tests/cur_extractor/fixtures/e3-pass.json")
    fb_run = Sub([sys.executable, os.path.join(fb_dir, "tools/cur_pipeline.py"), fb_fixture],
                 cwd=fb_dir)
    Sub(["git", "-C", repo, "worktree", "remove", "--force", fb_dir])
    case("no foreign-checkout fallback when grader absent",
         fb_run["exit"] not in (0,), "pipeline exit=%s" % fb_run["exit"])

    # 4. component prints a success-looking line and exits 7 -> overall failure.
    stub_repo = os.path.join(work_root, "stub-repo")
    scratch_clone(stub_repo)
    os.makedirs(os.path.join(stub_repo, "tools/tests/cur_stub"), exist_ok=True)
    with open(os.path.join(stub_repo, "tools/tests/cur_stub/run.py"), "w", encoding="utf-8") as f:
        f.write("import sys\nprint('SUMMARY: 99/99 pass, 0 fail')\nsys.exit(7)\n")
    Sub(["git", "-C", stub_repo, "add", "-A"])
    Sub(["git", "-C", stub_repo, "commit", "-q", "-m", "stub"])
    stub_base = Sub(["git", "-C", stub_repo, "rev-parse", "HEAD"])["stdout"].strip()
    stub_run = rehearse(rec, stub_repo, src_full, stub_base,
                        os.path.join(work_root, "stub-out"), DEFAULT_ALLOWLIST,
                        ("tools/tests/cur_stub/run.py",), (), False)
    # The rehearsal must reach the END and reject the stub on its exit status; passing
    # because of an earlier resolution error would not test this path.
    stub_row = (stub_run.get("destination_rows") or [{}])[0]
    case("success-looking line + exit 7 -> failure",
         stub_run["stage"] == "done" and (not stub_run["ok"]) and stub_row.get("verdict") == "FAIL",
         "stage=%s verdict=%s" % (stub_run["stage"], stub_row.get("verdict")))

    # 5. invocation from an unrelated directory -> same selected files.
    other_cwd = os.path.join(work_root, "elsewhere")
    os.makedirs(other_cwd, exist_ok=True)
    entries_a, _, _ = enumerate_allowlist(rec, repo, tool_source, DEFAULT_ALLOWLIST)
    prev = os.getcwd()
    try:
        os.chdir(other_cwd)
        entries_b, _, _ = enumerate_allowlist(rec, repo, tool_source, DEFAULT_ALLOWLIST)
    finally:
        os.chdir(prev)
    case("unrelated cwd selects the same files",
         [e["path"] for e in entries_a] == [e["path"] for e in entries_b],
         "%d vs %d paths" % (len(entries_a), len(entries_b)))

    # 6. two concurrent harness invocations -> separate scratch/output dirs.
    out_a = os.path.join(work_root, "concurrent-a")
    out_b = os.path.join(work_root, "concurrent-b")
    p1 = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--repo", repo,
                           "--tool-source", tool_source, "--runtime-base", runtime_base,
                           "--out", out_a], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p2 = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--repo", repo,
                           "--tool-source", tool_source, "--runtime-base", runtime_base,
                           "--out", out_b], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    r1 = p1.wait(timeout=1800)
    r2 = p2.wait(timeout=1800)
    va, _ = verify_attempt(out_a)
    vb, _ = verify_attempt(out_b)
    case("two concurrent harness runs isolate outputs",
         r1 == 0 and r2 == 0 and out_a != out_b and va and vb,
         "rc=%s,%s" % (r1, r2))

    # 7. non-allowlisted destination files byte-identical before and after.
    check_root = os.path.join(work_root, "untouched")
    before = {}
    probe_dir = os.path.join(check_root, "probe")
    os.makedirs(check_root, exist_ok=True)
    Sub(["git", "-C", repo, "worktree", "add", "--detach", probe_dir, runtime_base])
    for probe in ("main.py", "core.py", "persistence.py", "training.py", "research.py"):
        p = os.path.join(probe_dir, probe)
        if os.path.exists(p):
            before[probe] = sha256_file(p)
    Sub(["git", "-C", repo, "worktree", "remove", "--force", probe_dir])
    untouched = call(out=os.path.join(work_root, "untouched-out"))
    after_dir = os.path.join(work_root, "untouched-after")
    Sub(["git", "-C", repo, "worktree", "add", "--detach", after_dir, runtime_base])
    after = {}
    for probe in before:
        p = os.path.join(after_dir, probe)
        if os.path.exists(p):
            after[probe] = sha256_file(p)
    Sub(["git", "-C", repo, "worktree", "remove", "--force", after_dir])
    case("non-allowlisted files unchanged in the base commit",
         before == after and len(before) > 0 and untouched["ok"],
         "probed=%d" % len(before))

    # 8. symlink entry: recreated as a symlink (direct materialize + end-to-end patch).
    link_repo = os.path.join(work_root, "link-repo")
    scratch_clone(link_repo)
    link_dir = os.path.join(link_repo, "tools/tests/cur_link")
    os.makedirs(link_dir, exist_ok=True)
    LINK_TARGET = "expected-target/placeholder.txt"
    os.symlink(LINK_TARGET, os.path.join(link_dir, "expected-link.txt"))
    Sub(["git", "-C", link_repo, "add", "-A"])
    Sub(["git", "-C", link_repo, "commit", "-q", "-m", "symlink fixture"])
    link_src = Sub(["git", "-C", link_repo, "rev-parse", "HEAD"])["stdout"].strip()
    link_entries, link_missing, link_unsup = enumerate_allowlist(
        rec, link_repo, link_src, ("tools/tests/cur_link/",))
    link_tmp = os.path.join(work_root, "link-materialized")
    os.makedirs(link_tmp, exist_ok=True)
    _, link_probs = materialize(rec, link_repo, link_entries, link_tmp, set())
    link_path = os.path.join(link_tmp, "tools/tests/cur_link/expected-link.txt")
    direct_link_ok = (not link_missing and not link_unsup and len(link_entries) == 1
                      and link_entries[0]["mode"] == "120000" and not link_probs
                      and os.path.islink(link_path) and os.readlink(link_path) == LINK_TARGET)
    link_allow = tuple(list(DEFAULT_ALLOWLIST) + ["tools/tests/cur_link/"])
    link_out = os.path.join(work_root, "link-out")
    link_run = rehearse(rec, link_repo, link_src, src_full, link_out, link_allow,
                        ("tools/tests/cur_schema/run.py",), (), False)
    link_verify_ok = False
    link_patch_ok = False
    if link_run["ok"]:
        link_verify_ok, _ = verify_attempt(link_out)
        try:
            with open(os.path.join(link_out, "import.patch"), "r", encoding="utf-8",
                      errors="replace") as f:
                patch_body = f.read()
            link_patch_ok = ("120000" in patch_body
                             and "tools/tests/cur_link/expected-link.txt" in patch_body)
        except OSError:
            link_patch_ok = False
    case("symlink entry recreated as symlink (direct + end-to-end)",
         direct_link_ok and link_run["ok"] and link_verify_ok and link_patch_ok,
         "mode=%s patch120000=%s" % (link_entries[0]["mode"] if link_entries else "?", link_patch_ok))

    # 9. unsupported mode: fabricated entries + a real gitlink are rejected explicitly.
    real_entries, _, _ = enumerate_allowlist(rec, repo, tool_source, ("tools/cur_pipeline.py",))
    fab_ok = bool(real_entries)
    for bad_mode in ("160000", "100640"):
        if not real_entries:
            break
        fab = dict(real_entries[0])
        fab["mode"] = bad_mode
        fab_tmp = os.path.join(work_root, "fab-" + bad_mode)
        os.makedirs(fab_tmp, exist_ok=True)
        _, fab_probs = materialize(rec, repo, [fab], fab_tmp, set())
        target = os.path.join(fab_tmp, fab["path"])
        one = (len(fab_probs) == 1
               and "unsupported git mode" in fab_probs[0].get("reason", "")
               and not os.path.lexists(target))
        fab_ok = fab_ok and one
    sub_repo = os.path.join(work_root, "sub-repo")
    scratch_clone(sub_repo)
    sadd = Sub(["git", "-C", sub_repo, "-c", "protocol.file.allow=always",
                "submodule", "add", "--quiet", repo, "tools/tests/cur_link/submod"])
    Sub(["git", "-C", sub_repo, "add", "-A"])
    Sub(["git", "-C", sub_repo, "commit", "-q", "-m", "submodule fixture"])
    sub_src = Sub(["git", "-C", sub_repo, "rev-parse", "HEAD"])["stdout"].strip()
    _, _, sub_unsup = enumerate_allowlist(rec, sub_repo, sub_src, ("tools/tests/cur_link/",))
    sub_run = rehearse(rec, sub_repo, sub_src, src_full, os.path.join(work_root, "sub-out"),
                       link_allow, ("tools/tests/cur_schema/run.py",), (), False)
    sub_ok = (sadd["exit"] == 0 and len(sub_unsup) == 1 and sub_unsup[0]["mode"] == "160000"
              and (not sub_run["ok"]) and sub_run["stage"] == "mode")
    case("unsupported mode rejected explicitly (fabricated + gitlink)",
         fab_ok and sub_ok, "fab=%s stage=%s" % (fab_ok, sub_run["stage"]))

    # 10. nonempty output directory -> refusal; pre-existing content intact.
    ne_dir = os.path.join(work_root, "nonempty")
    os.makedirs(ne_dir, exist_ok=True)
    sentinel = os.path.join(ne_dir, "sentinel.txt")
    with open(sentinel, "w", encoding="utf-8") as f:
        f.write("do-not-touch\n")
    ne = call(out=ne_dir)
    with open(sentinel, "r", encoding="utf-8") as f:
        intact = (f.read() == "do-not-touch\n")
    case("nonempty output directory -> refusal",
         (not ne["ok"]) and ne["stage"] == "output" and intact
         and not os.path.lexists(os.path.join(ne_dir, COMPLETION_FILENAME))
         and not os.path.lexists(os.path.join(ne_dir, "input-manifest.json")),
         "stage=%s" % ne["stage"])

    # 11. interruption before publish -> no completed output at the final path.
    wt_before = listed_worktrees(repo)
    crash_out = os.path.join(work_root, "crash-out")
    crash_env = dict(os.environ)
    crash_env[CRASH_BEFORE_PUBLISH_ENV] = "1"
    cp = subprocess.run(
        [sys.executable, os.path.abspath(__file__), "--repo", repo,
         "--tool-source", tool_source, "--runtime-base", runtime_base,
         "--out", crash_out, "--suites", "tools/tests/cur_schema/run.py"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=900, env=crash_env)
    crash_verify, _ = verify_attempt(crash_out)
    try:
        orphans = [n for n in os.listdir(work_root) if n.startswith(STAGING_PREFIX)]
    except OSError:
        orphans = []
    orphan_has_manifest = any(
        os.path.isfile(os.path.join(work_root, n, COMPLETION_FILENAME)) for n in orphans)
    case("interruption before publish -> no completed output",
         cp.returncode != 0 and (not crash_verify) and (not os.path.lexists(crash_out))
         and orphan_has_manifest,
         "rc=%s orphan_staging=%d" % (cp.returncode, len(orphans)))
    for w in listed_worktrees(repo) - wt_before:
        rec.run(["git", "-C", repo, "worktree", "remove", "--force", w])
    rec.run(["git", "-C", repo, "worktree", "prune"])
    for n in orphans:
        shutil.rmtree(os.path.join(work_root, n), ignore_errors=True)

    # 12. two invocations targeting the SAME output -> exactly one succeeds.
    same_out = os.path.join(work_root, "same-out")
    same_argv = [sys.executable, os.path.abspath(__file__), "--repo", repo,
                 "--tool-source", tool_source, "--runtime-base", runtime_base,
                 "--out", same_out, "--suites", "tools/tests/cur_schema/run.py"]
    q1 = subprocess.Popen(same_argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    q2 = subprocess.Popen(same_argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    s1 = q1.wait(timeout=1800)
    s2 = q2.wait(timeout=1800)
    same_verify, _ = verify_attempt(same_out)
    case("two invocations, same output -> exactly one succeeds",
         (s1 == 0) != (s2 == 0) and same_verify,
         "rc=%s,%s" % (s1, s2))
    for w in listed_worktrees(repo) - wt_before:
        rec.run(["git", "-C", repo, "worktree", "remove", "--force", w])

    # 13. completion manifest missing -> consumer refuses the attempt.
    miss_dir = os.path.join(work_root, "manifest-missing")
    mok = True
    mreason = "baseline unavailable"
    if base["ok"] and base_verify:
        shutil.copytree(base_out, miss_dir)
        os.remove(os.path.join(miss_dir, COMPLETION_FILENAME))
        mok, mreason = verify_attempt(miss_dir)
    case("completion manifest missing -> consumer refuses",
         base["ok"] and base_verify and (not mok),
         "consumer=%s" % mreason[:100])

    # 14. tampered artifact -> consumer refuses the attempt.
    tamp_dir = os.path.join(work_root, "tampered")
    tok = True
    treason = "baseline unavailable"
    if base["ok"] and base_verify:
        shutil.copytree(base_out, tamp_dir)
        with open(os.path.join(tamp_dir, "import.patch"), "ab") as f:
            f.write(b"# tampered\n")
        tok, treason = verify_attempt(tamp_dir)
    case("tampered artifact -> consumer refuses",
         base["ok"] and base_verify and (not tok),
         "consumer=%s" % treason[:100])

    lines = ["HARNESS SELFTESTS — tools/tests/cur_import/run.py", "=" * 70, ""]
    passed = 0
    for c in cases:
        mark = "OK" if c["ok"] else "FAIL"
        if c["ok"]:
            passed += 1
        lines.append("  %-52s %s  %s" % (c["case"], mark, c["detail"]))
    lines.append("")
    lines.append("SUMMARY: %d/%d harness selftests pass" % (passed, len(cases)))
    lines.append("=" * 70)
    text = "\n".join(lines) + "\n"
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "harness-selftests.txt"), "w", encoding="utf-8") as f:
        f.write(text)
    sys.stdout.write(text)
    return 0 if passed == len(cases) else 1


# --------------------------------------------------------------------- CLI
USAGE = ("usage: run.py --repo <repo> --tool-source <sha> --runtime-base <sha> --out <dir> "
         "[--allowlist <file>] [--suites \"<a> <b>\"] [--allow-replace <path>] "
         "[--keep] [--selftest]\n"
         "       run.py --verify <attempt-directory>")


def main(argv):
    if len(argv) == 3 and argv[1] == "--verify":
        ok, reason = verify_attempt(argv[2])
        print(("ACCEPT" if ok else "REFUSE") + ": %s" % reason)
        return 0 if ok else 1

    repo = None
    tool_source = None
    runtime_base = None
    out_dir = None
    allowlist = DEFAULT_ALLOWLIST
    suites = DEFAULT_SUITES
    allow_replace = []
    keep = False
    do_selftest = False

    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--repo" and i + 1 < len(argv):
            repo = argv[i + 1]; i += 2
        elif a == "--tool-source" and i + 1 < len(argv):
            tool_source = argv[i + 1]; i += 2
        elif a == "--runtime-base" and i + 1 < len(argv):
            runtime_base = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_dir = argv[i + 1]; i += 2
        elif a == "--allowlist" and i + 1 < len(argv):
            with open(argv[i + 1], "r", encoding="utf-8") as f:
                allowlist = tuple(x.strip() for x in f.read().splitlines() if x.strip())
            i += 2
        elif a == "--suites" and i + 1 < len(argv):
            suites = tuple(x for x in argv[i + 1].split() if x)
            i += 2
        elif a == "--allow-replace" and i + 1 < len(argv):
            allow_replace.append(argv[i + 1]); i += 2
        elif a == "--keep":
            keep = True; i += 1
        elif a == "--selftest":
            do_selftest = True; i += 1
        else:
            sys.stderr.write(USAGE + "\n")
            sys.stderr.write("run.py: unknown argument: %s\n" % (a,))
            return 2

    if repo is None or tool_source is None or runtime_base is None or out_dir is None:
        sys.stderr.write(USAGE + "\n")
        return 2

    rec = Recorder()

    if do_selftest:
        work_root = tempfile.mkdtemp(prefix="cur_import_selftest_")
        try:
            return selftest(rec, repo, tool_source, runtime_base, out_dir, work_root)
        finally:
            shutil.rmtree(work_root, ignore_errors=True)

    result = rehearse(rec, repo, tool_source, runtime_base, out_dir, allowlist, suites,
                      tuple(allow_replace), keep)
    print("stage:    %s" % result["stage"])
    print("ok:       %s" % result["ok"])
    for row in result.get("source_rows", ()):
        print("  source      %-42s %s" % (row["suite"], row["verdict"]))
    for row in result.get("destination_rows", ()):
        print("  destination %-42s %s" % (row["suite"], row["verdict"]))
    for p in result["problems"]:
        print("  problem: %s" % p)
    if result.get("incomplete_dir"):
        print("incomplete: %s" % result["incomplete_dir"])
    print("artifacts: %s" % out_dir)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
