"""Finite observations from shared, bounded-depth evaluation tensors."""

from . import labels as L
from . import machine as M
from . import natural_tensor as NT
from . import playground as PG
from .math import arithmetic as A


class BinaryTerm(M.Edge):
    def __init__(self, label, left, right):
        self.result = M.Pair(label, M.Pair(left, M.Pair(right, M.EmptyList)))
        super().__init__(inputs=self.result, results=self.result)

    def __call__(self):
        return self.result


class Equation(M.Edge):
    def __init__(self, variables, left, right):
        self.result = M.Pair(
            L.DiscoveredEquationLabel,
            M.Pair(variables, M.Pair(left, M.Pair(right, M.EmptyList))),
        )
        super().__init__(inputs=self.result, results=self.result)

    def __call__(self):
        return self.result


class RemoveTerm(M.Edge):
    def __init__(self, term, chain):
        self.result = M.EmptyList
        if M.IsPair(chain)() is M.truth_value:
            if M.Compare(term, M.Head(chain)())() is M.truth_value:
                self.result = M.Tail(chain)()
            else:
                self.result = M.Pair(
                    M.Head(chain)(), RemoveTerm(term, M.Tail(chain)())(),
                )
        super().__init__(inputs=M.Pair(term, chain), results=self.result)

    def __call__(self):
        return self.result


class PrefixTerms(M.Edge):
    def __init__(self, term, chains):
        self.result = M.EmptyList
        if M.IsPair(chains)() is M.truth_value:
            self.result = M.Pair(
                M.Pair(term, M.Head(chains)()),
                PrefixTerms(term, M.Tail(chains)())(),
            )
        super().__init__(inputs=M.Pair(term, chains), results=self.result)

    def __call__(self):
        return self.result


class Permutations(M.Edge):
    def __init__(self, choices, original):
        self.result = M.Pair(M.EmptyList, M.EmptyList)
        if M.IsPair(choices)() is M.truth_value:
            selected = M.Head(choices)()
            remaining = RemoveTerm(selected, original)()
            prefixed = PrefixTerms(selected, Permutations(remaining, remaining)())()
            self.result = prefixed
            if M.IsPair(M.Tail(choices)())() is M.truth_value:
                self.result = PG.ChainConcat(
                    prefixed, Permutations(M.Tail(choices)(), original)(),
                )()
        super().__init__(inputs=M.Pair(choices, original), results=self.result)

    def __call__(self):
        return self.result


class TermSplits(M.Edge):
    def __init__(self, remaining, prefix=M.EmptyList):
        self.result = M.EmptyList
        if M.IsPair(M.Tail(remaining)())() is M.truth_value:
            extended = PG.ChainAppendEnd(prefix, M.Head(remaining)())()
            right = M.Tail(remaining)()
            self.result = M.Pair(
                M.Pair(extended, M.Pair(right, M.EmptyList)),
                TermSplits(right, extended)(),
            )
        super().__init__(inputs=M.Pair(remaining, prefix), results=self.result)

    def __call__(self):
        return self.result


class TermCrossRow(M.Edge):
    def __init__(self, left, right_terms, label):
        self.result = M.EmptyList
        if M.IsPair(right_terms)() is M.truth_value:
            self.result = M.Pair(
                BinaryTerm(label, left, M.Head(right_terms)())(),
                TermCrossRow(left, M.Tail(right_terms)(), label)(),
            )
        super().__init__(inputs=M.Pair(left, right_terms), results=self.result)

    def __call__(self):
        return self.result


class TermCross(M.Edge):
    def __init__(self, left_terms, right_terms, label):
        self.result = M.EmptyList
        if M.IsPair(left_terms)() is M.truth_value:
            self.result = PG.ChainConcat(
                TermCrossRow(M.Head(left_terms)(), right_terms, label)(),
                TermCross(M.Tail(left_terms)(), right_terms, label)(),
            )()
        super().__init__(inputs=M.Pair(left_terms, right_terms), results=self.result)

    def __call__(self):
        return self.result


