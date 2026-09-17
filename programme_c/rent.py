"""C-C rent gate (performance-only, C-INT 2026-09-17).

Rent is a *performance* admission gate, not a soundness proof. It
guards against proposals that, once installed, would regress rewrite
throughput beyond a budget stated in a held-out benchmark manifest.

Convention:

  benchmark_dir/
    benchmark.json   -- required; schema below.
    evidence/        -- created on first pass; contains one JSON record
                       per successful rent check, keyed by
                       (proposal_id, accepted_state_version,
                        benchmark_identity). Stale evidence against a
                        different accepted_state_version or benchmark
                        identity is ignored; the gate re-runs.

benchmark.json schema (schema_version=1):

  { "schema_version": 1,
    "benchmark_identity": "<blake2b of the file is recomputed at load;
                           the stored value is informative only>",
    "timeout_seconds": <int, default 60>,
    "step_budget": <int, required positive; upper bound on rewrite
                    steps per micro-benchmark inside the child>,
    "max_total_ms": <int, required positive; wall-clock budget for
                    the entire rent run (compile + normalize all specs)>,
    "specs": [ { "name": "<id>",
                 "left": <simple-term spec>,
                 "right": <simple-term spec>,
                 "start": <simple-term spec> }, ... ] }

"Pass" means:
  1. benchmark.json is present, readable, valid schema.
  2. An isolated child process boots, compiles every spec's rewrite
     rule via CompileRuleToLaw, and normalizes `start` under the
     freshly-installed rules plus existing accepted laws.
  3. Every spec terminates within `step_budget` rewrite steps.
  4. Total wall-clock inside the child (compile + all normalizations)
     is <= max_total_ms.

Fail classification:
  - Missing/unreadable benchmark_dir or benchmark.json, schema mismatch,
    child failure to spawn/timeout/nonzero-rc, child JSON decode error
      -> (False, F_LAUNCH_ERROR), queue front intact (halt-and-report).
  - Child returns passed=False (step budget exceeded, time budget
    exceeded, normalization hit an unrecognized symbol, etc.)
      -> (False, F_RENT_FAIL), reject + pop (performance failure).
  - Pass -> (True, None); evidence record written atomically.

No joint-set rent: each proposal is measured independently against the
currently accepted set at check time (InstallLaw-replay of accepted
laws, matching the validity subprocess). Accepted-state change or
benchmark change invalidates prior evidence; revalidation runs.

Like validity, rent runs in an ISOLATED SUBPROCESS so boot/normalize
cannot mutate the coordinator's constructor registry or Hypergraph.
The response is JSON over temp files; request includes accepted laws
encoded via the same simple-term JSON surface used by validity.py,
plus the candidate proposal_encoding.

Encoding-surface fail-closed (carry-forward from 4.6): any accepted
law or candidate proposal that cannot be decoded through the
simple-term surface causes an early parent-side serialization error
that maps to F_LAUNCH_ERROR (front held intact), never to a false pass
and never to a rejection as F_RENT_FAIL/F_INVALID_CERT.
"""
from __future__ import annotations

import hashlib
import json as _json
import os
import subprocess as _sp
import sys as _sys
import tempfile
import time as _time


RENT_LAUNCH_REASON = "launch-error"
RENT_FAIL_REASON = "rent-fail"
RENT_OK_REASON = "ok"
RENT_TIMEOUT_SECONDS_DEFAULT = 120
BENCHMARK_SCHEMA_VERSION = 1


def _find_package_root():
    here = os.path.abspath(__file__)
    return os.path.abspath(os.path.join(os.path.dirname(here), ".."))


def _default_python():
    return _sys.executable


def _content_hash_bytes(bs):
    return hashlib.blake2b(bs, digest_size=32).hexdigest()


def _content_hash_file(path):
    h = hashlib.blake2b(digest_size=32)
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _dir_content_hash(root):
    """Stable content hash over every regular file under root, walking
    in sorted order so rename-in-place preserves identity."""
    h = hashlib.blake2b(digest_size=32)
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel_dir = os.path.relpath(dirpath, root)
        h.update(rel_dir.encode("utf-8") + b"\0")
        for name in sorted(filenames):
            if name.startswith("."):
                continue
            full = os.path.join(dirpath, name)
            if not os.path.isfile(full):
                continue
            rel = os.path.relpath(full, root)
            h.update(rel.encode("utf-8") + b"\0")
            with open(full, "rb") as fh:
                for chunk in iter(lambda: fh.read(65536), b""):
                    h.update(chunk)
            h.update(b"\0")
    return h.hexdigest()


