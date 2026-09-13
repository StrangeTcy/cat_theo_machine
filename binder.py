from __future__ import annotations

from . import machine as M
from . import proof as P
from .labels import (
    BinderAxiomLabel,
    ContradictionIntroductionLabel,
    ContradictionLabel,
    EqLabel,
    FalseLabel,
    ForAllLabel,
    ForallIntroductionLabel,
    FreshnessEvidenceLabel,
    GreaterLabel,
    HumanSuppliedTrustedTheoremLabel,
    ImpliesIntroductionLabel,
    ImpliesLabel,
    InLabel,
    NosolutionsIntroductionLabel,
    NotLabel,
    PlusLabel,
)

TrustedReasonText = "HUMAN_SUPPLIED_TRUSTED_THEOREM"
AxiomEqReflText = "eq-refl"

ShowNames = (
    (ForAllLabel, "forall"),
    (ImpliesLabel, "implies"),
    (FalseLabel, "False"),
    (EqLabel, "eq"),
    (PlusLabel, "plus"),
    (GreaterLabel, "greater"),
    (NotLabel, "not"),
    (InLabel, "in"),
    (ContradictionLabel, "contradiction"),
    (ForallIntroductionLabel, "ForallIntroduction"),
    (ImpliesIntroductionLabel, "ImpliesIntroduction"),
    (ContradictionIntroductionLabel, "ContradictionIntroduction"),
    (NosolutionsIntroductionLabel, "NosolutionsIntroduction"),
    (FreshnessEvidenceLabel, "FreshnessEvidence"),
    (HumanSuppliedTrustedTheoremLabel, "HUMAN_SUPPLIED_TRUSTED_THEOREM"),
    (BinderAxiomLabel, "BinderAxiom"),
    (M.VarTag, "var"),
)


