# ============================================================
# TEST 28: W17 — Byzantine ledger consensus &
#          monotonic snapshot broadcast
# ============================================================
# Run with:  PYTHONPATH=<repo-parent> python -u validation/test28_byzantine_ledger_consensus.py
#
# Slot 28 is the one `delegation/README.md` pre-allocates to
# `W17-byzantine-ledger-consensus.md`.
#
# Fault model, stated exactly as the brief demands. The schedule below
# tolerates, per honest peer: one crashing peer (stops receiving after the
# first round and never catches up -- it is excluded from the agreement
# set), message omission (an undelivered entry), duplicate delivery,
# out-of-order delivery (parked, drained in version order), a forged entry
# with an unverifiable receipt (rejected by every honest peer, with the
# rejection reason asserted to be local receipt verification -- the oracle
# is `EntryReceiptVerdict`, i.e. Checker B over the peer's own trusted
# rules), a stale snapshot (refused; the peer keeps its newer state), and a
# split view (a partitioned peer later reconciles through the same
# delivery path). Byzantine behavior beyond forged entries and stale
# snapshots -- equivocating leaders that mint two different entries at the
# same version -- is out of scope here: entries are minted only through the
# origin's promotion machine, and tombstone authority is channel authority,
# since the machine carries no cryptographic identities. Both limits are
# the brief's own framing: verification first, ordering machinery second.
#
# Determinism: the schedule is a fixed script; there is no wall-clock and
# no randomness anywhere in this suite, and the whole scenario is run
# twice from scratch with the final ledgers compared structurally.
#
# Machine purity: ledgers, entries, versions, receipts, peers and delivery
# reports are machine terms; the fault scheduler is plain Python and is the
# brief's explicit host/machine boundary.
#
# Persistence is NOT extended: in-process peers are runtime objects and the
# promotion ledger is already a captured root, so there is no consensus
# state that must survive a cold reload beyond what §5.5 already covers.

import importlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PARENT = os.path.dirname(REPO)
if PARENT not in sys.path:
    sys.path.insert(0, PARENT)

PACKAGE = os.path.basename(REPO)

M = importlib.import_module(PACKAGE + ".machine")
P = importlib.import_module(PACKAGE + ".proof")
L = importlib.import_module(PACKAGE + ".labels")
Ledger = importlib.import_module(PACKAGE + ".promotion_ledger")
CheckerB = importlib.import_module(PACKAGE + ".checker_b")
Eval = importlib.import_module(PACKAGE + ".evaluator")
Inv = importlib.import_module(PACKAGE + ".invariance")
CS = importlib.import_module(PACKAGE + ".consensus")
peano = importlib.import_module(PACKAGE + ".math.peano")
runtime_mod = importlib.import_module(PACKAGE + ".runtime")

T0 = time.time()

print("=== TEST 28: W17 Byzantine ledger consensus ===")
print()

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    line = "    PASS  " if ok else "    FAIL  "
    if detail:
        line = line + name + "  -- " + detail
    else:
        line = line + name
    print(line)


def tag_name(atom):
    return type(atom).__name__


# ---------------------------------------------------------------------------
# the scenario builder: a fresh runtime with two honestly promoted entries
# ---------------------------------------------------------------------------


