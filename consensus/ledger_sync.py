"""W17: Byzantine ledger consensus and monotonic snapshot broadcast.

The security model is verification, not voting: an entry is admissible to a
peer iff its Checker B receipt verifies *locally* against that peer's own
trusted rules and policy. A quorum of peers asserting an unverifiable entry
promotes nothing; the receipt is the only oracle and it is checked on every
peer independently (`EntryReceiptVerdict`). What the consensus layer adds on
top of that is ordering: entries commit in version order (an entry commits
only at exactly the successor of the peer's ledger version; anything ahead of
that is parked and drained when the gap fills), duplicates are ignored by
entry id, and snapshots offered below the peer's own version are refused --
a version never goes backwards, locally or across peers.

Rollback is the ledger's own tombstone discipline (`RollbackPromotion`
re-marks an entry revoked *at a higher version* with the reason in its
provenance); the consensus layer broadcasts that revoked entry and peers
apply the same in-place rewrite. Tombstone authority is channel authority:
the machine carries no cryptographic identities, so who may originate a
tombstone is a property of the deployment, not of this module. That limit is
stated in the suite.

Peer state, ledgers, entries, versions, receipts and delivery reports are
machine terms. The fault scheduler that drives them -- crashes, omissions,
duplicates, reorders, forgeries, stale offers, partitions -- is plain Python
by design and lives in the suite; that boundary is the one the brief draws.
"""

from .. import machine as M
from .. import labels as L
from .. import proof as P
from .. import checker_b as CheckerB
from .. import peano as PN
from .. import promotion_ledger as Ledger