class BinderVar(M.Edge):
    def __init__(self, name):
        self.result = M.Pair(M.VarTag, M.Pair(M.Char(name), M.EmptyList))
        super().__init__(inputs=M.Pair(M.Char(name), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ForallTerm(M.Edge):
    def __init__(self, variable, body):
        self.result = M.Pair(ForAllLabel, M.Pair(variable, M.Pair(body, M.EmptyList)))
        super().__init__(inputs=M.Pair(variable, M.Pair(body, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ImpliesTerm(M.Edge):
    def __init__(self, antecedent, consequent):
        self.result = M.Pair(ImpliesLabel, M.Pair(antecedent, M.Pair(consequent, M.EmptyList)))
        super().__init__(inputs=M.Pair(antecedent, M.Pair(consequent, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FalseTerm(M.Edge):
    def __init__(self):
        self.result = M.Pair(FalseLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class NotTerm(M.Edge):
    def __init__(self, inner):
        self.result = M.Pair(NotLabel, M.Pair(inner, M.EmptyList))
        super().__init__(inputs=M.Pair(inner, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EqTerm(M.Edge):
    def __init__(self, left, right):
        self.result = M.Pair(EqLabel, M.Pair(left, M.Pair(right, M.EmptyList)))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PlusTerm(M.Edge):
    def __init__(self, left, right):
        self.result = M.Pair(PlusLabel, M.Pair(left, M.Pair(right, M.EmptyList)))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class GreaterTerm(M.Edge):
    def __init__(self, left, right):
        self.result = M.Pair(GreaterLabel, M.Pair(left, M.Pair(right, M.EmptyList)))
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class InTerm(M.Edge):
    def __init__(self, element, domain):
        self.result = M.Pair(InLabel, M.Pair(element, M.Pair(domain, M.EmptyList)))
        super().__init__(inputs=M.Pair(element, M.Pair(domain, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContradictionTerm(M.Edge):
    def __init__(self, witness):
        self.result = M.Pair(ContradictionLabel, M.Pair(witness, M.EmptyList))
        super().__init__(inputs=M.Pair(witness, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ScopeEntry(M.Edge):
    def __init__(self, scope_id, term):
        self.result = M.Pair(M.Char(scope_id), M.Pair(term, M.EmptyList))
        super().__init__(inputs=M.Pair(M.Char(scope_id), M.Pair(term, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class FreshnessEvidence(M.Edge):
    def __init__(self, variable, checked_scope):
        self.result = M.Pair(FreshnessEvidenceLabel, M.Pair(variable, M.Pair(checked_scope, M.EmptyList)))
        super().__init__(inputs=M.Pair(variable, M.Pair(checked_scope, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class Subst(M.Edge):
    def __init__(self, term, variable, replacement):
        outcome = self._subst(term, variable, replacement)
        self.result = M.Pair(outcome[0], outcome[1])
        super().__init__(inputs=M.Pair(term, M.Pair(variable, M.Pair(replacement, M.EmptyList))), results=self.result)

    def _forall_parts(self, term):
        if M.IsPair(term)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        if M.Compare(M.Head(term)(), ForAllLabel)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        args = M.Tail(term)()
        if M.IsPair(args)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        rest = M.Tail(args)()
        if M.IsPair(rest)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        return (M.truth_value, M.Head(args)(), M.Head(rest)())

    def _subst(self, term, variable, replacement):
        if M.Compare(term, variable)() is M.truth_value:
            return (M.truth_value, replacement)
        if M.IsPair(term)() is M.false_value:
            return (M.truth_value, term)
        parts = self._forall_parts(term)
        if parts[0] is M.truth_value:
            binder = parts[1]
            body = parts[2]
            if M.Compare(binder, variable)() is M.truth_value:
                return (M.truth_value, term)
            if M.Compare(binder, replacement)() is M.truth_value:
                return (M.false_value, M.EmptyList)
            inner = self._subst(body, variable, replacement)
            if inner[0] is M.truth_value:
                rebuilt = M.Pair(ForAllLabel, M.Pair(binder, M.Pair(inner[1], M.EmptyList)))
                return (M.truth_value, rebuilt)
            return (M.false_value, M.EmptyList)
        head_outcome = self._subst(M.Head(term)(), variable, replacement)
        tail_outcome = self._subst(M.Tail(term)(), variable, replacement)
        if head_outcome[0] is M.truth_value and tail_outcome[0] is M.truth_value:
            return (M.truth_value, M.Pair(head_outcome[1], tail_outcome[1]))
        return (M.false_value, M.EmptyList)

    def __call__(self):
        return self.result


class FreeOccurs(M.Edge):
    def __init__(self, variable, term):
        self.result = self._occurs(variable, term)
        super().__init__(inputs=M.Pair(variable, M.Pair(term, M.EmptyList)), results=self.result)

    def _forall_parts(self, term):
        if M.IsPair(term)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        if M.Compare(M.Head(term)(), ForAllLabel)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        args = M.Tail(term)()
        if M.IsPair(args)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        rest = M.Tail(args)()
        if M.IsPair(rest)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return (M.false_value, M.EmptyList, M.EmptyList)
        return (M.truth_value, M.Head(args)(), M.Head(rest)())

    def _occurs(self, variable, term):
        if M.Compare(term, variable)() is M.truth_value:
            return M.truth_value
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        parts = self._forall_parts(term)
        if parts[0] is M.truth_value:
            if M.Compare(parts[1], variable)() is M.truth_value:
                return M.false_value
            return self._occurs(variable, parts[2])
        return M.OrAtom(self._occurs(variable, M.Head(term)()), self._occurs(variable, M.Tail(term)()))()

    def __call__(self):
        return self.result


class AnyOccurs(M.Edge):
    def __init__(self, variable, term):
        self.result = self._occurs(variable, term)
        super().__init__(inputs=M.Pair(variable, M.Pair(term, M.EmptyList)), results=self.result)

    def _occurs(self, variable, term):
        if M.Compare(term, variable)() is M.truth_value:
            return M.truth_value
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        return M.OrAtom(self._occurs(variable, M.Head(term)()), self._occurs(variable, M.Tail(term)()))()

    def __call__(self):
        return self.result


class ScopeHasTerm(M.Edge):
    def __init__(self, scope, term):
        self.result = self._has(scope, term)
        super().__init__(inputs=M.Pair(scope, M.Pair(term, M.EmptyList)), results=self.result)

    def _entry_term(self, entry):
        if M.IsPair(entry)() is M.false_value:
            return M.EmptyList
        rest = M.Tail(entry)()
        if M.IsPair(rest)() is M.false_value:
            return M.EmptyList
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.EmptyList
        return M.Head(rest)()

    def _has(self, scope, term):
        node = scope
        while M.IsPair(node)() is M.truth_value:
            if M.Compare(self._entry_term(M.Head(node)()), term)() is M.truth_value:
                return M.truth_value
            node = M.Tail(node)()
        return M.false_value

    def __call__(self):
        return self.result


class ScopeCovers(M.Edge):
    def __init__(self, big, small):
        self.result = self._covers(big, small)
        super().__init__(inputs=M.Pair(big, M.Pair(small, M.EmptyList)), results=self.result)

    def _entry_term(self, entry):
        if M.IsPair(entry)() is M.false_value:
            return M.EmptyList
        rest = M.Tail(entry)()
        if M.IsPair(rest)() is M.false_value:
            return M.EmptyList
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.EmptyList
        return M.Head(rest)()

    def _covers(self, big, small):
        node = small
        while M.IsPair(node)() is M.truth_value:
            if ScopeHasTerm(big, self._entry_term(M.Head(node)()))() is M.false_value:
                return M.false_value
            node = M.Tail(node)()
        return M.truth_value

    def __call__(self):
        return self.result


class ScopeSame(M.Edge):
    def __init__(self, left, right):
        self.result = M.AndAtom(ScopeCovers(left, right)(), ScopeCovers(right, left)())()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CertHead(M.Edge):
    def __init__(self, cert):
        if M.IsPair(cert)() is M.truth_value:
            self.result = M.Head(cert)()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(cert, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CertField(M.Edge):
    def __init__(self, cert, index):
        self.result = self._field(cert, index)
        super().__init__(inputs=M.Pair(cert, M.EmptyList), results=self.result)

    def _field(self, cert, index):
        if M.IsPair(cert)() is M.false_value:
            return M.EmptyList
        node = M.Tail(cert)()
        step = 0
        while step < index:
            if M.IsPair(node)() is M.false_value:
                return M.EmptyList
            node = M.Tail(node)()
            step = step + 1
        if M.IsPair(node)() is M.false_value:
            return M.EmptyList
        return M.Head(node)()

    def __call__(self):
        return self.result


class CertConclusion(M.Edge):
    def __init__(self, cert):
        self.result = self._conclusion(cert)
        super().__init__(inputs=M.Pair(cert, M.EmptyList), results=self.result)

    def _conclusion(self, cert):
        head = CertHead(cert)()
        if M.Compare(head, BinderAxiomLabel)() is M.truth_value:
            return CertField(cert, 1)()
        if M.Compare(head, HumanSuppliedTrustedTheoremLabel)() is M.truth_value:
            return CertField(cert, 0)()
        if M.Compare(head, ForallIntroductionLabel)() is M.truth_value:
            return CertField(cert, 7)()
        if M.Compare(head, ImpliesIntroductionLabel)() is M.truth_value:
            return CertField(cert, 4)()
        if M.Compare(head, ContradictionIntroductionLabel)() is M.truth_value:
            return CertField(cert, 4)()
        if M.Compare(head, NosolutionsIntroductionLabel)() is M.truth_value:
            return CertField(cert, 8)()
        return M.EmptyList

    def __call__(self):
        return self.result


class CertScope(M.Edge):
    def __init__(self, cert):
        self.result = self._scope(cert)
        super().__init__(inputs=M.Pair(cert, M.EmptyList), results=self.result)

    def _scope(self, cert):
        head = CertHead(cert)()
        if M.Compare(head, BinderAxiomLabel)() is M.truth_value:
            return CertField(cert, 2)()
        if M.Compare(head, HumanSuppliedTrustedTheoremLabel)() is M.truth_value:
            return CertField(cert, 2)()
        if M.Compare(head, ForallIntroductionLabel)() is M.truth_value:
            return CertField(cert, 5)()
        if M.Compare(head, ImpliesIntroductionLabel)() is M.truth_value:
            return CertField(cert, 2)()
        if M.Compare(head, ContradictionIntroductionLabel)() is M.truth_value:
            return CertField(cert, 2)()
        if M.Compare(head, NosolutionsIntroductionLabel)() is M.truth_value:
            return CertField(cert, 6)()
        return M.EmptyList

    def __call__(self):
        return self.result


class CertBranch(M.Edge):
    def __init__(self, cert):
        self.result = self._branch(cert)
        super().__init__(inputs=M.Pair(cert, M.EmptyList), results=self.result)

    def _branch(self, cert):
        head = CertHead(cert)()
        if M.Compare(head, BinderAxiomLabel)() is M.truth_value:
            return CertField(cert, 3)()
        if M.Compare(head, HumanSuppliedTrustedTheoremLabel)() is M.truth_value:
            return CertField(cert, 3)()
        if M.Compare(head, ForallIntroductionLabel)() is M.truth_value:
            return CertField(cert, 6)()
        if M.Compare(head, ImpliesIntroductionLabel)() is M.truth_value:
            return CertField(cert, 3)()
        if M.Compare(head, ContradictionIntroductionLabel)() is M.truth_value:
            return CertField(cert, 3)()
        if M.Compare(head, NosolutionsIntroductionLabel)() is M.truth_value:
            return CertField(cert, 7)()
        return M.EmptyList

    def __call__(self):
        return self.result


class ReplaceCertField(M.Edge):
    def __init__(self, cert, index, value):
        self._value = value
        if M.IsPair(cert)() is M.false_value:
            self.result = M.EmptyList
        else:
            rebuilt = self._replace(M.Tail(cert)(), index)
            if rebuilt is None:
                self.result = M.EmptyList
            else:
                self.result = M.Pair(M.Head(cert)(), rebuilt)
        super().__init__(inputs=M.Pair(cert, M.EmptyList), results=self.result)

    def _replace(self, node, index):
        if M.IsPair(node)() is M.false_value:
            return None
        if index == 0:
            return M.Pair(self._value, M.Tail(node)())
        rest = self._replace(M.Tail(node)(), index - 1)
        if rest is None:
            return None
        return M.Pair(M.Head(node)(), rest)

    def __call__(self):
        return self.result


class CheckCertificate(M.Edge):
    def __init__(self, cert, globals_chain, trusted_chain):
        self._globals = globals_chain
        self._trusted = trusted_chain
        self.result = self._check(cert)
        super().__init__(
            inputs=M.Pair(cert, M.Pair(globals_chain, M.Pair(trusted_chain, M.EmptyList))),
            results=self.result,
        )

    def _check(self, cert):
        head = CertHead(cert)()
        if M.Compare(head, BinderAxiomLabel)() is M.truth_value:
            return self._check_axiom(cert)
        if M.Compare(head, HumanSuppliedTrustedTheoremLabel)() is M.truth_value:
            return self._check_trusted(cert)
        if M.Compare(head, ForallIntroductionLabel)() is M.truth_value:
            return self._check_forall(cert)
        if M.Compare(head, ImpliesIntroductionLabel)() is M.truth_value:
            return self._check_implies(cert)
        if M.Compare(head, ContradictionIntroductionLabel)() is M.truth_value:
            return self._check_contradiction(cert)
        if M.Compare(head, NosolutionsIntroductionLabel)() is M.truth_value:
            return self._check_nosolutions(cert)
        return M.false_value

    def _field(self, cert, index):
        return CertField(cert, index)()

    def _shape_ok(self, cert, label, count):
        if M.IsPair(cert)() is M.false_value:
            return M.false_value
        if M.Compare(M.Head(cert)(), label)() is M.false_value:
            return M.false_value
        node = M.Tail(cert)()
        step = 0
        while step < count:
            if M.IsPair(node)() is M.false_value:
                return M.false_value
            node = M.Tail(node)()
            step = step + 1
        if M.IdentityCompare(node, M.EmptyList)() is M.false_value:
            return M.false_value
        return M.truth_value

    def _chain_len(self, chain):
        count = 0
        node = chain
        while M.IsPair(node)() is M.truth_value:
            count = count + 1
            node = M.Tail(node)()
        return count

    def _entry_term(self, entry):
        if M.IsPair(entry)() is M.false_value:
            return M.EmptyList
        rest = M.Tail(entry)()
        if M.IsPair(rest)() is M.false_value:
            return M.EmptyList
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.EmptyList
        return M.Head(rest)()

    def _chain_has(self, chain, term):
        node = chain
        while M.IsPair(node)() is M.truth_value:
            if M.Compare(M.Head(node)(), term)() is M.truth_value:
                return M.truth_value
            node = M.Tail(node)()
        return M.false_value

    def _no_free_in_scope(self, variable, scope):
        node = scope
        while M.IsPair(node)() is M.truth_value:
            if FreeOccurs(variable, self._entry_term(M.Head(node)()))() is M.truth_value:
                return M.false_value
            node = M.Tail(node)()
        return M.truth_value

    def _no_any_in_scope(self, variable, scope):
        node = scope
        while M.IsPair(node)() is M.truth_value:
            if AnyOccurs(variable, self._entry_term(M.Head(node)()))() is M.truth_value:
                return M.false_value
            node = M.Tail(node)()
        return M.truth_value

    def _is_false_or_contradiction(self, term):
        false_term = M.Pair(FalseLabel, M.EmptyList)
        if M.Compare(term, false_term)() is M.truth_value:
            return M.truth_value
        if M.IsPair(term)() is M.truth_value:
            if M.Compare(M.Head(term)(), ContradictionLabel)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def _is_eq_refl(self, term):
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if M.Compare(M.Head(term)(), EqLabel)() is M.false_value:
            return M.false_value
        args = M.Tail(term)()
        if M.IsPair(args)() is M.false_value:
            return M.false_value
        rest = M.Tail(args)()
        if M.IsPair(rest)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.false_value
        return M.Compare(M.Head(args)(), M.Head(rest)())()

    def _check_axiom(self, cert):
        if self._shape_ok(cert, BinderAxiomLabel, 4) is M.false_value:
            return M.false_value
        if M.Compare(self._field(cert, 0), M.Char(AxiomEqReflText))() is M.false_value:
            return M.false_value
        return self._is_eq_refl(self._field(cert, 1))

    def _check_trusted(self, cert):
        if self._shape_ok(cert, HumanSuppliedTrustedTheoremLabel, 4) is M.false_value:
            return M.false_value
        if M.Compare(self._field(cert, 1), M.Char(TrustedReasonText))() is M.false_value:
            return M.false_value
        return self._chain_has(self._trusted, self._field(cert, 0))

    def _evidence_ok(self, evidence, variable, scope):
        if M.IsPair(evidence)() is M.false_value:
            return M.false_value
        if M.Compare(M.Head(evidence)(), FreshnessEvidenceLabel)() is M.false_value:
            return M.false_value
        args = M.Tail(evidence)()
        if M.IsPair(args)() is M.false_value:
            return M.false_value
        rest = M.Tail(args)()
        if M.IsPair(rest)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.false_value
        if M.Compare(M.Head(args)(), variable)() is M.false_value:
            return M.false_value
        return ScopeSame(M.Head(rest)(), scope)()

    def _check_forall(self, cert):
        if self._shape_ok(cert, ForallIntroductionLabel, 8) is M.false_value:
            return M.false_value
        variable = self._field(cert, 0)
        body = self._field(cert, 1)
        fresh = self._field(cert, 2)
        evidence = self._field(cert, 3)
        subcert = self._field(cert, 4)
        scope = self._field(cert, 5)
        branch = self._field(cert, 6)
        conclusion = self._field(cert, 7)
        if P.IsVarPattern(variable)() is M.false_value:
            return M.false_value
        if P.IsVarPattern(fresh)() is M.false_value:
            return M.false_value
        if M.Compare(variable, fresh)() is M.truth_value:
            return M.false_value
        expected_conclusion = M.Pair(ForAllLabel, M.Pair(variable, M.Pair(body, M.EmptyList)))
        if M.Compare(conclusion, expected_conclusion)() is M.false_value:
            return M.false_value
        if self._evidence_ok(evidence, variable, scope) is M.false_value:
            return M.false_value
        if self._no_free_in_scope(variable, scope) is M.false_value:
            return M.false_value
        if AnyOccurs(fresh, body)() is M.truth_value:
            return M.false_value
        if self._no_any_in_scope(fresh, scope) is M.false_value:
            return M.false_value
        subst_pair = Subst(body, variable, fresh)()
        if M.Head(subst_pair)() is M.false_value:
            return M.false_value
        expected_sub = M.Tail(subst_pair)()
        if CheckCertificate(subcert, self._globals, self._trusted)() is M.false_value:
            return M.false_value
        if M.Compare(CertConclusion(subcert)(), expected_sub)() is M.false_value:
            return M.false_value
        if ScopeSame(CertScope(subcert)(), scope)() is M.false_value:
            return M.false_value
        if M.Compare(CertBranch(subcert)(), branch)() is M.false_value:
            return M.false_value
        return M.truth_value

    def _check_implies(self, cert):
        if self._shape_ok(cert, ImpliesIntroductionLabel, 5) is M.false_value:
            return M.false_value
        assumption = self._field(cert, 0)
        subcert = self._field(cert, 1)
        scope = self._field(cert, 2)
        branch = self._field(cert, 3)
        conclusion = self._field(cert, 4)
        if CheckCertificate(subcert, self._globals, self._trusted)() is M.false_value:
            return M.false_value
        sub_conclusion = CertConclusion(subcert)()
        expected = M.Pair(ImpliesLabel, M.Pair(assumption, M.Pair(sub_conclusion, M.EmptyList)))
        if M.Compare(conclusion, expected)() is M.false_value:
            return M.false_value
        if self._chain_has(self._globals, assumption) is M.truth_value:
            return M.false_value
        if M.Compare(CertBranch(subcert)(), branch)() is M.false_value:
            return M.false_value
        subscope = CertScope(subcert)()
        if self._chain_len(subscope) != self._chain_len(scope) + 1:
            return M.false_value
        if ScopeCovers(subscope, scope)() is M.false_value:
            return M.false_value
        if ScopeHasTerm(subscope, assumption)() is M.false_value:
            return M.false_value
        return M.truth_value

    def _check_contradiction(self, cert):
        if self._shape_ok(cert, ContradictionIntroductionLabel, 5) is M.false_value:
            return M.false_value
        assumption = self._field(cert, 0)
        subcert = self._field(cert, 1)
        scope = self._field(cert, 2)
        branch = self._field(cert, 3)
        conclusion = self._field(cert, 4)
        if CheckCertificate(subcert, self._globals, self._trusted)() is M.false_value:
            return M.false_value
        sub_conclusion = CertConclusion(subcert)()
        if self._is_false_or_contradiction(sub_conclusion) is M.false_value:
            return M.false_value
        expected = M.Pair(NotLabel, M.Pair(assumption, M.EmptyList))
        if M.Compare(conclusion, expected)() is M.false_value:
            return M.false_value
        if self._chain_has(self._globals, assumption) is M.truth_value:
            return M.false_value
        if M.Compare(CertBranch(subcert)(), branch)() is M.false_value:
            return M.false_value
        subscope = CertScope(subcert)()
        if self._chain_len(subscope) != self._chain_len(scope) + 1:
            return M.false_value
        if ScopeCovers(subscope, scope)() is M.false_value:
            return M.false_value
        if ScopeHasTerm(subscope, assumption)() is M.false_value:
            return M.false_value
        return M.truth_value

    def _check_nosolutions(self, cert):
        if self._shape_ok(cert, NosolutionsIntroductionLabel, 9) is M.false_value:
            return M.false_value
        domain = self._field(cert, 0)
        unknowns = self._field(cert, 1)
        equation = self._field(cert, 2)
        assumed = self._field(cert, 3)
        substituted = self._field(cert, 4)
        subcert = self._field(cert, 5)
        scope = self._field(cert, 6)
        branch = self._field(cert, 7)
        conclusion = self._field(cert, 8)
        if P.IsVarPattern(unknowns)() is M.false_value:
            return M.false_value
        if M.IsPair(assumed)() is M.false_value:
            return M.false_value
        if M.Compare(M.Head(assumed)(), InLabel)() is M.false_value:
            return M.false_value
        assumed_args = M.Tail(assumed)()
        if M.IsPair(assumed_args)() is M.false_value:
            return M.false_value
        assumed_rest = M.Tail(assumed_args)()
        if M.IsPair(assumed_rest)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Tail(assumed_rest)(), M.EmptyList)() is M.false_value:
            return M.false_value
        solution = M.Head(assumed_args)()
        assumed_domain = M.Head(assumed_rest)()
        if M.Compare(assumed_domain, domain)() is M.false_value:
            return M.false_value
        subst_pair = Subst(equation, unknowns, solution)()
        if M.Head(subst_pair)() is M.false_value:
            return M.false_value
        if M.Compare(substituted, M.Tail(subst_pair)())() is M.false_value:
            return M.false_value
        if CheckCertificate(subcert, self._globals, self._trusted)() is M.false_value:
            return M.false_value
        if M.Compare(CertBranch(subcert)(), branch)() is M.false_value:
            return M.false_value
        subscope = CertScope(subcert)()
        if self._chain_len(subscope) != self._chain_len(scope) + 2:
            return M.false_value
        if ScopeCovers(subscope, scope)() is M.false_value:
            return M.false_value
        if ScopeHasTerm(subscope, assumed)() is M.false_value:
            return M.false_value
        if ScopeHasTerm(subscope, substituted)() is M.false_value:
            return M.false_value
        if self._is_false_or_contradiction(CertConclusion(subcert)()) is M.false_value:
            return M.false_value
        expected = M.Pair(NotLabel, M.Pair(substituted, M.EmptyList))
        if M.Compare(conclusion, expected)() is M.false_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class CheckCertificateInScope(M.Edge):
    def __init__(self, cert, scope, branch, globals_chain, trusted_chain):
        if CheckCertificate(cert, globals_chain, trusted_chain)() is M.false_value:
            self.result = M.false_value
        elif ScopeSame(CertScope(cert)(), scope)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(CertBranch(cert)(), branch)() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(cert, M.Pair(scope, M.Pair(branch, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class SiblingScopesDisjoint(M.Edge):
    def __init__(self, left, right):
        self.result = self._disjoint(left, right)
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def _entry_term(self, entry):
        if M.IsPair(entry)() is M.false_value:
            return M.EmptyList
        rest = M.Tail(entry)()
        if M.IsPair(rest)() is M.false_value:
            return M.EmptyList
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.EmptyList
        return M.Head(rest)()

    def _disjoint(self, left, right):
        node = left
        while M.IsPair(node)() is M.truth_value:
            if ScopeHasTerm(right, self._entry_term(M.Head(node)()))() is M.truth_value:
                return M.false_value
            node = M.Tail(node)()
        return M.truth_value

    def __call__(self):
        return self.result


class BinderAxiom(M.Edge):
    def __init__(self, term, scope, branch):
        conclusion = M.Pair(EqLabel, M.Pair(term, M.Pair(term, M.EmptyList)))
        cert = M.Pair(
            BinderAxiomLabel,
            M.Pair(
                M.Char(AxiomEqReflText),
                M.Pair(conclusion, M.Pair(scope, M.Pair(branch, M.EmptyList))),
            ),
        )
        flag = CheckCertificate(cert, M.EmptyList, M.EmptyList)()
        if flag is M.truth_value:
            self.result = M.Pair(flag, cert)
        else:
            self.result = M.Pair(flag, M.EmptyList)
        super().__init__(inputs=M.Pair(term, M.Pair(scope, M.Pair(branch, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class TrustedTheorem(M.Edge):
    def __init__(self, statement, scope, branch, globals_chain, trusted_chain):
        cert = M.Pair(
            HumanSuppliedTrustedTheoremLabel,
            M.Pair(
                statement,
                M.Pair(
                    M.Char(TrustedReasonText),
                    M.Pair(scope, M.Pair(branch, M.EmptyList)),
                ),
            ),
        )
        flag = CheckCertificate(cert, globals_chain, trusted_chain)()
        if flag is M.truth_value:
            self.result = M.Pair(flag, cert)
        else:
            self.result = M.Pair(flag, M.EmptyList)
        super().__init__(inputs=M.Pair(statement, M.Pair(scope, M.Pair(branch, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class ForallIntroduction(M.Edge):
    def __init__(self, variable, body, fresh, evidence, subcert, scope, branch, globals_chain, trusted_chain):
        conclusion = M.Pair(ForAllLabel, M.Pair(variable, M.Pair(body, M.EmptyList)))
        cert = M.Pair(
            ForallIntroductionLabel,
            M.Pair(
                variable,
                M.Pair(
                    body,
                    M.Pair(
                        fresh,
                        M.Pair(
                            evidence,
                            M.Pair(subcert, M.Pair(scope, M.Pair(branch, M.Pair(conclusion, M.EmptyList)))),
                        ),
                    ),
                ),
            ),
        )
        flag = CheckCertificate(cert, globals_chain, trusted_chain)()
        if flag is M.truth_value:
            self.result = M.Pair(flag, cert)
        else:
            self.result = M.Pair(flag, M.EmptyList)
        super().__init__(inputs=M.Pair(variable, M.Pair(body, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ImpliesIntroduction(M.Edge):
    def __init__(self, assumption, subcert, scope, branch, globals_chain, trusted_chain):
        sub_conclusion = CertConclusion(subcert)()
        conclusion = M.Pair(ImpliesLabel, M.Pair(assumption, M.Pair(sub_conclusion, M.EmptyList)))
        cert = M.Pair(
            ImpliesIntroductionLabel,
            M.Pair(assumption, M.Pair(subcert, M.Pair(scope, M.Pair(branch, M.Pair(conclusion, M.EmptyList))))),
        )
        flag = CheckCertificate(cert, globals_chain, trusted_chain)()
        if flag is M.truth_value:
            self.result = M.Pair(flag, cert)
        else:
            self.result = M.Pair(flag, M.EmptyList)
        super().__init__(inputs=M.Pair(assumption, M.Pair(subcert, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ContradictionIntroduction(M.Edge):
    def __init__(self, assumption, subcert, scope, branch, globals_chain, trusted_chain):
        conclusion = M.Pair(NotLabel, M.Pair(assumption, M.EmptyList))
        cert = M.Pair(
            ContradictionIntroductionLabel,
            M.Pair(assumption, M.Pair(subcert, M.Pair(scope, M.Pair(branch, M.Pair(conclusion, M.EmptyList))))),
        )
        flag = CheckCertificate(cert, globals_chain, trusted_chain)()
        if flag is M.truth_value:
            self.result = M.Pair(flag, cert)
        else:
            self.result = M.Pair(flag, M.EmptyList)
        super().__init__(inputs=M.Pair(assumption, M.Pair(subcert, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class NoSolutionsIntroduction(M.Edge):
    def __init__(
        self, domain, unknowns, equation, assumed, substituted, subcert, scope, branch, globals_chain, trusted_chain
    ):
        conclusion = M.Pair(NotLabel, M.Pair(substituted, M.EmptyList))
        cert = M.Pair(
            NosolutionsIntroductionLabel,
            M.Pair(
                domain,
                M.Pair(
                    unknowns,
                    M.Pair(
                        equation,
                        M.Pair(
                            assumed,
                            M.Pair(
                                substituted,
                                M.Pair(subcert, M.Pair(scope, M.Pair(branch, M.Pair(conclusion, M.EmptyList)))),
                            ),
                        ),
                    ),
                ),
            ),
        )
        flag = CheckCertificate(cert, globals_chain, trusted_chain)()
        if flag is M.truth_value:
            self.result = M.Pair(flag, cert)
        else:
            self.result = M.Pair(flag, M.EmptyList)
        super().__init__(inputs=M.Pair(domain, M.Pair(unknowns, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class BinderShow(M.Edge):
    def __init__(self, term):
        self.result = self._render(term)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=M.EmptyList)

    def _atom_name(self, atom):
        for entry in ShowNames:
            if M.Compare(atom, entry[0])() is M.truth_value:
                return entry[1]
        try:
            value = atom()
        except Exception:
            return "#?"
        if value is None:
            return "#atom"
        return str(value)

    def _render_list(self, node):
        text = ""
        current = node
        while M.IsPair(current)() is M.truth_value:
            text = text + self._render(M.Head(current)()) + " "
            current = M.Tail(current)()
        if M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            text = text + ". " + self._render(current) + " "
        if len(text) == 0:
            return ""
        return text[0:len(text) - 1]

    def _is_var_shape(self, term):
        if M.Compare(M.Head(term)(), M.VarTag)() is M.false_value:
            return M.false_value
        args = M.Tail(term)()
        if M.IsPair(args)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(M.Tail(args)(), M.EmptyList)() is M.false_value:
            return M.false_value
        return M.truth_value

    def _render(self, term):
        if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
            return "()"
        if M.IsPair(term)() is M.truth_value:
            if self._is_var_shape(term) is M.truth_value:
                return self._render(M.Head(M.Tail(term)())())
            return "(" + self._render_list(term) + ")"
        return self._atom_name(term)

    def __call__(self):
        return self.result


__all__ = (
    "TrustedReasonText",
    "AxiomEqReflText",
    "ShowNames",
    "BinderVar",
    "ForallTerm",
    "ImpliesTerm",
    "FalseTerm",
    "NotTerm",
    "EqTerm",
    "PlusTerm",
    "GreaterTerm",
    "InTerm",
    "ContradictionTerm",
    "ScopeEntry",
    "FreshnessEvidence",
    "Subst",
    "FreeOccurs",
    "AnyOccurs",
    "ScopeHasTerm",
    "ScopeCovers",
    "ScopeSame",
    "CertHead",
    "CertField",
    "CertConclusion",
    "CertScope",
    "CertBranch",
    "ReplaceCertField",
    "CheckCertificate",
    "CheckCertificateInScope",
    "SiblingScopesDisjoint",
    "BinderAxiom",
    "TrustedTheorem",
    "ForallIntroduction",
    "ImpliesIntroduction",
    "ContradictionIntroduction",
    "NoSolutionsIntroduction",
    "BinderShow",
)
