"""Researcher-v0 G1 — inert structural token-count domain.

Scope of this module (G1 only):

* structural Peano numerals over the repository's own Peano constructor labels
  (`labels.ZeroLabel`, `labels.SuccLabel`); **no Python integer is ever a
  semantic state**. Integers appear only in reporting helpers;
* a token-count world whose state is a two-fact `proof.Knowledge` term:
  `Tokens(k)` where ``k`` is a structural numeral counting **pairs** of
  tokens, plus `Parity(d)` with ``d`` in `{Even, Odd}`. The total number of
  tokens is ``d + 2k``, so the two facts are a faithful representation of the
  count and every rule below is a pure structural pattern;
* rulesets `R_even = {Add2, Remove2, Swap}` and
  `R_plus = R_even + {Add1Even, Add1Odd}`. Each rule is a real
  `proof.MultiRule` term whose premises carry the whole legality precondition:
  `Remove2` only matches states holding at least one pair, i.e. at least two
  tokens, so an illegal application is an inapplicable move and not an error;
* an inert transition applier derived from the rule *terms* through
  `machine.Match` / `machine.Instantiate`, so the reachable-state relation has
  a single source of truth: the rule content the fingerprint covers.

The carried `Parity` fact is derived, and it is derived *truthfully*: every
state built here satisfies ``parity = count mod 2`` (`StateIsConsistent`), and
every applied rule preserves that (checked in the domain test). It exists for
one reason — an observer can read a single value that `Add2`, `Remove2` and
`Swap` leave `Compare`-equal while `Add1` changes it. That is the shape the
later checker needs, because `invariance.Preserves` compares pre/post readings
by exact `Compare`-equality (approved inspection §3a).

What this module deliberately does NOT do (the A2.1 boundary):

* it issues no `CHECKED_UNREACHABLE` result and builds no certificate. The
  only move statuses are `APPLIED` and `MISS`. `MISS` means "this rule is
  inapplicable at this state": it is neither a crash nor a refutation, and
  never an unreachability result;
* it contains no miner, no invariant prover, no search, no journal writer;
* it imports no live path: `graph`, `search`, Programme C and `core` are
  untouched, and nothing imports this package.

`researcher_v0/g1_replay_procedure.md` states the operational replay the later
checker must perform before any unreachability claim exists.
"""

from __future__ import annotations

from .. import machine as M
from .. import proof as P
from ..labels import SuccLabel, ZeroLabel
from .chains import ChainAppend, ChainJoin, ChainLength, IsEmptyTerm
from .ruleset_digest import RuleContentDigest, RulesetVersion

DOMAIN_VERSION_TEXT = "token-count-structural-peano/1"


# --------------------------------------------------------------------------
# tags
# --------------------------------------------------------------------------
# Every tag is a `core.Char` atom, read through Compare: `constructors.Compare`
# equates constructor-less atoms with equal payloads, so a tag is a semantic
# constant of the domain and its payload is hashed by the fingerprint.


