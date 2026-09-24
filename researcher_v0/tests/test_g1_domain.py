"""Researcher-v0 / G1 tests — structural domain, transitions, fingerprint.

Every test is an `Edge` class whose `result` is `truth_value` or
`false_value`; the list of tests is itself a chain (`G1Tests`), so no Python
container is used anywhere. Run:

    python3 -m cat_theo_machine.researcher_v0.tests.run_g1_tests

from the workspace root (the repository's parent directory).

Coverage, against the G1 task text and amendments A1.2 / A2.2:

* `ZeroThroughThree` — construct Zero, One, Two, Three as structural numerals;
* `NoIntegersInStates` — no Python int or bool anywhere in a state or a rule;
* `Add2Transitions`, `Remove2LegalTransitions`, `SwapIsIdentity`;
* `Remove2IllegalIsInapplicable` — an illegal `Remove2` is a MISS, not a crash
  and not an unreachability result;
* `ParityCarriedTruthfully`, `Add1Perturbation`;
* `MoveVocabularyIsInert` — the only statuses are APPLIED and MISS;
* fingerprint: order, display-rename and variable-rename stability; sensitivity
  to `Add2`->`Add1`, to a legality precondition, to a semantic constant and to
  variable sharing; determinism; the display/content partition;
* `REvenRulesPreserveParityObserver` / `Add1RulesRefuteParityObserver` — the
  domain's *shape* fits `invariance.Preserves` (approved inspection §3a). No
  invariant is proved and no certificate is issued: a preserved reading here is
  a property of rule content, not a research result;
* `NoUnreachabilityVocabulary` — the domain and fingerprint modules contain no
  unreachability verdict.
"""

from __future__ import annotations

import os

from ... import machine as M
from ... import proof as P
from ... import invariance as I
from .. import ruleset_digest as RD
from .. import token_domain as D
from ..chains import ChainAppend, ChainLength

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = os.path.dirname(HERE)


