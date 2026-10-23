"""
dialogue.py -- Socratic tutor over the machine's own objects (W15).

The tutor is a *reader* of the machine, not a second knowledge base.  Every
answer it gives is computed from machine objects that already exist:

  * concept inspection reads the loaded packs' rule maps (rule id -> rule),
    the packs' declared phi, the surface-bridge definition table and the
    promotion ledger; a word that appears in none of those sources is
    reported as "not represented in the machine";
  * a claim is parsed into facts in the packs' own vocabulary, proved by a
    bounded search over proof.KnowledgeRewriteSuccessors and *verified by
    checker_b.VerifyDerivation* (the only route to the word "verified"),
    refuted by a counterexample found with playground.BuildNatRange /
    ProductOfDomains over the machine's naturals and arithmetic edges, or
    left honestly undecided with both pieces of evidence attached;
  * Socratic questions are generated from the goal fact's shape and the
    loaded rules that can conclude it (backward obligations), ranked by how
    many premises the user already holds, and tagged with the curriculum
    rung labels (Rung1Retrieval .. Rung6Negative) that classify them;
  * the ledger view reads promotion_ledger entries and the session's own
    judged claims and says which receipt a candidate lacks.

Host/machine boundary.  Parsing a line of words and rendering an answer are
I/O; they live in the Tutor class.  Everything the answers *mean* -- claim
records, counterexamples, derivations, question records -- is a machine
term built and checked with machine edges (Pair/Head/Tail/Compare/Match,
proof.py, checker_b.py, playground.py, math/arithmetic.py).  Two boundary
conventions are inherited from the repository: a label atom is *named* by
its class name (`type(label).__name__`, the convention prettyprinting.py
and test22 use -- the machine has no edge that returns a label's name), and
a Char atom is read with `atom()`.  Both are confined to the `_label_name`
and `_char_text` helpers below.

No per-concept prose lives in this module.  The templates in Tutor are
grammatical frames ("to use RULE you still need FACT"), filled from machine
objects; the only concept text the tutor can utter is text the machine
already holds (pack descriptions, SurfaceDefinition records).
"""

from __future__ import annotations

from . import machine as M
from . import labels as L
from . import proof as P
from . import checker_b as CB
from . import playground as PG
from . import surface_bridge as SB
from . import promotion_ledger as PL
from .math import arithmetic as AR


# ---------------------------------------------------------------------------
# machine-side helpers
# ---------------------------------------------------------------------------

def chain(items):
    """Python sequence -> machine cons chain."""
    acc = M.EmptyList
    for item in reversed(list(items)):
        acc = M.Pair(item, acc)
    return acc


def to_list(cur):
    """Machine cons chain -> Python list (a walk with Head/Tail)."""
    out = []
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        out.append(M.Head(cur)())
        cur = M.Tail(cur)()
    return out


def fact(label, *args):
    """Build the constructor-call form the packs use: Pair(Label, args)."""
    return M.Pair(label, chain(args))


def fact_label(f):
    if M.IsPair(f)() is M.false_value:
        return M.EmptyList
    return M.Head(f)()


def fact_args(f):
    if M.IsPair(f)() is M.false_value:
        return []
    return to_list(M.Tail(f)())


def chain_has(cur, target):
    """Compare-based membership in a chain (never IdentityCompare on Chars)."""
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        if M.Compare(M.Head(cur)(), target)() is M.truth_value:
            return M.truth_value
        cur = M.Tail(cur)()
    return M.false_value


def _label_name(atom):
    """Boundary: the machine has no edge naming a label; prettyprinting.py and
    test22 read the class name.  Returns None for anything that is not a
    label atom."""
    if M.IsPair(atom)() is M.truth_value:
        return None
    name = type(atom).__name__
    if name.endswith("Label") and name != "ConstructorLabel":
        return name
    return None


def _char_text(atom):
    """Boundary: a Char yields its symbol when called (surface_bridge idiom)."""
    if M.IsPair(atom)() is M.truth_value:
        return None
    if type(atom).__name__ != "Char":
        return None
    return str(atom())


def _nat_value(atom, registry):
    rep = M.NatRepOf(atom, registry)()
    if M.IdentityCompare(rep, M.EmptyList)() is M.truth_value:
        return None
    val = rep()
    if val is None:
        return None
    return int(val)


def _is_var(term):
    return P.IsVarPattern(term)() is M.truth_value


def _var_text(term):
    name = M.Head(M.Tail(term)())()
    val = name()
    return "?" + str(val) if val is not None else "?v"


def concept_words(label_name):
    """'MovesNonIncreasingLabel' -> ['moves', 'non', 'increasing'];
    'NatSumLabel' -> ['nat', 'sum'].  Pure string work at the boundary."""
    base = label_name[:-5] if label_name.endswith("Label") else label_name
    words = []
    cur = ""
    for ch in base:
        if ch.isupper() and cur:
            words.append(cur.lower())
            cur = ch
        elif ch == "_":
            if cur:
                words.append(cur.lower())
            cur = ""
        else:
            cur += ch
    if cur:
        words.append(cur.lower())
    return words


def normalise_word(word):
    w = word.lower().strip(" ?.,:;!\"'")
    w = w.replace("-", "")
    if len(w) > 4 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    return w


# ---------------------------------------------------------------------------
# rendering machine terms (host I/O)
# ---------------------------------------------------------------------------

def render_term(term, registry):
    """Render a fact / constructor call / atom for the user.  Facts render as
    Name(arg, ...), Chars as their symbol, naturals as digits, pattern
    variables as ?x.  Falls back to the kernel pretty printer."""
    if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
        return "[]"
    if M.IsPair(term)() is M.truth_value:
        if _is_var(term):
            return _var_text(term)
        head = M.Head(term)()
        head_name = _label_name(head)
        if head_name is not None:
            args = [render_term(a, registry) for a in fact_args(term)]
            return head_name[:-5] + "(" + ", ".join(args) + ")"
        return "[" + ", ".join(render_term(x, registry) for x in to_list(term)) + "]"
    nat = _nat_value(term, registry)
    if nat is not None:
        return str(nat)
    text = _char_text(term)
    if text is not None:
        return text
    name = _label_name(term)
    if name is not None:
        return name[:-5]
    return M.PrettyTerm(term, registry)()


def render_fact_list(facts_chain, registry):
    return ", ".join(render_term(f, registry) for f in to_list(facts_chain))


def render_rule(rule, registry):
    premises = P.RulePremises(rule)()
    replacement = P.RuleReplacement(rule)()
    if P.ReplacementIsFactList(rule)() is M.truth_value:
        rhs = render_fact_list(replacement, registry)
    else:
        rhs = render_term(replacement, registry)
    return render_fact_list(premises, registry) + "  ->  " + rhs


def term_label_atoms(term, acc):
    """Collect the label atoms occurring anywhere in a term (identity-distinct)."""
    if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
        return acc
    if M.IsPair(term)() is M.truth_value:
        if _is_var(term):
            return acc
        term_label_atoms(M.Head(term)(), acc)
        term_label_atoms(M.Tail(term)(), acc)
        return acc
    if _label_name(term) is not None and not any(a is term for a in acc):
        acc.append(term)
    return acc


def term_vocabulary(term, acc):
    """Collect label names and Char symbols occurring anywhere in a term."""
    if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
        return acc
    if M.IsPair(term)() is M.truth_value:
        if _is_var(term):
            return acc
        term_vocabulary(M.Head(term)(), acc)
        term_vocabulary(M.Tail(term)(), acc)
        return acc
    name = _label_name(term)
    if name is not None:
        acc.add(name)
        return acc
    text = _char_text(term)
    if text is not None:
        acc.add(text)
    return acc


# ---------------------------------------------------------------------------
# claims: machine records
#
#   Pair(DialogueClaimLabel,
#        Pair(variables,            chain of Char atoms, in order of appearance
#        Pair(definitions,          chain of NatSum/NatProduct facts naming
#                                   the composite terms
#        Pair(hypotheses,           chain of condition facts
#        Pair(conclusion, [])))))   one condition fact
# ---------------------------------------------------------------------------

def make_claim(variables, definitions, hypotheses, conclusion):
    return M.Pair(
        L.DialogueClaimLabel,
        M.Pair(
            variables,
            M.Pair(
                definitions,
                M.Pair(chain(hypotheses), M.Pair(conclusion, M.EmptyList)),
            ),
        ),
    )


def is_claim(term):
    if M.IsPair(term)() is M.false_value:
        return M.false_value
    return M.IdentityCompare(M.Head(term)(), L.DialogueClaimLabel)()


def claim_variables(claim):
    return M.Head(M.Tail(claim)())()


def claim_definitions(claim):
    return M.Head(M.Tail(M.Tail(claim)())())()


def claim_hypotheses(claim):
    return M.Head(M.Tail(M.Tail(M.Tail(claim)())())())()


def claim_conclusion(claim):
    return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(claim)())())())())()


def claim_start_facts(claim):
    """Hypotheses plus the defining facts of the composite terms: this is the
    Knowledge the prover starts from."""
    facts = to_list(claim_definitions(claim)) + to_list(claim_hypotheses(claim))
    return chain(facts)


