from __future__ import annotations

import os
import subprocess
import sys

from . import machine as M
from . import proof as P
from . import binder as B
from .binder_toy import ToyCertificate, ToyCorrupted, ToyGoal
from .labels import (
    BinderAxiomLabel,
    ContradictionIntroductionLabel,
    EqLabel,
    FalseLabel,
    ForAllLabel,
    ForallIntroductionLabel,
    FreshnessEvidenceLabel,
    GreaterLabel,
    ImpliesIntroductionLabel,
    ImpliesLabel,
    NosolutionsIntroductionLabel,
    PlusLabel,
)

EvidenceDirName = "2026-09-14-logic-checker"


class TestSuite(M.Edge):
    def __init__(self):
        self._scan = (
            ImpliesLabel,
            FalseLabel,
            EqLabel,
            PlusLabel,
            GreaterLabel,
            ForallIntroductionLabel,
            ImpliesIntroductionLabel,
            ContradictionIntroductionLabel,
            FreshnessEvidenceLabel,
            BinderAxiomLabel,
            ForAllLabel,
            NosolutionsIntroductionLabel,
        )
        entries = (
            self._guarded(self._run_t10, "T10 generic_rewriter_cannot_close_shell_test"),
            self._guarded(self._run_t1, "T1 forall_reflexivity_closes_test"),
            self._guarded(self._run_t2, "T2 forall_missing_freshness_rejected_test"),
            self._guarded(self._run_t3, "T3 implication_identity_closes_test"),
            self._guarded(self._run_t4, "T4 implication_assumption_leak_rejected_test"),
            self._guarded(self._run_t5, "T5 contradiction_certificate_required_test"),
            self._guarded(self._run_t6, "T6 nosolutions_scoped_assumption_test"),
            self._guarded(self._run_t7, "T7 sibling_assumption_leak_rejected_test"),
            self._guarded(self._run_t8, "T8 corrupted_quantified_certificate_rejected_test"),
            self._guarded(self._run_t9, "T9 cold_replay_quantified_toy_test"),
            self._guarded(self._run_a1, "A1 discharge_removes_assumption_test"),
            self._guarded(self._run_a2, "A2 cross_branch_certificate_rejected_test"),
            self._guarded(self._run_a3, "A3 assumption_scope_escape_rejected_test"),
            self._guarded(self._run_a4, "A4 fresh_variable_reuse_test"),
        )
        self.transcript = entries
        overall = M.truth_value
        for entry in entries:
            if entry[1] is M.false_value:
                overall = M.false_value
        self.result = overall
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _guarded(self, thunk, fallback):
        try:
            return thunk()
        except Exception as exc:
            return (fallback, M.false_value, "raised: " + str(exc) + "\n")

    def _verdict(self, flag):
        if flag is M.truth_value:
            return "accept"
        return "reject"

    def _pass(self, flag):
        if flag is M.truth_value:
            return "PASS"
        return "FAIL"

    def _show(self, term):
        return B.BinderShow(term)()

    def _count(self, chain):
        total = 0
        node = chain
        while M.IsPair(node)() is M.truth_value:
            total = total + 1
            node = M.Tail(node)()
        return total

    def _mentions_binder(self, term):
        if M.IsPair(term)() is M.truth_value:
            if self._mentions_binder(M.Head(term)()) is M.truth_value:
                return M.truth_value
            return self._mentions_binder(M.Tail(term)())
        for label in self._scan:
            if M.Compare(term, label)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def _run_t10(self):
        from .main import PACK_PATHS, _runtime_namespace
        from .runtime import boot_from_packs

        name = "T10 generic_rewriter_cannot_close_shell_test"
        runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        graph = runtime.graph
        registry = M.FromContextGetConstructors(graph)()
        rules = P.CollectRules(M.FromContextGetAllRules(graph)())()
        rule_total = self._count(rules)
        goal = ToyGoal()()
        knowledge = P.Knowledge(M.Pair(goal, M.EmptyList))()
        applicable = P.FilterApplicableRules(rules, knowledge, registry)()
        app_total = self._count(applicable)
        mentioning = 0
        node = rules
        while M.IsPair(node)() is M.truth_value:
            rule = M.Head(node)()
            hit = M.false_value
            premises = P.RulePremises(rule)()
            cursor = premises
            while M.IsPair(cursor)() is M.truth_value:
                if self._mentions_binder(M.Head(cursor)()) is M.truth_value:
                    hit = M.truth_value
                cursor = M.Tail(cursor)()
            if self._mentions_binder(P.RuleReplacement(rule)()) is M.truth_value:
                hit = M.truth_value
            if hit is M.truth_value:
                mentioning = mentioning + 1
            node = M.Tail(node)()
        shell_kept = 0
        shown = 0
        detail = "packs loaded: " + str(len(PACK_PATHS)) + "\n"
        detail = detail + "rules collected: " + str(rule_total) + "\n"
        detail = detail + "rules mentioning binder heads: " + str(mentioning) + "\n"
        detail = detail + "applicable to knowledge holding toy goal: " + str(app_total) + "\n"
        detail = detail + "toy goal: " + self._show(goal) + "\n"
        node = applicable
        while M.IsPair(node)() is M.truth_value:
            rule = M.Head(node)()
            successor = M.Head(M.Rewrite(rule, goal, registry)())()
            kept = M.false_value
            if M.IsPair(successor)() is M.truth_value:
                if M.Compare(M.Head(successor)(), ForAllLabel)() is M.truth_value:
                    kept = M.truth_value
            if kept is M.truth_value:
                shell_kept = shell_kept + 1
            if shown < 8:
                detail = detail + "successor head: " + self._verdict(kept) + " as forall shell\n"
                shown = shown + 1
            node = M.Tail(node)()
        detail = detail + "successors keeping the forall shell: " + str(shell_kept) + " of " + str(app_total) + "\n"
        if mentioning == 0 and (app_total == 0 or shell_kept == app_total):
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = detail + "goal remains open: " + self._verdict(flag) + "\n"
        return (name, flag, detail)

    def _run_t1(self):
        name = "T1 forall_reflexivity_closes_test"
        var_x = B.BinderVar("x")()
        fresh = B.BinderVar("xf")()
        body = B.EqTerm(var_x, var_x)()
        branch = M.Char("b0")
        axiom_pair = B.BinderAxiom(fresh, M.EmptyList, branch)()
        axiom_flag = M.Head(axiom_pair)()
        evidence = B.FreshnessEvidence(var_x, M.EmptyList)()
        forall_pair = B.ForallIntroduction(
            var_x, body, fresh, evidence, M.Tail(axiom_pair)(), M.EmptyList, branch, M.EmptyList, M.EmptyList
        )()
        forall_flag = M.Head(forall_pair)()
        replay = B.CheckCertificate(M.Tail(forall_pair)(), M.EmptyList, M.EmptyList)()
        if axiom_flag is M.truth_value and forall_flag is M.truth_value and replay is M.truth_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "axiom leaf: " + self._verdict(axiom_flag) + "\n"
        detail = detail + "forall intro: " + self._verdict(forall_flag) + "\n"
        detail = detail + "replay: " + self._verdict(replay) + "\n"
        detail = detail + "conclusion: " + self._show(B.CertConclusion(M.Tail(forall_pair)())()) + "\n"
        return (name, flag, detail)

    def _run_t2(self):
        name = "T2 forall_missing_freshness_rejected_test"
        var_x = B.BinderVar("x")()
        fresh = B.BinderVar("xf")()
        body = B.EqTerm(var_x, var_x)()
        branch = M.Char("b0")
        open_assumption = B.GreaterTerm(var_x, M.Char("1"))()
        scope = M.Pair(B.ScopeEntry("s0", open_assumption)(), M.EmptyList)
        sub_pair = B.BinderAxiom(fresh, scope, branch)()
        covering = B.FreshnessEvidence(var_x, scope)()
        attempt_covering = B.ForallIntroduction(
            var_x, body, fresh, covering, M.Tail(sub_pair)(), scope, branch, M.EmptyList, M.EmptyList
        )()
        empty_evidence = B.FreshnessEvidence(var_x, M.EmptyList)()
        attempt_bare = B.ForallIntroduction(
            var_x, body, fresh, empty_evidence, M.Tail(sub_pair)(), scope, branch, M.EmptyList, M.EmptyList
        )()
        flag_covering = M.Head(attempt_covering)()
        flag_bare = M.Head(attempt_bare)()
        if flag_covering is M.false_value and flag_bare is M.false_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "free var in open assumption: " + self._verdict(flag_covering) + " (expect reject)\n"
        detail = detail + "evidence missing coverage: " + self._verdict(flag_bare) + " (expect reject)\n"
        return (name, flag, detail)

    def _run_t3(self):
        name = "T3 implication_identity_closes_test"
        atom_a = M.Char("a")
        prop = B.EqTerm(atom_a, atom_a)()
        branch = M.Char("b0")
        inner = M.Pair(B.ScopeEntry("s0", prop)(), M.EmptyList)
        sub_pair = B.BinderAxiom(atom_a, inner, branch)()
        sub_flag = M.Head(sub_pair)()
        implies_pair = B.ImpliesIntroduction(prop, M.Tail(sub_pair)(), M.EmptyList, branch, M.EmptyList, M.EmptyList)()
        implies_flag = M.Head(implies_pair)()
        replay = B.CheckCertificate(M.Tail(implies_pair)(), M.EmptyList, M.EmptyList)()
        if sub_flag is M.truth_value and implies_flag is M.truth_value and replay is M.truth_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "axiom leaf: " + self._verdict(sub_flag) + "\n"
        detail = detail + "implies intro: " + self._verdict(implies_flag) + "\n"
        detail = detail + "replay: " + self._verdict(replay) + "\n"
        detail = detail + "conclusion: " + self._show(B.CertConclusion(M.Tail(implies_pair)())()) + "\n"
        return (name, flag, detail)

    def _run_t4(self):
        name = "T4 implication_assumption_leak_rejected_test"
        atom_a = M.Char("a")
        prop = B.EqTerm(atom_a, atom_a)()
        extra = B.GreaterTerm(atom_a, M.Char("1"))()
        branch = M.Char("b0")
        wide = M.Pair(B.ScopeEntry("s1", extra)(), M.Pair(B.ScopeEntry("s0", prop)(), M.EmptyList))
        sub_wide = B.BinderAxiom(atom_a, wide, branch)()
        attempt_wide = B.ImpliesIntroduction(prop, M.Tail(sub_wide)(), M.EmptyList, branch, M.EmptyList, M.EmptyList)()
        wrong = M.Pair(B.ScopeEntry("s0", extra)(), M.EmptyList)
        sub_wrong = B.BinderAxiom(atom_a, wrong, branch)()
        attempt_wrong = B.ImpliesIntroduction(
            prop, M.Tail(sub_wrong)(), M.EmptyList, branch, M.EmptyList, M.EmptyList
        )()
        flag_wide = M.Head(attempt_wide)()
        flag_wrong = M.Head(attempt_wrong)()
        if flag_wide is M.false_value and flag_wrong is M.false_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "extra assumption beyond scope: " + self._verdict(flag_wide) + " (expect reject)\n"
        detail = detail + "declared assumption absent: " + self._verdict(flag_wrong) + " (expect reject)\n"
        return (name, flag, detail)

    def _run_t5(self):
        name = "T5 contradiction_certificate_required_test"
        atom_a = M.Char("a")
        assumption = B.GreaterTerm(atom_a, M.Char("1"))()
        branch = M.Char("b0")
        inner = M.Pair(B.ScopeEntry("s0", assumption)(), M.EmptyList)
        false_term = B.FalseTerm()()
        trusted_false = M.Pair(false_term, M.EmptyList)
        good_leaf = B.TrustedTheorem(false_term, inner, branch, M.EmptyList, trusted_false)()
        good_flag = M.Head(good_leaf)()
        good_cert = B.ContradictionIntroduction(
            assumption, M.Tail(good_leaf)(), M.EmptyList, branch, M.EmptyList, trusted_false
        )()
        good_contra = M.Head(good_cert)()
        bad_leaf = B.BinderAxiom(atom_a, inner, branch)()
        bad_cert = B.ContradictionIntroduction(
            assumption, M.Tail(bad_leaf)(), M.EmptyList, branch, M.EmptyList, M.EmptyList
        )()
        bad_contra = M.Head(bad_cert)()
        if good_flag is M.truth_value and good_contra is M.truth_value and bad_contra is M.false_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "false leaf: " + self._verdict(good_flag) + "\n"
        detail = detail + "valid contradiction intro: " + self._verdict(good_contra) + "\n"
        detail = detail + "non-false subderivation: " + self._verdict(bad_contra) + " (expect reject)\n"
        detail = detail + "conclusion: " + self._show(B.CertConclusion(M.Tail(good_cert)())()) + "\n"
        return (name, flag, detail)

    def _run_t6(self):
        name = "T6 nosolutions_scoped_assumption_test"
        domain = M.Char("nat")
        unknown = B.BinderVar("k")()
        equation = B.EqTerm(B.PlusTerm(unknown, M.Char("0"))(), M.Char("1"))()
        solution = M.Char("s")
        assumed = B.InTerm(solution, domain)()
        branch = M.Char("b0")
        subst_pair = B.Subst(equation, unknown, solution)()
        subst_flag = M.Head(subst_pair)()
        substituted = M.Tail(subst_pair)()
        inner = M.Pair(B.ScopeEntry("s1", substituted)(), M.Pair(B.ScopeEntry("s0", assumed)(), M.EmptyList))
        false_term = B.FalseTerm()()
        trusted_false = M.Pair(false_term, M.EmptyList)
        leaf = B.TrustedTheorem(false_term, inner, branch, M.EmptyList, trusted_false)()
        leaf_flag = M.Head(leaf)()
        good = B.NoSolutionsIntroduction(
            domain, unknown, equation, assumed, substituted, M.Tail(leaf)(), M.EmptyList, branch, M.EmptyList,
            trusted_false,
        )()
        good_flag = M.Head(good)()
        replay = B.CheckCertificate(M.Tail(good)(), M.EmptyList, trusted_false)()
        wrong_sub = B.EqTerm(B.PlusTerm(solution, M.Char("0"))(), M.Char("0"))()
        bad = B.NoSolutionsIntroduction(
            domain, unknown, equation, assumed, wrong_sub, M.Tail(leaf)(), M.EmptyList, branch, M.EmptyList,
            trusted_false,
        )()
        bad_flag = M.Head(bad)()
        if (
            subst_flag is M.truth_value
            and leaf_flag is M.truth_value
            and good_flag is M.truth_value
            and replay is M.truth_value
            and bad_flag is M.false_value
        ):
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "substitution: " + self._verdict(subst_flag) + "\n"
        detail = detail + "false leaf: " + self._verdict(leaf_flag) + "\n"
        detail = detail + "nosolutions intro: " + self._verdict(good_flag) + "\n"
        detail = detail + "replay: " + self._verdict(replay) + "\n"
        detail = detail + "wrong substituted equation: " + self._verdict(bad_flag) + " (expect reject)\n"
        detail = detail + "conclusion: " + self._show(B.CertConclusion(M.Tail(good)())()) + "\n"
        return (name, flag, detail)

    def _run_t7(self):
        name = "T7 sibling_assumption_leak_rejected_test"
        assumption_a = B.GreaterTerm(M.Char("a"), M.Char("1"))()
        assumption_b = B.GreaterTerm(M.Char("b"), M.Char("1"))()
        scope_a = M.Pair(B.ScopeEntry("s0", assumption_a)(), M.EmptyList)
        scope_b = M.Pair(B.ScopeEntry("s0", assumption_b)(), M.EmptyList)
        branch_a = M.Char("b1")
        branch_b = M.Char("b2")
        statement = B.EqTerm(M.Char("c"), M.Char("c"))()
        trusted = M.Pair(statement, M.EmptyList)
        leaf_a = B.TrustedTheorem(statement, scope_a, branch_a, M.EmptyList, trusted)()
        leaf_flag = M.Head(leaf_a)()
        disjoint = B.SiblingScopesDisjoint(scope_a, scope_b)()
        cross = B.CheckCertificateInScope(M.Tail(leaf_a)(), scope_b, branch_b, M.EmptyList, trusted)()
        if leaf_flag is M.truth_value and disjoint is M.truth_value and cross is M.false_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "branch A leaf: " + self._verdict(leaf_flag) + "\n"
        detail = detail + "sibling scopes disjoint: " + self._verdict(disjoint) + "\n"
        detail = detail + "A certificate in B scope: " + self._verdict(cross) + " (expect reject)\n"
        return (name, flag, detail)

    def _run_t8(self):
        name = "T8 corrupted_quantified_certificate_rejected_test"
        toy = ToyCertificate()
        toy_pair = toy()
        toy_flag = M.Head(toy_pair)()
        globals_chain = toy.toy_globals
        trusted_chain = toy.toy_trusted
        bad0 = ToyCorrupted(0)()
        bad1 = ToyCorrupted(1)()
        bad2 = ToyCorrupted(2)()
        flag0 = B.CheckCertificate(bad0, globals_chain, trusted_chain)()
        flag1 = B.CheckCertificate(bad1, globals_chain, trusted_chain)()
        flag2 = B.CheckCertificate(bad2, globals_chain, trusted_chain)()
        if (
            toy_flag is M.truth_value
            and flag0 is M.false_value
            and flag1 is M.false_value
            and flag2 is M.false_value
        ):
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "uncorrupted toy: " + self._verdict(toy_flag) + "\n"
        detail = detail + "corrupted conclusion: " + self._verdict(flag0) + " (expect reject)\n"
        detail = detail + "corrupted fresh variable: " + self._verdict(flag1) + " (expect reject)\n"
        detail = detail + "corrupted freshness evidence: " + self._verdict(flag2) + " (expect reject)\n"
        return (name, flag, detail)

    def _run_t9(self):
        name = "T9 cold_replay_quantified_toy_test"
        toy = ToyCertificate()
        toy_pair = toy()
        toy_flag = M.Head(toy_pair)()
        cert = M.Tail(toy_pair)()
        replay = B.CheckCertificate(cert, toy.toy_globals, toy.toy_trusted)()
        conclusion = B.CertConclusion(cert)()
        goal_match = M.Compare(conclusion, ToyGoal()())()
        fresh_build = ToyCertificate()()
        fresh_replay = B.CheckCertificate(M.Tail(fresh_build)(), toy.toy_globals, toy.toy_trusted)()
        if (
            toy_flag is M.truth_value
            and replay is M.truth_value
            and goal_match is M.truth_value
            and M.Head(fresh_build)() is M.truth_value
            and fresh_replay is M.truth_value
        ):
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "trusted leaf: " + self._verdict(toy.leaf_flag) + "\n"
        detail = detail + "implies intro: " + self._verdict(toy.implies_flag) + "\n"
        detail = detail + "forall intro: " + self._verdict(toy.forall_flag) + "\n"
        detail = detail + "replay: " + self._verdict(replay) + "\n"
        detail = detail + "fresh rebuild replay: " + self._verdict(fresh_replay) + "\n"
        detail = detail + "conclusion matches goal: " + self._verdict(goal_match) + "\n"
        detail = detail + "conclusion: " + self._show(conclusion) + "\n"
        detail = detail + "trusted statement: " + self._show(M.Head(toy.toy_trusted)()) + "\n"
        return (name, flag, detail)

    def _run_a1(self):
        name = "A1 discharge_removes_assumption_test"
        atom_a = M.Char("a")
        prop = B.EqTerm(atom_a, atom_a)()
        branch = M.Char("b0")
        inner = M.Pair(B.ScopeEntry("s0", prop)(), M.EmptyList)
        leaf = B.BinderAxiom(atom_a, inner, branch)()
        implies_pair = B.ImpliesIntroduction(prop, M.Tail(leaf)(), M.EmptyList, branch, M.EmptyList, M.EmptyList)()
        implies_flag = M.Head(implies_pair)()
        discharged_scope = B.CertScope(M.Tail(implies_pair)())()
        still_present = B.ScopeHasTerm(discharged_scope, prop)()
        reuse = B.CheckCertificateInScope(M.Tail(leaf)(), M.EmptyList, branch, M.EmptyList, M.EmptyList)()
        if implies_flag is M.truth_value and still_present is M.false_value and reuse is M.false_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "implies intro: " + self._verdict(implies_flag) + "\n"
        detail = detail + "assumption present after discharge: " + self._verdict(still_present) + " (expect reject)\n"
        detail = detail + "inner leaf replayed at outer scope: " + self._verdict(reuse) + " (expect reject)\n"
        return (name, flag, detail)

    def _run_a2(self):
        name = "A2 cross_branch_certificate_rejected_test"
        scope_a = M.Pair(B.ScopeEntry("s0", B.GreaterTerm(M.Char("a"), M.Char("1"))())(), M.EmptyList)
        scope_b = M.Pair(B.ScopeEntry("s0", B.GreaterTerm(M.Char("b"), M.Char("1"))())(), M.EmptyList)
        branch_a = M.Char("b1")
        branch_b = M.Char("b2")
        statement = B.EqTerm(M.Char("v"), M.Char("v"))()
        trusted = M.Pair(statement, M.EmptyList)
        cert_a = M.Tail(B.TrustedTheorem(statement, scope_a, branch_a, M.EmptyList, trusted)())()
        cert_b = M.Tail(B.TrustedTheorem(statement, scope_b, branch_b, M.EmptyList, trusted)())()
        identical = M.Compare(B.CertConclusion(cert_a)(), B.CertConclusion(cert_b)())()
        cross_ab = B.CheckCertificateInScope(cert_a, scope_b, branch_b, M.EmptyList, trusted)()
        cross_ba = B.CheckCertificateInScope(cert_b, scope_a, branch_a, M.EmptyList, trusted)()
        if identical is M.truth_value and cross_ab is M.false_value and cross_ba is M.false_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "conclusions structurally identical: " + self._verdict(identical) + "\n"
        detail = detail + "A certificate in B scope: " + self._verdict(cross_ab) + " (expect reject)\n"
        detail = detail + "B certificate in A scope: " + self._verdict(cross_ba) + " (expect reject)\n"
        return (name, flag, detail)

    def _run_a3(self):
        name = "A3 assumption_scope_escape_rejected_test"
        outer = B.GreaterTerm(M.Char("o"), M.Char("1"))()
        inner = B.GreaterTerm(M.Char("i"), M.Char("1"))()
        branch = M.Char("b0")
        statement = B.EqTerm(M.Char("e"), M.Char("e"))()
        trusted = M.Pair(statement, M.EmptyList)
        wide = M.Pair(B.ScopeEntry("s1", inner)(), M.Pair(B.ScopeEntry("s0", outer)(), M.EmptyList))
        sub_wide = M.Tail(B.TrustedTheorem(statement, wide, branch, M.EmptyList, trusted)())()
        escape_implies = B.ImpliesIntroduction(inner, sub_wide, M.EmptyList, branch, M.EmptyList, trusted)()
        flag_implies = M.Head(escape_implies)()
        var_x = B.BinderVar("x")()
        fresh = B.BinderVar("xf")()
        outer_scope = M.Pair(B.ScopeEntry("s0", outer)(), M.EmptyList)
        sub_outer = M.Tail(B.BinderAxiom(fresh, outer_scope, branch)())()
        evidence = B.FreshnessEvidence(var_x, M.EmptyList)()
        escape_forall = B.ForallIntroduction(
            var_x, B.EqTerm(var_x, var_x)(), fresh, evidence, sub_outer, M.EmptyList, branch, M.EmptyList, M.EmptyList
        )()
        flag_forall = M.Head(escape_forall)()
        if flag_implies is M.false_value and flag_forall is M.false_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "implies escape with outer hypothesis: " + self._verdict(flag_implies) + " (expect reject)\n"
        detail = detail + "forall escape with outer hypothesis: " + self._verdict(flag_forall) + " (expect reject)\n"
        return (name, flag, detail)

    def _run_a4(self):
        name = "A4 fresh_variable_reuse_test"
        var_x = B.BinderVar("x")()
        var_y = B.BinderVar("y")()
        fresh = B.BinderVar("xf")()
        first_sub = M.Tail(B.BinderAxiom(fresh, M.EmptyList, M.Char("b0"))())()
        first_evidence = B.FreshnessEvidence(var_x, M.EmptyList)()
        first = B.ForallIntroduction(
            var_x, B.EqTerm(var_x, var_x)(), fresh, first_evidence, first_sub, M.EmptyList, M.Char("b0"),
            M.EmptyList, M.EmptyList,
        )()
        first_flag = M.Head(first)()
        second_sub = M.Tail(B.BinderAxiom(fresh, M.EmptyList, M.Char("b1"))())()
        second_evidence = B.FreshnessEvidence(var_y, M.EmptyList)()
        second = B.ForallIntroduction(
            var_y, B.EqTerm(var_y, var_y)(), fresh, second_evidence, second_sub, M.EmptyList, M.Char("b1"),
            M.EmptyList, M.EmptyList,
        )()
        second_flag = M.Head(second)()
        tainted = M.Pair(B.ScopeEntry("s0", B.GreaterTerm(fresh, M.Char("1"))())(), M.EmptyList)
        tainted_sub = M.Tail(B.BinderAxiom(fresh, tainted, M.Char("b2"))())()
        tainted_evidence = B.FreshnessEvidence(var_x, tainted)()
        tainted_attempt = B.ForallIntroduction(
            var_x, B.EqTerm(var_x, var_x)(), fresh, tainted_evidence, tainted_sub, tainted, M.Char("b2"),
            M.EmptyList, M.EmptyList,
        )()
        tainted_flag = M.Head(tainted_attempt)()
        if first_flag is M.truth_value and second_flag is M.truth_value and tainted_flag is M.false_value:
            flag = M.truth_value
        else:
            flag = M.false_value
        detail = "first instance: " + self._verdict(first_flag) + "\n"
        detail = detail + "sibling reuse in disjoint scope: " + self._verdict(second_flag) + "\n"
        detail = detail + "reuse where scope names it: " + self._verdict(tainted_flag) + " (expect reject)\n"
        return (name, flag, detail)

    def __call__(self):
        return self.result


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cold-replay":
        cold_toy = ToyCertificate()
        cold_pair = cold_toy()
        cold_flag = M.Head(cold_pair)()
        cold_cert = M.Tail(cold_pair)()
        cold_check = B.CheckCertificate(cold_cert, cold_toy.toy_globals, cold_toy.toy_trusted)()
        if cold_flag is M.truth_value:
            print("cold-replay: constructor-flag: accept")
        else:
            print("cold-replay: constructor-flag: reject")
        if cold_check is M.truth_value:
            print("cold-replay: checker-verdict: accept")
        else:
            print("cold-replay: checker-verdict: reject")
        print("cold-replay: conclusion: " + B.BinderShow(B.CertConclusion(cold_cert)())())
    else:
        suite = TestSuite()
        passed = 0
        total = 0
        output = ""
        for record in suite.transcript:
            total = total + 1
            if record[1] is M.truth_value:
                passed = passed + 1
                print(record[0] + ": PASS")
            else:
                print(record[0] + ": FAIL")
            output = output + record[0] + ": " + suite._pass(record[1]) + "\n" + record[2] + "\n"
        output = output + "total: " + str(passed) + "/" + str(total) + "\n"
        print("total: " + str(passed) + "/" + str(total))
        package_dir = os.path.dirname(os.path.abspath(__file__))
        evidence_dir = os.path.join(package_dir, "verification", EvidenceDirName)
        try:
            os.makedirs(evidence_dir)
        except OSError:
            pass
        before_text = "pending"
        after_text = "pending"
        corrupted_text = "pending"
        for record in suite.transcript:
            if record[0] == "T10 generic_rewriter_cannot_close_shell_test":
                before_text = record[2]
            if record[0] == "T9 cold_replay_quantified_toy_test":
                after_text = record[2]
            if record[0] == "T8 corrupted_quantified_certificate_rejected_test":
                corrupted_text = record[2]
        with open(os.path.join(evidence_dir, "test-output.txt"), "w") as handle:
            handle.write(output)
        with open(os.path.join(evidence_dir, "before.txt"), "w") as handle:
            handle.write("T10 generic rewriter cannot close the quantified shell\n\n" + before_text)
        with open(os.path.join(evidence_dir, "after.txt"), "w") as handle:
            handle.write("toy goal closed through introduction rules\n\n" + after_text)
        with open(os.path.join(evidence_dir, "corrupted-cert-rejected.txt"), "w") as handle:
            handle.write("single-field corruption is rejected on replay\n\n" + corrupted_text)
        parent_dir = os.path.dirname(package_dir)
        cold_args = (sys.executable, "-m", "cat_theo_machine.binder_tests", "cold-replay")
        cold_proc = subprocess.run(cold_args, cwd=parent_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
        cold_text = cold_proc.stdout.decode("utf-8", "replace")
        if cold_proc.returncode == 0 and "checker-verdict: accept" in cold_text:
            cold_verdict = "cold replay: PASS\n"
        else:
            cold_verdict = "cold replay: FAIL\n"
        with open(os.path.join(evidence_dir, "cold-replay.txt"), "w") as handle:
            handle.write("fresh-process rebuild plus recheck\nreturncode: " + str(cold_proc.returncode) + "\n" + cold_text + cold_verdict)
        print(cold_verdict[0:len(cold_verdict) - 1])