class SourceText(M.Edge):
    """Contents of a file that ships with this package (for inertness guards)."""

    def __init__(self, filename):
        handle = open(os.path.join(PACKAGE, filename))
        self.result = handle.read()
        handle.close()
        super().__init__(inputs=M.Pair(M.Char(filename), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TextContains(M.Edge):
    def __init__(self, text, needle):
        if needle in text:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(
            inputs=M.Pair(M.Char(needle), M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class SpecsByDisplay(M.Edge):
    """The specs of a chain whose display equals `display`, as a chain."""

    def __init__(self, specs, display):
        self.result = self._scan(specs, display, M.EmptyList)
        super().__init__(
            inputs=M.Pair(specs, M.Pair(display, M.EmptyList)), results=self.result
        )

    def _scan(self, specs, display, built):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return built
        spec = M.Head(specs)()
        if M.Compare(D.RuleDisplay(spec)(), M.Char(display))() is M.truth_value:
            built = ChainAppend(built, spec)()
        return self._scan(M.Tail(specs)(), display, built)

    def __call__(self):
        return self.result


class ParityObserver(M.Edge):
    """`invariance.Phi` over the carried Parity fact: `Parity(p)`.

    The observer is the domain's own fact shape, so a reading is exactly the
    carried parity value and nothing about the count of pairs.
    """

    def __init__(self):
        pattern = M.Pair(D.ParityTag()(), M.Pair(D.RuleVar("observed")(), M.EmptyList))
        self.result = I.Phi(pattern)()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# numerals and states
# --------------------------------------------------------------------------


class ZeroThroughThreeAreStructural(M.Edge):
    """Construct Zero..Three; each is a structural numeral with its own count."""

    def __init__(self):
        numerals = ChainAppend(
            ChainAppend(
                ChainAppend(
                    ChainAppend(M.EmptyList, D.PeanoZero()())(), D.PeanoFromInt(1)()
                )(),
                D.PeanoFromInt(2)(),
            )(),
            D.PeanoFromInt(3)(),
        )()
        self.result = self._check(numerals, 0)

    def _check(self, numerals, expected):
        if M.IdentityCompare(numerals, M.EmptyList)() is M.truth_value:
            return M.truth_value
        numeral = M.Head(numerals)()
        if D.IsStructuralNumeral(numeral)() is M.false_value:
            return M.false_value
        if D.StructuralCount(numeral)() != expected:
            return M.false_value
        if expected == 0:
            if M.Compare(numeral, D.PeanoSucc(D.PeanoZero()())())() is not M.false_value:
                return M.false_value
        return self._check(M.Tail(numerals)(), expected + 1)

    def __call__(self):
        return self.result


class NumeralsArePairwiseDistinct(M.Edge):
    def __init__(self):
        zero, one = D.PeanoZero()(), D.PeanoFromInt(1)()
        two, three = D.PeanoFromInt(2)(), D.PeanoFromInt(3)()
        self.result = M.truth_value
        if M.Compare(zero, one)() is M.truth_value:
            self.result = M.false_value
        if M.Compare(one, two)() is M.truth_value:
            self.result = M.false_value
        if M.Compare(two, three)() is M.truth_value:
            self.result = M.false_value
        if M.Compare(zero, D.PeanoZero()())() is M.false_value:
            self.result = M.false_value

    def __call__(self):
        return self.result


class NoIntegersInStates(M.Edge):
    """Every atom of every state Zero..Three is a declared singleton or text.

    `AtomsAreDeclaredOrText` fails on an atom whose payload is a Python int or
    bool (`ruleset_digest.PayloadIsText`), so this is the guard that the
    semantic state carries no Python integer.
    """

    def __init__(self):
        self.result = self._check(0)

    def _check(self, count):
        if count > 3:
            return self._check_rules(D.REvenSpecs()())
        if (
            RD.AtomsAreDeclaredOrText(D.FactsOfState(D.StateOfCount(count)())())()
            is M.false_value
        ):
            return M.false_value
        return self._check(count + 1)

    def _check_rules(self, specs):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return self._check_plus(D.RPlusSpecs()())
        if self._content_is_inert(M.Head(specs)()) is M.false_value:
            return M.false_value
        return self._check_rules(M.Tail(specs)())

    def _check_plus(self, specs):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return M.truth_value
        if self._content_is_inert(M.Head(specs)()) is M.false_value:
            return M.false_value
        return self._check_plus(M.Tail(specs)())

    def _content_is_inert(self, spec):
        content = D.RuleContent(spec)()
        if (
            RD.AtomsAreDeclaredOrText(D.PremisesOfRule(content)())() is M.false_value
        ):
            return M.false_value
        return RD.AtomsAreDeclaredOrText(D.ReplacementOfRule(content)())()

    def __call__(self):
        return self.result


class StateOfCountRoundTrips(M.Edge):
    """`StateOfCount(n)` reports count `n` and is consistent, for 0..7."""

    def __init__(self):
        self.result = self._check(0)

    def _check(self, count):
        if count > 7:
            return M.truth_value
        state = D.StateOfCount(count)()
        if D.CountOfState(state)() != count:
            return M.false_value
        if D.StateIsConsistent(state)() is M.false_value:
            return M.false_value
        return self._check(count + 1)

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# transitions
# --------------------------------------------------------------------------


class MoveOfRuleAt(M.Edge):
    """The move record of the rule with the given display at count `n`."""

    def __init__(self, specs, display, count):
        chosen = SpecsByDisplay(specs, display)()
        self.result = D.ApplyRule(M.Head(chosen)(), D.StateOfCount(count)())()
        super().__init__(
            inputs=M.Pair(M.Char(display), M.Pair(count, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RuleMovesCount(
    M.Edge
):
    """Does the rule take count `before` to count `after`, consistently?

    A `None` expectation means the move must be a MISS with reason `no_match`.
    """

    def __init__(self, specs, display, before, after):
        record = MoveOfRuleAt(specs, display, before)()
        self.result = self._expect(record, after)

    def _expect(self, record, after):
        if after is None:
            if D.IsAppliedOutcome(record)() is M.truth_value:
                return M.false_value
            if (
                M.Compare(D.OutcomeStatus(record)(), D.MissTag()())()
                is M.false_value
            ):
                return M.false_value
            if (
                M.Compare(D.OutcomeReason(record)(), D.NoMatchTag()())()
                is M.false_value
            ):
                return M.false_value
            if IsEmpty(D.OutcomeAfter(record)())() is M.false_value:
                return M.false_value
            return M.truth_value
        if D.IsAppliedOutcome(record)() is M.false_value:
            return M.false_value
        state_after = D.OutcomeAfter(record)()
        if D.CountOfState(state_after)() != after:
            return M.false_value
        if D.StateIsConsistent(state_after)() is M.false_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class IsEmpty(M.Edge):
    def __init__(self, term):
        if term is M.EmptyList:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Add2Transitions(M.Edge):
    """`Add2` takes n to n+2 at every tested state, keeping parity."""

    def __init__(self):
        specs = D.REvenSpecs()()
        self.result = M.truth_value
        if RuleMovesCount(specs, "Add2", 0, 2)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Add2", 1, 3)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Add2", 2, 4)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Add2", 3, 5)() is M.false_value:
            self.result = M.false_value

    def __call__(self):
        return self.result


class Remove2LegalTransitions(M.Edge):
    """Where legal (n >= 2), `Remove2` takes n to n-2 and keeps parity."""

    def __init__(self):
        specs = D.REvenSpecs()()
        self.result = M.truth_value
        if RuleMovesCount(specs, "Remove2", 2, 0)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Remove2", 3, 1)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Remove2", 5, 3)() is M.false_value:
            self.result = M.false_value

    def __call__(self):
        return self.result


class Remove2IllegalIsInapplicable(M.Edge):
    """Illegal `Remove2` (fewer than two tokens) is a MISS — not a crash, not
    an unreachability result, and not an error status of any kind."""

    def __init__(self):
        specs = D.REvenSpecs()()
        self.result = M.truth_value
        if RuleMovesCount(specs, "Remove2", 0, None)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Remove2", 1, None)() is M.false_value:
            self.result = M.false_value
        record = MoveOfRuleAt(specs, "Remove2", 0)()
        if D.IsAppliedOutcome(record)() is M.false_value:
            pass
        else:
            self.result = M.false_value
        if (
            D.IsDomainMoveStatus(D.OutcomeStatus(record)())() is M.false_value
        ):
            self.result = M.false_value

    def __call__(self):
        return self.result


class SwapIsIdentity(M.Edge):
    """`Swap` applies everywhere and returns the same state, structurally."""

    def __init__(self):
        specs = D.REvenSpecs()()
        self.result = self._check(specs, 0)

    def _check(self, specs, count):
        if count > 3:
            return M.truth_value
        record = MoveOfRuleAt(specs, "Swap", count)()
        if D.IsAppliedOutcome(record)() is M.false_value:
            return M.false_value
        if (
            M.Compare(D.OutcomeBefore(record)(), D.OutcomeAfter(record)())()
            is M.false_value
        ):
            return M.false_value
        return self._check(specs, count + 1)

    def __call__(self):
        return self.result


class ParityCarriedTruthfully(M.Edge):
    """Every successor of every R_even move keeps parity = count mod 2.

    This is what makes the carried `Parity` fact a derived fact rather than a
    free register: no rule of this domain can leave it stale.
    """

    def __init__(self):
        specs = D.REvenSpecs()()
        self.result = self._states(specs, 0)

    def _states(self, specs, count):
        if count > 5:
            return M.truth_value
        if self._rules(specs, count) is M.false_value:
            return M.false_value
        return self._states(specs, count + 1)

    def _rules(self, specs, count):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return M.truth_value
        record = D.ApplyRule(M.Head(specs)(), D.StateOfCount(count)())()
        if D.IsAppliedOutcome(record)() is M.truth_value:
            if D.StateIsConsistent(D.OutcomeAfter(record)())() is M.false_value:
                return M.false_value
        return self._rules(M.Tail(specs)(), count)

    def __call__(self):
        return self.result


class Add1Perturbation(M.Edge):
    """`Add1Even` applies exactly at even counts, `Add1Odd` exactly at odd
    counts; each adds one token and flips the carried parity. This is the
    scope breaker: on R_plus the parity reading is not preserved."""

    def __init__(self):
        specs = D.RPlusSpecs()()
        self.result = M.truth_value
        if RuleMovesCount(specs, "Add1Even", 0, 1)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Add1Even", 1, None)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Add1Even", 2, 3)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Add1Odd", 1, 2)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Add1Odd", 0, None)() is M.false_value:
            self.result = M.false_value
        if RuleMovesCount(specs, "Add1Odd", 3, 4)() is M.false_value:
            self.result = M.false_value
        if self._flips(specs, "Add1Even", 2) is M.false_value:
            self.result = M.false_value
        if self._flips(specs, "Add1Odd", 3) is M.false_value:
            self.result = M.false_value

    def _flips(self, specs, display, count):
        record = MoveOfRuleAt(specs, display, count)()
        if D.IsAppliedOutcome(record)() is M.false_value:
            return M.false_value
        before = D.ParityValue(D.OutcomeBefore(record)())()
        after = D.ParityValue(D.OutcomeAfter(record)())()
        if before == after:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class MoveVocabularyIsInert(M.Edge):
    """Every status produced by the domain is APPLIED or MISS, and nothing else.

    The domain cannot report unreachability, refutation or exhaustion: those
    are checker verdicts, and the move vocabulary does not contain them (A2.1).
    """

    def __init__(self):
        specs = D.RPlusSpecs()()
        states = ChainAppend(
            ChainAppend(
                ChainAppend(
                    ChainAppend(M.EmptyList, D.StateOfCount(0)())(),
                    D.StateOfCount(1)(),
                )(),
                D.StateOfCount(2)(),
            )(),
            D.StateOfCount(3)(),
        )()
        table = D.TransitionTable(states, specs)()
        self.result = self._scan(table)

    def _scan(self, table):
        if M.IdentityCompare(table, M.EmptyList)() is M.truth_value:
            return M.truth_value
        record = M.Head(table)()
        if D.IsDomainMoveStatus(D.OutcomeStatus(record)())() is M.false_value:
            return M.false_value
        return self._scan(M.Tail(table)())

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# fingerprint
# --------------------------------------------------------------------------


class ReversedChain(M.Edge):
    def __init__(self, chain):
        self.result = self._reverse(chain, M.EmptyList)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def _reverse(self, remaining, built):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return built
        return self._reverse(
            M.Tail(remaining)(), M.Pair(M.Head(remaining)(), built)
        )

    def __call__(self):
        return self.result


class RenamedDisplaySpecs(M.Edge):
    """Same rule contents, display-only names replaced by `display-<i>`."""

    def __init__(self, specs, position):
        self.result = self._rename(specs, position)
        super().__init__(inputs=M.Pair(specs, M.EmptyList), results=self.result)

    def _rename(self, specs, position):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        spec = M.Head(specs)()
        renamed = D.RuleSpec(
            M.Char("display-" + str(position)), D.RuleContent(spec)()
        )()
        return M.Pair(renamed, self._rename(M.Tail(specs)(), position + 1))

    def __call__(self):
        return self.result


class VersionOf(M.Edge):
    def __init__(self, specs):
        self.result = D.RulesetVersionOfSpecs(specs)()
        super().__init__(inputs=M.Pair(specs, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleVersionIsStableUnderOrder(M.Edge):
    def __init__(self):
        specs = D.REvenSpecs()()
        forward = VersionOf(specs)()
        backward = VersionOf(ReversedChain(specs)())()
        if M.Compare(forward, backward)() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value

    def __call__(self):
        return self.result


class RuleVersionIsStableUnderDisplayRename(M.Edge):
    def __init__(self):
        specs = D.REvenSpecs()()
        original = VersionOf(specs)()
        renamed = VersionOf(RenamedDisplaySpecs(specs, 0)())()
        if M.Compare(original, renamed)() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value

    def __call__(self):
        return self.result


class Add2RenamedVariables(M.Edge):
    """`Add2` content rebuilt with different variable *name* payloads."""

    def __init__(self):
        k = D.RuleVar("first")()
        p = D.RuleVar("second")()
        self.result = P.MultiRule(
            M.Pair(D.TokensFact(k)(), M.Pair(D.ParityFact(p)(), M.EmptyList)),
            M.Pair(
                D.TokensFact(D.PeanoSucc(k)())(),
                M.Pair(D.ParityFact(p)(), M.EmptyList),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RuleVersionIsStableUnderVariableRename(M.Edge):
    """Variable *name* payloads are display-only: renaming them preserves the
    per-rule content digest, because `machine.Match` never reads the name."""

    def __init__(self):
        original = D.RuleFingerprintOfSpec(
            M.Head(SpecsByDisplay(D.REvenSpecs()(), "Add2")())()
        )()
        renamed = RD.RuleContentDigest(Add2RenamedVariables()())()
        if M.Compare(original, renamed)() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value

    def __call__(self):
        return self.result


class Remove2RequiringTwoPairs(M.Edge):
    """`Remove2` with a *stricter* legality precondition: two pairs present.

    Same removal shape, different precondition — the content differs, so the
    fingerprint must differ (A2.2).
    """

    def __init__(self):
        k = D.RuleVar("k")()
        p = D.RuleVar("p")()
        self.result = P.MultiRule(
            M.Pair(
                D.TokensFact(D.PeanoSucc(D.PeanoSucc(k)())())(),
                M.Pair(D.ParityFact(p)(), M.EmptyList),
            ),
            M.Pair(D.TokensFact(k)(), M.Pair(D.ParityFact(p)(), M.EmptyList)),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Remove2WithTokenTag(M.Edge):
    """`Remove2` shape with the semantic constant `Tokens` renamed to `Token`."""

    def __init__(self):
        k = D.RuleVar("k")()
        p = D.RuleVar("p")()
        foreign = M.Char("Token")
        self.result = P.MultiRule(
            M.Pair(
                M.Pair(foreign, M.Pair(D.PeanoSucc(k)(), M.EmptyList)),
                M.Pair(D.ParityFact(p)(), M.EmptyList),
            ),
            M.Pair(
                M.Pair(foreign, M.Pair(k, M.EmptyList)),
                M.Pair(D.ParityFact(p)(), M.EmptyList),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Add1EvenWithOddPremise(M.Edge):
    """`Add1Even` with its semantic constant changed from Even to Odd."""

    def __init__(self):
        k = D.RuleVar("k")()
        self.result = P.MultiRule(
            M.Pair(D.TokensFact(k)(), M.Pair(D.ParityFact(D.OddTag()())(), M.EmptyList)),
            M.Pair(D.TokensFact(k)(), M.Pair(D.ParityFact(D.OddTag()())(), M.EmptyList)),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class Remove2WithUnsharedVariable(M.Edge):
    """`Remove2` whose replacement does not share the premise variable.

    `machine.FindBinding` compares variables by identity, so this rule means
    something else: the digest must differ (sharing is semantic).
    """

    def __init__(self):
        k = D.RuleVar("k")()
        p = D.RuleVar("p")()
        fresh_k = D.RuleVar("k")()
        fresh_p = D.RuleVar("p")()
        self.result = P.MultiRule(
            M.Pair(
                D.TokensFact(D.PeanoSucc(k)())(),
                M.Pair(D.ParityFact(p)(), M.EmptyList),
            ),
            M.Pair(
                D.TokensFact(fresh_k)(), M.Pair(D.ParityFact(fresh_p)(), M.EmptyList)
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class RuleVersionSensitivity(M.Edge):
    """Each content change must change the ruleset version."""

    def __init__(self):
        base = VersionOf(D.REvenSpecs()())()
        self.result = self._check(base)

    def _check(self, base):
        variant = VersionOf(
            D.SpecsOfContentChain(
                M.Pair(D.Remove2Rule()(), M.Pair(D.SwapRule()(), M.EmptyList)),
                0,
            )()
        )()
        if M.Compare(base, variant)() is M.truth_value:
            return M.false_value
        return self._check_add1(base)

    def _check_add1(self, base):
        if M.Compare(base, VersionOf(D.RPlusSpecs()())())() is M.truth_value:
            return M.false_value
        return self._check_singletons(base)

    def _check_singletons(self, base):
        original = D.RuleFingerprintOfSpec(
            M.Head(SpecsByDisplay(D.REvenSpecs()(), "Remove2")())()
        )()
        stricter = RD.RuleContentDigest(Remove2RequiringTwoPairs()())()
        foreign_tag = RD.RuleContentDigest(Remove2WithTokenTag()())()
        unshared = RD.RuleContentDigest(Remove2WithUnsharedVariable()())()
        if M.Compare(original, stricter)() is M.truth_value:
            return M.false_value
        if M.Compare(original, foreign_tag)() is M.truth_value:
            return M.false_value
        if M.Compare(original, unshared)() is M.truth_value:
            return M.false_value
        return self._check_add1_constant()

    def _check_add1_constant(self):
        original = D.RuleFingerprintOfSpec(
            M.Head(SpecsByDisplay(D.RPlusSpecs()(), "Add1Even")())()
        )()
        changed = RD.RuleContentDigest(Add1EvenWithOddPremise()())()
        if M.Compare(original, changed)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class DigestIsHexText(M.Edge):
    """A ruleset version is 64 hex characters, the same shape for both rulesets."""

    def __init__(self):
        text = VersionOf(D.REvenSpecs()())()
        other = VersionOf(D.RPlusSpecs()())()
        self.result = M.truth_value
        if RD.TextIsHex(text())() is M.false_value:
            self.result = M.false_value
        if M.Compare(text, other)() is M.truth_value:
            self.result = M.false_value

    def __call__(self):
        return self.result


class DisplayIsOutsideContent(M.Edge):
    """The declared display slot is not reachable from rule content, and no
    display payload appears in the canonical content text."""

    def __init__(self):
        self.result = self._check(D.REvenSpecs()())

    def _check(self, specs):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return self._check_plus(D.RPlusSpecs()())
        spec = M.Head(specs)()
        content = D.RuleContent(spec)()
        if RD.ContainsAtom(content, D.RuleDisplay(spec)())() is M.truth_value:
            return M.false_value
        return self._check(M.Tail(specs)())

    def _check_plus(self, specs):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return M.truth_value
        spec = M.Head(specs)()
        content = D.RuleContent(spec)()
        if RD.ContainsAtom(content, D.RuleDisplay(spec)())() is M.truth_value:
            return M.false_value
        return self._check_plus(M.Tail(specs)())

    def __call__(self):
        return self.result


class DisplayTextNotInContentText(M.Edge):
    """`PrettyTerm` output is never hashed: the display name is absent from the
    canonical content text of the very spec that displays it."""

    def __init__(self):
        spec = M.Head(SpecsByDisplay(D.REvenSpecs()(), "Add2")())()
        text = RD.RuleContentText(D.RuleContent(spec)())()
        if TextContains(text(), "Add2")() is M.false_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value

    def __call__(self):
        return self.result


# --------------------------------------------------------------------------
# checker-shape compatibility (approved inspection §3a) — no certificate
# --------------------------------------------------------------------------


class ParityReadings(M.Edge):
    """Pre and post parity reading of one rule, as `invariance.Preserves` reads
    them: the reading must be present on both sides for a rule to preserve."""

    def __init__(self, rule_term):
        phi = ParityObserver()()
        pre = I.PhiReading(P.Knowledge(P.RulePremises(rule_term)())(), phi)()
        # `ReplacementFacts` is the checker's own post-side reading: a unary
        # rule names one fact, a rule with several premises names the chain.
        post = I.PhiReading(P.Knowledge(I.ReplacementFacts(rule_term)())(), phi)()
        self.result = M.Pair(pre, M.Pair(post, M.EmptyList))
        super().__init__(inputs=M.Pair(rule_term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class REvenRulesPreserveParityObserver(M.Edge):
    """`Preserves` holds for Add2, Remove2 and Swap on the carried parity fact.

    This is a statement about rule content — the domain is shaped so a later
    checker can use it. It proves no invariant and issues no certificate.
    """

    def __init__(self):
        phi = ParityObserver()()
        self.result = self._check(D.REvenSpecs()(), phi)

    def _check(self, specs, phi):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return M.truth_value
        spec = M.Head(specs)()
        result = I.Preserves(D.RuleContent(spec)(), phi, M.EmptyList)()
        if I.IsPreserves(result)() is M.false_value:
            return M.false_value
        return self._check(M.Tail(specs)(), phi)

    def __call__(self):
        return self.result


class Add1RulesRefuteParityObserver(M.Edge):
    """`Preserves` fails for both Add1 rules of R_plus, with a present reading
    on both sides — the scope breaker is visible in rule content, not by
    fallback or by a missing reading."""

    def __init__(self):
        phi = ParityObserver()()
        self.result = self._check(D.RPlusSpecs()(), phi)

    def _check(self, specs, phi):
        if M.IdentityCompare(specs, M.EmptyList)() is M.truth_value:
            return M.truth_value
        spec = M.Head(specs)()
        display = D.RuleDisplay(spec)()
        if M.Compare(display, M.Char("Add1Even"))() is M.truth_value:
            if self._refuted(D.RuleContent(spec)(), phi) is M.false_value:
                return M.false_value
        if M.Compare(display, M.Char("Add1Odd"))() is M.truth_value:
            if self._refuted(D.RuleContent(spec)(), phi) is M.false_value:
                return M.false_value
        return self._check(M.Tail(specs)(), phi)

    def _refuted(self, rule_term, phi):
        result = I.Preserves(rule_term, phi, M.EmptyList)()
        if I.IsInvariantRefuted(result)() is M.false_value:
            return M.false_value
        readings = ParityReadings(rule_term)()
        if IsEmpty(M.Head(readings)())() is M.truth_value:
            return M.false_value
        if IsEmpty(M.Head(M.Tail(readings)())())() is M.truth_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class NoUnreachabilityVocabulary(M.Edge):
    """The domain and fingerprint modules hold no unreachability verdict.

    The guard checks code tokens (`UnreachableLabel`, `ReachabilityPrune`,
    `Invariant(`, `invariance`) rather than prose: the modules are allowed to
    *say* that they issue no verdict, and are not allowed to contain one.
    """

    def __init__(self):
        self.result = self._file("token_domain.py")

    def _file(self, filename):
        text = SourceText(filename)()
        if self._forbidden(text) is M.false_value:
            return M.false_value
        if filename == "token_domain.py":
            return self._file("ruleset_digest.py")
        if filename == "ruleset_digest.py":
            return self._file("chains.py")
        return M.truth_value

    def _forbidden(self, text):
        if TextContains(text, "import invariance")() is M.truth_value:
            return M.false_value
        if TextContains(text, "invariance.Preserves(")() is M.truth_value:
            return M.false_value
        if TextContains(text, "ReachabilityPrune(")() is M.truth_value:
            return M.false_value
        if TextContains(text, "IsUnreachable(")() is M.truth_value:
            return M.false_value
        if TextContains(text, "UnreachableLabel")() is M.truth_value:
            return M.false_value
        return M.truth_value

    def __call__(self):
        return self.result


class RuleFingerprintsAreDeterministic(M.Edge):
    """Rebuilding the same rulesets yields the same versions, twice over."""

    def __init__(self):
        self.result = M.truth_value
        if (
            M.Compare(VersionOf(D.REvenSpecs()())(), VersionOf(D.REvenSpecs()())())()
            is M.false_value
        ):
            self.result = M.false_value
        if (
            M.Compare(VersionOf(D.RPlusSpecs()())(), VersionOf(D.RPlusSpecs()())())()
            is M.false_value
        ):
            self.result = M.false_value

    def __call__(self):
        return self.result


class PlusDiffersFromEven(M.Edge):
    """Adding the Add1 perturbation changes the ruleset version (A1.2)."""

    def __init__(self):
        if (
            M.Compare(VersionOf(D.REvenSpecs()())(), VersionOf(D.RPlusSpecs()())())()
            is M.false_value
        ):
            self.result = M.truth_value
        else:
            self.result = M.false_value

    def __call__(self):
        return self.result


class G1Tests(M.Edge):
    """The G1 test chain: `Pair(name, test class)` in run order."""

    def __init__(self):
        built = M.EmptyList
        built = ChainAppend(built, M.Pair(M.Char("numerals: Zero..Three structural"), ZeroThroughThreeAreStructural))()
        built = ChainAppend(built, M.Pair(M.Char("numerals: pairwise distinct"), NumeralsArePairwiseDistinct))()
        built = ChainAppend(built, M.Pair(M.Char("states: no Python integers"), NoIntegersInStates))()
        built = ChainAppend(built, M.Pair(M.Char("states: count round-trip 0..7"), StateOfCountRoundTrips))()
        built = ChainAppend(built, M.Pair(M.Char("moves: Add2 n -> n+2"), Add2Transitions))()
        built = ChainAppend(built, M.Pair(M.Char("moves: Remove2 legal n -> n-2"), Remove2LegalTransitions))()
        built = ChainAppend(built, M.Pair(M.Char("moves: Remove2 illegal is a MISS"), Remove2IllegalIsInapplicable))()
        built = ChainAppend(built, M.Pair(M.Char("moves: Swap is identity"), SwapIsIdentity))()
        built = ChainAppend(built, M.Pair(M.Char("moves: parity carried truthfully"), ParityCarriedTruthfully))()
        built = ChainAppend(built, M.Pair(M.Char("moves: Add1 perturbation"), Add1Perturbation))()
        built = ChainAppend(built, M.Pair(M.Char("moves: vocabulary is inert"), MoveVocabularyIsInert))()
        built = ChainAppend(built, M.Pair(M.Char("fingerprint: order independent"), RuleVersionIsStableUnderOrder))()
        built = ChainAppend(built, M.Pair(M.Char("fingerprint: display rename stable"), RuleVersionIsStableUnderDisplayRename))()
        built = ChainAppend(built, M.Pair(M.Char("fingerprint: variable rename stable"), RuleVersionIsStableUnderVariableRename))()
        built = ChainAppend(built, M.Pair(M.Char("fingerprint: deterministic"), RuleFingerprintsAreDeterministic))()
        built = ChainAppend(built, M.Pair(M.Char("fingerprint: R_plus differs"), PlusDiffersFromEven))()
        built = ChainAppend(built, M.Pair(M.Char("fingerprint: content sensitivity"), RuleVersionSensitivity))()
        built = ChainAppend(built, M.Pair(M.Char("fingerprint: 64 hex characters"), DigestIsHexText))()
        built = ChainAppend(built, M.Pair(M.Char("partition: display outside content"), DisplayIsOutsideContent))()
        built = ChainAppend(built, M.Pair(M.Char("partition: display text not hashed"), DisplayTextNotInContentText))()
        built = ChainAppend(built, M.Pair(M.Char("checker shape: R_even preserves parity"), REvenRulesPreserveParityObserver))()
        built = ChainAppend(built, M.Pair(M.Char("checker shape: Add1 refutes parity"), Add1RulesRefuteParityObserver))()
        built = ChainAppend(built, M.Pair(M.Char("inertness: no unreachability vocabulary"), NoUnreachabilityVocabulary))()
        self.result = built
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result
