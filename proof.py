from __future__ import annotations

import sys
import threading
import time

from . import machine as M
from . import knowledge as K
from .heuristics import (
    AnchorPreferenceHeuristicCriterionFour,
    AnchorPreferenceHeuristicCriterionOne,
    AnchorPreferenceHeuristicCriterionThree,
    AnchorPreferenceHeuristicCriterionTwo,
    DefaultAnchorPreferenceHeuristic,
    HeuristicRuleOrder,
)
from .labels import (
    CompiledRuleLabel,
    DerivationLabel,
    GoalHeadOrderLabel,
    KnowledgeLabel,
    InvariantLabel,
    PreferEarlierPremiseLabel,
    PreferFewerVariablesLabel,
    PreferGreaterSpecificityLabel,
    PreferLowerFanoutLabel,
    ProofCostLabel,
    RewriteActionLabel,
    SearchAttemptLabel,
    SearchFailureLabel,
    SearchPausedLabel,
    SearchRunningLabel,
    SearchSuccessLabel,
    SearchTimedOutLabel,
    SearchAbortedByUserLabel,
    StepLabel,
    TheoremActionLabel,
    TotalCostLabel,
)
from .schemata import (
    DerivationSchemaGoal,
    DerivationSchemaPlan,
    DerivationSchemaStart,
    LookupDerivationSchema,
    StoreDerivationSchema,
)
from . import gmprep as Gmpmod

# Canonical zero as a GMP count text, so anchor metadata carries machine
# numerals instead of host integers.
ZeroCountText = M.GMPRepText(M.CountRep(M.EmptyList)())()

DEBUG_TRACE_STATE = M.Atom()
DEBUG_TRACE_STATE.value = M.false_value
DERIVATION_REPLAY_DEBUG_SUPPRESS_STATE = M.Atom()
DERIVATION_REPLAY_DEBUG_SUPPRESS_STATE.value = M.false_value
_DEBUG_STATUS_LINE_STATE = M.Atom()
_DEBUG_STATUS_LINE_STATE.value = ""
_DEBUG_STATUS_WIDTH_STATE = M.Atom()
_DEBUG_STATUS_WIDTH_STATE.value = 0
_DEBUG_LOCK = threading.RLock()