class ClaimsEquivalent(M.Edge):
    """Two claim records mean the same thing when they start from the same
    knowledge (proof.SameKnowledge: the hypothesis and definition facts cover
    each other, order-insensitive) and conclude the same fact (Compare)."""

    def __init__(self, left, right):
        if is_claim(left) is M.false_value or is_claim(right) is M.false_value:
            self.result = M.false_value
        else:
            same_start = P.SameKnowledge(
                P.Knowledge(claim_start_facts(left))(),
                P.Knowledge(claim_start_facts(right))(),
            )()
            same_goal = M.Compare(claim_conclusion(left), claim_conclusion(right))()
            self.result = M.AndAtom(same_start, same_goal)()
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# evaluation of a claim on a concrete assignment (machine arithmetic)
# ---------------------------------------------------------------------------

class EvaluateTerm(M.Edge):
    """Value of a term node under an assignment.  A node is either bound in
    the assignment (a variable), a natural literal, or defined by a NatSum /
    NatProduct fact in `definitions`.  Result: Pair(nat, Pair(registry, []))
    or Pair(EmptyList, Pair(registry, [])) when the node has no value."""

    def __init__(self, node, assignment, definitions, registry):
        self.registry = registry
        self.result = self._eval(node, assignment, definitions)
        super().__init__(
            inputs=M.Pair(node, M.Pair(assignment, M.Pair(definitions, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _lookup(self, node, assignment):
        cur = assignment
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            entry = M.Head(cur)()
            if M.Compare(M.Head(entry)(), node)() is M.truth_value:
                return M.Tail(entry)()
            cur = M.Tail(cur)()
        return M.EmptyList

    def _eval(self, node, assignment, definitions):
        bound = self._lookup(node, assignment)
        if M.IdentityCompare(bound, M.EmptyList)() is M.false_value:
            return M.Pair(bound, M.Pair(self.registry, M.EmptyList))
        rep = M.NatRepOf(node, self.registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            return M.Pair(node, M.Pair(self.registry, M.EmptyList))
        cur = definitions
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            d = M.Head(cur)()
            args = M.Tail(d)()
            x = M.Head(args)()
            y = M.Head(M.Tail(args)())()
            out = M.Head(M.Tail(M.Tail(args)())())()
            if M.Compare(out, node)() is M.truth_value:
                vx = self._eval(x, assignment, definitions)
                if M.IdentityCompare(M.Head(vx)(), M.EmptyList)() is M.truth_value:
                    return vx
                self.registry = M.Head(M.Tail(vx)())()
                vy = self._eval(y, assignment, definitions)
                if M.IdentityCompare(M.Head(vy)(), M.EmptyList)() is M.truth_value:
                    return vy
                self.registry = M.Head(M.Tail(vy)())()
                label = M.Head(d)()
                if M.IdentityCompare(label, L.NatSumLabel)() is M.truth_value:
                    res = AR.Add(M.Head(vx)(), M.Head(vy)(), self.registry)()
                elif M.IdentityCompare(label, L.NatProductLabel)() is M.truth_value:
                    res = AR.Multiply(M.Head(vx)(), M.Head(vy)(), self.registry)()
                else:
                    return M.Pair(M.EmptyList, M.Pair(self.registry, M.EmptyList))
                self.registry = M.Head(M.Tail(res)())()
                return res
            cur = M.Tail(cur)()
        return M.Pair(M.EmptyList, M.Pair(self.registry, M.EmptyList))

    def __call__(self):
        return self.result


class EvaluateCondition(M.Edge):
    """Truth of a condition fact (Even/Odd/Divides/Coprime) under an
    assignment, computed with the machine's arithmetic edges.
    Result: Pair(truth|false, Pair(registry, [])), or Pair(EmptyList, ...)
    when the predicate has no evaluator or an argument has no value."""

    def __init__(self, condition, assignment, definitions, two, registry):
        self.registry = registry
        self.result = self._eval(condition, assignment, definitions, two)
        super().__init__(
            inputs=M.Pair(condition, M.Pair(assignment, M.Pair(definitions, M.Pair(two, M.Pair(registry, M.EmptyList))))),
            results=self.result,
        )

    def _value(self, node, assignment, definitions):
        res = EvaluateTerm(node, assignment, definitions, self.registry)()
        self.registry = M.Head(M.Tail(res)())()
        return M.Head(res)()

    def _wrap(self, flag):
        return M.Pair(flag, M.Pair(self.registry, M.EmptyList))

    def _eval(self, condition, assignment, definitions, two):
        label = M.Head(condition)()
        args = M.Tail(condition)()
        first = self._value(M.Head(args)(), assignment, definitions)
        if M.IdentityCompare(first, M.EmptyList)() is M.truth_value:
            return self._wrap(M.EmptyList)
        parity = M.OrAtom(
            M.IdentityCompare(label, L.EvenLabel)(),
            M.IdentityCompare(label, L.OddLabel)(),
        )()
        if parity is M.truth_value:
            mod = AR.Modulo(first, two, self.registry)()
            self.registry = M.Head(M.Tail(mod)())()
            is_even = M.NatEq(M.Head(mod)(), M.Zero, self.registry)()
            if M.IdentityCompare(label, L.EvenLabel)() is M.truth_value:
                return self._wrap(is_even)
            return self._wrap(M.NotAtom(is_even)())
        rest = M.Tail(args)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return self._wrap(M.EmptyList)
        second = self._value(M.Head(rest)(), assignment, definitions)
        if M.IdentityCompare(second, M.EmptyList)() is M.truth_value:
            return self._wrap(M.EmptyList)
        if M.IdentityCompare(label, L.DividesLabel)() is M.truth_value:
            return self._wrap(AR.Divides(first, second, self.registry)())
        if M.IdentityCompare(label, L.CoprimeLabel)() is M.truth_value:
            return self._wrap(AR.IsCoprime(first, second, self.registry)())
        return self._wrap(M.EmptyList)

    def __call__(self):
        return self.result


class FindCounterexample(M.Edge):
    """Sweep every assignment of the claim's variables over the naturals
    below `bound` (playground.BuildNatRange / ProductOfDomains) and return
    the first assignment on which every hypothesis holds and the conclusion
    fails.

    Result:
      Pair(CounterexampleLabel, Pair(assignment, Pair(registry, [])))
      Pair(SweepReportLabel, Pair(instances_checked, Pair(instances_with_hypotheses, Pair(registry, []))))
      Pair(EmptyList, Pair(reason_label_or_fact, Pair(registry, [])))   -- a predicate with no evaluator
    """

    def __init__(self, claim, bound, two, registry):
        self.registry = registry
        self.result = self._sweep(claim, bound, two)
        super().__init__(
            inputs=M.Pair(claim, M.Pair(bound, M.Pair(two, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def _sweep(self, claim, bound, two):
        variables = claim_variables(claim)
        definitions = claim_definitions(claim)
        hypotheses = claim_hypotheses(claim)
        conclusion = claim_conclusion(claim)

        rng = PG.BuildNatRange(M.Zero, bound, self.registry)()
        domain = M.Head(rng)()
        self.registry = M.Head(M.Tail(rng)())()
        n_vars = len(to_list(variables))
        tuples = PG.ProductOfDomains(chain([domain] * n_vars))()

        checked = 0
        with_hyps = 0
        cur = tuples
        while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
            tup = M.Head(cur)()
            assignment = self._assignment(variables, tup)
            checked += 1
            hyps_hold = M.truth_value
            hcur = hypotheses
            while M.IdentityCompare(hcur, M.EmptyList)() is M.false_value:
                res = EvaluateCondition(M.Head(hcur)(), assignment, definitions, two, self.registry)()
                self.registry = M.Head(M.Tail(res)())()
                flag = M.Head(res)()
                if M.IdentityCompare(flag, M.EmptyList)() is M.truth_value:
                    return M.Pair(M.EmptyList, M.Pair(M.Head(hcur)(), M.Pair(self.registry, M.EmptyList)))
                if flag is M.false_value:
                    hyps_hold = M.false_value
                    break
                hcur = M.Tail(hcur)()
            if hyps_hold is M.truth_value:
                with_hyps += 1
                res = EvaluateCondition(conclusion, assignment, definitions, two, self.registry)()
                self.registry = M.Head(M.Tail(res)())()
                flag = M.Head(res)()
                if M.IdentityCompare(flag, M.EmptyList)() is M.truth_value:
                    return M.Pair(M.EmptyList, M.Pair(conclusion, M.Pair(self.registry, M.EmptyList)))
                if flag is M.false_value:
                    return M.Pair(L.CounterexampleLabel, M.Pair(assignment, M.Pair(self.registry, M.EmptyList)))
            cur = M.Tail(cur)()

        n_checked = M.NatFromRep(M.GMPRep(checked), self.registry)()
        self.registry = M.Head(M.Tail(n_checked)())()
        n_hyps = M.NatFromRep(M.GMPRep(with_hyps), self.registry)()
        self.registry = M.Head(M.Tail(n_hyps)())()
        return M.Pair(
            L.SweepReportLabel,
            M.Pair(M.Head(n_checked)(), M.Pair(M.Head(n_hyps)(), M.Pair(self.registry, M.EmptyList))),
        )

    def _assignment(self, variables, tup):
        entries = []
        vcur = variables
        tcur = tup
        while M.IdentityCompare(vcur, M.EmptyList)() is M.false_value:
            entries.append(M.Pair(M.Head(vcur)(), M.Head(tcur)()))
            vcur = M.Tail(vcur)()
            tcur = M.Tail(tcur)()
        return chain(entries)

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# proving a claim: bounded iterative-deepening search over knowledge rewrites
# ---------------------------------------------------------------------------

class SearchKnowledgeDerivation(M.Edge):
    """Depth-bounded search for a derivation from `start` to a state covering
    `goal` using the rules in `rules` (a chain of raw rules).  Successors come
    from proof.KnowledgeRewriteSuccessors; states already on the path are not
    revisited (SameKnowledge).  Iterative deepening, so the shortest
    derivation is found first.

    Result: Pair(derivation, Pair(registry, [])) or Pair(EmptyList, Pair(registry, []))."""

    def __init__(self, start, goal, rules, max_depth, registry):
        self.registry = registry
        self.rules = to_list(rules)
        self.goal_facts = P.KnowledgeFacts(goal)()
        self.result = self._run(start, max_depth)
        super().__init__(
            inputs=M.Pair(start, M.Pair(goal, M.Pair(rules, M.Pair(max_depth, M.Pair(registry, M.EmptyList))))),
            results=self.result,
        )

    def _covers(self, state):
        return P.FactsCover(self.goal_facts, P.KnowledgeFacts(state)())()

    def _seen(self, path, state):
        for prev in path:
            if P.SameKnowledge(prev, state)() is M.truth_value:
                return True
        return False

    def _dfs(self, state, depth, path):
        if self._covers(state) is M.truth_value:
            return []
        if depth == 0:
            return None
        for rule in self.rules:
            succs = P.KnowledgeRewriteSuccessors(state, rule)()
            for entry in to_list(succs):
                action = M.Head(entry)()
                nxt = M.Head(M.Tail(entry)())()
                if self._seen(path + [state], nxt):
                    continue
                rest = self._dfs(nxt, depth - 1, path + [state])
                if rest is not None:
                    return [(state, action, nxt)] + rest
        return None

    def _run(self, start, max_depth):
        limit = _nat_value(max_depth, self.registry) or 0
        found = None
        for depth in range(0, limit + 1):
            found = self._dfs(start, depth, [])
            if found is not None:
                break
        if found is None:
            return M.Pair(M.EmptyList, M.Pair(self.registry, M.EmptyList))
        steps = []
        for cur, action, nxt in found:
            step_res = P.Step(cur, action, nxt, self.registry)()
            steps.append(M.Head(step_res)())
            self.registry = M.Head(M.Tail(step_res)())()
        der = P.Derivation(chain(steps), P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)(), self.registry)()
        self.registry = M.Head(M.Tail(der)())()
        return M.Pair(M.Head(der)(), M.Pair(self.registry, M.EmptyList))

    def __call__(self):
        return self.result


class JudgeClaim(M.Edge):
    """Three-way verdict on a claim record.

      Pair(ClaimVerifiedLabel, Pair(derivation, Pair(checker_verdict, Pair(start, Pair(goal, Pair(registry, []))))))
          -- a derivation exists AND checker_b.VerifyDerivation accepted it
      Pair(ClaimRefutedLabel,  Pair(assignment, Pair(registry, [])))
          -- a counterexample below `bound`
      Pair(ClaimUndecidedLabel, Pair(search_outcome, Pair(sweep_outcome, Pair(registry, []))))
          -- neither; both pieces of evidence are attached.  search_outcome
             is EmptyList (no derivation within depth) or the checker's
             rejection record; sweep_outcome is the SweepReport or the
             predicate that had no evaluator.

    `trusted_rules` is the chain Checker B is told to trust; `rules` is the
    chain the search may use (normally the same chain)."""

    def __init__(self, claim, rules, trusted_rules, bound, max_depth, two, registry):
        self.registry = registry
        self.result = self._judge(claim, rules, trusted_rules, bound, max_depth, two)
        super().__init__(
            inputs=M.Pair(claim, M.Pair(rules, M.Pair(trusted_rules, M.Pair(bound, M.Pair(max_depth, M.Pair(two, M.Pair(registry, M.EmptyList))))))),
            results=self.result,
        )

    def _judge(self, claim, rules, trusted_rules, bound, max_depth, two):
        start = P.Knowledge(claim_start_facts(claim))()
        goal = P.Knowledge(M.Pair(claim_conclusion(claim), M.EmptyList))()

        search = SearchKnowledgeDerivation(start, goal, rules, max_depth, self.registry)()
        derivation = M.Head(search)()
        self.registry = M.Head(M.Tail(search)())()
        search_outcome = M.EmptyList
        if M.IdentityCompare(derivation, M.EmptyList)() is M.false_value:
            verdict = CB.VerifyDerivation(derivation, start, goal, trusted_rules, self.registry)()
            if M.IdentityCompare(M.Head(verdict)(), L.DerivationVerifiedLabel)() is M.truth_value:
                return M.Pair(
                    L.ClaimVerifiedLabel,
                    M.Pair(derivation, M.Pair(verdict, M.Pair(start, M.Pair(goal, M.Pair(self.registry, M.EmptyList))))),
                )
            search_outcome = verdict

        sweep = FindCounterexample(claim, bound, two, self.registry)()
        tag = M.Head(sweep)()
        if M.IdentityCompare(tag, L.CounterexampleLabel)() is M.truth_value:
            assignment = M.Head(M.Tail(sweep)())()
            self.registry = M.Head(M.Tail(M.Tail(sweep)())())()
            return M.Pair(L.ClaimRefutedLabel, M.Pair(assignment, M.Pair(self.registry, M.EmptyList)))
        if M.IdentityCompare(tag, L.SweepReportLabel)() is M.truth_value:
            self.registry = M.Head(M.Tail(M.Tail(M.Tail(sweep)())())())()
            sweep_outcome = M.Pair(tag, M.Pair(M.Head(M.Tail(sweep)())(), M.Pair(M.Head(M.Tail(M.Tail(sweep)())())(), M.EmptyList)))
        else:
            self.registry = M.Head(M.Tail(M.Tail(sweep)())())()
            sweep_outcome = M.Pair(M.EmptyList, M.Pair(M.Head(M.Tail(sweep)())(), M.EmptyList))
        return M.Pair(
            L.ClaimUndecidedLabel,
            M.Pair(search_outcome, M.Pair(sweep_outcome, M.Pair(self.registry, M.EmptyList))),
        )

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# Socratic obligations: which loaded rules can conclude the goal, and which
# of their premises the user already holds
# ---------------------------------------------------------------------------

class BackwardObligations(M.Edge):
    """For every rule whose replacement contains a fact matching `goal`,
    instantiate the premises with the goal bindings, then bind as much as
    the known facts allow.  Result: a chain of

        Pair(rule, Pair(satisfied_premises, Pair(open_premises, [])))

    in rule order; `open_premises` may still contain pattern variables the
    known facts could not bind."""

    def __init__(self, goal, known_facts, rules):
        self.result = self._analyse(goal, known_facts, to_list(rules))
        super().__init__(inputs=M.Pair(goal, M.Pair(known_facts, M.Pair(rules, M.EmptyList))), results=self.result)

    def _bind_against_known(self, premise, known_facts, bindings):
        """Match the original premise pattern against each known fact and keep
        the first match whose bindings merge consistently with `bindings`
        (the JoinPremises discipline: bindings are keyed by the pattern's own
        variable objects, so patterns are never copied before matching)."""
        kcur = known_facts
        while M.IdentityCompare(kcur, M.EmptyList)() is M.false_value:
            match = M.Match(premise, M.Head(kcur)())()
            if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
                merged = M.MergeBindings(bindings, M.Tail(match)())()
                if M.IdentityCompare(M.Head(merged)(), M.truth_value)() is M.truth_value:
                    return M.Pair(M.truth_value, M.Pair(M.Head(kcur)(), M.Tail(merged)()))
            kcur = M.Tail(kcur)()
        return M.Pair(M.false_value, M.Pair(premise, bindings))

    def _analyse(self, goal, known_facts, rules):
        entries = []
        for rule in rules:
            replacement = P.RuleReplacement(rule)()
            if P.ReplacementIsFactList(rule)() is M.false_value:
                continue
            for conclusion in to_list(replacement):
                match = M.Match(conclusion, goal)()
                if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.false_value:
                    continue
                bindings = M.Tail(match)()
                satisfied = []
                open_ = []
                for premise in to_list(P.RulePremises(rule)()):
                    res = self._bind_against_known(premise, known_facts, bindings)
                    hit = M.Head(res)()
                    payload = M.Tail(res)()
                    bindings = M.Tail(payload)()
                    if hit is M.truth_value:
                        satisfied.append(M.Head(payload)())
                    else:
                        open_.append(M.Head(payload)())
                # show the open premises with everything the goal and the known
                # facts bound (the originals are instantiated, so identity-keyed
                # bindings apply)
                open_ = [M.Head(M.Instantiate(p, bindings)())() for p in open_]
                entries.append(M.Pair(rule, M.Pair(chain(satisfied), M.Pair(chain(open_), M.EmptyList))))
                break
        return chain(entries)

    def __call__(self):
        return self.result


def make_question(rung_label, rule_or_empty, focus_fact):
    return M.Pair(L.SocraticQuestionLabel, M.Pair(rung_label, M.Pair(rule_or_empty, M.Pair(focus_fact, M.EmptyList))))


def question_rung(q):
    return M.Head(M.Tail(q)())()


def question_rule(q):
    return M.Head(M.Tail(M.Tail(q)())())()


def question_focus(q):
    return M.Head(M.Tail(M.Tail(M.Tail(q)())())())()


# ---------------------------------------------------------------------------
# the surface grammar for claims (host I/O; the result is a machine record)
# ---------------------------------------------------------------------------

_KEYWORDS = {
    "if", "then", "and", "is", "are", "an", "the", "of", "to", "with", "by",
    "even", "odd", "number", "divides", "divisible", "divisor", "coprime",
    "sum", "product", "times", "plus", "squared", "square", "implies",
    "whenever", "for", "every", "all", "any", "each", "natural", "naturals",
    "numbers", "integer", "integers", "we", "have", "it", "holds", "that",
    "true", ",", "+", "*", "(", ")",
}

_PREAMBLES = (
    ["is", "it", "true", "that"],
    ["claim", ":"],
    ["claim"],
    ["check", ":"],
    ["check"],
    ["prove", "that"],
    ["prove"],
    ["show", "that"],
    ["show"],
    ["conjecture", ":"],
    ["conjecture"],
)


def tokenize(text):
    out = []
    for raw in text.replace(",", " , ").replace("?", " ").replace("!", " ").split():
        word = raw.lower()
        if word.endswith(".") and len(word) > 1:
            word = word[:-1]
        if word.endswith(":") and len(word) > 1:
            out.append(word[:-1])
            out.append(":")
            continue
        # split arithmetic glued to identifiers: a+b, 2*n
        buf = ""
        for ch in word:
            if ch in "+*()":
                if buf:
                    out.append(buf)
                    buf = ""
                out.append(ch)
            else:
                buf += ch
        if buf:
            out.append(buf)
    return out


class ClaimGrammar:
    """Recursive-descent reader for the claim sublanguage.  Produces machine
    claim records whose facts use the packs' own labels (EvenLabel, OddLabel,
    DividesLabel, CoprimeLabel, NatSumLabel, NatProductLabel).  Composite
    terms are Char nodes named by their canonical infix text and *defined*
    by a NatSum / NatProduct fact, so "the sum of a and b" and "a + b" are
    the same node with the same defining fact."""

    def __init__(self, nat_builder, nat_reader):
        self._nat = nat_builder          # host int -> machine nat (registry-threaded)
        self._nat_value = nat_reader     # machine nat -> host int (or None)
        self.variables = M.EmptyList
        self.definitions = M.EmptyList

    # -- atoms ------------------------------------------------------------

    def char(self, symbol):
        return M.Char(symbol)

    def reset(self):
        self.variables = M.EmptyList
        self.definitions = M.EmptyList

    def _is_variable_word(self, word):
        return word.isalpha() and word not in _KEYWORDS and len(word) <= 3

    def _add_definition(self, label, x, y, name):
        node = self.char(name)
        new_fact = fact(label, x, y, node)
        if chain_has(self.definitions, new_fact) is M.truth_value:
            return node
        self.definitions = M.Pair(new_fact, self.definitions)
        return node

    # -- terms --------------------------------------------------------------

    def parse_term(self, words):
        """Returns a node or None.  Grammar (lowest precedence first):
           sum  := prod ('+' prod | 'plus' prod)*
           prod := atom ('*' atom | 'times' atom)*
           atom := VAR | NUMBER | 'the' 'sum' 'of' T 'and' T | 'the' 'product' 'of' T 'and' T
                 | 'the' 'square' 'of' atom | atom 'squared' | '(' sum ')'"""
        if not words:
            return None
        if words[0] == "the" and len(words) > 3 and words[1] in ("sum", "product") and words[2] == "of":
            inner = words[3:]
            # split at the top-level 'and'
            for i, w in enumerate(inner):
                if w == "and":
                    left = self.parse_term(inner[:i])
                    right = self.parse_term(inner[i + 1:])
                    if left is None or right is None:
                        return None
                    return self._binary(words[1], left, right)
            return None
        if words[0] == "the" and len(words) > 3 and words[1] == "square" and words[2] == "of":
            inner = self.parse_term(words[3:])
            if inner is None:
                return None
            return self._binary("product", inner, inner)
        if len(words) >= 2 and words[-1] == "squared":
            inner = self.parse_term(words[:-1])
            if inner is None:
                return None
            return self._binary("product", inner, inner)
        # split on top-level '+' / 'plus'
        split = self._top_level_split(words, ("+", "plus"))
        if split is not None:
            left = self.parse_term(split[0])
            right = self.parse_term(split[1])
            if left is None or right is None:
                return None
            return self._binary("sum", left, right)
        split = self._top_level_split(words, ("*", "times"))
        if split is not None:
            left = self.parse_term(split[0])
            right = self.parse_term(split[1])
            if left is None or right is None:
                return None
            return self._binary("product", left, right)
        if words[0] == "(" and words[-1] == ")":
            return self.parse_term(words[1:-1])
        if len(words) == 1:
            w = words[0]
            if w.isdigit():
                return self._nat(int(w))
            if self._is_variable_word(w):
                node = self.char(w)
                if PG.ChainHasTerm(self.variables, node)() is M.false_value:
                    self.variables = M.Pair(node, self.variables)
                return node
        return None

    def _top_level_split(self, words, ops):
        depth = 0
        for i in range(len(words) - 1, 0, -1):
            w = words[i]
            if w == ")":
                depth += 1
            elif w == "(":
                depth -= 1
            elif depth == 0 and w in ops:
                return words[:i], words[i + 1:]
        return None

    def _binary(self, kind, left, right):
        lt = self._text_of(left)
        rt = self._text_of(right)
        if kind == "sum":
            name = lt + "+" + rt
            return self._add_definition(L.NatSumLabel, left, right, name)
        if "+" in lt:
            lt = "(" + lt + ")"
        if "+" in rt:
            rt = "(" + rt + ")"
        name = lt + "*" + rt
        return self._add_definition(L.NatProductLabel, left, right, name)

    def _text_of(self, node):
        text = _char_text(node)
        if text is not None:
            return text
        val = self._nat_value(node)
        return str(val) if val is not None else "?"

    # -- conditions -----------------------------------------------------------

    def parse_condition(self, words):
        """Returns a condition fact or None.
           T 'is' ['an'] 'even' ['number'] | T 'is' ['an'] 'odd' ['number']
           T 'divides' T2 | T2 'is' 'divisible' 'by' T | T 'is' 'a' 'divisor' 'of' T2
           T 'and' T2 'are' 'coprime' | T 'is' 'coprime' ('to'|'with') T2"""
        if not words:
            return None
        if "divides" in words:
            i = words.index("divides")
            a = self.parse_term(words[:i])
            b = self.parse_term(words[i + 1:])
            if a is None or b is None:
                return None
            return fact(L.DividesLabel, a, b)
        for i in range(len(words) - 1, -1, -1):
            if words[i] != "is":
                continue
            subject = words[:i]
            pred = words[i + 1:]
            if pred and pred[0] in ("an", "a") and len(pred) > 1:
                pred = pred[1:]
            if pred and pred[-1] == "number" and len(pred) > 1:
                pred = pred[:-1]
            if pred == ["even"] or pred == ["odd"]:
                t = self.parse_term(subject)
                if t is None:
                    return None
                return fact(L.EvenLabel if pred == ["even"] else L.OddLabel, t)
            if len(pred) >= 3 and pred[0] == "divisible" and pred[1] == "by":
                b = self.parse_term(subject)
                a = self.parse_term(pred[2:])
                if a is None or b is None:
                    return None
                return fact(L.DividesLabel, a, b)
            if len(pred) >= 3 and pred[0] == "divisor" and pred[1] == "of":
                a = self.parse_term(subject)
                b = self.parse_term(pred[2:])
                if a is None or b is None:
                    return None
                return fact(L.DividesLabel, a, b)
            if len(pred) >= 3 and pred[0] == "coprime" and pred[1] in ("to", "with"):
                a = self.parse_term(subject)
                b = self.parse_term(pred[2:])
                if a is None or b is None:
                    return None
                return fact(L.CoprimeLabel, a, b)
            return None
        if len(words) >= 4 and words[-2] == "are" and words[-1] == "coprime" and "and" in words:
            i = words.index("and")
            a = self.parse_term(words[:i])
            b = self.parse_term(words[i + 1:-2])
            if a is None or b is None:
                return None
            return fact(L.CoprimeLabel, a, b)
        return None

    def parse_condition_list(self, words):
        """Split on 'and', re-merging chunks that only parse together
        ("a and b are coprime")."""
        chunks = []
        cur = []
        for w in words:
            if w == "and":
                chunks.append(cur)
                cur = []
            else:
                cur.append(w)
        chunks.append(cur)
        conditions = []
        i = 0
        while i < len(chunks):
            merged = list(chunks[i])
            j = i
            cond = self.parse_condition(merged)
            while cond is None and j + 1 < len(chunks):
                j += 1
                merged = merged + ["and"] + chunks[j]
                cond = self.parse_condition(merged)
            if cond is None:
                return None
            conditions.append(cond)
            i = j + 1
        return conditions

    # -- claims ---------------------------------------------------------------

    def parse_claim(self, words):
        """Returns a claim record or None.
           'if' C+ 'then' C  |  C+ 'implies' C  |  'whenever' C+ ',' C
           | 'for' ('every'|'all'|'any'|'each') VARS ',' C  |  C"""
        self.reset()
        words = list(words)
        for pre in _PREAMBLES:
            if words[: len(pre)] == pre:
                words = words[len(pre):]
                break
        if words and words[-1] == ".":
            words = words[:-1]
        if not words:
            return None
        hyp_words = None
        concl_words = None
        if words[0] == "if" and "then" in words:
            i = words.index("then")
            hyp_words, concl_words = words[1:i], words[i + 1:]
        elif "implies" in words:
            i = words.index("implies")
            hyp_words, concl_words = words[:i], words[i + 1:]
        elif words[0] == "whenever" and "," in words:
            i = words.index(",")
            hyp_words, concl_words = words[1:i], words[i + 1:]
        elif words[0] == "for" and "," in words:
            i = words.index(",")
            for w in words[1:i]:
                if self._is_variable_word(w):
                    self.parse_term([w])
            concl_words = words[i + 1:]
        else:
            concl_words = words
        if concl_words and concl_words[0] == "then":
            concl_words = concl_words[1:]
        hypotheses = []
        if hyp_words is not None:
            hypotheses = self.parse_condition_list(hyp_words)
            if hypotheses is None:
                return None
        conclusion = self.parse_condition(concl_words)
        if conclusion is None:
            return None
        return make_claim(self.variables, self.definitions, hypotheses, conclusion)

    # -- rendering back to the surface ------------------------------------------

    def covers(self, cond):
        """True when the condition is in the sentence grammar (so the user can
        state it as a sentence rather than as 'assume Name(args)')."""
        label = fact_label(cond)
        for known in (L.EvenLabel, L.OddLabel, L.DividesLabel, L.CoprimeLabel):
            if M.IdentityCompare(label, known)() is M.truth_value:
                return not term_vocabulary_vars(cond)
        return False

    def render_condition(self, cond, registry):
        label = fact_label(cond)
        args = fact_args(cond)
        texts = [self._render_node(a, registry) for a in args]
        if M.IdentityCompare(label, L.EvenLabel)() is M.truth_value:
            return texts[0] + " is even"
        if M.IdentityCompare(label, L.OddLabel)() is M.truth_value:
            return texts[0] + " is odd"
        if M.IdentityCompare(label, L.DividesLabel)() is M.truth_value:
            return texts[0] + " divides " + texts[1]
        if M.IdentityCompare(label, L.CoprimeLabel)() is M.truth_value:
            return texts[0] + " and " + texts[1] + " are coprime"
        return render_term(cond, registry)

    def _render_node(self, node, registry):
        text = _char_text(node)
        if text is None:
            return render_term(node, registry)
        spaced = ""
        for ch in text:
            spaced += " " + ch + " " if ch in "+*()" else ch
        return " ".join(spaced.split())

    def render_claim(self, claim, registry):
        hyps = [self.render_condition(h, registry) for h in to_list(claim_hypotheses(claim))]
        concl = self.render_condition(claim_conclusion(claim), registry)
        if hyps:
            return "if " + " and ".join(hyps) + " then " + concl
        return concl


# ---------------------------------------------------------------------------
# concept index over the machine's sources
# ---------------------------------------------------------------------------

class ConceptIndex:
    """word -> entries; each entry is (source_kind, source_name, machine_term).
    Sources: 'rule' (pack rule id -> rule), 'phi' (pack goal shape),
    'definition' (SurfaceDefinition record), 'ledger' (LedgerEntry)."""

    def __init__(self):
        self.entries = {}
        self.pack_descriptions = {}
        self.rule_packs = {}
        self.labels_by_name = {}

    def _add(self, word, entry):
        key = normalise_word(word)
        if not key:
            return
        bucket = self.entries.setdefault(key, [])
        if all(e[0] != entry[0] or e[1] != entry[1] for e in bucket):
            bucket.append(entry)

    def _add_vocabulary(self, term, entry):
        for atom in term_label_atoms(term, []):
            self.labels_by_name.setdefault(_label_name(atom)[:-5].lower(), atom)
        for name in term_vocabulary(term, set()):
            if name.endswith("Label"):
                words = concept_words(name)
                self._add("".join(words), entry)
                for w in words:
                    self._add(w, entry)
                for i in range(len(words) - 1):
                    self._add(words[i] + words[i + 1], entry)
            else:
                self._add(name, entry)

    def add_pack(self, pack):
        self.pack_descriptions[pack.name] = str(getattr(pack, "description", "") or "").strip()
        for rule_id, rule_obj in pack.rule_map.entries:
            rule = rule_obj()
            entry = ("rule", rule_id, rule)
            self.rule_packs[rule_id] = pack.name
            self._add(rule_id, entry)
            for piece in rule_id.split("_"):
                self._add(piece, entry)
            self._add_vocabulary(P.RulePremises(rule)(), entry)
            self._add_vocabulary(P.RuleReplacement(rule)(), entry)
        phi = getattr(pack, "phi", M.EmptyList)
        if M.IdentityCompare(phi, M.EmptyList)() is M.false_value:
            self._add_vocabulary(phi, ("phi", pack.name, phi))
        self._add(pack.name, ("pack", pack.name, M.EmptyList))
        for piece in pack.name.replace("-", "_").split("_"):
            self._add(piece, ("pack", pack.name, M.EmptyList))

    def add_definitions(self, defs_chain):
        for d in to_list(defs_chain):
            concept = M.Head(M.Tail(d)())()
            text = _char_text(concept)
            if text is not None:
                self._add(text, ("definition", text, d))

    def add_ledger(self, ledger, registry):
        if M.IdentityCompare(ledger, M.EmptyList)() is M.truth_value:
            return
        for entry in to_list(PL.PromotionLedgerProofSchemata(ledger)()) + to_list(PL.PromotionLedgerSearchPolicies(ledger)()):
            cid = PL.LedgerEntryId(entry)()
            text = _char_text(cid)
            name = text if text is not None else render_term(cid, registry)
            self._add(name, ("ledger", name, entry))
            self._add_vocabulary(PL.LedgerEntryCandidate(entry)(), ("ledger", name, entry))

    def lookup(self, word):
        return list(self.entries.get(normalise_word(word), []))


# ---------------------------------------------------------------------------
# the tutor session
# ---------------------------------------------------------------------------

class TutorAnswer:
    """Host record of one answer: `kind` routes the REPL, `record` is the
    machine term the answer was computed from, `text` is what the user sees."""

    def __init__(self, kind, record, text):
        self.kind = kind
        self.record = record
        self.text = text

    def __str__(self):
        return self.text


QUESTION_CLASSES = (
    ("concept", "what is X / define X / what do you know about X"),
    ("claim", "is it true that ... / claim: if ... then ... / for every n, ..."),
    ("focus", "let's work on ... / focus: <claim or goal>"),
    ("next", "next / hint / what next"),
    ("assert", "<a condition> (while a focus is open: 'b is odd')"),
    ("check", "check / prove it / verify"),
    ("why", "why / explain"),
    ("ledger", "show candidates / why is claim N not promoted / ledger"),
)


class Tutor:
    def __init__(self, runtime, packs=(), sweep_bound=12, max_depth=4):
        self.runtime = runtime
        self.graph = runtime.graph
        self.registry = M.FromContextGetConstructors(self.graph)()
        self.sweep_bound = sweep_bound
        self.max_depth = max_depth
        self.packs = []
        self.index = ConceptIndex()
        self.definitions = SB.BuildStandardDefinitions(self.registry)()
        self.index.add_definitions(self.definitions)
        for pack in packs:
            self.add_pack(pack)
        for pack in getattr(runtime, "loaded_packs", ()) or ():
            self.add_pack(pack)
        self.grammar = ClaimGrammar(self.nat, self.nat_value)
        self.focus = M.EmptyList     # machine Pair state: goal, known, question, rule, offered, asked
        self.focus_claim = M.EmptyList
        self.focus_assertions = M.EmptyList
        self.focus_definitions = M.EmptyList
        self.claims = M.EmptyList    # newest-first Pair chain of machine claim records
        self.claim_count = M.Zero
        self.turns = M.EmptyList     # newest-first Pair chain of dialogue turn records
        self.transcript = M.EmptyList
        self._two = None

    # -- machine plumbing -------------------------------------------------------

    def nat(self, n):
        res = M.NatFromRep(M.GMPRep(int(n)), self.registry)()
        self.registry = M.Head(M.Tail(res)())()
        return M.Head(res)()

    def nat_value(self, node):
        return _nat_value(node, self.registry)

    def two(self):
        if self._two is None:
            self._two = self.nat(2)
        return self._two

    def add_pack(self, pack):
        if any(p is pack for p in self.packs):
            return
        self.packs.append(pack)
        self.index.add_pack(pack)

    def rules(self):
        """Raw theorem rules (fact-list replacements, the shape
        KnowledgeRewriteSuccessors rewrites) of every loaded pack, in pack
        order, then any others the graph holds."""
        seen = []
        for pack in self.packs:
            for _rid, rule_obj in pack.rule_map.entries:
                rule = rule_obj()
                if P.ReplacementIsFactList(rule)() is M.truth_value:
                    seen.append(rule)
        for rule in to_list(self.runtime.flat_rules()):
            if P.ReplacementIsFactList(rule)() is M.truth_value and not any(rule is s for s in seen):
                seen.append(rule)
        return chain(seen)

    def rule_id_of(self, rule):
        for pack in self.packs:
            for rid, rule_obj in pack.rule_map.entries:
                if rule_obj() is rule:
                    return rid
        return "(unnamed rule)"

    def pack_of_rule(self, rule):
        for pack in self.packs:
            for _rid, rule_obj in pack.rule_map.entries:
                if rule_obj() is rule:
                    return pack.name
        return "(graph)"

    def _record_turn(self, text, answer):
        token = SB.SurfaceToken(M.Char(text))()
        tokens = M.Pair(token, M.EmptyList)
        turn = M.Pair(L.DialogueTurnLabel, M.Pair(tokens, M.Pair(answer.record, M.EmptyList)))
        self.turns = M.Pair(turn, self.turns)
        self.transcript = M.Pair(turn, self.transcript)
        return answer

    # -- routing (host I/O) ------------------------------------------------------

    def ask(self, text):
        words = tokenize(text)
        if not words:
            return self._record_turn(text, self._fallthrough("empty line"))
        joined = " ".join(words)

        if joined in ("next", "hint", "what next", "what is next", "go on", "continue"):
            return self._record_turn(text, self.next_question())
        for prefix in ("what is", "what are", "define", "what do you know about", "what does the machine know about", "explain the concept", "tell me about"):
            if joined.startswith(prefix + " "):
                rest = words[len(prefix.split()):]
                while rest and rest[0] in ("a", "an", "the"):
                    rest = rest[1:]
                if rest and rest[-1] in ("mean", "means"):
                    rest = rest[:-1]
                if rest:
                    return self._record_turn(text, self.explain_concept("".join(rest) if len(rest) > 1 else rest[0], rest))
        if joined in ("why", "explain", "why that"):
            return self._record_turn(text, self.explain_last())
        if joined in ("check", "verify", "prove it", "check it", "judge"):
            return self._record_turn(text, self.check_focus())
        if joined in ("show candidates", "ledger", "show ledger", "candidates", "show proposals"):
            return self._record_turn(text, self.ledger_report())
        if joined.startswith("why is claim") or joined.startswith("why isn't claim") or joined.startswith("why is not claim") or joined.startswith("status of claim"):
            digits = [w for w in words if w.isdigit()]
            if digits:
                return self._record_turn(text, self.explain_promotion(int(digits[0])))
        for prefix in ("let's work on", "lets work on", "focus on", "focus", "work on", "let us work on"):
            if joined.startswith(prefix + " ") or joined.startswith(prefix + ":"):
                rest = words[len(prefix.split()):]
                if rest and rest[0] == ":":
                    rest = rest[1:]
                return self._record_turn(text, self.set_focus(rest))
        # a bare condition while a focus is open is an assertion
        if M.IdentityCompare(self.focus, M.EmptyList)() is M.false_value:
            cond = self._parse_condition_in_focus(words)
            if cond is not None:
                return self._record_turn(text, self.assert_fact(cond))
        # a bare condition without a focus is a claim about all naturals
        claim = self.grammar.parse_claim(words)
        if claim is not None:
            return self._record_turn(text, self.judge_claim(words))
        return self._record_turn(text, self._fallthrough("no handled question class matches"))

    def _fallthrough(self, reason):
        record = M.Pair(L.DialogueFallthroughLabel, M.Pair(M.Char(reason), M.EmptyList))
        classes = "; ".join(k + ": " + d for k, d in QUESTION_CLASSES)
        return TutorAnswer("fallthrough", record, "[tutor] I can't route that (" + reason + "). Handled: " + classes + ".")

    # -- concepts ------------------------------------------------------------

    def explain_concept(self, word, words=None):
        candidates = [word]
        if words and len(words) > 1:
            candidates.append(" ".join(words))
            candidates.extend(words)
        # the ledger may have grown since the index was built
        self.index.add_ledger(self.graph.promotion_ledger, self.registry)
        entries = []
        matched = None
        for cand in candidates:
            found = self.index.lookup(cand)
            if found:
                entries = found
                matched = cand
                break
        # the bridge's own definition query (QueryConceptDefinition) runs as well
        def_res = SB.QueryConceptDefinition(M.Char(normalise_word(word)), self.definitions)()
        def_text = None
        if M.IdentityCompare(M.Head(def_res)(), L.SurfaceParseSuccessLabel)() is M.truth_value:
            def_node = M.Head(M.Tail(def_res)())()
            def_text = _char_text(SB.RenderConceptExplanation(def_node)())
        if not entries and def_text is None:
            record = M.Pair(L.ConceptNotRepresentedLabel, M.Pair(M.Char(word), M.EmptyList))
            text = ("[tutor] '" + word + "' is not represented in the machine: no loaded rule, pack goal, "
                    "definition record or ledger candidate mentions it (packs loaded: "
                    + (", ".join(p.name for p in self.packs) or "none") + ").")
            return TutorAnswer("not-represented", record, text)
        lines = "[tutor] what the machine holds about '" + word + "':"
        if def_text is not None:
            lines = lines + "\n  definition record: " + def_text
        lines = lines + "\n  matching entries are present in the loaded concept index."
        record = M.Pair(L.ConceptReportLabel, M.Pair(M.Char(word), M.EmptyList))
        return TutorAnswer("concept", record, lines)

    # -- claims --------------------------------------------------------------

    def parse_claim(self, words):
        return self.grammar.parse_claim(words)

    def claim_text(self, claim):
        return self.grammar.render_claim(claim, self.registry)

    def judge(self, claim):
        bound = self.sweep_bound
        n_vars = len(to_list(claim_variables(claim)))
        while n_vars >= 3 and bound ** n_vars > 2000 and bound > 3:
            bound -= 1
        verdict = JudgeClaim(claim, self.rules(), self.runtime.flat_rules(), self.nat(bound), self.nat(self.max_depth), self.two(), self.registry)()
        tag = M.Head(verdict)()
        payload = M.Tail(verdict)()
        if M.IdentityCompare(tag, L.ClaimVerifiedLabel)() is M.truth_value:
            payload_tail = M.Tail(payload)()
            payload_tail = M.Tail(payload_tail)()
            payload_tail = M.Tail(payload_tail)()
            payload_tail = M.Tail(payload_tail)()
            self.registry = M.Head(payload_tail)()
        else:
            if M.IdentityCompare(tag, L.ClaimRefutedLabel)() is M.truth_value:
                self.registry = M.Head(M.Tail(payload)())()
            else:
                payload_tail = M.Tail(payload)()
                payload_tail = M.Tail(payload_tail)()
                self.registry = M.Head(payload_tail)()
        return verdict, bound

    def judge_claim(self, words):
        claim = self.grammar.parse_claim(words)
        if claim is None:
            return self._fallthrough("I can read claims about naturals built from + and *, with even/odd/divides/coprime; this one did not parse")
        verdict, bound = self.judge(claim)
        count_res = AR.Add(self.claim_count, M.one, self.registry)()
        self.claim_count = M.Head(count_res)()
        self.registry = M.Head(M.Tail(count_res)())()
        bound_nat = self.nat(bound)
        claim_record = M.Pair(
            self.claim_count,
            M.Pair(
                M.Char(self.claim_text(claim)),
                M.Pair(claim, M.Pair(verdict, M.Pair(bound_nat, M.EmptyList))),
            ),
        )
        self.claims = M.Pair(claim_record, self.claims)
        index = _nat_value(self.claim_count, self.registry)
        return self._render_verdict(index, claim, verdict, bound)

    def _render_verdict(self, index, claim, verdict, bound):
        tag = M.Head(verdict)()
        payload = M.Tail(verdict)()
        head = "[tutor] claim " + str(index) + ": " + self.claim_text(claim)
        if M.IdentityCompare(tag, L.ClaimVerifiedLabel)() is M.truth_value:
            derivation = M.Head(payload)()
            steps_res = PG.ChainLength(
                P.DerivationSteps(derivation, self.registry)(), self.registry
            )()
            self.registry = M.Head(M.Tail(steps_res)())()
            step_count = _nat_value(M.Head(steps_res)(), self.registry)
            lines = head + "\n  VERIFIED: a " + str(step_count) + "-step derivation from the hypotheses to the conclusion passed Checker B (DerivationVerifiedLabel)."
            return TutorAnswer("claim-verified", verdict, lines)
        ground = M.IdentityCompare(claim_variables(claim), M.EmptyList)() is M.truth_value
        if M.IdentityCompare(tag, L.ClaimRefutedLabel)() is M.truth_value:
            assignment = M.Head(payload)()
            if ground:
                return TutorAnswer("claim-refuted", verdict, head + "\n  REFUTED: the claim has no variables and the machine's arithmetic evaluates it to false.")
            return TutorAnswer("claim-refuted", verdict, head + "\n  REFUTED by counterexample " + self._render_assignment(assignment, claim) + " (found by sweeping the naturals below " + str(bound) + ").")
        search_outcome = M.Head(payload)()
        sweep_outcome = M.Head(M.Tail(payload)())()
        if M.IdentityCompare(search_outcome, M.EmptyList)() is M.truth_value:
            s_text = "no derivation from the loaded rules within depth " + str(self.max_depth)
        else:
            s_text = "a candidate derivation was found but Checker B rejected it: " + render_term(M.Head(search_outcome)(), self.registry)
        if M.IdentityCompare(M.Head(sweep_outcome)(), L.SweepReportLabel)() is M.truth_value:
            n_checked = _nat_value(M.Head(M.Tail(sweep_outcome)())(), self.registry)
            n_hyps = _nat_value(M.Head(M.Tail(M.Tail(sweep_outcome)())())(), self.registry)
            if ground:
                w_text = "the claim has no variables and the machine's arithmetic evaluates it to true, which is computation, not a derivation"
            else:
                w_text = ("no counterexample below " + str(bound) + " (" + str(n_checked) + " assignments checked, the hypotheses held on "
                          + str(n_hyps) + " of them and the conclusion held on every one of those)")
        else:
            w_text = "the sweep could not evaluate " + render_term(M.Head(M.Tail(sweep_outcome)())(), self.registry) + " -- no machine evaluator for that predicate"
        text = head + "\n  UNDECIDED: " + s_text + "; " + w_text + ". Bounded evidence is not a proof."
        return TutorAnswer("claim-undecided", verdict, text)

    def _render_assignment(self, assignment, claim):
        parts = []
        for entry in to_list(assignment):
            parts.append(render_term(M.Head(entry)(), self.registry) + " = " + render_term(M.Tail(entry)(), self.registry))
        # also show the composite terms' values
        for d in to_list(claim_definitions(claim)):
            out = fact_args(d)[2]
            val = EvaluateTerm(out, assignment, claim_definitions(claim), self.registry)()
            self.registry = M.Head(M.Tail(val)())()
            if M.IdentityCompare(M.Head(val)(), M.EmptyList)() is M.false_value:
                parts.append(render_term(out, self.registry) + " = " + render_term(M.Head(val)(), self.registry))
        return "{" + ", ".join(parts) + "}"

    # -- focus and Socratic progression ----------------------------------------

    def set_focus(self, words):
        claim = self.grammar.parse_claim(words)
        if claim is None:
            return self._fallthrough("the focus must be a claim or a goal condition")
        goal = claim_conclusion(claim)
        known = claim_start_facts(claim)
        self.focus_claim = claim
        self.focus_assertions = M.EmptyList
        self.focus_definitions = M.EmptyList
        self.focus = M.Pair(
            goal,
            M.Pair(
                known,
                M.Pair(
                    M.EmptyList,
                    M.Pair(M.EmptyList, M.Pair(M.false_value, M.Pair(M.EmptyList, M.EmptyList))),
                ),
            ),
        )
        hypotheses = claim_hypotheses(claim)
        line = "[tutor] focus: goal " + render_term(goal, self.registry)
        if M.IdentityCompare(hypotheses, M.EmptyList)() is M.truth_value:
            line = line + " with no hypotheses yet."
        else:
            line = line + " with hypotheses: " + render_fact_list(hypotheses, self.registry) + "."
        first = self.next_question()
        return TutorAnswer("focus", first.record, line + "\n" + first.text)

    def intern(self, term):
        """Rebuild a term so that every Char is the session's one atom for that
        symbol.  The kernel's join discipline (TermEqual inside MergeBindings)
        identifies data atoms by identity, exactly as packs.py interns the
        Chars of a pack; a fresh Char with the same symbol would never join."""
        if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
            return term
        if M.IsPair(term)() is M.truth_value:
            if _is_var(term):
                return term
            return M.Pair(self.intern(M.Head(term)()), self.intern(M.Tail(term)()))
        text = _char_text(term)
        if text is not None:
            return self.grammar.char(text)
        return term

    def set_focus_goal(self, goal_fact, known_facts=M.EmptyList):
        """Open a focus on any machine fact (not only the claim grammar's):
        the Socratic machinery is generic over the loaded rules."""
        goal_fact = self.intern(goal_fact)
        known_facts = self.intern(known_facts)
        self.focus_claim = M.Pair(
            L.DialogueClaimLabel,
            M.Pair(
                M.EmptyList,
                M.Pair(M.EmptyList, M.Pair(known_facts, M.Pair(goal_fact, M.EmptyList))),
            ),
        )
        self.focus_assertions = M.EmptyList
        self.focus_definitions = M.EmptyList
        self.focus = M.Pair(
            goal_fact,
            M.Pair(
                known_facts,
                M.Pair(
                    M.EmptyList,
                    M.Pair(M.EmptyList, M.Pair(M.false_value, M.Pair(M.EmptyList, M.EmptyList))),
                ),
            ),
        )
        return self.next_question()

    def parse_generic_fact(self, words):
        """'name ( p , m )' -> Pair(NameLabel, [p, m]) when NameLabel is a label
        the loaded rules use; arguments are variable Chars or naturals.
        Returns None otherwise."""
        if len(words) < 3 or words[1] != "(" or words[-1] != ")":
            return None
        label = self.index.labels_by_name.get(words[0].replace("_", ""))
        if label is None:
            return None
        args = []
        for w in words[2:-1]:
            if w == ",":
                continue
            if w.isdigit():
                args.append(self.nat(int(w)))
            elif w.replace("_", "").isalnum():
                args.append(self.grammar.char(w))
            else:
                return None
        return fact(label, *args)

    def _parse_condition_in_focus(self, words):
        self.grammar.reset()
        if words and words[0] in ("assume", "suppose", "given", "assert"):
            words = words[1:]
            if words and words[0] == "that":
                words = words[1:]
        cond = self.grammar.parse_condition(words)
        if cond is None:
            cond = self.parse_generic_fact(words)
        if cond is None:
            return None
        # new composite terms introduced by the assertion join the known facts
        focus_tail = M.Tail(self.focus)()
        known = M.Head(focus_tail)()
        after_known = M.Tail(focus_tail)()
        new_definitions = self.grammar.definitions
        known = PG.ChainMergeUnique(known, new_definitions)()
        self.focus_definitions = PG.ChainConcat(
            new_definitions, self.focus_definitions
        )()
        self.focus = M.Pair(M.Head(self.focus)(), M.Pair(known, after_known))
        return cond

    def assert_fact(self, cond):
        focus_tail = M.Tail(self.focus)()
        known = M.Head(focus_tail)()
        after_known = M.Tail(focus_tail)()
        if chain_has(known, cond) is M.truth_value:
            return TutorAnswer("assert", cond, "[tutor] " + render_term(cond, self.registry) + " is already among your facts.\n" + self.next_question().text)
        known = M.Pair(cond, known)
        self.focus_assertions = M.Pair(cond, self.focus_assertions)
        self.focus = M.Pair(M.Head(self.focus)(), M.Pair(known, after_known))
        nxt = self.next_question()
        return TutorAnswer("assert", nxt.record, "[tutor] recorded " + render_term(cond, self.registry) + ".\n" + nxt.text)

    def obligations(self):
        goal = M.Head(self.focus)()
        known = M.Head(M.Tail(self.focus)())()
        return BackwardObligations(goal, known, self.rules())()

    def next_question(self):
        if M.IdentityCompare(self.focus, M.EmptyList)() is M.truth_value:
            return self._fallthrough("no focus is open; say \"let's work on <claim>\" first")
        goal = M.Head(self.focus)()
        focus_tail = M.Tail(self.focus)()
        known = M.Head(focus_tail)()
        after_known = M.Tail(focus_tail)()
        last_question = M.Head(after_known)()
        after_question = M.Tail(after_known)()
        current_rule = M.Head(after_question)()
        after_rule = M.Tail(after_question)()
        offered = M.Head(after_rule)()
        asked = M.Head(M.Tail(after_rule)())()
        if chain_has(known, goal) is M.truth_value:
            q = make_question(L.Rung4DerivationLabel, M.EmptyList, goal)
            self.focus = M.Pair(goal, M.Pair(known, M.Pair(q, after_question)))
            return TutorAnswer("question", q, "[tutor] (rung 4, derivation) " + render_term(goal, self.registry) + " is already among your facts; say 'check' and Checker B will confirm the (empty) derivation.")
        entries = self.obligations()
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            q = make_question(L.Rung6NegativeLabel, M.EmptyList, goal)
            self.focus = M.Pair(goal, M.Pair(known, M.Pair(q, after_question)))
            return TutorAnswer("question", q, "[tutor] (rung 6, negative) No loaded rule concludes a fact shaped like " + render_term(goal, self.registry)
                               + ". Before looking for a proof: could the claim be false? Say 'check' and I will sweep the naturals below " + str(self.sweep_bound) + " for a counterexample.")
        best = M.Head(entries)()
        rule = M.Head(best)()
        satisfied = M.Head(M.Tail(best)())()
        open_ = M.Head(M.Tail(M.Tail(best)())())()
        rid = self.rule_id_of(rule)
        if M.IdentityCompare(open_, M.EmptyList)() is M.truth_value:
            q = make_question(L.Rung4DerivationLabel, rule, goal)
            self.focus = M.Pair(goal, M.Pair(known, M.Pair(q, M.Pair(rule, after_rule))))
            return TutorAnswer("question", q, "[tutor] (rung 4, derivation) Every premise of " + rid + " is in hand: " + render_fact_list(satisfied, self.registry)
                               + ". Applying it gives " + render_term(goal, self.registry) + ". Say 'check' and I will build the derivation and have Checker B verify it.")
        same_rule = M.Compare(current_rule, rule)()
        if same_rule is M.false_value:
            current_rule = rule
        obligation = M.Head(open_)()
        repeat = chain_has(asked, obligation)
        q = make_question(L.Rung1RetrievalLabel, rule, obligation)
        asked = M.Pair(obligation, asked)
        self.focus = M.Pair(
            goal,
            M.Pair(
                known,
                M.Pair(q, M.Pair(current_rule, M.Pair(offered, M.Pair(asked, M.EmptyList)))),
            ),
        )
        if self.grammar.covers(obligation):
            sentence = "'" + self.grammar.render_condition(obligation, self.registry) + "'"
        else:
            sentence = "'assume " + render_term(obligation, self.registry) + "'"
        prompt = "Say " + sentence + " to take it as given, 'why' to see the rule, or 'next' for another premise."
        still = " (still open)"
        if repeat is M.false_value:
            still = ""
        return TutorAnswer("question", q, "[tutor] (rung 1, retrieval) To use " + rid + " you still need " + render_term(obligation, self.registry) + still + ". " + prompt)

    def explain_last(self):
        if M.IdentityCompare(self.focus, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(self.claims, M.EmptyList)() is M.false_value:
                last = M.Head(self.claims)()
                index = _nat_value(M.Head(last)(), self.registry)
                fields = M.Tail(last)()
                fields = M.Tail(fields)()
                claim = M.Head(fields)()
                fields = M.Tail(fields)()
                verdict = M.Head(fields)()
                fields = M.Tail(fields)()
                bound_nat = M.Head(fields)()
                bound = _nat_value(bound_nat, self.registry)
                return self._render_verdict(index, claim, verdict, bound)
            return self._fallthrough("nothing to explain yet")
        focus_tail = M.Tail(self.focus)()
        after_known = M.Tail(focus_tail)()
        q = M.Head(after_known)()
        if M.IdentityCompare(q, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(self.claims, M.EmptyList)() is M.false_value:
                last = M.Head(self.claims)()
                index = _nat_value(M.Head(last)(), self.registry)
                fields = M.Tail(last)()
                fields = M.Tail(fields)()
                claim = M.Head(fields)()
                fields = M.Tail(fields)()
                verdict = M.Head(fields)()
                fields = M.Tail(fields)()
                bound = _nat_value(M.Head(fields)(), self.registry)
                return self._render_verdict(index, claim, verdict, bound)
            return self._fallthrough("nothing to explain yet")
        rule = question_rule(q)
        if M.IdentityCompare(rule, M.EmptyList)() is M.truth_value:
            return TutorAnswer("why", q, "[tutor] the question came from the goal shape " + render_term(question_focus(q), self.registry) + " and the loaded rules: " + ", ".join(p.name for p in self.packs) + ".")
        rid = self.rule_id_of(rule)
        line = "[tutor] " + rid + " [" + self.pack_of_rule(rule) + "]: " + render_rule(rule, self.registry)
        return TutorAnswer("why", q, line)

    def check_focus(self):
        if M.IdentityCompare(self.focus, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(self.claims, M.EmptyList)() is M.false_value:
                last = M.Head(self.claims)()
                index = _nat_value(M.Head(last)(), self.registry)
                fields = M.Tail(last)()
                fields = M.Tail(fields)()
                claim = M.Head(fields)()
                fields = M.Tail(fields)()
                verdict = M.Head(fields)()
                fields = M.Tail(fields)()
                bound_nat = M.Head(fields)()
                bound = _nat_value(bound_nat, self.registry)
                return self._render_verdict(index, claim, verdict, bound)
            return self._fallthrough("nothing to check; state a claim or open a focus")
        claim = self.focus_claim
        original_definitions = claim_definitions(claim)
        definitions = PG.ChainConcat(
            original_definitions, self.focus_definitions
        )()
        original_hypotheses = claim_hypotheses(claim)
        hypotheses = PG.ChainConcat(
            original_hypotheses, self.focus_assertions
        )()
        variables = claim_variables(claim)
        goal = M.Head(self.focus)()
        full = M.Pair(
            L.DialogueClaimLabel,
            M.Pair(
                variables,
                M.Pair(definitions, M.Pair(hypotheses, M.Pair(goal, M.EmptyList))),
            ),
        )
        verdict, bound = self.judge(full)
        count_res = AR.Add(self.claim_count, M.one, self.registry)()
        self.claim_count = M.Head(count_res)()
        self.registry = M.Head(M.Tail(count_res)())()
        bound_nat = self.nat(bound)
        claim_record = M.Pair(
            self.claim_count,
            M.Pair(
                M.Char(self.claim_text(full)),
                M.Pair(full, M.Pair(verdict, M.Pair(bound_nat, M.EmptyList))),
            ),
        )
        self.claims = M.Pair(claim_record, self.claims)
        index = _nat_value(self.claim_count, self.registry)
        return self._render_verdict(index, full, verdict, bound)

    # -- ledger transparency ---------------------------------------------------

    def ledger_report(self, stage=M.EmptyList, remaining=M.EmptyList, records=M.EmptyList, report=M.EmptyList):
        if M.IdentityCompare(stage, M.EmptyList)() is M.truth_value:
            report = "[tutor] proposals and promotions:"
            ledger = self.graph.promotion_ledger
            if M.IdentityCompare(ledger, M.EmptyList)() is M.truth_value:
                report = report + "\n  promotion ledger: empty (nothing has been promoted in this runtime)"
                return self.ledger_report(M.Char("claims"), self.claims, records, report)
            proof_entries = PL.PromotionLedgerProofSchemata(ledger)()
            search_entries = PL.PromotionLedgerSearchPolicies(ledger)()
            remaining = PG.ChainConcat(proof_entries, search_entries)()
            report = report + "\n  promotion ledger version " + render_term(
                PL.PromotionLedgerVersion(ledger)(), self.registry
            )
            return self.ledger_report(M.Char("entries"), remaining, records, report)
        if M.Compare(stage, M.Char("entries"))() is M.truth_value:
            if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
                return self.ledger_report(M.Char("claims"), self.claims, records, report)
            entry = M.Head(remaining)()
            receipt_text = "present"
            if M.IdentityCompare(PL.LedgerEntryReceipt(entry)(), M.EmptyList)() is M.truth_value:
                receipt_text = "absent"
            report = (
                report
                + "\n    "
                + render_term(PL.LedgerEntryId(entry)(), self.registry)
                + ": "
                + render_term(PL.LedgerEntryStatus(entry)(), self.registry)
                + ", receipt "
                + receipt_text
            )
            records = M.Pair(entry, records)
            return self.ledger_report(M.Char("entries"), M.Tail(remaining)(), records, report)
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            record = M.Pair(
                L.ConceptReportLabel,
                M.Pair(M.Char("ledger"), M.Pair(records, M.EmptyList)),
            )
            return TutorAnswer("ledger", record, report)
        claim_record = M.Head(remaining)()
        saved_index = M.Head(claim_record)()
        fields = M.Tail(claim_record)()
        claim_text = M.Head(fields)()
        fields = M.Tail(fields)()
        claim = M.Head(fields)()
        fields = M.Tail(fields)()
        verdict = M.Head(fields)()
        report = (
            report
            + "\n  claim "
            + str(_nat_value(saved_index, self.registry))
            + " ("
            + claim_text()
            + "): "
            + self._promotion_status(verdict, claim)
        )
        records = M.Pair(verdict, records)
        return self.ledger_report(M.Char("claims"), M.Tail(remaining)(), records, report)

    def _promotion_status(self, verdict, claim):
        tag = M.Head(verdict)()
        if M.IdentityCompare(tag, L.ClaimVerifiedLabel)() is M.truth_value:
            return "has a Checker-B receipt (DerivationVerifiedLabel); promotable -- the ledger's ablation and holdout gates have not been run in this session"
        if M.IdentityCompare(tag, L.ClaimRefutedLabel)() is M.truth_value:
            return "cannot be promoted: refuted by " + self._render_assignment(M.Head(M.Tail(verdict)())(), claim)
        return "lacks a receipt: no Checker-B-verified derivation; " + self._what_would_earn_one(claim)

    def _what_would_earn_one(self, claim):
        entries = to_list(BackwardObligations(claim_conclusion(claim), claim_start_facts(claim), self.rules())())
        if not entries:
            return "what would earn one: a loaded rule whose replacement is shaped like " + render_term(claim_conclusion(claim), self.registry) + " (none is)"
        entries.sort(key=lambda e: len(to_list(M.Head(M.Tail(M.Tail(e)())())())))
        best = entries[0]
        open_ = to_list(M.Head(M.Tail(M.Tail(best)())())())
        return ("what would earn one: the premises " + (", ".join(render_term(f, self.registry) for f in open_) or "(none)")
                + " of " + self.rule_id_of(M.Head(best)()) + ", derived or assumed")

    def explain_promotion(self, index, remaining=M.EmptyList, started=M.false_value):
        wanted = index
        cursor = remaining
        if started is M.false_value:
            count_res = M.NatFromRep(M.GMPRep(int(index)), self.registry)()
            wanted = M.Head(count_res)()
            self.registry = M.Head(M.Tail(count_res)())()
            cursor = self.claims
        if M.IdentityCompare(cursor, M.EmptyList)() is M.truth_value:
            return self._fallthrough("there is no claim " + str(index) + " in this session")
        claim_record = M.Head(cursor)()
        saved_index = M.Head(claim_record)()
        if M.Compare(saved_index, wanted)() is M.truth_value:
            fields = M.Tail(claim_record)()
            claim_text = M.Head(fields)()
            claim_body = M.Tail(fields)()
            claim = M.Head(claim_body)()
            verdict_body = M.Tail(claim_body)()
            verdict = M.Head(verdict_body)()
            index_text = str(_nat_value(saved_index, self.registry))
            return TutorAnswer(
                "ledger",
                verdict,
                "[tutor] claim "
                + index_text
                + " ("
                + claim_text()
                + "): "
                + self._promotion_status(verdict, claim),
            )
        return self.explain_promotion(wanted, M.Tail(cursor)(), M.truth_value)


# ---------------------------------------------------------------------------
# small helpers used by the tutor
# ---------------------------------------------------------------------------

def _is_definition(f):
    label = fact_label(f)
    return M.OrAtom(
        M.IdentityCompare(label, L.NatSumLabel)(),
        M.IdentityCompare(label, L.NatProductLabel)(),
    )()


def term_vocabulary_vars(term):
    """Names of the pattern variables left in a term (for question prompts)."""
    acc = set()

    def walk(t):
        if M.IdentityCompare(t, M.EmptyList)() is M.truth_value:
            return
        if M.IsPair(t)() is M.truth_value:
            if _is_var(t):
                acc.add(_var_text(t))
                return
            walk(M.Head(t)())
            walk(M.Tail(t)())

    walk(term)
    return acc


def term_vocabulary_vars_chars(term):
    """Char symbols that look like variables (single short identifiers)."""
    acc = set()
    for name in term_vocabulary(term, set()):
        if not name.endswith("Label") and name.isalpha() and len(name) <= 3:
            acc.add(name)
    return acc
