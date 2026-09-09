#!/usr/bin/env python3
"""cur_pipeline.py — one-command entrypoint: frozen bundle -> evidence -> verdict.

Runs the full grader lane on a single frozen G-ENG-style bundle:

    bundle → tools/cur_extract_evidence.py → evidence manifest
          → tools/cur_grade_artifact.py → C1..C6 verdicts

and emits a single combined transcript (extractor diagnostics + grader verdict). It is pure glue
over the two existing tools — no new policy, no re-implementation of the checked handlers or the
grader ruleset.

SCOPE / HOST TOOL BOUNDARY
--------------------------
Host-side tooling under tools/, exactly like the extractor and grader. It does not construct
machine values or machine terms and is not part of the machine runtime. It deliberately avoids
isinstance/type/getattr/callable and uses only identity and attribute-availability checks.

USAGE
  python3 tools/cur_pipeline.py <bundle.json|bundle_dir> [--out <manifest.json>] [--transcript <file>]

EXIT
  0  final verdict PASS (all six checks PASS)
  1  final verdict FAIL (one or more checks FAIL)
  2  malformed / ambiguous / contradictory / schema / ruleset mismatch
  3  no FAIL but at least one CANNOT_DETERMINE

The exit is that of the grader after a successful extraction, or 2 when the extractor rejects the
bundle (meaningful downstream), so a caller can gate on a single nonzero exit for failure.
"""

import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXTRACTOR = os.path.join(HERE, "cur_extract_evidence.py")
GRADER = os.path.join(HERE, "cur_grade_artifact.py")


def _emit(text):
    print(text)


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: cur_pipeline.py <bundle.json|bundle_dir> [--out <manifest.json>] [--transcript <file>]\n")
        return 2
    src = argv[1]
    out_manifest = None
    transcript_path = None
    i = 2
    while i < len(argv):
        if argv[i] == "--out" and i + 1 < len(argv):
            out_manifest = argv[i + 1]
            i += 2
        elif argv[i] == "--transcript" and i + 1 < len(argv):
            transcript_path = argv[i + 1]
            i += 2
        else:
            i += 1

    # Accept a bundle file or a directory containing exactly one bundle json.
    if os.path.isdir(src):
        jsons = sorted(f for f in os.listdir(src) if f.endswith(".json"))
        if len(jsons) != 1:
            sys.stderr.write("pipeline: directory must contain exactly one bundle json\n")
            return 2
        src = os.path.join(src, jsons[0])

    # Use a temp manifest path unless the caller supplied --out.
    import tempfile
    tmp_dir = None
    manifest_path = out_manifest
    if manifest_path is None:
        tmp_dir = tempfile.mkdtemp(prefix="cur_pipeline_")
        manifest_path = os.path.join(tmp_dir, "manifest.json")

    # ---- phase 1: extract.
    ex = subprocess.run([sys.executable, EXTRACTOR, src, "--out", manifest_path],
                        capture_output=True, text=True)
    extractor_exit = ex.returncode
    extractor_stdout = ex.stdout.strip()
    extractor_stderr = ex.stderr.strip()

    transcript_lines = []
    transcript_lines.append("CUR-GRADER-ENG pipeline: %s" % os.path.basename(src))
    transcript_lines.append("  extractor: %s" % EXTRACTOR)
    transcript_lines.append("  grader:    %s" % GRADER)
    transcript_lines.append("=" * 70)
    transcript_lines.append("[extractor] exit=%s" % extractor_exit)
    if extractor_stdout:
        transcript_lines.append("[extractor] " + extractor_stdout)
    if extractor_stderr:
        transcript_lines.append("[extractor] stderr: " + extractor_stderr)

    if extractor_exit == 2 or not os.path.exists(manifest_path):
        # extractor rejected the bundle; do not grade.
        transcript_lines.append("[pipeline] extractor rejected bundle; not grading (exit 2)")
        if transcript_path:
            with open(transcript_path, "w", encoding="utf-8") as f:
                f.write("\n".join(transcript_lines) + "\n")
        else:
            _emit("\n".join(transcript_lines))
        return 2

    # ---- phase 2: grade.
    gr = subprocess.run([sys.executable, GRADER, manifest_path],
                        capture_output=True, text=True)
    grader_exit = gr.returncode
    grader_stdout = gr.stdout.strip()
    grader_stderr = gr.stderr.strip()
    transcript_lines.append("[grader] exit=%s" % grader_exit)
    if grader_stdout:
        transcript_lines.append("[grader] " + grader_stdout)
    if grader_stderr:
        transcript_lines.append("[grader] stderr: " + grader_stderr)
    transcript_lines.append("=" * 70)
    transcript_lines.append("PIPELINE_EXIT=%s" % grader_exit)

    out_text = "\n".join(transcript_lines) + "\n"
    if transcript_path:
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(out_text)
    else:
        _emit(out_text.rstrip("\n"))

    if tmp_dir:
        shutil_rmtree(tmp_dir)

    return grader_exit


def shutil_rmtree(path):
    import shutil
    shutil.rmtree(path, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
