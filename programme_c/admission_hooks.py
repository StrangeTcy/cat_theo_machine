"""C-C gate hooks for JoinAdmission with strict fail-closed semantics
(per C-INT review 2026-09-16):

Validity, rent, and human hooks each fail closed when their backing evidence
is unavailable. Proposals are inactive while any gate blocks; activation
never occurs inside a check.

Manifest persistence uses the Linux durability contract:
same-directory tmp, flush, fsync, os.replace, fsync parent dir. Enqueue is
persisted; corrupt/truncated/wrong-version manifests raise ManifestError
(callers must treat that as a hard block, not silently reset).

Gate evidence is bound to (proposal_id, accepted_state_version). After a
successful admission the accepted_state_version increments, invalidating
any gate evidence computed against an earlier version.
"""
from __future__ import annotations

import json as _json
import os
import time as _time


MANIFEST_SCHEMA_VERSION = 2


class ManifestError(RuntimeError):
    pass


def _fsync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


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
    schema-mismatch -> raise ManifestError."""
    if not os.path.exists(manifest_path):
        return [], [], 0
    try:
        with open(manifest_path, "r", encoding="utf-8") as h:
            payload = _json.load(h)
    except (OSError, _json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ManifestError("corrupt or unreadable manifest: " + str(exc))
    if not isinstance(payload, dict):
        raise ManifestError("manifest root is not a JSON object")
    schema = payload.get("schema_version")
    if schema != expected_schema:
        raise ManifestError("manifest schema_version mismatch: got "
                            + repr(schema) + " expected " + str(expected_schema))
    accepted = payload.get("accepted")
    queue = payload.get("queue")
    version = payload.get("accepted_state_version", 0)
    if not isinstance(accepted, list) or not isinstance(queue, list):
        raise ManifestError("manifest accepted/queue fields malformed")
    # Validate entry shapes lightly.
    for e in accepted + queue:
        if not isinstance(e, dict) or "proposal_id" not in e or "proposal_text" not in e:
            raise ManifestError("manifest entry missing required fields")
    return list(accepted), list(queue), int(version)


# ---------- fail-closed gate callables ------------------------------------

def make_validity_check(proposal_validator=None):
    """Validity gate. If proposal_validator is None (or raises), FAILS
    closed. proposal_validator is a callable (entry, accepted, accepted_version)
    -> bool; it MUST perform its checks without mutating parent state
    (caller is responsible for running any activation in an isolated runtime).
    """
    if proposal_validator is None:
        def _deny(_entry, _accepted, _version): return False
        return _deny
    def _check(entry, accepted, accepted_version):
        text = entry.get("proposal_text", "")
        if not text or "\x00" in text:
            return False
        try:
            return bool(proposal_validator(entry, accepted, accepted_version))
        except Exception:
            return False
    return _check


def structural_only_validity_for_tests():
    """Structural-only validity for unit tests where runtime boot is
    undesirable. This is NOT acceptable for live admission."""
    def _check(entry, accepted, version):
        text = entry.get("proposal_text", "")
        return bool(text) and "\x00" not in text
    return _check


def make_rent_check(benchmark_dir=None, benchmark_filename="rent_benchmark.json"):
    """Rent gate: fail-closed. benchmark_dir must exist and contain a readable
    JSON benchmark file for rent to pass. If benchmark_dir is None (no
    held-out benchmark configured) -> block. Joint-set rent deferred; this
    signals performance-evidence presence only."""
    if benchmark_dir is None:
        def _deny(_entry): return False
        return _deny
    def _check(entry):
        try:
            if not os.path.isdir(benchmark_dir):
                return False
            path = os.path.join(benchmark_dir, benchmark_filename)
            if not os.path.isfile(path):
                return False
            with open(path, "r", encoding="utf-8") as h:
                data = _json.load(h)
            return isinstance(data, dict)
        except Exception:
            return False
    return _check


def make_human_check(approval_callback=None):
    """Human gate: default denies (no private activation per protocol/F.md).
    Missing callback or exception -> deny."""
    if approval_callback is None:
        def _deny(_entry): return False
        return _deny
    def _check(entry):
        try:
            return bool(approval_callback(entry))
        except Exception:
            return False
    return _check


def make_live_activate_proposal_check(package_root=None, pack_paths=None):
    """Live (non-structural) validity gate: boot an isolated runtime on
    every call, attach Approved, run graph.ActivateProposal, accept iff
    installed_version != EmptyList. Raises BootError (from .validity)
    when the isolated runtime cannot boot -- caller must halt and report,
    NOT fall back to a structural check."""
    from hyge_int_pkg.programme_c.validity import (
        make_activate_proposal_validity_check, BootError,
    )
    return make_activate_proposal_validity_check(
        package_root=package_root, pack_paths=pack_paths), BootError
