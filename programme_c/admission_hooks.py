"""C-C gate hooks for JoinAdmission with strict fail-closed semantics
(per C-INT review 2026-09-16):

Validity, rent, and human hooks each fail closed when their backing evidence
is unavailable. Proposals are inactive while any gate blocks; activation
never occurs inside a check.

Manifest persistence uses the Linux durability contract: same-directory
tmp, flush, fsync, os.replace, fsync parent dir. Enqueue is persisted;
corrupt/truncated/wrong-version manifests raise ManifestError (callers
must treat that as a hard block, not silently reset).

Gate evidence is bound to (proposal_id, accepted_state_version). After a
successful admission the accepted_state_version increments, invalidating
any gate evidence computed against an earlier version.

Validity hook: live validity dispatches an ISOLATED SUBPROCESS running
graph.ActivateProposal on a freshly-booted runtime so boot_from_packs /
make_fresh_runtime cannot clobber the coordinator's live constructor
registry. The subprocess writes a JSON response; the hook translates
it to (ok, reason_atom) pairs expected by JoinAdmission.admit_next. On
call-time boot failure it returns (False, F_LAUNCH_ERROR) so admit_next
holds the queue front intact and returns 'validity-launch-error'.
"""
from __future__ import annotations

import json as _json
import os
import time as _time


MANIFEST_SCHEMA_VERSION = 2


class ManifestError(RuntimeError):
    pass


def _fsync_dir(path):
    # Durability contract: fsync the parent directory. Any OSError
    # (e.g., injected failure, I/O error) must propagate — caller
    # must not report durable success.
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _require(cond, msg):
    if not cond:
        raise ManifestError(msg)


def write_admission_manifest(manifest_path, accepted_proposals, queue,
                             accepted_state_version=0,
                             schema_version=MANIFEST_SCHEMA_VERSION):
    """Durable atomic write. Propagates I/O errors so callers do not report
    admission success on persistence failure."""
    payload = {
        "schema_version": schema_version,
        "written_at": _time.time(),
        "accepted_state_version": int(accepted_state_version),
        "accepted": list(accepted_proposals),
        "queue": list(queue),
    }
    d = os.path.dirname(os.path.abspath(manifest_path))
    if d:
        os.makedirs(d, exist_ok=True)
    tmp = manifest_path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as h:
            _json.dump(payload, h, indent=2, sort_keys=True, ensure_ascii=False)
            h.flush()
            os.fsync(h.fileno())
    except Exception:
        try: os.unlink(tmp)
        except OSError: pass
        raise
    os.replace(tmp, manifest_path)
    if d:
        _fsync_dir(d)
    return manifest_path