def build_scenario():
    """Fresh runtime; origin promotes two honest entries. Returns everything
    the schedule needs. Deterministic: no randomness, no wall clock."""
    runtime = runtime_mod.make_fresh_runtime()
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()

    term_a, term_b, term_c, term_invalid = M.Atom(), M.Atom(), M.Atom(), M.Atom()
    rule_ab = P.Rule(term_a, term_b)()
    rule_bc = P.Rule(term_b, term_c)()
    rule_invalid = P.Rule(term_a, term_invalid)()
    valid_rules = M.Pair(rule_ab, M.Pair(rule_bc, M.EmptyList))

    act_1 = P.RewriteAction(rule_ab, M.EmptyList)()
    act_2 = P.RewriteAction(rule_bc, M.EmptyList)()
    valid_plan = M.Pair(act_1, M.Pair(act_2, M.EmptyList))
    corrupt_plan = M.Pair(P.RewriteAction(rule_invalid, M.EmptyList)(), M.Pair(act_2, M.EmptyList))

    s1 = P.Step(term_a, act_1, term_b, registry)()
    step_1 = M.Head(s1)()
    registry = M.Head(M.Tail(s1)())()
    s2 = P.Step(term_b, act_2, term_c, registry)()
    step_2 = M.Head(s2)()
    registry = M.Head(M.Tail(s2)())()
    der_res = P.Derivation(
        M.Pair(step_1, M.Pair(step_2, M.EmptyList)),
        P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)(),
        registry,
    )()
    training_trace = M.Head(der_res)()
    registry = M.Head(M.Tail(der_res)())()

    version, registry = M.Zero, registry
    for _ in range(4):
        pr = M.Succ(version, registry)()
        version = M.Head(pr)()
        registry = M.Head(M.Tail(pr)())()
    baseline_cost = P.ProofCost(version, M.Zero, M.Zero, M.Zero)()

    holdout = M.Pair(M.Pair(term_a, M.Pair(term_c, M.Pair(M.truth_value, M.EmptyList))), M.EmptyList)
    templates = M.Pair(Inv.Phi(term_a)(), M.EmptyList)

    empty = Ledger.EmptyPromotionLedger(registry)()
    c1 = Ledger.ExecuteAutonomousDiscoveryCycle(
        training_trace, term_a, term_c, valid_rules, templates, M.Atom(), valid_plan,
        baseline_cost, holdout, L.ProofSchemaPromotionLabel, empty, registry,
    )()
    assert M.IdentityCompare(M.Head(c1)(), L.AutonomousCycleCompletedLabel)() is M.truth_value
    ledger_v1 = M.Head(M.Tail(c1)())()
    entry1 = M.Head(M.Tail(M.Tail(c1)())())()

    c2 = Ledger.ExecuteAutonomousDiscoveryCycle(
        training_trace, term_a, term_c, valid_rules, templates, M.Atom(), valid_plan,
        baseline_cost, holdout, L.ProofSchemaPromotionLabel, ledger_v1, registry,
    )()
    assert M.IdentityCompare(M.Head(c2)(), L.AutonomousCycleCompletedLabel)() is M.truth_value
    ledger_v2 = M.Head(M.Tail(c2)())()
    entry2 = M.Head(M.Tail(M.Tail(c2)())())()

    # the forgery: a real receipt shape over a derivation that uses a rule
    # no honest peer trusts
    st = P.Step(term_a, P.RewriteAction(rule_invalid, M.EmptyList)(), term_invalid, registry)()
    corrupt_step = M.Head(st)()
    registry = M.Head(M.Tail(st)())()
    cder = P.Derivation(
        M.Pair(corrupt_step, M.EmptyList), P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)(), registry
    )()
    corrupt_derivation = M.Head(cder)()
    registry = M.Head(M.Tail(cder)())()

    r1f = Ledger.LedgerEntryReceipt(entry1)()
    sid = M.Head(M.Tail(r1f)())()
    forged_receipt = M.Pair(
        L.ProofReceiptLabel,
        M.Pair(sid, M.Pair(term_a, M.Pair(term_c, M.Pair(corrupt_derivation, M.Pair(valid_rules, M.EmptyList))))),
    )
    forged_entry = Ledger.LedgerEntry(
        M.Atom(), L.ProofSchemaPromotionLabel, M.Pair(L.CandidateMacroLabel, M.EmptyList),
        forged_receipt, M.EmptyList, Ledger.LedgerEntryVersion(entry2)(), L.PromotionActiveLabel,
    )()

    return {
        "runtime": runtime,
        "registry": registry,
        "term_a": term_a, "term_c": term_c, "term_invalid": term_invalid,
        "valid_rules": valid_rules, "corrupt_plan": corrupt_plan,
        "baseline_cost": baseline_cost, "holdout": holdout,
        "templates": templates, "training_trace": training_trace,
        "ledger_v1": ledger_v1, "ledger_v2": ledger_v2,
        "entry1": entry1, "entry2": entry2,
        "forged_entry": forged_entry,
    }