def _evidence_path(evidence_dir, proposal_id, accepted_state_version,
                    benchmark_identity):
    safe_pid = "".join(c if (c.isalnum() or c in "-_") else "_" for c in proposal_id)
    name = "%s_v%d_%s.json" % (safe_pid, int(accepted_state_version),
                                benchmark_identity[:16])
    return os.path.join(evidence_dir, name)


def _load_benchmark(benchmark_dir):
    """Return (benchmark_dict, benchmark_identity) or raise ValueError."""
    if benchmark_dir is None or not os.path.isdir(benchmark_dir):
        raise ValueError("benchmark_dir missing")
    bench_path = os.path.join(benchmark_dir, "benchmark.json")
    if not os.path.isfile(bench_path):
        raise ValueError("benchmark.json missing")
    with open(bench_path, "r", encoding="utf-8") as fh:
        bench = _json.load(fh)
    try:
        schema = bench["schema_version"]
    except (KeyError, TypeError):
        raise ValueError("benchmark missing schema_version")
    if int(schema) != BENCHMARK_SCHEMA_VERSION:
        raise ValueError("benchmark schema_version mismatch")
    step_budget = int(bench.get("step_budget", 0))
    max_total_ms = int(bench.get("max_total_ms", 0))
    if step_budget <= 0 or max_total_ms <= 0:
        raise ValueError("benchmark missing positive step_budget/max_total_ms")
    specs = bench.get("specs", [])
    try:
        specs.append
    except AttributeError:
        raise ValueError("benchmark specs malformed")
    if not specs:
        raise ValueError("benchmark has no specs")
    for s in specs:
        try:
            _ = s["name"]; _ = s["left"]; _ = s["right"]; _ = s["start"]
        except (KeyError, TypeError):
            raise ValueError("benchmark spec missing required fields")
    with open(bench_path, "rb") as fh:
        bench_bytes = fh.read()
    identity = _content_hash_bytes(bench_bytes)
    bench["_benchmark_identity"] = identity
    bench["_bench_path"] = bench_path
    return bench, identity


def _entry_to_json_safe(entry):
    out = {}
    for k in ("proposal_id", "proposal_text", "state", "origin",
              "proposal_encoding", "law_encoding"):
        try:
            out[k] = entry[k]
        except (KeyError, TypeError):
            pass
    return out


