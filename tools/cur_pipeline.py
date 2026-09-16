#!/usr/bin/env python3
"""cur_pipeline.py — one-command entrypoint: frozen bundle -> evidence -> verdict.

Runs the full grader lane on a single frozen G-ENG-style bundle:

    bundle -> tools/cur_extract_evidence.py -> evidence manifest
           -> tools/cur_grade_artifact.py -> C1..C6 verdicts

and emits a single combined transcript in which extractor diagnostics and grader
results are kept as separate sections. It is pure glue over the two existing tools —
no new policy, no re-implementation of the checked handlers or the grader ruleset.

SCOPE / HOST TOOL BOUNDARY
--------------------------
Host-side tooling under tools/, exactly like the extractor and grader. It does not
construct machine values or machine terms and is not part of the machine runtime.
It deliberately avoids isinstance/type/getattr/callable.

GATE RULES (hardening)
----------------------
* Continuation is permitted ONLY when the extractor reports a documented status:
  exit 0 (no proof debt) or exit 1 (proof debt). An unexpected exit, a signal, a
  timeout, a missing manifest, or an invalid manifest identity is an EXECUTION ERROR
  and is never graded.
* Extraction always lands in a fresh, invocation-owned temporary directory. A manifest
  left by an earlier run is never read as a grading input. The requested --out manifest
  is published atomically only after extraction + identity validation succeed.
* The manifest identity (bundle digest, extractor name + digest, schema version) is
  validated against this invocation's input bundle and tools before grading.
* Unknown CLI options and ambiguous bundle directories are rejected.
* Outputs are published atomically and the input bundle is never overwritten.
* Only invocation-owned temporary files are cleaned, including on failure paths.

USAGE
  python3 tools/cur_pipeline.py <bundle.json|bundle_dir> \
         [--out <manifest.json>] [--transcript <file>] [--timeout <seconds>]

ENV TEST SEAMS (host tooling only)
  CUR_PIPELINE_EXTRACTOR  overrides the extractor command path (a python module).
  CUR_PIPELINE_GRADER     overrides the grader command path (a python module).

EXIT
  0  graded: final verdict PASS (all six checks PASS)
  1  graded: final verdict FAIL (one or more checks FAIL)
  2  either (a) a graded final verdict AMBIGUOUS / MALFORMED / schema / ruleset
     mismatch, or (b) not graded: extractor rejected the bundle (exit 2), or
     (c) not graded: EXECUTION ERROR (unexpected extractor/grader exit, signal,
     timeout, invalid manifest, or output-write failure)
  3  graded: no FAIL but at least one CANNOT_DETERMINE

The transcript always carries a PIPELINE_STATUS line that distinguishes an EXECUTION
ERROR from a graded verdict, so a caller can tell "the tooling failed" from "the
artifact failed." The numeric 0/1/2/3 interface is preserved; execution errors are
reported separately and never converted into a PASS.
"""

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
EXTRACTOR = os.environ.get("CUR_PIPELINE_EXTRACTOR") or os.path.join(HERE, "cur_extract_evidence.py")
GRADER = os.environ.get("CUR_PIPELINE_GRADER") or os.path.join(HERE, "cur_grade_artifact.py")

# Documented extractor statuses that permit continuation (grade).
_EXTRACTOR_OK = frozenset((0, 1))
# Documented grader verdicts, one per line of the exit contract above.
_GRADER_OK = frozenset((0, 1, 2, 3))

_USAGE = (
    "usage: cur_pipeline.py <bundle.json|bundle_dir> "
    "[--out <manifest.json>] [--transcript <file>] [--timeout <seconds>]"
)


def _sha256_text(text):
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _bundle_digest_from_file(path):
    """Reproduce the extractor's bundle digest: lexicographic JSON, compact separators."""
    with open(path, "r", encoding="utf-8") as f:
        bundle = json.load(f)
    cannon = json.dumps(bundle, sort_keys=True, separators=(",", ":"))
    return _sha256_text(cannon)