def load_admission_manifest(manifest_path,
                            expected_schema=MANIFEST_SCHEMA_VERSION):
    """Fail-closed load. Missing file -> new run (empty/empty/0). Corrupt or
    schema-mismatch -> raise ManifestError. Host type checks are done via
    try/except attribute probes (no isinstance)."""
    if not os.path.exists(manifest_path):
        return [], [], 0
    try:
        with open(manifest_path, "r", encoding="utf-8") as h:
            payload = _json.load(h)
    except (OSError, _json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ManifestError("corrupt or unreadable manifest: " + str(exc))
    # Root must be a JSON object (dict). Probe with dict-style access.
    try:
        schema = payload.get("schema_version")
        accepted = payload.get("accepted")
        queue = payload.get("queue")
        version = payload.get("accepted_state_version", 0)
    except AttributeError:
        raise ManifestError("manifest root is not a JSON object")
    if schema != expected_schema:
        raise ManifestError("manifest schema_version mismatch: got "
                            + repr(schema) + " expected " + str(expected_schema))
    # accepted/queue must be JSON arrays (lists); probe via list-append.
    try:
        accepted.append
        queue.append
    except AttributeError:
        raise ManifestError("manifest accepted/queue fields malformed")
    for e in accepted + queue:
        try:
            _ = e["proposal_id"]; _ = e["proposal_text"]
        except (AttributeError, KeyError, TypeError):
            raise ManifestError("manifest entry missing required fields")
    return list(accepted), list(queue), int(version)


# ---------- fail-closed gate callables ------------------------------------

def make_validity_check(proposal_validator=None):
    """Validity gate. If proposal_validator is None (or raises), FAILS
    closed. proposal_validator is a callable (entry, accepted, version) ->
    either bool or (bool, reason_atom). Returning (False, F_LAUNCH_ERROR)
    signals a transient boot failure; admit_next keeps the queue front."""
    import hyge_int_pkg.programme_c as P
    F_INVALID = P.F_INVALID_CERT
    if proposal_validator is None:
        def _deny(_entry, _accepted, _version): return False, F_INVALID
        return _deny
    def _check(entry, accepted, accepted_version):
        text = entry.get("proposal_text", "")
        if not text or "\x00" in text:
            return False, F_INVALID
        try:
            res = proposal_validator(entry, accepted, accepted_version)
        except Exception:
            return False, F_INVALID
        # Decode tuple (bool, reason) or plain bool via try/except on
        # indexing (no isinstance).
        try:
            ok = bool(res[0])
            reason = res[1] if len(res) > 1 else None
        except Exception:
            ok, reason = bool(res), None
        if ok:
            return True, None
        return False, (reason if reason is not None else F_INVALID)
    return _check


def structural_only_validity_for_tests():
    """Structural-only validity for unit tests where running the real
    ActivateProposal check is undesirable. NOT acceptable for live
    admission."""
    import hyge_int_pkg.programme_c as P
    F_INVALID = P.F_INVALID_CERT
    def _check(entry, accepted, version):
        text = entry.get("proposal_text", "")
        if bool(text) and "\x00" not in text:
            return True, None
        return False, F_INVALID
    return _check


def make_rent_check(benchmark_dir=None, benchmark_filename=None):
    """Rent gate: performance-only. Delegates to programme_c.rent which
    runs the held-out benchmark in an isolated subprocess. Returns
    (bool, reason_atom).

    Missing/unreadable benchmark -> (False, F_LAUNCH_ERROR) (front held).
    Benchmark execution failure -> (False, F_LAUNCH_ERROR) (front held).
    Rent fail (step/time budget exceeded or spec rejected)
        -> (False, F_RENT_FAIL) (reject + pop).
    Pass -> (True, None); evidence recorded keyed by
        (proposal_id, accepted_state_version, benchmark_identity).

    The benchmark_filename argument is retained for backward compat
    (default: "benchmark.json" inside benchmark_dir); new code should
    place the rent benchmark at benchmark_dir/benchmark.json per the
    convention in programme_c/rent.py.
    """
    from hyge_int_pkg.programme_c.rent import make_rent_check as _rent_make
    if benchmark_dir is None:
        import hyge_int_pkg.programme_c as PP
        F_LAUNCH = PP.F_LAUNCH_ERROR
        def _deny(_entry, _accepted=None, _version=None):
            return False, F_LAUNCH
        return _deny
    return _rent_make(benchmark_dir=benchmark_dir)


def make_human_check(approval_callback=None):
    """Human gate: default denies (no private activation per protocol/F.md).
    Missing callback or exception -> deny. Accepts (entry, accepted,
    accepted_version) signature consistent with the other gates; the
    callback receives the entry only. Human launch-error support is
    plumbed through admit_next for symmetry, but the default denier
    returns plain False -> awaiting-human (human is still fail-closed
    denier until its wiring slice)."""
    if approval_callback is None:
        def _deny(_entry, _accepted=None, _version=None): return False
        return _deny
    def _check(entry, _accepted=None, _version=None):
        try:
            return bool(approval_callback(entry)), None
        except Exception:
            return False, None
    return _check


# ---------- Live ActivateProposal validity (subprocess-isolated) ---------

def make_live_activate_proposal_check(package_root=None, python_exe=None,
                                       timeout_seconds=120):
    """Return a validity-check callable (entry, accepted, version) ->
    (ok, reason_atom_or_None). Call-time boot/runtime failure yields
    (False, F_LAUNCH_ERROR) so admit_next keeps the queue front intact
    and returns 'validity-launch-error'. The check runs in an isolated
    subprocess so the coordinator's live Hypergraph/AllConstructors is
    never mutated. The synthetic Approved annotation is attached inside
    the child to a COPY of the candidate; the queue entry is not
    mutated."""
    import hyge_int_pkg.programme_c as P
    from hyge_int_pkg.programme_c.validity import run_validity_check_subprocess
    F_LAUNCH = P.F_LAUNCH_ERROR
    F_INVALID = P.F_INVALID_CERT
    def _check(entry, accepted, version):
        try:
            res = run_validity_check_subprocess(
                entry, accepted, version,
                package_root=package_root, python_exe=python_exe,
                timeout_seconds=timeout_seconds)
        except Exception:
            return False, F_LAUNCH
        status = res.get("status")
        if status == "completed" and res.get("passed"):
            return True, None
        if status == "launch-error":
            return False, F_LAUNCH
        return False, F_INVALID
    return _check
