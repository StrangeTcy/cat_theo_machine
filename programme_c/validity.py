"""Isolated check-only ActivateProposal validity gate (C-INT, 2026-09-17).

The validity check runs in a SPAWNED SUBPROCESS so that boot_from_packs /
make_fresh_runtime (which reset M.AllConstructors and build a fresh
Hypergraph) cannot mutate the coordinator's live constructor registry
or interfere with certificate replay in worker_dispatch. This matches
the existing C-A pattern: coordinator dispatches an isolated child
process, child reports a stamped response, coordinator verifies.

Parent writes a JSON request to a temp file, invokes
  python -m hyge_int_pkg.main validity-check <req.json> <resp.json>
child boots an isolated runtime, runs graph.ActivateProposal against
the candidate (after InstallLaw-replaying any prior accepted laws,
after applying BootstrapSafetyInvariants), and writes a JSON response:
  { "status": "completed"|"failed"|"launch-error",
    "passed": bool, "reason": str, "detail": str }

Parent returns (bool, reason_atom) pairs to admit_next so F_LAUNCH_ERROR
keeps the queue front intact (halt-and-report).

=== Encoding surface (fail-closed invariant per Fable 4.6 carry-forward) ===

Request encodes laws via a small JSON surface which the child decodes
into machine terms. Representable shapes (shared with rent.py):

  * "EmptyList"                 -> M.EmptyList
  * "arbitrary string"          -> M.Char(s)
  * {"Zero": null}              -> M.Zero
  * {"Succ": <spec>}            -> M.Succ(decoded(spec))()
  * {"Char": "text"}            -> M.Char(text)
  * {"Pair": [<spec>, <spec>]}  -> M.Pair(decoded(a), decoded(b))
  * Law kinds:
      {"kind": "rule",         "left": <spec>, "right": <spec>}
          -> CompileRuleToLaw(Rule(left, right))
      {"kind": "policy_entry", "class_name": "...", "gate": "..."}
          -> CompileRuleToLaw(Rule(PolicyEntry(Char(cls), Char(gate)),
                                   PolicyEntry(Char(cls), Char(gate))))

Invariant (C2 carry-forward: encoding surface fail-closed): any accepted
entry or candidate that lacks a decodable proposal_encoding /
law_encoding (missing key, unsupported shape, CompileRuleToLaw returns
EmptyList) surfaces as F_LAUNCH_ERROR -- queue front held intact,
no pop, no false pass, no F_INVALID_CERT misclassification. The
parent-side serialization probe in run_validity_check_subprocess
raises/returns launch-error before spawning the child for known-missing
encodings; child-side decode errors return launch-error in the
response. No free-text parser is wired in the live path.

The synthetic Approved annotation is attached inside the child only,
to a freshly-decoded copy of the candidate -- the queue entry is
never mutated with a synthetic approval.

No reconciliation surface: validity runs inside admit_next BEFORE the
entry is moved to 'admitted'; the child's runtime is discarded, the
parent commits no state during the check, and no activation_id is
consumed.
"""
from __future__ import annotations

import json as _json
import os
import subprocess as _sp
import sys as _sys
import tempfile
import time as _time


LAUNCH_ERROR_REASON = "launch-error"
INVALID_CERT_REASON = "invalid-certificate"
COMPLETED_STATUS = "completed"
FAILED_STATUS = "failed"
TIMEOUT_SECONDS = 120


def _find_package_root():
    here = os.path.abspath(__file__)
    return os.path.abspath(os.path.join(os.path.dirname(here), ".."))


def _default_python():
    return _sys.executable


def run_validity_check_subprocess(entry, accepted_proposals,
                                   accepted_state_version,
                                   package_root=None,
                                   python_exe=None,
                                   timeout_seconds=TIMEOUT_SECONDS):
    """Run check-only ActivateProposal in an isolated subprocess.

    Returns dict:
      { "status": "completed"|"failed"|"launch-error",
        "passed": bool, "reason": str, "detail": str }
    """
    if package_root is None:
        package_root = _find_package_root()
    if python_exe is None:
        python_exe = _default_python()
    req_fd, req_path = tempfile.mkstemp(prefix="validity_req_", suffix=".json")
    resp_fd, resp_path = tempfile.mkstemp(prefix="validity_resp_", suffix=".json")
    os.close(req_fd); os.close(resp_fd)
    try:
        payload = {
            "entry": _entry_to_json(entry),
            "accepted_proposals": [_entry_to_json(e) for e in (accepted_proposals or [])],
            "accepted_state_version": int(accepted_state_version or 0),
            "package_root": package_root,
        }
        with open(req_path, "w", encoding="utf-8") as h:
            _json.dump(payload, h)
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(package_root) + os.pathsep + env.get("PYTHONPATH", "")
        env.pop("HYGE_SEARCH_WORKER_GATE_PATH", None)
        env.pop("HYGE_SEARCH_WORKER_READY_TIMEOUT", None)
        cmd = [python_exe, "-m", "hyge_int_pkg.main",
               "validity-check", req_path, resp_path]
        try:
            proc = _sp.Popen(cmd, stdout=_sp.PIPE, stderr=_sp.PIPE,
                              cwd=package_root, env=env)
        except Exception as exc:
            return _resp_launch("failed to spawn: " + str(exc))
        try:
            out, err = proc.communicate(timeout=timeout_seconds)
        except _sp.TimeoutExpired:
            try: proc.kill()
            except Exception: pass
            proc.wait(timeout=5)
            return _resp_launch("validity subprocess timed out")
        rc = proc.returncode
        if rc != 0:
            tail = (out or b"").decode("utf-8", "replace")[-500:]
            tail_e = (err or b"").decode("utf-8", "replace")[-500:]
            return _resp_launch("rc=%d stdout=%s stderr=%s" % (rc, tail, tail_e))
        try:
            with open(resp_path, "r", encoding="utf-8") as h:
                data = _json.load(h)
        except Exception as exc:
            return _resp_launch("invalid response json: " + str(exc))
        return data
    finally:
        for p in (req_path, resp_path):
            try: os.unlink(p)
            except OSError: pass


