from __future__ import annotations

from . import labels as L
from . import machine as M
from . import structure_play as SP


# ============================================================
# Catalogue of abstract structures
#
# The catalogue is ordered weakest profile first. An entry names one
# abstract structure and lists the law labels its recognition
# requires. The labels are the only thing recognition consumes: the
# carrier, its elements, and its operation name are never inspected.
# ============================================================


class CatalogueEntry(M.Edge):
    """(CatalogueEntry name required-law-labels)"""

    def __init__(self, name, required_labels):
        self.result = M.Pair(L.CatalogueEntryLabel, M.Pair(name, M.Pair(required_labels, M.EmptyList)))
        super().__init__(inputs=M.Pair(name, M.Pair(required_labels, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CatalogueEntryName(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CatalogueEntryRequirements(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RecognizerCatalogue(M.Edge):
    """The default catalogue, strongest profile first so that scanning
    yields the most specific structure whose gate opens:

      AbstractAbelianGroupLabel  closure, associativity, identity,
                                 inverses, commutativity
      AbstractGroupLabel         closure, associativity, identity, inverses
      AbstractMonoidLabel        closure, associativity, identity
      AbstractSemigroupLabel     closure, associativity"""

    def __init__(self):
        abelian = CatalogueEntry(
            L.AbstractAbelianGroupLabel,
            M.Pair(
                L.ClosureLawLabel,
                M.Pair(
                    L.AssociativeLawLabel,
                    M.Pair(
                        L.IdentityLawLabel,
                        M.Pair(L.InverseLawLabel, M.Pair(L.CommutativeLawLabel, M.EmptyList)),
                    ),
                ),
            ),
        )()
        group = CatalogueEntry(
            L.AbstractGroupLabel,
            M.Pair(
                L.ClosureLawLabel,
                M.Pair(
                    L.AssociativeLawLabel,
                    M.Pair(L.IdentityLawLabel, M.Pair(L.InverseLawLabel, M.EmptyList)),
                ),
            ),
        )()
        monoid = CatalogueEntry(
            L.AbstractMonoidLabel,
            M.Pair(
                L.ClosureLawLabel,
                M.Pair(L.AssociativeLawLabel, M.Pair(L.IdentityLawLabel, M.EmptyList)),
            ),
        )()
        semigroup = CatalogueEntry(
            L.AbstractSemigroupLabel,
            M.Pair(L.ClosureLawLabel, M.Pair(L.AssociativeLawLabel, M.EmptyList)),
        )()
        self.result = M.Pair(
            L.RecognizerCatalogueLabel,
            M.Pair(abelian, M.Pair(group, M.Pair(monoid, M.Pair(semigroup, M.EmptyList)))),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class CatalogueEntries(M.Edge):
    def __init__(self, catalogue):
        self.result = M.Tail(catalogue)()
        super().__init__(inputs=M.Pair(catalogue, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CatalogueEntryNamed(M.Edge):
    def __init__(self, catalogue, wanted):
        self.result = self._named(CatalogueEntries(catalogue)(), wanted)
        super().__init__(inputs=M.Pair(catalogue, M.Pair(wanted, M.EmptyList)), results=self.result)

    def _named(self, entries, wanted):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        entry = M.Head(entries)()
        if M.IdentityCompare(CatalogueEntryName(entry)(), wanted)() is M.truth_value:
            return entry
        return self._named(M.Tail(entries)(), wanted)

    def __call__(self):
        return self.result


# ============================================================
# Certification gate
#
# One requirement chain, checked against one signature. A requirement
# is met only when the matching signature slot carries a CertifiedLaw
# of exactly that law label whose replay record re-verifies against
# the declared operation stored in the signature evidence. Any other
# state leaves the gate closed and names the blocking requirement.
# ============================================================


class CertificationGate(M.Edge):
    """(CertificationGate signature required-labels verdict
          blocking-requirement)"""

    def __init__(self, signature, required_labels):
        operation = SP.SignatureOperationTerm(signature)()
        outcome = self._gate(signature, required_labels, operation)
        verdict = M.Head(outcome)()
        blocking = M.Head(M.Tail(outcome)())()
        fields = M.Pair(
            signature,
            M.Pair(required_labels, M.Pair(verdict, M.Pair(blocking, M.EmptyList))),
        )
        self.result = M.Pair(L.CertificationGateLabel, fields)
        super().__init__(inputs=fields, results=self.result)

    def _gate(self, signature, remaining, operation):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(M.EmptyList, M.EmptyList))
        required = M.Head(remaining)()
        slot = self._slot(signature, required)
        present = M.IdentityCompare(slot, M.EmptyList)()
        if present is M.truth_value:
            return M.Pair(M.false_value, M.Pair(required, M.EmptyList))
        label_ok = M.IdentityCompare(SP.CertifiedLawLabelOf(slot)(), required)()
        if label_ok is M.false_value:
            return M.Pair(M.false_value, M.Pair(required, M.EmptyList))
        replay = SP.CertifiedLawReplayOf(slot)()
        replay_verdict = SP.CheckReplay(replay, operation)()
        verified = M.IdentityCompare(replay_verdict, L.ReplayVerifiedLabel)()
        if verified is M.false_value:
            return M.Pair(M.false_value, M.Pair(required, M.EmptyList))
        return self._gate(signature, M.Tail(remaining)(), operation)

    def _slot(self, signature, law_label):
        if M.IdentityCompare(law_label, L.ClosureLawLabel)() is M.truth_value:
            return SP.SignatureClosureOf(signature)()
        if M.IdentityCompare(law_label, L.AssociativeLawLabel)() is M.truth_value:
            return SP.SignatureAssociativityOf(signature)()
        if M.IdentityCompare(law_label, L.IdentityLawLabel)() is M.truth_value:
            return SP.SignatureIdentityOf(signature)()
        if M.IdentityCompare(law_label, L.InverseLawLabel)() is M.truth_value:
            return SP.SignatureInversesOf(signature)()
        if M.IdentityCompare(law_label, L.CommutativeLawLabel)() is M.truth_value:
            return SP.SignatureCommutativityOf(signature)()
        return M.EmptyList

    def __call__(self):
        return self.result


class GateSignatureOf(M.Edge):
    def __init__(self, gate):
        self.result = M.Head(M.Tail(gate)())()
        super().__init__(inputs=M.Pair(gate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GateRequirements(M.Edge):
    def __init__(self, gate):
        self.result = M.Head(M.Tail(M.Tail(gate)())())()
        super().__init__(inputs=M.Pair(gate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GateVerdict(M.Edge):
    def __init__(self, gate):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(gate)())())())()
        super().__init__(inputs=M.Pair(gate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GateBlockingRequirement(M.Edge):
    def __init__(self, gate):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(gate)())())())())()
        super().__init__(inputs=M.Pair(gate, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# ============================================================
# Recognition
#
# Recognition is a separate act from exploration. It reads only the
# certified slots of a signature, compares them against catalogue
# entries, and reports the strongest entry whose gate opens. A
# signature with any withheld certificate recognizes as nothing.
# ============================================================


class RecognizeStructure(M.Edge):
    """(RecognizedStructure candidate recognized-entry
          blocking-requirement verdict)

    The verdict is CandidateRecognizedLabel when some catalogue entry
    opened, WithheldStructureLabel when none did. The blocking
    requirement names the law that closed the first scanned entry; for
    a fully recognized signature it is empty."""

    def __init__(self, candidate, catalogue):
        signature = SP.CandidateSignatureOf(candidate)()
        entries = CatalogueEntries(catalogue)()
        outcome = self._scan(signature, entries)
        recognized = M.Head(outcome)()
        blocking = M.Head(M.Tail(outcome)())()
        if M.IdentityCompare(recognized, M.EmptyList)() is M.truth_value:
            verdict = L.WithheldStructureLabel
        else:
            verdict = L.CandidateRecognizedLabel
        fields = M.Pair(candidate, M.Pair(recognized, M.Pair(blocking, M.Pair(verdict, M.EmptyList))))
        self.result = M.Pair(L.StructureRecognizedLabel, fields)
        super().__init__(inputs=M.Pair(candidate, M.Pair(catalogue, M.EmptyList)), results=self.result)

    def _scan(self, signature, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
        entry = M.Head(entries)()
        gate = CertificationGate(signature, CatalogueEntryRequirements(entry)())()
        if M.IdentityCompare(GateVerdict(gate)(), M.truth_value)() is M.truth_value:
            return M.Pair(CatalogueEntryName(entry)(), M.Pair(M.EmptyList, M.EmptyList))
        first_blocking = GateBlockingRequirement(gate)()
        rest = self._scan(signature, M.Tail(entries)())
        rest_name = M.Head(rest)()
        if M.IdentityCompare(rest_name, M.EmptyList)() is M.false_value:
            return rest
        return M.Pair(M.EmptyList, M.Pair(first_blocking, M.EmptyList))

    def __call__(self):
        return self.result


class RecognizedCandidateOf(M.Edge):
    def __init__(self, recognition):
        self.result = M.Head(M.Tail(recognition)())()
        super().__init__(inputs=M.Pair(recognition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RecognizedEntryOf(M.Edge):
    def __init__(self, recognition):
        self.result = M.Head(M.Tail(M.Tail(recognition)())())()
        super().__init__(inputs=M.Pair(recognition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RecognizedBlockingOf(M.Edge):
    def __init__(self, recognition):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(recognition)())())())()
        super().__init__(inputs=M.Pair(recognition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RecognizedVerdictOf(M.Edge):
    def __init__(self, recognition):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(recognition)())())())())()
        super().__init__(inputs=M.Pair(recognition, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
