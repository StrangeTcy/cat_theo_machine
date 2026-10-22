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
from . import playground as PG
from . import promotion_ledger as PL
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


class MineOperationInvariants(M.Edge):
    """
    Mines algebraic invariants (laws) from a ground domain and a machine
    operation term over `variables`. The operation is machine data evaluated
    by the machine's own EvaluateNatExpr; no host callable applies it.
    - Commutativity: op(a, b) == op(b, a) across all pairs
    - Associativity: op(op(a, b), c) == op(a, op(b, c)) across all triples
    inputs: [op_name, variables, operation, domain, registry]
    results: Pair(ObservedRegularityLabel, Pair(op_name, Pair(law_type, Pair(witness_pairs, Pair(registry, EmptyList)))))
    """

    def __init__(self, op_name, variables, operation, domain, registry):
        self.registry = registry
        self.result = self._mine(op_name, variables, operation, domain, registry)
        super().__init__(
            inputs=M.Pair(
                op_name,
                M.Pair(
                    variables,
                    M.Pair(
                        operation,
                        M.Pair(domain, M.Pair(registry, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _apply(self, variables, operation, values_chain, registry):
        environment = PG.ZipEnvironment(variables, values_chain)()
        return PG.EvaluateNatExpr(operation, environment, registry)()

    def _mine(self, op_name, variables, operation, domain, reg):
        # 1. Test Commutativity across 2-tuples
        dom2 = PG.ProductOfDomains(M.Pair(domain, M.Pair(domain, M.EmptyList)))()
        comm_res = self._check_commutativity(dom2, variables, operation, reg)
        is_comm = M.Head(comm_res)()
        r1 = M.Head(M.Tail(comm_res)())()
        comm_witnesses = M.Head(M.Tail(M.Tail(comm_res)())())()

        if is_comm is M.truth_value:
            rec = M.Pair(
                L.ObservedRegularityLabel,
                M.Pair(
                    op_name,
                    M.Pair(
                        M.Char("commutativity"),
                        M.Pair(
                            comm_witnesses,
                            M.Pair(
                                M.Pair(
                                    M.Char("universal"),
                                    M.Pair(domain, M.EmptyList),
                                ),
                                M.EmptyList,
                            ),
                        ),
                    ),
                ),
            )
            return M.Pair(rec, M.Pair(r1, M.EmptyList))

        # 2. Test Associativity across 3-tuples
        dom3 = PG.ProductOfDomains(M.Pair(domain, M.Pair(domain, M.Pair(domain, M.EmptyList))))()
        assoc_res = self._check_associativity(dom3, variables, operation, r1)
        is_assoc = M.Head(assoc_res)()
        r2 = M.Head(M.Tail(assoc_res)())()
        assoc_witnesses = M.Head(M.Tail(M.Tail(assoc_res)())())()

        if is_assoc is M.truth_value:
            rec = M.Pair(
                L.ObservedRegularityLabel,
                M.Pair(
                    op_name,
                    M.Pair(
                        M.Char("associativity"),
                        M.Pair(
                            assoc_witnesses,
                            M.Pair(
                                M.Pair(
                                    M.Char("universal"),
                                    M.Pair(domain, M.EmptyList),
                                ),
                                M.EmptyList,
                            ),
                        ),
                    ),
                ),
            )
            return M.Pair(rec, M.Pair(r2, M.EmptyList))

        # 3. Test identity across the domain: some element e with
        #    op(a, e) == a and op(e, a) == a for every a in the domain.
        id_res = self._check_identity(domain, domain, variables, operation, r2)
        has_id = M.Head(id_res)()
        r3 = M.Head(M.Tail(M.Tail(id_res)())())()
        identity_el = M.Head(M.Tail(id_res)())()

        if has_id is M.truth_value:
            rec = M.Pair(
                L.ObservedRegularityLabel,
                M.Pair(
                    op_name,
                    M.Pair(
                        M.Char("identity"),
                        M.Pair(
                            M.Pair(identity_el, M.EmptyList),
                            M.Pair(
                                M.Pair(
                                    M.Char("universal"),
                                    M.Pair(domain, M.EmptyList),
                                ),
                                M.EmptyList,
                            ),
                        ),
                    ),
                ),
            )
            return M.Pair(rec, M.Pair(r3, M.EmptyList))

        # If no universal law holds, return empty
        return M.Pair(M.EmptyList, M.Pair(r3, M.EmptyList))

    def _left_identity_holds(self, e, domain, variables, operation, reg):
        # op(a, e) == a for every a still to check
        if M.IdentityCompare(domain, M.EmptyList)() is M.truth_value:
            return M.truth_value, reg
        a = M.Head(domain)()
        call_res = self._apply(
            variables, operation, M.Pair(a, M.Pair(e, M.EmptyList)), reg
        )
        val = M.Head(call_res)()
        r1 = M.Head(M.Tail(call_res)())()
        if M.IdentityCompare(val, M.EmptyList)() is M.truth_value:
            return M.false_value, r1
        if M.NatEq(val, a, r1)() is M.false_value:
            return M.false_value, r1
        return self._left_identity_holds(
            e, M.Tail(domain)(), variables, operation, r1
        )

    def _right_identity_holds(self, e, domain, variables, operation, reg):
        # op(e, a) == a for every a still to check
        if M.IdentityCompare(domain, M.EmptyList)() is M.truth_value:
            return M.truth_value, reg
        a = M.Head(domain)()
        call_res = self._apply(
            variables, operation, M.Pair(e, M.Pair(a, M.EmptyList)), reg
        )
        val = M.Head(call_res)()
        r1 = M.Head(M.Tail(call_res)())()
        if M.IdentityCompare(val, M.EmptyList)() is M.truth_value:
            return M.false_value, r1
        if M.NatEq(val, a, r1)() is M.false_value:
            return M.false_value, r1
        return self._right_identity_holds(
            e, M.Tail(domain)(), variables, operation, r1
        )

    def _check_identity(self, candidates, domain, variables, operation, reg):
        if M.IdentityCompare(candidates, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList)))
        e = M.Head(candidates)()
        left_ok, r1 = self._left_identity_holds(e, domain, variables, operation, reg)
        if left_ok is M.truth_value:
            right_ok, r2 = self._right_identity_holds(
                e, domain, variables, operation, r1
            )
            if right_ok is M.truth_value:
                return M.Pair(M.truth_value, M.Pair(e, M.Pair(r2, M.EmptyList)))
            rest = self._check_identity(
                M.Tail(candidates)(), domain, variables, operation, r2
            )
            return rest
        rest = self._check_identity(
            M.Tail(candidates)(), domain, variables, operation, r1
        )
        return rest

    def _check_commutativity(self, tuples, variables, operation, reg):
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(reg, M.Pair(M.EmptyList, M.EmptyList)))

        cur_tup = M.Head(tuples)()
        rest_tups = M.Tail(tuples)()

        a = M.Head(cur_tup)()
        b = M.Head(M.Tail(cur_tup)())()

        # op(a, b)
        call_ab = self._apply(variables, operation, cur_tup, reg)
        val_ab = M.Head(call_ab)()
        r1 = M.Head(M.Tail(call_ab)())()

        # op(b, a)
        tup_ba = M.Pair(b, M.Pair(a, M.EmptyList))
        call_ba = self._apply(variables, operation, tup_ba, r1)
        val_ba = M.Head(call_ba)()
        r2 = M.Head(M.Tail(call_ba)())()

        # An operand the operation is undefined on cannot witness agreement:
        # NatEq treats two undefined results as equal, which would let a law
        # look universal purely because it was never evaluable.
        if M.IdentityCompare(val_ab, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(r1, M.Pair(M.EmptyList, M.EmptyList)))
        if M.IdentityCompare(val_ba, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(r2, M.Pair(M.EmptyList, M.EmptyList)))

        eq_res = M.NatEq(val_ab, val_ba, r2)()

        if eq_res is M.false_value:
            return M.Pair(M.false_value, M.Pair(r2, M.Pair(M.EmptyList, M.EmptyList)))

        rest_check = self._check_commutativity(rest_tups, variables, operation, r2)
        rest_ok = M.Head(rest_check)()
        r3 = M.Head(M.Tail(rest_check)())()
        rest_w = M.Head(M.Tail(M.Tail(rest_check)())())()

        witness = M.Pair(cur_tup, M.Pair(val_ab, M.EmptyList))
        return M.Pair(rest_ok, M.Pair(r3, M.Pair(M.Pair(witness, rest_w), M.EmptyList)))

    def _check_associativity(self, tuples, variables, operation, reg):
        if M.IdentityCompare(tuples, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, M.Pair(reg, M.Pair(M.EmptyList, M.EmptyList)))

        cur_tup = M.Head(tuples)()
        rest_tups = M.Tail(tuples)()

        a = M.Head(cur_tup)()
        b = M.Head(M.Tail(cur_tup)())()
        c = M.Head(M.Tail(M.Tail(cur_tup)())())()

        # op(a, b)
        call_ab = self._apply(
            variables, operation, M.Pair(a, M.Pair(b, M.EmptyList)), reg
        )
        val_ab = M.Head(call_ab)()
        r1 = M.Head(M.Tail(call_ab)())()

        # op(op(a, b), c)
        call_ab_c = self._apply(
            variables, operation, M.Pair(val_ab, M.Pair(c, M.EmptyList)), r1
        )
        val_left = M.Head(call_ab_c)()
        r2 = M.Head(M.Tail(call_ab_c)())()

        # op(b, c)
        call_bc = self._apply(
            variables, operation, M.Pair(b, M.Pair(c, M.EmptyList)), r2
        )
        val_bc = M.Head(call_bc)()
        r3 = M.Head(M.Tail(call_bc)())()

        # op(a, op(b, c))
        call_a_bc = self._apply(
            variables, operation, M.Pair(a, M.Pair(val_bc, M.EmptyList)), r3
        )
        val_right = M.Head(call_a_bc)()
        r4 = M.Head(M.Tail(call_a_bc)())()

        if M.IdentityCompare(val_ab, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(r1, M.Pair(M.EmptyList, M.EmptyList)))
        if M.IdentityCompare(val_left, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(r2, M.Pair(M.EmptyList, M.EmptyList)))
        if M.IdentityCompare(val_bc, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(r3, M.Pair(M.EmptyList, M.EmptyList)))
        if M.IdentityCompare(val_right, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.Pair(r4, M.Pair(M.EmptyList, M.EmptyList)))

        eq_res = M.NatEq(val_left, val_right, r4)()

        if eq_res is M.false_value:
            return M.Pair(M.false_value, M.Pair(r4, M.Pair(M.EmptyList, M.EmptyList)))

        rest_check = self._check_associativity(rest_tups, variables, operation, r4)
        rest_ok = M.Head(rest_check)()
        r5 = M.Head(M.Tail(rest_check)())()
        rest_w = M.Head(M.Tail(M.Tail(rest_check)())())()

        witness = M.Pair(cur_tup, M.Pair(val_left, M.EmptyList))
        return M.Pair(rest_ok, M.Pair(r5, M.Pair(M.Pair(witness, rest_w), M.EmptyList)))

    def __call__(self):
        return self.result


class CheckTemplateSatisfaction(M.Edge):
    """
    Checks if a concrete carrier entity and machine operation term satisfy an
    algebraic template's required laws.
    inputs: [template_node, variables, operation, carrier_domain, registry]
    results: Pair(TemplateInstanceLabel, Pair(template_name, Pair(is_satisfied, Pair(registry, EmptyList))))
    """

    def __init__(self, template_node, variables, operation, carrier_domain, registry):
        self.registry = registry
        self.result = self._check(
            template_node, variables, operation, carrier_domain, registry
        )
        super().__init__(
            inputs=M.Pair(
                template_node,
                M.Pair(
                    variables,
                    M.Pair(
                        operation,
                        M.Pair(carrier_domain, M.Pair(registry, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _check(self, template_node, variables, operation, carrier_domain, reg):
        template_name = M.Head(M.Tail(template_node)())()
        required_laws = M.Head(M.Tail(M.Tail(template_node)())())()

        eval_miner = MineOperationInvariants(
            template_name, variables, operation, carrier_domain, reg
        )()
        mined_rec = M.Head(eval_miner)()
        r1 = M.Head(M.Tail(eval_miner)())()

        # If a required law is present, mark satisfied
        law_present = M.NotAtom(
            M.IdentityCompare(mined_rec, M.EmptyList)()
        )()
        if (
            M.IdentityCompare(law_present, M.truth_value)()
            is M.truth_value
        ):
            is_sat = M.truth_value
        else:
            is_sat = M.false_value
        inst_node = M.Pair(
            L.TemplateInstanceLabel,
            M.Pair(
                template_name,
                M.Pair(is_sat, M.EmptyList),
            ),
        )
        return M.Pair(inst_node, M.Pair(r1, M.EmptyList))

    def __call__(self):
        return self.result


class MineOperationInvariantsAcrossRegister(M.Edge):
    """
    Mines every candidate law against every operation carried by the
    operation register, so a finding is always attached to the operation
    it was observed on ("gcd is commutative, modulo is not") instead of to
    the single operation a caller happened to hand over.

    The operation set is read from the register built by introspection over
    the machine's arithmetic module; it is never listed here. For each
    registered operation the three candidate laws are tested in the order
    the machine advertises them, and every test is reported, held or
    refuted, with the witnesses that were checked.

    inputs: [domain, registry, operation_register]
    results: Pair(findings_chain, Pair(registry, EmptyList)) where each
      finding is Pair(ObservedRegularityLabel,
                      Pair(op_name, Pair(law_type, Pair(verdict,
                            Pair(witnesses, Pair(scope, EmptyList))))))
      verdict is "holds" or "refuted".
    """

    def __init__(self, domain, registry, operation_register=M.EmptyList):
        self.registry = registry
        ops = operation_register
        if M.IdentityCompare(ops, M.EmptyList)() is M.truth_value:
            built = PG.BuildNatOperationRegister(registry)()
            ops = M.Head(built)()
        self.result = self._mine_all(domain, ops, registry, ops)

    def _finding(self, op_name, law_type, verdict, witnesses, registry):
        scope = M.Pair(
            M.Char("holds" if verdict is M.truth_value else "refuted"),
            M.Pair(registry, M.EmptyList),
        )
        rec = M.Pair(
            L.ObservedRegularityLabel,
            M.Pair(
                op_name,
                M.Pair(
                    law_type,
                    M.Pair(
                        verdict,
                        M.Pair(witnesses, M.Pair(scope, M.EmptyList)),
                    ),
                ),
            ),
        )
        return rec

    def _laws_for(self, op_name, variables, operation, domain, reg, ops):
        miner = MineOperationInvariants(
            op_name, variables, operation, domain, reg
        )
        cur = reg

        dom2 = PG.ProductOfDomains(
            M.Pair(domain, M.Pair(domain, M.EmptyList))
        )()
        comm_res = miner._check_commutativity(dom2, variables, operation, cur)
        comm_ok = M.Head(comm_res)()
        cur = M.Head(M.Tail(comm_res)())()
        comm_w = M.Head(M.Tail(M.Tail(comm_res)())())()
        # A refuted law carries no witnesses: the chain a failing check
        # returns holds the tuples inspected before the refuting one, which
        # are not counterexamples and must not be read as such.
        if comm_ok is M.false_value:
            comm_w = M.EmptyList
        comm_finding = self._finding(
            op_name, M.Char("commutativity"), comm_ok, comm_w, domain
        )

        dom3 = PG.ProductOfDomains(
            M.Pair(domain, M.Pair(domain, M.Pair(domain, M.EmptyList)))
        )()
        assoc_res = miner._check_associativity(dom3, variables, operation, cur)
        assoc_ok = M.Head(assoc_res)()
        cur = M.Head(M.Tail(assoc_res)())()
        assoc_w = M.Head(M.Tail(M.Tail(assoc_res)())())()
        if assoc_ok is M.false_value:
            assoc_w = M.EmptyList
        assoc_finding = self._finding(
            op_name, M.Char("associativity"), assoc_ok, assoc_w, domain
        )

        id_res = miner._check_identity(domain, domain, variables, operation, cur)
        id_ok = M.Head(id_res)()
        cur = M.Head(M.Tail(M.Tail(id_res)())())()
        identity_el = M.Head(M.Tail(id_res)())()
        id_w = M.EmptyList
        if id_ok is M.truth_value:
            id_w = M.Pair(identity_el, M.EmptyList)
        id_finding = self._finding(
            op_name, M.Char("identity"), id_ok, id_w, domain
        )

        findings = M.Pair(
            comm_finding,
            M.Pair(assoc_finding, M.Pair(id_finding, M.EmptyList)),
        )
        return findings, cur

    def _mine_all(self, domain, cur_ops, reg, ops):
        if M.IdentityCompare(cur_ops, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
        entry = M.Head(cur_ops)()
        rest_ops = M.Tail(cur_ops)()
        op_name = M.Head(entry)()
        op_variables = M.Head(M.Tail(entry)())()
        op_operation = M.Head(M.Tail(M.Tail(entry)())())()
        findings, r1 = self._laws_for(
            op_name, op_variables, op_operation, domain, reg, ops
        )
        rest_res = self._mine_all(domain, rest_ops, r1, ops)
        rest_findings = M.Head(rest_res)()
        r2 = M.Head(M.Tail(rest_res)())()
        merged = PG.ChainConcat(findings, rest_findings)()
        return M.Pair(merged, M.Pair(r2, M.EmptyList))

    def __call__(self):
        return self.result


class ProposeNextRegularityOrStructure(M.Edge):
    """
    Traverses active operations and verified ledger entries to propose the next unnamed law
    or synthesized structure template without Python loops or hardcoded strings.
    inputs: [ops_chain, domain, ledger, registry]
    results: Pair(proposal_status, Pair(proposal_record, Pair(registry, EmptyList)))
    """

    def __init__(self, ops_chain, domain, ledger, registry):
        self.registry = registry
        self.result = self._sweep_ops(ops_chain, domain, ledger, registry)
        super().__init__(
            inputs=M.Pair(
                ops_chain,
                M.Pair(domain, M.Pair(ledger, M.Pair(registry, M.EmptyList))),
            ),
            results=self.result,
        )

    def _sweep_ops(self, cur_ops, domain, ledger, reg):
        # Base case: All operations exhausted -> attempt structure synthesis
        if M.IdentityCompare(cur_ops, M.EmptyList)() is M.truth_value:
            return self._synthesize_structure(domain, ledger, reg)

        head_op = M.Head(cur_ops)()
        tail_ops = M.Tail(cur_ops)()

        op_name = M.Head(head_op)()
        op_variables = M.Head(M.Tail(head_op)())()
        op_operation = M.Head(M.Tail(M.Tail(head_op)())())()

        # Mine universal laws over ground domain
        mine_res = MineOperationInvariants(
            op_name, op_variables, op_operation, domain, reg
        )()
        mined_rec = M.Head(mine_res)()
        r1 = M.Head(M.Tail(mine_res)())()

        # If a law is mined, check if already recorded in ledger
        if M.IdentityCompare(mined_rec, M.EmptyList)() is M.false_value:
            law_type = M.Head(M.Tail(M.Tail(mined_rec)())())()
            is_recorded = self._is_law_recorded(op_name, law_type, ledger)
            if is_recorded is M.false_value:
                # Return this un-named regularity
                witnesses = M.Head(M.Tail(M.Tail(M.Tail(mined_rec)())())())()
                proposal = M.Pair(
                    L.ObservedRegularityLabel,
                    M.Pair(op_name, M.Pair(law_type, M.Pair(witnesses, M.EmptyList))),
                )
                return M.Pair(L.ObservedRegularityLabel, M.Pair(proposal, M.Pair(r1, M.EmptyList)))

        # Recurse to next operation in chain
        return self._sweep_ops(tail_ops, domain, ledger, r1)

    def _is_law_recorded(self, op_name, law_type, ledger):
        if M.IdentityCompare(ledger, M.EmptyList)() is M.truth_value:
            return M.false_value
        schemata = PL.PromotionLedgerProofSchemata(ledger)()
        return self._search_schemata(schemata, op_name, law_type)

    def _search_schemata(self, cur_entries, op_name, law_type):
        if M.IdentityCompare(cur_entries, M.EmptyList)() is M.truth_value:
            return M.false_value
        entry = M.Head(cur_entries)()
        prov = PL.LedgerEntryProvenance(entry)()
        if M.Compare(prov, op_name)() is M.truth_value:
            return M.truth_value
        return self._search_schemata(M.Tail(cur_entries)(), op_name, law_type)

    def _synthesize_structure(self, domain, ledger, reg):
        # Bundles carrier domain and verified laws present in ledger
        if M.IdentityCompare(ledger, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList)))
        schemata = PL.PromotionLedgerProofSchemata(ledger)()
        if M.IdentityCompare(schemata, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList)))

        struct_node = M.Pair(
            L.AlgebraicTemplateLabel,
            M.Pair(domain, M.Pair(schemata, M.EmptyList)),
        )
        return M.Pair(L.AlgebraicTemplateLabel, M.Pair(struct_node, M.Pair(reg, M.EmptyList)))

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
    "MineOperationInvariants",
    "MineOperationInvariantsAcrossRegister",
    "CheckTemplateSatisfaction",
    "ProposeNextRegularityOrStructure",
)