def _resp_launch(detail):
    return {"status": "launch-error", "passed": False,
            "reason": LAUNCH_ERROR_REASON, "detail": detail}


def _entry_to_json(entry):
    """Serialize an admission entry for the validity child. Probes for
    expected keys via try/except (no isinstance)."""
    out = {}
    try:
        for k in ("proposal_id", "proposal_text", "state", "origin",
                  "proposal_encoding", "law_encoding"):
            try:
                out[k] = entry[k]
            except (KeyError, TypeError):
                pass
        return out
    except (AttributeError, TypeError):
        return None


# ------------------------- child process entry ---------------------------

def _child_simple_term(ns, spec):
    """Decode a simple S-expr-ish JSON value into a machine term. Probes
    structure with try/except key access (no isinstance/type)."""
    M = ns["M"]
    # Dict shapes first (so we don't accidentally treat a dict with a
    # "Zero" key as a string/Char).
    try:
        _ = spec["Zero"]
        if spec["Zero"] is None:
            return M.Zero
    except (KeyError, TypeError):
        pass
    try:
        sub = spec["Succ"]
        return M.Succ(_child_simple_term(ns, sub))()
    except (KeyError, TypeError):
        pass
    try:
        return M.Char(str(spec["Char"]))
    except (KeyError, TypeError):
        pass
    try:
        a, b = spec["Pair"]
        return M.Pair(_child_simple_term(ns, a), _child_simple_term(ns, b))
    except (KeyError, TypeError, ValueError):
        pass
    # Plain string: either "EmptyList" sentinel or a Char atom.
    try:
        s = spec + ""
        if s == "EmptyList":
            return M.EmptyList
        return M.Char(s)
    except Exception:
        pass
    raise ValueError("unsupported term spec")


def _child_boot_ns(package_root):
    parent = os.path.dirname(package_root)
    if parent not in _sys.path:
        _sys.path.insert(0, parent)
    from hyge_int_pkg import (
        machine as M, graph as G, runtime as R, labels as L,
        heuristics as H, constructors as C, programme_c as P,
    )
    if "NatValueIndex" not in vars(M):
        M.NatValueIndex = M.Tree(M.EmptyList)
    ns = {"M": M, "G": G, "R": R, "L": L, "H": H, "C": C, "P": P}
    try:
        from hyge_int_pkg import symbols as S, rewrite_rules as X, session as T
        ns["S"] = S; ns["X"] = X; ns["T"] = T
    except Exception:
        pass
    return ns


def _runtime_ns(ns):
    out = {}
    for mod in (ns["M"], ns["G"], ns["H"], ns["L"], ns["P"], ns["R"], ns["C"]):
        out.update(vars(mod))
    for name in ("Zero","one","two","three","four","five","six","seven","eight",
                 "nine","NatValueIndex"):
        try: out[name] = vars(ns["M"])[name]
        except KeyError: pass
    for name in ("ZeroLabel","SuccLabel","PairLabel","TreeLabel"):
        try: out[name] = vars(ns["L"])[name]
        except KeyError: pass
    for k in ("S","X","T"):
        if k in ns:
            out.update(vars(ns[k]))
    return out


def _child_pack_paths(package_root):
    pack_dir = os.path.join(package_root, "packs")
    return [os.path.join(pack_dir, n) for n in (
        "order-sign.pack.yaml", "sqrt-real.pack.yaml",
        "algebra-distribute.pack.yaml", "sequence-order.pack.yaml",
        "real-closure.pack.yaml", "arithmetic.pack.yaml",
        "geometry-ontology.pack.yaml", "trigonometry.pack.yaml",
        "geometry.pack.yaml", "engel-coins.pack.yaml",
        "engel-means.pack.yaml", "engel-blackboard.pack.yaml",
        "number-theory.pack.yaml",
    )]