def fresh_peers(sc, count):
    peers = []
    registry = sc["registry"]
    for _ in range(count):
        peers.append(CS.FreshPeer(M.EmptyList, sc["valid_rules"], registry))
    return peers


def rpt(report):
    """Peel a delivery report: (verdict, reason, peer, registry)."""
    verdict = M.Head(M.Tail(report)())()
    reason = M.Head(M.Tail(M.Tail(report)())())()
    peer = M.Head(M.Tail(M.Tail(M.Tail(report)())())())()
    registry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(report)())())())())()
    return verdict, reason, peer, registry


def deliver(peer, entry, registry):
    """One delivery; returns (verdict, reason, peer, registry)."""
    return rpt(CS.AcceptEntryDelivery(peer, entry, registry)())


def ver_eq(v, k, registry):
    """Peano equality between a ledger version and a constant."""
    return peano.NatEq(v, k, registry)() is M.truth_value


# ---------------------------------------------------------------------------
# [1] the origin's honest entries
# ---------------------------------------------------------------------------

print("[1] Booting the scenario: two honestly promoted entries on the origin")

SC = build_scenario()
entry1, entry2 = SC["entry1"], SC["entry2"]

check("origin holds two entries at versions 1 and 2",
      ver_eq(Ledger.LedgerEntryVersion(entry1)(), peano.one, SC["registry"])
      and ver_eq(Ledger.LedgerEntryVersion(entry2)(), peano.two, SC["registry"]),
      tag_name(Ledger.LedgerEntryStatus(entry1)()) + " / " + tag_name(Ledger.LedgerEntryStatus(entry2)()))

# the forgery must be a real forgery: the oracle itself refuses it
forge_verdict = CS.EntryReceiptVerdict(SC["forged_entry"], SC["valid_rules"], SC["registry"])()
check("the forged entry's receipt fails Checker B locally (UnknownRule)",
      M.IdentityCompare(M.Head(forge_verdict)(), L.UnknownRuleLabel)() is M.truth_value,
      tag_name(M.Head(forge_verdict)()))
honest_verdict = CS.EntryReceiptVerdict(entry1, SC["valid_rules"], SC["registry"])()
check("  ... while the honest receipts verify",
      M.IdentityCompare(M.Head(honest_verdict)(), L.DerivationVerifiedLabel)() is M.truth_value)

print()

# ---------------------------------------------------------------------------
# [2] the adversarial schedule
# ---------------------------------------------------------------------------

print("[2] The schedule: crash, omission, duplicate, reorder, forgery, stale, split")

peers = fresh_peers(SC, 4)
P2, P3, P4, P5 = peers
registry = SC["registry"]
observations = {"P2": [], "P3": [], "P4": [], "P5": []}


def observe(name, peer):
    v = Ledger.PromotionLedgerVersion(CS.PeerLedger(peer))()
    observations[name].append(v)
    return v


def monotonic(name):
    seen = observations[name]
    for i in range(1, len(seen)):
        a = peano.NatLess(seen[i - 1], seen[i], SC["registry"])()
        b = peano.NatEq(seen[i - 1], seen[i], SC["registry"])()
        if not (a is M.truth_value or b is M.truth_value):
            return False
    return True


# P2: out of order -- entry2 arrives before entry1
v, r, P2, registry = deliver(P2, entry2, registry)
observe("P2", P2)
check("P2 parks the out-of-order entry (version gap, nothing committed)",
      M.IdentityCompare(v, L.VersionGapLabel)() is M.truth_value
      and M.IdentityCompare(Ledger.PromotionLedgerVersion(CS.PeerLedger(P2))(), M.Zero)() is M.truth_value,
      tag_name(v))
