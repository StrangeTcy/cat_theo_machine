"""Ingress regressions. Run as a module from the project's Anaconda Prompt.

No mocking or monkeypatching. This module checks parsing and dispatch.
Real coordinator and subprocess equality is checked through the live fixture
and ingress_receipts, using the normal installed packs, not a substitute prover.
"""
from . import machine as M
from . import graph as G
from . import labels as L
from . import heuristics as H
from . import proof_ingress as I


class ProofIngressRegression(M.Edge):
    def __init__(self):
        self.result = M.truth_value
        cases = M.Pair(
            M.Char("prove that for all n > 2 a^n + b^n = c^n has no solutions in natural numbers"),
            M.EmptyList,
        )
        while cases is not M.EmptyList:
            text = M.Head(cases)()()
            request = I.LiveProofRequest(I.ProofTokenStream(text)())
            direct = I.MathematicalSentence(request.claim)
            if request.recognized is not M.truth_value or request.goal is not M.EmptyList:
                self.result = M.false_value
            if M.Compare(M.Head(request.outcome)(), M.Char("semantic-clarification"))() is M.false_value:
                self.result = M.false_value
            if M.Compare(direct(), request.outcome)() is M.false_value:
                self.result = M.false_value
            # EmptyList has no prover interface: a mistaken submission raises.
            if I.SubmitForegroundGoal(M.EmptyList, request)() is not M.EmptyList:
                self.result = M.false_value
            if "No proof submitted." not in I.ProofIngressMessage(request.outcome)():
                self.result = M.false_value
            print(I.ProofIngressMessage(request.outcome)())
            cases = M.Tail(cases)()

        cases = M.Pair(
            M.Char("prove that for all > 2 a^n = b^n has no solutions in positive integers"),
            M.Pair(M.Char("prove that for all n in positive integers n + = n"),
            M.Pair(M.Char("prove that for all n in positive integers n = n trailing"),
            M.Pair(M.Char("prove that for all n in positive integers n = x"),
            M.Pair(M.Char("prove that for all n in positive integers > k n = n"),
            M.Pair(M.Char("prove that for all n in positive integers for all n in positive integers n = n"),
            M.Pair(M.Char("prove that"), M.EmptyList)))))),
        )
        while cases is not M.EmptyList:
            request = I.LiveProofRequest(I.ProofTokenStream(M.Head(cases)()())())
            if request.goal is not M.EmptyList:
                self.result = M.false_value
            if M.Compare(M.Head(request.outcome)(), M.Char("parse-failure"))() is M.false_value:
                self.result = M.false_value
            if I.SubmitForegroundGoal(M.EmptyList, request)() is not M.EmptyList:
                self.result = M.false_value
            token = M.Head(M.Tail(request.outcome)())()
            span = M.Tail(M.Tail(token)())()
            if span is M.EmptyList:
                self.result = M.false_value
            if "No proof submitted." not in I.ProofIngressMessage(request.outcome)():
                self.result = M.false_value
            print(I.ProofIngressMessage(request.outcome)())
            cases = M.Tail(cases)()

        cases = M.Pair(
            M.Char("prove that for all n in positive integers > 2 a^n + b^n = c^n has no solutions in positive integers"),
            M.Pair(M.Char("prove that for all k in nonnegative integers > 5 x^k + y^k = z^k has no solutions in nonnegative integers"),
            M.Pair(M.Char("prove that for all n in nonnegative integers n + 0 = n"),
            M.Pair(M.Char("prove that for all t in positive integers (t + 0) * 1 = t"), M.EmptyList))),
        )
        cases = M.Pair(M.Char("prove that for all n > 2 a^n + b^n = c^n has no solutions in positive integers"), cases)
        cases = M.Pair(M.Char("prove that for all k > 3 x^k + y^k = z^k has no solutions in positive integers"), cases)
        cases = M.Pair(M.Char("prove that for all t > 0 t + 0 = t"), cases)
        heuristic = H.Heuristic(M.DFSLabel, M.GoalHeadOrderLabel, M.Zero, M.one, M.one, M.one)()
        while cases is not M.EmptyList:
            request = I.LiveProofRequest(I.ProofTokenStream(M.Head(cases)()())())
            direct = I.MathematicalSentence(request.claim)
            if request.goal is M.EmptyList or M.Compare(request.goal, direct.goal)() is M.false_value:
                self.result = M.false_value
            else:
                print("parsed goal: " + I.ProofGoalText(request.goal)())
                canonical = H.HeuristicCanonicalize(request.goal, heuristic, M.AllConstructors)()
                if M.Compare(canonical, direct.goal)() is M.false_value:
                    self.result = M.false_value
                if M.Compare(M.Head(canonical)(), M.Char("forall"))() is M.false_value:
                    self.result = M.false_value
            cases = M.Tail(cases)()

        # Independent structural oracle for quantifier scope and no-solutions.
        n = M.Pair(M.Char("bound-variable"), M.Pair(M.Char("n"), M.EmptyList))
        a = M.Pair(M.Char("bound-variable"), M.Pair(M.Char("a"), M.EmptyList))
        b = M.Pair(M.Char("bound-variable"), M.Pair(M.Char("b"), M.EmptyList))
        c = M.Pair(M.Char("bound-variable"), M.Pair(M.Char("c"), M.EmptyList))
        a_power = M.Pair(L.ExprPowLabel, M.Pair(a, M.Pair(n, M.EmptyList)))
        b_power = M.Pair(L.ExprPowLabel, M.Pair(b, M.Pair(n, M.EmptyList)))
        c_power = M.Pair(L.ExprPowLabel, M.Pair(c, M.Pair(n, M.EmptyList)))
        addition = M.Pair(L.ExprAddLabel, M.Pair(a_power, M.Pair(b_power, M.EmptyList)))
        formula = M.Pair(L.ExprEqLabel, M.Pair(addition, M.Pair(c_power, M.EmptyList)))
        names = M.Pair(M.Char("unknowns"), M.Pair(M.Char("a"), M.Pair(M.Char("b"), M.Pair(M.Char("c"), M.EmptyList))))
        formula = M.Pair(M.Char("nosolutions"), M.Pair(M.Char("positive-integers"), M.Pair(names, M.Pair(formula, M.EmptyList))))
        two = M.Pair(L.ExprIntLabel, M.Pair(M.GMPRep("2"), M.EmptyList))
        guard = M.Pair(L.ExprLtLabel, M.Pair(two, M.Pair(n, M.EmptyList)))
        formula = M.Pair(M.Char("implies"), M.Pair(guard, M.Pair(formula, M.EmptyList)))
        oracle = M.Pair(M.Char("forall"), M.Pair(M.Char("n"), M.Pair(M.Char("positive-integers"), M.Pair(formula, M.EmptyList))))
        request = I.LiveProofRequest(I.ProofTokenStream("prove that for all n in positive integers > 2 a^n + b^n = c^n has no solutions in positive integers")())
        if M.Compare(oracle, request.goal)() is M.false_value:
            self.result = M.false_value
        bad = I.LiveProofRequest(I.ProofTokenStream("prove that for all >")())
        token = M.Head(M.Tail(bad.outcome)())()
        span = M.Tail(M.Tail(token)())()
        if M.Compare(M.Head(span)(), M.GMPRep("19"))() is M.false_value:
            self.result = M.false_value
        if M.Compare(M.Head(M.Tail(span)())(), M.GMPRep("20"))() is M.false_value:
            self.result = M.false_value

        # Repaired operator regressions: >= and <= are single operator tokens.
        strict = I.LiveProofRequest(I.ProofTokenStream("prove that for all n > 2 a^n + b^n = c^n has no solutions in positive integers")())
        inclusive = I.LiveProofRequest(I.ProofTokenStream("prove that for all n >= 2 a^n + b^n = c^n has no solutions in positive integers")())
        if inclusive.goal is M.EmptyList or strict.goal is M.EmptyList:
            self.result = M.false_value
        if M.Compare(strict.goal, inclusive.goal)() is M.truth_value:
            self.result = M.false_value
        inclusive_text = I.ProofGoalText(inclusive.goal)()
        strict_text = I.ProofGoalText(strict.goal)()
        if "ge(" not in inclusive_text or "lt(" not in strict_text:
            self.result = M.false_value
        # Whitespace around the operator cannot split >=.
        tight = I.LiveProofRequest(I.ProofTokenStream("prove that for all n >= 2 a^n+b^n=c^n has no solutions in positive integers")())
        spaced = I.LiveProofRequest(I.ProofTokenStream("prove that for all n >= 2 a^n + b^n = c^n has no solutions in positive integers")())
        if M.Compare(tight.goal, spaced.goal)() is M.false_value:
            self.result = M.false_value
        # <= keeps its own head and never turns into a strict comparison.
        le_request = I.LiveProofRequest(I.ProofTokenStream("prove that for all n <= 5 n + 0 = n")())
        if le_request.goal is M.EmptyList:
            self.result = M.false_value
        if "le(" not in I.ProofGoalText(le_request.goal)():
            self.result = M.false_value
        # Both no-solutions phrasings with an explicit positive-integer domain
        # agree, and bind exactly the listed variables.
        has_no = I.LiveProofRequest(I.ProofTokenStream("prove that for all n >= 2 a^n + b^n = c^n has no solutions in positive integers")())
        not_solvable = I.LiveProofRequest(I.ProofTokenStream("prove that for all n >= 2 a^n + b^n = c^n is not solvable for a, b, c which are positive integers")())
        if M.Compare(has_no.goal, not_solvable.goal)() is M.false_value:
            self.result = M.false_value
        ge_guard = M.Pair(M.Char("ge"), M.Pair(n, M.Pair(two, M.EmptyList)))
        explicit_names = M.Pair(M.Char("unknowns"), M.Pair(M.Char("a"), M.Pair(M.Char("b"), M.Pair(M.Char("c"), M.EmptyList))))
        explicit_equation = M.Pair(L.ExprEqLabel, M.Pair(addition, M.Pair(c_power, M.EmptyList)))
        explicit_nosol = M.Pair(M.Char("nosolutions"), M.Pair(M.Char("positive-integers"), M.Pair(explicit_names, M.Pair(explicit_equation, M.EmptyList))))
        explicit_implied = M.Pair(M.Char("implies"), M.Pair(ge_guard, M.Pair(explicit_nosol, M.EmptyList)))
        explicit_oracle = M.Pair(M.Char("forall"), M.Pair(M.Char("n"), M.Pair(explicit_implied, M.EmptyList)))
        if M.Compare(not_solvable.goal, explicit_oracle)() is M.false_value:
            self.result = M.false_value
        # The exact acceptance sentence requests clarification for its
        # natural-number domain and must not submit a proof.
        exact = I.LiveProofRequest(I.ProofTokenStream("prove that for all n >= 2 a^n + b^n = c^n is not solvable for a,b,c which are natural numbers")())
        if exact.goal is not M.EmptyList:
            self.result = M.false_value
        if M.Compare(M.Head(exact.outcome)(), M.Char("semantic-clarification"))() is M.false_value:
            self.result = M.false_value
        if I.SubmitForegroundGoal(M.EmptyList, exact)() is not M.EmptyList:
            self.result = M.false_value
        if "No proof submitted." not in I.ProofIngressMessage(exact.outcome)():
            self.result = M.false_value
        print(I.ProofIngressMessage(exact.outcome)())
        # Malformed solvable-for lists are precise diagnostics, not goals.
        omitted = I.LiveProofRequest(I.ProofTokenStream("prove that for all n >= 2 a^n + b^n = c^n is not solvable for a, b which are positive integers")())
        duplicate = I.LiveProofRequest(I.ProofTokenStream("prove that for all n >= 2 a^n + b^n = c^n is not solvable for a, a, b, c which are positive integers")())
        ghost = I.LiveProofRequest(I.ProofTokenStream("prove that for all n >= 2 a^n + b^n = c^n is not solvable for a, b, c, d which are positive integers")())
        malformed = M.Pair(omitted, M.Pair(duplicate, M.Pair(ghost, M.EmptyList)))
        while malformed is not M.EmptyList:
            bad_request = M.Head(malformed)()
            if bad_request.goal is not M.EmptyList:
                self.result = M.false_value
            if M.Compare(M.Head(bad_request.outcome)(), M.Char("parse-failure"))() is M.false_value:
                self.result = M.false_value
            if I.SubmitForegroundGoal(M.EmptyList, bad_request)() is not M.EmptyList:
                self.result = M.false_value
            malformed = M.Tail(malformed)()

        identity = I.LiveProofRequest(I.ProofTokenStream("prove that for all n in nonnegative integers n + 0 = n")())
        expected = "forall(n, nonnegative-integers, eq(add(bound-variable(n), 0), bound-variable(n)))"
        if I.ProofGoalText(identity.goal)() != expected:
            self.result = M.false_value
        natural = I.LiveProofRequest(I.ProofTokenStream("prove that for all n in natural numbers n = n")())
        if natural.goal is not M.EmptyList:
            self.result = M.false_value
        positive = I.LiveProofRequest(I.ProofTokenStream("prove that for all n in positive integers n = n")())
        zero_inclusive = I.LiveProofRequest(I.ProofTokenStream("prove that for all n in nonnegative integers n = n")())
        if M.Compare(positive.goal, zero_inclusive.goal)() is M.truth_value:
            self.result = M.false_value

        formal = "add ( two , two )"
        formal_request = I.LiveProofRequest(I.ProofTokenStream(formal)())
        if formal_request.recognized is not M.false_value:
            self.result = M.false_value
        if I.SubmitForegroundGoal(M.EmptyList, formal_request)() is not M.EmptyList:
            self.result = M.false_value
        vocabulary = G.DefaultCorrespondenceVocabulary()()
        digits = M.Head(M.Tail(M.Tail(vocabulary)())())()
        words = G.WordsOfText(formal, G.DefaultReadingPolicy()(), digits)()
        result = G.Converse(vocabulary, G.Surface(words)(), M.AllConstructors)()
        if M.Head(M.Head(result)())() is not L.UnderstoodLabel:
            self.result = M.false_value
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


if __name__ == "__main__":
    if ProofIngressRegression()() is M.truth_value:
        print("PASS: proof ingress parser/dispatcher/scope regressions")
    else:
        raise SystemExit("FAIL: proof ingress regressions")
