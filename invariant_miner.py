# ============================================================
# G4 / CL2B — Invariant Trace Miner & Unreachability Prover
# Mines structural invariants from execution traces and domain rules,
# packages discoveries into untrusted CandidateMacro envelopes, and
# constructs unreachability proofs under strict machine constraints.
# ============================================================
from . import evaluator as Eval
from . import invariance as Inv
from . import labels as L
from . import machine as M
from . import proof as P


class InvariantCertificate(M.Edge):
    """
    Machine-native certificate representing a verified invariant property.
    inputs: [phi, rules, trace]
    results: Pair(InvariantCertificateLabel, Pair(phi, Pair(rules, Pair(trace, EmptyList))))
    """

    def __init__(self, phi, rules, trace):
        self.phi = phi
        self.rules = rules
        self.trace = trace
        self.result = M.Pair(
            L.InvariantCertificateLabel,
            M.Pair(
                phi,
                M.Pair(
                    rules,
                    M.Pair(trace, M.EmptyList),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                phi,
                M.Pair(rules, M.Pair(trace, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InvariantCertificatePhi(M.Edge):
    def __init__(self, cert):
        self.result = M.Head(M.Tail(cert)())()
        super().__init__(inputs=M.Pair(cert, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InvariantCertificateRules(M.Edge):
    def __init__(self, cert):
        self.result = M.Head(M.Tail(M.Tail(cert)())())()
        super().__init__(inputs=M.Pair(cert, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InvariantCertificateProvenance(M.Edge):
    def __init__(self, cert):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(cert)())())()
        )()
        super().__init__(inputs=M.Pair(cert, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CheckInvariantPreservationAcrossRules(M.Edge):
    """
    Verifies that an invariant property Phi is preserved by every rule in a ruleset.
    """

    def __init__(self, phi, rules, registry):
        self.registry = registry
        self.result = self._check_all_rec(phi, rules)
        super().__init__(
            inputs=M.Pair(
                phi,
                M.Pair(rules, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _check_all_rec(self, phi, cur):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.EmptyList)

        rule = M.Head(cur)()
        pres_res = Inv.Preserves(rule, phi, self.registry)()
        if Inv.IsPreserves(pres_res)() is M.false_value:
            return M.Pair(
                M.false_value,
                M.Pair(rule, M.Pair(pres_res, M.EmptyList)),
            )

        return self._check_all_rec(phi, M.Tail(cur)())

    def __call__(self):
        return self.result


class ExtractTraceStates(M.Edge):
    """
    Extracts all visited intermediate states from an execution trace.
    Returns: Pair(start, [step0.next, step1.next, ...])
    """

    def __init__(self, trace, start, registry):
        self.registry = registry
        self.result = self._extract(trace, start)
        super().__init__(
            inputs=M.Pair(
                trace,
                M.Pair(start, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _extract_steps_rec(self, cur_steps):
        if M.IdentityCompare(cur_steps, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        step = M.Head(cur_steps)()
        next_state = P.StepNext(step, self.registry)()
        return M.Pair(next_state, self._extract_steps_rec(M.Tail(cur_steps)()))

    def _extract(self, trace, start):
        steps = P.DerivationSteps(trace, self.registry)()
        rest_states = self._extract_steps_rec(steps)
        return M.Pair(start, rest_states)

    def __call__(self):
        return self.result


class MineInvariantFromTrace(M.Edge):
    """
    Mines invariant candidates from execution traces by testing candidate
    property templates against the problem domain ruleset.
    """

    def __init__(self, trace, start, rules, candidate_templates, registry):
        self.registry = registry
        self.result = self._mine_rec(candidate_templates, trace, start, rules)
        super().__init__(
            inputs=M.Pair(
                trace,
                M.Pair(
                    start,
                    M.Pair(
                        rules,
                        M.Pair(
                            candidate_templates,
                            M.Pair(registry, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _mine_rec(self, cur_templates, trace, start, rules):
        if M.IdentityCompare(cur_templates, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)

        phi = M.Head(cur_templates)()
        pres_check = CheckInvariantPreservationAcrossRules(
            phi, rules, self.registry
        )()
        is_preserved = M.Head(pres_check)()

        if M.IdentityCompare(is_preserved, M.truth_value)() is M.truth_value:
            cert = InvariantCertificate(phi, rules, trace)()
            return M.Pair(M.truth_value, M.Pair(cert, M.EmptyList))

        return self._mine_rec(M.Tail(cur_templates)(), trace, start, rules)

    def __call__(self):
        return self.result


class MineInvariantToCandidateMacro(M.Edge):
    """
    Mines an invariant property from traces and constructs an untrusted
    CandidateMacro ready for evaluation by CL4 and checking by CL3B.
    """

    def __init__(
        self,
        trace,
        start_pattern,
        goal_pattern,
        rules,
        candidate_templates,
        macro_id,
        plan,
        registry,
    ):
        self.registry = registry
        self.result = self._mine_macro(
            trace,
            start_pattern,
            goal_pattern,
            rules,
            candidate_templates,
            macro_id,
            plan,
        )
        super().__init__(
            inputs=M.Pair(
                trace,
                M.Pair(
                    start_pattern,
                    M.Pair(
                        goal_pattern,
                        M.Pair(
                            rules,
                            M.Pair(
                                candidate_templates,
                                M.Pair(
                                    macro_id,
                                    M.Pair(
                                        plan,
                                        M.Pair(registry, M.EmptyList),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def _mine_macro(
        self,
        trace,
        start_pattern,
        goal_pattern,
        rules,
        candidate_templates,
        macro_id,
        plan,
    ):
        mine_res = MineInvariantFromTrace(
            trace, start_pattern, rules, candidate_templates, self.registry
        )()
        is_success = M.Head(mine_res)()

        if M.IdentityCompare(is_success, M.truth_value)() is M.truth_value:
            cert = M.Head(M.Tail(mine_res)())()
            macro = Eval.CandidateMacro(
                macro_id, start_pattern, goal_pattern, plan
            )()
            return M.Pair(
                L.CandidateMacroLabel,
                M.Pair(macro, M.Pair(cert, M.EmptyList)),
            )

        return M.Pair(M.false_value, M.EmptyList)

    def __call__(self):
        return self.result


class EnsureFactList(M.Edge):
    """
    Normalizes a state representation into a machine-native list of facts.
    """

    def __init__(self, state):
        if P.IsKnowledge(state)() is M.truth_value:
            self.result = P.KnowledgeFacts(state)()
        elif M.IsPair(state)() is M.truth_value:
            self.result = state
        elif M.IdentityCompare(state, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            self.result = M.Pair(state, M.EmptyList)
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class UnreachabilityProverByInvariant(M.Edge):
    """
    Constructs a proof of mathematical unreachability by invariant obstruction:
    if Phi(start) != Phi(target) and all rules preserve Phi, then target is
    mathematically unreachable from start.
    """

    def __init__(self, start, target, rules, phi, registry):
        self.registry = registry
        self.result = self._prove_unreachable(start, target, rules, phi)
        super().__init__(
            inputs=M.Pair(
                start,
                M.Pair(
                    target,
                    M.Pair(
                        rules,
                        M.Pair(phi, M.Pair(registry, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _prove_unreachable(self, start, target, rules, phi):
        pres_check = CheckInvariantPreservationAcrossRules(
            phi, rules, self.registry
        )()
        is_preserved = M.Head(pres_check)()

        if M.IdentityCompare(is_preserved, M.truth_value)() is M.false_value:
            return M.Pair(L.InvariantRefutedLabel, M.Tail(pres_check)())

        start_facts = EnsureFactList(start)()
        target_facts = EnsureFactList(target)()
        phi_start = Inv.PhiReading(start_facts, phi)()
        phi_target = Inv.PhiReading(target_facts, phi)()

        if M.Compare(phi_start, phi_target)() is M.false_value:
            return M.Pair(
                L.UnreachableLabel,
                M.Pair(
                    start,
                    M.Pair(
                        target,
                        M.Pair(
                            phi,
                            M.Pair(
                                phi_start,
                                M.Pair(phi_target, M.EmptyList),
                            ),
                        ),
                    ),
                ),
            )

        return M.Pair(M.false_value, M.EmptyList)

    def __call__(self):
        return self.result


__all__ = (
    "InvariantCertificate",
    "InvariantCertificatePhi",
    "InvariantCertificateRules",
    "InvariantCertificateProvenance",
    "CheckInvariantPreservationAcrossRules",
    "ExtractTraceStates",
    "MineInvariantFromTrace",
    "MineInvariantToCandidateMacro",
    "EnsureFactList",
    "UnreachabilityProverByInvariant",
)