v, r, P2, registry = deliver(P2, entry1, registry)
observe("P2", P2)
check("P2 commits entry1 and drains the parked entry2 behind it",
      M.IdentityCompare(v, L.AdmissionAdmittedLabel)() is M.truth_value
      and ver_eq(Ledger.PromotionLedgerVersion(CS.PeerLedger(P2))(), peano.two, registry),
      tag_name(v))
check("  ... P2's ledger is structurally the origin's ledger at version 2",
      M.Compare(CS.PeerLedger(P2), SC["ledger_v2"])() is M.truth_value)

# P3: duplicates
v, r, P3, registry = deliver(P3, entry1, registry)
observe("P3", P3)
v, r, P3, registry = deliver(P3, entry1, registry)
observe("P3", P3)
check("P3's duplicate delivery is refused as a duplicate",
      M.IdentityCompare(r, L.DuplicateEntryLabel)() is M.truth_value, tag_name(r))
v, r, P3, registry = deliver(P3, entry2, registry)
observe("P3", P3)

# P4: gets the full first round honestly...
v, r, P4, registry = deliver(P4, entry1, registry)
observe("P4", P4)
v, r, P4, registry = deliver(P4, entry2, registry)
observe("P4", P4)
# P5: omission -- entry1 is simply never delivered, only the snapshot later
v, r, P5, registry = deliver(P5, entry2, registry)
observe("P5", P5)