class ConsensusPeer(M.Edge):
    """
    One peer's consensus state: its promotion ledger, the entries parked
    ahead of its version, the check policy its admissions must satisfy, and
    the trusted rules its local verification runs against.

    inputs: [ledger, pending_entries, policy, trusted_rules]
    """

    def __init__(self, ledger, pending_entries, policy, trusted_rules):
        self.result = M.Pair(
            L.ConsensusPeerLabel,
            M.Pair(
                ledger,
                M.Pair(pending_entries, M.Pair(policy, M.Pair(trusted_rules, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                ledger,
                M.Pair(pending_entries, M.Pair(policy, M.Pair(trusted_rules, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


def PeerLedger(peer):
    return M.Head(M.Tail(peer)())()


def PeerPending(peer):
    return M.Head(M.Tail(M.Tail(peer)())())()


def PeerPolicy(peer):
    return M.Head(M.Tail(M.Tail(M.Tail(peer)())())())()


def PeerTrustedRules(peer):
    return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(peer)())())())())()


class EntryReceiptVerdict(M.Edge):
    """
    The local oracle: re-verify an entry's receipt against this peer's own
    trusted rules. The check policy is built from the receipt's own session,
    start and goal -- the claim is taken at face value and only its
    derivation is scrutinised -- because rule licensing against the peer's
    trusted rules is the security boundary: a forged derivation names a rule
    the peer does not trust and dies at UnknownRule, no matter what the
    receipt claims. (Session/scope pinning against a deployment-wide policy
    is a peer-configuration concern layered on top; the peer state carries
    the field for that, and consensus verdicts do not use it.)
    """

    def __init__(self, entry, trusted_rules, registry):
        receipt = Ledger.LedgerEntryReceipt(entry)()
        fields = M.Tail(receipt)()
        session = M.Head(fields)()
        start = M.Head(M.Tail(fields)())()
        goal = M.Head(M.Tail(M.Tail(fields)())())()
        policy = M.Pair(L.CheckPolicyLabel, M.Pair(session, M.Pair(start, M.Pair(goal, M.EmptyList))))
        self.result = CheckerB.VerifyProofReceipt(receipt, policy, trusted_rules, registry)()
        super().__init__(
            inputs=M.Pair(entry, M.Pair(trusted_rules, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


def _entry_in_branch(branch, entry_id):
    cursor = branch
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        if M.Compare(Ledger.LedgerEntryId(M.Head(cursor)())(), entry_id)() is M.truth_value:
            return M.truth_value
        cursor = M.Tail(cursor)()
    return M.false_value


def _entry_known(ledger, entry_id):
    if _entry_in_branch(Ledger.PromotionLedgerProofSchemata(ledger)(), entry_id) is M.truth_value:
        return M.truth_value
    return _entry_in_branch(Ledger.PromotionLedgerSearchPolicies(ledger)(), entry_id)


def _append_entry(ledger, entry):
    """Commit an active entry: onto the branch its class names, in front."""
    eclass = Ledger.LedgerEntryClass(entry)()
    if M.Compare(eclass, L.ProofSchemaPromotionLabel)() is M.truth_value:
        branch = M.Pair(entry, Ledger.PromotionLedgerProofSchemata(ledger)())
        return Ledger.PromotionLedger(
            branch, Ledger.PromotionLedgerSearchPolicies(ledger)(), Ledger.PromotionLedgerVersion(ledger)()
        )()
    branch = M.Pair(entry, Ledger.PromotionLedgerSearchPolicies(ledger)())
    return Ledger.PromotionLedger(
        Ledger.PromotionLedgerProofSchemata(ledger)(), branch, Ledger.PromotionLedgerVersion(ledger)()
    )()


def _apply_tombstone(ledger, tombstone):
    """The peer-side mirror of RollbackPromotion: replace the matched entry
    in place with the revoked one it was handed (which already carries the
    revocation reason in its provenance and the higher version). History is
    the entry itself, rewritten, never deleted."""
    target = Ledger.LedgerEntryId(tombstone)()

    def rewrite(cur):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)
        entry = M.Head(cur)()
        rest = M.Tail(cur)()
        if M.Compare(Ledger.LedgerEntryId(entry)(), target)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(tombstone, rest))
        deeper = rewrite(rest)
        if M.IdentityCompare(M.Head(deeper)(), M.truth_value)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(entry, M.Tail(deeper)()))
        return M.Pair(M.false_value, M.EmptyList)

    hit = rewrite(Ledger.PromotionLedgerProofSchemata(ledger)())
    if M.IdentityCompare(M.Head(hit)(), M.truth_value)() is M.truth_value:
        return Ledger.PromotionLedger(
            M.Tail(hit)(), Ledger.PromotionLedgerSearchPolicies(ledger)(), Ledger.PromotionLedgerVersion(ledger)()
        )()
    hit = rewrite(Ledger.PromotionLedgerSearchPolicies(ledger)())
    if M.IdentityCompare(M.Head(hit)(), M.truth_value)() is M.truth_value:
        return Ledger.PromotionLedger(
            Ledger.PromotionLedgerProofSchemata(ledger)(), M.Tail(hit)(), Ledger.PromotionLedgerVersion(ledger)()
        )()
    return ledger


def _remove_pending(pending, entry_id):
    if M.IdentityCompare(pending, M.EmptyList)() is M.truth_value:
        return M.Pair(M.false_value, M.EmptyList)
    entry = M.Head(pending)()
    rest = M.Tail(pending)()
    if M.Compare(Ledger.LedgerEntryId(entry)(), entry_id)() is M.truth_value:
        return M.Pair(M.truth_value, rest)
    deeper = _remove_pending(rest, entry_id)
    if M.IdentityCompare(M.Head(deeper)(), M.truth_value)() is M.truth_value:
        return M.Pair(M.truth_value, M.Pair(entry, M.Tail(deeper)()))
    return M.Pair(M.false_value, M.EmptyList)


def _commit_at_version(peer, entry, version, registry):
    """Rewire the peer's ledger to `version` and store the entry (append for
    active entries, in-place rewrite for tombstones), returning the new peer
    and the drained pending list."""
    ledger = PeerLedger(peer)
    estatus = Ledger.LedgerEntryStatus(entry)()
    if M.Compare(estatus, L.PromotionRevokedLabel)() is M.truth_value:
        rewritten = _apply_tombstone(ledger, entry)
        new_ledger = Ledger.PromotionLedger(
            Ledger.PromotionLedgerProofSchemata(rewritten)(),
            Ledger.PromotionLedgerSearchPolicies(rewritten)(),
            version,
        )()
    else:
        advanced = Ledger.PromotionLedger(
            Ledger.PromotionLedgerProofSchemata(ledger)(),
            Ledger.PromotionLedgerSearchPolicies(ledger)(),
            version,
        )()
        new_ledger = _append_entry(advanced, entry)
    return ConsensusPeer(new_ledger, PeerPending(peer), PeerPolicy(peer), PeerTrustedRules(peer))()


class AcceptEntryDelivery(M.Edge):
    """
    One delivery, one verdict.

    Order of tests, and the report each produces
    (Pair(DeliveryReportLabel, Pair(verdict, Pair(reason, Pair(peer, Pair(registry, Empty)))))):

      duplicate id already in the ledger   -> AdmissionRejected + DuplicateEntry
      tombstone (revoked status)           -> must target a known id, and
                                              commit in version order like
                                              any entry (authority is channel
                                              authority; stated in the suite)
      active entry: receipt fails local
      verification                         -> AdmissionRejected + ReceiptFailedLocally,
                                              with the verifier's own tag as
                                              the evidence; the peer state is
                                              untouched
      entry version behind the ledger      -> AdmissionRejected + DuplicateEntry
                                              (the slot is already covered)
      entry version ahead by more than one -> parked; VersionGap
      entry version exactly next           -> commit, advance, drain pending
    """

    def __init__(self, peer, entry, registry):
        self.result = self._deliver(peer, entry, registry)
        super().__init__(
            inputs=M.Pair(peer, M.Pair(entry, M.EmptyList)), results=self.result
        )

    def _deliver(self, peer, entry, registry):
        ledger = PeerLedger(peer)
        eid = Ledger.LedgerEntryId(entry)()
        estatus = Ledger.LedgerEntryStatus(entry)()
        is_tombstone = M.Compare(estatus, L.PromotionRevokedLabel)() is M.truth_value

        if is_tombstone:
            # A tombstone reuses the id of the entry it revokes, so the
            # duplicate test does not apply to it; its admissibility is that
            # the target is one this peer actually holds.
            if _entry_known(ledger, eid) is M.false_value:
                return M.Pair(
                    L.DeliveryReportLabel,
                    M.Pair(L.AdmissionRejectedLabel, M.Pair(L.UnknownTargetLabel, M.Pair(peer, M.Pair(registry, M.EmptyList)))),
                )
        else:
            if _entry_known(ledger, eid) is M.truth_value:
                return M.Pair(
                    L.DeliveryReportLabel,
                    M.Pair(L.AdmissionRejectedLabel, M.Pair(L.DuplicateEntryLabel, M.Pair(peer, M.Pair(registry, M.EmptyList)))),
                )
            verdict = EntryReceiptVerdict(entry, PeerTrustedRules(peer), registry)()
            vtag = M.Head(verdict)()
            if M.Compare(vtag, L.DerivationVerifiedLabel)() is M.false_value:
                return M.Pair(
                    L.DeliveryReportLabel,
                    M.Pair(
                        L.AdmissionRejectedLabel,
                        M.Pair(L.ReceiptFailedLocallyLabel, M.Pair(peer, M.Pair(registry, M.Pair(vtag, M.EmptyList)))),
                    ),
                )

        ev = Ledger.LedgerEntryVersion(entry)()
        lv = Ledger.PromotionLedgerVersion(ledger)()
        succ_pair = M.Succ(lv, registry)()
        next_v = M.Head(succ_pair)()
        registry = M.Head(M.Tail(succ_pair)())()

        if PN.NatLess(next_v, ev, registry)() is M.truth_value:
            parked = M.Pair(entry, PeerPending(peer))
            waiting_peer = ConsensusPeer(
                ledger, parked, PeerPolicy(peer), PeerTrustedRules(peer)
            )()
            return M.Pair(
                L.DeliveryReportLabel,
                M.Pair(L.VersionGapLabel, M.Pair(L.VersionGapLabel, M.Pair(waiting_peer, M.Pair(registry, M.EmptyList)))),
            )
        if PN.NatLess(ev, next_v, registry)() is M.truth_value:
            return M.Pair(
                L.DeliveryReportLabel,
                M.Pair(L.AdmissionRejectedLabel, M.Pair(L.DuplicateEntryLabel, M.Pair(peer, M.Pair(registry, M.EmptyList)))),
            )

        # in-order commit, then drain the park
        committed = _commit_at_version(peer, entry, ev, registry)
        drain = self._drain(committed, registry)
        return M.Pair(
            L.DeliveryReportLabel,
            M.Pair(L.AdmissionAdmittedLabel, M.Pair(L.AdmissionAdmittedLabel, drain)),
        )

    def _drain(self, peer, registry):
        progressed = M.truth_value
        current = peer
        while progressed is M.truth_value:
            progressed = M.false_value
            pending = PeerPending(current)
            cursor = pending
            while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
                candidate = M.Head(cursor)()
                cursor = M.Tail(cursor)()
                estatus = Ledger.LedgerEntryStatus(candidate)()
                is_tombstone = M.Compare(estatus, L.PromotionRevokedLabel)() is M.truth_value
                if not is_tombstone:
                    verdict = EntryReceiptVerdict(candidate, PeerTrustedRules(current), registry)()
                    if M.Compare(M.Head(verdict)(), L.DerivationVerifiedLabel)() is M.false_value:
                        continue
                ev = Ledger.LedgerEntryVersion(candidate)()
                lv = Ledger.PromotionLedgerVersion(PeerLedger(current))()
                succ_pair = M.Succ(lv, registry)()
                next_v = M.Head(succ_pair)()
                registry = M.Head(M.Tail(succ_pair)())()
                if PN.NatEq(ev, next_v, registry)() is M.truth_value:
                    without = _remove_pending(PeerPending(current), Ledger.LedgerEntryId(candidate)())
                    stripped = ConsensusPeer(
                        PeerLedger(current), M.Tail(without)(), PeerPolicy(current), PeerTrustedRules(current)
                    )()
                    current = _commit_at_version(stripped, candidate, ev, registry)
                    progressed = M.truth_value
                    break
        return M.Pair(current, M.Pair(registry, M.EmptyList))

    def __call__(self):
        return self.result


class OfferLedgerSnapshot(M.Edge):
    """
    A peer is handed a whole ledger. If it is at or behind the peer's own
    version the offer is refused -- monotonicity is not negotiable -- and if
    it is ahead, its entries are delivered through the same admission path
    as any broadcast, so a snapshot can never smuggle what a delivery could
    not.
    """

    def __init__(self, peer, offered_ledger, registry):
        self.result = self._offer(peer, offered_ledger, registry)
        super().__init__(
            inputs=M.Pair(peer, M.Pair(offered_ledger, M.EmptyList)), results=self.result
        )

    def _offer(self, peer, offered_ledger, registry):
        local_v = Ledger.PromotionLedgerVersion(PeerLedger(peer))()
        offered_v = Ledger.PromotionLedgerVersion(offered_ledger)()
        if PN.NatLess(offered_v, local_v, registry)() is M.truth_value or PN.NatEq(
            offered_v, local_v, registry
        )() is M.truth_value:
            return M.Pair(
                L.DeliveryReportLabel,
                M.Pair(L.StaleSnapshotLabel, M.Pair(L.StaleSnapshotLabel, M.Pair(peer, M.Pair(registry, M.EmptyList)))),
            )

        def entries_of(ledger):
            return M.Pair(
                Ledger.PromotionLedgerProofSchemata(ledger)(),
                Ledger.PromotionLedgerSearchPolicies(ledger)(),
            )

        both = entries_of(offered_ledger)
        current = peer
        branch = M.Head(both)()
        while M.IdentityCompare(branch, M.EmptyList)() is M.false_value:
            report = AcceptEntryDelivery(current, M.Head(branch)(), registry)()
            current = M.Head(M.Tail(M.Tail(M.Tail(report)())())())()
            registry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(report)())())())())()
            branch = M.Tail(branch)()
        branch = M.Tail(both)()
        while M.IdentityCompare(branch, M.EmptyList)() is M.false_value:
            report = AcceptEntryDelivery(current, M.Head(branch)(), registry)()
            current = M.Head(M.Tail(M.Tail(M.Tail(report)())())())()
            registry = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(report)())())())())()
            branch = M.Tail(branch)()
        return M.Pair(
            L.DeliveryReportLabel,
            M.Pair(L.SnapshotAdoptedLabel, M.Pair(L.SnapshotAdoptedLabel, M.Pair(current, M.Pair(registry, M.EmptyList)))),
        )

    def __call__(self):
        return self.result


class PeersAgree(M.Edge):
    """
    Agreement: two honest peers hold structurally equal ledgers -- same
    entries, same statuses, same provenance, same version.
    """

    def __init__(self, peer_a, peer_b):
        self.result = M.Compare(PeerLedger(peer_a), PeerLedger(peer_b))()
        super().__init__(inputs=M.Pair(peer_a, M.Pair(peer_b, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


def FreshPeer(policy, trusted_rules, registry):
    ledger = Ledger.EmptyPromotionLedger(registry)()
    return ConsensusPeer(ledger, M.EmptyList, policy, trusted_rules)()


__all__ = (
    "ConsensusPeer",
    "PeerLedger",
    "PeerPending",
    "PeerPolicy",
    "PeerTrustedRules",
    "EntryReceiptVerdict",
    "AcceptEntryDelivery",
    "OfferLedgerSnapshot",
    "PeersAgree",
    "FreshPeer",
)