def _extractor_digest():
    """sha256 of the extractor source as observed by a host consumer."""
    try:
        return _sha256_text(_read_text(EXTRACTOR))
    except OSError:
        return "unavailable"


def _graded_verdict(stdout):
    """Return the grader's verdict string if stdout carries a verdict object, else None."""
    text = (stdout or "").strip()
    if not text:
        return None
    tail = text.rsplit("\n", 1)[-1].strip()
    try:
        obj = json.loads(tail)
    except ValueError:
        return None
    final = obj.get("final")
    if not isinstance(final, str):
        return None
    return final


def _atomic_write_text(path, text):
    """Write text to a same-directory temp then atomically replace path. Never touches input."""
    d = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix=".cur_pipeline_pub_", dir=d)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _atomic_copy(src, dst):
    """Copy src to dst atomically (content inspectable only after a clean replace)."""
    text = _read_text(src)
    _atomic_write_text(dst, text)


def _emit(text):
    print(text)


def main(argv):
    if len(argv) < 2:
        sys.stderr.write(_USAGE + "\n")
        return 2

    src = argv[1]
    out_manifest = None
    transcript_path = None
    timeout = None
    i = 2
    while i < len(argv):
        arg = argv[i]
        if arg == "--out" and i + 1 < len(argv):
            out_manifest = argv[i + 1]
            i += 2
        elif arg == "--transcript" and i + 1 < len(argv):
            transcript_path = argv[i + 1]
            i += 2
        elif arg == "--timeout" and i + 1 < len(argv):
            try:
                timeout = float(argv[i + 1])
            except ValueError:
                sys.stderr.write("pipeline: --timeout must be a number\n")
                return 2
            if timeout <= 0:
                sys.stderr.write("pipeline: --timeout must be positive\n")
                return 2
            i += 2
        else:
            sys.stderr.write(_USAGE + "\n")
            sys.stderr.write("pipeline: unknown argument: %s\n" % (arg,))
            return 2

    # Resolve a bundle directory to a single json file; reject ambiguous directories.
    if os.path.isdir(src):
        jsons = sorted(f for f in os.listdir(src) if f.endswith(".json"))
        if len(jsons) != 1:
            sys.stderr.write("pipeline: directory must contain exactly one bundle json\n")
            return 2
        src = os.path.join(src, jsons[0])

    # Never overwrite the input bundle with an output.
    abs_src = os.path.abspath(src)
    for label, target in (("--out", out_manifest), ("--transcript", transcript_path)):
        if target is not None and os.path.abspath(target) == abs_src:
            sys.stderr.write("pipeline: refusing to overwrite the input bundle via %s\n" % (label,))
            return 2

    # ---- phase 1: extract into an invocation-owned temp manifest (never a stale --out).
    tmp_dir = tempfile.mkdtemp(prefix="cur_pipeline_")
    extract_manifest = os.path.join(tmp_dir, "manifest.json")
    transcript_lines = [
        "CUR-GRADER-ENG pipeline: %s" % os.path.basename(src),
        "  extractor: %s" % EXTRACTOR,
        "  grader:    %s" % GRADER,
        "=" * 70,
    ]

    def _finish(exit_code, status, extra_lines):
        transcript_lines.append("=" * 70)
        transcript_lines.append("PIPELINE_STATUS=%s" % status)
        transcript_lines.append("PIPELINE_EXIT=%s" % exit_code)
        out_text = "\n".join(transcript_lines) + "\n"
        try:
            if transcript_path is not None:
                _atomic_write_text(transcript_path, out_text)
            else:
                _emit(out_text.rstrip("\n"))
        except OSError as e:
            sys.stderr.write("pipeline: cannot write transcript: %s\n" % (e,))
            return 2
        return exit_code

    try:
        # Run the extractor; capture diagnostics separately.
        try:
            ex = subprocess.run([sys.executable, EXTRACTOR, src, "--out", extract_manifest],
                                capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            transcript_lines.append("[extractor] TIMEOUT")
            transcript_lines.append("[pipeline] extractor exceeded timeout; not grading")
            return _finish(2, "EXECUTION_ERROR", [])

        extractor_exit = ex.returncode
        extractor_stdout = ex.stdout.strip()
        extractor_stderr = ex.stderr.strip()
        transcript_lines.append("[extractor] exit=%s" % extractor_exit)
        if extractor_stdout:
            transcript_lines.append("[extractor] " + extractor_stdout)
        if extractor_stderr:
            transcript_lines.append("[extractor] stderr: " + extractor_stderr)

        # Gate on documented statuses only: 0 or 1. Anything else (incl. signals, exit 7)
        # is an execution error, not a grade and not a reject.
        if extractor_exit not in _EXTRACTOR_OK:
            if extractor_exit == 2:
                # Documented extractor rejection: meaningful downstream, never graded.
                transcript_lines.append("[pipeline] extractor rejected bundle; not grading (exit 2)")
                return _finish(2, "REJECTED", [])
            transcript_lines.append(
                "[pipeline] unexpected extractor exit %s; not grading" % (extractor_exit,))
            return _finish(2, "EXECUTION_ERROR", [])

        if not os.path.exists(extract_manifest):
            transcript_lines.append("[pipeline] extractor produced no manifest; not grading")
            return _finish(2, "EXECUTION_ERROR", [])

        # ---- validate manifest identity against this invocation's input and tools.
        try:
            manifest = json.loads(_read_text(extract_manifest))
            identity = manifest.get("identity")
            if identity is None:
                raise ValueError("manifest has no identity block")
            fmt_digest = _bundle_digest_from_file(src)
            if identity.get("bundle_digest") != fmt_digest:
                raise ValueError("manifest bundle digest does not match input bundle")
            if identity.get("extractor") != "cur_extract_evidence.py" and \
               identity.get("extractor") != os.path.basename(EXTRACTOR):
                raise ValueError("manifest extractor does not match this extractor")
            if identity.get("extractor_digest") != _extractor_digest():
                raise ValueError("manifest extractor digest does not match this extractor")
            if identity.get("grader_schema_version") is None or \
               manifest.get("schema_version") is None:
                raise ValueError("manifest missing schema version")
        except (ValueError, OSError) as e:
            transcript_lines.append("[pipeline] manifest identity invalid: %s" % (e,))
            transcript_lines.append("[pipeline] not grading")
            return _finish(2, "EXECUTION_ERROR", [])

        # Phase 1 succeeded: atomically publish the validated manifest to --out if requested.
        if out_manifest is not None:
            try:
                _atomic_copy(extract_manifest, out_manifest)
            except OSError:
                transcript_lines.append("[pipeline] cannot publish manifest to --out; not grading")
                return _finish(2, "EXECUTION_ERROR", [])

        # ---- phase 2: grade.
        try:
            gr = subprocess.run([sys.executable, GRADER, extract_manifest],
                                capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            transcript_lines.append("[grader] TIMEOUT")
            transcript_lines.append("[pipeline] grader exceeded timeout; no verdict")
            return _finish(2, "EXECUTION_ERROR", [])

        grader_exit = gr.returncode
        grader_stdout = gr.stdout.strip()
        grader_stderr = gr.stderr.strip()
        transcript_lines.append("[grader] exit=%s" % grader_exit)
        if grader_stdout:
            transcript_lines.append("[grader] " + grader_stdout)
        if grader_stderr:
            transcript_lines.append("[grader] stderr: " + grader_stderr)

        # A grader verdict requires BOTH a documented exit AND a parseable verdict object.
        verdict = _graded_verdict(grader_stdout)
        if grader_exit not in _GRADER_OK or verdict is None:
            transcript_lines.append(
                "[pipeline] grader did not produce a verdict (exit %s); no verdict" % (grader_exit,))
            return _finish(2, "EXECUTION_ERROR", [])

        return _finish(grader_exit, "GRADED", [])
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