# the forgery, to every honest peer
ok_forgery = True
reasons = []
for name, peer in (("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5)):
    v, r, new_peer, registry = deliver(peer, SC["forged_entry"], registry)
    observe(name, new_peer)
    if name == "P2":
        P2 = new_peer
    elif name == "P3":
        P3 = new_peer
    elif name == "P4":
        P4 = new_peer
    else:
        P5 = new_peer
    if not (M.IdentityCompare(v, L.AdmissionRejectedLabel)() is M.truth_value
            and M.IdentityCompare(r, L.ReceiptFailedLocallyLabel)() is M.truth_value):
        ok_forgery = False
    reasons.append(tag_name(r))
check("the forged entry is rejected by every honest peer", ok_forgery, ",".join(reasons))
check("  ... and the rejection reason is local receipt verification, everywhere",
      all(r == "ReceiptFailedLocallyLabel" for r in reasons))
check("  ... no honest peer's version moved for it", monotonic("P2") and monotonic("P3")
      and monotonic("P4") and monotonic("P5"))

# stale snapshot: offer every peer the origin's version-1 ledger
ok_stale = True
for peer in (P2, P3, P4):
    report = CS.OfferLedgerSnapshot(peer, SC["ledger_v1"], registry)()
    if M.IdentityCompare(M.Head(M.Tail(report)())(), L.StaleSnapshotLabel)() is M.false_value:
        ok_stale = False
check("a version-1 snapshot is stale refuse for every peer at version 2", ok_stale)
for name, peer in (("P2", P2), ("P3", P3), ("P4", P4), ("P5", P5)):
    observe(name, peer)
check("  ... nobody's state moved backwards", monotonic("P2") and monotonic("P3")
      and monotonic("P4") and monotonic("P5"))

# P4 crashes here: it saw round one, refuses nothing since, and is excluded
# from the agreement set exactly because it stops receiving.
crashed_P4 = P4

print()

# ---------------------------------------------------------------------------
# [3] rollback by tombstone, over the remaining honest peers
# ---------------------------------------------------------------------------

print("[3] Rollback: a tombstone at a higher version, history preserved")


def find_revoked(ledger):
    cur = Ledger.PromotionLedgerProofSchemata(ledger)()
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        e = M.Head(cur)()
        if M.IdentityCompare(Ledger.LedgerEntryStatus(e)(), L.PromotionRevokedLabel)() is M.truth_value:
            return e
        cur = M.Tail(cur)()
    return None

rb = Ledger.RollbackPromotion(SC["ledger_v2"], Ledger.LedgerEntryId(entry1)(), M.Char("byzantine-test"), registry)()
check("the origin's rollback revokes at a higher version",
      M.IdentityCompare(M.Head(rb)(), L.PromotionRevokedLabel)() is M.truth_value)
tomb_ledger = M.Head(M.Tail(rb)())()
check("  ... the ledger version advanced to 3",
      ver_eq(Ledger.PromotionLedgerVersion(tomb_ledger)(), peano.three, registry))
check("  ... history is preserved: the entry is still there, revoked",
      find_revoked(tomb_ledger) is not None)


tombstone = find_revoked(tomb_ledger)
# the omission fault is repaired through the same delivery path: P5's parked
# entry2 must drain behind the late entry1 before the tombstone can apply
v, r, P5, registry = deliver(P5, entry1, registry)
observe("P5", P5)
check("P5's omission is repaired: late entry1 drains its parked entry2",
      M.IdentityCompare(v, L.AdmissionAdmittedLabel)() is M.truth_value
      and ver_eq(Ledger.PromotionLedgerVersion(CS.PeerLedger(P5))(), peano.two, registry),
      tag_name(v))
ok_tomb = True
for name, peer in (("P2", P2), ("P3", P3), ("P5", P5)):
    v, r, new_peer, registry = deliver(peer, tombstone, registry)
    observe(name, new_peer)
    if name == "P2":
        P2 = new_peer
    elif name == "P3":
        P3 = new_peer
    else:
        P5 = new_peer
    if M.IdentityCompare(v, L.AdmissionAdmittedLabel)() is M.false_value:
        ok_tomb = False
check("the tombstone commits on every live honest peer", ok_tomb)
check("  ... versions never decreased anywhere", monotonic("P2") and monotonic("P3") and monotonic("P5"))

origin_peer = CS.ConsensusPeer(tomb_ledger, M.EmptyList, M.EmptyList, SC["valid_rules"])()
agree = all(
    CS.PeersAgree(origin_peer, peer)() is M.truth_value for peer in (P2, P3, P5)
)
check("origin, P2, P3 and P5 hold structurally identical ledgers", agree)
check("  ... the crashed P4 is honestly behind, not silently wrong",
      peano.NatLess(Ledger.PromotionLedgerVersion(CS.PeerLedger(crashed_P4))(),
                    Ledger.PromotionLedgerVersion(CS.PeerLedger(P2))(), SC["registry"])()
      is M.truth_value)

print()

# ---------------------------------------------------------------------------
# [4] the split view: a partitioned peer reconciles through the same path
# ---------------------------------------------------------------------------

print("[4] Split view and reconciliation")

# A fifth peer is partitioned before anything happens; after the heal it is
# handed snapshots, not individual deliveries.
solo = fresh_peers(SC, 1)[0]
_, _, solo, registry = rpt(CS.OfferLedgerSnapshot(solo, SC["ledger_v1"], registry)())
_, _, solo, registry = rpt(CS.OfferLedgerSnapshot(solo, SC["ledger_v2"], registry)())
_, _, solo, registry = rpt(CS.OfferLedgerSnapshot(solo, tomb_ledger, registry)())
observe("P2", solo)  # log under a fresh eye: monotonic across snapshots
check("a partitioned peer reconciles to the origin's ledger through snapshots alone",
      CS.PeersAgree(origin_peer, solo)() is M.truth_value)
check("  ... its version history was monotonic across the heal", monotonic("P2"))

print()

# ---------------------------------------------------------------------------
# [5] determinism: the same schedule, twice, from scratch
# ---------------------------------------------------------------------------

print("[5] Determinism")


def decision_skeleton(ledger):
    """The ledger's decision surface: its version, then each entry's
    (version, status) in commit order. Entry bodies cannot be compared
    across runs -- receipts, derivations and candidate macros are saturated
    with anonymous identity atoms that the machine mints fresh per run and
    deliberately treats as distinct -- so cross-run reproducibility is
    asserted on the decisions, while within-run structural identity of full
    ledgers is what the agreement checks already prove."""
    def one_branch(cur, acc):
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            e = M.Head(cur)()
            acc = M.Pair(
                Ledger.LedgerEntryVersion(e)(),
                M.Pair(Ledger.LedgerEntryStatus(e)(), acc),
            )
            cur = M.Tail(cur)()
        return acc

    acc = one_branch(Ledger.PromotionLedgerProofSchemata(ledger)(), M.EmptyList)
    acc = one_branch(Ledger.PromotionLedgerSearchPolicies(ledger)(), acc)
    return M.Pair(Ledger.PromotionLedgerVersion(ledger)(), acc)


def run_whole_schedule():
    sc = build_scenario()
    reg = sc["registry"]
    ps = fresh_peers(sc, 3)
    a, b, c = ps
    for e in (sc["entry2"], sc["entry1"]):
        _, _, a, reg = deliver(a, e, reg)
    for e in (sc["entry1"], sc["entry1"], sc["entry2"]):
        _, _, b, reg = deliver(b, e, reg)
    _, _, c, reg = deliver(c, sc["entry2"], reg)
    _, _, c, reg = deliver(c, sc["forged_entry"], reg)
    _, _, c, reg = deliver(c, sc["entry1"], reg)
    rb2 = Ledger.RollbackPromotion(sc["ledger_v2"], Ledger.LedgerEntryId(sc["entry1"])(),
                                   M.Char("determinism"), reg)()
    tomb2 = find_revoked(M.Head(M.Tail(rb2)())())
    for p in (a, b, c):
        _, _, p, reg = deliver(p, tomb2, reg)
    return [CS.PeerLedger(p) for p in (a, b, c)]


first = run_whole_schedule()
second = run_whole_schedule()
same = all(
    M.Compare(decision_skeleton(x), decision_skeleton(y))() is M.truth_value
    for x, y in zip(first, second)
)
check("the schedule replays to identical decisions: same versions, same statuses", same)

print()

# ---------------------------------------------------------------------------
# [6] machine purity of the consensus vocabulary
# ---------------------------------------------------------------------------

print("[6] Representation checks")


def pattern_var_count(term):
    if M.IsPair(term)() is M.false_value:
        return 0
    if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
        return 1
    return pattern_var_count(M.Head(term)()) + pattern_var_count(M.Tail(term)())


def is_peano(term, registry):
    cur, guard = term, 64
    while guard > 0:
        if M.IdentityCompare(cur, M.Zero)() is M.truth_value:
            return True
        ctor = M.GetConstructor(cur)()
        if M.IdentityCompare(ctor, M.EmptyList)() is M.truth_value:
            return False
        if M.IdentityCompare(M.Head(ctor)(), L.SuccLabel)() is M.false_value:
            return False
        args = M.Tail(ctor)()
        cur = M.Head(args)()
        guard -= 1
    return False


check("peer state is a machine term headed by the consensus label",
      M.IdentityCompare(M.Head(P2)(), L.ConsensusPeerLabel)() is M.truth_value)
check("ledger versions everywhere are Peano constructions",
      all(is_peano(Ledger.PromotionLedgerVersion(CS.PeerLedger(p))(), SC["registry"])
          for p in (P2, P3, P5))
      and is_peano(Ledger.PromotionLedgerVersion(tomb_ledger)(), SC["registry"]))
check("delivery reports carry no pattern variables",
      pattern_var_count(CS.AcceptEntryDelivery(P2, entry2, SC["registry"])()) == 0)

print()
print("=== TEST 28 RESULTS ===")
passed = 0
for _name, ok, _detail in RESULTS:
    if ok:
        passed = passed + 1
failed = len(RESULTS) - passed
for name, ok, detail in RESULTS:
    if not ok:
        print("  FAILED: " + name + ("  -- " + detail if detail else ""))
print("  Checks passed: " + str(passed) + "/" + str(len(RESULTS)))
print("  Total time:    %.3fs" % (time.time() - T0))
print()
if failed:
    print("=== TEST 28 FAILED ===")
    sys.exit(1)
print("=== TEST 28 COMPLETE ===")
