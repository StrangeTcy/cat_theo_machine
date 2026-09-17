"""Isolated check-only ActivateProposal validity gate (C-INT, slice 2026-09-16).

Boots an isolated runtime (fresh process-local heap; no shared mutable
state), attaches an Approved annotation to the candidate proposal entry,
calls graph.ActivateProposal(graph_version, approved_entry, proposal_store),
and accepts iff the returned installed_version is not EmptyList.

The isolated runtime is built from scratch on every call (via
runtime.boot_from_packs -> runtime.make_fresh_runtime), which resets
M.AllConstructors and creates a fresh Hypergraph; the runtime object is
discarded unconditionally after the check so no state leaks. There is
no reconciliation surface because check-only does not mutate durable
state and does not invoke any activation_fn (satisfies the forward
requirement from cint-integrated-4 review).

Fail-closed semantics:

  * If the isolated runtime cannot boot (packs missing, import error,
    runtime exception), raise F_LAUNCH_ERROR via the check raising --
    callers should halt and report rather than substituting a partial
    check. The factory returns a checker that raises BootError; tests
    may trap it.
  * If ActivateProposal returns EmptyList installed_version (rejected
    for any reason: unapproved/unsafe/uncountersigned), return False.
  * Unexpected exception -> return False (F_INVALID_CERT).
  * No structural/text fallback.

Entry keys:

  * entry["proposal_entry"]  - pre-built ProposalEntry term. The check
    will attach an additional Approved annotation (idempotent via
    ChainAddMissing) for check-only.
  * entry["proposal_term"]   - pre-built Proposal term; wrapped in a
    ProposalEntry with no existing annotations.
  * entry["proposal_text"]   - free text. The live path does NOT parse
    free text into laws; supplying only "proposal_text" fails closed
    with False unless the caller provides proposal_entry_constructor.

proposal_entry_constructor is TEST-ONLY: given (entry, ns) it returns a
ProposalEntry term. When absent (live-path default), only the two
term-bearing entry forms above are accepted; text-only entries fail
closed.
"""
from __future__ import annotations

import os


class BootError(RuntimeError):
    """Raised when the isolated runtime cannot be booted. Callers must
    HALT and report, not substitute a structural check."""


def _sync_constants(M, L=None):
    if "NatValueIndex" not in vars(M):
        M.NatValueIndex = M.Tree(M.EmptyList)
    out = {
        "Zero": M.Zero, "one": M.one, "two": M.two, "three": M.three,
        "four": M.four, "five": M.five, "six": M.six, "seven": M.seven,
        "eight": M.eight, "nine": M.nine,
        "NatValueIndex": M.NatValueIndex,
    }
    if L is not None:
        for n in ("ZeroLabel", "SuccLabel", "PairLabel", "TreeLabel"):
            if hasattr(L, n):
                out[n] = getattr(L, n)
    return out


def _default_pack_paths(package_root):
    pack_dir = os.path.join(package_root, "packs")
    names = [
        "order-sign.pack.yaml",
        "sqrt-real.pack.yaml",
        "algebra-distribute.pack.yaml",
        "sequence-order.pack.yaml",
        "real-closure.pack.yaml",
        "arithmetic.pack.yaml",
        "geometry-ontology.pack.yaml",
        "trigonometry.pack.yaml",
        "geometry.pack.yaml",
        "engel-coins.pack.yaml",
        "engel-means.pack.yaml",
        "engel-blackboard.pack.yaml",
        "number-theory.pack.yaml",
    ]
    return [os.path.join(pack_dir, n) for n in names]


def _install_accepted_proposals(G, M, graph_version, accepted_proposals):
    """Replay each previously-activated proposal_entry with InstallLaw
    into the isolated graph so ActivateProposal sees the actual accepted
    state (monotonic). Entries missing proposal_entry are skipped; this
    is conservative -- ActivateProposal will simply run against a
    smaller graph, which fails closed rather than spuriously accepting."""
    v = graph_version
    for e in accepted_proposals or ():
        if not isinstance(e, dict): continue
        if e.get("state") != "activated": continue
        entry = e.get("proposal_entry")
        if entry is None: continue
        try:
            proposal = G.ProposalEntryProposal(entry)()
            law = G.ProposalLaw(proposal)()
            v = G.InstallLaw(v, law)()
        except Exception:
            continue
    return v


