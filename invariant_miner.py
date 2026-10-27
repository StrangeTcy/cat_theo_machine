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
from .math import arithmetic as Arith


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
    """Compatibility entry point for the generic finite equation miner."""

    def __init__(self, op_name, variables, operation, domain, registry):
        self.registry = registry
        self.result = self._mine(op_name, variables, operation, domain, registry)
        super().__init__(
            inputs=M.Pair(
                op_name,
                M.Pair(
                    variables,
                    M.Pair(operation, M.Pair(domain, M.Pair(registry, M.EmptyList))),
                ),
            ),
            results=self.result,
        )

    def _mine(self, op_name, variables, operation, domain, registry):
        # The entry handed to the miner has to carry the same eight fields a
        # discovered register entry does, because the miner reads an
        # operation's law depth out of the tail of that description. Building
        # a three-field entry here made that read walk off the end of the
        # chain and crash on the fourth Tail. Describing the operation
        # through the register keeps one description of it for every consumer.
        built = PG.BuildNatOperationRegister(
            registry, M.Pair(operation, M.EmptyList)
        )()
        entries = M.Head(built)()
        reg1 = M.Head(M.Tail(built)())()
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg1, M.EmptyList))
        mined = MineOperationInvariantsAcrossRegister(domain, reg1, entries)()
        findings = M.Head(mined)()
        reg2 = M.Head(M.Tail(mined)())()
        if M.IdentityCompare(findings, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg2, M.EmptyList))
        return M.Pair(M.Head(findings)(), M.Pair(reg2, M.EmptyList))

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
        template_body = M.Tail(template_node)()
        template_name = M.Head(template_body)()
        required_laws = M.Head(M.Tail(template_body)())()
        template_tail = M.Tail(M.Tail(template_body)())()
        template_operations = M.EmptyList
        if M.IdentityCompare(template_tail, M.EmptyList)() is M.false_value:
            template_name = M.Char("finite-algebra-template")
            template_operations = M.Head(M.Tail(template_body)())()
            required_laws = M.Head(template_tail)()

        if M.IdentityCompare(template_operations, M.EmptyList)() is M.truth_value:
            built = PG.BuildNatOperationRegister(
                reg, M.Pair(operation, M.EmptyList)
            )()
            operations = M.Head(built)()
            r1 = M.Head(M.Tail(built)())()
        else:
            operations = template_operations
            r1 = reg
        mined = MineOperationInvariantsAcrossRegister(
            carrier_domain, r1, operations
        )()
        findings = M.Head(mined)()
        r2 = M.Head(M.Tail(mined)())()
        is_sat = self._required_laws_hold(
            required_laws, findings, carrier_domain
        )
        r1 = r2
        inst_node = M.Pair(
            L.TemplateInstanceLabel,
            M.Pair(
                template_name,
                M.Pair(is_sat, M.EmptyList),
            ),
        )
        return M.Pair(inst_node, M.Pair(r1, M.EmptyList))

    def _finding_matches(self, findings, operation_name, law, domain):
        if M.IdentityCompare(findings, M.EmptyList)() is M.truth_value:
            return M.false_value
        finding = M.Head(findings)()
        body = M.Tail(finding)()
        found_operation = M.Head(body)()
        found_law = M.Head(M.Tail(body)())()
        verdict_body = M.Tail(M.Tail(body)())()
        verdict = M.Head(verdict_body)()
        witness_body = M.Tail(verdict_body)()
        scope = M.Head(M.Tail(witness_body)())()
        found_domain = M.Head(M.Tail(scope)())()
        same = M.AndAtom(
            M.Compare(found_operation, operation_name)(),
            M.AndAtom(
                M.Compare(found_law, law)(),
                M.Compare(found_domain, domain)(),
            )(),
        )()
        if M.AndAtom(same, M.IdentityCompare(verdict, M.truth_value)())() is M.truth_value:
            return M.truth_value
        return self._finding_matches(M.Tail(findings)(), operation_name, law, domain)

    def _required_laws_hold(self, laws, findings, domain):
        if M.IdentityCompare(laws, M.EmptyList)() is M.truth_value:
            return M.truth_value
        named = M.Head(laws)()
        if M.IsPair(named)() is M.false_value:
            if M.IdentityCompare(findings, M.EmptyList)() is M.false_value:
                return self._required_laws_hold(
                    M.Tail(laws)(), findings, domain
                )
            return M.false_value
        if M.IdentityCompare(M.Head(named)(), L.NamedRegularityLabel)() is M.false_value:
            if M.IdentityCompare(findings, M.EmptyList)() is M.false_value:
                return self._required_laws_hold(
                    M.Tail(laws)(), findings, domain
                )
            return M.false_value
        body = M.Tail(named)()
        named_operation = M.Head(M.Tail(body)())()
        law = M.Head(M.Tail(M.Tail(body)())())()
        present = self._finding_matches(
            findings, named_operation, law, domain
        )
        if M.IdentityCompare(present, M.truth_value)() is M.false_value:
            return M.false_value
        return self._required_laws_hold(M.Tail(laws)(), findings, domain)

    def __call__(self):
        return self.result