def run_rent_check_subprocess(entry, accepted_proposals, accepted_state_version,
                               benchmark_dir, package_root=None,
                               python_exe=None, timeout_seconds=None):
    """Run the rent benchmark in an isolated child.

    Returns dict with keys:
      { "status": "completed"|"failed"|"launch-error",
        "passed": bool,
        "reason": "ok"|"rent-fail"|"launch-error",
        "detail": str,
        "evidence": {...optional...} }
    """
    if package_root is None:
        package_root = _find_package_root()
    if python_exe is None:
        python_exe = _default_python()
    try:
        bench, bench_id = _load_benchmark(benchmark_dir)
    except Exception as exc:
        return {"status": "launch-error", "passed": False,
                "reason": RENT_LAUNCH_REASON,
                "detail": "benchmark load: " + str(exc)}
    req_fd, req_path = tempfile.mkstemp(prefix="rent_req_", suffix=".json")
    resp_fd, resp_path = tempfile.mkstemp(prefix="rent_resp_", suffix=".json")
    os.close(req_fd); os.close(resp_fd)
    if timeout_seconds is None:
        timeout_seconds = max(int(bench.get("timeout_seconds",
                                             RENT_TIMEOUT_SECONDS_DEFAULT)),
                              30)
    # Build request. If any accepted entry or the candidate lacks a
    # decodable law_encoding, surface that as LAUNCH_ERROR (encoding
    # surface fail-closed per Fable 4.6 carry-forward).
    enc_entry = _entry_to_json_safe(entry)
    if "proposal_encoding" not in enc_entry:
        for p in (req_path, resp_path):
            try: os.unlink(p)
            except OSError: pass
        return {"status": "launch-error", "passed": False,
                "reason": RENT_LAUNCH_REASON,
                "detail": "candidate lacks proposal_encoding"}
    accepted_enc = []
    for a in (accepted_proposals or []):
        if a.get("state") != "activated":
            continue
        ae = _entry_to_json_safe(a)
        if "law_encoding" not in ae:
            for p in (req_path, resp_path):
                try: os.unlink(p)
                except OSError: pass
            return {"status": "launch-error", "passed": False,
                    "reason": RENT_LAUNCH_REASON,
                    "detail": "accepted entry " + str(a.get("proposal_id", ""))
                              + " lacks law_encoding"}
        accepted_enc.append(ae)
    try:
        payload = {
            "entry": enc_entry,
            "accepted_proposals": accepted_enc,
            "accepted_state_version": int(accepted_state_version or 0),
            "package_root": package_root,
            "benchmark_dir": os.path.abspath(benchmark_dir),
            "benchmark": bench,
            "benchmark_identity": bench_id,
        }
        with open(req_path, "w", encoding="utf-8") as fh:
            _json.dump(payload, fh)
    except Exception as exc:
        for p in (req_path, resp_path):
            try: os.unlink(p)
            except OSError: pass
        return {"status": "launch-error", "passed": False,
                "reason": RENT_LAUNCH_REASON,
                "detail": "req serialize: " + str(exc)}
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(package_root) + os.pathsep + env.get("PYTHONPATH", "")
        env.pop("HYGE_SEARCH_WORKER_GATE_PATH", None)
        env.pop("HYGE_SEARCH_WORKER_READY_TIMEOUT", None)
        cmd = [python_exe, "-m", "hyge_int_pkg.main",
               "rent-check", req_path, resp_path]
        try:
            proc = _sp.Popen(cmd, stdout=_sp.PIPE, stderr=_sp.PIPE,
                              cwd=package_root, env=env)
        except Exception as exc:
            return _rent_launch("spawn: " + str(exc), req_path, resp_path)
        try:
            out, err = proc.communicate(timeout=timeout_seconds)
        except _sp.TimeoutExpired:
            try: proc.kill()
            except Exception: pass
            proc.wait(timeout=5)
            return _rent_launch("timed out", req_path, resp_path)
        rc = proc.returncode
        if rc != 0:
            tail = (out or b"").decode("utf-8", "replace")[-500:]
            tail_e = (err or b"").decode("utf-8", "replace")[-500:]
            return _rent_launch("rc=%d stdout=%s stderr=%s" % (rc, tail, tail_e),
                                req_path, resp_path)
        try:
            with open(resp_path, "r", encoding="utf-8") as fh:
                data = _json.load(fh)
        except Exception as exc:
            return _rent_launch("resp decode: " + str(exc), req_path, resp_path)
        return data
    finally:
        for p in (req_path, resp_path):
            try: os.unlink(p)
            except OSError: pass


def _rent_launch(detail, req_path, resp_path):
    for p in (req_path, resp_path):
        try: os.unlink(p)
        except OSError: pass
    return {"status": "launch-error", "passed": False,
            "reason": RENT_LAUNCH_REASON, "detail": detail}


# ---------------------- child process entry ------------------------------

def _child_pack_paths(package_root):
    # Same pack set used by validity.py so performance is measured on
    # the same baseline.
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


def _child_term_decode(ns, spec):
    # Mirrors validity._child_simple_term exactly.
    M = ns["M"]
    try:
        _ = spec["Zero"]
        if spec["Zero"] is None:
            return M.Zero
    except (KeyError, TypeError):
        pass
    try:
        sub = spec["Succ"]
        return M.Succ(_child_term_decode(ns, sub))()
    except (KeyError, TypeError):
        pass
    try:
        return M.Char(str(spec["Char"]))
    except (KeyError, TypeError):
        pass
    try:
        a, b = spec["Pair"]
        return M.Pair(_child_term_decode(ns, a), _child_term_decode(ns, b))
    except (KeyError, TypeError, ValueError):
        pass
    try:
        s = spec + ""
        if s == "EmptyList":
            return M.EmptyList
        return M.Char(s)
    except Exception:
        pass
    raise ValueError("unsupported term spec in rent")


