"""The supervised teaching layer: words, facts, rules, and gaps.

Everything the dialogue boundary teaches and asks about lives here:
taught fact/rule/derivation records and their graph recovery, the
word and rule surface parsers with their constructor vocabulary, and
the vocabulary gap machinery -- detection, blast-radius ranking,
render laws, asked-question and acknowledgement records, and
recursive derivation trees.

This module follows the sibling-module pattern of the graph refactor:
it star-imports graph (which must be fully loaded first -- graph
re-exports this module from its end) and adds the teaching layer on
top. Machine-native throughout: Pair chains, GMPRep counts, machine
truth values.
"""

from __future__ import annotations

from . import labels as Lmod
from . import machine as M
from . import proof as P
from .gmprep import GMPEqualText, GMPLessText, GMPSuccText
from .graph import *


class TaughtDerivation(M.Edge):
    """Provenance for a fact produced by a taught monotone rule."""

    def __init__(self, derived, rule, premises):
        self.result = M.Pair(
            M.Char("taught-derivation"),
            M.Pair(
                derived,
                M.Pair(rule, M.Pair(premises, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                derived,
                M.Pair(rule, M.Pair(premises, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DerivationDerived(M.Edge):
    def __init__(self, derivation):
        self.result = M.Head(M.Tail(derivation)())()
        super().__init__(inputs=M.Pair(derivation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DerivationRule(M.Edge):
    def __init__(self, derivation):
        self.result = M.Head(M.Tail(M.Tail(derivation)())())()
        super().__init__(inputs=M.Pair(derivation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DerivationPremises(M.Edge):
    def __init__(self, derivation):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(derivation)())())(),
        )()
        super().__init__(inputs=M.Pair(derivation, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InstalledTaughtDerivations(M.Edge):
    """Recover persisted rule-firing provenance."""

    def __init__(self, graph_version):
        reversed_derivations = M.EmptyList
        agenda = GraphNodes(graph_version)()
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            node = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.IsPair(node)() is M.truth_value:
                node_head = M.Head(node)()
                if M.IsPair(node_head)() is M.truth_value:
                    nested = node
                    while M.IdentityCompare(nested, M.EmptyList)() is M.false_value:
                        agenda = M.Pair(M.Head(nested)(), agenda)
                        nested = M.Tail(nested)()
                elif M.Compare(
                    node_head, M.Char("taught-derivation"),
                )() is M.truth_value:
                    reversed_derivations = M.Pair(
                        node,
                        reversed_derivations,
                    )
        self.result = M.Reverse(reversed_derivations)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallTaughtDerivation(M.Edge):
    """Persist one rule-firing provenance record."""

    def __init__(self, graph_version, derivation):
        next_version = GraphVersion(
            M.Pair(derivation, GraphNodes(graph_version)()),
            GraphEdges(graph_version)(),
            GraphVersionInvariants(graph_version)(),
        )()
        self.result = next_version
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(derivation, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TaughtFact(M.Edge):
    """A ground fact taught at the dialogue boundary."""

    def __init__(self, fact):
        self.result = M.Pair(
            M.Char("taught-fact"),
            M.Pair(fact, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(fact, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstalledTaughtFacts(M.Edge):
    """Recover ground facts taught at the dialogue boundary."""

    def __init__(self, graph_version):
        reversed_facts = M.EmptyList
        agenda = GraphNodes(graph_version)()
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            node = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.IsPair(node)() is M.truth_value:
                node_head = M.Head(node)()
                if M.IsPair(node_head)() is M.truth_value:
                    nested = node
                    while M.IdentityCompare(nested, M.EmptyList)() is M.false_value:
                        agenda = M.Pair(M.Head(nested)(), agenda)
                        nested = M.Tail(nested)()
                elif M.Compare(
                    node_head, M.Char("taught-fact"),
                )() is M.truth_value:
                    fact = M.Head(M.Tail(node)())()
                    if ChainHasTerm(
                        M.Reverse(reversed_facts)(), fact,
                    )() is M.false_value:
                        reversed_facts = M.Pair(fact, reversed_facts)
        self.result = M.Reverse(reversed_facts)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallTaughtFact(M.Edge):
    """Append one ground fact to the learned graph version."""

    def __init__(self, graph_version, fact):
        existing = InstalledTaughtFacts(graph_version)()
        if ChainHasTerm(existing, fact)() is M.truth_value:
            self.result = M.Pair(graph_version, M.Pair(existing, M.EmptyList))
        else:
            next_version = GraphVersion(
                M.Pair(TaughtFact(fact)(), GraphNodes(graph_version)()),
                GraphEdges(graph_version)(),
                GraphVersionInvariants(graph_version)(),
            )()
            self.result = M.Pair(next_version, M.Pair(M.EmptyList, M.EmptyList))
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(fact, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallTaughtRuleSource(M.Edge):
    """Append an approved dialogue rule source before daemon activation."""

    def __init__(self, graph_version, premises, replacement):
        next_version = GraphVersion(
            M.Pair(
                TaughtRule(premises, replacement)(),
                GraphNodes(graph_version)(),
            ),
            GraphEdges(graph_version)(),
            GraphVersionInvariants(graph_version)(),
        )()
        self.result = next_version
        super().__init__(
            inputs=M.Pair(
                graph_version,
                M.Pair(premises, M.Pair(replacement, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstalledTaughtRules(M.Edge):
    """Recover activated dialogue rules for a term-native proof runtime."""

    def __init__(self, graph_version):
        reversed_rules = M.EmptyList
        agenda = GraphNodes(graph_version)()
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            node = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.IsPair(node)() is M.truth_value:
                node_head = M.Head(node)()
                if M.IsPair(node_head)() is M.truth_value:
                    nested = node
                    while M.IdentityCompare(nested, M.EmptyList)() is M.false_value:
                        agenda = M.Pair(M.Head(nested)(), agenda)
                        nested = M.Tail(nested)()
                elif M.Compare(
                    node_head, M.Char("taught-rule"),
                )() is M.truth_value:
                    premises = M.Head(M.Tail(node)())()
                    replacement = M.Head(M.Tail(M.Tail(node)())())()
                    reversed_rules = M.Pair(
                        P.MultiRule(premises, replacement)(),
                        reversed_rules,
                    )
        self.result = M.Reverse(reversed_rules)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RuleConstructors(M.Edge):
    """Constructors admitted by the rule surface.

    The pack index is the source of canonical constructors. A learned bridge
    contributes the constructor it names, a learned definition contributes
    its own word, and an earlier taught fact or rule preserves the identity
    of a newly introduced predicate. The parser may introduce a fresh
    predicate atom only at this teaching boundary; later lines recover that
    same atom from the learned graph.
    """

    def __init__(self, graph_version, pack_constructors):
        known = M.Pair(
            M.Pair(M.Char("word"), M.Pair(Lmod.WordLabel, M.EmptyList)),
            M.Pair(
                M.Pair(M.Char("concept"), M.Pair(Lmod.ConceptLabel, M.EmptyList)),
                M.Pair(
                    M.Pair(M.Char("isa"), M.Pair(Lmod.IsALabel, M.EmptyList)),
                    M.Pair(
                        M.Pair(M.Char("partof"), M.Pair(Lmod.PartOfLabel, M.EmptyList)),
                        M.Pair(
                            M.Pair(M.Char("wornby"), M.Pair(Lmod.WornByLabel, M.EmptyList)),
                            M.Pair(
                                M.Pair(M.Char("locatedat"), M.Pair(Lmod.LocatedAtLabel, M.EmptyList)),
                                M.Pair(
                                    M.Pair(M.Char("evidencefor"), M.Pair(Lmod.EvidenceForLabel, M.EmptyList)),
                                    M.Pair(
                                        M.Pair(M.Char("supported"), M.Pair(Lmod.SupportedLabel, M.EmptyList)),
                                        M.Pair(
                                            M.Pair(M.Char("roleof"), M.Pair(Lmod.RoleOfLabel, M.EmptyList)),
                                            M.Pair(
                                                M.Pair(M.Char("canaccess"), M.Pair(Lmod.CanAccessLabel, M.EmptyList)),
                                                M.Pair(
                                                    M.Pair(M.Char("responsiblefor"), M.Pair(Lmod.ResponsibleForLabel, M.EmptyList)),
                                                    M.Pair(
                                                        M.Pair(M.Char("opportunity"), M.Pair(Lmod.OpportunityLabel, M.EmptyList)),
                                                        pack_constructors,
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        known = M.Pair(
            M.Pair(M.Char("modifierof"), M.Pair(Lmod.ModifierOfLabel, M.EmptyList)),
            M.Pair(
                M.Pair(M.Char("undefinedconcept"), M.Pair(Lmod.UndefinedConceptLabel, M.EmptyList)),
                M.Pair(
                    M.Pair(M.Char("ungroundedmodifier"), M.Pair(Lmod.UngroundedModifierLabel, M.EmptyList)),
                    M.Pair(
                        M.Pair(M.Char("nousageexample"), M.Pair(Lmod.NoUsageExampleLabel, M.EmptyList)),
                        M.Pair(
                            M.Pair(M.Char("noparent"), M.Pair(Lmod.NoParentLabel, M.EmptyList)),
                            M.Pair(
                                M.Pair(M.Char("danglingreference"), M.Pair(Lmod.DanglingReferenceLabel, M.EmptyList)),
                                M.Pair(
                                    M.Pair(
                                        M.Char("missingrenderlaw"),
                                        M.Pair(Lmod.MissingRenderLawLabel, M.EmptyList),
                                    ),
                                    known,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        term_agenda = M.EmptyList
        agenda = GraphNodes(graph_version)()
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            node = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.IsPair(node)() is M.truth_value:
                node_head = M.Head(node)()
                if M.IsPair(node_head)() is M.truth_value:
                    nested = node
                    while M.IdentityCompare(nested, M.EmptyList)() is M.false_value:
                        agenda = M.Pair(M.Head(nested)(), agenda)
                        nested = M.Tail(nested)()
                elif M.IdentityCompare(
                    node_head, Lmod.CorrespondsLabel,
                )() is M.truth_value:
                    surface = M.Head(M.Tail(node)())()
                    word_chain = M.Head(M.Tail(surface)())()
                    if M.IdentityCompare(
                        word_chain, M.EmptyList,
                    )() is M.false_value:
                        word = M.Head(word_chain)()
                        constructor = BridgeConstructor(node)()
                        found = M.false_value
                        scan = known
                        while M.IdentityCompare(
                            scan, M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(M.Head(M.Head(scan)())(), word)() is M.truth_value:
                                found = M.truth_value
                                scan = M.EmptyList
                            else:
                                scan = M.Tail(scan)()
                        if M.IdentityCompare(found, M.false_value)() is M.truth_value:
                            known = M.Pair(
                                M.Pair(word, M.Pair(constructor, M.EmptyList)),
                                known,
                            )
                elif M.IdentityCompare(
                    node_head, Lmod.DefinitionNodeLabel,
                )() is M.truth_value:
                    definiendum = DefinitionNodeDefiniendum(node)()
                    concept = M.Head(M.Tail(definiendum)())()
                    word = M.EmptyList
                    if M.IsPair(concept)() is M.truth_value:
                        if M.IdentityCompare(
                            M.Head(concept)(), Lmod.HoleLabel,
                        )() is M.truth_value:
                            word = HolePredicate(concept)()
                    else:
                        word = concept
                    if M.IdentityCompare(word, M.EmptyList)() is M.false_value:
                        found = M.false_value
                        scan = known
                        while M.IdentityCompare(
                            scan, M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(M.Head(M.Head(scan)())(), word)() is M.truth_value:
                                found = M.truth_value
                                scan = M.EmptyList
                            else:
                                scan = M.Tail(scan)()
                        if M.IdentityCompare(found, M.false_value)() is M.truth_value:
                            known = M.Pair(
                                M.Pair(word, M.Pair(word, M.EmptyList)),
                                known,
                            )
                elif M.Compare(
                    node_head, M.Char("taught-fact"),
                )() is M.truth_value:
                    term_agenda = M.Pair(
                        M.Head(M.Tail(node)())(),
                        term_agenda,
                    )
                elif M.Compare(
                    node_head, M.Char("taught-rule"),
                )() is M.truth_value:
                    source_premises = M.Head(M.Tail(node)())()
                    source_replacement = M.Head(
                        M.Tail(M.Tail(node)())(),
                    )()
                    term_agenda = M.Pair(
                        source_replacement,
                        term_agenda,
                    )
                    premise_scan = source_premises
                    while M.IdentityCompare(
                        premise_scan, M.EmptyList,
                    )() is M.false_value:
                        term_agenda = M.Pair(
                            M.Head(premise_scan)(),
                            term_agenda,
                        )
                        premise_scan = M.Tail(premise_scan)()
            while M.IdentityCompare(
                term_agenda, M.EmptyList,
            )() is M.false_value:
                term = M.Head(term_agenda)()
                term_agenda = M.Tail(term_agenda)()
                if M.IsPair(term)() is M.truth_value:
                    term_head = M.Head(term)()
                    if M.IsPair(term_head)() is M.false_value:
                        if M.IdentityCompare(
                            term_head, M.VarTag,
                        )() is M.false_value:
                            term_word = M.Char(term_head())
                            term_found = M.false_value
                            term_scan = known
                            while M.IdentityCompare(
                                term_scan, M.EmptyList,
                            )() is M.false_value:
                                if M.Compare(
                                    M.Head(M.Head(term_scan)())(),
                                    term_word,
                                )() is M.truth_value:
                                    term_found = M.truth_value
                                    term_scan = M.EmptyList
                                else:
                                    term_scan = M.Tail(term_scan)()
                            if M.IdentityCompare(
                                term_found, M.false_value,
                            )() is M.truth_value:
                                known = M.Pair(
                                    M.Pair(
                                        term_word,
                                        M.Pair(term_head, M.EmptyList),
                                    ),
                                    known,
                                )
                    term_arguments = M.Tail(term)()
                    while M.IdentityCompare(
                        term_arguments, M.EmptyList,
                    )() is M.false_value:
                        term_argument = M.Head(term_arguments)()
                        if M.IsPair(term_argument)() is M.truth_value:
                            term_agenda = M.Pair(
                                term_argument,
                                term_agenda,
                            )
                        term_arguments = M.Tail(term_arguments)()
        self.result = known
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(pack_constructors, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ParseRuleTextFlat(M.Edge):
    """Legacy flat parser retained as a regression reference.

    Parsing crosses the text boundary through the ordinary reading policy.
    Predicate heads must occur in the supplied constructor chain. Arguments
    are variables, and equal argument words share one Var term. The result is
    Pair(rule, Pair(reason, EmptyList)); reason is EmptyList on success or a
    machine term whose head is `unknown-constructor` or `malformed-rule`.
    """

    def __init__(self, text, reading_policy, digit_words, constructors):
        tokens = WordsOfText(text, reading_policy, digit_words)()
        remaining = tokens
        premises_reversed = M.EmptyList
        variables = M.EmptyList
        conclusion = M.EmptyList
        arrow_seen = M.false_value
        expect_term = M.truth_value
        reason = M.EmptyList

        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(reason, M.EmptyList)() is M.false_value:
                remaining = M.EmptyList
            else:
                token = M.Head(remaining)()
                if M.Compare(token, M.Char(","))() is M.truth_value:
                    if M.IdentityCompare(expect_term, M.truth_value)() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("unexpected-comma"), M.EmptyList),
                        )
                    else:
                        expect_term = M.truth_value
                        remaining = M.Tail(remaining)()
                elif M.Compare(token, M.Char("->"))() is M.truth_value:
                    if M.IdentityCompare(arrow_seen, M.truth_value)() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("multiple-arrows"), M.EmptyList),
                        )
                    elif M.IdentityCompare(expect_term, M.truth_value)() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("missing-premise"), M.EmptyList),
                        )
                    elif M.IdentityCompare(
                        premises_reversed, M.EmptyList,
                    )() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("missing-premise"), M.EmptyList),
                        )
                    else:
                        arrow_seen = M.truth_value
                        expect_term = M.truth_value
                        remaining = M.Tail(remaining)()
                else:
                    if M.IdentityCompare(
                        arrow_seen, M.truth_value,
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            conclusion, M.EmptyList,
                        )() is M.false_value:
                            reason = M.Pair(
                                M.Char("malformed-rule"),
                                M.Pair(M.Char("extra-conclusion"), M.EmptyList),
                            )
                    if M.IdentityCompare(expect_term, M.truth_value)() is M.false_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("missing-comma"), M.EmptyList),
                        )
                    else:
                        predicate = token
                        term_remaining = M.Tail(remaining)()
                        valid_open = M.false_value
                        if M.IdentityCompare(
                            term_remaining, M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(term_remaining)(), M.Char("("),
                            )() is M.truth_value:
                                valid_open = M.truth_value
                                term_remaining = M.Tail(term_remaining)()
                        if M.IdentityCompare(valid_open, M.truth_value)() is M.false_value:
                            reason = M.Pair(
                                M.Char("malformed-rule"),
                                M.Pair(M.Char("expected-left-parenthesis"), M.EmptyList),
                            )
                        else:
                            argument_reversed = M.EmptyList
                            argument_expected = M.truth_value
                            closed = M.false_value
                            argument_remaining = term_remaining
                            while M.IdentityCompare(
                                argument_remaining, M.EmptyList,
                            )() is M.false_value:
                                if M.IdentityCompare(
                                    reason, M.EmptyList,
                                )() is M.false_value:
                                    argument_remaining = M.EmptyList
                                elif M.IdentityCompare(
                                    closed, M.truth_value,
                                )() is M.truth_value:
                                    argument_remaining = M.EmptyList
                                else:
                                    argument = M.Head(argument_remaining)()
                                    if M.IdentityCompare(
                                        argument_expected, M.truth_value,
                                    )() is M.truth_value:
                                        if M.Compare(
                                            argument, M.Char(")"),
                                        )() is M.truth_value:
                                            reason = M.Pair(
                                                M.Char("malformed-rule"),
                                                M.Pair(M.Char("empty-arguments"), M.EmptyList),
                                            )
                                        elif M.Compare(
                                            argument, M.Char(","),
                                        )() is M.truth_value:
                                            reason = M.Pair(
                                                M.Char("malformed-rule"),
                                                M.Pair(M.Char("empty-argument"), M.EmptyList),
                                            )
                                        else:
                                            variable = M.EmptyList
                                            variable_scan = variables
                                            while M.IdentityCompare(
                                                variable_scan, M.EmptyList,
                                            )() is M.false_value:
                                                entry = M.Head(variable_scan)()
                                                if M.Compare(
                                                    M.Head(entry)(), argument,
                                                )() is M.truth_value:
                                                    variable = M.Head(M.Tail(entry)())()
                                                    variable_scan = M.EmptyList
                                                else:
                                                    variable_scan = M.Tail(variable_scan)()
                                            if M.IdentityCompare(
                                                variable, M.EmptyList,
                                            )() is M.truth_value:
                                                variable = M.Pair(
                                                    M.VarTag,
                                                    M.Pair(
                                                        M.Char("?" + argument()),
                                                        M.EmptyList,
                                                    ),
                                                )
                                                variables = M.Pair(
                                                    M.Pair(
                                                        argument,
                                                        M.Pair(variable, M.EmptyList),
                                                    ),
                                                    variables,
                                                )
                                            argument_reversed = M.Pair(
                                                variable, argument_reversed,
                                            )
                                            argument_expected = M.false_value
                                        argument_remaining = M.Tail(argument_remaining)()
                                    else:
                                        if M.Compare(
                                            argument, M.Char(")"),
                                        )() is M.truth_value:
                                            closed = M.truth_value
                                            argument_remaining = M.Tail(argument_remaining)()
                                        elif M.Compare(
                                            argument, M.Char(","),
                                        )() is M.truth_value:
                                            argument_expected = M.truth_value
                                            argument_remaining = M.Tail(argument_remaining)()
                                        else:
                                            reason = M.Pair(
                                                M.Char("malformed-rule"),
                                                M.Pair(M.Char("expected-comma-or-right-parenthesis"), M.EmptyList),
                                            )
                            if M.IdentityCompare(closed, M.truth_value)() is M.false_value:
                                reason = M.Pair(
                                    M.Char("malformed-rule"),
                                    M.Pair(M.Char("missing-right-parenthesis"), M.EmptyList),
                                )
                            else:
                                found_constructor = M.EmptyList
                                constructor_scan = constructors
                                while M.IdentityCompare(
                                    constructor_scan, M.EmptyList,
                                )() is M.false_value:
                                    constructor_entry = M.Head(constructor_scan)()
                                    if M.Compare(
                                        M.Head(constructor_entry)(), predicate,
                                    )() is M.truth_value:
                                        found_constructor = M.Head(
                                            M.Tail(constructor_entry)(),
                                        )()
                                        constructor_scan = M.EmptyList
                                    else:
                                        constructor_scan = M.Tail(constructor_scan)()
                                if M.IdentityCompare(
                                    found_constructor, M.EmptyList,
                                )() is M.truth_value:
                                    reason = M.Pair(
                                        M.Char("unknown-constructor"),
                                        M.Pair(predicate, M.EmptyList),
                                    )
                                else:
                                    term = M.Pair(
                                        found_constructor,
                                        M.Reverse(argument_reversed)(),
                                    )
                                    if M.IdentityCompare(
                                        arrow_seen, M.truth_value,
                                    )() is M.truth_value:
                                        conclusion = term
                                    else:
                                        premises_reversed = M.Pair(
                                            term, premises_reversed,
                                        )
                                    expect_term = M.false_value
                                    remaining = argument_remaining
        if M.IdentityCompare(reason, M.EmptyList)() is M.truth_value:
            if M.IdentityCompare(arrow_seen, M.truth_value)() is M.false_value:
                reason = M.Pair(
                    M.Char("malformed-rule"),
                    M.Pair(M.Char("missing-arrow"), M.EmptyList),
                )
            elif M.IdentityCompare(expect_term, M.truth_value)() is M.truth_value:
                reason = M.Pair(
                    M.Char("malformed-rule"),
                    M.Pair(M.Char("missing-conclusion"), M.EmptyList),
                )
            elif M.IdentityCompare(conclusion, M.EmptyList)() is M.truth_value:
                reason = M.Pair(
                    M.Char("malformed-rule"),
                    M.Pair(M.Char("missing-conclusion"), M.EmptyList),
                )
        if M.IdentityCompare(reason, M.EmptyList)() is M.truth_value:
            rule = P.MultiRule(
                M.Reverse(premises_reversed)(),
                conclusion,
            )()
            self.result = M.Pair(rule, M.Pair(M.EmptyList, M.EmptyList))
        else:
            self.result = M.Pair(M.EmptyList, M.Pair(reason, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                M.Char(text),
                M.Pair(reading_policy, M.Pair(digit_words, M.Pair(constructors, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ParseRuleText(M.Edge):
    """Parse nested predicate applications into one monotone MultiRule.

    The parser is a machine-state walk over the ordinary token chain. A
    frame on the stack is predicate, reversed arguments, and whether the
    next item must be an argument. Closing a frame builds its term and
    returns it to the parent frame, so `Divides(k, Add(a, b))` is handled
    without a second string parser. Pack and learned constructors are
    reused by the supplied word-to-constructor chain; a new predicate at
    this boundary receives a persistent atom of its own.
    """

    def __init__(self, text, reading_policy, digit_words, constructors,
                 ground=M.false_value):
        empty = M.EmptyList
        tokens = WordsOfText(text, reading_policy, digit_words)()
        remaining = tokens
        stack = empty
        variables = empty
        variable_names = M.Pair(
            M.Char("substance"),
            M.Pair(
                M.Char("place"),
                M.Pair(
                    M.Char("time"),
                    M.Pair(
                        M.Char("a"),
                        M.Pair(
                            M.Char("b"),
                            M.Pair(
                                M.Char("c"),
                                M.Pair(
                                    M.Char("k"),
                                    M.Pair(
                                        M.Char("m"),
                                        M.Pair(
                                            M.Char("n"),
                                            M.Pair(
                                                M.Char("p"),
                                                M.Pair(
                                                    M.Char("q"),
                                                    M.Pair(
                                                        M.Char("s"),
                                                        M.Pair(
                                                            M.Char("t"),
                                                            M.Pair(
                                                                M.Char("x"),
                                                                M.Pair(
                                                                    M.Char("y"),
                                                                    M.Pair(
                                                                        M.Char("z"),
                                                                        empty,
                                                                    ),
                                                                ),
                                                            ),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        premises_reversed = empty
        conclusion = empty
        arrow_seen = M.false_value
        expect_term = M.truth_value
        reason = empty
        ground_arguments = M.false_value
        if M.IdentityCompare(ground, M.truth_value)() is M.truth_value:
            ground_arguments = M.truth_value
        elif M.Compare(
            ground, M.Char("exactly-one"),
        )() is M.truth_value:
            ground_arguments = M.truth_value

        while M.IdentityCompare(reason, empty)() is M.truth_value:
            if M.IdentityCompare(stack, empty)() is M.false_value:
                if M.IdentityCompare(remaining, empty)() is M.truth_value:
                    reason = M.Pair(
                        M.Char("malformed-rule"),
                        M.Pair(M.Char("missing-right-parenthesis"), empty),
                    )
                else:
                    frame = M.Head(stack)()
                    predicate = M.Head(frame)()
                    arguments_reversed = M.Head(M.Tail(frame)())()
                    argument_expected = M.Head(
                        M.Tail(M.Tail(frame)())(),
                    )()
                    token = M.Head(remaining)()
                    if M.IdentityCompare(
                        argument_expected, M.truth_value,
                    )() is M.truth_value:
                        if M.Compare(token, M.Char(")"))() is M.truth_value:
                            reason = M.Pair(
                                M.Char("malformed-rule"),
                                M.Pair(M.Char("empty-arguments"), empty),
                            )
                        elif M.Compare(token, M.Char(","))() is M.truth_value:
                            reason = M.Pair(
                                M.Char("malformed-rule"),
                                M.Pair(M.Char("empty-argument"), empty),
                            )
                        else:
                            after_token = M.Tail(remaining)()
                            nested = M.false_value
                            if M.IdentityCompare(
                                after_token, empty,
                            )() is M.false_value:
                                if M.Compare(
                                    M.Head(after_token)(), M.Char("("),
                                )() is M.truth_value:
                                    nested = M.truth_value
                            if M.IdentityCompare(nested, M.truth_value)() is M.truth_value:
                                nested_frame = M.Pair(
                                    token,
                                    M.Pair(
                                        empty,
                                        M.Pair(M.truth_value, empty),
                                    ),
                                )
                                stack = M.Pair(nested_frame, stack)
                                remaining = M.Tail(after_token)()
                            else:
                                argument_value = M.EmptyList
                                if M.IdentityCompare(
                                    ground_arguments, M.truth_value,
                                )() is M.truth_value:
                                    argument_value = M.Char(token())
                                else:
                                    # A number word is a constant, never a
                                    # variable: the digit chain is the one
                                    # grammar authority on which words name
                                    # numbers, so rules can state arithmetic
                                    # with numerals without any host parsing.
                                    is_number_word = M.false_value
                                    digit_scan = digit_words
                                    while M.IdentityCompare(
                                        digit_scan, empty,
                                    )() is M.false_value:
                                        digit_entry = M.Head(digit_scan)()
                                        if M.Compare(
                                            M.Head(M.Tail(digit_entry)())(),
                                            token,
                                        )() is M.truth_value:
                                            is_number_word = M.truth_value
                                            digit_scan = empty
                                        else:
                                            digit_scan = M.Tail(digit_scan)()
                                    if M.IdentityCompare(
                                        is_number_word, M.truth_value,
                                    )() is M.truth_value:
                                        argument_value = M.Char(token())
                                if M.IdentityCompare(
                                    argument_value, empty,
                                )() is M.truth_value:
                                    is_variable = M.false_value
                                    variable_name_scan = variable_names
                                    while M.IdentityCompare(
                                        variable_name_scan, empty,
                                    )() is M.false_value:
                                        if M.Compare(
                                            M.Head(variable_name_scan)(), token,
                                        )() is M.truth_value:
                                            is_variable = M.truth_value
                                            variable_name_scan = empty
                                        else:
                                            variable_name_scan = M.Tail(variable_name_scan)()
                                    if M.IdentityCompare(
                                        is_variable, M.truth_value,
                                    )() is M.truth_value:
                                        variable_scan = variables
                                        while M.IdentityCompare(
                                            variable_scan, empty,
                                        )() is M.false_value:
                                            variable_entry = M.Head(variable_scan)()
                                            if M.Compare(
                                                M.Head(variable_entry)(), token,
                                            )() is M.truth_value:
                                                argument_value = M.Head(
                                                    M.Tail(variable_entry)(),
                                                )()
                                                variable_scan = empty
                                            else:
                                                variable_scan = M.Tail(variable_scan)()
                                        if M.IdentityCompare(
                                            argument_value, empty,
                                        )() is M.truth_value:
                                            argument_value = M.Pair(
                                                M.VarTag,
                                                M.Pair(
                                                    M.Char("?" + token()),
                                                    empty,
                                                ),
                                            )
                                            variables = M.Pair(
                                                M.Pair(
                                                    token,
                                                    M.Pair(argument_value, empty),
                                                ),
                                                variables,
                                            )
                                    else:
                                        argument_value = M.Char(token())
                                updated_frame = M.Pair(
                                    predicate,
                                    M.Pair(
                                        M.Pair(argument_value, arguments_reversed),
                                        M.Pair(M.false_value, empty),
                                    ),
                                )
                                stack = M.Pair(
                                    updated_frame,
                                    M.Tail(stack)(),
                                )
                                remaining = M.Tail(remaining)()
                    elif M.Compare(token, M.Char(","))() is M.truth_value:
                        updated_frame = M.Pair(
                            predicate,
                            M.Pair(
                                arguments_reversed,
                                M.Pair(M.truth_value, empty),
                            ),
                        )
                        stack = M.Pair(
                            updated_frame,
                            M.Tail(stack)(),
                        )
                        remaining = M.Tail(remaining)()
                    elif M.Compare(token, M.Char(")"))() is M.truth_value:
                        found_constructor = empty
                        constructor_scan = constructors
                        while M.IdentityCompare(
                            constructor_scan, empty,
                        )() is M.false_value:
                            constructor_entry = M.Head(constructor_scan)()
                            if M.Compare(
                                M.Head(constructor_entry)(), predicate,
                            )() is M.truth_value:
                                found_constructor = M.Head(
                                    M.Tail(constructor_entry)(),
                                )()
                                constructor_scan = empty
                            else:
                                constructor_scan = M.Tail(constructor_scan)()
                        if M.IdentityCompare(
                            found_constructor, empty,
                        )() is M.truth_value:
                            # A rule may introduce a new predicate symbol.
                            # Pack constructors retain their canonical label;
                            # a new micromystery predicate is represented by
                            # its own atom and becomes known through this
                            # taught rule or fact.
                            found_constructor = predicate
                        if M.IdentityCompare(
                            found_constructor, empty,
                        )() is M.false_value:
                            term = M.Pair(
                                found_constructor,
                                M.Reverse(arguments_reversed)(),
                            )
                            parent_stack = M.Tail(stack)()
                            stack = parent_stack
                            remaining = M.Tail(remaining)()
                            if M.IdentityCompare(
                                parent_stack, empty,
                            )() is M.false_value:
                                parent = M.Head(parent_stack)()
                                parent_predicate = M.Head(parent)()
                                parent_arguments = M.Head(
                                    M.Tail(parent)(),
                                )()
                                parent_updated = M.Pair(
                                    parent_predicate,
                                    M.Pair(
                                        M.Pair(term, parent_arguments),
                                        M.Pair(M.false_value, empty),
                                    ),
                                )
                                stack = M.Pair(
                                    parent_updated,
                                    M.Tail(parent_stack)(),
                                )
                            else:
                                if M.IdentityCompare(
                                    arrow_seen, M.truth_value,
                                )() is M.truth_value:
                                    if M.IdentityCompare(
                                        conclusion, empty,
                                    )() is M.false_value:
                                        reason = M.Pair(
                                            M.Char("malformed-rule"),
                                            M.Pair(M.Char("extra-conclusion"), empty),
                                        )
                                    else:
                                        conclusion = term
                                else:
                                    premises_reversed = M.Pair(
                                        term, premises_reversed,
                                    )
                                expect_term = M.false_value
                    else:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(
                                M.Char("expected-comma-or-right-parenthesis"),
                                empty,
                            ),
                        )
            elif M.IdentityCompare(remaining, empty)() is M.truth_value:
                if M.Compare(ground, M.Char("exactly-one"))() is M.truth_value:
                    facts = M.Reverse(premises_reversed)()
                    if M.IdentityCompare(facts, empty)() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("missing-case"), empty),
                        )
                    elif M.IdentityCompare(
                        M.Tail(facts)(), empty,
                    )() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("case-needs-two-candidates"), empty),
                        )
                    else:
                        reason = M.Char("case-split-parse-complete")
                elif M.IdentityCompare(ground, M.truth_value)() is M.truth_value:
                    facts = M.Reverse(premises_reversed)()
                    if M.IdentityCompare(facts, empty)() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("missing-fact"), empty),
                        )
                    elif M.IdentityCompare(
                        M.Tail(facts)(), empty,
                    )() is M.false_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("multiple-facts"), empty),
                        )
                    else:
                        reason = M.Char("fact-parse-complete")
                elif M.IdentityCompare(arrow_seen, M.truth_value)() is M.false_value:
                    reason = M.Pair(
                        M.Char("malformed-rule"),
                        M.Pair(M.Char("missing-arrow"), empty),
                    )
                elif M.IdentityCompare(expect_term, M.truth_value)() is M.truth_value:
                    reason = M.Pair(
                        M.Char("malformed-rule"),
                        M.Pair(M.Char("missing-conclusion"), empty),
                    )
                elif M.IdentityCompare(conclusion, empty)() is M.truth_value:
                    reason = M.Pair(
                        M.Char("malformed-rule"),
                        M.Pair(M.Char("missing-conclusion"), empty),
                    )
                else:
                    reason = M.Char("rule-parse-complete")
            else:
                token = M.Head(remaining)()
                if M.Compare(token, M.Char(","))() is M.truth_value:
                    if M.IdentityCompare(expect_term, M.truth_value)() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("unexpected-comma"), empty),
                        )
                    else:
                        expect_term = M.truth_value
                        remaining = M.Tail(remaining)()
                elif M.Compare(token, M.Char("->"))() is M.truth_value:
                    if M.IdentityCompare(arrow_seen, M.truth_value)() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("multiple-arrows"), empty),
                        )
                    elif M.IdentityCompare(expect_term, M.truth_value)() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("missing-premise"), empty),
                        )
                    elif M.IdentityCompare(
                        premises_reversed, empty,
                    )() is M.truth_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("missing-premise"), empty),
                        )
                    else:
                        arrow_seen = M.truth_value
                        expect_term = M.truth_value
                        remaining = M.Tail(remaining)()
                elif M.IdentityCompare(expect_term, M.truth_value)() is M.false_value:
                    reason = M.Pair(
                        M.Char("malformed-rule"),
                        M.Pair(M.Char("missing-comma"), empty),
                    )
                else:
                    after_predicate = M.Tail(remaining)()
                    opened = M.false_value
                    if M.IdentityCompare(
                        after_predicate, empty,
                    )() is M.false_value:
                        if M.Compare(
                            M.Head(after_predicate)(), M.Char("("),
                        )() is M.truth_value:
                            opened = M.truth_value
                    if M.IdentityCompare(opened, M.truth_value)() is M.false_value:
                        reason = M.Pair(
                            M.Char("malformed-rule"),
                            M.Pair(M.Char("expected-left-parenthesis"), empty),
                        )
                    else:
                        frame = M.Pair(
                            token,
                            M.Pair(
                                empty,
                                M.Pair(M.truth_value, empty),
                            ),
                        )
                        stack = M.Pair(frame, stack)
                        remaining = M.Tail(after_predicate)()
        if M.Compare(reason, M.Char("case-split-parse-complete"))() is M.truth_value:
            facts = M.Reverse(premises_reversed)()
            exactly_one = ExactlyOne(facts)()
            self.result = M.Pair(
                CaseSplit(exactly_one)(),
                M.Pair(empty, empty),
            )
        elif M.Compare(reason, M.Char("fact-parse-complete"))() is M.truth_value:
            fact = M.Head(M.Reverse(premises_reversed)())()
            self.result = M.Pair(fact, M.Pair(empty, empty))
        elif M.Compare(reason, M.Char("rule-parse-complete"))() is M.truth_value:
            rule = P.MultiRule(
                M.Reverse(premises_reversed)(),
                conclusion,
            )()
            self.result = M.Pair(rule, M.Pair(empty, empty))
        else:
            self.result = M.Pair(empty, M.Pair(reason, empty))
        super().__init__(
            inputs=M.Pair(
                M.Char(text),
                M.Pair(
                    reading_policy,
                    M.Pair(
                        digit_words,
                        M.Pair(constructors, M.Pair(ground, empty)),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


ONTOLOGY_FACT_CAP = M.GMPRep("200")


class ParseWordText(M.Edge):
    """Parse one constrained word-teaching sentence into ontology facts."""

    def __init__(self, text, reading_policy, digit_words):
        empty = M.EmptyList
        words = WordsOfText(text, reading_policy, digit_words)()
        self.result = M.Pair(empty, M.Pair(empty, empty))
        if M.IdentityCompare(words, empty)() is M.false_value:
            surface = M.Head(words)()
            rest = M.Tail(words)()
            if M.IdentityCompare(rest, empty)() is M.false_value:
                relation_word = M.Head(rest)()
                remaining = M.Tail(rest)()
                accepted = M.false_value
                concept_text = ""
                concept_last = empty
                concept_modifier = empty
                first_concept = M.truth_value
                concept_scan = remaining
                if M.Compare(
                    relation_word, M.Char("means"),
                )() is M.truth_value:
                    while M.IdentityCompare(concept_scan, empty)() is M.false_value:
                        concept_word = M.Head(concept_scan)()
                        if M.IdentityCompare(
                            first_concept, M.truth_value,
                        )() is M.truth_value:
                            concept_modifier = concept_word
                        if M.IdentityCompare(
                            first_concept, M.truth_value,
                        )() is M.false_value:
                            concept_text = concept_text + "_"
                        concept_text = concept_text + concept_word()
                        concept_last = concept_word
                        first_concept = M.false_value
                        concept_scan = M.Tail(concept_scan)()
                    if M.Compare(
                        M.Char(concept_text), M.Char(""),
                    )() is M.false_value:
                        accepted = M.truth_value
                        word_fact = M.Pair(
                            Lmod.WordLabel,
                            M.Pair(surface, M.Pair(surface, empty)),
                        )
                        isa_fact = M.Pair(
                            Lmod.IsALabel,
                            M.Pair(
                                surface,
                                M.Pair(M.Char(concept_text), empty),
                            ),
                        )
                        relation_facts = M.Pair(isa_fact, empty)
                        if M.IdentityCompare(
                            concept_modifier, empty,
                        )() is M.false_value:
                            if M.Compare(
                                concept_modifier, concept_last,
                            )() is M.false_value:
                                modifier_fact = M.Pair(
                                    Lmod.ModifierOfLabel,
                                    M.Pair(
                                        concept_modifier,
                                        M.Pair(concept_last, empty),
                                    ),
                                )
                                relation_facts = M.Pair(
                                    isa_fact,
                                    M.Pair(modifier_fact, empty),
                                )
                        self.result = M.Pair(
                            M.Pair(word_fact, relation_facts),
                            M.Pair(empty, empty),
                        )
                else:
                    copula = M.false_value
                    if M.Compare(
                        relation_word, M.Char("is"),
                    )() is M.truth_value:
                        copula = M.truth_value
                    elif M.Compare(
                        relation_word, M.Char("are"),
                    )() is M.truth_value:
                        copula = M.truth_value
                    if M.IdentityCompare(copula, M.truth_value)() is M.truth_value:
                        if M.IdentityCompare(remaining, empty)() is M.false_value:
                            article = M.Head(remaining)()
                            article_word = M.false_value
                            if M.Compare(article, M.Char("a"))() is M.truth_value:
                                article_word = M.truth_value
                            elif M.Compare(article, M.Char("an"))() is M.truth_value:
                                article_word = M.truth_value
                            elif M.Compare(article, M.Char("the"))() is M.truth_value:
                                article_word = M.truth_value
                            if M.IdentityCompare(article_word, M.truth_value)() is M.truth_value:
                                remaining = M.Tail(remaining)()
                        worn = M.false_value
                        if M.IdentityCompare(remaining, empty)() is M.false_value:
                            if M.Compare(
                                M.Head(remaining)(), M.Char("worn"),
                            )() is M.truth_value:
                                after_worn = M.Tail(remaining)()
                                if M.IdentityCompare(
                                    after_worn, empty,
                                )() is M.false_value:
                                    if M.Compare(
                                        M.Head(after_worn)(), M.Char("by"),
                                    )() is M.truth_value:
                                        worn = M.truth_value
                                        remaining = M.Tail(after_worn)()
                        concept_scan = remaining
                        while M.IdentityCompare(concept_scan, empty)() is M.false_value:
                            concept_word = M.Head(concept_scan)()
                            if M.IdentityCompare(
                                first_concept, M.truth_value,
                            )() is M.false_value:
                                concept_text = concept_text + "_"
                            concept_text = concept_text + concept_word()
                            first_concept = M.false_value
                            concept_scan = M.Tail(concept_scan)()
                        if M.Compare(
                            M.Char(concept_text), M.Char(""),
                        )() is M.false_value:
                            accepted = M.truth_value
                            word_fact = M.Pair(
                                Lmod.WordLabel,
                                M.Pair(surface, M.Pair(surface, empty)),
                            )
                            if M.IdentityCompare(worn, M.truth_value)() is M.truth_value:
                                relation_fact = M.Pair(
                                    Lmod.WornByLabel,
                                    M.Pair(
                                        surface,
                                        M.Pair(M.Char(concept_text), empty),
                                    ),
                                )
                            else:
                                relation_fact = M.Pair(
                                    Lmod.IsALabel,
                                    M.Pair(
                                        surface,
                                        M.Pair(M.Char(concept_text), empty),
                                    ),
                                )
                            self.result = M.Pair(
                                M.Pair(
                                    word_fact,
                                    M.Pair(relation_fact, empty),
                                ),
                                M.Pair(empty, empty),
                            )
                if M.IdentityCompare(accepted, M.truth_value)() is M.false_value:
                    self.result = M.Pair(
                        empty,
                        M.Pair(
                            M.Pair(
                                M.Char("malformed-word"),
                                M.Pair(M.Char("expected-means-or-is"), empty),
                            ),
                            empty,
                        ),
                    )
            else:
                self.result = M.Pair(
                    empty,
                    M.Pair(
                        M.Pair(
                            M.Char("malformed-word"),
                            M.Pair(M.Char("missing-relation"), empty),
                        ),
                        empty,
                    ),
                )
        super().__init__(
            inputs=M.Pair(
                M.Char(text),
                M.Pair(reading_policy, M.Pair(digit_words, empty)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GapRecord(M.Edge):
    """A graph-stored open vocabulary gap."""

    def __init__(self, gap):
        self.result = M.Pair(
            Lmod.GapRecordLabel,
            M.Pair(gap, M.EmptyList),
        )
        super().__init__(inputs=M.Pair(gap, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GapRecordGap(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(record)())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TermContains(M.Edge):
    """Structural occurrence test using the machine comparison relation."""

    def __init__(self, term, target):
        self.result = M.false_value
        agenda = M.Pair(term, M.EmptyList)
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            candidate = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.Compare(candidate, target)() is M.truth_value:
                self.result = M.truth_value
                agenda = M.EmptyList
            elif M.IsPair(candidate)() is M.truth_value:
                children = M.Tail(candidate)()
                while M.IdentityCompare(children, M.EmptyList)() is M.false_value:
                    agenda = M.Pair(M.Head(children)(), agenda)
                    children = M.Tail(children)()
        super().__init__(
            inputs=M.Pair(term, M.Pair(target, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstalledGaps(M.Edge):
    """Open gaps already stored in the learned graph."""

    def __init__(self, graph_version):
        reversed_gaps = M.EmptyList
        agenda = GraphNodes(graph_version)()
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            node = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.IsPair(node)() is M.truth_value:
                node_head = M.Head(node)()
                if M.IsPair(node_head)() is M.truth_value:
                    nested = node
                    while M.IdentityCompare(nested, M.EmptyList)() is M.false_value:
                        agenda = M.Pair(M.Head(nested)(), agenda)
                        nested = M.Tail(nested)()
                elif M.Compare(
                    node_head, Lmod.GapRecordLabel,
                )() is M.truth_value:
                    gap = GapRecordGap(node)()
                    if M.Compare(
                        GapOpen(gap, graph_version)(),
                        M.truth_value,
                    )() is M.truth_value:
                        reversed_gaps = M.Pair(gap, reversed_gaps)
        self.result = M.Reverse(reversed_gaps)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GapOpen(M.Edge):
    """Whether a detected gap remains open in a learned version."""

    def __init__(self, gap, graph_version):
        self.result = M.false_value
        facts = InstalledTaughtFacts(graph_version)()
        gap_head = M.EmptyList
        if M.IsPair(gap)() is M.truth_value:
            gap_head = M.Head(gap)()
        target = M.EmptyList
        if M.IsPair(gap)() is M.truth_value:
            target = M.Head(M.Tail(gap)())()
        known_word = M.false_value
        known_concept = M.false_value
        usage = M.false_value
        fact_head_match = M.false_value
        scan = facts
        while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
            fact = M.Head(scan)()
            if M.IsPair(fact)() is M.truth_value:
                head = M.Head(fact)()
                args = M.Tail(fact)()
                if M.Compare(head, target)() is M.truth_value:
                    fact_head_match = M.truth_value
                if M.Compare(head, Lmod.WordLabel)() is M.truth_value:
                    if M.IdentityCompare(args, M.EmptyList)() is M.false_value:
                        if M.Compare(M.Head(args)(), target)() is M.truth_value:
                            known_word = M.truth_value
                        if M.IdentityCompare(
                            M.Tail(args)(), M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(M.Tail(args)())(), target,
                            )() is M.truth_value:
                                known_concept = M.truth_value
                elif M.Compare(head, Lmod.IsALabel)() is M.truth_value:
                    if M.IdentityCompare(args, M.EmptyList)() is M.false_value:
                        if M.Compare(M.Head(args)(), target)() is M.truth_value:
                            known_concept = M.truth_value
                        if M.IdentityCompare(
                            M.Tail(args)(), M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(M.Tail(args)())(), target,
                            )() is M.truth_value:
                                known_concept = M.truth_value
                elif M.Compare(head, Lmod.ModifierOfLabel)() is M.false_value:
                    if TermContains(fact, target)() is M.truth_value:
                        usage = M.truth_value
            scan = M.Tail(scan)()
        if M.Compare(gap_head, Lmod.UngroundedModifierLabel)() is M.truth_value:
            self.result = M.false_value
            if M.IdentityCompare(known_word, M.truth_value)() is M.truth_value:
                self.result = M.false_value
            else:
                self.result = M.truth_value
        elif M.Compare(gap_head, Lmod.UndefinedConceptLabel)() is M.truth_value:
            if M.IdentityCompare(known_concept, M.truth_value)() is M.false_value:
                self.result = M.truth_value
        elif M.Compare(gap_head, Lmod.ResidualGapLabel)() is M.truth_value:
            self.result = M.truth_value
            if M.IdentityCompare(fact_head_match, M.truth_value)() is M.truth_value:
                self.result = M.false_value
        elif M.Compare(gap_head, Lmod.NoUsageExampleLabel)() is M.truth_value:
            if M.IdentityCompare(usage, M.truth_value)() is M.false_value:
                self.result = M.truth_value
        elif M.Compare(gap_head, Lmod.NoParentLabel)() is M.truth_value:
            if M.IdentityCompare(known_word, M.truth_value)() is M.false_value:
                if M.IdentityCompare(
                    known_concept, M.truth_value,
                )() is M.false_value:
                    self.result = M.truth_value
        elif M.Compare(gap_head, Lmod.DanglingReferenceLabel)() is M.truth_value:
            self.result = M.truth_value
            rule_scan = InstalledTaughtRules(graph_version)()
            while M.IdentityCompare(rule_scan, M.EmptyList)() is M.false_value:
                rule_replacement = P.RuleReplacement(
                    M.Head(rule_scan)(),
                )()
                if M.IsPair(rule_replacement)() is M.truth_value:
                    if M.Compare(
                        M.Head(rule_replacement)(), target,
                    )() is M.truth_value:
                        self.result = M.false_value
                        rule_scan = M.EmptyList
                if M.IdentityCompare(rule_scan, M.EmptyList)() is M.false_value:
                    rule_scan = M.Tail(rule_scan)()
            if M.IdentityCompare(self.result, M.truth_value)() is M.truth_value:
                if M.IdentityCompare(
                    fact_head_match, M.truth_value,
                )() is M.truth_value:
                    self.result = M.false_value
        elif M.Compare(gap_head, Lmod.MissingRenderLawLabel)() is M.truth_value:
            self.result = M.truth_value
            law_scan = GapRenderLaws()()
            while M.IdentityCompare(law_scan, M.EmptyList)() is M.false_value:
                law = M.Head(law_scan)()
                law_pattern = M.Head(GraphNodes(LawLeft(law)())())()
                if M.IsPair(law_pattern)() is M.truth_value:
                    if M.Compare(
                        M.Head(law_pattern)(), target,
                    )() is M.truth_value:
                        self.result = M.false_value
                        law_scan = M.EmptyList
                if M.IdentityCompare(law_scan, M.EmptyList)() is M.false_value:
                    law_scan = M.Tail(law_scan)()
        super().__init__(
            inputs=M.Pair(gap, M.Pair(graph_version, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DetectVocabularyGaps(M.Edge):
    """Inspect typed vocabulary facts and emit explicit gap terms."""

    def __init__(self, graph_version):
        facts = InstalledTaughtFacts(graph_version)()
        reversed_undefined = M.EmptyList
        reversed_modifiers = M.EmptyList
        reversed_usage = M.EmptyList
        reversed_constants = M.EmptyList
        scan = facts
        while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
            fact = M.Head(scan)()
            if M.IsPair(fact)() is M.truth_value:
                head = M.Head(fact)()
                args = M.Tail(fact)()
                if M.Compare(head, Lmod.ModifierOfLabel)() is M.truth_value:
                    if M.IdentityCompare(args, M.EmptyList)() is M.false_value:
                        modifier = M.Head(args)()
                        rest = M.Tail(args)()
                        if M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
                            parent = M.Head(rest)()
                            concept_known = M.false_value
                            word_scan = facts
                            while M.IdentityCompare(
                                word_scan, M.EmptyList,
                            )() is M.false_value:
                                word_fact = M.Head(word_scan)()
                                if M.IsPair(word_fact)() is M.truth_value:
                                    word_head = M.Head(word_fact)()
                                    word_args = M.Tail(word_fact)()
                                    if M.Compare(
                                        word_head, Lmod.WordLabel,
                                    )() is M.truth_value:
                                        if M.Compare(
                                            M.Head(word_args)(), parent,
                                        )() is M.truth_value:
                                            concept_known = M.truth_value
                                    elif M.Compare(
                                        word_head, Lmod.IsALabel,
                                    )() is M.truth_value:
                                        if M.Compare(
                                            M.Head(word_args)(), parent,
                                        )() is M.truth_value:
                                            concept_known = M.truth_value
                                        elif M.Compare(
                                            M.Head(M.Tail(word_args)())(),
                                            parent,
                                        )() is M.truth_value:
                                            concept_known = M.truth_value
                                word_scan = M.Tail(word_scan)()
                            if M.IdentityCompare(
                                concept_known, M.false_value,
                            )() is M.truth_value:
                                gap = M.Pair(
                                    Lmod.UndefinedConceptLabel,
                                    M.Pair(parent, M.EmptyList),
                                )
                                if M.Compare(
                                    GapOpen(gap, graph_version)(),
                                    M.truth_value,
                                )() is M.truth_value:
                                    reversed_undefined = M.Pair(
                                        gap,
                                        reversed_undefined,
                                    )
                            word_known = M.false_value
                            word_scan = facts
                            while M.IdentityCompare(
                                word_scan, M.EmptyList,
                            )() is M.false_value:
                                word_fact = M.Head(word_scan)()
                                if M.IsPair(word_fact)() is M.truth_value:
                                    if M.Compare(
                                        M.Head(word_fact)(), Lmod.WordLabel,
                                    )() is M.truth_value:
                                        if M.Compare(
                                            M.Head(M.Tail(word_fact)())(),
                                            modifier,
                                        )() is M.truth_value:
                                            word_known = M.truth_value
                                word_scan = M.Tail(word_scan)()
                            if M.IdentityCompare(
                                word_known, M.false_value,
                            )() is M.truth_value:
                                reversed_modifiers = M.Pair(
                                    M.Pair(
                                        Lmod.UngroundedModifierLabel,
                                        M.Pair(
                                            modifier,
                                            M.Pair(parent, M.EmptyList),
                                        ),
                                    ),
                                    reversed_modifiers,
                                )
                elif M.Compare(head, Lmod.WordLabel)() is M.truth_value:
                    if M.IdentityCompare(args, M.EmptyList)() is M.false_value:
                        word = M.Head(args)()
                        used = M.false_value
                        usage_scan = facts
                        while M.IdentityCompare(
                            usage_scan, M.EmptyList,
                        )() is M.false_value:
                            usage_fact = M.Head(usage_scan)()
                            if M.IsPair(usage_fact)() is M.truth_value:
                                usage_head = M.Head(usage_fact)()
                                ontology_fact = M.false_value
                                if M.Compare(
                                    usage_head, Lmod.WordLabel,
                                )() is M.truth_value:
                                    ontology_fact = M.truth_value
                                elif M.Compare(
                                    usage_head, Lmod.IsALabel,
                                )() is M.truth_value:
                                    ontology_fact = M.truth_value
                                elif M.Compare(
                                    usage_head, Lmod.ModifierOfLabel,
                                )() is M.truth_value:
                                    ontology_fact = M.truth_value
                                if M.IdentityCompare(
                                    ontology_fact, M.false_value,
                                )() is M.truth_value:
                                    if TermContains(usage_fact, word)() is M.truth_value:
                                        used = M.truth_value
                            usage_scan = M.Tail(usage_scan)()
                        if M.IdentityCompare(used, M.false_value)() is M.truth_value:
                            reversed_usage = M.Pair(
                                M.Pair(
                                    Lmod.NoUsageExampleLabel,
                                    M.Pair(word, M.EmptyList),
                                ),
                                reversed_usage,
                            )
                else:
                    arg_stack = M.Pair(args, M.EmptyList)
                    while M.IdentityCompare(
                        arg_stack, M.EmptyList,
                    )() is M.false_value:
                        arg_chain = M.Head(arg_stack)()
                        arg_stack = M.Tail(arg_stack)()
                        while M.IdentityCompare(
                            arg_chain, M.EmptyList,
                        )() is M.false_value:
                            arg_item = M.Head(arg_chain)()
                            if M.IsPair(arg_item)() is M.truth_value:
                                arg_stack = M.Pair(
                                    M.Tail(arg_item)(), arg_stack,
                                )
                            else:
                                if ChainHasTerm(
                                    reversed_constants, arg_item,
                                )() is M.false_value:
                                    reversed_constants = M.Pair(
                                        arg_item, reversed_constants,
                                    )
                            arg_chain = M.Tail(arg_chain)()
            scan = M.Tail(scan)()
        reversed_noparent = M.EmptyList
        constant_scan = reversed_constants
        while M.IdentityCompare(constant_scan, M.EmptyList)() is M.false_value:
            constant = M.Head(constant_scan)()
            constant_word = M.false_value
            constant_isa = M.false_value
            known_scan = facts
            while M.IdentityCompare(known_scan, M.EmptyList)() is M.false_value:
                known_fact = M.Head(known_scan)()
                if M.IsPair(known_fact)() is M.truth_value:
                    known_head = M.Head(known_fact)()
                    known_args = M.Tail(known_fact)()
                    if M.Compare(known_head, Lmod.WordLabel)() is M.truth_value:
                        if M.IdentityCompare(
                            known_args, M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(known_args)(), constant,
                            )() is M.truth_value:
                                constant_word = M.truth_value
                            if M.IdentityCompare(
                                M.Tail(known_args)(), M.EmptyList,
                            )() is M.false_value:
                                if M.Compare(
                                    M.Head(M.Tail(known_args)())(), constant,
                                )() is M.truth_value:
                                    constant_word = M.truth_value
                    elif M.Compare(known_head, Lmod.IsALabel)() is M.truth_value:
                        if M.IdentityCompare(
                            known_args, M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(known_args)(), constant,
                            )() is M.truth_value:
                                constant_isa = M.truth_value
                            if M.IdentityCompare(
                                M.Tail(known_args)(), M.EmptyList,
                            )() is M.false_value:
                                if M.Compare(
                                    M.Head(M.Tail(known_args)())(), constant,
                                )() is M.truth_value:
                                    constant_isa = M.truth_value
                known_scan = M.Tail(known_scan)()
            if M.IdentityCompare(constant_word, M.truth_value)() is M.false_value:
                if M.IdentityCompare(
                    constant_isa, M.truth_value,
                )() is M.false_value:
                    reversed_noparent = M.Pair(
                        M.Pair(
                            Lmod.NoParentLabel,
                            M.Pair(constant, M.EmptyList),
                        ),
                        reversed_noparent,
                    )
            constant_scan = M.Tail(constant_scan)()
        reversed_dangling = M.EmptyList
        taught_rules = InstalledTaughtRules(graph_version)()
        rule_scan = taught_rules
        while M.IdentityCompare(rule_scan, M.EmptyList)() is M.false_value:
            taught_rule = M.Head(rule_scan)()
            rule_premises = P.RulePremises(taught_rule)()
            rule_replacement = P.RuleReplacement(taught_rule)()
            rule_signature = M.Pair(
                rule_premises, M.Pair(rule_replacement, M.EmptyList),
            )
            premise_scan = rule_premises
            while M.IdentityCompare(
                premise_scan, M.EmptyList,
            )() is M.false_value:
                premise = M.Head(premise_scan)()
                if M.IsPair(premise)() is M.truth_value:
                    premise_head = M.Head(premise)()
                    derivable = M.false_value
                    fact_scan = facts
                    while M.IdentityCompare(
                        fact_scan, M.EmptyList,
                    )() is M.false_value:
                        fact_candidate = M.Head(fact_scan)()
                        if M.IsPair(fact_candidate)() is M.truth_value:
                            if M.Compare(
                                M.Head(fact_candidate)(), premise_head,
                            )() is M.truth_value:
                                derivable = M.truth_value
                                fact_scan = M.EmptyList
                        if M.IdentityCompare(
                            fact_scan, M.EmptyList,
                        )() is M.false_value:
                            fact_scan = M.Tail(fact_scan)()
                    if M.IdentityCompare(
                        derivable, M.false_value,
                    )() is M.truth_value:
                        head_scan = taught_rules
                        while M.IdentityCompare(
                            head_scan, M.EmptyList,
                        )() is M.false_value:
                            other_replacement = P.RuleReplacement(
                                M.Head(head_scan)(),
                            )()
                            if M.IsPair(other_replacement)() is M.truth_value:
                                if M.Compare(
                                    M.Head(other_replacement)(), premise_head,
                                )() is M.truth_value:
                                    derivable = M.truth_value
                                    head_scan = M.EmptyList
                            if M.IdentityCompare(
                                head_scan, M.EmptyList,
                            )() is M.false_value:
                                head_scan = M.Tail(head_scan)()
                    if M.IdentityCompare(
                        derivable, M.false_value,
                    )() is M.truth_value:
                        already = M.false_value
                        dup_scan = reversed_dangling
                        while M.IdentityCompare(
                            dup_scan, M.EmptyList,
                        )() is M.false_value:
                            dup_gap = M.Head(dup_scan)()
                            if M.Compare(
                                M.Head(M.Tail(dup_gap)())(), premise_head,
                            )() is M.truth_value:
                                if M.Compare(
                                    M.Head(
                                        M.Tail(M.Tail(dup_gap)())(),
                                    )(),
                                    rule_signature,
                                )() is M.truth_value:
                                    already = M.truth_value
                                    dup_scan = M.EmptyList
                            if M.IdentityCompare(
                                dup_scan, M.EmptyList,
                            )() is M.false_value:
                                dup_scan = M.Tail(dup_scan)()
                        if M.IdentityCompare(
                            already, M.false_value,
                        )() is M.truth_value:
                            reversed_dangling = M.Pair(
                                M.Pair(
                                    Lmod.DanglingReferenceLabel,
                                    M.Pair(
                                        premise_head,
                                        M.Pair(rule_signature, M.EmptyList),
                                    ),
                                ),
                                reversed_dangling,
                            )
                premise_scan = M.Tail(premise_scan)()
            rule_scan = M.Tail(rule_scan)()
        all_reversed = M.EmptyList
        for_chain = M.Pair(
            M.Reverse(reversed_undefined)(),
            M.Pair(
                M.Reverse(reversed_modifiers)(),
                M.Pair(
                    M.Reverse(reversed_usage)(),
                    M.Pair(
                        M.Reverse(reversed_noparent)(),
                        M.Pair(
                            M.Reverse(reversed_dangling)(),
                            M.EmptyList,
                        ),
                    ),
                ),
            ),
        )
        chain_scan = for_chain
        while M.IdentityCompare(chain_scan, M.EmptyList)() is M.false_value:
            member_scan = M.Head(chain_scan)()
            while M.IdentityCompare(member_scan, M.EmptyList)() is M.false_value:
                all_reversed = M.Pair(M.Head(member_scan)(), all_reversed)
                member_scan = M.Tail(member_scan)()
            chain_scan = M.Tail(chain_scan)()
        self.result = M.Reverse(all_reversed)()
        super().__init__(inputs=M.Pair(graph_version, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InstallGap(M.Edge):
    """Store a detected gap once in the learned graph."""

    def __init__(self, graph_version, gap):
        found = M.false_value
        agenda = GraphNodes(graph_version)()
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            node = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.IsPair(node)() is M.truth_value:
                node_head = M.Head(node)()
                if M.Compare(
                    node_head, Lmod.GapRecordLabel,
                )() is M.truth_value:
                    if M.Compare(GapRecordGap(node)(), gap)() is M.truth_value:
                        found = M.truth_value
                        agenda = M.EmptyList
        if M.IdentityCompare(found, M.truth_value)() is M.truth_value:
            self.result = graph_version
        else:
            self.result = GraphVersion(
                M.Pair(GapRecord(gap)(), GraphNodes(graph_version)()),
                GraphEdges(graph_version)(),
                GraphVersionInvariants(graph_version)(),
            )()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(gap, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GapRenderLaws(M.Edge):
    """Typed render laws from gap terms to Surface question terms."""

    def __init__(self):
        empty = M.EmptyList
        var_c = M.Pair(M.VarTag, M.Pair(M.Char("?c"), empty))
        var_m = M.Pair(M.VarTag, M.Pair(M.Char("?m"), empty))
        var_o = M.Pair(M.VarTag, M.Pair(M.Char("?o"), empty))
        undefined = M.Pair(
            Lmod.UndefinedConceptLabel,
            M.Pair(var_c, empty),
        )
        modifier = M.Pair(
            Lmod.UngroundedModifierLabel,
            M.Pair(var_m, M.Pair(var_o, empty)),
        )
        no_usage = M.Pair(
            Lmod.NoUsageExampleLabel,
            M.Pair(var_c, empty),
        )
        residual = M.Pair(
            Lmod.ResidualGapLabel,
            M.Pair(var_c, empty),
        )
        undefined_surface = M.Pair(
            Lmod.SurfaceLabel,
            M.Pair(
                M.Pair(
                    M.Char("what"),
                    M.Pair(
                        M.Char("is"),
                        M.Pair(var_c, M.Pair(M.Char("?"), empty)),
                    ),
                ),
                empty,
            ),
        )
        residual_surface = M.Pair(
            Lmod.SurfaceLabel,
            M.Pair(
                M.Pair(
                    M.Char("what"),
                    M.Pair(
                        M.Char("lemma"),
                        M.Pair(
                            M.Char("proves"),
                            M.Pair(var_c, M.Pair(M.Char("?"), empty)),
                        ),
                    ),
                ),
                empty,
            ),
        )
        modifier_surface = M.Pair(
            Lmod.SurfaceLabel,
            M.Pair(
                M.Pair(M.Char("define"), M.Pair(var_m, empty)),
                empty,
            ),
        )
        usage_surface = M.Pair(
            Lmod.SurfaceLabel,
            M.Pair(
                M.Pair(
                    M.Char("give"),
                    M.Pair(
                        M.Char("an"),
                        M.Pair(
                            M.Char("example"),
                            M.Pair(
                                M.Char("of"),
                                M.Pair(var_c, empty),
                            ),
                        ),
                    ),
                ),
                empty,
            ),
        )
        self.result = M.Pair(
            CompileRuleToLaw(P.Rule(undefined, undefined_surface))(),
            M.Pair(
                CompileRuleToLaw(P.Rule(residual, residual_surface))(),
                M.Pair(
                    CompileRuleToLaw(P.Rule(modifier, modifier_surface))(),
                    M.Pair(
                        CompileRuleToLaw(P.Rule(no_usage, usage_surface))(),
                        empty,
                    ),
                ),
            ),
        )
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class RenderGapQuestion(M.Edge):
    """Render one gap through the stored correspondence render laws."""

    def __init__(self, gap):
        self.result = M.EmptyList
        laws = GapRenderLaws()()
        while M.IdentityCompare(laws, M.EmptyList)() is M.false_value:
            law = M.Head(laws)()
            surface = CorrespondenceApply(law, gap)()
            if M.IdentityCompare(surface, M.EmptyList)() is M.false_value:
                self.result = M.Pair(surface, M.Pair(law, M.EmptyList))
                laws = M.EmptyList
            else:
                laws = M.Tail(laws)()
        super().__init__(inputs=M.Pair(gap, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class GapTarget(M.Edge):
    """The primary concept term a gap is about."""

    def __init__(self, gap):
        self.result = M.EmptyList
        if M.IsPair(gap)() is M.truth_value:
            target_chain = M.Tail(gap)()
            if M.IdentityCompare(
                target_chain, M.EmptyList,
            )() is M.false_value:
                self.result = M.Head(target_chain)()
        super().__init__(inputs=M.Pair(gap, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleMentionCount(M.Edge):
    """How many installed rules mention a term in premises or replacement.

    A mention counts the whole premise or replacement term, its
    predicate head, and its argument structure -- the target can be a
    concept in argument position or a predicate symbol in head
    position. The count is a machine GMPRep number.
    """

    def __init__(self, term, graph_version):
        count_text = "0"
        if M.IdentityCompare(term, M.EmptyList)() is M.false_value:
            rule_scan = InstalledTaughtRules(graph_version)()
            while M.IdentityCompare(
                rule_scan, M.EmptyList,
            )() is M.false_value:
                taught_rule = M.Head(rule_scan)()
                mentioned = M.false_value
                premise_scan = P.RulePremises(taught_rule)()
                while M.IdentityCompare(
                    premise_scan, M.EmptyList,
                )() is M.false_value:
                    if M.IdentityCompare(
                        mentioned, M.truth_value,
                    )() is M.truth_value:
                        premise_scan = M.EmptyList
                    else:
                        premise = M.Head(premise_scan)()
                        if M.Compare(
                            premise, term,
                        )() is M.truth_value:
                            mentioned = M.truth_value
                        elif M.IsPair(premise)() is M.truth_value:
                            if M.Compare(
                                M.Head(premise)(), term,
                            )() is M.truth_value:
                                mentioned = M.truth_value
                        if M.IdentityCompare(
                            mentioned, M.truth_value,
                        )() is M.false_value:
                            if TermContains(
                                premise, term,
                            )() is M.truth_value:
                                mentioned = M.truth_value
                        premise_scan = M.Tail(premise_scan)()
                if M.IdentityCompare(
                    mentioned, M.truth_value,
                )() is M.false_value:
                    replacement = P.RuleReplacement(taught_rule)()
                    if M.Compare(
                        replacement, term,
                    )() is M.truth_value:
                        mentioned = M.truth_value
                    elif M.IsPair(replacement)() is M.truth_value:
                        if M.Compare(
                            M.Head(replacement)(), term,
                        )() is M.truth_value:
                            mentioned = M.truth_value
                    if M.IdentityCompare(
                        mentioned, M.truth_value,
                    )() is M.false_value:
                        if TermContains(
                            replacement, term,
                        )() is M.truth_value:
                            mentioned = M.truth_value
                if M.IdentityCompare(
                    mentioned, M.truth_value,
                )() is M.truth_value:
                    count_text = GMPSuccText(count_text)()
                rule_scan = M.Tail(rule_scan)()
        self.result = M.GMPRep(count_text)
        super().__init__(
            inputs=M.Pair(term, M.Pair(graph_version, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GapRankPriority(M.Edge):
    """Depth rank of a gap type in the asking priority chain.

    Deep structural gaps come first (they spawn further structure when
    closed); leaf gaps follow (cheap to close). The priority order is
    itself machine data -- this chain.
    """

    def __init__(self, gap):
        priority_chain = M.Pair(
            Lmod.UndefinedConceptLabel,
            M.Pair(
                Lmod.ResidualGapLabel,
                M.Pair(
                    Lmod.NoParentLabel,
                    M.Pair(
                        Lmod.UngroundedModifierLabel,
                        M.Pair(
                            Lmod.NoUsageExampleLabel,
                            M.Pair(
                                Lmod.DanglingReferenceLabel,
                                M.Pair(
                                    Lmod.MissingRenderLawLabel,
                                    M.EmptyList,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        self.result = M.Char("9")
        gap_head = M.EmptyList
        if M.IsPair(gap)() is M.truth_value:
            gap_head = M.Head(gap)()
        position_text = "0"
        chain_scan = priority_chain
        while M.IdentityCompare(chain_scan, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(chain_scan)(), gap_head)() is M.truth_value:
                self.result = M.Char(position_text)
                chain_scan = M.EmptyList
            else:
                position_text = GMPSuccText(position_text)()
                chain_scan = M.Tail(chain_scan)()
        super().__init__(inputs=M.Pair(gap, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RankGaps(M.Edge):
    """Order open gaps by blast radius as inspectable machine data.

    Ranking keys, in order: rule-mention count of the gap target
    (descending), whether the target blocks the pending query goal,
    then the gap-type depth priority, then detection order. The ranked
    chain holds RankedGaps records and is built by chain insertion --
    no host sort.
    """

    def __init__(self, gaps, goal, graph_version):
        ranked = M.EmptyList
        scan = gaps
        while M.IdentityCompare(scan, M.EmptyList)() is M.false_value:
            gap = M.Head(scan)()
            gap_target = GapTarget(gap)()
            gap_count = RuleMentionCount(gap_target, graph_version)()
            gap_count_text = M.GMPRepText(gap_count)()
            gap_blocking = M.false_value
            if M.IsPair(goal)() is M.truth_value:
                if TermContains(goal, gap_target)() is M.truth_value:
                    gap_blocking = M.truth_value
            entry = M.Pair(
                Lmod.RankedGapsLabel,
                M.Pair(
                    gap,
                    M.Pair(gap_count, M.Pair(gap_blocking, M.EmptyList)),
                ),
            )
            gap_priority_text = GapRankPriority(gap)()()
            prefix_reversed = M.EmptyList
            cursor = ranked
            rest = M.EmptyList
            placed = M.false_value
            while M.IdentityCompare(
                cursor, M.EmptyList,
            )() is M.false_value:
                if M.IdentityCompare(placed, M.truth_value)() is M.truth_value:
                    cursor = M.EmptyList
                else:
                    existing = M.Head(cursor)()
                    existing_gap = M.Head(M.Tail(existing)())()
                    existing_count_text = M.GMPRepText(
                        M.Head(M.Tail(M.Tail(existing)())())(),
                    )()
                    existing_blocking = M.Head(
                        M.Tail(M.Tail(M.Tail(existing)())())(),
                    )()
                    existing_priority_text = GapRankPriority(existing_gap)()()
                    entry_first = M.false_value
                    if GMPLessText(
                        existing_count_text, gap_count_text,
                    )() is M.truth_value:
                        entry_first = M.truth_value
                    elif GMPEqualText(
                        existing_count_text, gap_count_text,
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            gap_blocking, M.truth_value,
                        )() is M.truth_value:
                            if M.IdentityCompare(
                                existing_blocking, M.truth_value,
                            )() is M.false_value:
                                entry_first = M.truth_value
                        if M.IdentityCompare(
                            entry_first, M.false_value,
                        )() is M.truth_value:
                            if M.IdentityCompare(
                                gap_blocking, existing_blocking,
                            )() is M.truth_value:
                                if GMPLessText(
                                    gap_priority_text,
                                    existing_priority_text,
                                )() is M.truth_value:
                                    entry_first = M.truth_value
                    if M.IdentityCompare(
                        entry_first, M.truth_value,
                    )() is M.truth_value:
                        placed = M.truth_value
                        rest = cursor
                        cursor = M.EmptyList
                    else:
                        prefix_reversed = M.Pair(
                            existing, prefix_reversed,
                        )
                        cursor = M.Tail(cursor)()
            chain = M.Pair(entry, rest)
            while M.IdentityCompare(
                prefix_reversed, M.EmptyList,
            )() is M.false_value:
                chain = M.Pair(M.Head(prefix_reversed)(), chain)
                prefix_reversed = M.Tail(prefix_reversed)()
            ranked = chain
            scan = M.Tail(scan)()
        self.result = ranked
        super().__init__(
            inputs=M.Pair(
                gaps, M.Pair(goal, M.Pair(graph_version, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MissingRenderLawKnown(M.Edge):
    """Whether a MissingRenderLaw record already covers a gap type."""

    def __init__(self, graph_version, gap_head):
        self.result = M.false_value
        agenda = GraphNodes(graph_version)()
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            node = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.IsPair(node)() is M.truth_value:
                node_head = M.Head(node)()
                if M.Compare(
                    node_head, Lmod.MissingRenderLawLabel,
                )() is M.truth_value:
                    recorded_head = M.Head(M.Tail(node)())()
                    if M.Compare(recorded_head, gap_head)() is M.truth_value:
                        self.result = M.truth_value
                        agenda = M.EmptyList
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(gap_head, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallMissingRenderLaw(M.Edge):
    """Record MissingRenderLaw(gap_type) for a gap with no render law."""

    def __init__(self, graph_version, gap_head):
        self.result = GraphVersion(
            M.Pair(
                M.Pair(
                    Lmod.MissingRenderLawLabel,
                    M.Pair(gap_head, M.EmptyList),
                ),
                GraphNodes(graph_version)(),
            ),
            GraphEdges(graph_version)(),
            GraphVersionInvariants(graph_version)(),
        )()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(gap_head, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallRankGaps(M.Edge):
    """Store one ranked-gap chain in the learned graph for inspection."""

    def __init__(self, graph_version, ranked):
        self.result = GraphVersion(
            M.Pair(
                M.Pair(Lmod.RankedGapsLabel, M.Pair(ranked, M.EmptyList)),
                GraphNodes(graph_version)(),
            ),
            GraphEdges(graph_version)(),
            GraphVersionInvariants(graph_version)(),
        )()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(ranked, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class AskedQuestion(M.Edge):
    """A gap question the machine asked, with its render law name."""

    def __init__(self, gap, surface, law_name):
        self.result = M.Pair(
            Lmod.AskedQuestionLabel,
            M.Pair(gap, M.Pair(surface, M.Pair(law_name, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(
                gap, M.Pair(surface, M.Pair(law_name, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallAskedQuestion(M.Edge):
    """Persist one asked-question record in the learned graph."""

    def __init__(self, graph_version, record):
        self.result = GraphVersion(
            M.Pair(record, GraphNodes(graph_version)()),
            GraphEdges(graph_version)(),
            GraphVersionInvariants(graph_version)(),
        )()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(record, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstalledAskedQuestions(M.Edge):
    """Recover every asked-question record from the learned graph."""

    def __init__(self, graph_version):
        reversed_records = M.EmptyList
        agenda = GraphNodes(graph_version)()
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            node = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.IsPair(node)() is M.truth_value:
                node_head = M.Head(node)()
                if M.IsPair(node_head)() is M.truth_value:
                    nested = node
                    while M.IdentityCompare(
                        nested, M.EmptyList,
                    )() is M.false_value:
                        agenda = M.Pair(M.Head(nested)(), agenda)
                        nested = M.Tail(nested)()
                elif M.Compare(
                    node_head, Lmod.AskedQuestionLabel,
                )() is M.truth_value:
                    reversed_records = M.Pair(node, reversed_records)
        self.result = M.Reverse(reversed_records)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RenderAcknowledgement(M.Edge):
    """Render an acknowledgement through the acknowledgement render law.

    The utterance is produced by a correspondence law from an
    Acknowledged meaning term -- no host string is the machine's voice.
    """

    def __init__(self, term):
        var_t = M.Pair(M.VarTag, M.Pair(M.Char("?t"), M.EmptyList))
        pattern = M.Pair(
            Lmod.AcknowledgedLabel,
            M.Pair(var_t, M.EmptyList),
        )
        template = M.Pair(
            Lmod.SurfaceLabel,
            M.Pair(
                M.Pair(M.Char("noted"), M.Pair(M.Char("."), M.EmptyList)),
                M.EmptyList,
            ),
        )
        law = CompileRuleToLaw(P.Rule(pattern, template))()
        meaning = M.Pair(
            Lmod.AcknowledgedLabel,
            M.Pair(term, M.EmptyList),
        )
        self.result = CorrespondenceApply(law, meaning)()
        super().__init__(
            inputs=M.Pair(term, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class GapLawName(M.Edge):
    """The inspectable name of the render law that rendered a question."""

    def __init__(self, law):
        self.result = M.Char("unknown")
        law_scan = GapRenderLaws()()
        position_text = "0"
        while M.IdentityCompare(law_scan, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(
                M.Head(law_scan)(), law,
            )() is M.truth_value:
                if GMPEqualText(position_text, "0")() is M.truth_value:
                    self.result = M.Char("what-is")
                elif GMPEqualText(position_text, "1")() is M.truth_value:
                    self.result = M.Char("define")
                elif GMPEqualText(position_text, "2")() is M.truth_value:
                    self.result = M.Char("usage-example")
                law_scan = M.EmptyList
            else:
                position_text = GMPSuccText(position_text)()
                law_scan = M.Tail(law_scan)()
        super().__init__(inputs=M.Pair(law, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class InspectGaps(M.Edge):
    """One full gap inspection turn over the learned graph.

    Refreshes pending gaps: an open gap with no render law is recorded
    as MissingRenderLaw and stays silent -- it does not block the
    queue; an answerable gap stays pending. When nothing renderable
    remains pending, the vocabulary is re-inspected and only gaps in
    the neighborhood of the just-taught term -- the gap target occurs
    inside it -- enter the queue. The refreshed gaps are ranked by
    blast radius into an inspectable ranked chain stored in the graph,
    and the first renderable ranked gap becomes the question to ask.
    """

    def __init__(self, pending_gaps, goal, graph_version, taught_term):
        version = graph_version
        kept_reversed = M.EmptyList
        pending_scan = pending_gaps
        while M.IdentityCompare(
            pending_scan, M.EmptyList,
        )() is M.false_value:
            gap = M.Head(pending_scan)()
            if M.IdentityCompare(
                GapOpen(gap, version)(), M.truth_value,
            )() is M.truth_value:
                rendered_gap = RenderGapQuestion(gap)()
                if M.IdentityCompare(
                    rendered_gap, M.EmptyList,
                )() is M.false_value:
                    kept_reversed = M.Pair(gap, kept_reversed)
                else:
                    gap_head = M.EmptyList
                    if M.IsPair(gap)() is M.truth_value:
                        gap_head = M.Head(gap)()
                    if M.IdentityCompare(
                        MissingRenderLawKnown(version, gap_head)(),
                        M.truth_value,
                    )() is M.false_value:
                        version = InstallMissingRenderLaw(
                            version, gap_head,
                        )()
            pending_scan = M.Tail(pending_scan)()
        open_gaps = M.Reverse(kept_reversed)()
        if M.IdentityCompare(open_gaps, M.EmptyList)() is M.truth_value:
            detected_gaps = DetectVocabularyGaps(version)()
            detect_scan = detected_gaps
            detected_reversed = M.EmptyList
            while M.IdentityCompare(
                detect_scan, M.EmptyList,
            )() is M.false_value:
                gap = M.Head(detect_scan)()
                version = InstallGap(version, gap)()
                if TermContains(
                    taught_term, GapTarget(gap)(),
                )() is M.truth_value:
                    rendered_gap = RenderGapQuestion(gap)()
                    if M.IdentityCompare(
                        rendered_gap, M.EmptyList,
                    )() is M.false_value:
                        detected_reversed = M.Pair(gap, detected_reversed)
                    else:
                        gap_head = M.EmptyList
                        if M.IsPair(gap)() is M.truth_value:
                            gap_head = M.Head(gap)()
                        if M.IdentityCompare(
                            MissingRenderLawKnown(version, gap_head)(),
                            M.truth_value,
                        )() is M.false_value:
                            version = InstallMissingRenderLaw(
                                version, gap_head,
                            )()
                detect_scan = M.Tail(detect_scan)()
            open_gaps = M.Reverse(detected_reversed)()
        ranked = RankGaps(open_gaps, goal, version)()
        version = InstallRankGaps(version, ranked)()
        ask = M.EmptyList
        ranked_scan = ranked
        while M.IdentityCompare(
            ranked_scan, M.EmptyList,
        )() is M.false_value:
            if M.IdentityCompare(ask, M.EmptyList)() is M.false_value:
                ranked_scan = M.EmptyList
            else:
                ranked_record = M.Head(ranked_scan)()
                gap = M.Head(M.Tail(ranked_record)())()
                rendered_gap = RenderGapQuestion(gap)()
                if M.IdentityCompare(
                    rendered_gap, M.EmptyList,
                )() is M.false_value:
                    ask = M.Pair(
                        M.Head(rendered_gap)(),
                        M.Pair(
                            gap,
                            M.Pair(
                                GapLawName(
                                    M.Head(M.Tail(rendered_gap)())(),
                                )(),
                                M.EmptyList,
                            ),
                        ),
                    )
                ranked_scan = M.Tail(ranked_scan)()
        self.result = M.Pair(
            version,
            M.Pair(
                open_gaps,
                M.Pair(ranked, M.Pair(ask, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                pending_gaps,
                M.Pair(
                    goal,
                    M.Pair(
                        graph_version,
                        M.Pair(taught_term, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DerivationTree(M.Edge):
    """Expand one rule firing into a premise derivation tree.

    Each premise that was itself derived by a taught rule gets its own
    subtree; taught facts stay leaves. Depth is bounded by a machine
    counter, though firing provenance is acyclic by construction.
    """

    def __init__(self, derivation, graph_version, depth_text):
        children_reversed = M.EmptyList
        if GMPEqualText(depth_text, "50")() is M.false_value:
            all_derivations = InstalledTaughtDerivations(graph_version)()
            premise_scan = DerivationPremises(derivation)()
            while M.IdentityCompare(
                premise_scan, M.EmptyList,
            )() is M.false_value:
                premise = M.Head(premise_scan)()
                derivation_scan = all_derivations
                premise_derivation = M.EmptyList
                while M.IdentityCompare(
                    derivation_scan, M.EmptyList,
                )() is M.false_value:
                    candidate = M.Head(derivation_scan)()
                    if M.Compare(
                        DerivationDerived(candidate)(), premise,
                    )() is M.truth_value:
                        premise_derivation = candidate
                        derivation_scan = M.EmptyList
                    else:
                        derivation_scan = M.Tail(derivation_scan)()
                if M.IdentityCompare(
                    premise_derivation, M.EmptyList,
                )() is M.false_value:
                    children_reversed = M.Pair(
                        DerivationTree(
                            premise_derivation,
                            graph_version,
                            GMPSuccText(depth_text)(),
                        )(),
                        children_reversed,
                    )
                premise_scan = M.Tail(premise_scan)()
        self.result = M.Pair(
            M.Char("derivation-tree"),
            M.Pair(
                derivation,
                M.Pair(M.Reverse(children_reversed)(), M.EmptyList),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                derivation,
                M.Pair(
                    graph_version,
                    M.Pair(depth_text, M.EmptyList),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InductiveLaw(M.Edge):
    """The certificate that a claim predicate is proven by induction.

    Pair(Char("inductive-law"), Pair(claim, Pair(bases, Pair(steps,
    EmptyList)))) -- bases are rules concluding the claim at a numeral
    constant, steps are rules concluding the claim at a constructor
    application of a variable that also appears as a claim premise.

    The certificate rides the checkpoint wire, and rule objects do not
    survive it: they intern as opaque atoms and their premises and
    replacements are lost. Each base and step is therefore stored as
    its raw premises/replacement pair -- the same wire-safe shape the
    lemma and process records use -- and readers reconstruct the rule
    from the pair when they need one.
    """

    def __init__(self, claim, bases, steps):
        stored_bases = M.EmptyList
        base_scan = bases
        while M.IdentityCompare(
            base_scan, M.EmptyList,
        )() is M.false_value:
            base_rule = M.Head(base_scan)()
            stored_bases = M.Pair(
                M.Pair(
                    P.RulePremises(base_rule)(),
                    M.Pair(
                        P.RuleReplacement(base_rule)(), M.EmptyList,
                    ),
                ),
                stored_bases,
            )
            base_scan = M.Tail(base_scan)()
        stored_steps = M.EmptyList
        step_scan = steps
        while M.IdentityCompare(
            step_scan, M.EmptyList,
        )() is M.false_value:
            step_rule = M.Head(step_scan)()
            stored_steps = M.Pair(
                M.Pair(
                    P.RulePremises(step_rule)(),
                    M.Pair(
                        P.RuleReplacement(step_rule)(), M.EmptyList,
                    ),
                ),
                stored_steps,
            )
            step_scan = M.Tail(step_scan)()
        self.result = M.Pair(
            M.Char("inductive-law"),
            M.Pair(
                claim,
                M.Pair(
                    M.Reverse(stored_bases)(),
                    M.Pair(M.Reverse(stored_steps)(), M.EmptyList),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                claim, M.Pair(bases, M.Pair(steps, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InductiveLawKnown(M.Edge):
    """Whether an inductive law is already certified for a claim."""

    def __init__(self, graph_version, claim):
        self.result = M.false_value
        agenda = GraphNodes(graph_version)()
        while M.IdentityCompare(agenda, M.EmptyList)() is M.false_value:
            node = M.Head(agenda)()
            agenda = M.Tail(agenda)()
            if M.IsPair(node)() is M.truth_value:
                node_head = M.Head(node)()
                if M.Compare(
                    node_head, M.Char("inductive-law"),
                )() is M.truth_value:
                    if M.Compare(
                        M.Head(M.Tail(node)())(), claim,
                    )() is M.truth_value:
                        self.result = M.truth_value
                        agenda = M.EmptyList
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(claim, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CertifyInduction(M.Edge):
    """Certify a claim predicate as proven by induction over its first term.

    Scans installed taught rules for the claim's base and step shapes,
    and, when both exist, derives the universal rule the induction
    licenses: the step's side premises conclude the claim at its
    induction variable. Result:
    Pair(version, Pair(bases, Pair(steps, Pair(universal, Pair(reason,
    EmptyList))))) -- reason is EmptyList on certification and a Char
    text key otherwise.
    """

    def __init__(self, claim, graph_version):
        version = graph_version
        bases_reversed = M.EmptyList
        steps_reversed = M.EmptyList
        rule_scan = InstalledTaughtRules(graph_version)()
        while M.IdentityCompare(
            rule_scan, M.EmptyList,
        )() is M.false_value:
            taught_rule = M.Head(rule_scan)()
            replacement = P.RuleReplacement(taught_rule)()
            if M.IsPair(replacement)() is M.truth_value:
                if M.Compare(M.Head(replacement)(), claim)() is M.truth_value:
                    first_arg = M.Head(M.Tail(replacement)())()
                    if M.IsPair(first_arg)() is M.truth_value:
                        premise_scan = P.RulePremises(taught_rule)()
                        claim_premise = M.EmptyList
                        while M.IdentityCompare(
                            premise_scan, M.EmptyList,
                        )() is M.false_value:
                            premise = M.Head(premise_scan)()
                            if M.IsPair(premise)() is M.truth_value:
                                if M.Compare(
                                    M.Head(premise)(), claim,
                                )() is M.truth_value:
                                    claim_premise = premise
                                    premise_scan = M.EmptyList
                                else:
                                    premise_scan = M.Tail(premise_scan)()
                            else:
                                premise_scan = M.Tail(premise_scan)()
                        if M.IdentityCompare(
                            claim_premise, M.EmptyList,
                        )() is M.false_value:
                            steps_reversed = M.Pair(
                                taught_rule, steps_reversed,
                            )
                    else:
                        bases_reversed = M.Pair(
                            taught_rule, bases_reversed,
                        )
            rule_scan = M.Tail(rule_scan)()
        bases = M.Reverse(bases_reversed)()
        steps = M.Reverse(steps_reversed)()
        reason = M.EmptyList
        universal = M.EmptyList
        if M.IdentityCompare(bases, M.EmptyList)() is M.truth_value:
            reason = M.Char("no-base")
        elif M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            reason = M.Char("no-step")
        else:
            step_rule = M.Head(steps)()
            step_premises = P.RulePremises(step_rule)()
            claim_premise = M.EmptyList
            premise_scan = step_premises
            while M.IdentityCompare(
                premise_scan, M.EmptyList,
            )() is M.false_value:
                premise = M.Head(premise_scan)()
                if M.IsPair(premise)() is M.truth_value:
                    if M.Compare(
                        M.Head(premise)(), claim,
                    )() is M.truth_value:
                        claim_premise = premise
                        premise_scan = M.EmptyList
                    else:
                        premise_scan = M.Tail(premise_scan)()
                else:
                    premise_scan = M.Tail(premise_scan)()
            induction_variable = M.Head(M.Tail(claim_premise)())()
            side_premises_reversed = M.EmptyList
            premise_scan = step_premises
            while M.IdentityCompare(
                premise_scan, M.EmptyList,
            )() is M.false_value:
                premise = M.Head(premise_scan)()
                if M.Compare(premise, claim_premise)() is M.false_value:
                    side_premises_reversed = M.Pair(
                        premise, side_premises_reversed,
                    )
                premise_scan = M.Tail(premise_scan)()
            universal = P.MultiRule(
                M.Reverse(side_premises_reversed)(),
                M.Pair(
                    claim,
                    M.Pair(
                        induction_variable,
                        M.Tail(M.Tail(P.RuleReplacement(step_rule)())())(),
                    ),
                ),
            )()
            if M.IdentityCompare(
                InductiveLawKnown(version, claim)(),
                M.truth_value,
            )() is M.false_value:
                version = GraphVersion(
                    M.Pair(
                        InductiveLaw(
                            claim, bases, steps,
                        )(),
                        GraphNodes(version)(),
                    ),
                    GraphEdges(version)(),
                    GraphVersionInvariants(version)(),
                )()
        self.result = M.Pair(
            version,
            M.Pair(
                bases,
                M.Pair(
                    steps,
                    M.Pair(universal, M.Pair(reason, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(claim, M.Pair(graph_version, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DerivationTreeText(M.Edge):
    """Display text for one derivation tree, expanded recursively."""

    def __init__(self, tree):
        derivation = M.Head(M.Tail(tree)())()
        children = M.Head(M.Tail(M.Tail(tree)())())()
        text = (
            M.PrettyTerm(DerivationDerived(derivation)(), M.AllConstructors)()
            + " was derived by "
            + P.PrettyRule(
                DerivationRule(derivation)(), M.AllConstructors,
            )()
            + " from "
            + M.PrettyTerm(
                DerivationPremises(derivation)(), M.AllConstructors,
            )()
        )
        child_scan = children
        while M.IdentityCompare(child_scan, M.EmptyList)() is M.false_value:
            text = text + "; " + DerivationTreeText(M.Head(child_scan)())()
            child_scan = M.Tail(child_scan)()
        self.result = text
        super().__init__(inputs=M.Pair(tree, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


__all__ = [name for name in globals() if not name.startswith("_")]