class MineOperationInvariantsAcrossRegister(M.Edge):
    """
    Mines every candidate law against every operation carried by the
    operation register, so a finding is always attached to the operation
    it was observed on ("gcd is commutative, modulo is not") instead of to
    the single operation a caller happened to hand over.

    The operation set is read from the supplied operation register. Candidate
    laws are generated as equations between operation terms, rather than
    selected from a property-name list. The finite scan considers binary term
    shapes over two and three distinct variables and records every equation
    that holds throughout the tested domain.

    inputs: [domain, registry, operation_register]
    results: Pair(findings_chain, Pair(registry, EmptyList)) where each
      finding is Pair(ObservedRegularityLabel,
                      Pair(op_name, Pair(law_type, Pair(verdict,
                            Pair(witnesses, Pair(scope, EmptyList))))))
      verdict is "holds" or "refuted".
    """

    def __init__(self, domain, registry, operation_register=M.EmptyList,
                 known_nodes=M.EmptyList):
        self.registry = registry
        self.known_nodes = known_nodes
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
        if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
        if M.IdentityCompare(M.Tail(M.Tail(variables)())(), M.EmptyList)() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
        equation_label = M.Head(operation)()
        vars2 = M.Pair(M.Char("x"), M.Pair(M.Char("y"), M.EmptyList))
        vars3 = M.Pair(
            M.Char("x"), M.Pair(M.Char("y"), M.Pair(M.Char("z"), M.EmptyList))
        )
        found2 = self._laws_for_variables(
            op_name, equation_label, vars2, domain, reg, ops
        )
        laws2 = M.Head(found2)()
        reg2 = M.Head(M.Tail(found2)())()
        operation_entry = PG.LookupOperationByLabel(equation_label, ops)()
        profile_tail = operation_entry
        profile_tail = M.Tail(profile_tail)()
        profile_tail = M.Tail(profile_tail)()
        profile_tail = M.Tail(profile_tail)()
        profile_tail = M.Tail(profile_tail)()
        profile_tail = M.Tail(profile_tail)()
        profile_tail = M.Tail(profile_tail)()
        profile_tail = M.Tail(profile_tail)()
        law_depth = M.Head(profile_tail)()
        if M.Compare(law_depth, M.Char("expensive"))() is M.truth_value:
            return laws2, reg2
        found3 = self._laws_for_variables(
            op_name, equation_label, vars3, domain, reg2, ops
        )
        laws3 = M.Head(found3)()
        reg3 = M.Head(M.Tail(found3)())()
        return PG.ChainConcat(laws2, laws3)(), reg3

    def _append_chain(self, prefix, suffix):
        if M.IdentityCompare(prefix, M.EmptyList)() is M.truth_value:
            return suffix
        return M.Pair(
            M.Head(prefix)(), self._append_chain(M.Tail(prefix)(), suffix)
        )

    def _remove_first(self, selected, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        head = M.Head(chain)()
        if M.Compare(head, selected)() is M.truth_value:
            return M.Tail(chain)()
        return M.Pair(
            head,
            self._remove_first(selected, M.Tail(chain)()),
        )

    def _prefix_each(self, selected, chains):
        if M.IdentityCompare(chains, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(
            M.Pair(selected, M.Head(chains)()),
            self._prefix_each(selected, M.Tail(chains)()),
        )

    def _permutations(self, remaining, original):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.EmptyList)
        selected = M.Head(remaining)()
        rest = self._remove_first(selected, original)
        suffixes = self._permutations(rest, rest)
        prefixed = self._prefix_each(selected, suffixes)
        if M.IdentityCompare(M.Tail(remaining)(), M.EmptyList)() is M.truth_value:
            return prefixed
        later = self._permutations(M.Tail(remaining)(), original)
        return PG.ChainConcat(prefixed, later)()

    def _splits(self, remaining, prefix):
        if M.IdentityCompare(M.Tail(remaining)(), M.EmptyList)() is M.truth_value:
            return M.EmptyList
        extended = self._append_chain(prefix, M.Pair(M.Head(remaining)(), M.EmptyList))
        right = M.Tail(remaining)()
        split = M.Pair(extended, M.Pair(right, M.EmptyList))
        return M.Pair(split, self._splits(right, extended))

    def _combine_split_terms(self, splits, operation_label):
        if M.IdentityCompare(splits, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        split = M.Head(splits)()
        left_terms = self._terms_for_order(
            M.Head(split)(), operation_label
        )
        right_terms = self._terms_for_order(
            M.Head(M.Tail(split)())(), operation_label
        )
        combined = self._cross_terms(left_terms, right_terms, operation_label)
        return PG.ChainConcat(
            combined,
            self._combine_split_terms(M.Tail(splits)(), operation_label),
        )()

    def _cross_terms(self, left_terms, right_terms, operation_label):
        if M.IdentityCompare(left_terms, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        left = M.Head(left_terms)()
        return PG.ChainConcat(
            self._terms_with_left(left, right_terms, operation_label),
            self._cross_terms(
                M.Tail(left_terms)(), right_terms, operation_label
            ),
        )()

    def _terms_with_left(self, left, right_terms, operation_label):
        if M.IdentityCompare(right_terms, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        right = M.Head(right_terms)()
        term = M.Pair(
            operation_label,
            M.Pair(left, M.Pair(right, M.EmptyList)),
        )
        return M.Pair(
            term,
            self._terms_with_left(left, M.Tail(right_terms)(), operation_label),
        )

    def _terms_for_order(self, variables, operation_label):
        if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.truth_value:
            return M.Pair(M.Head(variables)(), M.EmptyList)
        return self._combine_split_terms(
            self._splits(variables, M.EmptyList), operation_label
        )

    def _terms_for_orders(self, orders, operation_label):
        if M.IdentityCompare(orders, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        terms = self._terms_for_order(M.Head(orders)(), operation_label)
        return PG.ChainConcat(
            terms,
            self._terms_for_orders(M.Tail(orders)(), operation_label),
        )()

    def _terms(self, variables, operation_label):
        orders = self._permutations(variables, variables)
        return self._terms_for_orders(orders, operation_label)

    def _equations_with_left(self, law, variables, remaining):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        candidate = M.Head(remaining)()
        if M.Compare(law, candidate)() is M.false_value:
            equation = M.Pair(
                L.DiscoveredEquationLabel,
                M.Pair(variables, M.Pair(law, M.Pair(candidate, M.EmptyList))),
            )
            return M.Pair(
                equation,
                self._equations_with_left(
                    law, variables, M.Tail(remaining)()
                )
            )
        return self._equations_with_left(law, variables, M.Tail(remaining)())

    def _equations(self, terms, variables):
        if M.IdentityCompare(terms, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        law = M.Head(terms)()
        return PG.ChainConcat(
            self._equations_with_left(law, variables, M.Tail(terms)()),
            self._equations(M.Tail(terms)(), variables),
        )()

    def _domains_for_variables(self, variables, domain):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(
            domain, self._domains_for_variables(M.Tail(variables)(), domain)
        )

    def _equation_value(
        self, term, variables, assignment, registry, ops, tensor
    ):
        """Value of one side of a candidate law at one assignment.

        The term is read out of the operation result grid rather than
        evaluated afresh, so the cells a law needs were computed once when
        the grid was built instead of once per candidate and per assignment.
        """
        environment = PG.ZipEnvironment(variables, assignment)()
        # A flat operation term -- both operands are leaves bound to domain
        # elements -- is read out of the result grid. A nested term is
        # evaluated instead, because an intermediate result can fall outside
        # the tested domain and the grid holds cells for domain elements
        # only, so reading it would report undefined for a term that in fact
        # has a value.
        if M.IsPair(term)() is M.truth_value:
            args = M.Tail(term)()
            if M.IsPair(M.Head(args)())() is M.false_value:
                if M.IsPair(M.Head(M.Tail(args)())())() is M.false_value:
                    return PG.TensorOperationValue(
                        tensor, term, environment, registry
                    )()
        return PG.EvaluateNatExpr(term, environment, registry, ops)()

    def _check_equation_tuples(
        self, equation, variables, tuples, reg, ops, tensor, witnesses
    ):
        """Check every assignment of one candidate law, iteratively.

        Recursing once per assignment makes the recursion depth the size of
        the Cartesian product, so a three-variable domain over 0..10 needs
        1331 frames and overflows Python's limit before the product is even
        exhausted. Walking the tuple chain in a loop keeps the depth
        constant regardless of how many assignments there are, and hoists
        the two operand extractions out of the walk so each assignment pays
        for its own evaluations only.
        """
        lhs = M.Head(M.Tail(M.Tail(equation)())())()
        rhs = M.Head(M.Tail(M.Tail(M.Tail(equation)())())())()
        cur = tuples
        found = witnesses
        active = reg
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            assignment = M.Head(cur)()
            environment = PG.ZipEnvironment(variables, assignment)()
            comparison_text = (
                PG.RenderOperationCall(lhs, environment, ops, active)()
                + " == "
                + PG.RenderOperationCall(rhs, environment, ops, active)()
            )
            PG.NaturalPlaygroundDebugEmit(M.Char(
                "Pairwise comparing the results of the same operation: "
                + comparison_text + "?"
            ))()
            lhs_res = self._equation_value(
                lhs, variables, assignment, active, ops, tensor
            )
            lhs_value = M.Head(lhs_res)()
            active = M.Head(M.Tail(lhs_res)())()
            if M.IdentityCompare(lhs_value, M.EmptyList)() is M.truth_value:
                PG.NaturalPlaygroundDebugEmit(M.Char(
                    comparison_text + " -> undefined left operand; candidate not established"
                ))()
                return M.Pair(
                    M.false_value, M.Pair(active, M.Pair(M.EmptyList, M.EmptyList))
                )
            rhs_res = self._equation_value(
                rhs, variables, assignment, active, ops, tensor
            )
            rhs_value = M.Head(rhs_res)()
            active = M.Head(M.Tail(rhs_res)())()
            if M.IdentityCompare(rhs_value, M.EmptyList)() is M.truth_value:
                PG.NaturalPlaygroundDebugEmit(M.Char(
                    comparison_text + " -> undefined right operand; candidate not established"
                ))()
                return M.Pair(
                    M.false_value, M.Pair(active, M.Pair(M.EmptyList, M.EmptyList))
                )
            if M.IdentityCompare(lhs_value, M.truth_value)() is M.truth_value:
                equal = M.IdentityCompare(rhs_value, M.truth_value)()
            elif M.IdentityCompare(lhs_value, M.false_value)() is M.truth_value:
                equal = M.IdentityCompare(rhs_value, M.false_value)()
            elif A.IsNat(lhs_value, active)() is M.truth_value:
                if A.IsNat(rhs_value, active)() is M.truth_value:
                    equal = M.NatEq(lhs_value, rhs_value, active)()
                else:
                    equal = M.false_value
            else:
                equal = M.Compare(lhs_value, rhs_value)()
            PG.NaturalPlaygroundDebugEmit(M.Char(
                comparison_text + " -> " + PG.RenderOperationValue(equal, active)()
                + " (" + PG.RenderOperationValue(lhs_value, active)()
                + " == " + PG.RenderOperationValue(rhs_value, active)() + ")"
            ))()
            if equal is M.false_value:
                return M.Pair(
                    M.false_value, M.Pair(active, M.Pair(M.EmptyList, M.EmptyList))
                )
            found = M.Pair(
                M.Pair(assignment, M.Pair(lhs_value, M.Pair(rhs_value, M.EmptyList))),
                found,
            )
            cur = M.Tail(cur)()
        return M.Pair(M.truth_value, M.Pair(active, M.Pair(found, M.EmptyList)))

    def _check_equation_candidates(
        self, op_name, operation_label, equations, variables, domain, reg,
        ops, findings,
    ):
        if M.IdentityCompare(equations, M.EmptyList)() is M.truth_value:
            return M.Pair(findings, M.Pair(reg, M.EmptyList))
        # The Cartesian product depends only on the variables and the domain,
        # never on which law is being checked, so it is built once here rather
        # than once per candidate. Walking the equation chain in a loop keeps
        # the recursion depth constant as well.
        domains = self._domains_for_variables(variables, domain)
        tuples = PG.ProductOfDomains(domains)()
        # One result grid per operation, built once here and read by every
        # candidate law below, so testing a law costs lookups into cells that
        # have already been computed rather than fresh evaluations of them.
        entry = PG.LookupOperationByLabel(operation_label, ops)()
        tensor = M.EmptyList
        cur = equations
        found = findings
        active = reg
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            equation = M.Head(cur)()
            if self._known_equation(op_name, equation) is M.false_value:
                if M.IdentityCompare(tensor, M.EmptyList)() is M.truth_value:
                    tensor = PG.BuildOperationTensor(
                        domain, M.Pair(entry, M.EmptyList), active
                    )()
                checked = self._check_equation_tuples(
                    equation, variables, tuples, active, ops, tensor, M.EmptyList
                )
                verdict = M.Head(checked)()
                active = M.Head(M.Tail(checked)())()
                witnesses = M.Head(M.Tail(M.Tail(checked)())())()
                if verdict is M.truth_value:
                    finding = self._finding(
                        op_name, equation, verdict, witnesses, domain
                    )
                    found = M.Pair(finding, found)
                    PG.NaturalPlaygroundDebugEmit(M.Char(
                        "Gathering observations of a regularity for " + op_name()
                        + "(): [" + PG.FormatOperationLawExamples(equation, witnesses, ops, active)()
                        + "]; held across the tested domain " + PG.FormatSetChain(domain, active)()
                    ))()
            cur = M.Tail(cur)()
        return M.Pair(found, M.Pair(active, M.EmptyList))

    def _known_equation(self, operation, equation, nodes=M.EmptyList,
                        initialized=M.false_value):
        if M.IdentityCompare(initialized, M.false_value)() is M.truth_value:
            nodes = self.known_nodes
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            return M.false_value
        node = M.Head(nodes)()
        if M.IdentityCompare(M.Head(node)(), L.NamedRegularityLabel)() is M.truth_value:
            body = M.Tail(node)()
            name_body = M.Tail(body)()
            saved_operation = M.Head(name_body)()
            saved_law = M.Head(M.Tail(name_body)())()
            if M.AndAtom(
                M.Compare(saved_operation, operation)(),
                M.Compare(saved_law, equation)(),
            )() is M.truth_value:
                return M.truth_value
        return self._known_equation(
            operation, equation, M.Tail(nodes)(), M.truth_value
        )

    def _laws_for_variables(self, op_name, operation_label, variables, domain, reg, ops):
        terms = self._terms(variables, operation_label)
        equations = self._equations(terms, variables)
        checked = self._check_equation_candidates(
            op_name, operation_label, equations, variables, domain, reg,
            ops, M.EmptyList,
        )
        findings = PG.ChainReverse(M.Head(checked)())()
        reg1 = M.Head(M.Tail(checked)())()
        return M.Pair(findings, M.Pair(reg1, M.EmptyList))

    def _binary_entry(self, entry):
        variables = M.Head(M.Tail(entry)())()
        if M.IdentityCompare(M.Tail(variables)(), M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(M.Tail(M.Tail(variables)())(), M.EmptyList)() is M.false_value:
            return M.false_value
        return M.truth_value

    def _entry_is_expensive(self, entry):
        tail = entry
        tail = M.Tail(tail)()
        tail = M.Tail(tail)()
        tail = M.Tail(tail)()
        tail = M.Tail(tail)()
        tail = M.Tail(tail)()
        tail = M.Tail(tail)()
        tail = M.Tail(tail)()
        return M.Compare(M.Head(tail)(), M.Char("expensive"))()

    def _mixed_equation(self, outer_label, inner_label):
        x = M.Char("x")
        y = M.Char("y")
        z = M.Char("z")
        inner_yz = M.Pair(
            inner_label,
            M.Pair(y, M.Pair(z, M.EmptyList)),
        )
        outer_xy = M.Pair(
            outer_label,
            M.Pair(x, M.Pair(y, M.EmptyList)),
        )
        outer_xz = M.Pair(
            outer_label,
            M.Pair(x, M.Pair(z, M.EmptyList)),
        )
        left = M.Pair(
            outer_label,
            M.Pair(x, M.Pair(inner_yz, M.EmptyList)),
        )
        right_inner = M.Pair(
            inner_label,
            M.Pair(outer_xy, M.Pair(outer_xz, M.EmptyList)),
        )
        return M.Pair(
            L.DiscoveredEquationLabel,
            M.Pair(
                M.Pair(x, M.Pair(y, M.Pair(z, M.EmptyList))),
                M.Pair(left, M.Pair(right_inner, M.EmptyList)),
            ),
        )

    def _mixed_laws_for(self, outer_entry, domain, reg, ops):
        if self._binary_entry(outer_entry) is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
        if self._entry_is_expensive(outer_entry) is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
        outer_name = M.Head(outer_entry)()
        outer_label = M.Head(M.Head(M.Tail(M.Tail(outer_entry)())())())()
        remaining = ops
        findings = M.EmptyList
        active = reg
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            inner_entry = M.Head(remaining)()
            inner_label = M.Head(M.Head(M.Tail(M.Tail(inner_entry)())())())()
            if M.IdentityCompare(inner_label, outer_label)() is M.false_value:
                if self._binary_entry(inner_entry) is M.truth_value:
                    if self._entry_is_expensive(inner_entry) is M.false_value:
                        inner_name = M.Head(inner_entry)()
                        equation = self._mixed_equation(outer_label, inner_label)
                        mixed_name = M.Char(outer_name() + " over " + inner_name() )
                        checked = self._check_equation_candidates(
                            mixed_name,
                            outer_label,
                            M.Pair(equation, M.EmptyList),
                            M.Pair(M.Char("x"), M.Pair(M.Char("y"), M.Pair(M.Char("z"), M.EmptyList))),
                            domain,
                            active,
                            ops,
                            findings,
                        )
                        findings = M.Head(checked)()
                        active = M.Head(M.Tail(checked)())()
            remaining = M.Tail(remaining)()
        return M.Pair(findings, M.Pair(active, M.EmptyList))

    def _divisibility_laws(self, domain, reg, ops):
        divides = PG.LookupOperationByLabel(L.DividesLabel, ops)()
        multiply = PG.LookupOperationByLabel(L.ExprMulLabel, ops)()
        implies = PG.LookupOperationByLabel(L.ImpliesLabel, ops)()
        if M.IdentityCompare(divides, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
        if M.IdentityCompare(multiply, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
        if M.IdentityCompare(implies, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
        x = M.Char("x")
        y = M.Char("y")
        z = M.Char("z")
        vars3 = M.Pair(x, M.Pair(y, M.Pair(z, M.EmptyList)))
        antecedent = M.Pair(
            L.DividesLabel,
            M.Pair(x, M.Pair(z, M.EmptyList)),
        )
        product = M.Pair(
            L.ExprMulLabel,
            M.Pair(x, M.Pair(y, M.EmptyList)),
        )
        conclusion = M.Pair(
            L.DividesLabel,
            M.Pair(product, M.Pair(z, M.EmptyList)),
        )
        implication = M.Pair(
            L.ImpliesLabel,
            M.Pair(antecedent, M.Pair(conclusion, M.EmptyList)),
        )
        equation = M.Pair(
            L.DiscoveredEquationLabel,
            M.Pair(vars3, M.Pair(implication, M.Pair(M.truth_value, M.EmptyList))),
        )
        checked = self._check_equation_candidates(
            M.Char("divisibility propagation"),
            L.ImpliesLabel,
            M.Pair(equation, M.EmptyList),
            vars3,
            domain,
            reg,
            ops,
            M.EmptyList,
        )
        return M.Pair(
            M.Head(checked)(),
            M.Pair(M.Head(M.Tail(checked)())(), M.EmptyList),
        )

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
        mixed = self._mixed_laws_for(entry, domain, r1, ops)
        mixed_findings = M.Head(mixed)()
        r1 = M.Head(M.Tail(mixed)())()
        findings = PG.ChainConcat(findings, mixed_findings)()
        if M.IdentityCompare(
            M.Head(M.Head(M.Tail(M.Tail(entry)())())())(),
            L.DividesLabel,
        )() is M.truth_value:
            divisibility = self._divisibility_laws(domain, r1, ops)
            findings = PG.ChainConcat(findings, M.Head(divisibility)())()
            r1 = M.Head(M.Tail(divisibility)())()
        rest_res = self._mine_all(domain, rest_ops, r1, ops)
        rest_findings = M.Head(rest_res)()
        r2 = M.Head(M.Tail(rest_res)())()
        merged = PG.ChainConcat(findings, rest_findings)()
        return M.Pair(merged, M.Pair(r2, M.EmptyList))

    def __call__(self):
        return self.result


class ProposeNextRegularityOrStructure(M.Edge):
    """
    Scans every mined operation-law finding, skips laws already named for the
    same operation/equation even when the new finite domain is different, then
    proposes a bundle of named laws for the current operation set.
    `known_nodes` is the graph's machine-native node chain.
    inputs: [ops_chain, domain, known_nodes, registry]
    results: Pair(proposal_status, Pair(proposal_record, Pair(registry, EmptyList)))
    """

    def __init__(self, ops_chain, domain, known_nodes, registry):
        self.registry = registry
        mined = MineOperationInvariantsAcrossRegister(
            domain, registry, ops_chain, known_nodes
        )()
        findings = M.Head(mined)()
        reg1 = M.Head(M.Tail(mined)())()
        self.result = self._propose(findings, domain, known_nodes, reg1, ops_chain)
        super().__init__(
            inputs=M.Pair(
                ops_chain,
                M.Pair(domain, M.Pair(known_nodes, M.Pair(registry, M.EmptyList))),
            ),
            results=self.result,
        )

    def _propose(self, findings, domain, known_nodes, reg, ops):
        if M.IdentityCompare(findings, M.EmptyList)() is M.truth_value:
            return self._synthesize_structure(domain, ops, known_nodes, reg)
        finding = M.Head(findings)()
        finding_body = M.Tail(finding)()
        op_name = M.Head(finding_body)()
        law_body = M.Tail(finding_body)()
        law_type = M.Head(law_body)()
        verdict_body = M.Tail(law_body)()
        verdict = M.Head(verdict_body)()
        witness_body = M.Tail(verdict_body)()
        witnesses = M.Head(witness_body)()
        scope = M.Head(M.Tail(witness_body)())()
        found_domain = M.Head(M.Tail(scope)())()
        is_named = self._law_recorded(
            known_nodes, op_name, law_type, found_domain
        )
        if verdict is M.truth_value:
            if is_named is M.false_value:
                return M.Pair(
                    L.ObservedRegularityLabel,
                    M.Pair(finding, M.Pair(reg, M.EmptyList)),
                )
        return self._propose(M.Tail(findings)(), domain, known_nodes, reg, ops)

    def _law_recorded(self, nodes, op_name, law_type, domain):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            return M.false_value
        node = M.Head(nodes)()
        tag = M.Head(node)()
        if M.IdentityCompare(tag, L.NamedRegularityLabel)() is M.truth_value:
            body = M.Tail(node)()
            name_body = M.Tail(body)()
            saved_op = M.Head(name_body)()
            law_body = M.Tail(name_body)()
            saved_law = M.Head(law_body)()
            same_op = M.Compare(saved_op, op_name)()
            same_law = M.Compare(saved_law, law_type)()
            if M.AndAtom(same_op, same_law)() is M.truth_value:
                return M.truth_value
        return self._law_recorded(M.Tail(nodes)(), op_name, law_type, domain)

    def _operation_is_registered(self, operations, operation_name):
        if M.IdentityCompare(operations, M.EmptyList)() is M.truth_value:
            return M.false_value
        entry = M.Head(operations)()
        if M.Compare(M.Head(entry)(), operation_name)() is M.truth_value:
            return M.truth_value
        return self._operation_is_registered(M.Tail(operations)(), operation_name)

    def _laws_for_domain(self, nodes, operations):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        node = M.Head(nodes)()
        rest = self._laws_for_domain(M.Tail(nodes)(), operations)
        tag = M.Head(node)()
        if M.IdentityCompare(tag, L.NamedRegularityLabel)() is M.false_value:
            return rest
        body = M.Tail(node)()
        name_body = M.Tail(body)()
        operation_name = M.Head(name_body)()
        if self._operation_is_registered(operations, operation_name)() is M.false_value:
            return rest
        return M.Pair(node, rest)

    def _structure_recorded(self, nodes, template):
        if M.IdentityCompare(nodes, M.EmptyList)() is M.truth_value:
            return M.false_value
        node = M.Head(nodes)()
        tag = M.Head(node)()
        if M.IdentityCompare(tag, L.NamedStructureLabel)() is M.truth_value:
            saved_template = M.Head(M.Tail(M.Tail(node)())())()
            if M.Compare(saved_template, template)() is M.truth_value:
                return M.truth_value
        return self._structure_recorded(M.Tail(nodes)(), template)

    def _synthesize_structure(self, domain, operations, known_nodes, reg):
        named_laws = self._laws_for_domain(known_nodes, operations)
        if M.IdentityCompare(named_laws, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList)))
        template = M.Pair(
            L.AlgebraicTemplateLabel,
            M.Pair(
                domain,
                M.Pair(operations, M.Pair(named_laws, M.EmptyList)),
            ),
        )
        if self._structure_recorded(known_nodes, template) is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList)))
        return M.Pair(L.AlgebraicTemplateLabel, M.Pair(template, M.Pair(reg, M.EmptyList)))

    def __call__(self):
        return self.result


# ============================================================
# W27 — ground-transition observables: independent verification of
# Preserves / StrictlyDecreases / NonIncreases claims, and mining of
# preserved observables over an enumerated transition relation.
#
# The miner above (MineInvariantFromTrace) tests candidate *patterns*
# against rule premises/replacements; it cannot evaluate a computed
# observable such as a count parity, because nothing computes the
# readings. The edges below close that gap for finite processes whose
# transition relation is supplied as ground data:
#
#   transition  ::= Pair(move, Pair(state, Pair(next_state, [])))
#   state       ::= chain of nat components
#   observable  ::= Pair(LinearObservableLabel,
#                        Pair(coefficients, Pair(modulus, [])))
#                   coefficients aligned with the state components;
#                   modulus EmptyList means the raw linear form (a
#                   measure), otherwise the form reduced modulo it.
#
# Every reading is computed by the machine's own arithmetic edges
# (Multiply / Add / Modulo) and every comparison is decided by NatEq /
# NatLess. The reading caches below are bookkeeping only: they memoise
# machine-computed reading terms per state term so an exhaustive check
# over a few hundred transitions stays affordable; no verdict is ever
# taken from the cache without the reading having been computed by
# LinearObservableValue first.
# ============================================================


class LinearObservable(M.Edge):
    """
    Observable descriptor term: a linear form over state components,
    optionally reduced by a modulus.

    inputs: [coefficients, modulus]   (modulus EmptyList = raw value)
    results: Pair(LinearObservableLabel, Pair(coefficients, Pair(modulus, EmptyList)))
    """

    def __init__(self, coefficients, modulus):
        self.result = M.Pair(
            L.LinearObservableLabel,
            M.Pair(coefficients, M.Pair(modulus, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(coefficients, M.Pair(modulus, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class LinearObservableValue(M.Edge):
    """
    Evaluates a linear observable on one state.

    inputs: [observable, state, registry]
    results: Pair(value, Pair(registry, EmptyList)); value is EmptyList
    on any refusal (descriptor head mismatch, coefficient/state length
    mismatch, a non-nat component, or a zero modulus).
    """

    def __init__(self, observable, state, registry):
        self.result = self._evaluate(observable, state, registry)
        super().__init__(
            inputs=M.Pair(
                observable,
                M.Pair(state, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _evaluate(self, observable, state, registry):
        refused = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IsPair(observable)() is M.false_value:
            return refused
        if M.IdentityCompare(M.Head(observable)(), L.LinearObservableLabel)() is M.false_value:
            return refused
        fields = M.Tail(observable)()
        coefficients = M.Head(fields)()
        modulus = M.Head(M.Tail(fields)())()

        total = M.Zero
        reg = registry
        coeffs = coefficients
        components = state
        while M.IdentityCompare(coeffs, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(components, M.EmptyList)() is M.truth_value:
                return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
            if M.IdentityCompare(M.Head(coeffs)(), M.Zero)() is M.truth_value:
                # A zero coefficient contributes nothing; skipping its
                # product is decided by identity against the Zero term
                # and changes no value -- it only keeps exhaustive
                # mining affordable.
                coeffs = M.Tail(coeffs)()
                components = M.Tail(components)()
                continue
            product_pair = Arith.Multiply(M.Head(coeffs)(), M.Head(components)(), reg)()
            product = M.Head(product_pair)()
            reg = M.Head(M.Tail(product_pair)())()
            if M.IdentityCompare(product, M.EmptyList)() is M.truth_value:
                return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
            sum_pair = Arith.Add(total, product, reg)()
            total = M.Head(sum_pair)()
            reg = M.Head(M.Tail(sum_pair)())()
            if M.IdentityCompare(total, M.EmptyList)() is M.truth_value:
                return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
            coeffs = M.Tail(coeffs)()
            components = M.Tail(components)()
        if M.IdentityCompare(components, M.EmptyList)() is M.false_value:
            return M.Pair(M.EmptyList, M.Pair(reg, M.EmptyList))
        if M.IdentityCompare(modulus, M.EmptyList)() is M.truth_value:
            return M.Pair(total, M.Pair(reg, M.EmptyList))
        residue_pair = Arith.Modulo(total, modulus, reg)()
        return residue_pair

    def __call__(self):
        return self.result


class _GroundTransitionCheck:
    """Shared transition walking for the W27 verifier/miner edges.

    Not an edge itself. Holds the registry being threaded and the
    reading cache (state term -> machine-computed reading term).
    """

    def _init_ground(self, registry):
        self.registry = registry
        self._reading_cache = {}

    def _reading(self, observable, state):
        cached = self._reading_cache.get(state)
        if cached is not None:
            return cached
        pair = LinearObservableValue(observable, state, self.registry)()
        value = M.Head(pair)()
        self.registry = M.Head(M.Tail(pair)())()
        self._reading_cache[state] = value
        return value

    def _transition_parts(self, transition):
        move = M.Head(transition)()
        rest = M.Tail(transition)()
        state = M.Head(rest)()
        next_state = M.Head(M.Tail(rest)())()
        return move, state, next_state


class VerifyObservablePreserved(M.Edge, _GroundTransitionCheck):
    """
    Independently verifies that one move preserves one observable over
    every ground transition of that move, by machine arithmetic.

    inputs: [move, observable, transitions, registry]
    results: Pair(verdict, Pair(registry, EmptyList)) where verdict is
      Pair(PreservesLabel, Pair(move, Pair(observable, EmptyList)))
    on success (exactly the fact the engel-strategies pack consumes), or
      Pair(InvariantRefutedLabel, Pair(observable, Pair(move, Pair(reason, EmptyList))))
    with reason = Pair(before, Pair(after, Pair(transition, EmptyList)))
    on the first refuting transition. A move with no transitions in the
    chain is refused rather than vacuously certified: no evidence, no
    certificate (reason is then EmptyList).
    """

    def __init__(self, move, observable, transitions, registry):
        self._init_ground(registry)
        self.result = self._verify(move, observable, transitions)
        super().__init__(
            inputs=M.Pair(
                move,
                M.Pair(
                    observable,
                    M.Pair(transitions, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _refuted(self, move, observable, reason):
        verdict = M.Pair(
            L.InvariantRefutedLabel,
            M.Pair(observable, M.Pair(move, M.Pair(reason, M.EmptyList))),
        )
        return M.Pair(verdict, M.Pair(self.registry, M.EmptyList))

    def _verify(self, move, observable, transitions):
        seen_any = M.false_value
        remaining = transitions
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            transition = M.Head(remaining)()
            remaining = M.Tail(remaining)()
            tmove, state, next_state = self._transition_parts(transition)
            if M.TermEqual(tmove, move)() is M.false_value:
                continue
            seen_any = M.truth_value
            before = self._reading(observable, state)
            after = self._reading(observable, next_state)
            if M.IdentityCompare(before, M.EmptyList)() is M.truth_value:
                return self._refuted(
                    move, observable,
                    M.Pair(before, M.Pair(after, M.Pair(transition, M.EmptyList))),
                )
            if M.IdentityCompare(after, M.EmptyList)() is M.truth_value:
                return self._refuted(
                    move, observable,
                    M.Pair(before, M.Pair(after, M.Pair(transition, M.EmptyList))),
                )
            if M.NatEq(before, after, self.registry)() is M.false_value:
                return self._refuted(
                    move, observable,
                    M.Pair(before, M.Pair(after, M.Pair(transition, M.EmptyList))),
                )
        if seen_any is M.false_value:
            return self._refuted(move, observable, M.EmptyList)
        verdict = M.Pair(
            L.PreservesLabel,
            M.Pair(move, M.Pair(observable, M.EmptyList)),
        )
        return M.Pair(verdict, M.Pair(self.registry, M.EmptyList))

    def __call__(self):
        return self.result


class VerifyMeasureDecrease(M.Edge, _GroundTransitionCheck):
    """
    Independently verifies that one move strictly decreases a measure
    (a linear observable, raw in every intended use) over every ground
    transition of that move.

    inputs: [move, measure, transitions, registry]
    results: Pair(verdict, Pair(registry, EmptyList)) where verdict is
      Pair(StrictlyDecreasesLabel, Pair(move, Pair(measure, EmptyList)))
    on success (exactly the fact the engel-strategies pack consumes), or
      Pair(CounterexampleLabel, Pair(move, Pair(measure, Pair(reason, EmptyList))))
    with reason = Pair(before, Pair(after, Pair(transition, EmptyList)))
    on the first non-decreasing transition. No transitions for the move
    is a counterexample with an EmptyList reason: no evidence, no
    certificate.
    """

    def __init__(self, move, measure, transitions, registry):
        self._init_ground(registry)
        self.result = self._verify(move, measure, transitions, strict=M.truth_value)
        super().__init__(
            inputs=M.Pair(
                move,
                M.Pair(
                    measure,
                    M.Pair(transitions, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def _refused(self, move, measure, reason):
        verdict = M.Pair(
            L.CounterexampleLabel,
            M.Pair(move, M.Pair(measure, M.Pair(reason, M.EmptyList))),
        )
        return M.Pair(verdict, M.Pair(self.registry, M.EmptyList))

    def _verify(self, move, measure, transitions, strict):
        seen_any = M.false_value
        remaining = transitions
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            transition = M.Head(remaining)()
            remaining = M.Tail(remaining)()
            tmove, state, next_state = self._transition_parts(transition)
            if M.TermEqual(tmove, move)() is M.false_value:
                continue
            seen_any = M.truth_value
            before = self._reading(measure, state)
            after = self._reading(measure, next_state)
            reason = M.Pair(
                before, M.Pair(after, M.Pair(transition, M.EmptyList)))
            if M.IdentityCompare(before, M.EmptyList)() is M.truth_value:
                return self._refused(move, measure, reason)
            if M.IdentityCompare(after, M.EmptyList)() is M.truth_value:
                return self._refused(move, measure, reason)
            if strict is M.truth_value:
                ok = M.NatLess(after, before, self.registry)()
            else:
                ok = M.OrAtom(
                    M.NatLess(after, before, self.registry)(),
                    M.NatEq(after, before, self.registry)(),
                )()
            if ok is M.false_value:
                return self._refused(move, measure, reason)
        if seen_any is M.false_value:
            return self._refused(move, measure, M.EmptyList)
        if strict is M.truth_value:
            verdict = M.Pair(
                L.StrictlyDecreasesLabel,
                M.Pair(move, M.Pair(measure, M.EmptyList)),
            )
        else:
            verdict = M.Pair(
                L.NonIncreasesLabel,
                M.Pair(move, M.Pair(measure, M.EmptyList)),
            )
        return M.Pair(verdict, M.Pair(self.registry, M.EmptyList))

    def __call__(self):
        return self.result


class VerifyMeasureNonIncrease(VerifyMeasureDecrease):
    """
    The semi-invariant half of VerifyMeasureDecrease: the measure never
    rises on any ground transition of the move.

    results: Pair(NonIncreasesLabel, Pair(move, Pair(measure, EmptyList)))
    on success, the same Counterexample packaging on refusal.
    """

    def __init__(self, move, measure, transitions, registry):
        self._init_ground(registry)
        self.result = self._verify(move, measure, transitions, strict=M.false_value)
        M.Edge.__init__(
            self,
            inputs=M.Pair(
                move,
                M.Pair(
                    measure,
                    M.Pair(transitions, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )


class MinePreservedObservables(M.Edge, _GroundTransitionCheck):
    """
    Mines preserved observables over a ground transition relation: each
    candidate descriptor is evaluated on both endpoints of every
    transition (all moves), and certified only if machine arithmetic
    finds equal readings throughout.

    inputs: [transitions, candidates, registry]
    results: Pair(certified, Pair(refuted, Pair(registry, EmptyList)))
      certified: chain of the candidate observable terms that are
        preserved everywhere (input order preserved);
      refuted: chain of
        Pair(observable, Pair(transition, Pair(before, Pair(after, EmptyList))))
        first-refutation witnesses.
    With no transitions nothing is certified and nothing refuted: the
    miner does not manufacture an observable out of no evidence.
    """

    def __init__(self, transitions, candidates, registry):
        self._init_ground(registry)
        self.result = self._mine(transitions, candidates)
        super().__init__(
            inputs=M.Pair(
                transitions,
                M.Pair(candidates, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _reverse(self, chain):
        out = M.EmptyList
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            out = M.Pair(M.Head(remaining)(), out)
            remaining = M.Tail(remaining)()
        return out

    def _mine(self, transitions, candidates):
        if M.IdentityCompare(transitions, M.EmptyList)() is M.truth_value:
            return M.Pair(
                M.EmptyList,
                M.Pair(M.EmptyList, M.Pair(self.registry, M.EmptyList)),
            )
        certified_rev = M.EmptyList
        refuted_rev = M.EmptyList
        remaining_candidates = candidates
        while M.IdentityCompare(remaining_candidates, M.EmptyList)() is M.false_value:
            observable = M.Head(remaining_candidates)()
            remaining_candidates = M.Tail(remaining_candidates)()
            self._reading_cache = {}
            witness = M.EmptyList
            remaining = transitions
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                transition = M.Head(remaining)()
                remaining = M.Tail(remaining)()
                _move, state, next_state = self._transition_parts(transition)
                before = self._reading(observable, state)
                after = self._reading(observable, next_state)
                unequal = M.false_value
                if M.IdentityCompare(before, M.EmptyList)() is M.truth_value:
                    unequal = M.truth_value
                elif M.IdentityCompare(after, M.EmptyList)() is M.truth_value:
                    unequal = M.truth_value
                elif M.NatEq(before, after, self.registry)() is M.false_value:
                    unequal = M.truth_value
                if unequal is M.truth_value:
                    witness = M.Pair(
                        observable,
                        M.Pair(
                            transition,
                            M.Pair(before, M.Pair(after, M.EmptyList)),
                        ),
                    )
                    break
            if M.IdentityCompare(witness, M.EmptyList)() is M.truth_value:
                certified_rev = M.Pair(observable, certified_rev)
            else:
                refuted_rev = M.Pair(witness, refuted_rev)
        return M.Pair(
            self._reverse(certified_rev),
            M.Pair(
                self._reverse(refuted_rev),
                M.Pair(self.registry, M.EmptyList),
            ),
        )

    def __call__(self):
        return self.result


class GroundObservableCertificate(M.Edge):
    """
    Provenance record a promotion can offer for a ground-verified
    observable claim (W30).  The term is
    Pair(GroundObservableCertificateLabel,
         Pair(verdict_label,
              Pair(observable, Pair(moves, Pair(transitions, [])))))
    where verdict_label is PreservesLabel or StrictlyDecreasesLabel.
    The claim: the matching ground-transition verifier certifies
    `observable` for every move in `moves` over `transitions`.  The
    record itself asserts nothing checkable; the promotion ledger's
    provenance gate re-runs the verifier (below) before trusting it.
    """

    def __init__(self, verdict_label, observable, moves, transitions):
        fields = M.Pair(
            verdict_label,
            M.Pair(
                observable,
                M.Pair(moves, M.Pair(transitions, M.EmptyList)),
            ),
        )
        self.result = M.Pair(L.GroundObservableCertificateLabel, fields)
        super().__init__(inputs=fields, results=self.result)

    def __call__(self):
        return self.result


class VerifyGroundObservableCertificate(M.Edge):
    """
    Independent re-verification of a GroundObservableCertificate: for
    every listed move, re-run the ground-transition verifier the
    certificate names and demand the certified verdict fact back,
    term for term.  Result is
    Pair(truth_or_false, Pair(reason, Pair(registry, []))) with reason
    EmptyList on success and the refusing verdict otherwise.  A
    malformed certificate, an unrecognised verdict label, or an empty
    move list refuses -- there is no vacuous passage, matching the
    verifiers' own no-evidence refusal.
    """

    def __init__(self, certificate, registry):
        self.registry = registry
        self.result = self._verify(certificate)
        super().__init__(
            inputs=M.Pair(certificate, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _refuse(self, reason):
        return M.Pair(
            M.false_value,
            M.Pair(reason, M.Pair(self.registry, M.EmptyList)),
        )

    def _verify(self, certificate):
        if M.IsPair(certificate)() is M.false_value:
            return self._refuse(certificate)
        if (
            M.IdentityCompare(
                M.Head(certificate)(), L.GroundObservableCertificateLabel
            )()
            is M.false_value
        ):
            return self._refuse(certificate)
        try:
            fields = M.Tail(certificate)()
            verdict_label = M.Head(fields)()
            observable = M.Head(M.Tail(fields)())()
            moves = M.Head(M.Tail(M.Tail(fields)())())()
            transitions = M.Head(M.Tail(M.Tail(M.Tail(fields)())())())()
        except Exception:
            return self._refuse(certificate)
        if (
            M.IdentityCompare(verdict_label, L.PreservesLabel)()
            is M.truth_value
        ):
            verifier = VerifyObservablePreserved
        elif (
            M.IdentityCompare(verdict_label, L.StrictlyDecreasesLabel)()
            is M.truth_value
        ):
            verifier = VerifyMeasureDecrease
        else:
            return self._refuse(certificate)
        if M.IdentityCompare(moves, M.EmptyList)() is M.truth_value:
            return self._refuse(certificate)
        remaining = moves
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            move = M.Head(remaining)()
            remaining = M.Tail(remaining)()
            pair = verifier(move, observable, transitions, self.registry)()
            verdict = M.Head(pair)()
            self.registry = M.Head(M.Tail(pair)())()
            expected = M.Pair(
                verdict_label,
                M.Pair(move, M.Pair(observable, M.EmptyList)),
            )
            if M.Compare(verdict, expected)() is M.false_value:
                return M.Pair(
                    M.false_value,
                    M.Pair(verdict, M.Pair(self.registry, M.EmptyList)),
                )
        return M.Pair(
            M.truth_value,
            M.Pair(M.EmptyList, M.Pair(self.registry, M.EmptyList)),
        )

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
    "LinearObservable",
    "LinearObservableValue",
    "VerifyObservablePreserved",
    "VerifyMeasureDecrease",
    "VerifyMeasureNonIncrease",
    "MinePreservedObservables",
    "GroundObservableCertificate",
    "VerifyGroundObservableCertificate",
)