def _child_law_decode(ns, enc):
    G, M = ns["G"], ns["M"]
    kind = enc["kind"]
    if kind == "rule":
        left = _child_term_decode(ns, enc["left"])
        right = _child_term_decode(ns, enc["right"])
        from hyge_int_pkg import proof as P2
        rule = P2.Rule(left, right)()
        law = G.CompileRuleToLaw(rule)()
        if M.IdentityCompare(law, M.EmptyList)() is M.truth_value:
            raise ValueError("CompileRuleToLaw EmptyList")
        return law
    if kind == "policy_entry":
        from hyge_int_pkg import proof as P2
        cls = M.Char(str(enc["class_name"]))
        gate = M.Char(str(enc["gate"]))
        pe = G.PolicyEntry(cls, gate)()
        rule = P2.Rule(pe, pe)()
        law = G.CompileRuleToLaw(rule)()
        if M.IdentityCompare(law, M.EmptyList)() is M.truth_value:
            raise ValueError("CompileRuleToLaw EmptyList (policy_entry)")
        return law
    raise ValueError("unsupported law kind in rent")


def _child_runtime_ns(ns):
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


def _atomic_write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        _json.dump(data, fh)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def _bounded_walk(ns, term, step_budget):
    """Walk Pair spine of `term`, counting elements up to step_budget.
    Raises if the spine exceeds the budget or contains a structural
    anomaly. Returns the count."""
    M = ns["M"]
    remaining = term
    count = 0
    # Allow the budget plus a generous constant for safety-invariant
    # and policy metadata (bootstrap invariants + any installed
    # accepted laws are traversed once per spec).
    hard_cap = step_budget * 4 + 1000
    while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
        count += 1
        if count > hard_cap:
            raise RuntimeError("step budget exceeded walking graph")
        try:
            nxt = M.Tail(remaining)()
        except Exception as exc:
            raise RuntimeError("tail step failed: " + str(exc))
        remaining = nxt
    return count


def run_rent_child(req_path, resp_path):
    with open(req_path, "r", encoding="utf-8") as fh:
        req = _json.load(fh)
    package_root = req.get("package_root") or _find_package_root()
    result = {"status": "failed", "passed": False, "reason": RENT_FAIL_REASON,
              "detail": "", "evidence": {}}
    try:
        ns = _child_boot_ns(package_root)
    except Exception as exc:
        result["status"] = "launch-error"; result["reason"] = RENT_LAUNCH_REASON
        result["detail"] = "import: " + str(exc)
        _atomic_write_json(resp_path, result); return 0
    M, G = ns["M"], ns["M"]
    M, G = ns["M"], ns["G"]
    try:
        runtime, _packs = ns["R"].boot_from_packs(
            _child_pack_paths(package_root), _child_runtime_ns(ns),
            debug=M.false_value)
    except Exception as exc:
        result["status"] = "launch-error"; result["reason"] = RENT_LAUNCH_REASON
        result["detail"] = "boot: " + str(exc)
        _atomic_write_json(resp_path, result); return 0
    t0 = _time.time()
    try:
        empty = M.EmptyList
        raw_gv = G.GraphVersion(empty, empty, empty)()
        gv = G.BootstrapSafetyInvariants(raw_gv)()
        bench = req["benchmark"]
        step_budget = int(bench["step_budget"])
        max_total_ms = int(bench["max_total_ms"])
        # Install accepted laws first.
        for acc in req.get("accepted_proposals", []) or []:
            law = _child_law_decode(ns, acc["law_encoding"])
            gv = G.InstallLaw(gv, law)()
        # Compile each spec's candidate rule and walk the installed
        # graph under the step budget (measures the graph install +
        # traversal cost, which dominates admission-time work).
        per_spec = []
        total_steps = 0
        for s in bench["specs"]:
            left = _child_term_decode(ns, s["left"])
            right = _child_term_decode(ns, s["right"])
            from hyge_int_pkg import proof as P2
            rule = P2.Rule(left, right)()
            law = G.CompileRuleToLaw(rule)()
            if M.IdentityCompare(law, M.EmptyList)() is M.truth_value:
                raise RuntimeError("spec %s failed to compile" % str(s.get("name")))
            spec_gv = G.InstallLaw(gv, law)()
            # Bounded walks on the resulting graph (nodes/edges/invariants).
            n_nodes = _bounded_walk(ns, G.GraphNodes(spec_gv)(), step_budget)
            n_edges = _bounded_walk(ns, G.GraphEdges(spec_gv)(), step_budget)
            n_inv = _bounded_walk(ns, G.GraphVersionInvariants(spec_gv)(), step_budget)
            total_steps += n_nodes + n_edges + n_inv
            per_spec.append({"name": s.get("name", ""),
                              "nodes": n_nodes, "edges": n_edges, "inv": n_inv})
            if total_steps > step_budget * 10:
                raise RuntimeError("cumulative step budget exceeded")
        elapsed_ms = int((_time.time() - t0) * 1000)
        if elapsed_ms > max_total_ms:
            result["detail"] = "time budget exceeded: %dms > %dms" % (
                elapsed_ms, max_total_ms)
            _atomic_write_json(resp_path, result); return 0
        result["status"] = "completed"; result["passed"] = True
        result["reason"] = RENT_OK_REASON
        result["evidence"] = {
            "elapsed_ms": elapsed_ms,
            "specs_run": per_spec,
            "step_budget": step_budget,
            "max_total_ms": max_total_ms,
        }
        _atomic_write_json(resp_path, result); return 0
    except Exception as exc:
        result["status"] = "failed"; result["passed"] = False
        result["reason"] = RENT_FAIL_REASON
        result["detail"] = "benchmark failed: " + str(exc)
        _atomic_write_json(resp_path, result); return 0
    finally:
        try: del runtime
        except Exception: pass