class SplitTerms(M.Edge):
    def __init__(self, splits, label):
        self.result = M.EmptyList
        if M.IsPair(splits)() is M.truth_value:
            split = M.Head(splits)()
            left = OrderedTerms(M.Head(split)(), label)()
            right = OrderedTerms(M.Head(M.Tail(split)())(), label)()
            self.result = PG.ChainConcat(
                TermCross(left, right, label)(),
                SplitTerms(M.Tail(splits)(), label)(),
            )()
        super().__init__(inputs=M.Pair(splits, label), results=self.result)

    def __call__(self):
        return self.result


class OrderedTerms(M.Edge):
    def __init__(self, variables, label):
        self.result = M.Pair(M.Head(variables)(), M.EmptyList)
        if M.IsPair(M.Tail(variables)())() is M.truth_value:
            self.result = SplitTerms(TermSplits(variables)(), label)()
        super().__init__(inputs=M.Pair(variables, label), results=self.result)

    def __call__(self):
        return self.result


class TermsByOrder(M.Edge):
    def __init__(self, orders, label):
        self.result = M.EmptyList
        if M.IsPair(orders)() is M.truth_value:
            self.result = PG.ChainConcat(
                OrderedTerms(M.Head(orders)(), label)(),
                TermsByOrder(M.Tail(orders)(), label)(),
            )()
        super().__init__(inputs=M.Pair(orders, label), results=self.result)

    def __call__(self):
        return self.result


class EquationRow(M.Edge):
    def __init__(self, left, remaining, variables):
        self.result = M.EmptyList
        if M.IsPair(remaining)() is M.truth_value:
            self.result = EquationRow(left, M.Tail(remaining)(), variables)()
            if M.Compare(left, M.Head(remaining)())() is M.false_value:
                self.result = M.Pair(
                    Equation(variables, left, M.Head(remaining)())(), self.result,
                )
        super().__init__(inputs=M.Pair(left, remaining), results=self.result)

    def __call__(self):
        return self.result


class Equations(M.Edge):
    def __init__(self, terms, variables):
        self.result = M.EmptyList
        if M.IsPair(terms)() is M.truth_value:
            self.result = PG.ChainConcat(
                EquationRow(M.Head(terms)(), M.Tail(terms)(), variables)(),
                Equations(M.Tail(terms)(), variables)(),
            )()
        super().__init__(inputs=M.Pair(terms, variables), results=self.result)

    def __call__(self):
        return self.result


class ConstantTerms(M.Edge):
    def __init__(self, constants, variable, label):
        self.result = M.EmptyList
        if M.IsPair(constants)() is M.truth_value:
            constant = M.Head(constants)()
            self.result = M.Pair(
                BinaryTerm(label, variable, constant)(),
                M.Pair(
                    BinaryTerm(label, constant, variable)(),
                    ConstantTerms(M.Tail(constants)(), variable, label)(),
                ),
            )
        super().__init__(inputs=M.Pair(constants, label), results=self.result)

    def __call__(self):
        return self.result