def make_activate_proposal_validity_check(package_root=None, pack_paths=None,
                                           proposal_entry_constructor=None):
    """Return a validity check callable:
        (entry, accepted_proposals, accepted_state_version) -> bool
    Raises BootError if the isolated runtime cannot be booted (caller
    must halt, not fall back)."""
    # Import the hyge stack once per factory -- the boot call rebuilds a
    # fresh runtime (fresh Hypergraph + registry) on each invocation so
    # state does not leak across calls.
    from hyge_int_pkg import (
        machine as M, graph as G, runtime as R, labels as L,
        heuristics as H, constructors as C, programme_c as P,
    )
    _sync_constants(M, L)

    if package_root is None:
        here = os.path.abspath(__file__)
        package_root = os.path.abspath(os.path.join(os.path.dirname(here), ".."))
    if pack_paths is None:
        pack_paths = _default_pack_paths(package_root)
    for p in pack_paths:
        if not os.path.isfile(p):
            raise BootError("pack file missing: " + p)

    def _check(entry, accepted_proposals, accepted_state_version):
        # Fresh isolated runtime per call. boot_from_packs calls
        # make_fresh_runtime which rebuilds constructors/Hypergraph
        # from scratch, so prior installs from previous checks do not
        # leak across calls.
        try:
            runtime, _packs = R.boot_from_packs(
                list(pack_paths), _runtime_namespace(M, G, H, L, P, R, C),
                debug=M.false_value)
        except Exception as exc:
            raise BootError("failed to boot isolated runtime: " + str(exc))
        try:
            empty = M.EmptyList
            # Starting GraphVersion: empty nodes/edges/invariants. Note
            # that pack booting loads rules/constructors into the graph
            # but does not populate the GraphVersion term (GraphVersion
            # is a separate term threaded through install operations).
            gv = G.GraphVersion(empty, empty, empty)()
            gv = _install_accepted_proposals(G, M, gv, accepted_proposals)

            cand_entry = None
            if isinstance(entry, dict):
                cand_entry = entry.get("proposal_entry")
                cand_prop = entry.get("proposal_term")
                if cand_entry is None and cand_prop is None and proposal_entry_constructor is not None:
                    try:
                        cand_entry = proposal_entry_constructor(entry, {
                            "M": M, "G": G, "L": L, "P": P,
                        })
                    except Exception:
                        cand_entry = None
                if cand_entry is None and cand_prop is not None:
                    cand_entry = G.ProposalEntry(cand_prop, empty)()
            if cand_entry is None:
                return False

            proposal = G.ProposalEntryProposal(cand_entry)()
            existing = G.ProposalEntryAnnotations(cand_entry)()
            approval = G.Approved(proposal, M.Char("c-int-validity-check"))()
            annotated = G.ProposalEntry(
                proposal,
                G.ChainAddMissing(existing, M.Pair(approval, empty))(),
            )()
            store = G.ProposalStore(M.Pair(annotated, empty))()
            activated = G.ActivateProposal(gv, annotated, store)()
            installed = M.Head(activated)()
            # installed != EmptyList -> ActivateProposal produced a next
            # version (law installed). That is the validity pass.
            return M.IdentityCompare(installed, empty)() is not M.truth_value
        except BootError:
            raise
        except Exception:
            return False
        finally:
            del runtime

    return _check


def _runtime_namespace(M, G, H, L, P, R, C):
    ns = {}
    for mod in (M, G, H, L, P, R, C):
        ns.update(vars(mod))
    ns.update(_sync_constants(M, L))
    # Populate additional modules that packs may reference.
    try:
        from hyge_int_pkg import (
            symbols as S, rewrite_rules as X, session as T,
        )
        ns.update(vars(S)); ns.update(vars(X)); ns.update(vars(T))
    except Exception:
        pass
    return ns


def make_failing_activate_proposal_check():
    """Explicit fail-closed sentinel for environments where boot is
    impossible (e.g., pack files unavailable). This never accepts; the
    caller is expected to HALT and report rather than substitute."""
    def _check(entry, accepted, version):
        return False
    return _check