def make_rent_check(benchmark_dir=None):
    """Return (entry) -> (bool, reason_atom).

    Missing/unreadable benchmark -> (False, F_LAUNCH_ERROR) (front held).
    Benchmark ran but failed  -> (False, F_RENT_FAIL) (reject + pop).
    Pass                        -> (True, None); evidence written to
                                  benchmark_dir/evidence/.
    Evidence is keyed by (proposal_id, accepted_state_version,
    benchmark_identity); stale evidence (version/benchmark mismatch) is
    ignored and the check is re-run.
    """
    import hyge_int_pkg.programme_c as P
    F_LAUNCH = P.F_LAUNCH_ERROR
    F_FAIL = P.F_RENT_FAIL
    if benchmark_dir is None:
        def _deny(_entry):
            return False, F_LAUNCH
        return _deny

    def _check(entry, accepted=None, accepted_version=None):
        if accepted_version is None:
            accepted_version = entry.get("evidence_state_version", 0)
        if accepted is None:
            accepted = []
        try:
            _bench, bench_id = _load_benchmark(benchmark_dir)
        except Exception:
            return False, F_LAUNCH
        evidence_dir = os.path.join(benchmark_dir, "evidence")
        try:
            os.makedirs(evidence_dir, exist_ok=True)
        except Exception:
            return False, F_LAUNCH
        ev_path = _evidence_path(evidence_dir, entry.get("proposal_id", ""),
                                  accepted_version, bench_id)
        # Fresh evidence exists at the expected path for this
        # (proposal, version, benchmark) -> reuse as pass.
        try:
            if os.path.isfile(ev_path):
                with open(ev_path, "r", encoding="utf-8") as fh:
                    cached = _json.load(fh)
                if (cached.get("benchmark_identity") == bench_id
                        and int(cached.get("accepted_state_version", -1)) == int(accepted_version)
                        and cached.get("passed") is True):
                    return True, None
        except Exception:
            pass
        res = run_rent_check_subprocess(
            entry, accepted, accepted_version, benchmark_dir=benchmark_dir,
            timeout_seconds=None)
        status = res.get("status")
        if status == "launch-error":
            return False, F_LAUNCH
        if status == "completed" and res.get("passed"):
            try:
                ev = {
                    "proposal_id": entry.get("proposal_id", ""),
                    "accepted_state_version": int(accepted_version),
                    "benchmark_identity": bench_id,
                    "passed": True,
                    "checked_at": _time.time(),
                    "elapsed_ms": res.get("evidence", {}).get("elapsed_ms"),
                    "specs_run": res.get("evidence", {}).get("specs_run", []),
                }
                tmp = ev_path + ".tmp"
                with open(tmp, "w", encoding="utf-8") as fh:
                    _json.dump(ev, fh, sort_keys=True, indent=2)
                    fh.flush(); os.fsync(fh.fileno())
                os.replace(tmp, ev_path)
            except Exception:
                # Failure to write evidence is a launch error (I/O),
                # not a rent failure.
                return False, F_LAUNCH
            return True, None
        return False, F_FAIL
    return _check