class TokensTag(M.Edge):
    def __init__(self):
        self.result = M.Char("Tokens")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class ParityTag(M.Edge):
    def __init__(self):
        self.result = M.Char("Parity")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class EvenTag(M.Edge):
    def __init__(self):
        self.result = M.Char("Even")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class OddTag(M.Edge):
    def __init__(self):
        self.result = M.Char("Odd")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RuleSpecTag(M.Edge):
    def __init__(self):
        self.result = M.Char("RuleSpec")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class AppliedTag(M.Edge):
    def __init__(self):
        self.result = M.Char("APPLIED")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class MissTag(M.Edge):
    def __init__(self):
        self.result = M.Char("MISS")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class NoMatchTag(M.Edge):
    def __init__(self):
        self.result = M.Char("no_match")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class VariableConflictTag(M.Edge):
    def __init__(self):
        self.result = M.Char("variable_conflict")
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class IsDomainMoveStatus(M.Edge):
    """Is this atom a move status of this domain (APPLIED or MISS)?

    The vocabulary has no third member: nothing here can report
    unreachability, refutation or exhaustion (A2.1).
    """

    def __init__(self, atom):
        if M.Compare(atom, AppliedTag()())() is M.truth_value:
            self.result = M.truth_value
        elif M.Compare(atom, MissTag()())() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(atom, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# structural Peano numerals
# --------------------------------------------------------------------------
# Zero = Pair(ZeroLabel, EmptyList); Succ(n) = Pair(SuccLabel, Pair(n, EmptyList)).
# A pair skeleton is used rather than a registry-backed atom because the
# applier, the matcher and the fingerprint all walk plain structure: the rule
# content is then its own single source of truth, and `Compare` decides
# numeral identity exactly (`Compare(Zero, Succ(Zero))` is false).


class PeanoZero(M.Edge):
    def __init__(self):
        self.result = M.Pair(ZeroLabel, M.EmptyList)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PeanoSucc(M.Edge):
    def __init__(self, numeral):
        self.result = M.Pair(SuccLabel, M.Pair(numeral, M.EmptyList))
        super().__init__(inputs=M.Pair(numeral, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PeanoFromInt(M.Edge):
    """The structural numeral for a reporting int >= 0 (construction only)."""

    def __init__(self, count):
        if count < 0:
            raise ValueError("token counts are non-negative")
        self.result = self._build(count, PeanoZero()())
        super().__init__(inputs=M.Pair(count, M.EmptyList), results=self.result)

    def _build(self, remaining, numeral):
        if remaining == 0:
            return numeral
        return self._build(remaining - 1, PeanoSucc(numeral)())

    def __call__(self):
        return self.result


class StructuralCount(M.Edge):
    """Number of Succ layers of a structural numeral (reporting int)."""

    def __init__(self, numeral):
        if M.IsPair(numeral)() is M.false_value:
            raise ValueError("not a structural Peano numeral")
        self.result = self._count(numeral, 0)
        super().__init__(inputs=M.Pair(numeral, M.EmptyList), results=self.result)

    def _count(self, numeral, so_far):
        if M.Compare(M.Head(numeral)(), ZeroLabel)() is M.truth_value:
            return so_far
        if M.Compare(M.Head(numeral)(), SuccLabel)() is M.false_value:
            raise ValueError("not a structural Peano numeral")
        inner = M.Tail(numeral)()
        if M.IsPair(inner)() is M.false_value:
            raise ValueError("not a structural Peano numeral")
        if M.IdentityCompare(M.Tail(inner)(), M.EmptyList)() is M.false_value:
            raise ValueError("not a structural Peano numeral")
        return self._count(M.Head(inner)(), so_far + 1)

    def __call__(self):
        return self.result


class IsStructuralNumeral(M.Edge):
    """Is this term a structural numeral: Zero, or Succ of one?"""

    def __init__(self, term):
        if M.IsPair(term)() is M.false_value:
            self.result = M.false_value
        elif M.Compare(M.Head(term)(), ZeroLabel)() is M.truth_value:
            if DecidableZeroShape(term)() is M.truth_value:
                self.result = M.truth_value
            else:
                self.result = M.false_value
        elif M.Compare(M.Head(term)(), SuccLabel)() is M.truth_value:
            if DecidableSuccShape(term)() is M.truth_value:
                self.result = IsStructuralNumeral(M.Head(M.Tail(term)())())()
            else:
                self.result = M.false_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DecidableZeroShape(M.Edge):
    """`Pair(ZeroLabel, EmptyList)` exactly."""

    def __init__(self, term):
        if M.IsPair(term)() is M.false_value:
            self.result = M.false_value
        elif IsEmptyTerm(M.Tail(term)())() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DecidableSuccShape(M.Edge):
    """`Pair(SuccLabel, Pair(inner, EmptyList))` exactly."""

    def __init__(self, term):
        if M.IsPair(term)() is M.false_value:
            self.result = M.false_value
        elif M.IsPair(M.Tail(term)())() is M.false_value:
            self.result = M.false_value
        elif IsEmptyTerm(M.Tail(M.Tail(term)())())() is M.false_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# facts and states
# --------------------------------------------------------------------------


class TokensFact(M.Edge):
    """Fact `Tokens(k)`: ``k`` structural pairs of tokens, so ``2k`` tokens."""

    def __init__(self, pairs):
        self.result = M.Pair(TokensTag()(), M.Pair(pairs, M.EmptyList))
        super().__init__(inputs=M.Pair(pairs, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ParityFact(M.Edge):
    """Fact `Parity(d)`: the unpaired token, Even (0) or Odd (1)."""

    def __init__(self, parity):
        self.result = M.Pair(ParityTag()(), M.Pair(parity, M.EmptyList))
        super().__init__(inputs=M.Pair(parity, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TokenState(M.Edge):
    """A state: `Knowledge([Tokens(k), Parity(d)])`."""

    def __init__(self, pairs, parity):
        facts = M.Pair(TokensFact(pairs)(), M.Pair(ParityFact(parity)(), M.EmptyList))
        self.result = P.Knowledge(facts)()
        super().__init__(
            inputs=M.Pair(pairs, M.Pair(parity, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class StateOfCount(M.Edge):
    """The consistent state whose total token count is the reporting int ``n``.

    The carried parity fact is derived here, once, from the count: ``d = n mod 2``
    and ``k = (n - d) / 2``. Every state this module builds is consistent.
    """

    def __init__(self, count):
        if count < 0:
            raise ValueError("token counts are non-negative")
        unpaired = count % 2
        pair_count = (count - unpaired) // 2
        parity = OddTag()() if unpaired == 1 else EvenTag()()
        self.result = TokenState(PeanoFromInt(pair_count)(), parity)()
        super().__init__(inputs=M.Pair(count, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FactsOfState(M.Edge):
    """The fact chain of a `Knowledge` state."""

    def __init__(self, state):
        self.result = P.KnowledgeFacts(state)()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FactArgument(M.Edge):
    """Argument of the first fact of `state` whose tag matches `tag`."""

    def __init__(self, state, tag):
        self.result = self._scan(FactsOfState(state)(), tag)
        super().__init__(
            inputs=M.Pair(state, M.Pair(tag, M.EmptyList)), results=self.result
        )

    def _scan(self, facts, tag):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            raise ValueError("state does not carry the requested fact")
        fact = M.Head(facts)()
        if M.Compare(M.Head(fact)(), tag)() is M.truth_value:
            return M.Head(M.Tail(fact)())()
        return self._scan(M.Tail(facts)(), tag)

    def __call__(self):
        return self.result


class TokensOfState(M.Edge):
    """The structural pair count carried by a state."""

    def __init__(self, state):
        self.result = FactArgument(state, TokensTag()())()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ParityOfState(M.Edge):
    """The parity value carried by a state."""

    def __init__(self, state):
        self.result = FactArgument(state, ParityTag()())()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ParityValue(M.Edge):
    """The carried parity as 0 or 1 (reporting only)."""

    def __init__(self, state):
        parity = ParityOfState(state)()
        if M.Compare(parity, EvenTag()())() is M.truth_value:
            self.result = 0
        elif M.Compare(parity, OddTag()())() is M.truth_value:
            self.result = 1
        else:
            raise ValueError("unknown parity value")
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CountOfState(M.Edge):
    """Total token count ``d + 2k`` (reporting only).

    The only place a state becomes an integer, and the integer is never put
    back into a term.
    """

    def __init__(self, state):
        self.result = ParityValue(state)() + 2 * StructuralCount(TokensOfState(state)())()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StateIsConsistent(M.Edge):
    """Does the carried parity fact agree with the structural pair count?"""

    def __init__(self, state):
        if ParityValue(state)() == CountOfState(state)() % 2:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# rules
# --------------------------------------------------------------------------
# A rule spec is an inert term with an explicit display slot:
#   Pair(RuleSpec, Pair(display, Pair(content, EmptyList)))
# `content` is the real `proof.MultiRule` that matching, the applier and the
# fingerprint all use. `display` is the only display-only part (A2.2): it is
# never reachable from `content`, which the partition test checks by identity.


class RuleVar(M.Edge):
    """A rule variable pattern. Sharing across a rule is by object identity,
    because `machine.FindBinding` compares variable atoms by identity."""

    def __init__(self, name):
        self.result = M.Pair(M.VarTag, M.Pair(M.Char(name), M.EmptyList))
        super().__init__(inputs=M.Pair(name, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleSpec(M.Edge):
    def __init__(self, display, content):
        self.result = M.Pair(
            RuleSpecTag()(), M.Pair(display, M.Pair(content, M.EmptyList))
        )
        super().__init__(
            inputs=M.Pair(display, M.Pair(content, M.EmptyList)), results=self.result
        )

    def __call__(self):
        return self.result


class RuleDisplay(M.Edge):
    def __init__(self, spec):
        self.result = M.Head(M.Tail(spec)())()
        super().__init__(inputs=M.Pair(spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleContent(M.Edge):
    def __init__(self, spec):
        self.result = M.Head(M.Tail(M.Tail(spec)())())()
        super().__init__(inputs=M.Pair(spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DisplayText(M.Edge):
    """Display text of an atom-wrapper Edge (reporting and evidence only).

    Never hashed: the fingerprint reads atoms, not wrappers. It exists so the
    report and the test runner can print a result without a string conversion
    at a call site.
    """

    def __init__(self, wrapper):
        self.result = M.Char(wrapper()())
        super().__init__(inputs=M.Pair(wrapper, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleChainOf(M.Edge):
    """The rule content of every spec in a chain, in order."""

    def __init__(self, specs):
        self.result = self._collect(specs, M.EmptyList)
        super().__init__(inputs=M.Pair(specs, M.EmptyList), results=self.result)

    def _collect(self, remaining, built):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return built
        return self._collect(
            M.Tail(remaining)(),
            ChainAppend(built, RuleContent(M.Head(remaining)())())(),
        )

    def __call__(self):
        return self.result


class Add2Rule(M.Edge):
    """`Tokens(k), Parity(p) -> Tokens(Succ(k)), Parity(p)` — two tokens."""

    def __init__(self):
        k = RuleVar("k")()
        p = RuleVar("p")()
        self.result = P.MultiRule(
            M.Pair(TokensFact(k)(), M.Pair(ParityFact(p)(), M.EmptyList)),
            M.Pair(
                TokensFact(PeanoSucc(k)())(), M.Pair(ParityFact(p)(), M.EmptyList)
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Remove2Rule(M.Edge):
    """`Tokens(Succ(k)), Parity(p) -> Tokens(k), Parity(p)` — two tokens.

    The `Succ` inside the premise is the legality precondition: a state with
    fewer than two tokens does not match, so an illegal `Remove2` is an
    inapplicable move rather than a crash or an unreachability result.
    """

    def __init__(self):
        k = RuleVar("k")()
        p = RuleVar("p")()
        self.result = P.MultiRule(
            M.Pair(
                TokensFact(PeanoSucc(k)())(), M.Pair(ParityFact(p)(), M.EmptyList)
            ),
            M.Pair(TokensFact(k)(), M.Pair(ParityFact(p)(), M.EmptyList)),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SwapRule(M.Edge):
    """`Tokens(k), Parity(p) -> Tokens(k), Parity(p)` — identity."""

    def __init__(self):
        k = RuleVar("k")()
        p = RuleVar("p")()
        facts = M.Pair(TokensFact(k)(), M.Pair(ParityFact(p)(), M.EmptyList))
        self.result = P.MultiRule(facts, facts)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Add1EvenRule(M.Edge):
    """`Tokens(k), Parity(Even) -> Tokens(k), Parity(Odd)` — one token.

    The even case of the Add1 perturbation: the pair count stays, the carried
    parity flips.
    """

    def __init__(self):
        k = RuleVar("k")()
        self.result = P.MultiRule(
            M.Pair(TokensFact(k)(), M.Pair(ParityFact(EvenTag()())(), M.EmptyList)),
            M.Pair(TokensFact(k)(), M.Pair(ParityFact(OddTag()())(), M.EmptyList)),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Add1OddRule(M.Edge):
    """`Tokens(k), Parity(Odd) -> Tokens(Succ(k)), Parity(Even)` — one token."""

    def __init__(self):
        k = RuleVar("k")()
        self.result = P.MultiRule(
            M.Pair(TokensFact(k)(), M.Pair(ParityFact(OddTag()())(), M.EmptyList)),
            M.Pair(
                TokensFact(PeanoSucc(k)())(), M.Pair(ParityFact(EvenTag()())(), M.EmptyList)
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class REvenSpecs(M.Edge):
    """R_even as a chain of rule specs, in canonical declaration order."""

    def __init__(self):
        self.result = M.Pair(
            RuleSpec(M.Char("Add2"), Add2Rule()())(),
            M.Pair(
                RuleSpec(M.Char("Remove2"), Remove2Rule()())(),
                M.Pair(RuleSpec(M.Char("Swap"), SwapRule()())(), M.EmptyList),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RPlusSpecs(M.Edge):
    """R_plus = R_even with the Add1 perturbation added."""

    def __init__(self):
        self.result = ChainAppend(
            ChainAppend(
                REvenSpecs()(), RuleSpec(M.Char("Add1Even"), Add1EvenRule()())()
            )(),
            RuleSpec(M.Char("Add1Odd"), Add1OddRule()())(),
        )()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class SpecsOfContentChain(M.Edge):
    """Wrap a chain of rule contents into display-named specs (test/evidence use)."""

    def __init__(self, contents, start_index):
        self.result = self._wrap(contents, start_index)
        super().__init__(
            inputs=M.Pair(contents, M.Pair(start_index, M.EmptyList)),
            results=self.result,
        )

    def _wrap(self, remaining, position):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        spec = RuleSpec(M.Char("rule-" + str(position)), M.Head(remaining)())()
        return M.Pair(spec, self._wrap(M.Tail(remaining)(), position + 1))

    def __call__(self):
        return self.result


class RulesetVersionOfSpecs(M.Edge):
    """The A1.2/A2.2 content version of a chain of rule specs."""

    def __init__(self, specs):
        self.result = RulesetVersion(RuleChainOf(specs)())()
        super().__init__(inputs=M.Pair(specs, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleFingerprintOfSpec(M.Edge):
    """The per-rule content digest of one spec."""

    def __init__(self, spec):
        self.result = RuleContentDigest(RuleContent(spec)())()
        super().__init__(inputs=M.Pair(spec, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# inert transition applier
# --------------------------------------------------------------------------
# Statuses are APPLIED and MISS only. No status in this vocabulary means
# "unreachable", "refuted" or "exhausted": those are checker verdicts, and G1
# is not authorised to produce them (A2.1).
#
# Record layout (version 1):
#   Pair(status, Pair(display, Pair(before, Pair(after, Pair(reason,
#        Pair(premise-index, Pair(bindings, EmptyList)))))))
# `after` is EmptyList on a MISS; `reason` and `premise-index` are EmptyList on
# an APPLIED move. Accessors below are the only readers of this layout.

RECORD_LAYOUT_VERSION_TEXT = "researcher-v0-move-record/1"


class MoveRecordLayoutVersion(M.Edge):
    def __init__(self):
        self.result = M.Char(RECORD_LAYOUT_VERSION_TEXT)
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class OutcomeStatus(M.Edge):
    def __init__(self, record):
        self.result = M.Head(record)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomeDisplay(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(record)())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomeBefore(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(record)())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomeAfter(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(record)())())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomeReason(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomePremiseIndex(M.Edge):
    def __init__(self, record):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())()
        )()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomeBindings(M.Edge):
    def __init__(self, record):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(record)())())())())())()
        )()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsAppliedOutcome(M.Edge):
    """Did this move apply? (Any other status is a MISS.)"""

    def __init__(self, record):
        if (
            M.Compare(OutcomeStatus(record)(), AppliedTag()())() is M.truth_value
        ):
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class OutcomeRecord(M.Edge):
    """Build a move record in layout version 1."""

    def __init__(self, status, display, before, after, reason, index, bindings):
        self.result = M.Pair(
            status,
            M.Pair(
                display,
                M.Pair(
                    before,
                    M.Pair(
                        after,
                        M.Pair(
                            reason, M.Pair(index, M.Pair(bindings, M.EmptyList))
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class PremisesOfRule(M.Edge):
    def __init__(self, rule_term):
        self.result = P.RulePremises(rule_term)()
        super().__init__(inputs=M.Pair(rule_term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReplacementOfRule(M.Edge):
    """Replacement templates of a rule term, always as a chain.

    A unary rule (exactly one premise) names a single replacement fact; a rule
    with several premises names a chain of them. Both are returned as a chain.
    """

    def __init__(self, rule_term):
        replacement = P.RuleReplacement(rule_term)()
        if P.RuleIsUnary(rule_term)() is M.truth_value:
            self.result = M.Pair(replacement, M.EmptyList)
        else:
            self.result = replacement
        super().__init__(inputs=M.Pair(rule_term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ApplyRule(M.Edge):
    """The move of a spec at a state: an APPLIED record, else a MISS record.

    In this domain each rule has at most one consistent match at a state (the
    `Tokens` and `Parity` premises match the two distinct facts), so this is
    the complete one-step transition relation and not an arbitrary choice
    among several moves.

    Premises are matched against *distinct* facts and bindings are merged with
    `machine.MergeBindings`, so a repeated variable must bind consistently. A
    MISS never raises, never mutates the state, and never claims anything
    about reachability: an illegal `Remove2` is simply an inapplicable move.
    """

    def __init__(self, spec, state):
        self.result = self._move(spec, state)
        super().__init__(
            inputs=M.Pair(spec, M.Pair(state, M.EmptyList)), results=self.result
        )

    def _move(self, spec, state):
        rule_term = RuleContent(spec)()
        facts = FactsOfState(state)()
        match = FirstMatchOfRule(rule_term, facts)()
        if M.IdentityCompare(match, M.EmptyList)() is M.false_value:
            used = M.Head(match)()
            bindings = M.Head(M.Tail(match)())()
            successors = InstantiatedReplacement(rule_term, bindings)()
            kept = FactsWithoutPositions(facts, used)()
            return OutcomeRecord(
                AppliedTag()(),
                RuleDisplay(spec)(),
                state,
                P.Knowledge(ChainJoin(successors, kept)())(),
                M.EmptyList,
                M.EmptyList,
                bindings,
            )()
        return self._missing(spec, state, rule_term, facts)

    def _missing(self, spec, state, rule_term, facts):
        unmatched = FirstPremiseWithoutMatch(PremisesOfRule(rule_term)(), facts)()
        if IsEmptyTerm(unmatched)() is M.truth_value:
            reason = VariableConflictTag()()
            index = M.EmptyList
        else:
            reason = NoMatchTag()()
            index = M.Head(unmatched)()
        return OutcomeRecord(
            MissTag()(),
            RuleDisplay(spec)(),
            state,
            M.EmptyList,
            reason,
            index,
            M.EmptyList,
        )()

    def __call__(self):
        return self.result


class FirstMatchOfRule(M.Edge):
    """The first consistent premise-to-distinct-fact match of a rule.

    `result` is `Pair(used_positions, Pair(bindings, EmptyList))`, or
    EmptyList when the rule is inapplicable at this state.
    """

    def __init__(self, rule_term, facts):
        self.result = self._premise(
            PremisesOfRule(rule_term)(), facts, M.EmptyList, 0, M.EmptyList
        )
        super().__init__(
            inputs=M.Pair(rule_term, M.Pair(facts, M.EmptyList)), results=self.result
        )

    def _premise(self, premises, facts, used, index, bindings):
        if index == ChainLength(premises)():
            return M.Pair(used, M.Pair(bindings, M.EmptyList))
        return self._fact(
            premises, facts, used, index, bindings, HeadAt(premises, index)(), 0
        )

    def _fact(self, premises, facts, used, index, bindings, premise, position):
        if position >= ChainLength(facts)():
            return M.EmptyList
        if PositionUsed(used, position)() is M.truth_value:
            return self._fact(
                premises, facts, used, index, bindings, premise, position + 1
            )
        match = M.Match(premise, HeadAt(facts, position)())()
        if M.Head(match)() is M.truth_value:
            merged = M.MergeBindings(bindings, M.Tail(match)())()
            if M.Head(merged)() is M.truth_value:
                deeper = self._premise(
                    premises,
                    facts,
                    ChainAppend(used, position)(),
                    index + 1,
                    M.Tail(merged)(),
                )
                if M.IdentityCompare(deeper, M.EmptyList)() is M.false_value:
                    return deeper
        return self._fact(
            premises, facts, used, index, bindings, premise, position + 1
        )

    def __call__(self):
        return self.result


class PositionUsed(M.Edge):
    """Is `position` already taken by this match?"""

    def __init__(self, positions, position):
        self.result = self._scan(positions, position)
        super().__init__(
            inputs=M.Pair(positions, M.Pair(position, M.EmptyList)),
            results=self.result,
        )

    def _scan(self, positions, position):
        if M.IdentityCompare(positions, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.Head(positions)() == position:
            return M.truth_value
        return self._scan(M.Tail(positions)(), position)

    def __call__(self):
        return self.result


class FactsWithoutPositions(M.Edge):
    """The facts chain with the given positions removed, remaining order kept."""

    def __init__(self, facts, positions):
        self.result = self._drop(facts, positions, 0, M.EmptyList)
        super().__init__(
            inputs=M.Pair(facts, M.Pair(positions, M.EmptyList)), results=self.result
        )

    def _drop(self, facts, positions, position, built):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return built
        if PositionUsed(positions, position)() is M.truth_value:
            return self._drop(M.Tail(facts)(), positions, position + 1, built)
        return self._drop(
            M.Tail(facts)(),
            positions,
            position + 1,
            ChainAppend(built, M.Head(facts)())(),
        )

    def __call__(self):
        return self.result


class HeadAt(M.Edge):
    """The term at a chain position (0-based)."""

    def __init__(self, chain, position):
        self.result = self._at(chain, position)
        super().__init__(
            inputs=M.Pair(chain, M.Pair(position, M.EmptyList)), results=self.result
        )

    def _at(self, chain, position):
        if position == 0:
            return M.Head(chain)()
        return self._at(M.Tail(chain)(), position - 1)

    def __call__(self):
        return self.result


class FirstPremiseWithoutMatch(M.Edge):
    """The first premise that matches no single fact, as a term.

    `Pair(position, EmptyList)` when one is found, `EmptyList` otherwise: the
    position rides inside a term, so no emptiness test ever receives an int.
    A rule reported as MISS with a result here failed on *matching*; a MISS
    with `EmptyList` failed on *binding consistency* (a repeated variable that
    could not be bound to one value).
    """

    def __init__(self, premises, facts):
        self.result = self._scan(premises, facts, 0)
        super().__init__(
            inputs=M.Pair(premises, M.Pair(facts, M.EmptyList)), results=self.result
        )

    def _scan(self, premises, facts, position):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if self._matches_any(facts, M.Head(premises)()) is M.truth_value:
            return self._scan(M.Tail(premises)(), facts, position + 1)
        return M.Pair(position, M.EmptyList)

    def _matches_any(self, facts, premise):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.Head(M.Match(premise, M.Head(facts)())())() is M.truth_value:
            return M.truth_value
        return self._matches_any(M.Tail(facts)(), premise)

    def __call__(self):
        return self.result


class InstantiatedReplacement(M.Edge):
    """Replacement facts of a rule with its bindings applied, as a chain."""

    def __init__(self, rule_term, bindings):
        self.result = self._instantiate(
            ReplacementOfRule(rule_term)(), bindings, M.EmptyList
        )
        super().__init__(
            inputs=M.Pair(rule_term, M.Pair(bindings, M.EmptyList)),
            results=self.result,
        )

    def _instantiate(self, templates, bindings, built):
        if M.IdentityCompare(templates, M.EmptyList)() is M.truth_value:
            return built
        return self._instantiate(
            M.Tail(templates)(),
            bindings,
            ChainAppend(
                built, M.Head(M.Instantiate(M.Head(templates)(), bindings)())()
            )(),
        )

    def __call__(self):
        return self.result


class TransitionTable(M.Edge):
    """Every (state, rule) move record: states outer, rules inner, in order."""

    def __init__(self, states, specs):
        self.result = self._rows(states, specs, M.EmptyList)
        super().__init__(
            inputs=M.Pair(states, M.Pair(specs, M.EmptyList)), results=self.result
        )

    def _rows(self, states, specs, built):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return built
        return self._rows(
            M.Tail(states)(),
            specs,
            self._rule_rows(M.Head(states)(), specs, built),
        )

    def _rule_rows(self, state, specs, built):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return built
        return self._rule_rows(
            state,
            M.Tail(specs)(),
            ChainAppend(built, ApplyRule(M.Head(specs)(), state)())(),
        )

    def __call__(self):
        return self.result
