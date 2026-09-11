"""Machine-native ingress for quantified arithmetic proof requests.

No theorem rules live here. Arithmetic uses the existing Expr labels. The
logical syntax is explicit Pair terms headed by Char atoms: forall(name,
body), forall(name, domain, body), implies(guard, body), nosolutions(domain,
unknowns(names...), equation), and bound-variable(name). Names are NOT
rewrite-rule VarTags. This initial
grammar admits one outer universal scope and an inner no-solutions scope;
nested universal scopes are rejected rather than flattened.

Only ProofTokenStream handles host characters. Everything past that boundary
-- tokens, spans, parser state, variable sets, failures and goals -- is a
machine term. Edges perform the grammar transitions. No text round trip is
used to submit a goal.
"""
import io

from . import machine as M
from . import labels as L
from . import graph as G


class ProofTokenStream(M.Edge):
    """Lossless punctuation and decimal tokens with half-open character spans.

    EOF is an explicit token, so even a missing final expression has a span.
    Positions are GMP decimal text at the character-I/O boundary.
    """

    def __init__(self, text):
        stream = io.StringIO(text)
        position = "0"
        start = "0"
        run = ""
        kind = M.EmptyList
        reversed_tokens = M.EmptyList
        reading = M.truth_value
        while reading is M.truth_value:
            character = stream.read(1)
            if character == "":
                reading = M.false_value
            next_position = position
            if reading is M.truth_value:
                next_position = G.GMPSuccText(position)()
            next_kind = M.Char("symbol")
            if character.isascii() and character.isdecimal():
                next_kind = M.Char("number")
            elif character.isascii() and (character.isalpha() or character == "_"):
                next_kind = M.Char("name")
            extend = M.false_value
            if run != "" and character != "":
                if M.Compare(kind, M.Char("name"))() is M.truth_value:
                    if M.Compare(next_kind, M.Char("name"))() is M.truth_value or M.Compare(next_kind, M.Char("number"))() is M.truth_value:
                        extend = M.truth_value
                elif M.Compare(kind, M.Char("number"))() is M.truth_value and M.Compare(next_kind, M.Char("number"))() is M.truth_value:
                    extend = M.truth_value
            if extend is M.truth_value:
                run = run + character
            else:
                if run != "":
                    reversed_tokens = M.Pair(M.Pair(M.Char(run), M.Pair(kind, M.Pair(M.GMPRep(start), M.Pair(M.GMPRep(position), M.EmptyList)))), reversed_tokens)
                    run = ""
                if reading is M.truth_value and not character.isspace():
                    start = position
                    kind = next_kind
                    run = character
                    if M.Compare(kind, M.Char("symbol"))() is M.truth_value:
                        reversed_tokens = M.Pair(M.Pair(M.Char(run), M.Pair(kind, M.Pair(M.GMPRep(start), M.Pair(M.GMPRep(next_position), M.EmptyList)))), reversed_tokens)
                        run = ""
            position = next_position
        eof = M.Pair(M.Char(""), M.Pair(M.Char("eof"), M.Pair(M.GMPRep(position), M.Pair(M.GMPRep(position), M.EmptyList))))
        self.result = M.Reverse(M.Pair(eof, reversed_tokens))()
        super().__init__(inputs=M.Pair(M.Char(text), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofParseState(M.Edge):
    def __init__(self, tokens):
        self.remaining = tokens
        self.failure = M.EmptyList
        self.free = M.EmptyList
        self.bound = M.EmptyList
        self.clarification = M.EmptyList
        self.fuel = M.GMPRep("256")
        self.token = M.Head(tokens)()
        self.word = M.Head(self.token)()
        self.kind = M.Head(M.Tail(self.token)())()
        self.result = tokens
        super().__init__(inputs=M.Pair(tokens, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofAdvance(M.Edge):
    def __init__(self, state):
        self.result = state.token
        if state.failure is M.EmptyList:
            tail = M.Tail(state.remaining)()
            if tail is not M.EmptyList:
                state.remaining = tail
                state.token = M.Head(tail)()
                state.word = M.Head(state.token)()
                state.kind = M.Head(M.Tail(state.token)())()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofFailure(M.Edge):
    """First failure wins: parse-failure(offending-token-with-span, expected)."""

    def __init__(self, state, expected):
        if state.failure is M.EmptyList:
            state.failure = M.Pair(M.Char("parse-failure"), M.Pair(state.token, M.Pair(expected, M.EmptyList)))
        self.result = state.failure
        super().__init__(inputs=M.Pair(state, M.Pair(expected, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ProofExpect(M.Edge):
    def __init__(self, state, word):
        self.result = M.EmptyList
        if state.failure is M.EmptyList:
            if M.Compare(state.word, word)() is M.truth_value:
                self.result = ProofAdvance(state)()
            else:
                ProofFailure(state, word)()
        super().__init__(inputs=M.Pair(state, M.Pair(word, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ProofName(M.Edge):
    def __init__(self, state):
        self.result = M.EmptyList
        reserved = M.Pair(M.Char("for"), M.Pair(M.Char("all"), M.Pair(M.Char("in"), M.Pair(M.Char("has"), M.Pair(M.Char("no"), M.Pair(M.Char("solutions"), M.EmptyList))))))
        if state.failure is M.EmptyList:
            if M.Compare(state.kind, M.Char("name"))() is M.truth_value and G.SurfaceChainHasWord(reserved, state.word)() is M.false_value:
                self.result = state.word
                ProofAdvance(state)()
            else:
                ProofFailure(state, M.Char("variable name"))()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofDomain(M.Edge):
    def __init__(self, state):
        self.result = M.EmptyList
        if state.failure is M.EmptyList:
            if M.Compare(state.word, M.Char("positive"))() is M.truth_value:
                ProofAdvance(state)()
                ProofExpect(state, M.Char("integers"))()
                self.result = M.Char("positive-integers")
            elif M.Compare(state.word, M.Char("nonnegative"))() is M.truth_value:
                ProofAdvance(state)()
                ProofExpect(state, M.Char("integers"))()
                self.result = M.Char("nonnegative-integers")
            elif M.Compare(state.word, M.Char("natural"))() is M.truth_value:
                token = state.token
                ProofAdvance(state)()
                ProofExpect(state, M.Char("numbers"))()
                state.clarification = M.Pair(M.Char("semantic-clarification"), M.Pair(token, M.Pair(M.Char("Does natural numbers include zero? Specify nonnegative integers (includes zero) or positive integers (excludes zero)."), M.EmptyList)))
                self.result = M.Char("unresolved-natural-numbers")
            else:
                ProofFailure(state, M.Char("domain: positive integers, nonnegative integers, or natural numbers"))()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofArithmetic(M.Edge):
    """Precedence grammar: sum -> product -> right-associative power -> atom."""

    def __init__(self, state, level):
        self.result = M.EmptyList
        fuel = M.GMPRepText(state.fuel)()
        if G.GMPEqualText(fuel, "0")() is M.truth_value:
            ProofFailure(state, M.Char("arithmetic within the 256-transition ingress budget"))()
        else:
            state.fuel = M.GMPRep(G.GMPSubText(fuel, "1")())
        if state.failure is M.EmptyList:
            if M.Compare(level, M.Char("atom"))() is M.truth_value:
                if M.Compare(state.word, M.Char("("))() is M.truth_value:
                    ProofAdvance(state)()
                    self.result = ProofArithmetic(state, M.Char("sum"))()
                    ProofExpect(state, M.Char(")"))()
                elif M.Compare(state.kind, M.Char("number"))() is M.truth_value:
                    self.result = M.Pair(L.ExprIntLabel, M.Pair(M.GMPRep(state.word()), M.EmptyList))
                    ProofAdvance(state)()
                else:
                    if M.Compare(state.kind, M.Char("name"))() is M.false_value:
                        ProofFailure(state, M.Char("arithmetic atom: numeral, variable, or parenthesized expression"))()
                    name = ProofName(state)()
                    if state.failure is M.EmptyList:
                        self.result = M.Pair(M.Char("bound-variable"), M.Pair(name, M.EmptyList))
                        if M.Compare(name, state.bound)() is M.false_value and G.SurfaceChainHasWord(state.free, name)() is M.false_value:
                            state.free = M.Pair(name, state.free)
            else:
                next_level = M.Char("atom")
                if M.Compare(level, M.Char("sum"))() is M.truth_value:
                    next_level = M.Char("product")
                elif M.Compare(level, M.Char("product"))() is M.truth_value:
                    next_level = M.Char("power")
                self.result = ProofArithmetic(state, next_level)()
                scanning = M.truth_value
                while scanning is M.truth_value and state.failure is M.EmptyList:
                    head = M.EmptyList
                    if M.Compare(level, M.Char("sum"))() is M.truth_value and M.Compare(state.word, M.Char("+"))() is M.truth_value:
                        head = L.ExprAddLabel
                    elif M.Compare(level, M.Char("product"))() is M.truth_value and M.Compare(state.word, M.Char("*"))() is M.truth_value:
                        head = L.ExprMulLabel
                    elif M.Compare(level, M.Char("power"))() is M.truth_value and M.Compare(state.word, M.Char("^"))() is M.truth_value:
                        head = L.ExprPowLabel
                        next_level = M.Char("power")
                    if head is M.EmptyList:
                        scanning = M.false_value
                    else:
                        ProofAdvance(state)()
                        right = ProofArithmetic(state, next_level)()
                        self.result = M.Pair(head, M.Pair(self.result, M.Pair(right, M.EmptyList)))
        if state.failure is not M.EmptyList:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(state, M.Pair(level, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ProofComparison(M.Edge):
    def __init__(self, state, left):
        self.result = M.EmptyList
        operator = state.word
        allowed = M.Pair(M.Char("="), M.Pair(M.Char("<"), M.Pair(M.Char(">"), M.EmptyList)))
        if G.SurfaceChainHasWord(allowed, operator)() is M.false_value:
            ProofFailure(state, M.Char("comparison: =, < or >"))()
        if state.failure is M.EmptyList:
            ProofAdvance(state)()
            right = ProofArithmetic(state, M.Char("sum"))()
            head = L.ExprLtLabel
            if M.Compare(operator, M.Char("="))() is M.truth_value:
                head = L.ExprEqLabel
            elif M.Compare(operator, M.Char(">"))() is M.truth_value:
                swap = left
                left = right
                right = swap
            self.result = M.Pair(head, M.Pair(left, M.Pair(right, M.EmptyList)))
        super().__init__(inputs=M.Pair(state, M.Pair(left, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class MathematicalSentence(M.Edge):
    """Complete claim parse. An unresolved domain never becomes a proof goal.

    The suffix domain binds only the equation's solution variables. An
    omitted universal domain remains an untyped universal, not an inferred
    natural or positive-integer domain. Free variables outside no-solutions
    clauses fail. Bare natural-number domains require clarification.
    """

    def __init__(self, tokens):
        state = ProofParseState(tokens)
        ProofExpect(state, M.Char("for"))()
        ProofExpect(state, M.Char("all"))()
        state.bound = ProofName(state)()
        domain = M.EmptyList
        if M.Compare(state.word, M.Char("in"))() is M.truth_value:
            ProofAdvance(state)()
            domain = ProofDomain(state)()
        guard = M.EmptyList
        if M.Compare(state.word, M.Char(">"))() is M.truth_value or M.Compare(state.word, M.Char("<"))() is M.truth_value:
            variable = M.Pair(M.Char("bound-variable"), M.Pair(state.bound, M.EmptyList))
            guard = ProofComparison(state, variable)()
            if state.free is not M.EmptyList:
                ProofFailure(state, M.Char("a bound comparison using only the quantified variable and numerals"))()
        if M.Compare(state.word, M.Char(","))() is M.truth_value:
            ProofAdvance(state)()
        if M.Compare(state.word, M.Char("for"))() is M.truth_value:
            ProofFailure(state, M.Char("single outer universal scope; nested universal grammar is not supported"))()
        left = ProofArithmetic(state, M.Char("sum"))()
        formula = ProofComparison(state, left)()
        if M.Compare(state.word, M.Char("has"))() is M.truth_value:
            ProofAdvance(state)()
            ProofExpect(state, M.Char("no"))()
            ProofExpect(state, M.Char("solutions"))()
            ProofExpect(state, M.Char("in"))()
            solution_domain = ProofDomain(state)()
            unknowns = M.Pair(M.Char("unknowns"), M.Reverse(state.free)())
            formula = M.Pair(M.Char("nosolutions"), M.Pair(solution_domain, M.Pair(unknowns, M.Pair(formula, M.EmptyList))))
        elif state.free is not M.EmptyList:
            ProofFailure(state, M.Char("no-solutions domain for free variables, or a closed quantified identity"))()
        if M.Compare(state.word, M.Char("."))() is M.truth_value:
            ProofAdvance(state)()
        ProofExpect(state, M.Char(""))()
        self.goal = M.EmptyList
        self.failure = state.failure
        self.clarification = state.clarification
        if self.failure is M.EmptyList and self.clarification is M.EmptyList:
            if guard is not M.EmptyList:
                formula = M.Pair(M.Char("implies"), M.Pair(guard, M.Pair(formula, M.EmptyList)))
            if domain is M.EmptyList:
                self.goal = M.Pair(M.Char("forall"), M.Pair(state.bound, M.Pair(formula, M.EmptyList)))
            else:
                self.goal = M.Pair(M.Char("forall"), M.Pair(state.bound, M.Pair(domain, M.Pair(formula, M.EmptyList))))
        self.result = self.goal
        if self.failure is not M.EmptyList:
            self.result = self.failure
        elif self.clarification is not M.EmptyList:
            self.result = self.clarification
        super().__init__(inputs=M.Pair(tokens, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LiveProofRequest(M.Edge):
    """Recognize the command envelope before invoking the claim grammar.

    Nonmatching commands are left to Converse, including existing formal
    arithmetic such as add ( two , two ). Tokens retain original line spans.
    """

    def __init__(self, tokens):
        self.recognized = M.false_value
        self.goal = M.EmptyList
        self.outcome = M.EmptyList
        self.claim = M.EmptyList
        state = ProofParseState(tokens)
        if M.Compare(state.word, M.Char("prove"))() is M.truth_value:
            ProofAdvance(state)()
            if M.Compare(state.word, M.Char("that"))() is M.truth_value:
                self.recognized = M.truth_value
                ProofAdvance(state)()
                self.claim = state.remaining
                parsed = MathematicalSentence(self.claim)
                self.goal = parsed.goal
                self.outcome = parsed()
        self.result = self.outcome
        super().__init__(inputs=M.Pair(tokens, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofIngressMessage(M.Edge):
    """Render a machine diagnostic only at the conversation's output boundary."""

    def __init__(self, outcome):
        token = M.Head(M.Tail(outcome)())()
        span = M.Tail(M.Tail(token)())()
        start = M.GMPRepText(M.Head(span)())()
        end = M.GMPRepText(M.Head(M.Tail(span)())())()
        description = M.Head(M.Tail(M.Tail(outcome)())())()
        self.result = str(M.Head(outcome)()()) + " at input span [" + start + ", " + end + "): " + str(description()) + " No proof submitted."
        super().__init__(inputs=M.Pair(outcome, M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result


class SubmitForegroundGoal(M.Edge):
    """Pass the parsed object to the existing runtime, never a reparsed string."""

    def __init__(self, runtime, request):
        self.goal = request.goal
        self.result = M.EmptyList
        if request.recognized is M.truth_value and self.goal is not M.EmptyList:
            self.result = runtime.prove(M.truth_value, self.goal)
        super().__init__(inputs=M.Pair(request, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofGoalText(M.Edge):
    """Render only the known ingress syntax, without general host introspection."""

    def __init__(self, term):
        if M.IsPair(term)() is M.truth_value:
            head = M.Head(term)()
            arguments = M.Tail(term)()
            if M.IdentityCompare(head, L.ExprIntLabel)() is M.truth_value:
                self.result = M.GMPRepText(M.Head(arguments)())()
            else:
                if M.IdentityCompare(head, L.ExprAddLabel)() is M.truth_value:
                    name = "add"
                elif M.IdentityCompare(head, L.ExprMulLabel)() is M.truth_value:
                    name = "mul"
                elif M.IdentityCompare(head, L.ExprPowLabel)() is M.truth_value:
                    name = "pow"
                elif M.IdentityCompare(head, L.ExprEqLabel)() is M.truth_value:
                    name = "eq"
                elif M.IdentityCompare(head, L.ExprLtLabel)() is M.truth_value:
                    name = "lt"
                else:
                    name = head()
                self.result = name + "("
                separator = ""
                while arguments is not M.EmptyList:
                    self.result = self.result + separator + ProofGoalText(M.Head(arguments)())()
                    separator = ", "
                    arguments = M.Tail(arguments)()
                self.result = self.result + ")"
        else:
            self.result = term()
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result