class OperationProfile(M.Edge):
    def __init__(self, entry):
        fields = M.Tail(M.Tail(M.Tail(entry)())())()
        fields = M.Tail(M.Tail(M.Tail(fields)())())()
        self.result = M.Head(M.Tail(fields)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class MixedEquations(M.Edge):
    """Compare bounded mixed trees with duplicated and permuted inputs."""

    def __init__(self, label, operations, variables):
        self.result = M.EmptyList
        if M.IsPair(operations)() is M.truth_value:
            entry = M.Head(operations)()
            other = M.Head(M.Head(M.Tail(M.Tail(entry)())())())()
            remaining = MixedEquations(label, M.Tail(operations)(), variables)()
            self.result = remaining
            if M.Compare(OperationProfile(entry)(), M.Char("bounded"))() is M.truth_value:
                if M.IdentityCompare(label, other)() is M.false_value:
                    x = M.Head(variables)()
                    y = M.Head(M.Tail(variables)())()
                    z = M.Head(M.Tail(M.Tail(variables)())())()
                    nested = BinaryTerm(other, y, z)()
                    terms = M.Pair(
                        BinaryTerm(label, x, nested)(),
                        M.Pair(
                            BinaryTerm(label, nested, x)(),
                            M.Pair(
                                BinaryTerm(
                                    other, BinaryTerm(label, x, y)(),
                                    BinaryTerm(label, x, z)(),
                                )(),
                                M.Pair(
                                    BinaryTerm(
                                        other, BinaryTerm(label, y, x)(),
                                        BinaryTerm(label, z, x)(),
                                    )(), M.EmptyList,
                                ),
                            ),
                        ),
                    )
                    self.result = PG.ChainConcat(Equations(terms, variables)(), remaining)()
        super().__init__(inputs=M.Pair(label, operations), results=self.result)

    def __call__(self):
        return self.result


class OperationCandidates(M.Edge):
    def __init__(self, entry, operations, domain, registry):
        label = M.Head(M.Head(M.Tail(M.Tail(entry)())())())()
        x = M.Char("x")
        y = M.Char("y")
        z = M.Char("z")
        variables2 = M.Pair(x, M.Pair(y, M.EmptyList))
        terms2 = TermsByOrder(Permutations(variables2, variables2)(), label)()
        self.result = Equations(terms2, variables2)()
        profile = OperationProfile(entry)()
        if M.Compare(profile, M.Char("predicate"))() is M.false_value:
            constants = domain
            if PG.ChainContains(constants, M.Zero, registry)() is M.false_value:
                constants = M.Pair(M.Zero, constants)
            if PG.ChainContains(constants, M.one, registry)() is M.false_value:
                constants = M.Pair(M.one, constants)
            unary = M.Pair(
                BinaryTerm(label, x, x)(), ConstantTerms(constants, x, label)(),
            )
            self.result = PG.ChainConcat(
                self.result, EquationRow(x, unary, M.Pair(x, M.EmptyList))(),
            )()
        if M.Compare(profile, M.Char("bounded"))() is M.truth_value:
            variables3 = M.Pair(x, M.Pair(y, M.Pair(z, M.EmptyList)))
            terms3 = TermsByOrder(Permutations(variables3, variables3)(), label)()
            self.result = PG.ChainConcat(
                self.result,
                PG.ChainConcat(
                    Equations(terms3, variables3)(),
                    MixedEquations(label, operations, variables3)(),
                )(),
            )()
        super().__init__(inputs=M.Pair(entry, domain), results=self.result)

    def __call__(self):
        return self.result


class KnownEquation(M.Edge):
    def __init__(self, nodes, operation, equation, domain):
        self.result = M.false_value
        if M.IsPair(nodes)() is M.truth_value:
            node = M.Head(nodes)()
            if M.IsPair(node)() is M.truth_value:
                if M.IdentityCompare(M.Head(node)(), L.NamedRegularityLabel)() is M.truth_value:
                    body = M.Tail(M.Tail(node)())()
                    saved_operation = M.Head(body)()
                    saved_equation = M.Head(M.Tail(body)())()
                    saved_domain = M.Head(M.Tail(M.Tail(body)())())()
                    self.result = M.AndAtom(
                        M.Compare(operation, saved_operation)(),
                        M.AndAtom(
                            M.Compare(equation, saved_equation)(),
                            M.Compare(domain, saved_domain)(),
                        )(),
                    )()
            if self.result is M.false_value:
                self.result = KnownEquation(M.Tail(nodes)(), operation, equation, domain)()
        super().__init__(inputs=M.Pair(nodes, equation), results=self.result)

    def __call__(self):
        return self.result


class CachedTensorLookup(M.Edge):
    def __init__(self, key, tensors):
        self.result = M.EmptyList
        if M.IsPair(tensors)() is M.truth_value:
            entry = M.Head(tensors)()
            if M.Compare(key, M.Head(entry)())() is M.truth_value:
                self.result = M.Head(M.Tail(entry)())()
            else:
                self.result = CachedTensorLookup(key, M.Tail(tensors)())()
        super().__init__(inputs=M.Pair(key, tensors), results=self.result)

    def __call__(self):
        return self.result


class CachedTensor(M.Edge):
    def __init__(self, term, variables, domain, registry, operations, cache):
        tensors = M.Head(cache)()
        evaluations = M.Head(M.Tail(cache)())()
        key = M.Pair(variables, M.Pair(term, M.Pair(domain, M.Pair(operations, M.EmptyList))))
        tensor = CachedTensorLookup(key, tensors)()
        if M.IdentityCompare(tensor, M.EmptyList)() is M.truth_value:
            built = NT.TensorGrid(term, variables, domain, registry, operations, evaluations)()
            tensor = M.Head(built)()
            registry = M.Head(M.Tail(built)())()
            evaluations = M.Head(M.Tail(M.Tail(built)())())()
            tensors = M.Pair(M.Pair(key, M.Pair(tensor, M.EmptyList)), tensors)
        cache = M.Pair(tensors, M.Pair(evaluations, M.EmptyList))
        self.result = M.Pair(tensor, M.Pair(registry, M.Pair(cache, M.EmptyList)))
        super().__init__(inputs=M.Pair(term, variables), results=self.result)

    def __call__(self):
        return self.result


class TakeWitnesses(M.Edge):
    def __init__(self, witnesses, remaining=M.Pair(M.one, M.Pair(M.one, M.Pair(M.one, M.EmptyList)))):
        self.result = M.EmptyList
        if M.IsPair(remaining)() is M.truth_value:
            if M.IsPair(witnesses)() is M.truth_value:
                self.result = M.Pair(
                    M.Head(witnesses)(),
                    TakeWitnesses(M.Tail(witnesses)(), M.Tail(remaining)())(),
                )
        super().__init__(inputs=M.Pair(witnesses, remaining), results=self.result)

    def __call__(self):
        return self.result


class UsefulAssignment(M.Edge):
    def __init__(self, assignment, registry):
        self.result = M.false_value
        if M.IsPair(assignment)() is M.truth_value:
            first = M.Head(assignment)()
            if M.NatEq(first, M.Zero, registry)() is M.false_value:
                self.result = M.truth_value
                rest = M.Tail(assignment)()
                if M.IsPair(rest)() is M.truth_value:
                    self.result = M.AndAtom(
                        M.NotAtom(M.NatEq(first, M.Head(rest)(), registry)())(),
                        UsefulAssignment(rest, registry)(),
                    )()
        super().__init__(inputs=M.Pair(assignment, registry), results=self.result)

    def __call__(self):
        return self.result


class CompareTensors(M.Edge):
    """Traverse axes separately; stack depth follows axis sizes, not D**arity."""

    def __init__(self, left, right, variables, registry):
        verdict = M.truth_value
        witnesses = M.EmptyList
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            assignment = M.Head(M.Tail(left)())()
            lv = M.Head(M.Tail(M.Tail(left)())())()
            rv = M.Head(M.Tail(M.Tail(right)())())()
            if M.IdentityCompare(lv, M.EmptyList)() is M.truth_value:
                verdict = M.false_value
            elif M.IdentityCompare(rv, M.EmptyList)() is M.truth_value:
                verdict = M.false_value
            elif A.IsNat(lv, registry)() is M.truth_value:
                if A.IsNat(rv, registry)() is M.truth_value:
                    verdict = M.NatEq(lv, rv, registry)()
                else:
                    verdict = M.false_value
            else:
                verdict = M.Compare(lv, rv)()
            if verdict is M.truth_value:
                if UsefulAssignment(assignment, registry)() is M.truth_value:
                    witnesses = M.Pair(
                        M.Pair(assignment, M.Pair(lv, M.Pair(rv, M.EmptyList))), M.EmptyList,
                    )
        elif M.IsPair(left)() is M.truth_value:
            if M.IsPair(right)() is M.truth_value:
                first = CompareTensors(M.Head(left)(), M.Head(right)(), M.Tail(variables)(), registry)()
                verdict = M.Head(first)()
                witnesses = M.Head(M.Tail(first)())()
                if verdict is M.truth_value:
                    rest = CompareTensors(M.Tail(left)(), M.Tail(right)(), variables, registry)()
                    verdict = M.Head(rest)()
                    witnesses = TakeWitnesses(PG.ChainConcat(witnesses, M.Head(M.Tail(rest)())())())()
            else:
                verdict = M.false_value
        elif M.IdentityCompare(left, right)() is M.false_value:
            verdict = M.false_value
        self.result = M.Pair(verdict, M.Pair(witnesses, M.EmptyList))
        super().__init__(inputs=M.Pair(left, M.Pair(right, variables)), results=self.result)

    def __call__(self):
        return self.result


class FirstTensorWitness(M.Edge):
    def __init__(self, left, right, variables):
        if M.IdentityCompare(variables, M.EmptyList)() is M.truth_value:
            assignment = M.Head(M.Tail(left)())()
            lv = M.Head(M.Tail(M.Tail(left)())())()
            rv = M.Head(M.Tail(M.Tail(right)())())()
            self.result = M.Pair(M.Pair(assignment, M.Pair(lv, M.Pair(rv, M.EmptyList))), M.EmptyList)
        else:
            self.result = FirstTensorWitness(M.Head(left)(), M.Head(right)(), M.Tail(variables)())()
        super().__init__(inputs=M.Pair(left, right), results=self.result)

    def __call__(self):
        return self.result


class CheckEquation(M.Edge):
    def __init__(self, equation, domain, registry, operations, cache):
        variables = M.Head(M.Tail(equation)())()
        body = M.Tail(M.Tail(equation)())()
        left = CachedTensor(M.Head(body)(), variables, domain, registry, operations, cache)()
        registry = M.Head(M.Tail(left)())()
        cache = M.Head(M.Tail(M.Tail(left)())())()
        right = CachedTensor(M.Head(M.Tail(body)())(), variables, domain, registry, operations, cache)()
        registry = M.Head(M.Tail(right)())()
        cache = M.Head(M.Tail(M.Tail(right)())())()
        checked = CompareTensors(M.Head(left)(), M.Head(right)(), variables, registry)()
        verdict = M.Head(checked)()
        witnesses = M.Head(M.Tail(checked)())()
        if verdict is M.truth_value:
            if M.IdentityCompare(witnesses, M.EmptyList)() is M.truth_value:
                witnesses = FirstTensorWitness(M.Head(left)(), M.Head(right)(), variables)()
        self.result = M.Pair(verdict, M.Pair(witnesses, M.Pair(registry, M.Pair(cache, M.EmptyList))))
        super().__init__(inputs=M.Pair(equation, domain), results=self.result)

    def __call__(self):
        return self.result


class ObserveEquations(M.Edge):
    def __init__(self, operation, equations, domain, registry, operations, known, cache, stop_after_first):
        findings = M.EmptyList
        remaining = M.EmptyList
        if M.IsPair(equations)() is M.truth_value:
            equation = M.Head(equations)()
            remaining = M.Tail(equations)()
            if KnownEquation(known, operation, equation, domain)() is M.false_value:
                checked = CheckEquation(equation, domain, registry, operations, cache)()
                verdict = M.Head(checked)()
                witnesses = M.Head(M.Tail(checked)())()
                registry = M.Head(M.Tail(M.Tail(checked)())())()
                cache = M.Head(M.Tail(M.Tail(M.Tail(checked)())())())()
                if verdict is M.truth_value:
                    scope = M.Pair(M.Char("holds"), M.Pair(domain, M.EmptyList))
                    finding = M.Pair(
                        L.ObservedRegularityLabel,
                        M.Pair(operation, M.Pair(equation, M.Pair(verdict, M.Pair(witnesses, M.Pair(scope, M.EmptyList))))),
                    )
                    findings = M.Pair(finding, M.EmptyList)
                    PG.NaturalPlaygroundDebugEmit(M.Char("observed " + operation() + ": " + PG.RenderDiscoveredEquation(equation, registry)()))()
                    if stop_after_first is M.truth_value:
                        remaining = M.EmptyList
            if M.IsPair(remaining)() is M.truth_value:
                rest = ObserveEquations(operation, remaining, domain, registry, operations, known, cache, stop_after_first)()
                findings = PG.ChainConcat(findings, M.Head(rest)())()
                registry = M.Head(M.Tail(rest)())()
                cache = M.Head(M.Tail(M.Tail(rest)())())()
        self.result = M.Pair(findings, M.Pair(registry, M.Pair(cache, M.EmptyList)))
        super().__init__(inputs=M.Pair(operation, equations), results=self.result)

    def __call__(self):
        return self.result


class ObserveOperations(M.Edge):
    def __init__(self, remaining, domain, registry, operations, known, cache, stop_after_first):
        findings = M.EmptyList
        if M.IsPair(remaining)() is M.truth_value:
            entry = M.Head(remaining)()
            operation = M.Head(entry)()
            equations = OperationCandidates(entry, operations, domain, registry)()
            PG.NaturalPlaygroundDebugEmit(M.Char("comparing cached tensors for " + operation()))()
            observed = ObserveEquations(operation, equations, domain, registry, operations, known, cache, stop_after_first)()
            findings = M.Head(observed)()
            registry = M.Head(M.Tail(observed)())()
            cache = M.Head(M.Tail(M.Tail(observed)())())()
            rest = ObserveOperations(M.Tail(remaining)(), domain, registry, operations, known, cache, stop_after_first)()
            findings = PG.ChainConcat(findings, M.Head(rest)())()
            registry = M.Head(M.Tail(rest)())()
            cache = M.Head(M.Tail(M.Tail(rest)())())()
        self.result = M.Pair(findings, M.Pair(registry, M.Pair(cache, M.EmptyList)))
        super().__init__(inputs=M.Pair(remaining, domain), results=self.result)

    def __call__(self):
        return self.result


class MineOperationInvariantsAcrossRegister(M.Edge):
    def __init__(self, domain, registry, operation_register=M.EmptyList,
                 known_nodes=M.EmptyList, target_operations=M.EmptyList,
                 stop_after_first=M.false_value, tensor_cache=M.EmptyList):
        operations = operation_register
        if M.IdentityCompare(operations, M.EmptyList)() is M.truth_value:
            operations = M.Head(PG.BuildNatOperationRegister(registry)())()
        targets = target_operations
        if M.IdentityCompare(targets, M.EmptyList)() is M.truth_value:
            targets = operations
        cache = tensor_cache
        if M.IdentityCompare(cache, M.EmptyList)() is M.truth_value:
            cache = M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))
        self.result = M.Pair(M.EmptyList, M.Pair(registry, M.Pair(cache, M.EmptyList)))
        if M.IsPair(domain)() is M.truth_value:
            self.result = ObserveOperations(targets, domain, registry, operations, known_nodes, cache, stop_after_first)()
        super().__init__(inputs=M.Pair(domain, operations), results=self.result)

    def __call__(self):
        return self.result