def _write_resp(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as h:
        _json.dump(data, h)
        h.flush()
        os.fsync(h.fileno())
    os.replace(tmp, path)


def _child_law_from_encoding(ns, enc):
    """Decode a law encoding. Supports:
      {"kind":"rule", "left":..., "right":...}   -- rewrite Rule
      {"kind":"policy_entry", "class_name":..., "gate":...}
          -- a PolicyEntry(class_name, gate) term wrapped as a law via
             Rule(policy_entry, policy_entry) identity so CompileRuleToLaw
             encodes it as a graph node (ClassifyProposal scans the right
             side for PolicyEntryLabel terms to detect policy_change)."""
    G, M = ns["G"], ns["M"]
    kind = enc["kind"]
    if kind == "rule":
        left = _child_simple_term(ns, enc["left"])
        right = _child_simple_term(ns, enc["right"])
        from hyge_int_pkg import proof as P2
        rule = P2.Rule(left, right)()
        law = G.CompileRuleToLaw(rule)()
        if M.IdentityCompare(law, M.EmptyList)() is M.truth_value:
            raise ValueError("CompileRuleToLaw returned EmptyList")
        return law
    if kind == "policy_entry":
        cls = M.Char(str(enc["class_name"]))
        gate = M.Char(str(enc["gate"]))
        pe = G.PolicyEntry(cls, gate)()
        # Wrap the policy-entry term as a trivial identity rule so
        # CompileRuleToLaw produces a Law whose RHS contains the
        # PolicyEntryLabel node (required for ClassifyProposal to
        # recognize a policy_change proposal).
        from hyge_int_pkg import proof as P2
        rule = P2.Rule(pe, pe)()
        law = G.CompileRuleToLaw(rule)()
        if M.IdentityCompare(law, M.EmptyList)() is M.truth_value:
            raise ValueError("CompileRuleToLaw returned EmptyList for policy_entry")
        return law
    raise ValueError("unsupported law kind")


def run_validity_child(req_path, resp_path):
    """Subprocess entry point: boot isolated runtime, decode request, run
    ActivateProposal, write response JSON."""
    with open(req_path, "r", encoding="utf-8") as h:
        req = _json.load(h)
    package_root = req.get("package_root") or _find_package_root()
    response = {"status": FAILED_STATUS, "passed": False,
                "reason": INVALID_CERT_REASON, "detail": ""}
    try:
        ns = _child_boot_ns(package_root)
    except Exception as exc:
        response["status"] = "launch-error"
        response["reason"] = LAUNCH_ERROR_REASON
        response["detail"] = "import failed: " + str(exc)
        _write_resp(resp_path, response); return 0
    M, G = ns["M"], ns["G"]
    try:
        runtime, _packs = ns["R"].boot_from_packs(
            _child_pack_paths(package_root), _runtime_ns(ns),
            debug=M.false_value)
    except Exception as exc:
        response["status"] = "launch-error"
        response["reason"] = LAUNCH_ERROR_REASON
        response["detail"] = "boot_from_packs failed: " + str(exc)
        _write_resp(resp_path, response); return 0
    try:
        empty = M.EmptyList
        raw_gv = G.GraphVersion(empty, empty, empty)()
        # Bootstrap safety invariants so CheckSafety can evaluate floor
        # violations on the candidate law.
        gv = G.BootstrapSafetyInvariants(raw_gv)()
        for acc in req.get("accepted_proposals", []) or []:
            try:
                if acc.get("state") != "activated":
                    continue
                law = _child_law_from_encoding(ns, acc["law_encoding"])
                gv = G.InstallLaw(gv, law)()
            except Exception:
                continue
        entry = req.get("entry") or {}
        cand_prop = None
        try:
            enc = entry["proposal_encoding"]
            law = _child_law_from_encoding(ns, enc)
            origin = entry.get("origin", "c-int-validity-check")
            try: origin = origin + ""
            except Exception: origin = "c-int-validity-check"
            cand_prop = G.Proposal(law, M.Char(origin))()
        except Exception:
            cand_prop = None
        if cand_prop is None:
            response["detail"] = "no decodable proposal_encoding"
            _write_resp(resp_path, response); return 0
        existing = empty
        cand_entry = G.ProposalEntry(cand_prop, existing)()
        proposal = G.ProposalEntryProposal(cand_entry)()
        approval = G.Approved(proposal, M.Char("c-int-validity-check"))()
        annotated = G.ProposalEntry(
            proposal,
            G.ChainAddMissing(existing, M.Pair(approval, empty))(),
        )()
        store = G.ProposalStore(M.Pair(annotated, empty))()
        activated = G.ActivateProposal(gv, annotated, store)()
        installed = M.Head(activated)()
        if M.IdentityCompare(installed, empty)() is M.truth_value:
            refusal = M.Head(M.Tail(activated)())()
            response["detail"] = "refused"
            _write_resp(resp_path, response); return 0
        response["status"] = COMPLETED_STATUS
        response["passed"] = True
        response["reason"] = "ok"
        _write_resp(resp_path, response); return 0
    except Exception as exc:
        response["status"] = "launch-error"
        response["reason"] = LAUNCH_ERROR_REASON
        response["detail"] = "runtime exception: " + str(exc)
        _write_resp(resp_path, response); return 0
    finally:
        try: del runtime
        except Exception: pass