class SetDebugTrace(M.Edge):
    def __init__(self, enabled):
        if M.IdentityCompare(enabled, M.truth_value)() is M.truth_value:
            DEBUG_TRACE_STATE.value = M.truth_value
        else:
            DEBUG_TRACE_STATE.value = M.false_value
        self.result = DEBUG_TRACE_STATE()
        super().__init__(inputs=M.Pair(enabled, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


def _derivation_replay_debug_enabled():
    if M.IdentityCompare(DEBUG_TRACE_STATE(), M.false_value)() is M.truth_value:
        return M.false_value
    if M.IdentityCompare(DERIVATION_REPLAY_DEBUG_SUPPRESS_STATE(), M.truth_value)() is M.truth_value:
        return M.false_value
    return M.truth_value


def _derivation_replay_action_debug_enabled():
    if M.IdentityCompare(DEBUG_TRACE_STATE(), M.false_value)() is M.truth_value:
        return M.false_value
    return M.truth_value


def _debug_clear_status():
    if _DEBUG_STATUS_WIDTH_STATE.value > 0:
        sys.stdout.write("\r" + (" " * _DEBUG_STATUS_WIDTH_STATE.value) + "\r")
        _DEBUG_STATUS_WIDTH_STATE.value = 0


def _debug_status(message):
    if M.IdentityCompare(DEBUG_TRACE_STATE(), M.false_value)() is M.truth_value:
        return
    with _DEBUG_LOCK:
        _DEBUG_STATUS_LINE_STATE.value = "DEBUG: " + message
        _debug_clear_status()
        sys.stdout.write(_DEBUG_STATUS_LINE_STATE.value)
        sys.stdout.flush()
        _DEBUG_STATUS_WIDTH_STATE.value = len(_DEBUG_STATUS_LINE_STATE.value)


def _debug_status_clear():
    if M.IdentityCompare(DEBUG_TRACE_STATE(), M.false_value)() is M.truth_value:
        return
    with _DEBUG_LOCK:
        _debug_clear_status()
        _DEBUG_STATUS_LINE_STATE.value = ""
        sys.stdout.flush()


def _debug(message):
    if M.IdentityCompare(DEBUG_TRACE_STATE(), M.false_value)() is M.truth_value:
        return
    with _DEBUG_LOCK:
        had_status = _DEBUG_STATUS_WIDTH_STATE.value > 0
        if had_status:
            _debug_clear_status()
        sys.stdout.write("DEBUG: " + message + "\n")
        if had_status and _DEBUG_STATUS_LINE_STATE.value != "":
            sys.stdout.write(_DEBUG_STATUS_LINE_STATE.value)
            _DEBUG_STATUS_WIDTH_STATE.value = len(_DEBUG_STATUS_LINE_STATE.value)
        sys.stdout.flush()


class DebugTerm(M.Edge):
    """Render a term for tracing without exception-driven discrimination."""

    def __init__(self, x, registry):
        if M.IdentityCompare(DEBUG_TRACE_STATE(), M.false_value)() is M.truth_value:
            self.result = ""
        elif M.IsPair(x)() is M.truth_value:
            self.result = M.PrettyTerm(x, registry)()
        elif x is M.EmptyList:
            self.result = M.PrettyTerm(x, registry)()
        else:
            self.result = M.PrettyTerm(x, registry)()
        super().__init__(
            inputs=M.Pair(x, M.Pair(registry, M.EmptyList)),
            results=M.EmptyList,
        )

    def __call__(self):
        return self.result


def _debug_term(x, registry):
    return DebugTerm(x, registry)()


class Rule(M.Edge):
    def __init__(self, pattern, replacement):
        super().__init__(
            inputs=M.Pair(M.Pair(pattern, M.EmptyList), M.Pair(replacement, M.EmptyList)),
            results=M.EmptyList,
        )

    def __call__(self):
        return self


class MultiRule(M.Edge):
    def __init__(self, premises, replacement):
        super().__init__(
            inputs=M.Pair(premises, M.Pair(replacement, M.EmptyList)),
            results=M.EmptyList,
        )

    def __call__(self):
        return self


class CompiledRule(M.Edge):
    def __init__(self, rule, anchor_meta, requires_variable_anchor, premise_meta=None):
        if premise_meta is None:
            premise_meta = M.EmptyList
        self.result = M.Pair(
            CompiledRuleLabel,
            M.Pair(
                rule,
                M.Pair(
                    anchor_meta,
                    M.Pair(requires_variable_anchor, M.Pair(premise_meta, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                rule,
                M.Pair(
                    anchor_meta,
                    M.Pair(requires_variable_anchor, M.Pair(premise_meta, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsCompiledRule(M.Edge):
    def __init__(self, rule):
        if M.IsPair(rule)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(rule)(), CompiledRuleLabel)() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CompiledRuleRaw(M.Edge):
    def __init__(self, rule):
        if IsCompiledRule(rule)() is M.truth_value:
            self.result = M.Head(M.Tail(rule)())()
        else:
            self.result = rule
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CompiledRuleAnchorMeta(M.Edge):
    def __init__(self, rule):
        if IsCompiledRule(rule)() is M.truth_value:
            self.result = M.Head(M.Tail(M.Tail(rule)())())()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CompiledRuleRequiresVariableAnchor(M.Edge):
    def __init__(self, rule):
        if IsCompiledRule(rule)() is M.truth_value:
            self.result = M.Head(M.Tail(M.Tail(M.Tail(rule)())())())()
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CompiledRulePremiseMeta(M.Edge):
    def __init__(self, rule):
        if IsCompiledRule(rule)() is M.truth_value:
            args = M.Tail(rule)()
            if M.IsPair(M.Tail(M.Tail(M.Tail(args)())())())() is M.truth_value:
                self.result = M.Head(M.Tail(M.Tail(M.Tail(args)())())())()
            else:
                self.result = M.EmptyList
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CompileRule(M.Edge):
    def __init__(self, rule, registry):
        anchor_meta = RuleAnchorStaticMeta(rule, registry)()
        premise_meta = M.EmptyList
        premise_meta_rev = M.EmptyList
        premises = RulePremises(rule)()
        while M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
            premise = M.Head(premises)()
            contains_variable = ContainsVar(premise)()
            head_key = K.HeadBucketKey(premise, registry)()
            premise_meta_rev = M.Pair(
                M.Pair(premise, M.Pair(contains_variable, M.Pair(head_key, M.EmptyList))),
                premise_meta_rev,
            )
            premises = M.Tail(premises)()
        while M.IdentityCompare(premise_meta_rev, M.EmptyList)() is M.false_value:
            premise_meta = M.Pair(M.Head(premise_meta_rev)(), premise_meta)
            premise_meta_rev = M.Tail(premise_meta_rev)()
        requires_variable_anchor = AnchorMetaRequiresVariableAnchor(anchor_meta)()
        self.result = CompiledRule(rule, anchor_meta, requires_variable_anchor, premise_meta)()
        super().__init__(inputs=M.Pair(rule, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class CompileRuleChain(M.Edge):
    def __init__(self, rules, registry):
        self.registry = registry
        self.result = self._compile(rules)
        super().__init__(inputs=M.Pair(rules, M.Pair(registry, M.EmptyList)), results=self.result)

    def _compile(self, rules):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rule = M.Head(rules)()
        rest = M.Tail(rules)()
        return M.Pair(CompileRule(rule, self.registry)(), self._compile(rest))

    def __call__(self):
        return self.result


class RulePremises(M.Edge):
    def __init__(self, rule):
        raw_rule = CompiledRuleRaw(rule)()
        self.result = M.Head(M.EdgeInputs(raw_rule)())()
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RulePattern(M.Edge):
    def __init__(self, rule):
        premises = RulePremises(rule)()
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            self.result = M.Head(premises)()
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleIsUnary(M.Edge):
    def __init__(self, rule):
        premises = RulePremises(rule)()
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Tail(premises)(), M.EmptyList)() is M.truth_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleReplacement(M.Edge):
    def __init__(self, rule):
        raw_rule = CompiledRuleRaw(rule)()
        self.result = M.Head(M.Tail(M.EdgeInputs(raw_rule)())())()
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TheoremAction(M.Edge):
    def __init__(self, rule, bindings=None):
        if bindings is None:
            bindings = M.EmptyList
        raw_rule = CompiledRuleRaw(rule)()
        self.result = M.Pair(TheoremActionLabel, M.Pair(raw_rule, M.Pair(bindings, M.EmptyList)))
        super().__init__(inputs=M.Pair(raw_rule, M.Pair(bindings, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeRewriteSuccessors(M.Edge):
    def __init__(self, state, rule):
        facts = KnowledgeFacts(state)()
        premises = RulePremises(rule)()
        bindings_list = JoinPremises(premises, facts, M.EmptyList)()
        self.result = self._successors(state, rule, bindings_list)
        super().__init__(inputs=M.Pair(state, M.Pair(rule, M.EmptyList)), results=self.result)

    def _successors(self, state, rule, bindings_list):
        if M.IdentityCompare(bindings_list, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        bindings = M.Head(bindings_list)()
        nxt = ApplyKnowledgeRewrite(state, rule, bindings)()
        action = TheoremAction(rule, bindings)()
        rest = self._successors(state, rule, M.Tail(bindings_list)())
        return M.Pair(M.Pair(action, M.Pair(nxt, M.EmptyList)), rest)

    def __call__(self):
        return self.result


class RewriteAction(M.Edge):
    def __init__(self, rule, path):
        raw_rule = CompiledRuleRaw(rule)()
        self.result = M.Pair(RewriteActionLabel, M.Pair(raw_rule, M.Pair(path, M.EmptyList)))
        super().__init__(inputs=M.Pair(raw_rule, M.Pair(path, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsTheoremAction(M.Edge):
    def __init__(self, x):
        if M.IsPair(x)() is M.false_value:
            self.result = M.false_value
        else:
            head = M.Head(x)()
            tail = M.Tail(x)()
            if M.IdentityCompare(head, TheoremActionLabel)() is M.false_value:
                self.result = M.false_value
            elif M.IsPair(tail)() is M.false_value:
                self.result = M.false_value
            elif M.IsPair(M.Tail(tail)())() is M.false_value:
                self.result = M.false_value
            elif M.IdentityCompare(M.Tail(M.Tail(tail)())(), M.EmptyList)() is M.false_value:
                self.result = M.false_value
            else:
                self.result = M.truth_value
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsRewriteAction(M.Edge):
    def __init__(self, x):
        if M.IsPair(x)() is M.false_value:
            self.result = M.false_value
        else:
            head = M.Head(x)()
            tail = M.Tail(x)()
            if M.IdentityCompare(head, RewriteActionLabel)() is M.false_value:
                self.result = M.false_value
            elif M.IsPair(tail)() is M.false_value:
                self.result = M.false_value
            else:
                tail_rest = M.Tail(tail)()
                if M.IsPair(tail_rest)() is M.false_value:
                    self.result = M.false_value
                elif M.IdentityCompare(M.Tail(tail_rest)(), M.EmptyList)() is M.false_value:
                    self.result = M.false_value
                else:
                    self.result = M.truth_value
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ActionRule(M.Edge):
    def __init__(self, x):
        if IsTheoremAction(x)() is M.truth_value:
            self.result = M.Head(M.Tail(x)())()
        elif IsRewriteAction(x)() is M.truth_value:
            self.result = M.Head(M.Tail(x)())()
        else:
            self.result = x
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ActionPath(M.Edge):
    def __init__(self, x):
        if IsRewriteAction(x)() is M.truth_value:
            self.result = M.Head(M.Tail(M.Tail(x)())())()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ActionBindings(M.Edge):
    def __init__(self, x):
        if IsTheoremAction(x)() is M.truth_value:
            self.result = M.Head(M.Tail(M.Tail(x)())())()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Append(M.Edge):
    def __init__(self, left, right):
        self.result = self._append(left, right)
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def _append(self, left, right):
        reversed_left = M.EmptyList
        current = left
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            reversed_left = M.Pair(M.Head(current)(), reversed_left)
            current = M.Tail(current)()
        result = right
        current = reversed_left
        while M.IdentityCompare(current, M.EmptyList)() is M.false_value:
            result = M.Pair(M.Head(current)(), result)
            current = M.Tail(current)()
        return result

    def __call__(self):
        return self.result


class CollectRules(M.Edge):
    def __init__(self, tree):
        collected = self._collect(M.TreeEntries(tree)())
        self.result = M.Reverse(collected)()
        super().__init__(inputs=M.Pair(tree, M.EmptyList), results=self.result)

    def _collect(self, entries):
        stack = M.EmptyList
        curr = entries
        while M.IdentityCompare(curr, M.EmptyList)() is M.false_value:
            entry = M.Head(curr)()
            fact = M.Head(M.Tail(entry)())()
            stack = M.Pair(fact, stack)
            curr = M.Tail(curr)()
        
        res = M.EmptyList
        while M.IdentityCompare(stack, M.EmptyList)() is M.false_value:
            res = M.Pair(M.Head(stack)(), res)
            stack = M.Tail(stack)()
        return res

    def __call__(self):
        return self.result


class Knowledge(M.Edge):
    def __init__(self, facts):
        self.result = M.Pair(KnowledgeLabel, M.Pair(facts, M.EmptyList))
        super().__init__(inputs=M.Pair(facts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsKnowledge(M.Edge):
    def __init__(self, x):
        if M.IsPair(x)() is M.false_value:
            atom_result = M.false_value
        else:
            head = M.Head(x)()
            tail = M.Tail(x)()
            if M.IdentityCompare(head, KnowledgeLabel)() is M.false_value:
                atom_result = M.false_value
            elif M.IsPair(tail)() is M.false_value:
                atom_result = M.false_value
            elif M.IdentityCompare(M.Tail(tail)(), M.EmptyList)() is M.false_value:
                atom_result = M.false_value
            else:
                atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class KnowledgeFacts(M.Edge):
    def __init__(self, x):
        if IsKnowledge(x)() is M.truth_value:
            self.result = M.Head(M.Tail(x)())()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class NormalizeKnowledgeFacts(M.Edge):
    def __init__(self, facts, registry):
        self.registry = registry
        trie = K.KnowledgeTrieInsertChain(M.EmptyTree, facts, registry)()
        self.result = K.KnowledgeTrieFacts(trie, registry)()
        super().__init__(inputs=M.Pair(facts, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class NormalizeKnowledge(M.Edge):
    def __init__(self, x, registry):
        if IsKnowledge(x)() is M.truth_value:
            facts = NormalizeKnowledgeFacts(KnowledgeFacts(x)(), registry)()
            self.result = Knowledge(facts)()
        else:
            self.result = x
        super().__init__(inputs=M.Pair(x, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ReplacementIsFactList(M.Edge):
    def __init__(self, rule):
        replacement = RuleReplacement(rule)()
        atom_result = M.false_value
        if M.IsPair(replacement)() is M.truth_value:
            if M.IsPair(M.Head(replacement)())() is M.truth_value:
                atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DropMatchedFacts(M.Edge):
    def __init__(self, facts, matched):
        self.result = self._drop(facts, matched)
        super().__init__(inputs=M.Pair(facts, M.Pair(matched, M.EmptyList)), results=self.result)

    def _drop_one(self, facts, target, kept):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return kept
        fact = M.Head(facts)()
        rest = M.Tail(facts)()
        if M.Compare(fact, target)() is M.truth_value:
            acc = rest
            while M.IdentityCompare(kept, M.EmptyList)() is M.false_value:
                acc = M.Pair(M.Head(kept)(), acc)
                kept = M.Tail(kept)()
            return acc
        return self._drop_one(rest, target, M.Pair(fact, kept))

    def _drop(self, facts, matched):
        remaining = facts
        targets = matched
        while M.IdentityCompare(targets, M.EmptyList)() is M.false_value:
            remaining = self._drop_one(remaining, M.Head(targets)(), M.EmptyList)
            targets = M.Tail(targets)()
        return remaining

    def __call__(self):
        return self.result


class InstantiateFactList(M.Edge):
    def __init__(self, terms, bindings):
        self.bindings = bindings
        self.result = self._walk(terms)
        super().__init__(inputs=M.Pair(terms, M.Pair(bindings, M.EmptyList)), results=self.result)

    def _walk(self, terms):
        if M.IdentityCompare(terms, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        inst = M.Instantiate(M.Head(terms)(), self.bindings)()
        return M.Pair(M.Head(inst)(), self._walk(M.Tail(terms)()))

    def __call__(self):
        return self.result


class JoinPremises(M.Edge):
    def __init__(self, premises, facts, bindings):
        self.facts = facts
        self.result = self._join(premises, bindings)
        super().__init__(inputs=M.Pair(premises, M.Pair(facts, M.Pair(bindings, M.EmptyList))), results=self.result)

    def _join(self, premises, bindings):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.Pair(bindings, M.EmptyList)
        premise = M.Head(premises)()
        rest = M.Tail(premises)()
        acc = M.EmptyList
        remaining = self.facts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            fact = M.Head(remaining)()
            match = M.Match(premise, fact)()
            if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
                merged = M.MergeBindings(bindings, M.Tail(match)())()
                if M.IdentityCompare(M.Head(merged)(), M.truth_value)() is M.truth_value:
                    deeper = self._join(rest, M.Tail(merged)())
                    while M.IdentityCompare(deeper, M.EmptyList)() is M.false_value:
                        acc = M.Pair(M.Head(deeper)(), acc)
                        deeper = M.Tail(deeper)()
            remaining = M.Tail(remaining)()
        return acc

    def __call__(self):
        return self.result


class FactsCover(M.Edge):
    def __init__(self, left, right):
        self.right = right
        self.result = self._cover(left)
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def _has(self, facts, target):
        remaining = facts
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(remaining)(), target)() is M.truth_value:
                return M.truth_value
            remaining = M.Tail(remaining)()
        return M.false_value

    def _cover(self, left):
        remaining = left
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if self._has(self.right, M.Head(remaining)()) is M.false_value:
                return M.false_value
            remaining = M.Tail(remaining)()
        return M.truth_value

    def __call__(self):
        return self.result


class SameKnowledge(M.Edge):
    def __init__(self, left, right):
        if IsKnowledge(left)() is M.false_value:
            self.result = M.TermEqual(left, right)()
        elif IsKnowledge(right)() is M.false_value:
            self.result = M.false_value
        else:
            left_facts = KnowledgeFacts(left)()
            right_facts = KnowledgeFacts(right)()
            if FactsCover(left_facts, right_facts)() is M.truth_value:
                if FactsCover(right_facts, left_facts)() is M.truth_value:
                    self.result = M.truth_value
                else:
                    self.result = M.false_value
            else:
                self.result = M.false_value
        super().__init__(inputs=M.Pair(left, M.Pair(right, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ApplyKnowledgeRewrite(M.Edge):
    def __init__(self, state, rule, bindings):
        facts = KnowledgeFacts(state)()
        premises = RulePremises(rule)()
        replacement = RuleReplacement(rule)()
        consumed = InstantiateFactList(premises, bindings)()
        leftover = DropMatchedFacts(facts, consumed)()
        added = InstantiateFactList(replacement, bindings)()
        next_facts = leftover
        extra = added
        while M.IdentityCompare(extra, M.EmptyList)() is M.false_value:
            next_facts = M.Pair(M.Head(extra)(), next_facts)
            extra = M.Tail(extra)()
        self.result = Knowledge(next_facts)()
        super().__init__(inputs=M.Pair(state, M.Pair(rule, M.Pair(bindings, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class TermHead(M.Edge):
    def __init__(self, x, registry):
        if M.IsPair(x)() is M.truth_value:
            atom_result = M.Head(x)()
        else:
            c = M.GetConstructor(x, registry)()
            if M.IdentityCompare(c, M.EmptyList)() is M.truth_value:
                atom_result = M.EmptyList
            else:
                atom_result = M.Head(c)()
        self.result = atom_result
        super().__init__(inputs=M.Pair(x, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsVarPattern(M.Edge):
    def __init__(self, p):
        if M.IsPair(p)() is M.false_value:
            atom_result = M.false_value
        else:
            h = M.Head(p)()
            t = M.Tail(p)()
            if M.IdentityCompare(h, M.VarTag)() is M.false_value:
                atom_result = M.false_value
            elif M.IsPair(t)() is M.false_value:
                atom_result = M.false_value
            elif M.IdentityCompare(M.Tail(t)(), M.EmptyList)() is M.false_value:
                atom_result = M.false_value
            else:
                atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(p, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContainsVar(M.Edge):
    def __init__(self, x):
        self.result = self._contains(x)
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=self.result)

    def _contains(self, x):
        if IsVarPattern(x)() is M.truth_value:
            return M.truth_value
        if M.IsPair(x)() is M.truth_value:
            head_has = self._contains(M.Head(x)())
            tail_has = self._contains(M.Tail(x)())
            return M.OrAtom(head_has, tail_has)()
        return M.false_value

    def __call__(self):
        return self.result


class AnchorEntryPremise(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(entry)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AnchorEntryIndex(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AnchorEntryVarCount(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AnchorEntrySpecificity(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(entry)())())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleAnchorStaticEntry(M.Edge):
    """Anchor metadata for one premise, as a machine list.

    Shape: Pair(premise, Pair(index, Pair(var_count, Pair(specificity, []))))
    where index, var_count and specificity are GMP count texts, so the
    entry is an ordinary hypergraph structure rather than a host tuple.
    """

    def __init__(self, premise, premise_index, registry):
        self.result = M.Pair(
            premise,
            M.Pair(
                premise_index,
                M.Pair(
                    self._var_count(premise),
                    M.Pair(self._specificity(premise), M.EmptyList),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(premise, M.Pair(premise_index, M.Pair(registry, M.EmptyList))), results=self.result)

    def _var_count(self, term):
        if IsVarPattern(term)() is M.truth_value:
            return Gmpmod.GMPSuccText(ZeroCountText)()
        if M.IsPair(term)() is M.truth_value:
            return Gmpmod.GMPAddText(
                self._var_count(M.Head(term)()),
                self._var_count(M.Tail(term)()),
            )()
        return ZeroCountText

    def _specificity(self, term):
        if IsVarPattern(term)() is M.truth_value:
            return ZeroCountText
        if M.IsPair(term)() is M.truth_value:
            return Gmpmod.GMPSuccText(
                Gmpmod.GMPAddText(
                    self._specificity(M.Head(term)()),
                    self._specificity(M.Tail(term)()),
                )()
            )()
        return Gmpmod.GMPSuccText(ZeroCountText)()

    def __call__(self):
        return self.result


class RuleAnchorStaticMeta(M.Edge):
    def __init__(self, rule, registry):
        premises = RulePremises(rule)()
        premise_index = ZeroCountText
        entries_rev = M.EmptyList
        while M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
            entries_rev = M.Pair(
                RuleAnchorStaticEntry(M.Head(premises)(), premise_index, registry)(),
                entries_rev,
            )
            premises = M.Tail(premises)()
            premise_index = Gmpmod.GMPSuccText(premise_index)()
        entries = M.EmptyList
        while M.IdentityCompare(entries_rev, M.EmptyList)() is M.false_value:
            entries = M.Pair(M.Head(entries_rev)(), entries)
            entries_rev = M.Tail(entries_rev)()
        self.result = entries
        super().__init__(inputs=M.Pair(rule, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class AnchorMetaIsEmpty(M.Edge):
    def __init__(self, meta):
        if M.IdentityCompare(meta, M.EmptyList)() is M.truth_value:
            self.result = M.truth_value
        elif M.IsPair(meta)() is M.false_value:
            self.result = M.truth_value
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(meta, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AnchorMetaRequiresVariableAnchor(M.Edge):
    """True when any entry anchors on a variable-bearing premise."""

    def __init__(self, meta):
        atom_result = M.false_value
        remaining = meta
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            var_count = AnchorEntryVarCount(M.Head(remaining)())()
            if Gmpmod.GMPLessText(ZeroCountText, var_count)() is M.truth_value:
                atom_result = M.truth_value
                remaining = M.EmptyList
            else:
                remaining = M.Tail(remaining)()
        self.result = atom_result
        super().__init__(inputs=M.Pair(meta, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ChooseRuleAnchorWithMeta(M.Edge):
    def __init__(self, heuristic, anchor_meta, requires_variable_anchor, current, knowledge_head_index, registry):
        self.registry = registry
        self.heuristic = heuristic
        self.current = current
        self._knowledge_head_index = knowledge_head_index
        self._requires_variable_anchor = requires_variable_anchor
        self.result = self._choose(anchor_meta, None)
        super().__init__(inputs=M.Pair(heuristic, M.Pair(anchor_meta, M.Pair(requires_variable_anchor, M.Pair(current, M.Pair(knowledge_head_index, M.Pair(registry, M.EmptyList)))))), results=self.result)

    def _fact_count(self, facts):
        return M.GMPRepText(M.CountRep(facts)())()

    def _facts(self):
        if IsKnowledge(self.current)() is M.truth_value:
            return KnowledgeFacts(self.current)()
        return M.Pair(self.current, M.EmptyList)

    def _entry_premise(self, entry):
        return AnchorEntryPremise(entry)()

    def _entry_index(self, entry):
        return AnchorEntryIndex(entry)()

    def _entry_var_count(self, entry):
        return AnchorEntryVarCount(entry)()

    def _entry_specificity(self, entry):
        return AnchorEntrySpecificity(entry)()

    def _fanout(self, premise):
        if M.IdentityCompare(self._knowledge_head_index, M.EmptyList)() is M.false_value:
            return M.GMPRepText(M.CountRep(K.KnowledgeHeadIndexBucket(self._knowledge_head_index, premise, self.registry)())())()
        return self._fact_count(self._facts())

    def _criterion_prefers_left(self, criterion, left_entry, right_entry):
        if M.IdentityCompare(criterion, PreferLowerFanoutLabel)() is M.truth_value:
            left_value = self._fanout(self._entry_premise(left_entry))
            right_value = self._fanout(self._entry_premise(right_entry))
            if Gmpmod.GMPLessText(left_value, right_value)() is M.truth_value:
                return M.truth_value
            if Gmpmod.GMPLessText(right_value, left_value)() is M.truth_value:
                return M.false_value
            return M.EmptyList
        if M.IdentityCompare(criterion, PreferFewerVariablesLabel)() is M.truth_value:
            left_value = self._entry_var_count(left_entry)
            right_value = self._entry_var_count(right_entry)
            if Gmpmod.GMPLessText(left_value, right_value)() is M.truth_value:
                return M.truth_value
            if Gmpmod.GMPLessText(right_value, left_value)() is M.truth_value:
                return M.false_value
            return M.EmptyList
        if M.IdentityCompare(criterion, PreferGreaterSpecificityLabel)() is M.truth_value:
            left_value = self._entry_specificity(left_entry)
            right_value = self._entry_specificity(right_entry)
            if Gmpmod.GMPLessText(right_value, left_value)() is M.truth_value:
                return M.truth_value
            if Gmpmod.GMPLessText(left_value, right_value)() is M.truth_value:
                return M.false_value
            return M.EmptyList
        if M.IdentityCompare(criterion, PreferEarlierPremiseLabel)() is M.truth_value:
            left_value = self._entry_index(left_entry)
            right_value = self._entry_index(right_entry)
            if Gmpmod.GMPLessText(left_value, right_value)() is M.truth_value:
                return M.truth_value
            if Gmpmod.GMPLessText(right_value, left_value)() is M.truth_value:
                return M.false_value
            return M.EmptyList
        return M.EmptyList

    def _prefer(self, left_entry, right_entry):
        criterion = AnchorPreferenceHeuristicCriterionOne(self.heuristic)()
        choice = self._criterion_prefers_left(criterion, left_entry, right_entry)
        if M.IdentityCompare(choice, M.EmptyList)() is M.false_value:
            return choice
        criterion = AnchorPreferenceHeuristicCriterionTwo(self.heuristic)()
        choice = self._criterion_prefers_left(criterion, left_entry, right_entry)
        if M.IdentityCompare(choice, M.EmptyList)() is M.false_value:
            return choice
        criterion = AnchorPreferenceHeuristicCriterionThree(self.heuristic)()
        choice = self._criterion_prefers_left(criterion, left_entry, right_entry)
        if M.IdentityCompare(choice, M.EmptyList)() is M.false_value:
            return choice
        criterion = AnchorPreferenceHeuristicCriterionFour(self.heuristic)()
        choice = self._criterion_prefers_left(criterion, left_entry, right_entry)
        if M.IdentityCompare(choice, M.EmptyList)() is M.false_value:
            return choice
        return M.false_value

    def _choose(self, meta, best_entry):
        next_best = M.EmptyList
        if best_entry is not None:
            next_best = best_entry
        remaining = meta
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            entry = M.Head(remaining)()
            skip = M.false_value
            if M.IdentityCompare(self._requires_variable_anchor, M.truth_value)() is M.truth_value:
                var_count = self._entry_var_count(entry)
                if Gmpmod.GMPEqualText(var_count, ZeroCountText)() is M.truth_value:
                    skip = M.truth_value
            if M.IdentityCompare(skip, M.false_value)() is M.truth_value:
                if M.IdentityCompare(next_best, M.EmptyList)() is M.truth_value:
                    next_best = entry
                elif self._prefer(entry, next_best) is M.truth_value:
                    next_best = entry
            remaining = M.Tail(remaining)()
        if M.IdentityCompare(next_best, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return self._entry_premise(next_best)

    def __call__(self):
        return self.result


class ChooseRuleAnchor(M.Edge):
    def __init__(self, heuristic, rule, current, registry, knowledge_head_index=None):
        if RuleIsUnary(rule)() is M.truth_value:
            self.result = RulePattern(rule)()
        else:
            if knowledge_head_index is None:
                knowledge_head_index = M.EmptyList
                if IsKnowledge(current)() is M.truth_value:
                    knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, KnowledgeFacts(current)(), registry)()
            anchor_meta = CompiledRuleAnchorMeta(rule)()
            requires_variable_anchor = CompiledRuleRequiresVariableAnchor(rule)()
            if AnchorMetaIsEmpty(anchor_meta)() is M.truth_value:
                anchor_meta = RuleAnchorStaticMeta(rule, registry)()
                requires_variable_anchor = AnchorMetaRequiresVariableAnchor(anchor_meta)()
            self.result = ChooseRuleAnchorWithMeta(
                heuristic,
                anchor_meta,
                requires_variable_anchor,
                current,
                knowledge_head_index,
                registry,
            )()
        super().__init__(inputs=M.Pair(heuristic, M.Pair(rule, M.Pair(current, M.Pair(registry, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class FilterApplicableRules(M.Edge):
    """Production rule admission.

    Contains no timing, no pretty-printing, no Peano probe counters and no
    per-rule debug calls. Diagnostic admission lives in
    FilterApplicableRulesProbe, which is dispatched to before any timing or
    formatting occurs.
    """

    def __init__(self, rules, current, registry, knowledge_head_index=None, knowledge_exact_trie=None):
        self.registry = registry
        self.current = current
        self._anchor_heuristic = DefaultAnchorPreferenceHeuristic()()
        self._knowledge_head_index = M.EmptyList
        self._knowledge_exact_trie = M.EmptyList
        self._knowledge_ground_fact_cache = M.EmptyList
        self._premise_bucket_cache = M.EmptyList
        if knowledge_head_index is None:
            if IsKnowledge(current)() is M.truth_value:
                self._knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, KnowledgeFacts(current)(), self.registry)()
        else:
            self._knowledge_head_index = knowledge_head_index
        if knowledge_exact_trie is None:
            if IsKnowledge(current)() is M.truth_value:
                self._knowledge_exact_trie = K.KnowledgeTrieInsertChain(M.EmptyTree, KnowledgeFacts(current)(), self.registry)()
        else:
            self._knowledge_exact_trie = knowledge_exact_trie
        compiled_rules = rules
        if M.IdentityCompare(compiled_rules, M.EmptyList)() is M.false_value:
            if IsCompiledRule(M.Head(compiled_rules)())() is M.false_value:
                compiled_rules = CompileRuleChain(compiled_rules, registry)()
        self.result = self._filter(compiled_rules, current)
        super().__init__(inputs=M.Pair(rules, M.Pair(current, M.Pair(registry, M.EmptyList))), results=self.result)

    def _rule_anchor(self, rule):
        premises = RulePremises(rule)()
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return RulePattern(rule)()
        if RuleIsUnary(rule)() is M.truth_value:
            return RulePattern(rule)()
        return ChooseRuleAnchor(self._anchor_heuristic, rule, self.current, self.registry, self._knowledge_head_index)()

    def _knowledge_has_ground_fact(self, term):
        term_key = M.ExactKey(term, self.registry)()
        cache_cursor = self._knowledge_ground_fact_cache
        while M.IdentityCompare(cache_cursor, M.EmptyList)() is M.false_value:
            cache_entry = M.Head(cache_cursor)()
            if M.TermEqual(M.Head(cache_entry)(), term_key)() is M.truth_value:
                return M.Head(M.Tail(cache_entry)())()
            cache_cursor = M.Tail(cache_cursor)()
        result = M.false_value
        if M.IdentityCompare(self._knowledge_exact_trie, M.EmptyList)() is M.false_value:
            result = K.KnowledgeTrieHasFact(self._knowledge_exact_trie, term, self.registry)()
        else:
            facts = KnowledgeFacts(self.current)()
            while M.IdentityCompare(facts, M.EmptyList)() is M.false_value:
                if M.TermEqual(M.Head(facts)(), term)() is M.truth_value:
                    result = M.truth_value
                    facts = M.EmptyList
                else:
                    facts = M.Tail(facts)()
        self._knowledge_ground_fact_cache = M.Pair(
            M.Pair(term_key, M.Pair(result, M.EmptyList)),
            self._knowledge_ground_fact_cache,
        )
        return result

    def _rule_has_missing_required_premise_head(self, rule):
        premise_meta = CompiledRulePremiseMeta(rule)()
        if M.IdentityCompare(premise_meta, M.EmptyList)() is M.false_value:
            while M.IdentityCompare(premise_meta, M.EmptyList)() is M.false_value:
                entry = M.Head(premise_meta)()
                premise = M.Head(entry)()
                contains_variable = M.Head(M.Tail(entry)())()
                if IsVarPattern(premise)() is M.truth_value:
                    premise_meta = M.Tail(premise_meta)()
                    continue
                if contains_variable is M.false_value:
                    if self._knowledge_has_ground_fact(premise) is M.false_value:
                        return M.truth_value
                    premise_meta = M.Tail(premise_meta)()
                    continue
                premise_key = M.ExactKey(premise, self.registry)()
                bucket = M.EmptyList
                cache_cursor = self._premise_bucket_cache
                while M.IdentityCompare(cache_cursor, M.EmptyList)() is M.false_value:
                    cache_entry = M.Head(cache_cursor)()
                    if M.TermEqual(M.Head(cache_entry)(), premise_key)() is M.truth_value:
                        bucket = M.Head(M.Tail(cache_entry)())()
                        cache_cursor = M.EmptyList
                    else:
                        cache_cursor = M.Tail(cache_cursor)()
                if M.IdentityCompare(bucket, M.EmptyList)() is M.truth_value:
                    bucket = K.KnowledgeHeadIndexBucket(self._knowledge_head_index, premise, self.registry)()
                    self._premise_bucket_cache = M.Pair(
                        M.Pair(premise_key, M.Pair(bucket, M.EmptyList)),
                        self._premise_bucket_cache,
                    )
                if M.IdentityCompare(bucket, M.EmptyList)() is M.truth_value:
                    return M.truth_value
                premise_meta = M.Tail(premise_meta)()
            return M.false_value
        premises = RulePremises(rule)()
        while M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
            premise = M.Head(premises)()
            if IsVarPattern(premise)() is M.truth_value:
                premises = M.Tail(premises)()
                continue
            if ContainsVar(premise)() is M.false_value:
                if self._knowledge_has_ground_fact(premise) is M.false_value:
                    return M.truth_value
                premises = M.Tail(premises)()
                continue
            premise_key = M.ExactKey(premise, self.registry)()
            bucket = M.EmptyList
            cache_cursor = self._premise_bucket_cache
            while M.IdentityCompare(cache_cursor, M.EmptyList)() is M.false_value:
                cache_entry = M.Head(cache_cursor)()
                if M.TermEqual(M.Head(cache_entry)(), premise_key)() is M.truth_value:
                    bucket = M.Head(M.Tail(cache_entry)())()
                    cache_cursor = M.EmptyList
                else:
                    cache_cursor = M.Tail(cache_cursor)()
            if M.IdentityCompare(bucket, M.EmptyList)() is M.truth_value:
                bucket = K.KnowledgeHeadIndexBucket(self._knowledge_head_index, premise, self.registry)()
                self._premise_bucket_cache = M.Pair(
                    M.Pair(premise_key, M.Pair(bucket, M.EmptyList)),
                    self._premise_bucket_cache,
                )
            if M.IdentityCompare(bucket, M.EmptyList)() is M.truth_value:
                return M.truth_value
            premises = M.Tail(premises)()
        return M.false_value

    def _anchor_matches_facts(self, anchor, facts):
        if M.IdentityCompare(anchor, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        match = M.Match(anchor, fact)()
        if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
            return M.truth_value
        return self._anchor_matches_facts(anchor, M.Tail(facts)())

    def _rule_head_applicable(self, rule, current):
        if IsKnowledge(current)() is M.truth_value:
            premises = RulePremises(rule)()
            if M.IdentityCompare(self._knowledge_head_index, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
                    if self._rule_has_missing_required_premise_head(rule) is M.truth_value:
                        return M.false_value
            anchor = self._rule_anchor(rule)
            facts = KnowledgeFacts(current)()
            if M.IdentityCompare(self._knowledge_head_index, M.EmptyList)() is M.false_value:
                if IsVarPattern(anchor)() is M.false_value:
                    anchor_key = M.ExactKey(anchor, self.registry)()
                    cache_cursor = self._premise_bucket_cache
                    facts = M.EmptyList
                    while M.IdentityCompare(cache_cursor, M.EmptyList)() is M.false_value:
                        cache_entry = M.Head(cache_cursor)()
                        if M.TermEqual(M.Head(cache_entry)(), anchor_key)() is M.truth_value:
                            facts = M.Head(M.Tail(cache_entry)())()
                            cache_cursor = M.EmptyList
                        else:
                            cache_cursor = M.Tail(cache_cursor)()
                    if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
                        facts = K.KnowledgeHeadIndexBucket(self._knowledge_head_index, anchor, self.registry)()
                        self._premise_bucket_cache = M.Pair(
                            M.Pair(anchor_key, M.Pair(facts, M.EmptyList)),
                            self._premise_bucket_cache,
                        )
            if ContainsVar(anchor)() is M.false_value:
                return self._knowledge_has_ground_fact(anchor)
            return self._anchor_matches_facts(anchor, facts)
        pattern = RulePattern(rule)()
        if IsVarPattern(pattern)() is M.truth_value:
            return M.truth_value
        p_head = TermHead(pattern, self.registry)()
        c_head = TermHead(current, self.registry)()
        if M.AndAtom(
            M.IdentityCompare(p_head, M.EmptyList)(),
            M.IdentityCompare(c_head, M.EmptyList)(),
        )() is M.truth_value:
            match = M.Match(pattern, current)()
            if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
                return M.truth_value
            return M.false_value
        if M.OrAtom(
            M.IdentityCompare(p_head, M.EmptyList)(),
            M.IdentityCompare(c_head, M.EmptyList)(),
        )() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(p_head, c_head)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _filter(self, rules, current):
        if M.Compare(rules, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        r = M.Head(rules)()
        rest = M.Tail(rules)()
        if self._rule_head_applicable(r, current) is M.truth_value:
            return M.Pair(r, self._filter(rest, current))
        return self._filter(rest, current)

    def __call__(self):
        return self.result


class FilterApplicableRulesProbe(M.Edge):
    """Diagnostic rule admission.

    Mirrors FilterApplicableRules but records per-rule anchor/bucket/match
    timings, Peano attempt and rule-index counters, and emits a per-rule
    debug line. Never used by the production admission path.
    """

    def __init__(self, rules, current, registry, knowledge_head_index=None, knowledge_exact_trie=None):
        self.registry = registry
        self.current = current
        self._anchor_heuristic = DefaultAnchorPreferenceHeuristic()()
        self._knowledge_head_index = M.EmptyList
        self._knowledge_exact_trie = M.EmptyList
        self._probe_rule_index = M.Zero
        self._last_anchor_match_attempts = M.Zero
        if knowledge_head_index is None:
            if IsKnowledge(current)() is M.truth_value:
                self._knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, KnowledgeFacts(current)(), self.registry)()
        else:
            self._knowledge_head_index = knowledge_head_index
        if knowledge_exact_trie is None:
            if IsKnowledge(current)() is M.truth_value:
                self._knowledge_exact_trie = K.KnowledgeTrieInsertChain(M.EmptyTree, KnowledgeFacts(current)(), self.registry)()
        else:
            self._knowledge_exact_trie = knowledge_exact_trie
        compiled_rules = rules
        if M.IdentityCompare(compiled_rules, M.EmptyList)() is M.false_value:
            if IsCompiledRule(M.Head(compiled_rules)())() is M.false_value:
                compiled_rules = CompileRuleChain(compiled_rules, registry)()
        self.result = self._filter(compiled_rules, current)
        super().__init__(inputs=M.Pair(rules, M.Pair(current, M.Pair(registry, M.EmptyList))), results=self.result)

    def _rule_anchor(self, rule):
        premises = RulePremises(rule)()
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return RulePattern(rule)()
        if RuleIsUnary(rule)() is M.truth_value:
            return RulePattern(rule)()
        return ChooseRuleAnchor(self._anchor_heuristic, rule, self.current, self.registry, self._knowledge_head_index)()

    def _knowledge_has_ground_fact(self, term):
        if M.IdentityCompare(self._knowledge_exact_trie, M.EmptyList)() is M.false_value:
            return K.KnowledgeTrieHasFact(self._knowledge_exact_trie, term, self.registry)()
        facts = KnowledgeFacts(self.current)()
        while M.IdentityCompare(facts, M.EmptyList)() is M.false_value:
            if M.TermEqual(M.Head(facts)(), term)() is M.truth_value:
                return M.truth_value
            facts = M.Tail(facts)()
        return M.false_value

    def _rule_has_missing_required_premise_head(self, rule):
        premises = RulePremises(rule)()
        while M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
            premise = M.Head(premises)()
            if IsVarPattern(premise)() is M.truth_value:
                premises = M.Tail(premises)()
                continue
            if ContainsVar(premise)() is M.false_value:
                if self._knowledge_has_ground_fact(premise) is M.false_value:
                    return M.truth_value
                premises = M.Tail(premises)()
                continue
            if M.IdentityCompare(K.KnowledgeHeadIndexBucket(self._knowledge_head_index, premise, self.registry)(), M.EmptyList)() is M.truth_value:
                return M.truth_value
            premises = M.Tail(premises)()
        return M.false_value

    def _anchor_matches_facts(self, anchor, facts):
        if M.IdentityCompare(anchor, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        next_count_pair = M.Succ(self._last_anchor_match_attempts, self.registry)()
        self._last_anchor_match_attempts = M.Head(next_count_pair)()
        self.registry = M.Head(M.Tail(next_count_pair)())()
        fact = M.Head(facts)()
        match = M.Match(anchor, fact)()
        if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
            return M.truth_value
        return self._anchor_matches_facts(anchor, M.Tail(facts)())

    def _rule_head_applicable(self, rule, current):
        if IsKnowledge(current)() is M.truth_value:
            premises = RulePremises(rule)()
            if M.IdentityCompare(self._knowledge_head_index, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
                    if self._rule_has_missing_required_premise_head(rule) is M.truth_value:
                        _debug(
                            "filter-applicable: rule-index="
                            + M.PrettyTerm(self._probe_rule_index, self.registry)()
                            + " anchor=<skipped:no-head> anchor-s=0.000 bucket-s=0.000 bucket-size=0 match-s=0.000 attempts=0 admitted=no"
                        )
                        return M.false_value
            anchor_started_at = time.time()
            anchor = self._rule_anchor(rule)
            after_anchor = time.time()
            facts = KnowledgeFacts(current)()
            bucket_size = M.Zero
            if M.IdentityCompare(self._knowledge_head_index, M.EmptyList)() is M.false_value:
                if IsVarPattern(anchor)() is M.false_value:
                    bucket_size = K.KnowledgeHeadIndexBucketSize(self._knowledge_head_index, anchor, self.registry)()
                    facts = K.KnowledgeHeadIndexBucket(self._knowledge_head_index, anchor, self.registry)()
            after_bucket_lookup = time.time()
            if M.IdentityCompare(self._knowledge_head_index, M.EmptyList)() is M.truth_value:
                if M.IdentityCompare(facts, M.EmptyList)() is M.false_value:
                    bucket_count_pair = M.Count(facts, self.registry)()
                    bucket_size = M.Head(bucket_count_pair)()
                    self.registry = M.Head(M.Tail(bucket_count_pair)())()
            self._last_anchor_match_attempts = M.Zero
            match_started_at = time.time()
            if ContainsVar(anchor)() is M.false_value:
                admitted = self._knowledge_has_ground_fact(anchor)
            else:
                admitted = self._anchor_matches_facts(anchor, facts)
            after_match = time.time()
            if admitted is M.truth_value:
                admitted_text = "yes"
            else:
                admitted_text = "no"
            _debug(
                "filter-applicable: rule-index="
                + M.PrettyTerm(self._probe_rule_index, self.registry)()
                + " anchor="
                + _debug_term(anchor, self.registry)
                + " anchor-s="
                + "{:.3f}".format(after_anchor - anchor_started_at)
                + " bucket-s="
                + "{:.3f}".format(after_bucket_lookup - after_anchor)
                + " bucket-size="
                + M.PrettyTerm(bucket_size, self.registry)()
                + " match-s="
                + "{:.3f}".format(after_match - match_started_at)
                + " attempts="
                + M.PrettyTerm(self._last_anchor_match_attempts, self.registry)()
                + " admitted="
                + admitted_text
            )
            return admitted
        pattern = RulePattern(rule)()
        if IsVarPattern(pattern)() is M.truth_value:
            return M.truth_value
        p_head = TermHead(pattern, self.registry)()
        c_head = TermHead(current, self.registry)()
        if M.AndAtom(
            M.IdentityCompare(p_head, M.EmptyList)(),
            M.IdentityCompare(c_head, M.EmptyList)(),
        )() is M.truth_value:
            match = M.Match(pattern, current)()
            if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
                return M.truth_value
            return M.false_value
        if M.OrAtom(
            M.IdentityCompare(p_head, M.EmptyList)(),
            M.IdentityCompare(c_head, M.EmptyList)(),
        )() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(p_head, c_head)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _filter(self, rules, current):
        if M.Compare(rules, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        r = M.Head(rules)()
        rest = M.Tail(rules)()
        admitted = self._rule_head_applicable(r, current)
        next_index_pair = M.Succ(self._probe_rule_index, self.registry)()
        self._probe_rule_index = M.Head(next_index_pair)()
        self.registry = M.Head(M.Tail(next_index_pair)())()
        if admitted is M.truth_value:
            return M.Pair(r, self._filter(rest, current))
        return self._filter(rest, current)

    def __call__(self):
        return self.result


class GoalHeadApplicableRuleBuckets(M.Edge):
    def __init__(self, rules, current, goal, registry, knowledge_head_index=None):
        started_at = time.time()
        self.registry = registry
        self._knowledge_head_index = M.EmptyList
        if knowledge_head_index is None:
            if IsKnowledge(current)() is M.truth_value:
                self._knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, KnowledgeFacts(current)(), self.registry)()
        else:
            self._knowledge_head_index = knowledge_head_index
        buckets = self._partition(rules, goal, M.EmptyList, M.EmptyList)
        after_partition = time.time()
        _debug("goal-head-buckets: after partition in " + "{:.3f}".format(after_partition - started_at) + "s")
        goal_bucket = M.Reverse(M.Head(buckets)())()
        other_bucket = M.Reverse(M.Head(M.Tail(buckets)())())()
        after_reverse = time.time()
        _debug("goal-head-buckets: after reverse in " + "{:.3f}".format(after_reverse - after_partition) + "s total=" + "{:.3f}".format(after_reverse - started_at) + "s")
        self.result = M.Pair(goal_bucket, M.Pair(other_bucket, M.EmptyList))
        super().__init__(inputs=M.Pair(rules, M.Pair(current, M.Pair(goal, M.Pair(registry, M.EmptyList)))), results=self.result)

    def _replacement_matches_goal_head(self, rule, goal):
        r_head = TermHead(RuleReplacement(rule)(), self.registry)()
        g_head = TermHead(goal, self.registry)()
        if M.IdentityCompare(r_head, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(g_head, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(r_head, g_head)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _partition(self, rules, goal, goal_acc, other_acc):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return M.Pair(goal_acc, M.Pair(other_acc, M.EmptyList))
        rule = M.Head(rules)()
        rest = M.Tail(rules)()
        toward_goal = self._replacement_matches_goal_head(rule, goal)
        if toward_goal is M.truth_value:
            return self._partition(rest, goal, M.Pair(rule, goal_acc), other_acc)
        return self._partition(rest, goal, goal_acc, M.Pair(rule, other_acc))

    def __call__(self):
        return self.result


class FilterApplicableRulesShard(M.Edge):
    def __init__(self, rules, current, knowledge_head_index, registry, knowledge_exact_trie=None):
        self.result = FilterApplicableRules(rules, current, registry, knowledge_head_index, knowledge_exact_trie)()
        super().__init__(
            inputs=M.Pair(rules, M.Pair(current, M.Pair(knowledge_head_index, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FilterApplicableRulesWithIndex(M.Edge):
    def __init__(self, rules, current, knowledge_head_index, registry, knowledge_exact_trie=None):
        self.result = FilterApplicableRules(rules, current, registry, knowledge_head_index, knowledge_exact_trie)()
        super().__init__(
            inputs=M.Pair(rules, M.Pair(current, M.Pair(knowledge_head_index, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalHeadApplicableRuleBucketsWithIndex(M.Edge):
    def __init__(self, rules, current, goal, knowledge_head_index, registry):
        self.result = GoalHeadApplicableRuleBuckets(rules, current, goal, registry, knowledge_head_index)()
        super().__init__(
            inputs=M.Pair(rules, M.Pair(current, M.Pair(goal, M.Pair(knowledge_head_index, M.Pair(registry, M.EmptyList))))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GoalHeadRuleBuckets(M.Edge):
    def __init__(self, rules, current, goal, registry, knowledge_head_index=None):
        applicable = FilterApplicableRules(rules, current, registry, knowledge_head_index)()
        self.result = GoalHeadApplicableRuleBuckets(applicable, current, goal, registry, knowledge_head_index)()
        super().__init__(inputs=M.Pair(rules, M.Pair(current, M.Pair(goal, M.Pair(registry, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class GoalHeadRuleOrdererWithIndex(M.Edge):
    def __init__(self, rules, current, goal, knowledge_head_index, knowledge_exact_trie, registry, prepared_entries=None):
        self.registry = registry
        self._knowledge_head_index = knowledge_head_index
        self._knowledge_exact_trie = knowledge_exact_trie
        self._knowledge_ground_fact_cache = M.EmptyList
        self._premise_bucket_cache = M.EmptyList
        self._premise_ready_cache = M.EmptyList
        if IsKnowledge(current)() is M.truth_value:
            self._all_facts = KnowledgeFacts(current)()
        else:
            self._all_facts = M.Pair(current, M.EmptyList)
        entries = prepared_entries
        if entries is None:
            entries = self._entries(rules)
        self.result = self._sort(entries)
        super().__init__(
            inputs=M.Pair(rules, M.Pair(current, M.Pair(goal, M.Pair(knowledge_head_index, M.Pair(knowledge_exact_trie, M.Pair(registry, M.EmptyList)))))),
            results=self.result,
        )

    def _premise_matches_facts(self, premise, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        match = M.Match(premise, M.Head(facts)())()
        if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.truth_value:
            return M.truth_value
        return self._premise_matches_facts(premise, M.Tail(facts)())

    def _knowledge_has_ground_fact(self, term):
        term_key = M.ExactKey(term, self.registry)()
        cache_cursor = self._knowledge_ground_fact_cache
        while M.IdentityCompare(cache_cursor, M.EmptyList)() is M.false_value:
            cache_entry = M.Head(cache_cursor)()
            if M.TermEqual(M.Head(cache_entry)(), term_key)() is M.truth_value:
                return M.Head(M.Tail(cache_entry)())()
            cache_cursor = M.Tail(cache_cursor)()
        result = M.false_value
        if M.IdentityCompare(self._knowledge_exact_trie, M.EmptyList)() is M.false_value:
            result = K.KnowledgeTrieHasFact(self._knowledge_exact_trie, term, self.registry)()
        else:
            facts = self._all_facts
            while M.IdentityCompare(facts, M.EmptyList)() is M.false_value:
                if M.TermEqual(M.Head(facts)(), term)() is M.truth_value:
                    result = M.truth_value
                    facts = M.EmptyList
                else:
                    facts = M.Tail(facts)()
        self._knowledge_ground_fact_cache = M.Pair(
            M.Pair(term_key, M.Pair(result, M.EmptyList)),
            self._knowledge_ground_fact_cache,
        )
        return result

    def _premise_ready(self, premise):
        premise_key = M.ExactKey(premise, self.registry)()
        cache_cursor = self._premise_ready_cache
        while M.IdentityCompare(cache_cursor, M.EmptyList)() is M.false_value:
            cache_entry = M.Head(cache_cursor)()
            if M.TermEqual(M.Head(cache_entry)(), premise_key)() is M.truth_value:
                return M.Head(M.Tail(cache_entry)())()
            cache_cursor = M.Tail(cache_cursor)()
        result = M.false_value
        if IsVarPattern(premise)() is M.truth_value:
            if M.IdentityCompare(self._all_facts, M.EmptyList)() is M.false_value:
                result = M.truth_value
        elif ContainsVar(premise)() is M.false_value:
            result = self._knowledge_has_ground_fact(premise)
        else:
            bucket = M.EmptyList
            bucket_cursor = self._premise_bucket_cache
            while M.IdentityCompare(bucket_cursor, M.EmptyList)() is M.false_value:
                bucket_entry = M.Head(bucket_cursor)()
                if M.TermEqual(M.Head(bucket_entry)(), premise_key)() is M.truth_value:
                    bucket = M.Head(M.Tail(bucket_entry)())()
                    bucket_cursor = M.EmptyList
                else:
                    bucket_cursor = M.Tail(bucket_cursor)()
            if M.IdentityCompare(bucket, M.EmptyList)() is M.truth_value:
                bucket = K.KnowledgeHeadIndexBucket(self._knowledge_head_index, premise, self.registry)()
                self._premise_bucket_cache = M.Pair(
                    M.Pair(premise_key, M.Pair(bucket, M.EmptyList)),
                    self._premise_bucket_cache,
                )
            result = self._premise_matches_facts(
                premise,
                bucket,
            )
        self._premise_ready_cache = M.Pair(
            M.Pair(premise_key, M.Pair(result, M.EmptyList)),
            self._premise_ready_cache,
        )
        return result

    def _entry_rule(self, entry):
        return entry[0]

    def _entry_ready(self, entry):
        return entry[1]

    def _entry_unmatched(self, entry):
        return entry[2]

    def _entry_total(self, entry):
        return entry[3]

    def _make_entry(self, rule):
        premise_meta = CompiledRulePremiseMeta(rule)()
        ready_count = 0
        total_count = 0
        while M.IdentityCompare(premise_meta, M.EmptyList)() is M.false_value:
            entry = M.Head(premise_meta)()
            premise = M.Head(entry)()
            total_count = total_count + 1
            if self._premise_ready(premise) is M.truth_value:
                ready_count = ready_count + 1
            premise_meta = M.Tail(premise_meta)()
        if total_count == 0:
            premises = RulePremises(rule)()
            while M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
                total_count = total_count + 1
                if self._premise_ready(M.Head(premises)()) is M.truth_value:
                    ready_count = ready_count + 1
                premises = M.Tail(premises)()
        return (rule, ready_count, total_count - ready_count, total_count)

    def _entries(self, rules):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(self._make_entry(M.Head(rules)()), self._entries(M.Tail(rules)()))

    def _prefer_left(self, left_entry, right_entry):
        left_ready = self._entry_ready(left_entry)
        right_ready = self._entry_ready(right_entry)
        left_unmatched = self._entry_unmatched(left_entry)
        right_unmatched = self._entry_unmatched(right_entry)
        left_total = self._entry_total(left_entry)
        right_total = self._entry_total(right_entry)
        if left_unmatched == 0:
            if right_unmatched != 0:
                return M.truth_value
        else:
            if right_unmatched == 0:
                return M.false_value
        if left_ready != right_ready:
            if left_ready > right_ready:
                return M.truth_value
            return M.false_value
        if left_unmatched != right_unmatched:
            if right_unmatched > left_unmatched:
                return M.truth_value
            return M.false_value
        if left_total != right_total:
            if right_total > left_total:
                return M.truth_value
            return M.false_value
        return M.false_value

    def _insert(self, entry, ordered):
        if M.IdentityCompare(ordered, M.EmptyList)() is M.truth_value:
            return M.Pair(entry, M.EmptyList)
        head_entry = M.Head(ordered)()
        if self._prefer_left(entry, head_entry) is M.truth_value:
            return M.Pair(entry, ordered)
        return M.Pair(head_entry, self._insert(entry, M.Tail(ordered)()))

    def _sort_entries(self, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return self._insert(M.Head(entries)(), self._sort_entries(M.Tail(entries)()))

    def _rules(self, entries):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(self._entry_rule(M.Head(entries)()), self._rules(M.Tail(entries)()))

    def _sort(self, entries):
        return self._rules(self._sort_entries(entries))

    def __call__(self):
        return self.result


class GoalHeadRewriteOrderer(M.Edge):
    def __init__(self, rules, goal, registry):
        self.registry = registry
        buckets = self._bucket(rules, goal, M.EmptyList, M.EmptyList)
        goal_bucket = M.Reverse(M.Head(buckets)())()
        other_bucket = M.Reverse(M.Head(M.Tail(buckets)())())()
        self.result = Append(goal_bucket, other_bucket)()
        super().__init__(inputs=M.Pair(rules, M.Pair(goal, M.Pair(registry, M.EmptyList))), results=self.result)

    def _replacement_matches_goal_head(self, rule, goal):
        r_head = TermHead(RuleReplacement(rule)(), self.registry)()
        g_head = TermHead(goal, self.registry)()
        if M.IdentityCompare(r_head, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(g_head, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(r_head, g_head)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _bucket(self, rules, goal, goal_acc, other_acc):
        if M.Compare(rules, M.EmptyList)() is M.truth_value:
            return M.Pair(goal_acc, M.Pair(other_acc, M.EmptyList))
        r = M.Head(rules)()
        rest = M.Tail(rules)()
        toward_goal = self._replacement_matches_goal_head(r, goal)
        if toward_goal is M.truth_value:
            return self._bucket(rest, goal, M.Pair(r, goal_acc), other_acc)
        return self._bucket(rest, goal, goal_acc, M.Pair(r, other_acc))

    def __call__(self):
        return self.result


class OrderRules(M.Edge):
    def __init__(self, rules, current, goal, heuristic, registry):
        mode = HeuristicRuleOrder(heuristic)()
        if M.IdentityCompare(mode, GoalHeadOrderLabel)() is M.truth_value:
            atom_result = GoalHeadRuleOrderer(rules, current, goal, registry)()
        else:
            atom_result = FilterApplicableRules(rules, current, registry)()
        self.result = atom_result
        super().__init__(inputs=M.Pair(rules, M.Pair(current, M.Pair(goal, M.Pair(heuristic, M.Pair(registry, M.EmptyList))))), results=self.result)

    def __call__(self):
        return self.result


class Step(M.Edge):
    def __init__(self, current, action, next_term, registry):
        # Change B of the snapshot-cost plan: Step no longer registers in
        # the constructor tree. Measured over the e2 proof, the TreeLookup
        # dedup never hit once (10 calls -> 10 entries) while the insert
        # paid TreePatriciaPath tokenization on the largest keys in the
        # system (205-700 tokens each). The readers -- StepCurrent /
        # StepAction / StepNext via GetConstructor -- resolve through the
        # node attribute set here, never through the tree.
        #
        # LOAD-BEARING CONSEQUENCE: .constructor is not serialized, and
        # the registry entry was its only persistent record. Proof
        # runtimes always cold-boot from packs (the invariant behind the
        # sqrt fix, commit 73efb13), so nothing reads step structure
        # after a reload today. Whoever implements snapshot proof-replay
        # must either restore Step registration here or serialize
        # .constructor in the snapshot codec.
        args = M.Pair(current, M.Pair(action, M.Pair(next_term, M.EmptyList)))
        node = M.Atom()
        node.constructor = M.Pair(StepLabel, args)
        self.result = M.Pair(node, M.Pair(registry, M.EmptyList))
        super().__init__(inputs=M.Pair(current, M.Pair(action, M.Pair(next_term, M.Pair(registry, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class StepCurrent(M.Edge):
    def __init__(self, step, registry):
        c = M.GetConstructor(step, registry)()
        if M.IdentityCompare(c, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            args = M.Tail(c)()
            self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(step, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class StepAction(M.Edge):
    def __init__(self, step, registry):
        c = M.GetConstructor(step, registry)()
        if M.IdentityCompare(c, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            args = M.Tail(c)()
            self.result = M.Head(M.Tail(args)())()
        super().__init__(inputs=M.Pair(step, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


StepRule = StepAction


class StepNext(M.Edge):
    def __init__(self, step, registry):
        c = M.GetConstructor(step, registry)()
        if M.IdentityCompare(c, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            args = M.Tail(c)()
            self.result = M.Head(M.Tail(M.Tail(args)())())()
        super().__init__(inputs=M.Pair(step, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class ProofCost(M.Edge):
    def __init__(self, value, steps, theorem_steps, rewrite_steps):
        self.result = M.Pair(
            ProofCostLabel,
            M.Pair(value, M.Pair(steps, M.Pair(theorem_steps, M.Pair(rewrite_steps, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(value, M.Pair(steps, M.Pair(theorem_steps, M.Pair(rewrite_steps, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IsProofCost(M.Edge):
    def __init__(self, x):
        if M.IsPair(x)() is M.false_value:
            atom_result = M.false_value
        else:
            head = M.Head(x)()
            tail = M.Tail(x)()
            if M.IdentityCompare(head, ProofCostLabel)() is M.false_value:
                atom_result = M.false_value
            elif M.IsPair(tail)() is M.false_value:
                atom_result = M.false_value
            else:
                atom_result = M.truth_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(x, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofCostValue(M.Edge):
    def __init__(self, cost):
        self.result = M.Head(M.Tail(cost)())()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofCostSteps(M.Edge):
    def __init__(self, cost):
        self.result = M.Head(M.Tail(M.Tail(cost)())())()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofCostTheoremSteps(M.Edge):
    def __init__(self, cost):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(cost)())())())()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ProofCostRewriteSteps(M.Edge):
    def __init__(self, cost):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(cost)())())())())()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BuildProofCost(M.Edge):
    def __init__(self, steps, registry):
        counts_pair = self._counts(steps, registry)
        counts = M.Head(counts_pair)()
        new_registry = M.Head(M.Tail(counts_pair)())()
        total_steps = M.Head(counts)()
        theorem_steps = M.Head(M.Tail(counts)())()
        rewrite_steps = M.Head(M.Tail(M.Tail(counts)())())()
        self.result = M.Pair(
            ProofCost(total_steps, total_steps, theorem_steps, rewrite_steps)(),
            M.Pair(new_registry, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(steps, M.Pair(registry, M.EmptyList)), results=self.result)

    def _counts(self, steps, registry):
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            zero_counts = M.Pair(M.Zero, M.Pair(M.Zero, M.Pair(M.Zero, M.EmptyList)))
            return M.Pair(zero_counts, M.Pair(registry, M.EmptyList))

        rest_pair = self._counts(M.Tail(steps)(), registry)
        rest_counts = M.Head(rest_pair)()
        reg1 = M.Head(M.Tail(rest_pair)())()

        total_inc_pair = M.Succ(M.Head(rest_counts)(), reg1)()
        total_steps = M.Head(total_inc_pair)()
        reg2 = M.Head(M.Tail(total_inc_pair)())()
        theorem_steps = M.Head(M.Tail(rest_counts)())()
        rewrite_steps = M.Head(M.Tail(M.Tail(rest_counts)())())()
        action = StepAction(M.Head(steps)(), reg2)()

        if IsTheoremAction(action)() is M.truth_value:
            theorem_inc_pair = M.Succ(theorem_steps, reg2)()
            theorem_steps = M.Head(theorem_inc_pair)()
            reg2 = M.Head(M.Tail(theorem_inc_pair)())()
        elif IsRewriteAction(action)() is M.truth_value:
            rewrite_inc_pair = M.Succ(rewrite_steps, reg2)()
            rewrite_steps = M.Head(rewrite_inc_pair)()
            reg2 = M.Head(M.Tail(rewrite_inc_pair)())()

        counts = M.Pair(total_steps, M.Pair(theorem_steps, M.Pair(rewrite_steps, M.EmptyList)))
        return M.Pair(counts, M.Pair(reg2, M.EmptyList))

    def __call__(self):
        return self.result


class Derivation(M.Edge):
    def __init__(self, steps, cost, registry):
        args = M.Pair(steps, M.Pair(cost, M.EmptyList))
        key = M.Pair(DerivationLabel, args)
        existing = M.TreeLookup(registry, key, registry)()
        if M.IdentityCompare(existing, M.EmptyList)() is M.truth_value:
            node = M.Atom()
            constructed = M.ConstructedBy(node, DerivationLabel, args, registry)()
            new_registry = M.Head(M.Tail(constructed)())()
        else:
            node = existing
            new_registry = registry
        self.result = M.Pair(node, M.Pair(new_registry, M.EmptyList))
        super().__init__(inputs=M.Pair(steps, M.Pair(cost, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class DerivationSteps(M.Edge):
    def __init__(self, d, registry):
        c = M.GetConstructor(d, registry)()
        if M.IdentityCompare(c, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            args = M.Tail(c)()
            if M.IsPair(args)() is M.truth_value:
                rest = M.Tail(args)()
                if (
                    M.IsPair(rest)() is M.truth_value
                    and M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.truth_value
                    and IsProofCost(M.Head(rest)())() is M.truth_value
                ):
                    self.result = M.Head(args)()
                else:
                    self.result = args
            else:
                self.result = args
        super().__init__(inputs=M.Pair(d, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class DerivationCost(M.Edge):
    def __init__(self, d, registry):
        c = M.GetConstructor(d, registry)()
        if M.IdentityCompare(c, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        else:
            args = M.Tail(c)()
            if M.IsPair(args)() is M.truth_value:
                rest = M.Tail(args)()
                if (
                    M.IsPair(rest)() is M.truth_value
                    and M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.truth_value
                    and IsProofCost(M.Head(rest)())() is M.truth_value
                ):
                    self.result = M.Pair(M.Head(rest)(), M.Pair(registry, M.EmptyList))
                else:
                    self.result = BuildProofCost(args, registry)()
            else:
                self.result = BuildProofCost(args, registry)()
        super().__init__(inputs=M.Pair(d, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class IsDerivation(M.Edge):
    def __init__(self, x, registry):
        c = M.GetConstructor(x, registry)()
        if M.IdentityCompare(c, M.EmptyList)() is M.truth_value:
            atom_result = M.false_value
        else:
            label = M.Head(c)()
            atom_result = M.truth_value if M.IdentityCompare(label, DerivationLabel)() is M.truth_value else M.false_value
        self.result = atom_result
        super().__init__(inputs=M.Pair(x, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class DerivationStart(M.Edge):
    def __init__(self, d, registry):
        steps = DerivationSteps(d, registry)()
        if M.Compare(steps, M.EmptyList)() is M.truth_value:
            atom_result = M.EmptyList
        else:
            atom_result = StepCurrent(M.Head(steps)(), registry)()
        self.result = atom_result
        super().__init__(inputs=M.Pair(d, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class DerivationEnd(M.Edge):
    def __init__(self, d, registry):
        steps = DerivationSteps(d, registry)()
        self.registry = registry
        self.result = self._end(steps)
        super().__init__(inputs=M.Pair(d, M.Pair(registry, M.EmptyList)), results=self.result)

    def _end(self, steps):
        if M.Compare(steps, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rest = M.Tail(steps)()
        if M.Compare(rest, M.EmptyList)() is M.truth_value:
            return StepNext(M.Head(steps)(), self.registry)()
        return self._end(rest)

    def __call__(self):
        return self.result


class DerivationEntryStart(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(entry)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DerivationEntryGoal(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DerivationEntryProof(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LookupDerivation(M.Edge):
    def __init__(self, start, goal, tree):
        self.result = self._lookup(M.TreeEntries(tree)(), start, goal)
        super().__init__(inputs=M.Pair(start, M.Pair(goal, M.Pair(tree, M.EmptyList))), results=self.result)

    def _lookup(self, entries, start, goal):
        if M.IdentityCompare(entries, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        item = M.Head(entries)()
        entry = M.Head(M.Tail(item)())()
        entry_start = DerivationEntryStart(entry)()
        entry_goal = DerivationEntryGoal(entry)()
        same_start = M.TermEqual(entry_start, start)()
        same_goal = M.TermEqual(entry_goal, goal)()
        if M.AndAtom(same_start, same_goal)() is M.truth_value:
            return DerivationEntryProof(entry)()
        return self._lookup(M.Tail(entries)(), start, goal)

    def __call__(self):
        return self.result


class StoreDerivation(M.Edge):
    def __init__(self, start, goal, derivation, tree, registry):
        entry = M.Pair(start, M.Pair(goal, M.Pair(derivation, M.EmptyList)))
        key = M.Atom()
        new_tree = M.TreeInsert(tree, key, entry, registry)()
        self.result = M.Pair(new_tree, M.EmptyList)
        super().__init__(inputs=M.Pair(start, M.Pair(goal, M.Pair(derivation, M.Pair(tree, M.Pair(registry, M.EmptyList))))), results=self.result)

    def __call__(self):
        return self.result


class InstantiateDerivation(M.Edge):
    def __init__(self, start, plan, bindings, registry):
        pair = BuildDerivation(start, plan, registry, bindings)()
        self.result = pair
        super().__init__(inputs=M.Pair(start, M.Pair(plan, M.Pair(bindings, M.Pair(registry, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class PrettyRule(M.Edge):
    def __init__(self, rule, term_registry):
        premises = RulePremises(rule)()
        replacement = RuleReplacement(rule)()
        if RuleIsUnary(rule)() is M.truth_value:
            left_text = M.PrettyTerm(M.Head(premises)(), term_registry)()
        else:
            left_text = "[" + self._show_premises(premises, term_registry) + "]"
        self.result = left_text + "  ->  " + M.PrettyTerm(replacement, term_registry)()
        super().__init__(inputs=M.Pair(rule, M.Pair(term_registry, M.EmptyList)), results=M.EmptyList)

    def _show_premises(self, premises, registry):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return ""
        premise = M.Head(premises)()
        rest = M.Tail(premises)()
        here = M.PrettyTerm(premise, registry)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return here
        return here + ", " + self._show_premises(rest, registry)

    def __call__(self):
        return self.result


class PrettyRuleChain(M.Edge):
    def __init__(self, rules, term_registry):
        self.term_registry = term_registry
        self.result = "[" + self._walk(rules) + "]"
        super().__init__(inputs=M.Pair(rules, M.Pair(term_registry, M.EmptyList)), results=M.EmptyList)

    def _walk(self, rules):
        if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
            return ""
        r = M.Head(rules)()
        rest = M.Tail(rules)()
        here = PrettyRule(r, self.term_registry)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return here
        return here + ", " + self._walk(rest)

    def __call__(self):
        return self.result


class PrettyPath(M.Edge):
    def __init__(self, path, registry):
        self.registry = registry
        self.result = self._show(path)
        super().__init__(inputs=M.Pair(path, M.Pair(registry, M.EmptyList)), results=M.EmptyList)

    def _show(self, path):
        if M.IdentityCompare(path, M.EmptyList)() is M.truth_value:
            return "root"
        segment = M.Head(path)()
        rest = M.Tail(path)()
        here = "head" if M.NatEq(segment, M.Zero, self.registry)() is M.truth_value else "tail"
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return here
        return here + "." + self._show(rest)

    def __call__(self):
        return self.result


class GoalHeadRuleOrderer(M.Edge):
    def __init__(self, rules, current, goal, registry, knowledge_head_index=None):
        buckets = GoalHeadRuleBuckets(rules, current, goal, registry, knowledge_head_index)()
        goal_bucket = M.Head(buckets)()
        other_bucket = M.Head(M.Tail(buckets)())()
        self.result = Append(goal_bucket, other_bucket)()
        super().__init__(inputs=M.Pair(rules, M.Pair(current, M.Pair(goal, M.Pair(registry, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class PrettyAction(M.Edge):
    def __init__(self, action, registry):
        rule = ActionRule(action)()
        if IsRewriteAction(action)() is M.truth_value:
            path = ActionPath(action)()
            self.result = "rewrite " + PrettyRule(rule, registry)() + " at " + PrettyPath(path, registry)()
        elif IsTheoremAction(action)() is M.truth_value:
            self.result = "apply " + PrettyRule(rule, registry)()
        else:
            self.result = PrettyRule(rule, registry)()
        super().__init__(inputs=M.Pair(action, M.Pair(registry, M.EmptyList)), results=M.EmptyList)

    def __call__(self):
        return self.result


class PrettyPlanItem(M.Edge):
    def __init__(self, x, registry):
        if IsDerivation(x, registry)() is M.truth_value:
            start = DerivationStart(x, registry)()
            end = DerivationEnd(x, registry)()
            self.result = "CachedDerivation(" + M.PrettyTerm(start, registry)() + " -> " + M.PrettyTerm(end, registry)() + ")"
        elif M.OrAtom(IsTheoremAction(x)(), IsRewriteAction(x)())() is M.truth_value:
            self.result = PrettyAction(x, registry)()
        elif M.IsEdge(x, registry)() is M.truth_value:
            self.result = PrettyRule(x, registry)()
        else:
            self.result = M.PrettyTerm(x, registry)()
        super().__init__(inputs=M.Pair(x, M.Pair(registry, M.EmptyList)), results=M.EmptyList)

    def __call__(self):
        return self.result


class PrettyPlanChain(M.Edge):
    def __init__(self, plan, registry):
        self.registry = registry
        self.result = "[" + self._walk(plan) + "]"
        super().__init__(inputs=M.Pair(plan, M.Pair(registry, M.EmptyList)), results=M.EmptyList)

    def _walk(self, plan):
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            return ""
        h = M.Head(plan)()
        t = M.Tail(plan)()
        here = PrettyPlanItem(h, self.registry)()
        if M.IdentityCompare(t, M.EmptyList)() is M.truth_value:
            return here
        return here + ", " + self._walk(t)

    def __call__(self):
        return self.result


class RewriteHere(M.Edge):
    def __init__(self, rule, target):
        if RuleIsUnary(rule)() is M.false_value:
            self.result = target
        else:
            match = M.Match(RulePattern(rule)(), target)()
            flag = M.Head(match)()
            bindings = M.Tail(match)()
            if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
                inst = M.Instantiate(RuleReplacement(rule)(), bindings)()
                self.result = M.Head(inst)()
            else:
                self.result = target
        super().__init__(inputs=M.Pair(rule, M.Pair(target, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class RewriteAtPath(M.Edge):
    def __init__(self, rule, target, path, registry):
        self.registry = registry
        _debug(
            "rewrite-at-path: rule="
            + PrettyRule(rule, registry)()
            + " path="
            + PrettyPath(path, registry)()
            + " target="
            + _debug_term(target, registry)
        )
        self.result = self._rewrite(rule, target, path)
        _debug("rewrite-at-path result: " + _debug_term(self.result, registry))
        super().__init__(inputs=M.Pair(rule, M.Pair(target, M.Pair(path, M.Pair(registry, M.EmptyList)))), results=self.result)

    def _rewrite(self, rule, target, path):
        if M.IdentityCompare(path, M.EmptyList)() is M.truth_value:
            return RewriteHere(rule, target)()
        if M.IsPair(target)() is M.false_value:
            return target
        step = M.Head(path)()
        rest = M.Tail(path)()
        if M.NatEq(step, M.Zero, self.registry)() is M.truth_value:
            new_head = self._rewrite(rule, M.Head(target)(), rest)
            return M.Pair(new_head, M.Tail(target)())
        new_tail = self._rewrite(rule, M.Tail(target)(), rest)
        return M.Pair(M.Head(target)(), new_tail)

    def __call__(self):
        return self.result


class BuildDerivation(M.Edge):
    def __init__(self, start, plan, registry, bindings=None):
        if bindings is None:
            bindings = M.EmptyList
        self.bindings = bindings
        self.registry = registry
        self._knowledge_head_index = M.EmptyList
        self._match_memo = M.EmptyTree
        if _derivation_replay_debug_enabled() is M.truth_value:
            _debug("build-derivation: start=" + _debug_term(start, registry))
        if _derivation_replay_debug_enabled() is M.truth_value:
            _debug("build-derivation: plan=" + PrettyPlanChain(plan, registry)())
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        else:
            pair = self._build(start, plan, registry)
            steps = M.Head(pair)()
            new_registry = M.Head(M.Tail(pair)())()
            cost_pair = BuildProofCost(steps, new_registry)()
            cost = M.Head(cost_pair)()
            new_registry = M.Head(M.Tail(cost_pair)())()
            deriv_pair = Derivation(steps, cost, new_registry)()
            self.result = deriv_pair
        if _derivation_replay_debug_enabled() is M.truth_value:
            _debug("build-derivation: finished")
        super().__init__(inputs=M.Pair(start, M.Pair(plan, M.Pair(bindings, M.Pair(registry, M.EmptyList)))), results=self.result)

    def _knowledge_has_fact(self, facts, target):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if M.Compare(fact, target)() is M.truth_value:
            return M.truth_value
        return self._knowledge_has_fact(M.Tail(facts)(), target)

    def _match_premises(self, rule, premises, facts, bindings):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, bindings)
        premise = M.Head(premises)()
        rest = M.Tail(premises)()
        candidate_facts = facts
        if M.IdentityCompare(self._knowledge_head_index, M.EmptyList)() is M.false_value:
            if IsVarPattern(premise)() is M.false_value:
                candidate_facts = K.KnowledgeHeadIndexBucket(self._knowledge_head_index, premise, self.registry)()
        if M.IdentityCompare(bindings, M.EmptyList)() is M.truth_value:
            memo_hit = K.MatchMemoLookup(self._match_memo, rule, premises, candidate_facts, self.registry)()
            if M.IdentityCompare(memo_hit, M.EmptyList)() is M.false_value:
                return memo_hit
        result = self._match_premise_against_facts(rule, premise, rest, candidate_facts, facts, bindings)
        if M.IdentityCompare(bindings, M.EmptyList)() is M.truth_value:
            self._match_memo = K.MatchMemoStore(self._match_memo, rule, premises, candidate_facts, result, self.registry)()
        return result

    def _match_premise_against_facts(self, rule, premise, rest_premises, facts, all_facts, bindings):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)

        fact = M.Head(facts)()
        match = M.Match(premise, fact)()
        flag = M.Head(match)()
        bound = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            merged = M.MergeBindings(bindings, bound)()
            merged_flag = M.Head(merged)()
            merged_bindings = M.Tail(merged)()
            if M.IdentityCompare(merged_flag, M.truth_value)() is M.truth_value:
                rest_result = self._match_premises(rule, rest_premises, all_facts, merged_bindings)
                if M.IdentityCompare(M.Head(rest_result)(), M.truth_value)() is M.truth_value:
                    return rest_result

        return self._match_premise_against_facts(rule, premise, rest_premises, M.Tail(facts)(), all_facts, bindings)

    def _premises_satisfied_by_bindings(self, premises, facts, bindings):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.truth_value
        premise = M.Head(premises)()
        instantiated = M.Instantiate(premise, bindings)()
        concrete_premise = M.Head(instantiated)()
        has_fact = self._knowledge_has_fact(facts, concrete_premise)
        if M.IdentityCompare(has_fact, M.false_value)() is M.truth_value:
            return M.false_value
        return self._premises_satisfied_by_bindings(M.Tail(premises)(), facts, bindings)

    def _apply_theorem_rule_to_knowledge(self, rule, current, registry):
        if ReplacementIsFactList(rule)() is M.truth_value:
            facts = KnowledgeFacts(current)()
            if M.IdentityCompare(self.bindings, M.EmptyList)() is M.false_value:
                return ApplyKnowledgeRewrite(current, rule, self.bindings)()
            bindings_pair = JoinPremises(RulePremises(rule)(), facts, M.EmptyList)()
            if M.IdentityCompare(bindings_pair, M.EmptyList)() is M.truth_value:
                return current
            return ApplyKnowledgeRewrite(current, rule, M.Head(bindings_pair)())()
        facts = KnowledgeFacts(current)()
        self._knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, facts, registry)()
        self._match_memo = M.EmptyTree
        bindings_are_empty = M.IdentityCompare(self.bindings, M.EmptyList)()
        if bindings_are_empty is M.false_value:
            _debug("apply-action: theorem replay using concrete bindings")
            if self._premises_satisfied_by_bindings(RulePremises(rule)(), facts, self.bindings) is M.false_value:
                _debug("apply-action: concrete theorem premises missing")
                return current
            inst = M.Instantiate(RuleReplacement(rule)(), self.bindings)()
            conclusion = M.CanonicalArithmeticTerm(M.Head(inst)(), registry)()
            if self._knowledge_has_fact(facts, conclusion) is M.truth_value:
                _debug("apply-action: concrete theorem conclusion already known")
                return current
            _debug("apply-action: concrete theorem conclusion added")
            return Knowledge(M.Pair(conclusion, facts))()

        bindings_pair = self._match_premises(rule, RulePremises(rule)(), facts, self.bindings)
        bindings_flag = M.Head(bindings_pair)()
        bindings = M.Tail(bindings_pair)()
        if M.IdentityCompare(bindings_flag, M.truth_value)() is M.false_value:
            return current

        inst = M.Instantiate(RuleReplacement(rule)(), bindings)()
        conclusion = M.CanonicalArithmeticTerm(M.Head(inst)(), registry)()
        if self._knowledge_has_fact(facts, conclusion) is M.truth_value:
            return current
        return NormalizeKnowledge(Knowledge(M.Pair(conclusion, facts))(), registry)()

    def _apply_theorem_rule_at_root(self, rule, current, registry):
        if IsKnowledge(current)() is M.truth_value:
            return self._apply_theorem_rule_to_knowledge(rule, current, registry)
        if RuleIsUnary(rule)() is M.false_value:
            return current
        pattern = RulePattern(rule)()
        replacement = RuleReplacement(rule)()
        match = M.Match(pattern, current)()
        flag = M.Head(match)()
        binds = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            merged = M.MergeBindings(self.bindings, binds)()
            merged_flag = M.Head(merged)()
            merged_bindings = M.Tail(merged)()
            if M.IdentityCompare(merged_flag, M.truth_value)() is M.truth_value:
                inst = M.Instantiate(replacement, merged_bindings)()
                return M.CanonicalArithmeticTerm(M.Head(inst)(), registry)()
        return current

    def _apply_action(self, action, current, registry):
        debug_replay = _derivation_replay_action_debug_enabled()
        if debug_replay is M.truth_value:
            _debug("apply-action: current=" + _debug_term(current, registry))
            if IsTheoremAction(action)() is M.truth_value:
                if RuleIsUnary(ActionRule(action)())() is M.false_value:
                    _debug("apply-action: apply multi-premise theorem rule")
                else:
                    _debug("apply-action: " + PrettyAction(action, registry)())
            else:
                _debug("apply-action: " + PrettyAction(action, registry)())
        if IsTheoremAction(action)() is M.truth_value:
            previous_bindings = self.bindings
            action_bindings = ActionBindings(action)()
            if M.IdentityCompare(action_bindings, M.EmptyList)() is M.false_value:
                self.bindings = action_bindings
            invariant_premise = M.EmptyList
            remaining_premises = RulePremises(ActionRule(action)())()
            while M.IdentityCompare(remaining_premises, M.EmptyList)() is M.false_value:
                premise = M.Head(remaining_premises)()
                if M.IsPair(premise)() is M.truth_value:
                    if M.IdentityCompare(M.Head(premise)(), InvariantLabel)() is M.truth_value:
                        invariant_premise = M.Head(M.Instantiate(premise, self.bindings)())()
                remaining_premises = M.Tail(remaining_premises)()
            result = self._apply_theorem_rule_at_root(ActionRule(action)(), current, registry)
            if debug_replay is M.truth_value:
                if M.Compare(result, current)() is M.false_value:
                    if M.IdentityCompare(invariant_premise, M.EmptyList)() is M.false_value:
                        _debug("apply-action: used invariant premise " + _debug_term(invariant_premise, registry))
            self.bindings = previous_bindings
            if debug_replay is M.truth_value:
                _debug("apply-action result=" + _debug_term(result, registry))
            return result
        if IsRewriteAction(action)() is M.truth_value:
            result = RewriteAtPath(ActionRule(action)(), current, ActionPath(action)(), registry)()
            if debug_replay is M.truth_value:
                _debug("apply-action result=" + _debug_term(result, registry))
            return result
        result = self._apply_theorem_rule_at_root(action, current, registry)
        if debug_replay is M.truth_value:
            _debug("apply-action result=" + _debug_term(result, registry))
        return result

    def _build(self, current, plan, registry):
        if M.IdentityCompare(plan, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        item = M.Head(plan)()
        rest = M.Tail(plan)()
        if IsDerivation(item, registry)() is M.truth_value:
            cached_steps = DerivationSteps(item, registry)()
            cached_end = DerivationEnd(item, registry)()
            rest_pair = self._build(cached_end, rest, registry)
            rest_steps = M.Head(rest_pair)()
            reg2 = M.Head(M.Tail(rest_pair)())()
            return M.Pair(Append(cached_steps, rest_steps)(), M.Pair(reg2, M.EmptyList))
        next_term = self._apply_action(item, current, registry)
        step_pair = Step(current, item, next_term, registry)()
        step_node = M.Head(step_pair)()
        reg1 = M.Head(M.Tail(step_pair)())()
        rest_pair = self._build(next_term, rest, reg1)
        rest_steps = M.Head(rest_pair)()
        reg2 = M.Head(M.Tail(rest_pair)())()
        return M.Pair(M.Pair(step_node, rest_steps), M.Pair(reg2, M.EmptyList))

    def __call__(self):
        return self.result


class BuildRewriteDerivation(M.Edge):
    def __init__(self, start, plan, registry):
        self.result = BuildDerivation(start, plan, registry)()
        super().__init__(inputs=M.Pair(start, M.Pair(plan, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class ExplainDerivation(M.Edge):
    def __init__(self, derivation, goal, registry):
        self.registry = registry
        self.goal = goal
        if derivation is None:
            self.result = "We were looking for " + M.PrettyTerm(goal, registry)() + ".\nNo derivation was produced (got Python None)."
        elif M.Compare(derivation, M.EmptyList)() is M.truth_value:
            self.result = "We were looking for " + M.PrettyTerm(goal, registry)() + ".\nNo derivation was found."
        else:
            steps = DerivationSteps(derivation, registry)()
            if M.Compare(steps, M.EmptyList)() is M.truth_value:
                self.result = "We found a derivation node, but it contains no steps."
            else:
                first_step = M.Head(steps)()
                start = StepCurrent(first_step, registry)()
                self.result = "We were looking for " + M.PrettyTerm(goal, registry)() + ".\nWe started with " + M.PrettyTerm(start, registry)() + ".\n\n" + self._walk(steps, 1)
        super().__init__(inputs=M.Pair(derivation, M.Pair(goal, M.Pair(registry, M.EmptyList))), results=M.EmptyList)

    def _walk(self, steps, n):
        if M.Compare(steps, M.EmptyList)() is M.truth_value:
            return ""
        s = M.Head(steps)()
        rest = M.Tail(steps)()
        cur = StepCurrent(s, self.registry)()
        action = StepAction(s, self.registry)()
        nxt = StepNext(s, self.registry)()
        line = "Step " + str(n) + ": from " + M.PrettyTerm(cur, self.registry)() + "\n  " + PrettyAction(action, self.registry)() + "\n  get " + M.PrettyTerm(nxt, self.registry)() + "\n\n"
        if M.Compare(rest, M.EmptyList)() is M.truth_value:
            if self._goal_reached(nxt) is M.truth_value:
                return line + "Therefore we reached " + M.PrettyTerm(nxt, self.registry)() + ", so the goal follows."
            return line + "We ended at " + M.PrettyTerm(nxt, self.registry)() + ", which is not the goal."
        return line + self._walk(rest, n + 1)

    def _knowledge_has_fact(self, facts, target):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if M.Compare(fact, target)() is M.truth_value:
            return M.truth_value
        return self._knowledge_has_fact(M.Tail(facts)(), target)

    def _goal_reached(self, current):
        if IsKnowledge(current)() is M.truth_value:
            return self._knowledge_has_fact(KnowledgeFacts(current)(), self.goal)
        return M.Compare(current, self.goal)()

    def __call__(self):
        return self.result


class TotalCost(M.Edge):
    def __init__(self, value, alpha, beta, proof_value, search_value):
        self.result = M.Pair(
            TotalCostLabel,
            M.Pair(value, M.Pair(alpha, M.Pair(beta, M.Pair(proof_value, M.Pair(search_value, M.EmptyList))))),
        )
        super().__init__(
            inputs=M.Pair(value, M.Pair(alpha, M.Pair(beta, M.Pair(proof_value, M.Pair(search_value, M.EmptyList))))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TotalCostValue(M.Edge):
    def __init__(self, cost):
        self.result = M.Head(M.Tail(cost)())()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TotalCostAlpha(M.Edge):
    def __init__(self, cost):
        self.result = M.Head(M.Tail(M.Tail(cost)())())()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TotalCostBeta(M.Edge):
    def __init__(self, cost):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(cost)())())())()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TotalCostProofValue(M.Edge):
    def __init__(self, cost):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(cost)())())())())()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TotalCostSearchValue(M.Edge):
    def __init__(self, cost):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(cost)())())())())())()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BuildTotalCost(M.Edge):
    def __init__(self, proof_cost, search_cost, heuristic, registry):
        from .search import SearchCostValue

        alpha = M.HeuristicAlpha(heuristic)()
        beta = M.HeuristicBeta(heuristic)()
        proof_value = ProofCostValue(proof_cost)()
        search_value = SearchCostValue(search_cost)()
        weighted_proof_pair = M.Multiply(alpha, proof_value, registry)()
        weighted_proof = M.Head(weighted_proof_pair)()
        reg1 = M.Head(M.Tail(weighted_proof_pair)())()
        weighted_search_pair = M.Multiply(beta, search_value, reg1)()
        weighted_search = M.Head(weighted_search_pair)()
        reg2 = M.Head(M.Tail(weighted_search_pair)())()
        total_pair = M.Add(weighted_proof, weighted_search, reg2)()
        total_value = M.Head(total_pair)()
        reg3 = M.Head(M.Tail(total_pair)())()
        self.result = M.Pair(
            TotalCost(total_value, alpha, beta, proof_value, search_value)(),
            M.Pair(reg3, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(proof_cost, M.Pair(search_cost, M.Pair(heuristic, M.Pair(registry, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchAttempt(M.Edge):
    def __init__(self, start, goal, heuristic, status, derivation, proof_cost, search_cost, total_cost):
        self.result = M.Pair(
            SearchAttemptLabel,
            M.Pair(
                start,
                M.Pair(
                    goal,
                    M.Pair(
                        heuristic,
                        M.Pair(
                            status,
                            M.Pair(derivation, M.Pair(proof_cost, M.Pair(search_cost, M.Pair(total_cost, M.EmptyList)))),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                start,
                M.Pair(
                    goal,
                    M.Pair(
                        heuristic,
                        M.Pair(
                            status,
                            M.Pair(derivation, M.Pair(proof_cost, M.Pair(search_cost, M.Pair(total_cost, M.EmptyList)))),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


def _search_attempt_has_status(candidate):
    return M.OrAtom(
        M.OrAtom(
            M.IdentityCompare(candidate, SearchSuccessLabel)(),
            M.IdentityCompare(candidate, SearchFailureLabel)(),
        )(),
        M.OrAtom(
            M.OrAtom(
                M.IdentityCompare(candidate, SearchRunningLabel)(),
                M.IdentityCompare(candidate, SearchPausedLabel)(),
            )(),
            M.OrAtom(
                M.IdentityCompare(candidate, SearchTimedOutLabel)(),
                M.IdentityCompare(candidate, SearchAbortedByUserLabel)(),
            )(),
        )(),
    )()


class SearchAttemptStatus(M.Edge):
    def __init__(self, attempt):
        candidate = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())()
        if _search_attempt_has_status(candidate) is M.truth_value:
            self.result = candidate
        elif M.Compare(candidate, M.EmptyList)() is M.truth_value:
            self.result = SearchFailureLabel
        else:
            self.result = SearchSuccessLabel
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchAttemptStart(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(attempt)())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchAttemptGoal(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(M.Tail(attempt)())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchAttemptDerivation(M.Edge):
    def __init__(self, attempt):
        candidate = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())()
        if _search_attempt_has_status(candidate) is M.truth_value:
            self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())())()
        else:
            self.result = candidate
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchAttemptHeuristic(M.Edge):
    def __init__(self, attempt):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(attempt)())())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchAttemptProofCost(M.Edge):
    def __init__(self, attempt):
        candidate = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())()
        if _search_attempt_has_status(candidate) is M.truth_value:
            self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())())())()
        else:
            self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchAttemptSearchCost(M.Edge):
    def __init__(self, attempt):
        candidate = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())()
        if _search_attempt_has_status(candidate) is M.truth_value:
            self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())())())())()
        else:
            self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchAttemptTotalCost(M.Edge):
    def __init__(self, attempt):
        candidate = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())()
        if _search_attempt_has_status(candidate) is M.truth_value:
            self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())())())())())()
        else:
            self.result = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(attempt)())())())())())())())()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchAttemptSucceeded(M.Edge):
    def __init__(self, attempt):
        self.result = M.IdentityCompare(SearchAttemptStatus(attempt)(), SearchSuccessLabel)()
        super().__init__(inputs=M.Pair(attempt, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class Prove(M.Edge):
    def __init__(self, graph, start, goal, rules, heuristic, registry, phi=None):
        from . import invariance as Imod

        self.graph = graph
        self._knowledge_head_index = M.EmptyList
        self._match_memo = M.EmptyTree
        self.start = NormalizeKnowledge(start, registry)()
        self.goal = NormalizeKnowledge(goal, registry)()
        self.rules = rules
        self.heuristic = heuristic
        self.registry = registry
        if phi is None:
            phi = M.EmptyList
        self.phi = phi
        self._found_limit = M.EmptyList
        _debug("prove: start=" + _debug_term(start, registry))
        _debug("prove: goal=" + _debug_term(goal, registry))
        if M.IdentityCompare(phi, M.EmptyList)() is M.false_value:
            _debug("phi is " + M.PrettyTerm(Imod.PhiPattern(phi)(), registry)())
            rewrite_rules = CollectRules(M.FromContextGetAllRules(graph)())()
            if M.IdentityCompare(rules, M.EmptyList)() is M.truth_value:
                self.rules = rewrite_rules
            invariant = Imod.Invariant(phi, rules, registry, self.start, rewrite_rules)()
            if Imod.IsInvariant(invariant)() is M.truth_value:
                _debug("invariant independently proven over theorem rule chain")
                formula = Imod.FormulaFromFindings(self.start, phi, registry, rewrite_rules)()
                if M.IdentityCompare(formula, M.EmptyList)() is M.false_value:
                    _debug("derived equation: " + _debug_term(formula, registry))
                    if M.Compare(formula, self.goal)() is M.truth_value:
                        self._found_limit = formula
            else:
                _debug("invariant not independently proven over theorem rule chain")
            start_facts = Imod.StateFacts(self.start)()
            remaining_start_facts = start_facts
            while M.IdentityCompare(remaining_start_facts, M.EmptyList)() is M.false_value:
                start_fact = M.Head(remaining_start_facts)()
                if M.IsPair(start_fact)() is M.truth_value:
                    if M.IdentityCompare(M.Head(start_fact)(), InvariantLabel)() is M.truth_value:
                        _debug("invariant fact supplied in start state: " + _debug_term(start_fact, registry))
                remaining_start_facts = M.Tail(remaining_start_facts)()
            prune = Imod.ReachabilityPrune(self.start, self.goal, invariant, phi, registry)()
            if Imod.IsUnreachable(prune)() is M.truth_value:
                self.result = M.Pair(prune, M.EmptyList)
                super().__init__(inputs=M.Pair(graph, M.Pair(start, M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.Pair(registry, M.EmptyList)))))), results=self.result)
                return
        atom_result = self._prove()
        if atom_result is None:
            atom_result = M.EmptyList
        self.result = M.Pair(atom_result, M.EmptyList)
        if M.Compare(atom_result, M.EmptyList)() is M.truth_value:
            _debug("prove: no derivation found")
        else:
            _debug("prove: derivation produced")
        super().__init__(inputs=M.Pair(graph, M.Pair(start, M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.Pair(registry, M.EmptyList)))))), results=self.result)

    def _knowledge_has_fact(self, facts, target):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.false_value
        fact = M.Head(facts)()
        if M.Compare(fact, target)() is M.truth_value:
            return M.truth_value
        return self._knowledge_has_fact(M.Tail(facts)(), target)

    def _premises_satisfied_by_bindings(self, premises, facts, bindings):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.truth_value
        premise = M.Head(premises)()
        instantiated = M.Instantiate(premise, bindings)()
        concrete_premise = M.Head(instantiated)()
        if self._knowledge_has_fact(facts, concrete_premise) is M.false_value:
            return M.false_value
        return self._premises_satisfied_by_bindings(M.Tail(premises)(), facts, bindings)

    def _match_premises(self, rule, premises, facts, bindings):
        if M.IdentityCompare(premises, M.EmptyList)() is M.truth_value:
            return M.Pair(M.truth_value, bindings)
        premise = M.Head(premises)()
        rest = M.Tail(premises)()
        candidate_facts = facts
        if M.IdentityCompare(self._knowledge_head_index, M.EmptyList)() is M.false_value:
            if IsVarPattern(premise)() is M.false_value:
                candidate_facts = K.KnowledgeHeadIndexBucket(self._knowledge_head_index, premise, self.registry)()
        if M.IdentityCompare(bindings, M.EmptyList)() is M.truth_value:
            memo_hit = K.MatchMemoLookup(self._match_memo, rule, premises, candidate_facts, self.registry)()
            if M.IdentityCompare(memo_hit, M.EmptyList)() is M.false_value:
                return memo_hit
        result = self._match_premise_against_facts(rule, premise, rest, candidate_facts, facts, bindings)
        if M.IdentityCompare(bindings, M.EmptyList)() is M.truth_value:
            self._match_memo = K.MatchMemoStore(self._match_memo, rule, premises, candidate_facts, result, self.registry)()
        return result

    def _match_premise_against_facts(self, rule, premise, rest_premises, facts, all_facts, bindings):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)

        fact = M.Head(facts)()
        match = M.Match(premise, fact)()
        flag = M.Head(match)()
        bound = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            merged = M.MergeBindings(bindings, bound)()
            merged_flag = M.Head(merged)()
            merged_bindings = M.Tail(merged)()
            if M.IdentityCompare(merged_flag, M.truth_value)() is M.truth_value:
                rest_result = self._match_premises(rule, rest_premises, all_facts, merged_bindings)
                if M.IdentityCompare(M.Head(rest_result)(), M.truth_value)() is M.truth_value:
                    return rest_result

        return self._match_premise_against_facts(rule, premise, rest_premises, M.Tail(facts)(), all_facts, bindings)

    def _direct_next_term(self, rule, current):
        if IsKnowledge(current)() is M.truth_value:
            if ReplacementIsFactList(rule)() is M.truth_value:
                bindings_pair = JoinPremises(RulePremises(rule)(), KnowledgeFacts(current)(), M.EmptyList)()
                if M.IdentityCompare(bindings_pair, M.EmptyList)() is M.truth_value:
                    return current
                return ApplyKnowledgeRewrite(current, rule, M.Head(bindings_pair)())()
            facts = KnowledgeFacts(current)()
            self._knowledge_head_index = K.KnowledgeHeadIndexInsertChain(M.EmptyTree, facts, self.registry)()
            self._match_memo = M.EmptyTree
            bindings_pair = self._match_premises(rule, RulePremises(rule)(), facts, M.EmptyList)
            bindings_flag = M.Head(bindings_pair)()
            bindings = M.Tail(bindings_pair)()
            if M.IdentityCompare(bindings_flag, M.truth_value)() is M.false_value:
                return current
            inst = M.Instantiate(RuleReplacement(rule)(), bindings)()
            conclusion = M.CanonicalArithmeticTerm(M.Head(inst)(), self.registry)()
            if self._knowledge_has_fact(facts, conclusion) is M.truth_value:
                return current
            registry = M.FromContextGetConstructors(self.graph)()
            return NormalizeKnowledge(Knowledge(M.Pair(conclusion, facts))(), registry)()

        if RuleIsUnary(rule)() is M.false_value:
            return current
        match = M.Match(RulePattern(rule)(), current)()
        flag = M.Head(match)()
        binds = M.Tail(match)()
        if M.IdentityCompare(flag, M.truth_value)() is M.truth_value:
            inst = M.Instantiate(RuleReplacement(rule)(), binds)()
            return M.CanonicalArithmeticTerm(M.Head(inst)(), self.registry)()
        return current

    def _match_replacement_to_goal_facts(self, replacement, facts):
        if M.IdentityCompare(facts, M.EmptyList)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)
        hit = M.Match(replacement, M.Head(facts)())()
        if M.IdentityCompare(M.Head(hit)(), M.truth_value)() is M.truth_value:
            return hit
        return self._match_replacement_to_goal_facts(replacement, M.Tail(facts)())

    def _find_goal_instantiating_plan(self, rule_list, current):
        if M.IdentityCompare(rule_list, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        rule = M.Head(rule_list)()
        _debug(
            "prove-stage: goal-instantiating check replacement="
            + _debug_term(RuleReplacement(rule)(), M.FromContextGetConstructors(self.graph)())
        )
        replacement_match = M.Match(RuleReplacement(rule)(), self.goal)()
        replacement_flag = M.Head(replacement_match)()
        replacement_bindings = M.Tail(replacement_match)()

        if M.IdentityCompare(replacement_flag, M.truth_value)() is M.truth_value:
            _debug("prove-stage: replacement matched goal")
            if IsKnowledge(current)() is M.truth_value:
                facts = KnowledgeFacts(current)()
                if self._premises_satisfied_by_bindings(RulePremises(rule)(), facts, replacement_bindings) is M.truth_value:
                    _debug("prove-stage: instantiated premises are present in knowledge facts")
                    return M.Pair(TheoremAction(rule)(), M.Pair(replacement_bindings, M.EmptyList))
                _debug("prove-stage: instantiated premises are missing from knowledge facts")
            elif RuleIsUnary(rule)() is M.truth_value:
                premise_match = M.Match(RulePattern(rule)(), current)()
                premise_flag = M.Head(premise_match)()
                premise_bindings = M.Tail(premise_match)()
                if M.IdentityCompare(premise_flag, M.truth_value)() is M.truth_value:
                    merged = M.MergeBindings(replacement_bindings, premise_bindings)()
                    merged_flag = M.Head(merged)()
                    merged_bindings = M.Tail(merged)()
                    if M.IdentityCompare(merged_flag, M.truth_value)() is M.truth_value:
                        _debug("prove-stage: unary premise matched current")
                        return M.Pair(TheoremAction(rule)(), M.Pair(merged_bindings, M.EmptyList))
                _debug("prove-stage: unary premise did not match current")
        else:
            _debug("prove-stage: replacement did not match goal")

        return self._find_goal_instantiating_plan(M.Tail(rule_list)(), current)

    def _find_immediate_rule_plan(self, rule_list, current):
        if M.IdentityCompare(rule_list, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rule = M.Head(rule_list)()
        next_term = self._direct_next_term(rule, current)
        if M.TermEqual(next_term, current)() is M.false_value:
            if IsKnowledge(next_term)() is M.truth_value:
                if self._knowledge_has_fact(KnowledgeFacts(next_term)(), self.goal) is M.truth_value:
                    return M.Pair(TheoremAction(rule)(), M.EmptyList)
            elif M.TermEqual(next_term, self.goal)() is M.truth_value:
                return M.Pair(TheoremAction(rule)(), M.EmptyList)
        return self._find_immediate_rule_plan(M.Tail(rule_list)(), current)

    def _derivation_reaches_goal(self, derivation, registry):
        end = DerivationEnd(derivation, registry)()
        if IsKnowledge(self.goal)() is M.truth_value:
            if IsKnowledge(end)() is M.false_value:
                return M.false_value
            return FactsCover(KnowledgeFacts(self.goal)(), KnowledgeFacts(end)())()
        if IsKnowledge(end)() is M.truth_value:
            return self._knowledge_has_fact(KnowledgeFacts(end)(), self.goal)
        return M.TermEqual(end, self.goal)()

    def _zero_search_cost(self, registry):
        from .search import BuildSearchCost

        return BuildSearchCost(M.EmptyList, M.Zero, M.Zero, M.Zero, SearchSuccessLabel, registry)()

    def _store_search_attempt(self, derivation, search_cost, heuristic=None):
        if heuristic is None:
            heuristic = self.heuristic
        registry = M.FromContextGetConstructors(self.graph)()
        status = SearchFailureLabel if M.Compare(derivation, M.EmptyList)() is M.truth_value else SearchSuccessLabel
        if M.Compare(derivation, M.EmptyList)() is M.truth_value:
            proof_cost = ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
            reg1 = registry
        else:
            proof_cost_pair = DerivationCost(derivation, registry)()
            proof_cost = M.Head(proof_cost_pair)()
            reg1 = M.Head(M.Tail(proof_cost_pair)())()

        total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, reg1)()
        total_cost = M.Head(total_cost_pair)()
        reg2 = M.Head(M.Tail(total_cost_pair)())()
        self.graph._replace_context(constructors=reg2)
        if M.Compare(derivation, M.EmptyList)() is M.false_value:
            alpha = TotalCostAlpha(total_cost)()
            beta = TotalCostBeta(total_cost)()
            proof_value = TotalCostProofValue(total_cost)()
            search_value = TotalCostSearchValue(total_cost)()
            weighted_proof_pair = M.Multiply(alpha, proof_value, reg2)()
            weighted_proof = M.Head(weighted_proof_pair)()
            reg3 = M.Head(M.Tail(weighted_proof_pair)())()
            weighted_search_pair = M.Multiply(beta, search_value, reg3)()
            weighted_search = M.Head(weighted_search_pair)()
            reg4 = M.Head(M.Tail(weighted_search_pair)())()
            self.graph._replace_context(constructors=reg4)
            _debug(
                "prove-stage: total_cost = "
                + M.PrettyTerm(alpha, reg4)()
                + "*"
                + M.PrettyTerm(proof_value, reg4)()
                + " + "
                + M.PrettyTerm(beta, reg4)()
                + "*"
                + M.PrettyTerm(search_value, reg4)()
                + " = "
                + M.PrettyTerm(weighted_proof, reg4)()
                + " + "
                + M.PrettyTerm(weighted_search, reg4)()
                + " = "
                + M.PrettyTerm(TotalCostValue(total_cost)(), reg4)()
                + " (proof_cost="
                + M.PrettyTerm(ProofCostValue(proof_cost)(), reg4)()
                + ", search_cost="
                + M.PrettyTerm(M.SearchCostValue(search_cost)(), reg4)()
                + ")"
            )
        attempt = SearchAttempt(self.start, self.goal, heuristic, status, derivation, proof_cost, search_cost, total_cost)()
        _debug("prove-stage: storing search attempt in context.search_history")
        self.graph.add_search_attempt(attempt)
        return attempt

    def _store_success(self, derivation, new_registry, search_cost, heuristic=None):
        self.graph._replace_context(constructors=new_registry)
        _debug("prove-stage: storing derivation in context.derivations (snapshot will persist current context when saved)")
        stored = self.graph.add_derivation(self.start, self.goal, derivation)
        self._store_search_attempt(stored, search_cost, heuristic)
        return stored

    def _comparison_for_problem(self, registry):
        from .search import (
            LookupSearchComparison,
            LookupSearchComparisonJob,
            SearchComparisonBestAttempt,
            SearchComparisonJobOutcome,
            SearchSignatureForProblem,
        )

        signature = SearchSignatureForProblem(self.start, self.goal, registry)()
        paused_job = LookupSearchComparisonJob(signature, self.graph.search_comparison_jobs)()
        if M.Compare(paused_job, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(SearchComparisonJobOutcome(paused_job)(), SearchPausedLabel)() is M.truth_value:
                return M.EmptyList
        comparison = LookupSearchComparison(signature, M.FromContextGetSearchComparisons(self.graph)())()
        if M.Compare(comparison, M.EmptyList)() is M.truth_value:
            return comparison
        if M.Compare(SearchComparisonBestAttempt(comparison)(), M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return comparison

    def _maybe_seed_search_comparison(self):
        from .search import CompareSearchModes

        if M.IdentityCompare(self.graph._search_disable_console, M.truth_value)() is M.truth_value:
            return M.EmptyList

        registry = M.FromContextGetConstructors(self.graph)()
        existing = self._comparison_for_problem(registry)
        if M.Compare(existing, M.EmptyList)() is M.false_value:
            return existing
        _debug("prove-stage: seeding search mode comparison evidence")
        comparison_pair = CompareSearchModes(
            self.graph,
            self.start,
            self.goal,
            self.rules,
            self.heuristic,
            registry,
        )()
        return M.Head(comparison_pair)()

    def _recommended_search(self, comparison, registry):
        from .search import SearchAdviceText, SearchComparisonBestAttempt, SearchComparisonBestHeuristic, SearchComparisonHasUniqueBestAttempt

        best_attempt = SearchComparisonBestAttempt(comparison)()
        if M.Compare(best_attempt, M.EmptyList)() is M.false_value:
            if SearchAttemptSucceeded(best_attempt)() is M.truth_value:
                if SearchComparisonHasUniqueBestAttempt(comparison)() is M.truth_value:
                    recommended_heuristic = SearchComparisonBestHeuristic(comparison)()
                    _debug("prove-stage: " + SearchAdviceText(comparison)())
                else:
                    recommended_heuristic = self.heuristic
                    _debug("prove-stage: comparison did not distinguish a unique best mode; keeping current heuristic")
            else:
                recommended_heuristic = self.heuristic
                _debug("prove-stage: comparison found no successful mode; keeping current heuristic")
        else:
            recommended_heuristic = self.heuristic
            _debug("prove-stage: comparison did not distinguish a unique best mode; keeping current heuristic")
        search_pair = M.Search(self.graph, self.start, self.goal, self.rules, recommended_heuristic, registry)()
        return M.Pair(search_pair, M.Pair(recommended_heuristic, M.EmptyList))

    # def _prove(self):
    #     from .search import CompareSearchModes, SearchCostOutcome

    #     start_has_var = ContainsVar(self.start)()
    #     goal_has_var = ContainsVar(self.goal)()
    #     schematic_proof = M.OrAtom(start_has_var, goal_has_var)()
    #     if schematic_proof is M.false_value:
    #         _debug("prove-stage: concrete proof path")
    #         cached = self.graph.lookup_derivation(self.start, self.goal)
    #         if M.Compare(cached, M.EmptyList)() is not M.truth_value:
    #             _debug("prove-stage: derivation cache hit")
    #             zero_search_pair = self._zero_search_cost(M.FromContextGetConstructors(self.graph)())
    #             zero_search_cost = M.Head(zero_search_pair)()
    #             self.graph._replace_context(constructors=M.Head(M.Tail(zero_search_pair)())())
    #             self._store_search_attempt(cached, zero_search_cost)
    #             self._maybe_seed_search_comparison()
    #             return cached
    #         # schema_hit = self.graph.lookup_derivation_schema(self.start, self.goal)
    #         # if M.Compare(schema_hit, M.EmptyList)() is not M.truth_value:
    #         #     _debug("prove-stage: schema hit")
    #         #     plan = M.Head(schema_hit)()
    #         #     bindings = M.Head(M.Tail(schema_hit)())()
    #         #     _debug("prove-stage: schema plan=" + PrettyPlanChain(plan, M.FromContextGetConstructors(self.graph)())())
    #         #     derivation_pair = BuildDerivation(self.start, plan, M.FromContextGetConstructors(self.graph)(), bindings)()
    #         #     derivation = M.Head(derivation_pair)()
    #         #     new_registry = M.Head(M.Tail(derivation_pair)())()
    #         #     if M.Compare(derivation, M.EmptyList)() is not M.truth_value:
    #         #         if self._derivation_reaches_goal(derivation, new_registry) is M.truth_value:
    #         #             _debug("prove-stage: schema replay succeeded")
    #         #             zero_search_pair = self._zero_search_cost(new_registry)
    #         #             zero_search_cost = M.Head(zero_search_pair)()
    #         #             zero_registry = M.Head(M.Tail(zero_search_pair)())()
    #         #             stored = self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)
    #         #             self._maybe_seed_search_comparison()
    #         #             return stored
    #         # goal_instantiating_plan = self._find_goal_instantiating_plan(self.rules, self.start)
    #         # if M.Compare(goal_instantiating_plan, M.EmptyList)() is not M.truth_value:
    #         #     _debug("prove-stage: found goal-instantiating theorem action")
    #         #     action = M.Head(goal_instantiating_plan)()
    #         #     bindings = M.Head(M.Tail(goal_instantiating_plan)())()
    #         #     plan = M.Pair(action, M.EmptyList)
    #         #     _debug("prove-stage: plan=" + PrettyPlanChain(plan, M.FromContextGetConstructors(self.graph)())())
    #         #     derivation_pair = BuildDerivation(self.start, plan, M.FromContextGetConstructors(self.graph)(), bindings)()
    #         #     derivation = M.Head(derivation_pair)()
    #         #     new_registry = M.Head(M.Tail(derivation_pair)())()
    #         #     if M.Compare(derivation, M.EmptyList)() is not M.truth_value:
    #         #         if self._derivation_reaches_goal(derivation, new_registry) is M.truth_value:
    #         #             _debug("prove-stage: goal-instantiating plan succeeded")
    #         #             zero_search_pair = self._zero_search_cost(new_registry)
    #         #             zero_search_cost = M.Head(zero_search_pair)()
    #         #             zero_registry = M.Head(M.Tail(zero_search_pair)())()
    #         #             stored = self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)
    #         #             self._maybe_seed_search_comparison()
    #         #             return stored
    #         # immediate_plan = self._find_immediate_rule_plan(self.rules, self.start)
    #         # if M.Compare(immediate_plan, M.EmptyList)() is not M.truth_value:
    #         #     _debug("prove-stage: found immediate plan=" + PrettyPlanChain(immediate_plan, M.FromContextGetConstructors(self.graph)())())
    #         #     derivation_pair = BuildDerivation(self.start, immediate_plan, M.FromContextGetConstructors(self.graph)())()
    #         #     derivation = M.Head(derivation_pair)()
    #         #     new_registry = M.Head(M.Tail(derivation_pair)())()
    #         #     if M.Compare(derivation, M.EmptyList)() is not M.truth_value:
    #         #         _debug("prove-stage: immediate plan succeeded")
    #         #         zero_search_pair = self._zero_search_cost(new_registry)
    #         #         zero_search_cost = M.Head(zero_search_pair)()
    #         #         zero_registry = M.Head(M.Tail(zero_search_pair)())()
    #         #         stored = self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)
    #         #         self._maybe_seed_search_comparison()
    #         #         return stored
    #         # comparison = self._comparison_for_problem(M.FromContextGetConstructors(self.graph)())
    #         # if M.Compare(comparison, M.EmptyList)() is M.truth_value:
    #         #     _debug("prove-stage: no search comparison evidence yet; benchmarking all current search modes")
    #         #     comparison_pair = CompareSearchModes(
    #         #         self.graph,
    #         #         self.start,
    #         #         self.goal,
    #         #         self.rules,
    #         #         self.heuristic,
    #         #         M.FromContextGetConstructors(self.graph)(),
    #         #     )()
    #         #     comparison = M.Head(comparison_pair)()
    #         #     if M.Compare(comparison, M.EmptyList)() is M.truth_value:
    #         #         if M.IdentityCompare(self.graph._last_search_comparison_outcome, SearchPausedLabel)() is M.truth_value:
    #         #             _debug("prove-stage: benchmarking paused")
    #         #         else:
    #         #             _debug("prove-stage: benchmarking aborted")
    #         #         return M.EmptyList
    #         #     _debug("prove-stage: benchmarking selected a best heuristic")
    #         #     recommended_search = self._recommended_search(comparison, M.FromContextGetConstructors(self.graph)())
    #         #     search_pair = M.Head(recommended_search)()
    #         #     recommended_heuristic = M.Head(M.Tail(recommended_search)())()
    #         #     search_result = M.Head(search_pair)()
    #         #     search_cost = M.Head(M.Tail(search_pair)())()

    #         #     if M.IdentityCompare(SearchCostOutcome(search_cost)(), SearchPausedLabel)() is M.truth_value:
    #         #         _debug("prove-stage: recommended search paused")
    #         #         return M.EmptyList

    #         #     if M.Compare(search_result, M.EmptyList)() is M.false_value:
    #         #         _debug("prove-stage: recommended search produced a plan")
    #         #         derivation_pair = BuildDerivation(
    #         #             self.start,
    #         #             search_result,
    #         #             M.FromContextGetConstructors(self.graph)(),
    #         #         )()
    #         #         derivation = M.Head(derivation_pair)()
    #         #         new_registry = M.Head(M.Tail(derivation_pair)())()
    #         #         if M.Compare(derivation, M.EmptyList)() is M.false_value:
    #         #             return self._store_success(
    #         #                 derivation,
    #         #                 new_registry,
    #         #                 search_cost,
    #         #                 recommended_heuristic,
    #         #             )
    #         # else:
    #         #     recommended_search = self._recommended_search(comparison, M.FromContextGetConstructors(self.graph)())
    #         #     search_pair = M.Head(recommended_search)()
    #         #     recommended_heuristic = M.Head(M.Tail(recommended_search)())()
    #         #     search_result = M.Head(search_pair)()
    #         #     search_cost = M.Head(M.Tail(search_pair)())()
    #         #     if M.IdentityCompare(SearchCostOutcome(search_cost)(), SearchPausedLabel)() is M.truth_value:
    #         #         _debug("prove-stage: recommended search paused")
    #         #         return M.EmptyList
    #         #     if M.Compare(search_result, M.EmptyList)() is M.false_value:
    #         #         _debug("prove-stage: recommended search produced a plan")
    #         #         derivation_pair = BuildDerivation(self.start, search_result, M.FromContextGetConstructors(self.graph)())()
    #         #         derivation = M.Head(derivation_pair)()
    #         #         new_registry = M.Head(M.Tail(derivation_pair)())()
    #         #         if M.Compare(derivation, M.EmptyList)() is M.false_value:
    #         #             return self._store_success(derivation, new_registry, search_cost, recommended_heuristic)
    #         # _debug("prove-stage: falling through to mixed search")


    #         comparison = self._comparison_for_problem(M.FromContextGetConstructors(self.graph)())
    #         if M.Compare(comparison, M.EmptyList)() is M.truth_value:
    #             _debug("prove-stage: no search comparison evidence yet; benchmarking all current search modes first")
    #             comparison_pair = CompareSearchModes(
    #                 self.graph,
    #                 self.start,
    #                 self.goal,
    #                 self.rules,
    #                 self.heuristic,
    #                 M.FromContextGetConstructors(self.graph)(),
    #             )()
    #             comparison = M.Head(comparison_pair)()
    #             if M.Compare(comparison, M.EmptyList)() is M.truth_value:
    #                 if M.IdentityCompare(self.graph._last_search_comparison_outcome, SearchPausedLabel)() is M.truth_value:
    #                     _debug("prove-stage: benchmarking paused")
    #                 else:
    #                     _debug("prove-stage: benchmarking aborted")
    #                 return M.EmptyList

    #         recommended_search = self._recommended_search(comparison, M.FromContextGetConstructors(self.graph)())
    #         search_pair = M.Head(recommended_search)()
    #         recommended_heuristic = M.Head(M.Tail(recommended_search)())()
    #         search_result = M.Head(search_pair)()
    #         search_cost = M.Head(M.Tail(search_pair)())()
    #         if M.IdentityCompare(SearchCostOutcome(search_cost)(), SearchPausedLabel)() is M.truth_value:
    #             _debug("prove-stage: recommended search paused")
    #             return M.EmptyList
    #         if M.Compare(search_result, M.EmptyList)() is M.false_value:
    #             _debug("prove-stage: recommended search produced a plan")
    #             derivation_pair = BuildDerivation(self.start, search_result, M.FromContextGetConstructors(self.graph)())()
    #             derivation = M.Head(derivation_pair)()
    #             new_registry = M.Head(M.Tail(derivation_pair)())()
    #             if M.Compare(derivation, M.EmptyList)() is M.false_value:
    #                 return self._store_success(derivation, new_registry, search_cost, recommended_heuristic)

    #         schema_hit = self.graph.lookup_derivation_schema(self.start, self.goal)
    #         if M.Compare(schema_hit, M.EmptyList)() is not M.truth_value:
    #             _debug("prove-stage: schema hit")
    #             plan = M.Head(schema_hit)()
    #             bindings = M.Head(M.Tail(schema_hit)())()
    #             _debug("prove-stage: schema plan=" + PrettyPlanChain(plan, M.FromContextGetConstructors(self.graph)())())
    #             derivation_pair = BuildDerivation(self.start, plan, M.FromContextGetConstructors(self.graph)(), bindings)()
    #             derivation = M.Head(derivation_pair)()
    #             new_registry = M.Head(M.Tail(derivation_pair)())()
    #             if M.Compare(derivation, M.EmptyList)() is not M.truth_value:
    #                 if self._derivation_reaches_goal(derivation, new_registry) is M.truth_value:
    #                     _debug("prove-stage: schema replay succeeded")
    #                     zero_search_pair = self._zero_search_cost(new_registry)
    #                     zero_search_cost = M.Head(zero_search_pair)()
    #                     zero_registry = M.Head(M.Tail(zero_search_pair)())()
    #                     return self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)

    #         goal_instantiating_plan = self._find_goal_instantiating_plan(self.rules, self.start)
    #         if M.Compare(goal_instantiating_plan, M.EmptyList)() is not M.truth_value:
    #             _debug("prove-stage: found goal-instantiating theorem action")
    #             action = M.Head(goal_instantiating_plan)()
    #             bindings = M.Head(M.Tail(goal_instantiating_plan)())()
    #             plan = M.Pair(action, M.EmptyList)
    #             _debug("prove-stage: plan=" + PrettyPlanChain(plan, M.FromContextGetConstructors(self.graph)())())
    #             derivation_pair = BuildDerivation(self.start, plan, M.FromContextGetConstructors(self.graph)(), bindings)()
    #             derivation = M.Head(derivation_pair)()
    #             new_registry = M.Head(M.Tail(derivation_pair)())()
    #             if M.Compare(derivation, M.EmptyList)() is not M.truth_value:
    #                 if self._derivation_reaches_goal(derivation, new_registry) is M.truth_value:
    #                     _debug("prove-stage: goal-instantiating plan succeeded")
    #                     zero_search_pair = self._zero_search_cost(new_registry)
    #                     zero_search_cost = M.Head(zero_search_pair)()
    #                     zero_registry = M.Head(M.Tail(zero_search_pair)())()
    #                     return self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)

    #         immediate_plan = self._find_immediate_rule_plan(self.rules, self.start)
    #         if M.Compare(immediate_plan, M.EmptyList)() is not M.truth_value:
    #             _debug("prove-stage: found immediate plan=" + PrettyPlanChain(immediate_plan, M.FromContextGetConstructors(self.graph)())())
    #             derivation_pair = BuildDerivation(self.start, immediate_plan, M.FromContextGetConstructors(self.graph)())()
    #             derivation = M.Head(derivation_pair)()
    #             new_registry = M.Head(M.Tail(derivation_pair)())()
    #             if M.Compare(derivation, M.EmptyList)() is not M.truth_value:
    #                 _debug("prove-stage: immediate plan succeeded")
    #                 zero_search_pair = self._zero_search_cost(new_registry)
    #                 zero_search_cost = M.Head(zero_search_pair)()
    #                 zero_registry = M.Head(M.Tail(zero_search_pair)())()
    #                 return self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)
    #     search_pair = M.Search(self.graph, self.start, self.goal, self.rules, self.heuristic, M.FromContextGetConstructors(self.graph)())()
    #     search_result = M.Head(search_pair)()
    #     search_cost = M.Head(M.Tail(search_pair)())()
    #     if M.IdentityCompare(SearchCostOutcome(search_cost)(), SearchPausedLabel)() is M.truth_value:
    #         _debug("prove-stage: mixed search paused")
    #         return M.EmptyList
    #     if M.Compare(search_result, M.EmptyList)() is M.truth_value:
    #         _debug("prove-stage: mixed search returned empty plan")
    #         self._store_search_attempt(M.EmptyList, search_cost, self.heuristic)
    #         return M.EmptyList
    #     _debug("prove-stage: mixed search plan=" + PrettyPlanChain(search_result, M.FromContextGetConstructors(self.graph)())())
    #     derivation_pair = BuildDerivation(self.start, search_result, M.FromContextGetConstructors(self.graph)())()
    #     derivation = M.Head(derivation_pair)()
    #     new_registry = M.Head(M.Tail(derivation_pair)())()
    #     _debug("prove-stage: mixed search derivation built")
    #     return self._store_success(derivation, new_registry, search_cost, self.heuristic)


    # def _prove(self):
    #     from .search import CompareSearchModes, SearchCostOutcome

    #     start_has_var = ContainsVar(self.start)()
    #     goal_has_var = ContainsVar(self.goal)()
    #     schematic_proof = M.OrAtom(start_has_var, goal_has_var)()

    #     if schematic_proof is M.false_value:
    #         _debug("prove-stage: concrete proof path")

    #         cached = self.graph.lookup_derivation(self.start, self.goal)
    #         if M.Compare(cached, M.EmptyList)() is not M.truth_value:
    #             _debug("prove-stage: derivation cache hit")
    #             zero_search_pair = self._zero_search_cost(M.FromContextGetConstructors(self.graph)())
    #             zero_search_cost = M.Head(zero_search_pair)()
    #             self.graph._replace_context(constructors=M.Head(M.Tail(zero_search_pair)())())
    #             self._store_search_attempt(cached, zero_search_cost)
    #             return cached

    #         comparison = self._comparison_for_problem(M.FromContextGetConstructors(self.graph)())
    #         if M.Compare(comparison, M.EmptyList)() is M.truth_value:
    #             _debug("prove-stage: no search comparison evidence yet; benchmarking all current search modes first")
    #             comparison_pair = CompareSearchModes(
    #                 self.graph,
    #                 self.start,
    #                 self.goal,
    #                 self.rules,
    #                 self.heuristic,
    #                 M.FromContextGetConstructors(self.graph)(),
    #             )()
    #             comparison = M.Head(comparison_pair)()
    #             if M.Compare(comparison, M.EmptyList)() is M.truth_value:
    #                 if M.IdentityCompare(self.graph._last_search_comparison_outcome, SearchPausedLabel)() is M.truth_value:
    #                     _debug("prove-stage: benchmarking paused")
    #                 else:
    #                     _debug("prove-stage: benchmarking aborted")
    #                 return M.EmptyList

    #         recommended_search = self._recommended_search(comparison, M.FromContextGetConstructors(self.graph)())
    #         search_pair = M.Head(recommended_search)()
    #         recommended_heuristic = M.Head(M.Tail(recommended_search)())()
    #         search_result = M.Head(search_pair)()
    #         search_cost = M.Head(M.Tail(search_pair)())()

    #         if M.IdentityCompare(SearchCostOutcome(search_cost)(), SearchPausedLabel)() is M.truth_value:
    #             _debug("prove-stage: recommended search paused")
    #             return M.EmptyList

    #         if M.Compare(search_result, M.EmptyList)() is M.false_value:
    #             _debug("prove-stage: recommended search produced a plan")
    #             derivation_pair = BuildDerivation(
    #                 self.start,
    #                 search_result,
    #                 M.FromContextGetConstructors(self.graph)(),
    #             )()
    #             derivation = M.Head(derivation_pair)()
    #             new_registry = M.Head(M.Tail(derivation_pair)())()
    #             if M.Compare(derivation, M.EmptyList)() is M.false_value:
    #                 return self._store_success(
    #                     derivation,
    #                     new_registry,
    #                     search_cost,
    #                     recommended_heuristic,
    #                 )

    #         schema_hit = self.graph.lookup_derivation_schema(self.start, self.goal)
    #         if M.Compare(schema_hit, M.EmptyList)() is not M.truth_value:
    #             _debug("prove-stage: schema hit")
    #             plan = M.Head(schema_hit)()
    #             bindings = M.Head(M.Tail(schema_hit)())()
    #             _debug("prove-stage: schema plan=" + PrettyPlanChain(plan, M.FromContextGetConstructors(self.graph)())())
    #             derivation_pair = BuildDerivation(self.start, plan, M.FromContextGetConstructors(self.graph)(), bindings)()
    #             derivation = M.Head(derivation_pair)()
    #             new_registry = M.Head(M.Tail(derivation_pair)())()
    #             if M.Compare(derivation, M.EmptyList)() is not M.truth_value:
    #                 if self._derivation_reaches_goal(derivation, new_registry) is M.truth_value:
    #                     _debug("prove-stage: schema replay succeeded")
    #                     zero_search_pair = self._zero_search_cost(new_registry)
    #                     zero_search_cost = M.Head(zero_search_pair)()
    #                     zero_registry = M.Head(M.Tail(zero_search_pair)())()
    #                     return self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)

    #         goal_instantiating_plan = self._find_goal_instantiating_plan(self.rules, self.start)
    #         if M.Compare(goal_instantiating_plan, M.EmptyList)() is not M.truth_value:
    #             _debug("prove-stage: found goal-instantiating theorem action")
    #             action = M.Head(goal_instantiating_plan)()
    #             bindings = M.Head(M.Tail(goal_instantiating_plan)())()
    #             plan = M.Pair(action, M.EmptyList)
    #             _debug("prove-stage: plan=" + PrettyPlanChain(plan, M.FromContextGetConstructors(self.graph)())())
    #             derivation_pair = BuildDerivation(self.start, plan, M.FromContextGetConstructors(self.graph)(), bindings)()
    #             derivation = M.Head(derivation_pair)()
    #             new_registry = M.Head(M.Tail(derivation_pair)())()
    #             if M.Compare(derivation, M.EmptyList)() is not M.truth_value:
    #                 if self._derivation_reaches_goal(derivation, new_registry) is M.truth_value:
    #                     _debug("prove-stage: goal-instantiating plan succeeded")
    #                     zero_search_pair = self._zero_search_cost(new_registry)
    #                     zero_search_cost = M.Head(zero_search_pair)()
    #                     zero_registry = M.Head(M.Tail(zero_search_pair)())()
    #                     return self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)

    #         immediate_plan = self._find_immediate_rule_plan(self.rules, self.start)
    #         if M.Compare(immediate_plan, M.EmptyList)() is not M.truth_value:
    #             _debug("prove-stage: found immediate plan=" + PrettyPlanChain(immediate_plan, M.FromContextGetConstructors(self.graph)())())
    #             derivation_pair = BuildDerivation(self.start, immediate_plan, M.FromContextGetConstructors(self.graph)())()
    #             derivation = M.Head(derivation_pair)()
    #             new_registry = M.Head(M.Tail(derivation_pair)())()
    #             if M.Compare(derivation, M.EmptyList)() is not M.truth_value:
    #                 _debug("prove-stage: immediate plan succeeded")
    #                 zero_search_pair = self._zero_search_cost(new_registry)
    #                 zero_search_cost = M.Head(zero_search_pair)()
    #                 zero_registry = M.Head(M.Tail(zero_search_pair)())()
    #                 return self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)

    #         _debug("prove-stage: falling through to mixed search")

    #     search_pair = M.Search(
    #         self.graph,
    #         self.start,
    #         self.goal,
    #         self.rules,
    #         self.heuristic,
    #         M.FromContextGetConstructors(self.graph)(),
    #     )()
    #     search_result = M.Head(search_pair)()
    #     search_cost = M.Head(M.Tail(search_pair)())()

    #     if M.IdentityCompare(SearchCostOutcome(search_cost)(), SearchPausedLabel)() is M.truth_value:
    #         _debug("prove-stage: mixed search paused")
    #         return M.EmptyList

    #     if M.Compare(search_result, M.EmptyList)() is M.truth_value:
    #         _debug("prove-stage: mixed search returned empty plan")
    #         self._store_search_attempt(M.EmptyList, search_cost, self.heuristic)
    #         return M.EmptyList

    #     _debug("prove-stage: mixed search plan=" + PrettyPlanChain(search_result, M.FromContextGetConstructors(self.graph)())())
    #     derivation_pair = BuildDerivation(self.start, search_result, M.FromContextGetConstructors(self.graph)())()
    #     derivation = M.Head(derivation_pair)()
    #     new_registry = M.Head(M.Tail(derivation_pair)())()
    #     _debug("prove-stage: mixed search derivation built")
    #     return self._store_success(derivation, new_registry, search_cost, self.heuristic)

    def _prove(self):
        from .search import CompareSearchModes, SearchComparisonBestAttempt, SearchComparisonOutcome, SearchCostOutcome

        if M.IdentityCompare(self._found_limit, M.EmptyList)() is M.false_value:
            if M.Compare(self._found_limit, self.goal)() is M.truth_value:
                _debug("prove-stage: derived Apply(X, n) as a function of a and b")
                zero_search_pair = self._zero_search_cost(M.FromContextGetConstructors(self.graph)())
                zero_search_cost = M.Head(zero_search_pair)()
                zero_registry = M.Head(M.Tail(zero_search_pair)())()
                step_pair = Step(self.start, M.EmptyList, self._found_limit, zero_registry)()
                step_node = M.Head(step_pair)()
                step_registry = M.Head(M.Tail(step_pair)())()
                cost_pair = BuildProofCost(M.Pair(step_node, M.EmptyList), step_registry)()
                cost = M.Head(cost_pair)()
                cost_registry = M.Head(M.Tail(cost_pair)())()
                deriv_pair = Derivation(M.Pair(step_node, M.EmptyList), cost, cost_registry)()
                derivation = M.Head(deriv_pair)()
                new_registry = M.Head(M.Tail(deriv_pair)())()
                return self._store_success(derivation, new_registry, zero_search_cost, self.heuristic)

        if IsKnowledge(self.goal)() is M.truth_value:
            if IsKnowledge(self.start)() is M.truth_value:
                if FactsCover(KnowledgeFacts(self.goal)(), KnowledgeFacts(self.start)())() is M.truth_value:
                    _debug("prove-stage: findings already cover the goal")
                    zero_search_pair = self._zero_search_cost(M.FromContextGetConstructors(self.graph)())
                    zero_search_cost = M.Head(zero_search_pair)()
                    zero_registry = M.Head(M.Tail(zero_search_pair)())()
                    step_pair = Step(self.start, M.EmptyList, self.start, zero_registry)()
                    step_node = M.Head(step_pair)()
                    step_registry = M.Head(M.Tail(step_pair)())()
                    cost_pair = BuildProofCost(M.Pair(step_node, M.EmptyList), step_registry)()
                    cost = M.Head(cost_pair)()
                    cost_registry = M.Head(M.Tail(cost_pair)())()
                    deriv_pair = Derivation(M.Pair(step_node, M.EmptyList), cost, cost_registry)()
                    derivation = M.Head(deriv_pair)()
                    new_registry = M.Head(M.Tail(deriv_pair)())()
                    return self._store_success(derivation, new_registry, zero_search_cost, self.heuristic)

        schema_hit = self.graph.lookup_derivation_schema(
            self.start,
            self.goal,
        )
        if M.Compare(schema_hit, M.EmptyList)() is M.false_value:
            plan = M.Head(schema_hit)()
            bindings = M.Head(M.Tail(schema_hit)())()
            derivation_pair = BuildDerivation(
                self.start,
                plan,
                M.FromContextGetConstructors(self.graph)(),
                bindings,
            )()
            derivation = M.Head(derivation_pair)()
            new_registry = M.Head(M.Tail(derivation_pair)())()
            if M.Compare(derivation, M.EmptyList)() is M.false_value:
                if self._derivation_reaches_goal(
                    derivation, new_registry,
                ) is M.truth_value:
                    zero_search_pair = self._zero_search_cost(new_registry)
                    zero_search_cost = M.Head(zero_search_pair)()
                    zero_registry = M.Head(M.Tail(zero_search_pair)())()
                    return self._store_success(
                        derivation,
                        zero_registry,
                        zero_search_cost,
                        self.heuristic,
                    )

        start_has_var = ContainsVar(self.start)()
        goal_has_var = ContainsVar(self.goal)()
        schematic_proof = M.OrAtom(start_has_var, goal_has_var)()

        if IsKnowledge(self.goal)() is M.truth_value:
            if IsKnowledge(self.start)() is M.truth_value:
                goal_instantiating_plan = self._find_goal_instantiating_plan(self.rules, self.start)
                if M.Compare(goal_instantiating_plan, M.EmptyList)() is M.false_value:
                    _debug("prove-stage: goal-instantiating theorem on findings")
                    action = M.Head(goal_instantiating_plan)()
                    bindings = M.Head(M.Tail(goal_instantiating_plan)())()
                    plan = M.Pair(action, M.EmptyList)
                    derivation_pair = BuildDerivation(self.start, plan, M.FromContextGetConstructors(self.graph)(), bindings)()
                    derivation = M.Head(derivation_pair)()
                    new_registry = M.Head(M.Tail(derivation_pair)())()
                    if M.Compare(derivation, M.EmptyList)() is M.false_value:
                        if self._derivation_reaches_goal(derivation, new_registry) is M.truth_value:
                            zero_search_pair = self._zero_search_cost(new_registry)
                            zero_search_cost = M.Head(zero_search_pair)()
                            zero_registry = M.Head(M.Tail(zero_search_pair)())()
                            return self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)
            immediate_plan = self._find_immediate_rule_plan(self.rules, self.start)
            if M.Compare(immediate_plan, M.EmptyList)() is M.false_value:
                _debug("prove-stage: immediate theorem on findings")
                derivation_pair = BuildDerivation(self.start, immediate_plan, M.FromContextGetConstructors(self.graph)())()
                derivation = M.Head(derivation_pair)()
                new_registry = M.Head(M.Tail(derivation_pair)())()
                if M.Compare(derivation, M.EmptyList)() is M.false_value:
                    if self._derivation_reaches_goal(derivation, new_registry) is M.truth_value:
                        zero_search_pair = self._zero_search_cost(new_registry)
                        zero_search_cost = M.Head(zero_search_pair)()
                        zero_registry = M.Head(M.Tail(zero_search_pair)())()
                        return self._store_success(derivation, zero_registry, zero_search_cost, self.heuristic)

        if schematic_proof is M.false_value:
            _debug("prove-stage: concrete proof path")

            if IsKnowledge(self.goal)() is M.truth_value:
                _debug("prove-stage: knowledge-board goal; skip search-mode comparison")
                search_pair = M.Search(
                    self.graph,
                    self.start,
                    self.goal,
                    self.rules,
                    self.heuristic,
                    M.FromContextGetConstructors(self.graph)(),
                )()
                search_result = M.Head(search_pair)()
                search_cost = M.Head(M.Tail(search_pair)())()
                if M.IdentityCompare(SearchCostOutcome(search_cost)(), SearchPausedLabel)() is M.truth_value:
                    _debug("prove-stage: knowledge search paused")
                    return M.EmptyList
                if M.Compare(search_result, M.EmptyList)() is M.truth_value:
                    _debug("prove-stage: knowledge search returned empty plan")
                    self._store_search_attempt(M.EmptyList, search_cost, self.heuristic)
                    return M.EmptyList
                derivation_pair = BuildDerivation(self.start, search_result, M.FromContextGetConstructors(self.graph)())()
                derivation = M.Head(derivation_pair)()
                new_registry = M.Head(M.Tail(derivation_pair)())()
                return self._store_success(derivation, new_registry, search_cost, self.heuristic)

            cached = self.graph.lookup_derivation(self.start, self.goal)
            if M.Compare(cached, M.EmptyList)() is not M.truth_value:
                _debug("prove-stage: derivation cache hit")
                zero_search_pair = self._zero_search_cost(M.FromContextGetConstructors(self.graph)())
                zero_search_cost = M.Head(zero_search_pair)()
                self.graph._replace_context(constructors=M.Head(M.Tail(zero_search_pair)())())
                self._store_search_attempt(cached, zero_search_cost)
                self._maybe_seed_search_comparison()
                return cached

            comparison = self._comparison_for_problem(M.FromContextGetConstructors(self.graph)())
            if M.Compare(comparison, M.EmptyList)() is M.truth_value:
                _debug("prove-stage: no search comparison evidence yet; benchmarking all current search modes")
                comparison_pair = CompareSearchModes(
                    self.graph,
                    self.start,
                    self.goal,
                    self.rules,
                    self.heuristic,
                    M.FromContextGetConstructors(self.graph)(),
                )()
                comparison = M.Head(comparison_pair)()
                if M.Compare(comparison, M.EmptyList)() is M.truth_value:
                    if M.IdentityCompare(self.graph._last_search_comparison_outcome, SearchPausedLabel)() is M.truth_value:
                        _debug("prove-stage: benchmarking paused")
                    else:
                        _debug("prove-stage: benchmarking aborted")
                    return M.EmptyList
            if M.IdentityCompare(SearchComparisonOutcome(comparison)(), SearchPausedLabel)() is M.truth_value:
                _debug("prove-stage: benchmarking paused")
                return M.EmptyList

            best_attempt = SearchComparisonBestAttempt(comparison)()
            if M.Compare(best_attempt, M.EmptyList)() is M.false_value:
                if SearchAttemptSucceeded(best_attempt)() is M.truth_value:
                    comparison_derivation = SearchAttemptDerivation(best_attempt)()
                    if M.Compare(comparison_derivation, M.EmptyList)() is M.false_value:
                        _debug("prove-stage: comparison already produced a derivation")
                        _debug("prove-stage: storing derivation in context.derivations (snapshot will persist current context when saved)")
                        self.graph.add_derivation(self.start, self.goal, comparison_derivation)
                        _debug("prove-stage: storing search attempt in context.search_history")
                        self.graph.add_search_attempt(best_attempt)
                        return comparison_derivation
                else:
                    _debug("prove-stage: comparison found no successful mode; not rerunning the same search immediately")
                    return M.EmptyList

            recommended_search = self._recommended_search(comparison, M.FromContextGetConstructors(self.graph)())
            search_pair = M.Head(recommended_search)()
            recommended_heuristic = M.Head(M.Tail(recommended_search)())()
            search_result = M.Head(search_pair)()
            search_cost = M.Head(M.Tail(search_pair)())()

            if M.IdentityCompare(SearchCostOutcome(search_cost)(), SearchPausedLabel)() is M.truth_value:
                _debug("prove-stage: recommended search paused")
                return M.EmptyList

            if M.Compare(search_result, M.EmptyList)() is M.false_value:
                _debug("prove-stage: recommended search produced a plan")
                derivation_pair = BuildDerivation(
                    self.start,
                    search_result,
                    M.FromContextGetConstructors(self.graph)(),
                )()
                derivation = M.Head(derivation_pair)()
                new_registry = M.Head(M.Tail(derivation_pair)())()
                if M.Compare(derivation, M.EmptyList)() is M.false_value:
                    return self._store_success(
                        derivation,
                        new_registry,
                        search_cost,
                        recommended_heuristic,
                    )

            _debug("prove-stage: falling through to mixed search")

        search_pair = M.Search(
            self.graph,
            self.start,
            self.goal,
            self.rules,
            self.heuristic,
            M.FromContextGetConstructors(self.graph)(),
        )()
        search_result = M.Head(search_pair)()
        search_cost = M.Head(M.Tail(search_pair)())()

        if M.IdentityCompare(SearchCostOutcome(search_cost)(), SearchPausedLabel)() is M.truth_value:
            _debug("prove-stage: mixed search paused")
            return M.EmptyList

        if M.Compare(search_result, M.EmptyList)() is M.truth_value:
            _debug("prove-stage: mixed search returned empty plan")
            self._store_search_attempt(M.EmptyList, search_cost, self.heuristic)
            return M.EmptyList

        _debug("prove-stage: mixed search plan=" + PrettyPlanChain(search_result, M.FromContextGetConstructors(self.graph)())())
        derivation_pair = BuildDerivation(self.start, search_result, M.FromContextGetConstructors(self.graph)())()
        derivation = M.Head(derivation_pair)()
        new_registry = M.Head(M.Tail(derivation_pair)())()
        _debug("prove-stage: mixed search derivation built")
        return self._store_success(derivation, new_registry, search_cost, self.heuristic)

    def __call__(self):
        return self.result


def sync_from_namespace(namespace):
    for name in (
        "KnowledgeLabel",
        "CompiledRuleLabel",
        "StepLabel",
        "DerivationLabel",
        "ProofCostLabel",
        "SearchAttemptLabel",
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchPausedLabel",
        "SearchRunningLabel",
        "TheoremActionLabel",
        "RewriteActionLabel",
        "TotalCostLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_")]
