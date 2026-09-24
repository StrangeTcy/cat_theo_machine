from __future__ import annotations

import io
import multiprocessing

from . import context as Ctx
from . import machine as M
from . import proof as P
from . import schemata as S
from . import labels as Lmod
from . import trees as Tmod
from .gmprep import GMPAddText, GMPEqualText, GMPLessText, GMPMulText, GMPRepDigitList, GMPSubText, GMPSuccText
from .search.patricia import SearchPatriciaIsTree, SearchPatriciaEntries
from .search.model import (
    SearchMatchCursor,
    SearchMatchCursorComplete,
    SearchMatchCursorPending,
    SearchMatchCursorRoot,
    SearchState,
    SearchStateCursor,
)
from . import graph
from . import firing
from . import ledger

class ObservedSymbolStep(M.Edge):
    """One symbol observed between two cursors.

    Pair(ObservedSymbolStepLabel, Pair(utterance, Pair(before,
    Pair(symbol, Pair(after, EmptyList))))). The client emits one of
    these per symbol as it arrives. It establishes no words, guesses no
    boundaries, normalises nothing and discards nothing -- it records
    what was observed, in order.
    """

    def __init__(self, utterance, before, symbol, after):
        self.result = M.Pair(
            Lmod.ObservedSymbolStepLabel,
            M.Pair(
                utterance,
                M.Pair(before, M.Pair(symbol, M.Pair(after, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                utterance,
                M.Pair(before, M.Pair(symbol, M.Pair(after, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ObservedStepBefore(M.Edge):
    def __init__(self, step):
        self.result = M.Head(M.Tail(M.Tail(step)())())()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObservedStepSymbol(M.Edge):
    def __init__(self, step):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(step)())())())()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObservedStepAfter(M.Edge):
    def __init__(self, step):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(step)())())())(),
        )()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FormArc(M.Edge):
    """One step of a shared form trie: state, symbol, next state."""

    def __init__(self, state, symbol, next_state):
        self.result = M.Pair(
            Lmod.FormArcLabel,
            M.Pair(state, M.Pair(symbol, M.Pair(next_state, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(
                state, M.Pair(symbol, M.Pair(next_state, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormSense(M.Edge):
    """A form state that spells something: its category and its meaning."""

    def __init__(self, state, category, meaning):
        self.result = M.Pair(
            Lmod.FormSenseLabel,
            M.Pair(state, M.Pair(category, M.Pair(meaning, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(
                state, M.Pair(category, M.Pair(meaning, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormScan(M.Edge):
    """A recognition in progress: trie state, where it began, where it is."""

    def __init__(self, state, start, cursor):
        self.result = M.Pair(
            Lmod.FormScanLabel,
            M.Pair(state, M.Pair(start, M.Pair(cursor, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(state, M.Pair(start, M.Pair(cursor, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Reading(M.Edge):
    """A meaning found over an interval of the observed input."""

    def __init__(self, category, start, end, meaning):
        self.result = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                category, M.Pair(start, M.Pair(end, M.Pair(meaning, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                category, M.Pair(start, M.Pair(end, M.Pair(meaning, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ObservedStepUtterance(M.Edge):
    def __init__(self, step):
        self.result = M.Head(M.Tail(step)())()
        super().__init__(inputs=M.Pair(step, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ObservedBy(M.Edge):
    """Provenance: which event stream the observations came from.

    Pair(ObservedByLabel, Pair(utterance, Pair(stream, EmptyList))). The
    client states where its ObservedSymbolStep facts came from; the
    machine stores the claim and derives nothing from it.
    """

    def __init__(self, utterance, stream):
        self.result = M.Pair(
            Lmod.ObservedByLabel,
            M.Pair(utterance, M.Pair(stream, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(utterance, M.Pair(stream, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class LexiconRoot(M.Edge):
    """The one shared trie root a language's forms hang from."""

    def __init__(self, language, root):
        self.result = M.Pair(
            Lmod.LexiconRootLabel,
            M.Pair(language, M.Pair(root, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(language, M.Pair(root, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class IndexSpec(M.Edge):
    """A declared index: a relation and the argument chain keying it.

    Pair(IndexSpecLabel, Pair(relation, Pair(keys, EmptyList))). The
    engine builds exactly the indexes it declares here and answers every
    premise from one; a spec without a root behind it would be a claim,
    so none is recorded that is not kept.
    """

    def __init__(self, relation, keys):
        self.result = M.Pair(
            Lmod.IndexSpecLabel,
            M.Pair(relation, M.Pair(keys, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(relation, M.Pair(keys, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DeductionPlan(M.Edge):
    """The execution certificate for one trigger position of a law.

    Pair(DeductionPlanLabel, Pair(law, Pair(trigger, Pair(lookups,
    Pair(conclusion, EmptyList))))). The law stays the authoritative
    statement; the plan says which premise the delta arrives on, which
    declared indexes the other premises are answered from, and what
    relation the conclusion carries. One plan exists per premise
    position the engine executes; PlansByTriggerRelation holds them by
    trigger label.
    """

    def __init__(self, law, trigger, lookups, conclusion):
        self.result = M.Pair(
            Lmod.DeductionPlanLabel,
            M.Pair(
                law,
                M.Pair(trigger, M.Pair(lookups, M.Pair(conclusion, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                law,
                M.Pair(trigger, M.Pair(lookups, M.Pair(conclusion, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DeltaAgenda(M.Edge):
    """The pending delta facts. Empty is quiescence."""

    def __init__(self, facts):
        self.result = M.Pair(Lmod.DeltaAgendaLabel, M.Pair(facts, M.EmptyList))
        super().__init__(inputs=M.Pair(facts, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IndexedFiring(M.Edge):
    """One firing of a law by index: its premises and its conclusion.

    Pair(IndexedFiringLabel, Pair(law, Pair(premises, Pair(bindings,
    Pair(conclusion, EmptyList))))). The bindings slot stays empty until
    templates carry variables; every join here is by identity, so there
    is nothing else to record yet.
    """

    def __init__(self, law, premises, bindings, conclusion):
        self.result = M.Pair(
            Lmod.IndexedFiringLabel,
            M.Pair(
                law,
                M.Pair(
                    premises,
                    M.Pair(bindings, M.Pair(conclusion, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                law,
                M.Pair(
                    premises,
                    M.Pair(bindings, M.Pair(conclusion, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class BinaryProduction(M.Edge):
    """One binary grammar production: categories and a meaning template.

    Pair(BinaryProductionLabel, Pair(left, Pair(right, Pair(result,
    Pair(template, EmptyList))))). The template's variables bind the
    daughter meanings in order of first appearance: the first distinct
    variable takes the left daughter's meaning, the second the right
    daughter's, and one variable appearing twice shares one meaning in
    both places. A template that must keep the right daughter alone --
    a determiner or a command word dropped from the meaning -- cannot
    say so with a bare variable, since one variable binds to the left
    daughter; it says so with Pair(ProjectRightLabel,
    Pair(inner_template, EmptyList)), under which the first distinct
    variable of the inner template takes the right daughter's meaning.
    Every firing runs the template through FreshenTemplate before
    anything binds, so two applications of one production never share
    a variable.
    """

    def __init__(self, left, right, result, template):
        self.result = M.Pair(
            Lmod.BinaryProductionLabel,
            M.Pair(
                left,
                M.Pair(
                    right,
                    M.Pair(result, M.Pair(template, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                left,
                M.Pair(
                    right,
                    M.Pair(result, M.Pair(template, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Freshened(M.Edge):
    """The record of one freshening: template, scope, bindings, result."""

    def __init__(self, template, scope, bindings, instantiated):
        self.result = M.Pair(
            Lmod.FreshenedLabel,
            M.Pair(
                template,
                M.Pair(
                    scope,
                    M.Pair(
                        bindings, M.Pair(instantiated, M.EmptyList),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                template,
                M.Pair(
                    scope,
                    M.Pair(
                        bindings, M.Pair(instantiated, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FreshenTemplate(M.Edge):
    """Allocate fresh variables for one application of a template.

    The walk collects each distinct variable of the template by
    identity, in order of first appearance; allocates one new variable
    per distinct variable -- Pair(VarTag, Pair(scope, Pair(old,
    EmptyList))), so the recognised VarTag shape is kept and the scope
    tells applications apart -- builds the old-to-new binding chain,
    and rebuilds the template through it. Two occurrences of one old
    variable receive the same new variable; two applications receive
    different ones, whatever the scope atoms are.
    """

    def __init__(self, template, scope):
        empty = M.EmptyList

        distinct = empty
        stack = M.Pair(template, empty)
        while M.IdentityCompare(stack, empty)() is M.false_value:
            node = M.Head(stack)()
            stack = M.Tail(stack)()
            if M.IsPair(node)() is M.truth_value:
                if M.IdentityCompare(M.Head(node)(), M.VarTag)() is M.truth_value:
                    present = M.false_value
                    walker = distinct
                    while M.IdentityCompare(walker, empty)() is M.false_value:
                        if M.IdentityCompare(
                            M.Head(walker)(), node,
                        )() is M.truth_value:
                            present = M.truth_value
                            walker = empty
                        else:
                            walker = M.Tail(walker)()
                    if present is M.false_value:
                        distinct = M.Pair(node, distinct)
                else:
                    stack = M.Pair(M.Tail(node)(), stack)
                    stack = M.Pair(M.Head(node)(), stack)

        bindings = empty
        walker = distinct
        while M.IdentityCompare(walker, empty)() is M.false_value:
            old_variable = M.Head(walker)()
            fresh_variable = M.Pair(
                M.VarTag, M.Pair(scope, M.Pair(old_variable, empty)),
            )
            bindings = M.Pair(M.Pair(old_variable, fresh_variable), bindings)
            walker = M.Tail(walker)()

        self.bindings_chain = bindings
        self.instantiated = self._rebuild(template, bindings)
        self.result = Freshened(
            template, scope, bindings, self.instantiated,
        )()
        super().__init__(
            inputs=M.Pair(template, M.Pair(scope, empty)),
            results=self.result,
        )

    def _rebuild(self, node, bindings):
        if M.IsPair(node)() is M.truth_value:
            if M.IdentityCompare(M.Head(node)(), M.VarTag)() is M.truth_value:
                walker = bindings
                while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
                    entry = M.Head(walker)()
                    if M.IdentityCompare(
                        M.Head(entry)(), node,
                    )() is M.truth_value:
                        return M.Tail(entry)()
                    walker = M.Tail(walker)()
                return node
            return M.Pair(
                self._rebuild(M.Head(node)(), bindings),
                self._rebuild(M.Tail(node)(), bindings),
            )
        return node

    def __call__(self):
        return self.result


class ResolveReflexives(M.Edge):
    """Replace every reflexive marker in a term with one variable.

    Pair(ReflexiveLabel, ...) anywhere in the term becomes the given
    variable -- the same object at every site, which is the sharing a
    definition's self needs: "one and itself" must read as [one, self]
    with the self in the application and the self in the restriction
    being one variable. Every other structure is preserved and leaves
    are untouched.
    """

    def __init__(self, term, variable):
        self.result = self._resolve(term, variable)
        super().__init__(
            inputs=M.Pair(term, M.Pair(variable, M.EmptyList)),
            results=self.result,
        )

    def _resolve(self, node, variable):
        if M.IsPair(node)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(node)(), Lmod.ReflexiveLabel,
            )() is M.truth_value:
                return variable
            return M.Pair(
                self._resolve(M.Head(node)(), variable),
                self._resolve(M.Tail(node)(), variable),
            )
        return node

    def __call__(self):
        return self.result


class PredicateHoles(M.Edge):
    """Keep undefined predicates as holes inside a formed chain.

    Pair(conditions, defined_labels) -> Pair(conditions_with_holes,
    Pair(hole_predicates, EmptyList)). A condition is holed when its
    label is installed nowhere and it is not the structural
    ExactFillers, which is scope rather than a predicate. The
    arguments move inside the hole unchanged and the reason is
    NoDefinitionInstalled; the predicate labels chain, in condition
    order with duplicates dropped, is the open-dependency report. A
    hole is the difference between lexical ignorance and a formed
    graph with a named gap: the graph exists, the gap is in it.
    """

    def __init__(self, conditions, defined_labels):
        empty = M.EmptyList
        reversed_conditions = empty
        reversed_holes = empty
        walker = conditions
        while M.IdentityCompare(walker, empty)() is M.false_value:
            condition = M.Head(walker)()
            label = M.Head(condition)()
            keep = M.false_value
            if M.IdentityCompare(
                label, Lmod.ExactFillersLabel,
            )() is M.truth_value:
                keep = M.truth_value
            else:
                defined_walker = defined_labels
                while M.IdentityCompare(
                    defined_walker, empty,
                )() is M.false_value:
                    if M.IdentityCompare(
                        label, M.Head(defined_walker)(),
                    )() is M.truth_value:
                        keep = M.truth_value
                        defined_walker = empty
                    else:
                        defined_walker = M.Tail(defined_walker)()
            if keep is M.truth_value:
                reversed_conditions = M.Pair(condition, reversed_conditions)
            else:
                holed = M.Pair(
                    Lmod.HoleLabel,
                    M.Pair(
                        label,
                        M.Pair(
                            M.Tail(condition)(),
                            M.Pair(
                                Lmod.NoDefinitionInstalledLabel, empty,
                            ),
                        ),
                    ),
                )
                reversed_conditions = M.Pair(holed, reversed_conditions)
                present = M.false_value
                hole_walker = reversed_holes
                while M.IdentityCompare(
                    hole_walker, empty,
                )() is M.false_value:
                    if M.IdentityCompare(
                        label, M.Head(hole_walker)(),
                    )() is M.truth_value:
                        present = M.truth_value
                        hole_walker = empty
                    else:
                        hole_walker = M.Tail(hole_walker)()
                if present is M.false_value:
                    reversed_holes = M.Pair(label, reversed_holes)
            walker = M.Tail(walker)()
        self.result = M.Pair(
            M.Reverse(reversed_conditions)(),
            M.Pair(M.Reverse(reversed_holes)(), empty),
        )
        super().__init__(
            inputs=M.Pair(conditions, M.Pair(defined_labels, empty)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionNodeOpenDependencies(M.Edge):
    """The open dependencies of a formed definition graph, read off it.

    Walks the conditions; a Hole's predicate is an open dependency.
    Order follows the conditions; duplicates drop. This is the report
    that replaces asking about unknown words: the graph was formed, and
    these are the predicates it still needs definitions for.
    """

    def __init__(self, node):
        empty = M.EmptyList
        reversed_dependencies = empty
        walker = DefinitionNodeConditions(node)()
        while M.IdentityCompare(walker, empty)() is M.false_value:
            condition = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(condition)(), Lmod.HoleLabel,
            )() is M.truth_value:
                predicate = M.Head(M.Tail(condition)())()
                present = M.false_value
                dependency_walker = reversed_dependencies
                while M.IdentityCompare(
                    dependency_walker, empty,
                )() is M.false_value:
                    if M.IdentityCompare(
                        predicate, M.Head(dependency_walker)(),
                    )() is M.truth_value:
                        present = M.truth_value
                        dependency_walker = empty
                    else:
                        dependency_walker = M.Tail(dependency_walker)()
                if present is M.false_value:
                    reversed_dependencies = M.Pair(
                        predicate, reversed_dependencies,
                    )
            walker = M.Tail(walker)()
        self.result = M.Reverse(reversed_dependencies)()
        super().__init__(
            inputs=M.Pair(node, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class SpanningDefinitionReading(M.Edge):
    """The definition reading that spans exactly the given cursors."""

    def __init__(self, readings, category, start, end):
        empty = M.EmptyList
        self.result = empty
        walker = readings
        while M.IdentityCompare(walker, empty)() is M.false_value:
            reading = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(M.Tail(reading)())(), category,
            )() is M.truth_value:
                if M.IdentityCompare(
                    M.Head(M.Tail(M.Tail(reading)())())(), start,
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Head(M.Tail(M.Tail(M.Tail(reading)())())())(), end,
                    )() is M.truth_value:
                        self.result = M.Head(
                            M.Tail(M.Tail(M.Tail(M.Tail(reading)())())())(),
                        )()
                        walker = empty
                    else:
                        walker = M.Tail(walker)()
                else:
                    walker = M.Tail(walker)()
            else:
                walker = M.Tail(walker)()
        super().__init__(
            inputs=M.Pair(
                readings,
                M.Pair(category, M.Pair(start, M.Pair(end, empty))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionFragment(M.Edge):
    """The definition fragment's lexicon and grammar, as facts.

    Thirteen forms: the command word, the colon, the space, the
    article, the adjective, the category noun carrying its category
    and its NonNegative presupposition, the copula, the relation
    adjective naming Divides, the restriction, the role preposition
    naming the divisor, the numeral, the conjunction, the reflexive.
    Thirty-seven binary productions compose them -- glue that eats the
    spaces and the colon, the adjective over the noun into a lexical
    noun phrase, coordination in either order, the restriction, and
    two definition shapes -- the head-noun order ("a prime number is
    divisible...") and the predicate-nominal order ("a prime is a
    number divisible..."), where the category rides after the copula.
    The fragment carries no entry for either shape's definiendum: a
    word that is not a form is a gap, and the gap is filled by the
    loop, not by hand. The trie states
    are found through nested red-black trees, the same shape the
    engine indexes arcs by.

    Returns Pair(arcs, Pair(senses, Pair(productions, Pair(root,
    Pair(def_category, Pair(one, Pair(prime, Pair(nat,
    Pair(divisor, Pair(alphabet, EmptyList))))))))) -- the atoms
    callers assert against ride after the facts, and the alphabet is
    the fragment's canonical symbols: an observed step only matches
    the trie if the client emits these atoms, because index keys are
    identities, not texts.
    """

    def __init__(self):
        empty = M.EmptyList

        sym_a = M.Char("a")
        sym_b = M.Char("b")
        sym_d = M.Char("d")
        sym_e = M.Char("e")
        sym_f = M.Char("f")
        sym_i = M.Char("i")
        sym_l = M.Char("l")
        sym_m = M.Char("m")
        sym_n = M.Char("n")
        sym_o = M.Char("o")
        sym_p = M.Char("p")
        sym_r = M.Char("r")
        sym_s = M.Char("s")
        sym_t = M.Char("t")
        sym_u = M.Char("u")
        sym_v = M.Char("v")
        sym_y = M.Char("y")
        # Letters no fragment word uses, carried so the gap loop can
        # OBSERVE unknown words that contain them ("six", "eight",
        # "twenty"): a word the lexicon lacks is a gap to learn, but a
        # letter the alphabet lacks kills the whole line unread.
        sym_c = M.Char("c")
        sym_g = M.Char("g")
        sym_h = M.Char("h")
        sym_j = M.Char("j")
        sym_k = M.Char("k")
        sym_q = M.Char("q")
        sym_w = M.Char("w")
        sym_x = M.Char("x")
        sym_z = M.Char("z")
        sym_colon = M.Char(":")
        sym_space = M.Char(" ")
        sym_open = M.Char("(")
        sym_close = M.Char(")")

        word_definition = M.Pair(sym_d, M.Pair(sym_e, M.Pair(sym_f, M.Pair(sym_i, M.Pair(sym_n, M.Pair(sym_i, M.Pair(sym_t, M.Pair(sym_i, M.Pair(sym_o, M.Pair(sym_n, empty))))))))))

        word_colon = M.Pair(sym_colon, empty)

        word_space = M.Pair(sym_space, empty)

        word_a = M.Pair(sym_a, empty)


        word_number = M.Pair(sym_n, M.Pair(sym_u, M.Pair(sym_m, M.Pair(sym_b, M.Pair(sym_e, M.Pair(sym_r, empty))))))

        word_is = M.Pair(sym_i, M.Pair(sym_s, empty))

        word_divisible = M.Pair(sym_d, M.Pair(sym_i, M.Pair(sym_v, M.Pair(sym_i, M.Pair(sym_s, M.Pair(sym_i, M.Pair(sym_b, M.Pair(sym_l, M.Pair(sym_e, empty)))))))))

        word_only = M.Pair(sym_o, M.Pair(sym_n, M.Pair(sym_l, M.Pair(sym_y, empty))))

        word_by = M.Pair(sym_b, M.Pair(sym_y, empty))

        word_one = M.Pair(sym_o, M.Pair(sym_n, M.Pair(sym_e, empty)))

        word_and = M.Pair(sym_a, M.Pair(sym_n, M.Pair(sym_d, empty)))

        word_itself = M.Pair(sym_i, M.Pair(sym_t, M.Pair(sym_s, M.Pair(sym_e, M.Pair(sym_l, M.Pair(sym_f, empty))))))

        word_natural = M.Pair(sym_n, M.Pair(sym_a, M.Pair(sym_t, M.Pair(sym_u, M.Pair(sym_r, M.Pair(sym_a, M.Pair(sym_l, empty)))))))

        word_that = M.Pair(sym_t, M.Pair(sym_h, M.Pair(sym_a, M.Pair(sym_t, empty))))

        word_not = M.Pair(sym_n, M.Pair(sym_o, M.Pair(sym_t, empty)))

        one = M.Char("one")
        prime = M.Char("prime")
        nat = M.Char("nat")
        divisor = M.Char("divisor")
        number_chunk = M.Pair(
            CategoryTerm(nat)(),
            M.Pair(M.Pair(Lmod.NonNegativeLabel, empty), empty),
        )

        cat_cw = M.Char("CW")
        cat_col = M.Char("COL")
        cat_spc = M.Char("SPC")
        cat_det = M.Char("DET")
        cat_adj = M.Char("ADJ")
        cat_cn = M.Char("CN")
        cat_cop = M.Char("COP")
        cat_radj = M.Char("RADJ")
        cat_rop = M.Char("ROP")
        cat_p = M.Char("P")
        cat_num = M.Char("NUM")
        cat_conj = M.Char("CONJ")
        cat_rpron = M.Char("RPRON")
        cat_adjg = M.Char("ADJG")
        cat_detg = M.Char("DETG")
        cat_cwg = M.Char("CWG")
        cat_cwgg = M.Char("CWGG")
        cat_np = M.Char("NP")
        cat_npg = M.Char("NPG")
        cat_sbj = M.Char("SBJ")
        cat_copg = M.Char("COPG")
        cat_numg = M.Char("NUMG")
        cat_conjg = M.Char("CONJG")
        cat_cjpron = M.Char("CJPRON")
        cat_coord = M.Char("COORD")
        cat_pg = M.Char("PG")
        cat_pp = M.Char("PP")
        cat_ropg = M.Char("ROPG")
        cat_rpred = M.Char("RPRED")
        cat_radg = M.Char("RADJG")
        cat_pred = M.Char("PRED")
        cat_def = M.Char("DEF")
        cat_sbare = M.Char("SBARE")
        cat_sbareg = M.Char("SBAREG")
        cat_sbare2 = M.Char("SBARE2")
        cat_sbare2g = M.Char("SBARE2G")
        cat_rprong = M.Char("RPRONG")
        cat_cjnum = M.Char("CJNUM")
        cat_ncat = M.Char("NCAT")
        cat_ncatg = M.Char("NCATG")
        cat_prednom = M.Char("PREDNOM")
        cat_relpron = M.Char("RELPRON")
        cat_neg = M.Char("NEG")
        cat_relprong = M.Char("RELPRONG")
        cat_negg = M.Char("NEGG")
        cat_negpred = M.Char("NEGPRED")
        cat_negpredg = M.Char("NEGPREDG")
        cat_relpred = M.Char("RELPRED")
        cat_qsubj = M.Char("QSUBJ")
        cat_question = M.Char("QUESTION")


        entries = M.Pair(M.Pair(word_definition, M.Pair(cat_cw, M.Char("definition"))), M.Pair(M.Pair(word_colon, M.Pair(cat_col, M.Char(":"))), M.Pair(M.Pair(word_space, M.Pair(cat_spc, M.Char(" "))), M.Pair(M.Pair(word_a, M.Pair(cat_det, M.Char("a"))), M.Pair(M.Pair(word_number, M.Pair(cat_cn, number_chunk)), M.Pair(M.Pair(word_is, M.Pair(cat_cop, M.Char("is"))), M.Pair(M.Pair(word_divisible, M.Pair(cat_radj, Lmod.DividesLabel)), M.Pair(M.Pair(word_only, M.Pair(cat_rop, M.Char("only"))), M.Pair(M.Pair(word_by, M.Pair(cat_p, divisor)), M.Pair(M.Pair(word_one, M.Pair(cat_num, one)), M.Pair(M.Pair(word_and, M.Pair(cat_conj, M.Char("and"))), M.Pair(M.Pair(word_itself, M.Pair(cat_rpron, M.Pair(Lmod.ReflexiveLabel, empty))), M.Pair(M.Pair(word_natural, M.Pair(cat_adj, M.Char("natural"))), M.Pair(M.Pair(word_that, M.Pair(cat_relpron, M.Char("that"))), M.Pair(M.Pair(word_not, M.Pair(cat_neg, Lmod.NotLabel)), empty)))))))))))))))

        root = M.Char("frag-root")
        self._state_counter_text = "0"
        tree = empty
        arcs_reversed = empty
        senses_reversed = empty
        walker = entries
        while M.IdentityCompare(walker, empty)() is M.false_value:
            entry = M.Head(walker)()
            outcome = self._extend_trie(
                tree, arcs_reversed, root, M.Head(entry)(),
            )
            tree = M.Head(outcome)()
            arcs_reversed = M.Head(M.Tail(outcome)())()
            final_state = M.Head(M.Tail(M.Tail(outcome)())())()
            senses_reversed = M.Pair(
                FormSense(
                    final_state,
                    M.Head(M.Tail(entry)())(),
                    M.Tail(M.Tail(entry)())(),
                )(),
                senses_reversed,
            )
            walker = M.Tail(walker)()
        arcs = M.Reverse(arcs_reversed)()
        senses = M.Reverse(senses_reversed)()

        kind_left = M.Char("kind-left")
        kind_project = M.Char("kind-project")
        kind_pair = M.Char("kind-pair")
        kind_np = M.Char("kind-np")
        kind_restriction = M.Char("kind-restriction")
        kind_definition = M.Char("kind-definition")
        specs = M.Pair(M.Pair(cat_adj, M.Pair(cat_spc, M.Pair(cat_adjg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_adjg, M.Pair(cat_cn, M.Pair(cat_np, M.Pair(kind_np, empty)))), M.Pair(M.Pair(cat_det, M.Pair(cat_spc, M.Pair(cat_detg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_detg, M.Pair(cat_adj, M.Pair(cat_sbare, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_detg, M.Pair(cat_np, M.Pair(cat_np, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_cw, M.Pair(cat_col, M.Pair(cat_cwg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_cwg, M.Pair(cat_spc, M.Pair(cat_cwgg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_cwgg, M.Pair(cat_np, M.Pair(cat_np, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_cwgg, M.Pair(cat_sbare, M.Pair(cat_sbare, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_np, M.Pair(cat_spc, M.Pair(cat_npg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_cop, M.Pair(cat_spc, M.Pair(cat_copg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_copg, M.Pair(cat_numg, M.Pair(cat_qsubj, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_npg, M.Pair(cat_copg, M.Pair(cat_sbj, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_qsubj, M.Pair(cat_npg, M.Pair(cat_question, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_qsubj, M.Pair(cat_np, M.Pair(cat_question, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_num, M.Pair(cat_spc, M.Pair(cat_numg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_conj, M.Pair(cat_spc, M.Pair(cat_conjg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_conjg, M.Pair(cat_rpron, M.Pair(cat_cjpron, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_numg, M.Pair(cat_cjpron, M.Pair(cat_coord, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_p, M.Pair(cat_spc, M.Pair(cat_pg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_pg, M.Pair(cat_coord, M.Pair(cat_pp, M.Pair(kind_restriction, empty)))), M.Pair(M.Pair(cat_rop, M.Pair(cat_spc, M.Pair(cat_ropg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_ropg, M.Pair(cat_pp, M.Pair(cat_rpred, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_radj, M.Pair(cat_spc, M.Pair(cat_radg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_radg, M.Pair(cat_rpred, M.Pair(cat_pred, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_sbj, M.Pair(cat_pred, M.Pair(cat_def, M.Pair(kind_definition, empty)))), M.Pair(M.Pair(cat_sbare, M.Pair(cat_spc, M.Pair(cat_sbareg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_sbareg, M.Pair(cat_copg, M.Pair(cat_sbare2, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_sbare2, M.Pair(cat_spc, M.Pair(cat_sbare2g, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_sbare2, M.Pair(cat_prednom, M.Pair(cat_def, M.Pair(kind_definition, empty)))), M.Pair(M.Pair(cat_sbare2g, M.Pair(cat_prednom, M.Pair(cat_def, M.Pair(kind_definition, empty)))), M.Pair(M.Pair(cat_rpron, M.Pair(cat_spc, M.Pair(cat_rprong, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_conjg, M.Pair(cat_num, M.Pair(cat_cjnum, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_rprong, M.Pair(cat_cjnum, M.Pair(cat_coord, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_detg, M.Pair(cat_cn, M.Pair(cat_ncat, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_ncat, M.Pair(cat_spc, M.Pair(cat_ncatg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_ncatg, M.Pair(cat_pred, M.Pair(cat_prednom, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_qsubj, M.Pair(cat_adj, M.Pair(cat_question, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_qsubj, M.Pair(cat_sbare, M.Pair(cat_question, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_np, M.Pair(cat_spc, M.Pair(cat_npg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_relpron, M.Pair(cat_spc, M.Pair(cat_relprong, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_relprong, M.Pair(cat_copg, M.Pair(cat_negg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_negg, M.Pair(cat_neg, M.Pair(cat_negpred, M.Pair(kind_project, empty)))), M.Pair(M.Pair(cat_negpred, M.Pair(cat_spc, M.Pair(cat_negpredg, M.Pair(kind_left, empty)))), M.Pair(M.Pair(cat_negpredg, M.Pair(cat_adj, M.Pair(cat_relpred, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_npg, M.Pair(cat_relpred, M.Pair(cat_prednom, M.Pair(kind_pair, empty)))), M.Pair(M.Pair(cat_sbj, M.Pair(cat_prednom, M.Pair(cat_def, M.Pair(kind_definition, empty)))), empty)))))))))))))))))))))))))))))))))))))))))))))))

        self._production_counter_text = "0"
        productions_reversed = empty
        walker = specs
        while M.IdentityCompare(walker, empty)() is M.false_value:
            spec = M.Head(walker)()
            kind = M.Head(M.Tail(M.Tail(M.Tail(spec)())())())()
            first = M.Pair(
                M.VarTag,
                M.Pair(
                    M.Char("?frag" + self._production_counter_text + "a"), empty,
                ),
            )
            second = M.Pair(
                M.VarTag,
                M.Pair(
                    M.Char("?frag" + self._production_counter_text + "b"), empty,
                ),
            )
            if M.IdentityCompare(kind, kind_left)() is M.truth_value:
                built = first
            elif M.IdentityCompare(kind, kind_project)() is M.truth_value:
                built = M.Pair(Lmod.ProjectRightLabel, M.Pair(second, empty))
            elif M.IdentityCompare(kind, kind_pair)() is M.truth_value:
                built = M.Pair(first, M.Pair(second, empty))
            elif M.IdentityCompare(kind, kind_np)() is M.truth_value:
                built = M.Pair(
                    Lmod.LexicalNpLabel, M.Pair(first, M.Pair(second, empty)),
                )
            elif M.IdentityCompare(kind, kind_restriction)() is M.truth_value:
                built = M.Pair(
                    Lmod.RestrictionLabel,
                    M.Pair(first, M.Pair(second, empty)),
                )
            else:
                built = M.Pair(
                    Lmod.DefinitionMeaningLabel,
                    M.Pair(first, M.Pair(second, empty)),
                )
            productions_reversed = M.Pair(
                BinaryProduction(
                    M.Head(spec)(),
                    M.Head(M.Tail(spec)())(),
                    M.Head(M.Tail(M.Tail(spec)())())(),
                    built,
                )(),
                productions_reversed,
            )
            self._production_counter_text = GMPSuccText(
                self._production_counter_text,
            )()
            walker = M.Tail(walker)()
        productions = M.Reverse(productions_reversed)()

        alphabet = M.Pair(sym_a, M.Pair(sym_b, M.Pair(sym_c, M.Pair(sym_d, M.Pair(sym_e, M.Pair(sym_f, M.Pair(sym_g, M.Pair(sym_h, M.Pair(sym_i, M.Pair(sym_j, M.Pair(sym_k, M.Pair(sym_l, M.Pair(sym_m, M.Pair(sym_n, M.Pair(sym_o, M.Pair(sym_p, M.Pair(sym_q, M.Pair(sym_r, M.Pair(sym_s, M.Pair(sym_t, M.Pair(sym_u, M.Pair(sym_v, M.Pair(sym_w, M.Pair(sym_x, M.Pair(sym_y, M.Pair(sym_z, M.Pair(sym_colon, M.Pair(sym_space, M.Pair(sym_open, M.Pair(sym_close, empty))))))))))))))))))))))))))))))
        self.result = M.Pair(
            arcs,
            M.Pair(
                senses,
                M.Pair(
                    productions,
                    M.Pair(
                        root,
                        M.Pair(
                            cat_def,
                            M.Pair(
                                one,
                                M.Pair(
                                    prime,
                                    M.Pair(
                                        nat,
                                        M.Pair(
                                            divisor,
                                            M.Pair(
                                                alphabet,
                                                M.Pair(
                                                    cat_spc,
                                                    M.Pair(cat_adj, empty),
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
        super().__init__(inputs=empty, results=self.result)

    def _extend_trie(self, tree, arcs_reversed, state, word_chain):
        empty = M.EmptyList
        if M.IdentityCompare(word_chain, empty)() is M.truth_value:
            return M.Pair(
                tree, M.Pair(arcs_reversed, M.Pair(state, empty)),
            )
        symbol = M.Head(word_chain)()
        by_symbol = Tmod.IdentityRedBlackLookupValue(tree, state)()
        if M.IdentityCompare(by_symbol, empty)() is M.truth_value:
            by_symbol = M.EmptyList
        next_state = Tmod.IdentityRedBlackLookupValue(by_symbol, symbol)()
        if M.IdentityCompare(next_state, empty)() is M.truth_value:
            next_state = M.Char("frag-st-" + self._state_counter_text)
            self._state_counter_text = GMPSuccText(self._state_counter_text)()
            arcs_reversed = M.Pair(
                FormArc(state, symbol, next_state)(), arcs_reversed,
            )
            tree = Tmod.IdentityRedBlackInsert(
                tree,
                state,
                Tmod.IdentityRedBlackInsert(by_symbol, symbol, next_state)(),
            )()
        return self._extend_trie(
            tree, arcs_reversed, next_state, M.Tail(word_chain)(),
        )

    def __call__(self):
        return self.result


class LexicalGap(M.Edge):
    """The word-shaped hole between readings, and the category the grammar asks to fill it.

    Pair(readings, Pair(productions, Pair(spc_category, EmptyList))) ->
    Pair(start, Pair(end, Pair(category, EmptyList))), or EmptyList.

    A gap is a run between two space readings that no reading covers;
    spaces are observed events, so the run between two of them is a
    word-shaped hole, not a tokenized word. The category is read
    backwards through the grammar: the reading that starts where the
    right space ends anchors a production's right daughter; the left
    daughter then wants to end where the right space begins; and the
    glue production (word, space, left-daughter) says which
    word-category spans the gap. One backward step and one hop of
    glue -- what the grammar says at the boundary, no more.
    """

    def __init__(self, readings, productions, spc_category,
                 line_end=M.EmptyList):
        empty = M.EmptyList
        self.result = empty

        spaces_reversed = empty
        walker = readings
        while M.IdentityCompare(walker, empty)() is M.false_value:
            reading = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(M.Tail(reading)())(), spc_category,
            )() is M.truth_value:
                spaces_reversed = M.Pair(reading, spaces_reversed)
            walker = M.Tail(walker)()
        spaces = M.Reverse(spaces_reversed)()

        outer = spaces
        while M.IdentityCompare(outer, empty)() is M.false_value:
            if M.IdentityCompare(self.result, empty)() is M.false_value:
                outer = empty
            else:
                space_a = M.Head(outer)()
                gap_start = M.Head(M.Tail(M.Tail(M.Tail(space_a)())())())()
                inner = spaces
                while M.IdentityCompare(inner, empty)() is M.false_value:
                    if M.IdentityCompare(self.result, empty)() is M.false_value:
                        inner = empty
                    else:
                        space_b = M.Head(inner)()
                        gap_end = M.Head(M.Tail(M.Tail(space_b)())())()
                        forward = GMPLessText(
                            M.GMPRepText(gap_start)(),
                            M.GMPRepText(gap_end)(),
                        )()
                        if forward is M.truth_value:
                            uncovered = M.truth_value
                            check = readings
                            while M.IdentityCompare(check, empty)() is M.false_value:
                                other = M.Head(check)()
                                other_start = M.Head(M.Tail(M.Tail(other)())())()
                                other_end = M.Head(M.Tail(M.Tail(M.Tail(other)())())())()
                                starts_before_end = GMPLessText(
                                    M.GMPRepText(other_start)(),
                                    M.GMPRepText(gap_end)(),
                                )()
                                ends_after_start = GMPLessText(
                                    M.GMPRepText(gap_start)(),
                                    M.GMPRepText(other_end)(),
                                )()
                                if starts_before_end is M.truth_value:
                                    if ends_after_start is M.truth_value:
                                        uncovered = M.false_value
                                check = M.Tail(check)()
                            if uncovered is M.truth_value:
                                # The left context first: what has already
                                # been parsed up to the hole is the
                                # incremental reading order, and anchoring
                                # on the right reading first proposed a
                                # category the left context cannot use
                                # ("is seven prime": the right-anchored
                                # read saw ADJ and proposed DET for
                                # "seven"; the COPG on the left wants
                                # NUM). Right anchor stays as fallback.
                                self._infer_category_from_left(
                                    readings, productions, spc_category,
                                    gap_start, gap_end,
                                )
                                if M.IdentityCompare(
                                    self.result, empty,
                                )() is M.truth_value:
                                    self._infer_category(
                                        readings, productions, space_b,
                                        gap_start, gap_end,
                                    )
                        inner = M.Tail(inner)()
                outer = M.Tail(outer)()

        if M.IdentityCompare(self.result, empty)() is M.truth_value:
            # A word that ENDS the line has a left space but no right
            # space, so the two-space scan above never sees it. The
            # readings cannot say where the line ends -- an uncovered
            # final word leaves no reading over itself -- so the caller
            # passes the line's final cursor. A run from a space to
            # that cursor that no reading covers is the same
            # word-shaped hole, read leftward for its category.
            if M.IdentityCompare(line_end, empty)() is M.false_value:
                outer = spaces
                while M.IdentityCompare(outer, empty)() is M.false_value:
                    if M.IdentityCompare(
                        self.result, empty,
                    )() is M.false_value:
                        outer = empty
                    else:
                        space_a = M.Head(outer)()
                        gap_start = M.Head(
                            M.Tail(M.Tail(M.Tail(space_a)())())(),
                        )()
                        forward = GMPLessText(
                            M.GMPRepText(gap_start)(),
                            M.GMPRepText(line_end)(),
                        )()
                        if forward is M.truth_value:
                            uncovered = M.truth_value
                            check = readings
                            while M.IdentityCompare(
                                check, empty,
                            )() is M.false_value:
                                other = M.Head(check)()
                                other_start = M.Head(
                                    M.Tail(M.Tail(other)())(),
                                )()
                                other_end = M.Head(
                                    M.Tail(M.Tail(M.Tail(other)())())(),
                                )()
                                starts_before_end = GMPLessText(
                                    M.GMPRepText(other_start)(),
                                    M.GMPRepText(line_end)(),
                                )()
                                ends_after_start = GMPLessText(
                                    M.GMPRepText(gap_start)(),
                                    M.GMPRepText(other_end)(),
                                )()
                                if starts_before_end is M.truth_value:
                                    if ends_after_start is M.truth_value:
                                        uncovered = M.false_value
                                check = M.Tail(check)()
                            if uncovered is M.truth_value:
                                self._infer_category_from_left(
                                    readings, productions, spc_category,
                                    gap_start, line_end,
                                )
                        outer = M.Tail(outer)()

        super().__init__(
            inputs=M.Pair(
                readings,
                M.Pair(productions, M.Pair(spc_category, empty)),
            ),
            results=self.result,
        )

    def _infer_category(self, readings, productions, space_b, gap_start, gap_end):
        empty = M.EmptyList
        anchor_start = M.Head(M.Tail(M.Tail(M.Tail(space_b)())())())()
        walker = readings
        anchor_category = empty
        while M.IdentityCompare(walker, empty)() is M.false_value:
            reading = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(M.Tail(M.Tail(reading)())())(), anchor_start,
            )() is M.truth_value:
                anchor_category = M.Head(M.Tail(reading)())()
                walker = empty
            else:
                walker = M.Tail(walker)()
        if M.IdentityCompare(anchor_category, empty)() is M.truth_value:
            return
        outer = productions
        while M.IdentityCompare(outer, empty)() is M.false_value:
            production = M.Head(outer)()
            right_category = M.Head(M.Tail(M.Tail(production)())())()
            if M.IdentityCompare(right_category, anchor_category)() is M.truth_value:
                left_category = M.Head(M.Tail(production)())()
                inner = productions
                while M.IdentityCompare(inner, empty)() is M.false_value:
                    glue = M.Head(inner)()
                    glue_left = M.Head(M.Tail(glue)())()
                    glue_result = M.Head(M.Tail(M.Tail(M.Tail(glue)())())())()
                    if M.IdentityCompare(glue_result, left_category)() is M.truth_value:
                        self.result = M.Pair(
                            gap_start,
                            M.Pair(gap_end, M.Pair(glue_left, empty)),
                        )
                        inner = empty
                        outer = empty
                    else:
                        inner = M.Tail(inner)()
            else:
                outer = M.Tail(outer)()

    def _infer_category_from_left(
        self, readings, productions, spc_category, gap_start, gap_end,
    ):
        """The other half of the boundary read.

        The right-anchored half asks what the reading after the hole
        wants to its left; this half asks what the reading that ends
        where the hole begins wants to its right. A production whose
        left daughter is that category names the wanted category as
        its right daughter, and the wanted one must be a word
        category -- one that glues with a space to its right.
        Production order is the grammar's precedence when two
        productions want different things at the same boundary; the
        chart, not the inference, has the final word.
        """
        empty = M.EmptyList
        walker = readings
        anchor_category = empty
        while M.IdentityCompare(walker, empty)() is M.false_value:
            reading = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(M.Tail(reading)())(), spc_category,
            )() is M.truth_value:
                walker = M.Tail(walker)()
            elif M.IdentityCompare(
                M.Head(M.Tail(M.Tail(M.Tail(reading)())())())(), gap_start,
            )() is M.truth_value:
                anchor_category = M.Head(M.Tail(reading)())()
                walker = empty
            else:
                walker = M.Tail(walker)()
        if M.IdentityCompare(anchor_category, empty)() is M.truth_value:
            return
        outer = productions
        while M.IdentityCompare(outer, empty)() is M.false_value:
            production = M.Head(outer)()
            if M.IdentityCompare(
                M.Head(M.Tail(production)())(), anchor_category,
            )() is M.truth_value:
                wanted = M.Head(M.Tail(M.Tail(production)())())()
                inner = productions
                while M.IdentityCompare(inner, empty)() is M.false_value:
                    glue = M.Head(inner)()
                    glue_left = M.Head(M.Tail(glue)())()
                    glue_right = M.Head(M.Tail(M.Tail(glue)())())()
                    glue_result = M.Head(M.Tail(M.Tail(M.Tail(glue)())())())()
                    glue_is_space = M.IdentityCompare(
                        glue_right, spc_category,
                    )() is M.truth_value
                    word_direct = M.IdentityCompare(
                        glue_left, wanted,
                    )() is M.truth_value and glue_is_space
                    word_glued = M.IdentityCompare(
                        glue_result, wanted,
                    )() is M.truth_value and glue_is_space
                    if word_direct:
                        self.result = M.Pair(
                            gap_start,
                            M.Pair(gap_end, M.Pair(wanted, empty)),
                        )
                        inner = empty
                        outer = empty
                    elif word_glued:
                        self.result = M.Pair(
                            gap_start,
                            M.Pair(gap_end, M.Pair(glue_left, empty)),
                        )
                        inner = empty
                        outer = empty
                    else:
                        inner = M.Tail(inner)()
            else:
                outer = M.Tail(outer)()

    def __call__(self):
        return self.result


class ProvisionalWord(M.Edge):
    """A gap becomes lexicon: arcs for its symbols, and a sense with a hole.

    Pair(root, Pair(symbols, Pair(category, Pair(word, EmptyList)))) ->
    Pair(arcs, Pair(sense, Pair(final_state, EmptyList))). The states
    are fresh, the arcs spell the gap's symbols from the root, and the
    sense's meaning is Hole(word, EmptyList, NoDefinitionInstalled):
    the category came from the grammar, the meaning is not known yet,
    and the definition the word appears in is what will supply it.
    Learn the arcs and the sense into the running engine and drain;
    the chart completes without anything re-observing.
    """

    def __init__(self, root, symbols, category, word):
        empty = M.EmptyList
        arcs_reversed = empty
        state = root
        counter_text = "0"
        walker = symbols
        while M.IdentityCompare(walker, empty)() is M.false_value:
            next_state = M.Char("gap-st-" + counter_text)
            counter_text = GMPSuccText(counter_text)()
            arcs_reversed = M.Pair(
                FormArc(state, M.Head(walker)(), next_state)(),
                arcs_reversed,
            )
            state = next_state
            walker = M.Tail(walker)()
        sense = FormSense(
            state, category, Hole(word, empty, Lmod.NoDefinitionInstalledLabel)(),
        )()
        self.result = M.Pair(
            M.Reverse(arcs_reversed)(),
            M.Pair(sense, M.Pair(state, empty)),
        )
        super().__init__(
            inputs=M.Pair(
                root,
                M.Pair(
                    symbols,
                    M.Pair(category, M.Pair(word, empty)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RecogniseForms(M.Edge):
    """The reader's deduction, run by index and delta instead of by search.

    Three ordinary monotone laws, compiled by CompileDeductionToLaw and
    left whole:

        FormScan(?f, ?start, ?cur),
        ObservedSymbolStep(?u, ?cur, ?sym, ?next),
        FormArc(?f, ?sym, ?f2)
            ->  FormScan(?f2, ?start, ?next)

        FormScan(?f, ?start, ?cur),
        FormSense(?f, ?cat, ?mean)
            ->  Reading(?cat, ?start, ?cur, ?mean)

        Reading(?a, ?start, ?mid, ?ma),
        BinaryProduction(?a, ?b, ?c, ?t),
        Reading(?b, ?mid, ?end, ?mb)
            ->  Reading(?c, ?start, ?end, composed)

    The laws stay authoritative; the engine never reads them back to
    run. Each is executed through the DeductionPlan records keyed by
    trigger relation in PlansByTriggerRelation: a plan names its
    trigger premise, one lookup step per remaining premise -- an
    IndexSpec together with that premise's variable pattern -- and the
    conclusion template. The interpreter binds the trigger's arguments,
    resolves each lookup's key positions from those bindings, walks the
    index chains, checks the remaining bound arguments by identity,
    instantiates the conclusion, and inserts it. One plan exists per
    premise position of the first two laws, so facts arrive in any
    order: a late arc finds the scans waiting for it, a late sense the
    scans at its state. Composition is triggered by either daughter.
    The one position not executed is a production arriving after
    readings exist.

    Every fact enters through one insert that deduplicates on the
    relation's first declared index -- a lookup by the declared keys
    and a value comparison along the small chain it returns --
    maintains every declared index, and queues itself on the
    DeltaAgenda. The loop pops until the agenda is empty, which is
    quiescence; no pass ever rereads the store, and nothing asks the
    generic matcher anything. The indexes are red-black trees keyed on
    atoms, the one structure here with sublinear fan-out. All observed
    steps must belong to one utterance, and composition refuses a
    daughter of zero width: readings over an empty span would compose
    with themselves forever.
    """

    def __init__(self, steps, arcs, senses, root, productions):
        empty = M.EmptyList

        self.facts_inserted_text = "0"
        self.delta_popped_text = "0"
        self.index_lookups_text = "0"
        self.facts_returned_text = "0"
        self.conclusions_attempted_text = "0"
        self.new_conclusions_text = "0"
        self.full_store_enumerations_text = "0"
        self.freshen_count_text = "0"
        self.definition_count_text = "0"

        var_f = M.Pair(M.VarTag, M.Pair(M.Char("?f"), empty))
        var_start = M.Pair(M.VarTag, M.Pair(M.Char("?start"), empty))
        var_cur = M.Pair(M.VarTag, M.Pair(M.Char("?cur"), empty))
        var_u = M.Pair(M.VarTag, M.Pair(M.Char("?u"), empty))
        var_sym = M.Pair(M.VarTag, M.Pair(M.Char("?sym"), empty))
        var_next = M.Pair(M.VarTag, M.Pair(M.Char("?next"), empty))
        var_f2 = M.Pair(M.VarTag, M.Pair(M.Char("?f2"), empty))
        var_g = M.Pair(M.VarTag, M.Pair(M.Char("?g"), empty))
        var_s2 = M.Pair(M.VarTag, M.Pair(M.Char("?s2"), empty))
        var_c2 = M.Pair(M.VarTag, M.Pair(M.Char("?c2"), empty))
        var_cat = M.Pair(M.VarTag, M.Pair(M.Char("?cat"), empty))
        var_mean = M.Pair(M.VarTag, M.Pair(M.Char("?mean"), empty))
        var_ra = M.Pair(M.VarTag, M.Pair(M.Char("?ra"), empty))
        var_rb = M.Pair(M.VarTag, M.Pair(M.Char("?rb"), empty))
        var_rc = M.Pair(M.VarTag, M.Pair(M.Char("?rc"), empty))
        var_rs = M.Pair(M.VarTag, M.Pair(M.Char("?rs"), empty))
        var_re = M.Pair(M.VarTag, M.Pair(M.Char("?re"), empty))
        var_rmid = M.Pair(M.VarTag, M.Pair(M.Char("?rmid"), empty))
        var_rma = M.Pair(M.VarTag, M.Pair(M.Char("?rma"), empty))
        var_rmb = M.Pair(M.VarTag, M.Pair(M.Char("?rmb"), empty))
        var_rt = M.Pair(M.VarTag, M.Pair(M.Char("?rt"), empty))
        self._compose_start_var = var_rs
        self._compose_mid_var = var_rmid
        self._compose_end_var = var_re

        self.scan_law = CompileDeductionToLaw(
            P.MultiRule(
                M.Pair(
                    M.Pair(
                        Lmod.FormScanLabel,
                        M.Pair(var_f, M.Pair(var_start, M.Pair(var_cur, empty))),
                    ),
                    M.Pair(
                        M.Pair(
                            Lmod.ObservedSymbolStepLabel,
                            M.Pair(
                                var_u,
                                M.Pair(
                                    var_cur,
                                    M.Pair(var_sym, M.Pair(var_next, empty)),
                                ),
                            ),
                        ),
                        M.Pair(
                            M.Pair(
                                Lmod.FormArcLabel,
                                M.Pair(
                                    var_f,
                                    M.Pair(var_sym, M.Pair(var_f2, empty)),
                                ),
                            ),
                            empty,
                        ),
                    ),
                ),
                M.Pair(
                    Lmod.FormScanLabel,
                    M.Pair(var_f2, M.Pair(var_start, M.Pair(var_next, empty))),
                ),
            ),
        )()
        self.sense_law = CompileDeductionToLaw(
            P.MultiRule(
                M.Pair(
                    M.Pair(
                        Lmod.FormScanLabel,
                        M.Pair(var_g, M.Pair(var_s2, M.Pair(var_c2, empty))),
                    ),
                    M.Pair(
                        M.Pair(
                            Lmod.FormSenseLabel,
                            M.Pair(
                                var_g,
                                M.Pair(var_cat, M.Pair(var_mean, empty)),
                            ),
                        ),
                        empty,
                    ),
                ),
                M.Pair(
                    Lmod.ReadingLabel,
                    M.Pair(
                        var_cat,
                        M.Pair(
                            var_s2,
                            M.Pair(var_c2, M.Pair(var_mean, empty)),
                        ),
                    ),
                ),
            ),
        )()
        self.compose_law = CompileDeductionToLaw(
            P.MultiRule(
                M.Pair(
                    M.Pair(
                        Lmod.ReadingLabel,
                        M.Pair(
                            var_ra,
                            M.Pair(
                                var_rs,
                                M.Pair(var_rmid, M.Pair(var_rma, empty)),
                            ),
                        ),
                    ),
                    M.Pair(
                        M.Pair(
                            Lmod.BinaryProductionLabel,
                            M.Pair(
                                var_ra,
                                M.Pair(
                                    var_rb,
                                    M.Pair(var_rc, M.Pair(var_rt, empty)),
                                ),
                            ),
                        ),
                        M.Pair(
                            M.Pair(
                                Lmod.ReadingLabel,
                                M.Pair(
                                    var_rb,
                                    M.Pair(
                                        var_rmid,
                                        M.Pair(var_re, M.Pair(var_rmb, empty)),
                                    ),
                                ),
                            ),
                            empty,
                        ),
                    ),
                ),
                M.Pair(
                    Lmod.ReadingLabel,
                    M.Pair(
                        var_rc,
                        M.Pair(
                            var_rs,
                            M.Pair(
                                var_re,
                                M.Pair(
                                    M.Pair(
                                        Lmod.ComposeMeaningLabel,
                                        M.Pair(
                                            var_rt,
                                            M.Pair(
                                                var_rma,
                                                M.Pair(var_rmb, empty),
                                            ),
                                        ),
                                    ),
                                    empty,
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )()

        self.step_index_spec = IndexSpec(
            Lmod.ObservedSymbolStepLabel, M.Pair(M.GMPRep("1"), empty),
        )()
        self.arc_index_spec = IndexSpec(
            Lmod.FormArcLabel,
            M.Pair(M.GMPRep("0"), M.Pair(M.GMPRep("1"), empty)),
        )()
        self.sense_index_spec = IndexSpec(
            Lmod.FormSenseLabel, M.Pair(M.GMPRep("0"), empty),
        )()
        self.scan_cursor_index_spec = IndexSpec(
            Lmod.FormScanLabel, M.Pair(M.GMPRep("2"), empty),
        )()
        self.scan_state_index_spec = IndexSpec(
            Lmod.FormScanLabel, M.Pair(M.GMPRep("0"), empty),
        )()
        self.reading_start_index_spec = IndexSpec(
            Lmod.ReadingLabel,
            M.Pair(M.GMPRep("0"), M.Pair(M.GMPRep("1"), empty)),
        )()
        self.reading_end_index_spec = IndexSpec(
            Lmod.ReadingLabel,
            M.Pair(M.GMPRep("0"), M.Pair(M.GMPRep("2"), empty)),
        )()
        self.production_left_index_spec = IndexSpec(
            Lmod.BinaryProductionLabel, M.Pair(M.GMPRep("0"), empty),
        )()
        self.production_right_index_spec = IndexSpec(
            Lmod.BinaryProductionLabel, M.Pair(M.GMPRep("1"), empty),
        )()
        self.index_specs = M.Pair(
            self.step_index_spec,
            M.Pair(
                self.arc_index_spec,
                M.Pair(
                    self.sense_index_spec,
                    M.Pair(
                        self.scan_cursor_index_spec,
                        M.Pair(
                            self.scan_state_index_spec,
                            M.Pair(
                                self.reading_start_index_spec,
                                M.Pair(
                                    self.reading_end_index_spec,
                                    M.Pair(
                                        self.production_left_index_spec,
                                        M.Pair(
                                            self.production_right_index_spec,
                                            empty,
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )

        scan_pattern = M.Pair(
            Lmod.FormScanLabel,
            M.Pair(var_f, M.Pair(var_start, M.Pair(var_cur, empty))),
        )
        step_pattern = M.Pair(
            Lmod.ObservedSymbolStepLabel,
            M.Pair(
                var_u,
                M.Pair(var_cur, M.Pair(var_sym, M.Pair(var_next, empty))),
            ),
        )
        arc_pattern = M.Pair(
            Lmod.FormArcLabel,
            M.Pair(var_f, M.Pair(var_sym, M.Pair(var_f2, empty))),
        )
        sense_pattern = M.Pair(
            Lmod.FormSenseLabel,
            M.Pair(var_f, M.Pair(var_cat, M.Pair(var_mean, empty))),
        )
        reading_a_pattern = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                var_ra,
                M.Pair(var_rs, M.Pair(var_rmid, M.Pair(var_rma, empty))),
            ),
        )
        production_pattern = M.Pair(
            Lmod.BinaryProductionLabel,
            M.Pair(
                var_ra,
                M.Pair(var_rb, M.Pair(var_rc, M.Pair(var_rt, empty))),
            ),
        )
        reading_b_pattern = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                var_rb,
                M.Pair(var_rmid, M.Pair(var_re, M.Pair(var_rmb, empty))),
            ),
        )
        scan_conclusion = M.Pair(
            Lmod.FormScanLabel,
            M.Pair(var_f2, M.Pair(var_start, M.Pair(var_next, empty))),
        )
        reading_conclusion = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                var_cat,
                M.Pair(var_start, M.Pair(var_cur, M.Pair(var_mean, empty))),
            ),
        )
        compose_conclusion = M.Pair(
            Lmod.ReadingLabel,
            M.Pair(
                var_rc,
                M.Pair(
                    var_rs,
                    M.Pair(
                        var_re,
                        M.Pair(
                            M.Pair(
                                Lmod.ComposeMeaningLabel,
                                M.Pair(
                                    var_rt,
                                    M.Pair(var_rma, M.Pair(var_rmb, empty)),
                                ),
                            ),
                            empty,
                        ),
                    ),
                ),
            ),
        )

        self.plan_from_scan = DeductionPlan(
            self.scan_law,
            scan_pattern,
            M.Pair(
                M.Pair(
                    self.step_index_spec, M.Pair(step_pattern, empty),
                ),
                M.Pair(
                    M.Pair(self.arc_index_spec, M.Pair(arc_pattern, empty)),
                    empty,
                ),
            ),
            scan_conclusion,
        )()
        self.plan_from_step = DeductionPlan(
            self.scan_law,
            step_pattern,
            M.Pair(
                M.Pair(
                    self.scan_cursor_index_spec,
                    M.Pair(scan_pattern, empty),
                ),
                M.Pair(
                    M.Pair(self.arc_index_spec, M.Pair(arc_pattern, empty)),
                    empty,
                ),
            ),
            scan_conclusion,
        )()
        self.plan_from_arc = DeductionPlan(
            self.scan_law,
            arc_pattern,
            M.Pair(
                M.Pair(
                    self.scan_state_index_spec, M.Pair(scan_pattern, empty),
                ),
                M.Pair(
                    M.Pair(self.step_index_spec, M.Pair(step_pattern, empty)),
                    empty,
                ),
            ),
            scan_conclusion,
        )()
        self.plan_sense_from_scan = DeductionPlan(
            self.sense_law,
            scan_pattern,
            M.Pair(
                M.Pair(self.sense_index_spec, M.Pair(sense_pattern, empty)),
                empty,
            ),
            reading_conclusion,
        )()
        self.plan_sense_from_sense = DeductionPlan(
            self.sense_law,
            sense_pattern,
            M.Pair(
                M.Pair(
                    self.scan_state_index_spec, M.Pair(scan_pattern, empty),
                ),
                empty,
            ),
            reading_conclusion,
        )()
        self.plan_from_left_daughter = DeductionPlan(
            self.compose_law,
            reading_a_pattern,
            M.Pair(
                M.Pair(
                    self.production_left_index_spec,
                    M.Pair(production_pattern, empty),
                ),
                M.Pair(
                    M.Pair(
                        self.reading_start_index_spec,
                        M.Pair(reading_b_pattern, empty),
                    ),
                    empty,
                ),
            ),
            compose_conclusion,
        )()
        self.plan_from_right_daughter = DeductionPlan(
            self.compose_law,
            reading_b_pattern,
            M.Pair(
                M.Pair(
                    self.production_right_index_spec,
                    M.Pair(production_pattern, empty),
                ),
                M.Pair(
                    M.Pair(
                        self.reading_end_index_spec,
                        M.Pair(reading_a_pattern, empty),
                    ),
                    empty,
                ),
            ),
            compose_conclusion,
        )()
        self.plans = M.Pair(
            self.plan_from_scan,
            M.Pair(
                self.plan_from_step,
                M.Pair(
                    self.plan_from_arc,
                    M.Pair(
                        self.plan_sense_from_scan,
                        M.Pair(
                            self.plan_sense_from_sense,
                            M.Pair(
                                self.plan_from_left_daughter,
                                M.Pair(self.plan_from_right_daughter, empty),
                            ),
                        ),
                    ),
                ),
            ),
        )

        plans_by_trigger = empty
        plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.FormScanLabel,
            M.Pair(
                self.plan_from_scan,
                M.Pair(self.plan_sense_from_scan, empty),
            ),
        )()
        plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.ObservedSymbolStepLabel,
            M.Pair(self.plan_from_step, empty),
        )()
        plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.FormArcLabel,
            M.Pair(self.plan_from_arc, empty),
        )()
        plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.FormSenseLabel,
            M.Pair(self.plan_sense_from_sense, empty),
        )()
        self._plans_by_trigger = Tmod.IdentityRedBlackInsert(
            plans_by_trigger,
            Lmod.ReadingLabel,
            M.Pair(
                self.plan_from_left_daughter,
                M.Pair(self.plan_from_right_daughter, empty),
            ),
        )()

        registry = empty
        specs_walker = self.index_specs
        while M.IdentityCompare(specs_walker, empty)() is M.false_value:
            spec = M.Head(specs_walker)()
            registry = M.Pair(M.Pair(spec, M.Pair(empty, empty)), registry)
            specs_walker = M.Tail(specs_walker)()
        self._index_registry = M.Reverse(registry)()

        self._agenda = empty
        self._firings_reversed = empty
        self._readings_reversed = empty
        self._root_state = root

        remaining = steps
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            self._insert(M.Head(remaining)())
            remaining = M.Tail(remaining)()
        remaining = arcs
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            self._insert(M.Head(remaining)())
            remaining = M.Tail(remaining)()
        remaining = senses
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            self._insert(M.Head(remaining)())
            remaining = M.Tail(remaining)()
        remaining = productions
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            self._insert(M.Head(remaining)())
            remaining = M.Tail(remaining)()
        remaining = steps
        while M.IdentityCompare(remaining, empty)() is M.false_value:
            cursor = ObservedStepBefore(M.Head(remaining)())()
            self._insert(FormScan(root, cursor, cursor)())
            remaining = M.Tail(remaining)()

        self._steps_index_root = self._root_for(self.step_index_spec)
        self._arcs_index_root = self._root_for(self.arc_index_spec)
        self._senses_index_root = self._root_for(self.sense_index_spec)

        self._drain_agenda()
        self._assemble_result()
        super().__init__(
            inputs=M.Pair(
                steps,
                M.Pair(
                    arcs,
                    M.Pair(
                        senses, M.Pair(root, M.Pair(productions, empty)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _drain_agenda(self):
        empty = M.EmptyList
        while M.IdentityCompare(self._agenda, empty)() is M.false_value:
            fact = M.Head(self._agenda)()
            self._agenda = M.Tail(self._agenda)()
            self.delta_popped_text = GMPSuccText(self.delta_popped_text)()
            label = M.Head(fact)()
            held_plans = self._lookup(self._plans_by_trigger, label)
            walker = held_plans
            while M.IdentityCompare(walker, empty)() is M.false_value:
                self._execute_plan(M.Head(walker)(), fact)
                walker = M.Tail(walker)()

    def _assemble_result(self):
        self._steps_index_root = self._root_for(self.step_index_spec)
        self._arcs_index_root = self._root_for(self.arc_index_spec)
        self._senses_index_root = self._root_for(self.sense_index_spec)
        self.result = M.Pair(
            M.Reverse(self._readings_reversed)(),
            M.Pair(
                M.Reverse(self._firings_reversed)(),
                M.Pair(DeltaAgenda(self._agenda)(), M.EmptyList),
            ),
        )

    def Observe(self, utterance, before, symbol, after):
        """One observed symbol event, and the root scan it seeds.

        The client's whole contract: report each symbol as it arrives.
        The step enters through the same insert as every fact, and the
        cursor's scan is seeded whether or not one was there -- the
        dedupe decides. Drain afterwards to run the delta.
        """
        self._insert(ObservedSymbolStep(utterance, before, symbol, after)())
        return self._insert(FormScan(self._root_state, before, before)())

    def Drain(self):
        """Run the delta agenda to quiescence; the readings so far are
        the result. A conversation keeps arriving; this is how it does
        so without repaying the parse.
        """
        self._drain_agenda()
        self._assemble_result()
        return self.result

    def Learn(self, arcs, senses):
        """Teach lexicon facts mid-conversation.

        Arcs and senses enter through the same insert as every fact,
        the delta agenda carries them, and the drain completes the
        chart -- nothing re-observes, nothing restarts, and the
        counters show only the new work.
        """
        arcs_walker = arcs
        while M.IdentityCompare(arcs_walker, M.EmptyList)() is M.false_value:
            self._insert(M.Head(arcs_walker)())
            arcs_walker = M.Tail(arcs_walker)()
        senses_walker = senses
        while M.IdentityCompare(senses_walker, M.EmptyList)() is M.false_value:
            self._insert(M.Head(senses_walker)())
            senses_walker = M.Tail(senses_walker)()
        return self.Drain()

    def _lookup(self, tree, key):
        self.index_lookups_text = GMPSuccText(self.index_lookups_text)()
        return Tmod.IdentityRedBlackLookupValue(tree, key)()

    def _root_for(self, spec):
        walker = self._index_registry
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            if M.IdentityCompare(M.Head(entry)(), spec)() is M.truth_value:
                return M.Head(M.Tail(entry)())()
            walker = M.Tail(walker)()
        return M.EmptyList

    def _arg_at(self, args, position_text):
        counter = "0"
        walker = args
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            if GMPEqualText(counter, position_text)() is M.truth_value:
                return M.Head(walker)()
            counter = GMPSuccText(counter)()
            walker = M.Tail(walker)()
        return M.EmptyList

    def _binding(self, bindings, variable):
        walker = bindings
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            if M.IdentityCompare(
                M.Head(entry)(), variable,
            )() is M.truth_value:
                return M.Tail(entry)()
            walker = M.Tail(walker)()
        return M.false_value

    def _keys_from_fact(self, spec, fact):
        keys_reversed = M.EmptyList
        walker = M.Head(M.Tail(M.Tail(spec)())())()
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            keys_reversed = M.Pair(
                self._arg_at(
                    M.Tail(fact)(), M.GMPRepText(M.Head(walker)())(),
                ),
                keys_reversed,
            )
            walker = M.Tail(walker)()
        return M.Reverse(keys_reversed)()

    def _keys_from_pattern(self, spec, pattern, bindings):
        keys_reversed = M.EmptyList
        walker = M.Head(M.Tail(M.Tail(spec)())())()
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            variable = self._arg_at(
                M.Tail(pattern)(), M.GMPRepText(M.Head(walker)())(),
            )
            value = self._binding(bindings, variable)
            if value is M.false_value:
                return M.false_value
            keys_reversed = M.Pair(value, keys_reversed)
            walker = M.Tail(walker)()
        return M.Reverse(keys_reversed)()

    def _index_lookup(self, spec, keys):
        tree = self._root_for(spec)
        walker = keys
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(tree, M.EmptyList)() is M.truth_value:
                return M.EmptyList
            tree = self._lookup(tree, M.Head(walker)())
            walker = M.Tail(walker)()
        return tree

    def _index_insert(self, tree, keys, fact):
        key = M.Head(keys)()
        rest = M.Tail(keys)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            held = self._lookup(tree, key)
            if M.IdentityCompare(held, M.EmptyList)() is M.truth_value:
                held = M.EmptyList
            return Tmod.IdentityRedBlackInsert(
                tree, key, M.Pair(fact, held),
            )()
        subtree = self._lookup(tree, key)
        if M.IdentityCompare(subtree, M.EmptyList)() is M.truth_value:
            subtree = M.EmptyList
        return Tmod.IdentityRedBlackInsert(
            tree, key, self._index_insert(subtree, rest, fact),
        )()

    def _insert(self, fact):
        label = M.Head(fact)()

        walker = self._index_registry
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            spec = M.Head(entry)()
            if M.IdentityCompare(
                M.Head(M.Tail(spec)())(), label,
            )() is M.truth_value:
                keys = self._keys_from_fact(spec, fact)
                held = self._index_lookup(spec, keys)
                seen_walker = held
                while M.IdentityCompare(
                    seen_walker, M.EmptyList,
                )() is M.false_value:
                    if M.TermEqual(M.Head(seen_walker)(), fact)() is M.truth_value:
                        return M.false_value
                    seen_walker = M.Tail(seen_walker)()
                walker = M.EmptyList
            else:
                walker = M.Tail(walker)()

        updated = M.EmptyList
        walker = self._index_registry
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            spec = M.Head(entry)()
            root = M.Head(M.Tail(entry)())()
            if M.IdentityCompare(
                M.Head(M.Tail(spec)())(), label,
            )() is M.truth_value:
                root = self._index_insert(
                    root, self._keys_from_fact(spec, fact), fact,
                )
            updated = M.Pair(
                M.Pair(spec, M.Pair(root, M.EmptyList)), updated,
            )
            walker = M.Tail(walker)()
        self._index_registry = M.Reverse(updated)()

        if M.IdentityCompare(label, Lmod.ReadingLabel)() is M.truth_value:
            self._readings_reversed = M.Pair(fact, self._readings_reversed)

        self.facts_inserted_text = GMPSuccText(self.facts_inserted_text)()
        self._agenda = M.Pair(fact, self._agenda)
        return M.truth_value

    def _match_pattern(self, pattern, fact, bindings):
        pattern_args = M.Tail(pattern)()
        fact_args = M.Tail(fact)()
        extended = bindings
        while M.IdentityCompare(pattern_args, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(fact_args, M.EmptyList)() is M.truth_value:
                return M.false_value
            pattern_arg = M.Head(pattern_args)()
            fact_arg = M.Head(fact_args)()
            if M.IsPair(pattern_arg)() is M.truth_value:
                if M.IdentityCompare(
                    M.Head(pattern_arg)(), M.VarTag,
                )() is M.truth_value:
                    bound = self._binding(extended, pattern_arg)
                    if bound is M.false_value:
                        extended = M.Pair(
                            M.Pair(pattern_arg, fact_arg), extended,
                        )
                    else:
                        if M.IdentityCompare(
                            bound, fact_arg,
                        )() is M.false_value:
                            return M.false_value
                else:
                    if M.IdentityCompare(
                        pattern_arg, fact_arg,
                    )() is M.false_value:
                        return M.false_value
            else:
                if M.IdentityCompare(
                    pattern_arg, fact_arg,
                )() is M.false_value:
                    return M.false_value
            pattern_args = M.Tail(pattern_args)()
            fact_args = M.Tail(fact_args)()
        if M.IdentityCompare(fact_args, M.EmptyList)() is M.false_value:
            return M.false_value
        return extended

    def _execute_plan(self, plan, fact):
        law = M.Head(M.Tail(plan)())()
        trigger = M.Head(M.Tail(M.Tail(plan)())())()
        bindings = self._match_pattern(trigger, fact, M.EmptyList)
        if bindings is M.false_value:
            return
        steps = M.Head(M.Tail(M.Tail(M.Tail(plan)())())())()
        conclusion = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(plan)())())())())()
        self._run_steps(
            steps, bindings, M.Pair(fact, M.EmptyList), conclusion, law,
        )

    def _run_steps(self, steps, bindings, premises, conclusion, law):
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            self._conclude(conclusion, bindings, premises, law)
            return
        step = M.Head(steps)()
        spec = M.Head(step)()
        pattern = M.Head(M.Tail(step)())()
        keys = self._keys_from_pattern(spec, pattern, bindings)
        if keys is M.false_value:
            return
        held = self._index_lookup(spec, keys)
        walker = held
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            candidate = M.Head(walker)()
            self.facts_returned_text = GMPSuccText(self.facts_returned_text)()
            extended = self._match_pattern(pattern, candidate, bindings)
            if extended is not M.false_value:
                self._run_steps(
                    M.Tail(steps)(),
                    extended,
                    M.Pair(candidate, premises),
                    conclusion,
                    law,
                )
            walker = M.Tail(walker)()

    def _conclude(self, conclusion, bindings, premises, law):
        args_reversed = M.EmptyList
        walker = M.Tail(conclusion)()
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            built = self._build_arg(M.Head(walker)(), bindings)
            if built is M.false_value:
                return
            args_reversed = M.Pair(built, args_reversed)
            walker = M.Tail(walker)()
        fact = M.Pair(M.Head(conclusion)(), M.Reverse(args_reversed)())
        self.conclusions_attempted_text = GMPSuccText(
            self.conclusions_attempted_text,
        )()
        if self._insert(fact) is M.truth_value:
            self.new_conclusions_text = GMPSuccText(self.new_conclusions_text)()
            self._firings_reversed = M.Pair(
                IndexedFiring(law, premises, bindings, fact)(),
                self._firings_reversed,
            )

    def _build_arg(self, arg, bindings):
        if M.IsPair(arg)() is M.truth_value:
            if M.IdentityCompare(M.Head(arg)(), M.VarTag)() is M.truth_value:
                value = self._binding(bindings, arg)
                if value is M.false_value:
                    return M.false_value
                return value
            if M.IdentityCompare(
                M.Head(arg)(), Lmod.ComposeMeaningLabel,
            )() is M.truth_value:
                meaning = self._compose_meaning(arg, bindings)
                if meaning is M.false_value:
                    return M.false_value
                return self._build_arg(meaning, bindings)
            if M.IdentityCompare(
                M.Head(arg)(), Lmod.DefinitionMeaningLabel,
            )() is M.truth_value:
                return self._definition_meaning(arg)
            head_built = self._build_arg(M.Head(arg)(), bindings)
            if head_built is M.false_value:
                return M.false_value
            tail_built = self._build_arg(M.Tail(arg)(), bindings)
            if tail_built is M.false_value:
                return M.false_value
            return M.Pair(head_built, tail_built)
        return arg

    def _compose_meaning(self, marker, bindings):
        start = self._binding(bindings, self._compose_start_var)
        middle = self._binding(bindings, self._compose_mid_var)
        end = self._binding(bindings, self._compose_end_var)
        if start is M.false_value or middle is M.false_value:
            return M.false_value
        if end is M.false_value:
            return M.false_value
        if M.IdentityCompare(start, middle)() is M.truth_value:
            return M.false_value
        if M.IdentityCompare(middle, end)() is M.truth_value:
            return M.false_value
        template_var = M.Head(M.Tail(marker)())()
        left_var = M.Head(M.Tail(M.Tail(marker)())())()
        right_var = M.Head(M.Tail(M.Tail(M.Tail(marker)())())())()
        template = self._binding(bindings, template_var)
        left_meaning = self._binding(bindings, left_var)
        right_meaning = self._binding(bindings, right_var)
        if template is M.false_value:
            return M.false_value
        if left_meaning is M.false_value:
            return M.false_value
        if right_meaning is M.false_value:
            return M.false_value
        inner_template = template
        right_first = M.false_value
        if M.IsPair(template)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(template)(), Lmod.ProjectRightLabel,
            )() is M.truth_value:
                inner_template = M.Head(M.Tail(template)())()
                right_first = M.truth_value
        scope = M.GMPRep(self.freshen_count_text)
        self.freshen_count_text = GMPSuccText(self.freshen_count_text)()
        fresh = FreshenTemplate(inner_template, scope)
        fresh_bindings = M.EmptyList
        walker = fresh.bindings_chain
        slot = "0"
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            entry = M.Head(walker)()
            fresh_variable = M.Tail(entry)()
            if GMPEqualText(slot, "0")() is M.truth_value:
                if right_first is M.truth_value:
                    fresh_bindings = M.Pair(
                        M.Pair(fresh_variable, right_meaning), fresh_bindings,
                    )
                else:
                    fresh_bindings = M.Pair(
                        M.Pair(fresh_variable, left_meaning), fresh_bindings,
                    )
            else:
                if right_first is M.truth_value:
                    fresh_bindings = M.Pair(
                        M.Pair(fresh_variable, left_meaning), fresh_bindings,
                    )
                else:
                    fresh_bindings = M.Pair(
                        M.Pair(fresh_variable, right_meaning), fresh_bindings,
                    )
            slot = GMPSuccText(slot)()
            walker = M.Tail(walker)()
        return self._instantiate(fresh.instantiated, fresh_bindings)

    def _definition_meaning(self, marker):
        """The definition production: one scope, one self, and the graph.

        The grammar hands over one of two shapes. With the head-noun
        order -- "a prime number is divisible..." -- the left daughter
        is LexicalNp(concept, Pair(category, Pair(presuppositions,
        EmptyList))) and the right is the predicate chain. With the
        predicate-nominal order -- "a prime is a number divisible..."
        -- the left daughter is the bare concept and the right is
        Pair(chunk, predicate-chain), the category riding after the
        copula. This side allocates what no template can: the scope and
        the fresh self. The noun's presuppositions become conditions
        over that self; the reflexives among the fillers resolve to it,
        so "one and itself" and "itself and one" both read with one
        variable object in the application and the restriction alike --
        and the sample application pairs the self with the filler that
        is not itself, whichever order was spoken. The restriction
        becomes ExactFillers(relation, self, role, fillers) rather than
        a quantifier, because the parser records what was said and
        normalization is a law's job.
        """
        left = M.Head(M.Tail(marker)())()
        right = M.Head(M.Tail(M.Tail(marker)())())()
        if M.IdentityCompare(
            M.Tail(M.Tail(M.Tail(marker)())())(), M.EmptyList,
        )() is M.false_value:
            return M.false_value
        predicate_chain = M.EmptyList
        if M.IsPair(left)() is M.truth_value:
            if M.IdentityCompare(
                M.Head(left)(), Lmod.HoleLabel,
            )() is M.truth_value:
                concept = left
                if M.IsPair(right)() is M.false_value:
                    return M.false_value
                chunk = M.Head(right)()
                predicate_chain = M.Head(M.Tail(right)())()
                if M.IdentityCompare(
                    M.Tail(M.Tail(right)())(), M.EmptyList,
                )() is M.false_value:
                    return M.false_value
            elif M.IdentityCompare(
                M.Head(left)(), Lmod.LexicalNpLabel,
            )() is M.false_value:
                return M.false_value
            else:
                concept = M.Head(M.Tail(left)())()
                chunk = M.Head(M.Tail(M.Tail(left)())())()
                predicate_chain = right
        else:
            concept = left
            if M.IsPair(right)() is M.false_value:
                return M.false_value
            chunk = M.Head(right)()
            predicate_chain = M.Head(M.Tail(right)())()
            if M.IdentityCompare(
                M.Tail(M.Tail(right)())(), M.EmptyList,
            )() is M.false_value:
                return M.false_value
        if M.IsPair(chunk)() is M.false_value:
            return M.false_value
        category = M.Head(chunk)()
        presuppositions = M.Tail(chunk)()
        if M.IdentityCompare(predicate_chain, M.EmptyList)() is M.truth_value:
            return M.false_value
        relation = M.Head(predicate_chain)()
        rest = M.Tail(predicate_chain)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return M.false_value
        restriction = M.Head(rest)()
        if M.IdentityCompare(M.Tail(rest)(), M.EmptyList)() is M.false_value:
            return M.false_value
        if M.IsPair(restriction)() is M.false_value:
            return M.false_value
        if M.IdentityCompare(
            M.Head(restriction)(), Lmod.RestrictionLabel,
        )() is M.false_value:
            return M.false_value
        role = M.Head(M.Tail(restriction)())()
        fillers = M.Head(M.Tail(M.Tail(restriction)())())()
        if M.IdentityCompare(fillers, M.EmptyList)() is M.truth_value:
            return M.false_value

        scope = M.GMPRep(self.definition_count_text)
        self.definition_count_text = GMPSuccText(self.definition_count_text)()
        self_variable = M.Pair(
            M.VarTag, M.Pair(scope, M.Pair(M.Char("?self"), M.EmptyList)),
        )
        resolved_fillers = ResolveReflexives(fillers, self_variable)()
        chosen_filler = M.EmptyList
        filler_walker = resolved_fillers
        while M.IdentityCompare(filler_walker, M.EmptyList)() is M.false_value:
            candidate_filler = M.Head(filler_walker)()
            if M.IdentityCompare(
                candidate_filler, self_variable,
            )() is M.false_value:
                chosen_filler = candidate_filler
                filler_walker = M.EmptyList
            else:
                filler_walker = M.Tail(filler_walker)()
        if M.IdentityCompare(chosen_filler, M.EmptyList)() is M.truth_value:
            chosen_filler = M.Head(resolved_fillers)()

        conditions_reversed = M.Pair(
            M.Pair(
                Lmod.ExactFillersLabel,
                M.Pair(
                    relation,
                    M.Pair(
                        self_variable,
                        M.Pair(role, M.Pair(resolved_fillers, M.EmptyList)),
                    ),
                ),
            ),
            M.EmptyList,
        )
        conditions_reversed = M.Pair(
            M.Pair(
                relation,
                M.Pair(
                    chosen_filler,
                    M.Pair(self_variable, M.EmptyList),
                ),
            ),
            conditions_reversed,
        )
        walker = presuppositions
        while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
            condition_marker = M.Head(walker)()
            conditions_reversed = M.Pair(
                M.Pair(
                    M.Head(condition_marker)(),
                    M.Pair(self_variable, M.EmptyList),
                ),
                conditions_reversed,
            )
            walker = M.Tail(walker)()
        conditions = conditions_reversed

        definiendum = M.Pair(
            Lmod.DefiniendumLabel,
            M.Pair(concept, M.Pair(category, M.EmptyList)),
        )
        return DefinitionNode(
            definiendum, Binder(scope, self_variable)(), conditions,
        )()

    def _instantiate(self, term, bindings):
        if M.IsPair(term)() is M.truth_value:
            if M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.truth_value:
                value = self._binding(bindings, term)
                if value is M.false_value:
                    return term
                return value
            return M.Pair(
                self._instantiate(M.Head(term)(), bindings),
                self._instantiate(M.Tail(term)(), bindings),
            )
        return term

    def __call__(self):
        return self.result


class ReadingPolicy(M.Edge):
    """What counts as a word, stated as data rather than as string surgery.

    Pair(ReadingPolicyLabel, Pair(separators, Pair(discarded,
    Pair(standalone, Pair(foldings, EmptyList))))).

    Reading a typed line used to be a chain of host replaces: lowercase
    the line, blank out the sentence punctuation, pad the brackets and
    the comma with spaces, split on whitespace, spell out any word that
    is all digits. Six decisions about what a word is, made in Python
    before the machine saw anything, and none of them stateable,
    retirable or learnable. A pack that wanted a semicolon for a
    separator would have had to edit the reader.

    Each of those decisions is a chain here. Separators end a word.
    Discarded characters end a word and are dropped. Standalone
    characters end a word and are one themselves -- which is the whole
    of why a comma is a word. Foldings say which character stands for
    which, so case is a correspondence rather than a method call.
    """

    def __init__(self, separators, discarded, standalone, foldings):
        self.result = M.Pair(
            Lmod.ReadingPolicyLabel,
            M.Pair(
                separators,
                M.Pair(discarded, M.Pair(standalone, M.Pair(foldings, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                separators,
                M.Pair(discarded, M.Pair(standalone, M.Pair(foldings, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReadingPolicySeparators(M.Edge):
    def __init__(self, policy):
        self.result = M.Head(M.Tail(policy)())()
        super().__init__(inputs=M.Pair(policy, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReadingPolicyDiscarded(M.Edge):
    def __init__(self, policy):
        self.result = M.Head(M.Tail(M.Tail(policy)())())()
        super().__init__(inputs=M.Pair(policy, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReadingPolicyStandalone(M.Edge):
    def __init__(self, policy):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(policy)())())())()
        super().__init__(inputs=M.Pair(policy, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ReadingPolicyFoldings(M.Edge):
    def __init__(self, policy):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(policy)())())())(),
        )()
        super().__init__(inputs=M.Pair(policy, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class DefaultReadingPolicy(M.Edge):
    """The reader's own decisions, as the chains a pack could replace.

    These reproduce exactly what the host replaces used to do: space,
    tab and newline break a word; a full stop, question mark and
    exclamation mark break one and vanish; a bracket or a comma is a
    word standing alone; and each capital stands for its small letter.
    """

    def __init__(self):
        empty = M.EmptyList
        separators = M.Pair(
            M.Char(" "),
            M.Pair(M.Char("\t"), M.Pair(M.Char("\n"), M.Pair(M.Char("\r"), empty))),
        )
        discarded = M.Pair(
            M.Char("."),
            M.Pair(M.Char("?"), M.Pair(M.Char("!"), empty)),
        )
        standalone = M.Pair(
            M.Char("("),
            M.Pair(M.Char(")"), M.Pair(M.Char(","), empty)),
        )
        foldings = empty
        foldings = M.Pair(M.Pair(M.Char("Z"), M.Pair(M.Char("z"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("Y"), M.Pair(M.Char("y"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("X"), M.Pair(M.Char("x"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("W"), M.Pair(M.Char("w"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("V"), M.Pair(M.Char("v"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("U"), M.Pair(M.Char("u"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("T"), M.Pair(M.Char("t"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("S"), M.Pair(M.Char("s"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("R"), M.Pair(M.Char("r"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("Q"), M.Pair(M.Char("q"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("P"), M.Pair(M.Char("p"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("O"), M.Pair(M.Char("o"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("N"), M.Pair(M.Char("n"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("M"), M.Pair(M.Char("m"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("L"), M.Pair(M.Char("l"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("K"), M.Pair(M.Char("k"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("J"), M.Pair(M.Char("j"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("I"), M.Pair(M.Char("i"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("H"), M.Pair(M.Char("h"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("G"), M.Pair(M.Char("g"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("F"), M.Pair(M.Char("f"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("E"), M.Pair(M.Char("e"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("D"), M.Pair(M.Char("d"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("C"), M.Pair(M.Char("c"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("B"), M.Pair(M.Char("b"), empty)), foldings)
        foldings = M.Pair(M.Pair(M.Char("A"), M.Pair(M.Char("a"), empty)), foldings)
        self.result = ReadingPolicy(separators, discarded, standalone, foldings)()
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class FoldCharacter(M.Edge):
    """The character this one stands for, or itself when nothing says."""

    def __init__(self, character, foldings):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = character
        scan_text = "0"
        remaining = foldings
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining)()
                if M.Compare(M.Head(entry)(), character)() is M.truth_value:
                    self.result = M.Head(M.Tail(entry)())()
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(character, M.Pair(foldings, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WordForDigitCharacter(M.Edge):
    """The number word a digit character names, or EmptyList.

    The inverse of SurfaceDigitOfWord, over the same chain, so the
    reader and the printer agree by construction about which digit is
    which word.
    """

    def __init__(self, character, digit_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        scan_text = "0"
        remaining = digit_words
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining)()
                if M.Compare(M.Head(entry)(), character)() is M.truth_value:
                    self.result = M.Head(M.Tail(entry)())()
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(character, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WordsOfStream(M.Edge):
    """A stream of characters as words, by the policy and nothing else.

    The host boundary and the word rule in one place, because splitting
    a line into one-character atoms and then concatenating them back
    into a word is ceremony: it allocates a Char and three identities
    per character to arrive at the string it started from. What the
    policy decides is data -- these chains -- and what the host does is
    read.

    Characters arrive one at a time from the stream, so no host
    container is walked. Each is folded through the policy, then asked
    of the policy's chains: a separator ends the run, a discarded
    character ends it and is gone, a standalone character ends it and
    is a word itself, which is the whole of why a comma is a word. A
    finished run that is entirely digits becomes one number word per
    digit through the same chain RenderNatSurface prints with, so
    reader and printer agree by construction; a run that is not stays
    whole, so e2 and sqrt2 survive.
    """

    def __init__(self, stream, policy, digit_words):
        separators = ReadingPolicySeparators(policy)()
        discarded = ReadingPolicyDiscarded(policy)()
        standalone = ReadingPolicyStandalone(policy)()
        foldings = ReadingPolicyFoldings(policy)()
        reversed_words = M.EmptyList
        run_text = ""
        run_digits = M.EmptyList
        all_digits = M.truth_value
        reading = M.truth_value
        while M.IdentityCompare(reading, M.truth_value)() is M.truth_value:
            symbol = stream.read(1)
            if symbol == "":
                reading = M.false_value
                character = M.Head(separators)()
            else:
                character = FoldCharacter(M.Char(symbol), foldings)()
            ends_run = M.false_value
            stands_alone = M.false_value
            if SurfaceChainHasWord(separators, character)() is M.truth_value:
                ends_run = M.truth_value
            elif SurfaceChainHasWord(discarded, character)() is M.truth_value:
                ends_run = M.truth_value
            elif SurfaceChainHasWord(standalone, character)() is M.truth_value:
                ends_run = M.truth_value
                stands_alone = M.truth_value
            if M.IdentityCompare(ends_run, M.false_value)() is M.truth_value:
                digit_word = WordForDigitCharacter(character, digit_words)()
                if M.IdentityCompare(digit_word, M.EmptyList)() is M.truth_value:
                    all_digits = M.false_value
                else:
                    run_digits = M.Pair(digit_word, run_digits)
                run_text = run_text + character()
            else:
                if run_text != "":
                    if M.IdentityCompare(all_digits, M.truth_value)() is M.truth_value:
                        spelled = M.Reverse(run_digits)()
                        while M.IdentityCompare(
                            spelled, M.EmptyList,
                        )() is M.false_value:
                            reversed_words = M.Pair(
                                M.Head(spelled)(), reversed_words,
                            )
                            spelled = M.Tail(spelled)()
                    else:
                        reversed_words = M.Pair(M.Char(run_text), reversed_words)
                run_text = ""
                run_digits = M.EmptyList
                all_digits = M.truth_value
                if M.IdentityCompare(stands_alone, M.truth_value)() is M.truth_value:
                    reversed_words = M.Pair(character, reversed_words)
        self.result = M.Reverse(reversed_words)()
        super().__init__(
            inputs=M.Pair(policy, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WordsOfText(M.Edge):
    """Host text as words: the one place a stream is made of a string."""

    def __init__(self, text, policy, digit_words):
        self.result = WordsOfStream(io.StringIO(text), policy, digit_words)()
        super().__init__(
            inputs=M.Pair(policy, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WordChainWithout(M.Edge):
    """The words of a chain that are not in `unwanted`."""

    def __init__(self, words, unwanted):
        reversed_kept = M.EmptyList
        remaining = words
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            word = M.Head(remaining)()
            if SurfaceChainHasWord(unwanted, word)() is M.false_value:
                reversed_kept = M.Pair(word, reversed_kept)
            remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_kept)()
        super().__init__(
            inputs=M.Pair(words, M.Pair(unwanted, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SoleWord(M.Edge):
    """The one word of a chain, or EmptyList when there is not exactly one.

    "what is a triangle" asks about one term. Reading that used to be a
    host comprehension over a host list and a length check; the question
    it answers is about a chain, and this is that question.
    """

    def __init__(self, words):
        self.result = M.EmptyList
        if M.IdentityCompare(words, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(M.Tail(words)(), M.EmptyList)() is M.truth_value:
                self.result = M.Head(words)()
        super().__init__(
            inputs=M.Pair(words, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionTermAndBody(M.Edge):
    """Split "a triangle is a polygon ..." into its term and its body.

    Leading articles are skipped, the next word is the term being
    defined, a copula after it is dropped, and what remains is the body.
    Returns Pair(term, Pair(body, EmptyList)), or EmptyList when there
    is no term or no body left to define it with.

    The console did this by walking an index over a host list and
    slicing it, then building the very chain it had just taken apart.
    The articles and the copulas are chains here, so a reader that says
    "one triangle is ..." is a longer chain rather than a longer tuple
    in Python.
    """

    def __init__(self, words, articles, copulas):
        self.result = M.EmptyList
        remaining = words
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if SurfaceChainHasWord(articles, M.Head(remaining)())() is M.truth_value:
                remaining = M.Tail(remaining)()
            else:
                term = M.Head(remaining)()
                body = M.Tail(remaining)()
                if M.IdentityCompare(body, M.EmptyList)() is M.false_value:
                    if SurfaceChainHasWord(
                        copulas, M.Head(body)(),
                    )() is M.truth_value:
                        body = M.Tail(body)()
                if M.IdentityCompare(body, M.EmptyList)() is M.false_value:
                    self.result = M.Pair(term, M.Pair(body, M.EmptyList))
                remaining = M.EmptyList
        super().__init__(
            inputs=M.Pair(
                words, M.Pair(articles, M.Pair(copulas, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceOfText(M.Edge):
    """A typed line as a Surface, through the policy."""

    def __init__(self, text, policy, digit_words):
        self.words = WordsOfText(text, policy, digit_words)()
        self.result = Surface(self.words)()
        super().__init__(
            inputs=M.Pair(policy, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Surface(M.Edge):
    """A surface form: an ordered Pair chain of symbol atoms."""

    def __init__(self, symbol_chain):
        self.result = M.Pair(
            Lmod.SurfaceLabel,
            M.Pair(symbol_chain, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(symbol_chain, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Meaning(M.Edge):
    """A structural interpretation wrapped as a labeled term."""

    def __init__(self, graph_term):
        self.result = M.Pair(
            Lmod.MeaningLabel,
            M.Pair(graph_term, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(graph_term, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Corresponds(M.Edge):
    """A recorded correspondence between one surface and one meaning."""

    def __init__(self, surface_term, meaning_term, law):
        self.result = M.Pair(
            Lmod.CorrespondsLabel,
            M.Pair(
                surface_term,
                M.Pair(meaning_term, M.Pair(law, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                surface_term,
                M.Pair(meaning_term, M.Pair(law, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CorrespondenceApply(M.Edge):
    """Apply one correspondence law in one direction via the term matcher.

    The law is a compiled Law whose single L node is the source pattern and
    whose single R node is the target template. Returns the instantiated
    target term, or EmptyList when the source does not match.
    """

    def __init__(self, law, source_term):
        self.result = M.EmptyList
        if IsLawTerm(law)() is M.truth_value:
            left_nodes = GraphNodes(LawLeft(law)())()
            right_nodes = GraphNodes(LawRight(law)())()
            if M.IdentityCompare(left_nodes, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(right_nodes, M.EmptyList)() is M.false_value:
                    pattern = M.Head(left_nodes)()
                    template = M.Head(right_nodes)()
                    matched = M.Match(pattern, source_term)()
                    if M.IdentityCompare(
                        M.Head(matched)(),
                        M.truth_value,
                    )() is M.truth_value:
                        self.result = M.Head(
                            M.Instantiate(template, M.Tail(matched)())(),
                        )()
        super().__init__(
            inputs=M.Pair(law, M.Pair(source_term, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


CORRESPONDENCE_SCAN_CAP = M.GMPRep("200")


class CorrespondenceWordEntry(M.Edge):
    """One vocabulary word: its parse law and its render association."""

    def __init__(self, word_symbol, nat):
        parse_law = CompileRuleToLaw(
            P.Rule(Surface(M.Pair(word_symbol, M.EmptyList))(), nat),
        )()
        self.result = M.Pair(
            word_symbol,
            M.Pair(nat, M.Pair(parse_law, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(word_symbol, M.Pair(nat, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefaultCorrespondenceVocabulary(M.Edge):
    """Hand-authored correspondence laws for spoken arithmetic sentences.

    Pair(template_law_chain, Pair(word_entry_chain, Pair(digit_word_chain,
    EmptyList))). Every law is compiled through CompileRuleToLaw; nothing
    here parses host strings.
    """

    def __init__(self):
        empty = M.EmptyList
        var_a = M.Pair(M.VarTag, M.Pair(M.Char("?a"), empty))
        var_b = M.Pair(M.VarTag, M.Pair(M.Char("?b"), empty))
        var_c = M.Pair(M.VarTag, M.Pair(M.Char("?c"), empty))

        # A definition body is a sentence, so it is read the way every
        # other sentence is read: by correspondence templates that are
        # themselves laws. The relation words were a host list and the
        # parse a hand-written state machine; each shape below is one law
        # instead, so a new phrasing is a new template rather than a new
        # branch, and induction can learn one from examples.
        genus_meaning = Meaning(
            M.Pair(
                M.DefinitionGenusLabel,
                M.Pair(Surface(M.Pair(var_a, empty))(), empty),
            ),
        )()
        counted_meaning = Meaning(
            M.Pair(
                M.DefinitionCountedLabel,
                M.Pair(
                    Surface(M.Pair(var_a, empty))(),
                    M.Pair(
                        Surface(M.Pair(var_b, empty))(),
                        M.Pair(Surface(M.Pair(var_c, empty))(), empty),
                    ),
                ),
            ),
        )()
        genus_body = Surface(M.Pair(M.Char("a"), M.Pair(var_a, empty)))()
        genus_body_bare = Surface(M.Pair(var_a, empty))()
        with_body = Surface(
            M.Pair(
                M.Char("a"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("with"),
                        M.Pair(var_b, M.Pair(var_c, empty)),
                    ),
                ),
            ),
        )()
        having_body = Surface(
            M.Pair(
                M.Char("a"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("having"),
                        M.Pair(var_b, M.Pair(var_c, empty)),
                    ),
                ),
            ),
        )()
        has_body = Surface(
            M.Pair(
                M.Char("a"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("has"),
                        M.Pair(var_b, M.Pair(var_c, empty)),
                    ),
                ),
            ),
        )()
        whose_body = Surface(
            M.Pair(
                M.Char("a"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("whose"),
                        M.Pair(var_b, M.Pair(var_c, empty)),
                    ),
                ),
            ),
        )()

        add_meaning = Meaning(
            M.Pair(
                M.ExprAddLabel,
                M.Pair(
                    Surface(M.Pair(var_a, empty))(),
                    M.Pair(Surface(M.Pair(var_b, empty))(), empty),
                ),
            ),
        )()
        mul_meaning = Meaning(
            M.Pair(
                M.ExprMulLabel,
                M.Pair(
                    Surface(M.Pair(var_a, empty))(),
                    M.Pair(Surface(M.Pair(var_b, empty))(), empty),
                ),
            ),
        )()

        sum_sentence = Surface(
            M.Pair(
                M.Char("the"),
                M.Pair(
                    M.Char("sum"),
                    M.Pair(
                        M.Char("of"),
                        M.Pair(
                            var_a,
                            M.Pair(M.Char("and"), M.Pair(var_b, empty)),
                        ),
                    ),
                ),
            ),
        )()
        product_sentence = Surface(
            M.Pair(
                M.Char("the"),
                M.Pair(
                    M.Char("product"),
                    M.Pair(
                        M.Char("of"),
                        M.Pair(
                            var_a,
                            M.Pair(M.Char("and"), M.Pair(var_b, empty)),
                        ),
                    ),
                ),
            ),
        )()
        plus_sentence = Surface(
            M.Pair(var_a, M.Pair(M.Char("plus"), M.Pair(var_b, empty))),
        )()
        times_sentence = Surface(
            M.Pair(var_a, M.Pair(M.Char("times"), M.Pair(var_b, empty))),
        )()
        formal_mul_sentence = Surface(
            M.Pair(
                M.Char("mul"),
                M.Pair(
                    M.Char("("),
                    M.Pair(
                        var_a,
                        M.Pair(
                            M.Char(","),
                            M.Pair(var_b, M.Pair(M.Char(")"), empty)),
                        ),
                    ),
                ),
            ),
        )()
        formal_add_sentence = Surface(
            M.Pair(
                M.Char("add"),
                M.Pair(
                    M.Char("("),
                    M.Pair(
                        var_a,
                        M.Pair(
                            M.Char(","),
                            M.Pair(var_b, M.Pair(M.Char(")"), empty)),
                        ),
                    ),
                ),
            ),
        )()
        equal_meaning = Meaning(
            M.Pair(
                Lmod.EqualLabel,
                M.Pair(
                    Surface(M.Pair(var_a, empty))(),
                    M.Pair(Surface(M.Pair(var_b, empty))(), empty),
                ),
            ),
        )()
        real_meaning = Meaning(
            M.Pair(
                M.IsRealLabel,
                M.Pair(
                    M.Pair(
                        M.SqrtLabel,
                        M.Pair(Surface(M.Pair(var_a, empty))(), empty),
                    ),
                    empty,
                ),
            ),
        )()
        # A radicand may itself be a root. "sqrt ( X )" on its own is not a
        # sentence and has no value, so the group reducer had nothing to
        # splice and the whole sentence failed. As a phrase it does have a
        # meaning -- the Sqrt term -- which is exactly what the surrounding
        # slot wants.
        sqrt_phrase = Surface(
            M.Pair(
                M.Char("sqrt"),
                M.Pair(
                    M.Char("("),
                    M.Pair(var_a, M.Pair(M.Char(")"), empty)),
                ),
            ),
        )()
        # Once the inner group has reduced, the radicand is a spliced term and
        # the brackets are gone: the phrase reaching the reducer is "sqrt X",
        # not "sqrt ( X )". Both forms mean the same root.
        sqrt_bare_phrase = Surface(
            M.Pair(M.Char("sqrt"), M.Pair(var_a, empty)),
        )()
        sqrt_phrase_meaning = Meaning(
            M.Pair(
                M.SqrtLabel,
                M.Pair(Surface(M.Pair(var_a, empty))(), empty),
            ),
        )()
        equal_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    var_a,
                    M.Pair(
                        M.Char("equal"),
                        M.Pair(M.Char("to"), M.Pair(var_b, empty)),
                    ),
                ),
            ),
        )()
        real_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    M.Char("sqrt"),
                    M.Pair(
                        M.Char("("),
                        M.Pair(
                            var_a,
                            M.Pair(M.Char(")"), M.Pair(M.Char("real"), empty)),
                        ),
                    ),
                ),
            ),
        )()

        # The reducer strips the brackets it consumes, so a sentence whose
        # radicand was a group arrives as "is sqrt X real". The bracketed
        # form above still matches what the reader typed; this matches what
        # reduction leaves behind.
        real_bare_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(
                    M.Char("sqrt"),
                    M.Pair(var_a, M.Pair(M.Char("real"), empty)),
                ),
            ),
        )()

        even_meaning = Meaning(
            M.Pair(
                Lmod.EvenPropLabel,
                M.Pair(Surface(M.Pair(var_a, empty))(), empty),
            ),
        )()
        odd_meaning = Meaning(
            M.Pair(
                Lmod.OddPropLabel,
                M.Pair(Surface(M.Pair(var_a, empty))(), empty),
            ),
        )()
        even_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(var_a, M.Pair(M.Char("even"), empty)),
            ),
        )()
        odd_sentence = Surface(
            M.Pair(
                M.Char("is"),
                M.Pair(var_a, M.Pair(M.Char("odd"), empty)),
            ),
        )()

        def _task_meaning(task_name):
            return Meaning(
                M.Pair(Lmod.TaskLabel, M.Pair(M.Char(task_name), empty)),
            )()

        def _task_law(task_meaning_term, *symbols):
            chain = empty
            index = len(symbols)
            while index != 0:
                index = index - 1
                chain = M.Pair(M.Char(symbols[index]), chain)
            return CompileRuleToLaw(P.Rule(Surface(chain)(), task_meaning_term))()

        diagnostics_meaning = _task_meaning("self-diagnostics")
        tao_meaning = _task_meaning("tao")
        e1_meaning = _task_meaning("e1")
        e2_meaning = _task_meaning("e2")
        coins_meaning = _task_meaning("coins")
        sqrt_meaning = _task_meaning("sqrt")

        templates = M.Pair(
            CompileRuleToLaw(P.Rule(with_body, counted_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(having_body, counted_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(has_body, counted_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(whose_body, counted_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(genus_body, genus_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(genus_body_bare, genus_meaning))(),
            M.Pair(
            CompileRuleToLaw(P.Rule(equal_sentence, equal_meaning))(),
            M.Pair(
                CompileRuleToLaw(P.Rule(even_sentence, even_meaning))(),
            M.Pair(
                CompileRuleToLaw(P.Rule(odd_sentence, odd_meaning))(),
            M.Pair(
                CompileRuleToLaw(P.Rule(real_sentence, real_meaning))(),
                M.Pair(
                    CompileRuleToLaw(
                        P.Rule(sqrt_phrase, sqrt_phrase_meaning),
                    )(),
                M.Pair(
                    CompileRuleToLaw(
                        P.Rule(sqrt_bare_phrase, sqrt_phrase_meaning),
                    )(),
                M.Pair(
                    CompileRuleToLaw(
                        P.Rule(real_bare_sentence, real_meaning),
                    )(),
                M.Pair(
                    CompileRuleToLaw(P.Rule(sum_sentence, add_meaning))(),
                    M.Pair(
                        CompileRuleToLaw(P.Rule(product_sentence, mul_meaning))(),
                        M.Pair(
                            CompileRuleToLaw(P.Rule(plus_sentence, add_meaning))(),
                            M.Pair(
                                CompileRuleToLaw(
                                    P.Rule(times_sentence, mul_meaning),
                                )(),
                                M.Pair(
                                    CompileRuleToLaw(
                                        P.Rule(formal_mul_sentence, mul_meaning),
                                    )(),
                                    M.Pair(
                                        CompileRuleToLaw(
                                            P.Rule(formal_add_sentence, add_meaning),
                                        )(),
                                        M.Pair(
                                            _task_law(
                                                diagnostics_meaning,
                                                "run", "self-diagnostics",
                                            ),
                                            M.Pair(
                                                _task_law(
                                                    diagnostics_meaning,
                                                    "run", "the", "tests",
                                                ),
                                                M.Pair(
                                                    _task_law(
                                                        tao_meaning,
                                                        "solve", "the", "tao",
                                                        "triangle", "problem",
                                                    ),
                                                    M.Pair(
                                                        _task_law(
                                                            tao_meaning,
                                                            "solve", "tao",
                                                        ),
                                                        M.Pair(
                                                            _task_law(
                                                                e2_meaning,
                                                                "solve", "engel", "e2",
                                                            ),
                                                            M.Pair(
                                                                _task_law(
                                                                    e1_meaning,
                                                                    "solve", "engel", "e1",
                                                                ),
                                                                M.Pair(
                                                                    _task_law(
                                                                        coins_meaning,
                                                                        "solve", "the",
                                                                        "coin", "problem",
                                                                    ),
                                                                    M.Pair(
                                                                        _task_law(
                                                                            sqrt_meaning,
                                                                            "prove", "square",
                                                                            "roots", "are",
                                                                            "real",
                                                                        ),
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

        words = M.Pair(
            CorrespondenceWordEntry(M.Char("zero"), M.Zero)(),
            M.Pair(
                CorrespondenceWordEntry(M.Char("one"), M.one)(),
                M.Pair(
                    CorrespondenceWordEntry(M.Char("two"), M.two)(),
                    M.Pair(
                        CorrespondenceWordEntry(M.Char("three"), M.three)(),
                        M.Pair(
                            CorrespondenceWordEntry(M.Char("four"), M.four)(),
                            M.Pair(
                                CorrespondenceWordEntry(M.Char("five"), M.five)(),
                                M.Pair(
                                    CorrespondenceWordEntry(M.Char("six"), M.six)(),
                                    M.Pair(
                                        CorrespondenceWordEntry(
                                            M.Char("seven"),
                                            M.seven,
                                        )(),
                                        M.Pair(
                                            CorrespondenceWordEntry(
                                                M.Char("eight"),
                                                M.eight,
                                            )(),
                                            M.Pair(
                                                CorrespondenceWordEntry(
                                                    M.Char("nine"),
                                                    M.nine,
                                                )(),
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
        )

        digit_words = M.Pair(
            M.Pair(M.Char("0"), M.Pair(M.Char("zero"), empty)),
            M.Pair(
                M.Pair(M.Char("1"), M.Pair(M.Char("one"), empty)),
                M.Pair(
                    M.Pair(M.Char("2"), M.Pair(M.Char("two"), empty)),
                    M.Pair(
                        M.Pair(M.Char("3"), M.Pair(M.Char("three"), empty)),
                        M.Pair(
                            M.Pair(M.Char("4"), M.Pair(M.Char("four"), empty)),
                            M.Pair(
                                M.Pair(M.Char("5"), M.Pair(M.Char("five"), empty)),
                                M.Pair(
                                    M.Pair(M.Char("6"), M.Pair(M.Char("six"), empty)),
                                    M.Pair(
                                        M.Pair(
                                            M.Char("7"),
                                            M.Pair(M.Char("seven"), empty),
                                        ),
                                        M.Pair(
                                            M.Pair(
                                                M.Char("8"),
                                                M.Pair(M.Char("eight"), empty),
                                            ),
                                            M.Pair(
                                                M.Pair(
                                                    M.Char("9"),
                                                    M.Pair(M.Char("nine"), empty),
                                                ),
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
        )

        self.result = M.Pair(
            templates,
            M.Pair(words, M.Pair(digit_words, empty)),
        )
        super().__init__(inputs=empty, results=self.result)

    def __call__(self):
        return self.result


class CorrespondenceResolveWord(M.Edge):
    """Resolve one Surface word to its Nat through the word parse laws."""

    def __init__(self, word_entries, surface_term):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        scan_text = "0"
        self.result = M.EmptyList
        remaining = word_entries
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining)()
                law = M.Head(M.Tail(M.Tail(entry)())())()
                value = CorrespondenceApply(law, surface_term)()
                if M.IdentityCompare(value, M.EmptyList)() is M.false_value:
                    self.result = value
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(word_entries, M.Pair(surface_term, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class MeaningEvaluate(M.Edge):
    """Evaluate a parsed Meaning to a Nat through the arithmetic edges."""

    def __init__(self, meaning_term, word_entries, registry):
        self.word_entries = word_entries
        evaluated = self._eval(meaning_term, registry, "0")
        self.result = evaluated
        super().__init__(
            inputs=M.Pair(
                meaning_term,
                M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def _eval(self, term, registry, depth_text):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        if GMPEqualText(depth_text, cap_text)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        next_depth = GMPSuccText(depth_text)()
        if M.IsPair(term)() is M.truth_value:
            label = M.Head(term)()
            if M.TermEqual(label, Lmod.MeaningLabel)() is M.truth_value:
                return self._eval(M.Head(M.Tail(term)())(), registry, next_depth)
            if M.TermEqual(label, Lmod.SurfaceLabel)() is M.truth_value:
                value = CorrespondenceResolveWord(self.word_entries, term)()
                if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                    chain = M.Head(M.Tail(term)())()
                    if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
                        if M.IdentityCompare(
                            M.Tail(chain)(),
                            M.EmptyList,
                        )() is M.truth_value:
                            element = M.Head(chain)()
                            if M.IsNat(element, registry)() is M.truth_value:
                                value = element
                            else:
                                # Group reduction splices whole terms into the
                                # chain, so a one-element Surface may hold a
                                # Sqrt rather than a number word. Evaluate it
                                # as the term it is.
                                if M.IsPair(element)() is M.truth_value:
                                    return self._eval(
                                        element,
                                        registry,
                                        next_depth,
                                    )
                return M.Pair(value, M.Pair(registry, M.EmptyList))
            arguments = M.Tail(term)()
            is_add = M.TermEqual(label, M.ExprAddLabel)()
            is_mul = M.TermEqual(label, M.ExprMulLabel)()
            if M.OrAtom(is_add, is_mul)() is M.truth_value:
                left_pair = self._eval(M.Head(arguments)(), registry, next_depth)
                left_value = M.Head(left_pair)()
                registry = M.Head(M.Tail(left_pair)())()
                if M.IdentityCompare(left_value, M.EmptyList)() is M.truth_value:
                    return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
                right_pair = self._eval(
                    M.Head(M.Tail(arguments)())(),
                    registry,
                    next_depth,
                )
                right_value = M.Head(right_pair)()
                registry = M.Head(M.Tail(right_pair)())()
                if M.IdentityCompare(right_value, M.EmptyList)() is M.truth_value:
                    return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
                left_nat = M.IsNat(left_value, registry)()
                right_nat = M.IsNat(right_value, registry)()
                if M.AndAtom(left_nat, right_nat)() is M.false_value:
                    # A root has no Nat value and neither does a product
                    # or sum built on one. The operands are still perfectly
                    # good terms, so the expression is too: hand back the
                    # symbolic term, exactly as the Sqrt case below does.
                    return M.Pair(
                        M.Pair(
                            label,
                            M.Pair(
                                left_value,
                                M.Pair(right_value, M.EmptyList),
                            ),
                        ),
                        M.Pair(registry, M.EmptyList),
                    )
                if M.IdentityCompare(is_add, M.truth_value)() is M.truth_value:
                    return M.Add(left_value, right_value, registry)()
                return M.Multiply(left_value, right_value, registry)()
            if M.TermEqual(label, M.SqrtLabel)() is M.truth_value:
                # A root has no Nat value, but it is a perfectly good term and
                # the prover takes it as one. Evaluate the radicand so a
                # nested root loses its Surface wrappers at every depth, then
                # hand back the Sqrt term itself.
                inner_pair = self._eval(
                    M.Head(arguments)(),
                    registry,
                    next_depth,
                )
                inner_value = M.Head(inner_pair)()
                registry = M.Head(M.Tail(inner_pair)())()
                if M.IdentityCompare(
                    inner_value,
                    M.EmptyList,
                )() is M.truth_value:
                    return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
                return M.Pair(
                    M.Pair(
                        M.SqrtLabel,
                        M.Pair(inner_value, M.EmptyList),
                    ),
                    M.Pair(registry, M.EmptyList),
                )
            return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))
        if M.IsNat(term, registry)() is M.truth_value:
            return M.Pair(term, M.Pair(registry, M.EmptyList))
        return M.Pair(M.EmptyList, M.Pair(registry, M.EmptyList))

    def __call__(self):
        return self.result


class RenderNatSurface(M.Edge):
    """Render a Nat as a Surface of number words, one word per digit."""

    def __init__(self, nat, digit_words, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        rep = M.NatRepOf(nat, registry)()
        if M.IdentityCompare(rep, M.EmptyList)() is M.false_value:
            digits = GMPRepDigitList(rep)()
            reversed_words = M.EmptyList
            complete = M.truth_value
            scan_text = "0"
            remaining_digits = digits
            while M.IdentityCompare(remaining_digits, M.EmptyList)() is M.false_value:
                if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                    complete = M.false_value
                    remaining_digits = M.EmptyList
                else:
                    scan_text = GMPSuccText(scan_text)()
                    digit = M.Head(remaining_digits)()
                    word = M.EmptyList
                    lookup_text = "0"
                    remaining_words = digit_words
                    while M.IdentityCompare(
                        remaining_words,
                        M.EmptyList,
                    )() is M.false_value:
                        if GMPEqualText(lookup_text, cap_text)() is M.truth_value:
                            remaining_words = M.EmptyList
                        else:
                            lookup_text = GMPSuccText(lookup_text)()
                            association = M.Head(remaining_words)()
                            if M.Compare(
                                M.Head(association)(),
                                digit,
                            )() is M.truth_value:
                                word = M.Head(M.Tail(association)())()
                                remaining_words = M.EmptyList
                            else:
                                remaining_words = M.Tail(remaining_words)()
                    if M.IdentityCompare(word, M.EmptyList)() is M.truth_value:
                        complete = M.false_value
                        remaining_digits = M.EmptyList
                    else:
                        reversed_words = M.Pair(word, reversed_words)
                        remaining_digits = M.Tail(remaining_digits)()
            if M.IdentityCompare(complete, M.truth_value)() is M.truth_value:
                self.result = Surface(M.Reverse(reversed_words)())()
        super().__init__(
            inputs=M.Pair(
                nat,
                M.Pair(digit_words, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ConstructorSignature(M.Edge):
    """A constructor, the word that names it, and how many arguments it takes.

    Pair(SignatureLabel, Pair(word, Pair(constructor, Pair(arity, Empty)))).

    The formal notation "mul ( a , b )" was one hand-written template per
    constructor, so a constructor the packs knew about had no formal form
    until someone added a branch. A signature is that form as data:
    FormalProductions below turns it into a production of the grammar, so
    every constructor a pack emits is writable the moment it is loaded and
    nothing in the parser mentions it.
    """

    def __init__(self, word, constructor, arity):
        self.result = M.Pair(
            Lmod.SignatureLabel,
            M.Pair(
                word,
                M.Pair(constructor, M.Pair(arity, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                word,
                M.Pair(constructor, M.Pair(arity, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SignatureWord(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(signature)())()
        super().__init__(
            inputs=M.Pair(signature, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class SignatureConstructor(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(M.Tail(signature)())())()
        super().__init__(
            inputs=M.Pair(signature, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class SignatureArity(M.Edge):
    def __init__(self, signature):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(signature)())())())()
        super().__init__(
            inputs=M.Pair(signature, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


# The chart's own limits. A pass that adds nothing is the fixed point;
# CHART_PASS_CAP is what stops a grammar whose productions keep feeding
# each other, so a cycle in the productions is a bounded failure rather
# than a host recursion error.
CHART_PASS_CAP = M.GMPRep("50")

# The category the formal notation is written in. An argument is the
# same category as the whole application, which is the entire reason
# nesting needs no machinery.
CHART_TERM_CATEGORY = M.Char("term")

# The notation's function words. These carry no meaning of their own and
# no branch of their own: they appear in productions exactly the way
# "mul" does, as words to be matched in order.
FORMAL_OPEN_WORD = M.Char("(")
FORMAL_CLOSE_WORD = M.Char(")")
FORMAL_SEPARATOR_WORD = M.Char(",")


class WordSymbol(M.Edge):
    """A production symbol matching one literal word of the input.

    Pair(WordSymbolLabel, Pair(word, EmptyList)).
    """

    def __init__(self, word):
        self.result = M.Pair(
            Lmod.WordSymbolLabel,
            M.Pair(word, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(word, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class CategorySymbol(M.Edge):
    """A production symbol matching a constituent of one category.

    Pair(CategorySymbolLabel, Pair(category, Pair(variable, EmptyList))).
    The variable is the slot the matched constituent's term binds to, so
    the production's template can name what the symbol found.
    """

    def __init__(self, category, variable):
        self.result = M.Pair(
            Lmod.CategorySymbolLabel,
            M.Pair(category, M.Pair(variable, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(category, M.Pair(variable, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Production(M.Edge):
    """One grammar rule: a category, a symbol sequence, and a template.

    Pair(ProductionLabel, Pair(category, Pair(symbols, Pair(template,
    EmptyList)))). The symbols say what stands next to what; the
    template says what the result term is, built by the same Instantiate
    every law's right-hand side is built by. A grammar is a chain of
    these and nothing else -- there is no production that is a branch in
    the parser instead.
    """

    def __init__(self, category, symbols, template):
        self.result = M.Pair(
            Lmod.ProductionLabel,
            M.Pair(
                category,
                M.Pair(symbols, M.Pair(template, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                category,
                M.Pair(symbols, M.Pair(template, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ProductionCategory(M.Edge):
    def __init__(self, production):
        self.result = M.Head(M.Tail(production)())()
        super().__init__(
            inputs=M.Pair(production, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ProductionSymbols(M.Edge):
    def __init__(self, production):
        self.result = M.Head(M.Tail(M.Tail(production)())())()
        super().__init__(
            inputs=M.Pair(production, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ProductionTemplate(M.Edge):
    def __init__(self, production):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(production)())())())()
        super().__init__(
            inputs=M.Pair(production, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class Constituent(M.Edge):
    """One reading of one span: a category, a term, and the two cells.

    Pair(ConstituentLabel, Pair(category, Pair(term, Pair(start,
    Pair(after, EmptyList))))). `start` is the cell it begins at and
    `after` the cell it ends before, so a constituent is a fact about a
    span rather than about a position in a scan.
    """

    def __init__(self, category, term, start, after):
        self.result = M.Pair(
            Lmod.ConstituentLabel,
            M.Pair(
                category,
                M.Pair(term, M.Pair(start, M.Pair(after, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                category,
                M.Pair(term, M.Pair(start, M.Pair(after, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ConstituentCategory(M.Edge):
    def __init__(self, constituent):
        self.result = M.Head(M.Tail(constituent)())()
        super().__init__(
            inputs=M.Pair(constituent, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ConstituentTerm(M.Edge):
    def __init__(self, constituent):
        self.result = M.Head(M.Tail(M.Tail(constituent)())())()
        super().__init__(
            inputs=M.Pair(constituent, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ConstituentStart(M.Edge):
    def __init__(self, constituent):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(constituent)())())())()
        super().__init__(
            inputs=M.Pair(constituent, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ConstituentAfter(M.Edge):
    def __init__(self, constituent):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(constituent)())())())(),
        )()
        super().__init__(
            inputs=M.Pair(constituent, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ChartCells(M.Edge):
    """The cells of a word chain: every position a span may start or end at.

    A cell is a position, named by the suffix of the chain that begins
    there -- the chain itself is the first cell and EmptyList the cell
    past the last word. Two spans are the same span exactly when their
    cells are the same objects, so nothing counts positions and nothing
    compares counts.
    """

    def __init__(self, chain):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_cells = M.EmptyList
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                reversed_cells = M.Pair(remaining, reversed_cells)
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(M.Pair(M.EmptyList, reversed_cells))()
        super().__init__(
            inputs=M.Pair(chain, M.EmptyList), results=self.result,
        )

    def __call__(self):
        return self.result


class ChartSymbolMatches(M.Edge):
    """Every way one symbol sequence can be matched starting at one cell.

    Returns a chain of Pair(bindings, Pair(after, EmptyList)): the
    bindings the category symbols made and the cell the match ended
    before. Every way, not the first way -- two readings of the same
    words are two matches here, and choosing between them is not this
    edge's business.

    A word symbol consumes one input word; a category symbol consumes a
    constituent already in the chart and hands its term to the template
    through the symbol's variable. The recursion is over the symbol
    chain, which shrinks at every step, so it ends when the symbols run
    out.
    """

    def __init__(self, symbols, cell, constituents):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        if M.IdentityCompare(symbols, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(
                M.Pair(M.EmptyList, M.Pair(cell, M.EmptyList)),
                M.EmptyList,
            )
        else:
            symbol = M.Head(symbols)()
            rest_symbols = M.Tail(symbols)()
            if M.TermEqual(
                M.Head(symbol)(),
                Lmod.WordSymbolLabel,
            )() is M.truth_value:
                if M.IdentityCompare(cell, M.EmptyList)() is M.false_value:
                    if M.Compare(
                        M.Head(cell)(),
                        M.Head(M.Tail(symbol)())(),
                    )() is M.truth_value:
                        self.result = ChartSymbolMatches(
                            rest_symbols,
                            M.Tail(cell)(),
                            constituents,
                        )()
            elif M.TermEqual(
                M.Head(symbol)(),
                Lmod.CategorySymbolLabel,
            )() is M.truth_value:
                category = M.Head(M.Tail(symbol)())()
                variable = M.Head(M.Tail(M.Tail(symbol)())())()
                reversed_matches = M.EmptyList
                scan_text = "0"
                remaining = constituents
                while M.IdentityCompare(
                    remaining, M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                        remaining = M.EmptyList
                    else:
                        scan_text = GMPSuccText(scan_text)()
                        constituent = M.Head(remaining)()
                        if M.IdentityCompare(
                            ConstituentStart(constituent)(), cell,
                        )() is M.truth_value:
                            if M.Compare(
                                ConstituentCategory(constituent)(), category,
                            )() is M.truth_value:
                                tail_matches = ChartSymbolMatches(
                                    rest_symbols,
                                    ConstituentAfter(constituent)(),
                                    constituents,
                                )()
                                tail_scan_text = "0"
                                remaining_tail = tail_matches
                                while M.IdentityCompare(
                                    remaining_tail, M.EmptyList,
                                )() is M.false_value:
                                    if GMPEqualText(
                                        tail_scan_text, cap_text,
                                    )() is M.truth_value:
                                        remaining_tail = M.EmptyList
                                    else:
                                        tail_scan_text = GMPSuccText(
                                            tail_scan_text,
                                        )()
                                        tail_match = M.Head(remaining_tail)()
                                        reversed_matches = M.Pair(
                                            M.Pair(
                                                M.Pair(
                                                    M.Pair(
                                                        variable,
                                                        M.Pair(
                                                            ConstituentTerm(
                                                                constituent,
                                                            )(),
                                                            M.EmptyList,
                                                        ),
                                                    ),
                                                    M.Head(tail_match)(),
                                                ),
                                                M.Tail(tail_match)(),
                                            ),
                                            reversed_matches,
                                        )
                                        remaining_tail = M.Tail(
                                            remaining_tail,
                                        )()
                        remaining = M.Tail(remaining)()
                self.result = M.Reverse(reversed_matches)()
        super().__init__(
            inputs=M.Pair(
                symbols,
                M.Pair(cell, M.Pair(constituents, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ChartAddConstituent(M.Edge):
    """Add a constituent unless one exactly like it is already present.

    Two constituents are the same when they are the same category over
    the same two cells carrying structurally equal terms. Two readings
    of one span with different terms are both kept: ambiguity is a fact
    about the sentence, and collapsing it here would be the parser
    choosing on the reader's behalf.

    Returns Pair(constituents, Pair(added, EmptyList)).
    """

    def __init__(self, constituents, constituent):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        category = ConstituentCategory(constituent)()
        term = ConstituentTerm(constituent)()
        start = ConstituentStart(constituent)()
        after = ConstituentAfter(constituent)()
        self.capped = M.false_value
        present = M.false_value
        scan_text = "0"
        remaining = constituents
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                self.capped = M.truth_value
                present = M.truth_value
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                other = M.Head(remaining)()
                if M.IdentityCompare(
                    ConstituentStart(other)(), start,
                )() is M.truth_value:
                    if M.IdentityCompare(
                        ConstituentAfter(other)(), after,
                    )() is M.truth_value:
                        if M.Compare(
                            ConstituentCategory(other)(), category,
                        )() is M.truth_value:
                            if M.TermEqual(
                                ConstituentTerm(other)(), term,
                            )() is M.truth_value:
                                present = M.truth_value
                if M.IdentityCompare(present, M.truth_value)() is M.truth_value:
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        self.added = M.false_value
        grown = constituents
        if M.IdentityCompare(present, M.false_value)() is M.truth_value:
            grown = M.Pair(constituent, constituents)
            self.added = M.truth_value
        self.result = M.Pair(grown, M.Pair(self.added, M.EmptyList))
        super().__init__(
            inputs=M.Pair(constituents, M.Pair(constituent, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ChartSaturate(M.Edge):
    """Close a set of constituents under a set of productions.

    One pass tries every production at every cell against every
    constituent the chart already holds; a pass that adds nothing is the
    fixed point. This loop knows nothing about what any production says.
    Brackets, separators, argument order and arity live in the
    productions; the loop is the same loop whatever they are, which is
    the whole difference between a grammar and a parser written by hand.

    `saturated` is truth only when a pass added nothing before the pass
    cap ran out and no addition hit the chart's own size cap, so an
    unfinished parse is visible rather than silently partial.
    """

    def __init__(self, productions, seeds, cells):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        pass_cap_text = M.GMPRepText(CHART_PASS_CAP)()
        constituents = seeds
        self.saturated = M.false_value
        self.capped = M.false_value
        pass_text = "0"
        growing = M.truth_value
        while M.IdentityCompare(growing, M.truth_value)() is M.truth_value:
            if GMPEqualText(pass_text, pass_cap_text)() is M.truth_value:
                growing = M.false_value
            else:
                pass_text = GMPSuccText(pass_text)()
                growing = M.false_value
                production_scan_text = "0"
                remaining_productions = productions
                while M.IdentityCompare(
                    remaining_productions, M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(
                        production_scan_text, cap_text,
                    )() is M.truth_value:
                        remaining_productions = M.EmptyList
                    else:
                        production_scan_text = GMPSuccText(
                            production_scan_text,
                        )()
                        production = M.Head(remaining_productions)()
                        category = ProductionCategory(production)()
                        symbols = ProductionSymbols(production)()
                        template = ProductionTemplate(production)()
                        cell_scan_text = "0"
                        remaining_cells = cells
                        while M.IdentityCompare(
                            remaining_cells, M.EmptyList,
                        )() is M.false_value:
                            if GMPEqualText(
                                cell_scan_text, cap_text,
                            )() is M.truth_value:
                                remaining_cells = M.EmptyList
                            else:
                                cell_scan_text = GMPSuccText(cell_scan_text)()
                                cell = M.Head(remaining_cells)()
                                matches = ChartSymbolMatches(
                                    symbols, cell, constituents,
                                )()
                                match_scan_text = "0"
                                remaining_matches = matches
                                while M.IdentityCompare(
                                    remaining_matches, M.EmptyList,
                                )() is M.false_value:
                                    if GMPEqualText(
                                        match_scan_text, cap_text,
                                    )() is M.truth_value:
                                        remaining_matches = M.EmptyList
                                    else:
                                        match_scan_text = GMPSuccText(
                                            match_scan_text,
                                        )()
                                        match = M.Head(remaining_matches)()
                                        after = M.Head(M.Tail(match)())()
                                        if M.IdentityCompare(
                                            after, cell,
                                        )() is M.false_value:
                                            addition = ChartAddConstituent(
                                                constituents,
                                                Constituent(
                                                    category,
                                                    M.Head(
                                                        M.Instantiate(
                                                            template,
                                                            M.Head(match)(),
                                                        )(),
                                                    )(),
                                                    cell,
                                                    after,
                                                )(),
                                            )
                                            constituents = M.Head(addition())()
                                            if M.IdentityCompare(
                                                addition.added,
                                                M.truth_value,
                                            )() is M.truth_value:
                                                growing = M.truth_value
                                            if M.IdentityCompare(
                                                addition.capped,
                                                M.truth_value,
                                            )() is M.truth_value:
                                                self.capped = M.truth_value
                                        remaining_matches = M.Tail(
                                            remaining_matches,
                                        )()
                                remaining_cells = M.Tail(remaining_cells)()
                        remaining_productions = M.Tail(remaining_productions)()
                if M.IdentityCompare(growing, M.false_value)() is M.truth_value:
                    if M.IdentityCompare(
                        self.capped, M.false_value,
                    )() is M.truth_value:
                        self.saturated = M.truth_value
        self.result = constituents
        super().__init__(
            inputs=M.Pair(
                productions,
                M.Pair(seeds, M.Pair(cells, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ChartSpanningTerms(M.Edge):
    """Every term of one category whose constituent covers the whole chain."""

    def __init__(self, constituents, category, chain):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_terms = M.EmptyList
        scan_text = "0"
        remaining = constituents
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                constituent = M.Head(remaining)()
                if M.IdentityCompare(
                    ConstituentStart(constituent)(), chain,
                )() is M.truth_value:
                    if M.IdentityCompare(
                        ConstituentAfter(constituent)(), M.EmptyList,
                    )() is M.truth_value:
                        if M.Compare(
                            ConstituentCategory(constituent)(), category,
                        )() is M.truth_value:
                            reversed_terms = M.Pair(
                                ConstituentTerm(constituent)(),
                                reversed_terms,
                            )
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_terms)()
        super().__init__(
            inputs=M.Pair(
                constituents,
                M.Pair(category, M.Pair(chain, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ChartSeedConstituents(M.Edge):
    """What the words of a chain mean standing on their own.

    One constituent per word the vocabulary resolves, and one per run of
    adjacent digit words, since "six four" is one number spanning two
    cells and no production says so. This is the only place a word's own
    meaning is consulted; everything above it is productions.
    """

    def __init__(self, word_entries, digit_words, category, chain):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_seeds = M.EmptyList
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                word = M.Head(remaining)()
                value = CorrespondenceResolveWord(
                    word_entries,
                    Surface(M.Pair(word, M.EmptyList))(),
                )()
                if M.IdentityCompare(value, M.EmptyList)() is M.false_value:
                    reversed_seeds = M.Pair(
                        Constituent(
                            category, value, remaining, M.Tail(remaining)(),
                        )(),
                        reversed_seeds,
                    )
                reversed_run = M.EmptyList
                run_scan_text = "0"
                run_remaining = remaining
                while M.IdentityCompare(
                    run_remaining, M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(
                        run_scan_text, cap_text,
                    )() is M.truth_value:
                        run_remaining = M.EmptyList
                    else:
                        run_scan_text = GMPSuccText(run_scan_text)()
                        digit = SurfaceDigitOfWord(
                            M.Head(run_remaining)(), digit_words,
                        )()
                        if M.IdentityCompare(
                            digit, M.EmptyList,
                        )() is M.truth_value:
                            run_remaining = M.EmptyList
                        else:
                            reversed_run = M.Pair(
                                M.Head(run_remaining)(), reversed_run,
                            )
                            run_remaining = M.Tail(run_remaining)()
                            run_value = SurfaceDigitRunValue(
                                M.Reverse(reversed_run)(), digit_words,
                            )()
                            if M.IdentityCompare(
                                run_value, M.EmptyList,
                            )() is M.false_value:
                                reversed_seeds = M.Pair(
                                    Constituent(
                                        category,
                                        run_value,
                                        remaining,
                                        run_remaining,
                                    )(),
                                    reversed_seeds,
                                )
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_seeds)()
        super().__init__(
            inputs=M.Pair(
                word_entries,
                M.Pair(
                    digit_words,
                    M.Pair(category, M.Pair(chain, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormalProductions(M.Edge):
    """The formal notation as productions, generated from the signatures.

    "mul ( a , b )" used to be a scan for an open bracket, a depth
    counter, a split on commas at depth zero and an arity check after
    the fact -- one grammar written as control flow. A signature is now
    one production: the word, an open bracket, an argument category per
    argument with separators between them, a close bracket, and a
    template putting the matched arguments under the constructor.

    Arity is not checked, it is matched: a production with two argument
    slots does not match one argument. Nesting is not implemented at
    all: an argument is the same category the whole application is, so
    the chart has already read the inner application by the time the
    outer one asks for it. Brackets and commas are words in a
    production, the same as "mul" is.

    Returns Pair(productions, Pair(registry, EmptyList)).
    """

    def __init__(self, signatures, category, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_productions = M.EmptyList
        scan_text = "0"
        remaining = signatures
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                signature = M.Head(remaining)()
                reversed_symbols = M.Pair(
                    WordSymbol(FORMAL_OPEN_WORD)(),
                    M.Pair(
                        WordSymbol(SignatureWord(signature)())(),
                        M.EmptyList,
                    ),
                )
                reversed_variables = M.EmptyList
                separated = M.false_value
                arity_scan_text = "0"
                remaining_arity = SignatureArity(signature)()
                while M.NatEq(
                    remaining_arity, M.Zero, registry,
                )() is M.false_value:
                    if GMPEqualText(
                        arity_scan_text, cap_text,
                    )() is M.truth_value:
                        remaining_arity = M.Zero
                    else:
                        arity_scan_text = GMPSuccText(arity_scan_text)()
                        if M.IdentityCompare(
                            separated, M.truth_value,
                        )() is M.truth_value:
                            reversed_symbols = M.Pair(
                                WordSymbol(FORMAL_SEPARATOR_WORD)(),
                                reversed_symbols,
                            )
                        variable = M.Pair(
                            M.VarTag, M.Pair(M.Atom(), M.EmptyList),
                        )
                        reversed_symbols = M.Pair(
                            CategorySymbol(category, variable)(),
                            reversed_symbols,
                        )
                        reversed_variables = M.Pair(
                            variable, reversed_variables,
                        )
                        separated = M.truth_value
                        stepped = M.NatPred(remaining_arity, registry)()
                        remaining_arity = M.Head(stepped)()
                        registry = M.Head(M.Tail(stepped)())()
                reversed_symbols = M.Pair(
                    WordSymbol(FORMAL_CLOSE_WORD)(), reversed_symbols,
                )
                reversed_productions = M.Pair(
                    Production(
                        category,
                        M.Reverse(reversed_symbols)(),
                        M.Pair(
                            SignatureConstructor(signature)(),
                            M.Reverse(reversed_variables)(),
                        ),
                    )(),
                    reversed_productions,
                )
                remaining = M.Tail(remaining)()
        self.result = M.Pair(
            M.Reverse(reversed_productions)(),
            M.Pair(registry, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(
                signatures,
                M.Pair(category, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FormalTermReadings(M.Edge):
    """Read "name ( arg , arg )" by chart, as the first client of the chart.

    The formal notation gets no reader of its own. Its signatures become
    productions, the vocabulary seeds the words, and the same saturation
    that any other grammar runs through produces the terms. Takes a
    Surface, as every other reader in this file does, and returns every
    term spanning the whole of it, so an ambiguous notation reports both
    readings instead of one of them.

    Returns Pair(terms, Pair(registry, EmptyList)). An empty chain of
    terms means the words do not spell an application: a word with no
    signature, a wrong count of arguments and a missing bracket are all
    the same answer here, which is that no production spans the input.
    """

    def __init__(self, signatures, vocabulary, surface_term, registry):
        word_entries = M.Head(M.Tail(vocabulary)())()
        digit_words = M.Head(M.Tail(M.Tail(vocabulary)())())()
        chain = M.Head(M.Tail(surface_term)())()
        generated = FormalProductions(
            signatures, CHART_TERM_CATEGORY, registry,
        )()
        registry = M.Head(M.Tail(generated)())()
        chart = ChartSaturate(
            M.Head(generated)(),
            ChartSeedConstituents(
                word_entries, digit_words, CHART_TERM_CATEGORY, chain,
            )(),
            ChartCells(chain)(),
        )
        self.saturated = chart.saturated
        self.result = M.Pair(
            ChartSpanningTerms(chart(), CHART_TERM_CATEGORY, chain)(),
            M.Pair(registry, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(
                signatures,
                M.Pair(
                    vocabulary,
                    M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ConverseInterpretations(M.Edge):
    """Every structurally distinct Meaning for one group-free Surface chain.

    All template laws run within the scan cap; every distinct Meaning is
    retained as Pair(meaning, Pair(law, EmptyList)). Nothing collapses to
    the first match. Word and spliced-Nat readings apply when no template
    matches.
    """

    def __init__(self, vocabulary, surface_term, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        templates = M.Head(vocabulary)()
        word_entries = M.Head(M.Tail(vocabulary)())()

        reversed_interpretations = M.EmptyList
        scan_text = "0"
        remaining = templates
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                law = M.Head(remaining)()
                candidate = CorrespondenceApply(law, surface_term)()
                if M.IdentityCompare(candidate, M.EmptyList)() is M.false_value:
                    duplicate = M.false_value
                    check_text = "0"
                    checking = reversed_interpretations
                    while M.IdentityCompare(checking, M.EmptyList)() is M.false_value:
                        if GMPEqualText(check_text, cap_text)() is M.truth_value:
                            checking = M.EmptyList
                        else:
                            check_text = GMPSuccText(check_text)()
                            if M.Compare(
                                M.Head(M.Head(checking)())(),
                                candidate,
                            )() is M.truth_value:
                                duplicate = M.truth_value
                                checking = M.EmptyList
                            else:
                                checking = M.Tail(checking)()
                    if M.IdentityCompare(duplicate, M.false_value)() is M.truth_value:
                        reversed_interpretations = M.Pair(
                            M.Pair(candidate, M.Pair(law, M.EmptyList)),
                            reversed_interpretations,
                        )
                remaining = M.Tail(remaining)()

        if M.IdentityCompare(
            reversed_interpretations,
            M.EmptyList,
        )() is M.truth_value:
            direct = CorrespondenceResolveWord(word_entries, surface_term)()
            if M.IdentityCompare(direct, M.EmptyList)() is M.truth_value:
                chain = M.Head(M.Tail(surface_term)())()
                if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(
                        M.Tail(chain)(),
                        M.EmptyList,
                    )() is M.truth_value:
                        element = M.Head(chain)()
                        if M.IsNat(element, registry)() is M.truth_value:
                            direct = element
            if M.IdentityCompare(direct, M.EmptyList)() is M.false_value:
                reversed_interpretations = M.Pair(
                    M.Pair(Meaning(direct)(), M.Pair(M.EmptyList, M.EmptyList)),
                    reversed_interpretations,
                )

        self.result = M.Pair(
            M.Reverse(reversed_interpretations)(),
            M.Pair(registry, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ConverseValue(M.Edge):
    """Evaluate one group-free Surface chain to its single agreed Nat value.

    Every interpretation is enumerated and evaluated; the value returns
    only when all evaluable interpretations agree. Zero interpretations or
    conflicting values return EmptyList explicitly — never a silent pick.
    """

    def __init__(self, vocabulary, surface_term, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        word_entries = M.Head(M.Tail(vocabulary)())()
        interpreted = ConverseInterpretations(vocabulary, surface_term, registry)()
        interpretations = M.Head(interpreted)()
        registry = M.Head(M.Tail(interpreted)())()

        value = M.EmptyList
        conflicted = M.false_value
        scan_text = "0"
        remaining = interpretations
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                meaning = M.Head(M.Head(remaining)())()
                evaluated = MeaningEvaluate(meaning, word_entries, registry)()
                candidate = M.Head(evaluated)()
                registry = M.Head(M.Tail(evaluated)())()
                if M.IdentityCompare(candidate, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                        value = candidate
                    elif M.NatEq(value, candidate, registry)() is M.false_value:
                        conflicted = M.truth_value
                        remaining = M.EmptyList
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    remaining = M.Tail(remaining)()

        if M.IdentityCompare(conflicted, M.truth_value)() is M.truth_value:
            value = M.EmptyList
        self.result = M.Pair(value, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceOperatorWords(M.Edge):
    """The infix words the vocabulary's binary templates are keyed on."""

    def __init__(self, vocabulary):
        self.result = M.Pair(
            M.Char("plus"),
            M.Pair(
                M.Char("times"),
                M.Pair(M.Char("minus"), M.EmptyList),
            ),
        )
        super().__init__(
            inputs=M.Pair(vocabulary, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceChainHasWord(M.Edge):
    """Membership by word value rather than object identity."""

    def __init__(self, chain, word):
        self.result = M.false_value
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(remaining)(), word)() is M.truth_value:
                self.result = M.truth_value
                remaining = M.EmptyList
            else:
                remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(chain, M.Pair(word, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceFoldChainedOperator(M.Edge):
    """Rewrite `a OP b OP c` as `( a OP b ) OP c`, left-associating.

    The correspondence laws are strictly binary: "two times two" has one
    interpretation and "two times two times two" has none, which surfaced
    as "no correspondence law for that shape" -- true, but only because
    nothing had grouped the chain. Parenthesising by hand already worked,
    so this supplies the grouping the reader would otherwise have to type.

    One fold per call, leftmost first; the caller re-reduces, so a longer
    chain folds one step at a time. A chain with fewer than two operators
    is returned unchanged, and the operator words must be the same one --
    mixing "plus" and "times" would impose a precedence this has no
    grounds to choose.
    """

    def __init__(self, chain, operator_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        first_index_text = ""
        second_index_text = ""
        first_word = M.EmptyList
        seen_text = "0"
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                word = M.Head(remaining)()
                # Compare, not ChainHasTerm: M.Char does not intern, so a
                # word read from a sentence is a different object from the
                # same word in the operator list, and identity would miss it.
                if SurfaceChainHasWord(operator_words, word)() is M.truth_value:
                    if M.IdentityCompare(first_word, M.EmptyList)() is M.truth_value:
                        first_word = word
                        first_index_text = scan_text
                    elif M.Compare(word, first_word)() is M.truth_value:
                        if GMPEqualText(second_index_text, "")() is M.truth_value:
                            second_index_text = scan_text
                scan_text = GMPSuccText(scan_text)()
                remaining = M.Tail(remaining)()
        self.result = chain
        if GMPEqualText(second_index_text, "")() is M.false_value:
            # The group opens at the operand immediately before the first
            # operator, not at the start of the sentence: "is two times two
            # times two" must fold to "is ( two times two ) times two", or
            # the leading words are swallowed into a group that cannot be
            # evaluated -- which is how a question became a group failure.
            open_index_text = "0"
            if GMPLessText("0", first_index_text)() is M.truth_value:
                open_index_text = GMPSubText(first_index_text, "1")()
            reversed_output = M.EmptyList
            cursor_text = "0"
            remaining = chain
            while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                if GMPEqualText(cursor_text, open_index_text)() is M.truth_value:
                    reversed_output = M.Pair(M.Char("("), reversed_output)
                if GMPEqualText(cursor_text, second_index_text)() is M.truth_value:
                    reversed_output = M.Pair(M.Char(")"), reversed_output)
                    while M.IdentityCompare(
                        remaining,
                        M.EmptyList,
                    )() is M.false_value:
                        reversed_output = M.Pair(M.Head(remaining)(), reversed_output)
                        remaining = M.Tail(remaining)()
                else:
                    reversed_output = M.Pair(M.Head(remaining)(), reversed_output)
                    cursor_text = GMPSuccText(cursor_text)()
                    remaining = M.Tail(remaining)()
            self.result = Reverse(reversed_output)()
        super().__init__(
            inputs=M.Pair(chain, M.Pair(operator_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceDigitRunValue(M.Edge):
    """A chain that is entirely digit words, read as one Nat.

    Only a chain of two or more digit words qualifies: a single word is
    already handled by the ordinary correspondence laws, and any non-digit
    word means this is a sentence rather than a numeral.
    """

    def __init__(self, chain, digit_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        digits_text = ""
        counted_text = "0"
        all_digits = M.truth_value
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                all_digits = M.false_value
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                digit = SurfaceDigitOfWord(M.Head(remaining)(), digit_words)()
                if M.IdentityCompare(digit, M.EmptyList)() is M.truth_value:
                    all_digits = M.false_value
                    remaining = M.EmptyList
                else:
                    digits_text = digits_text + digit()
                    counted_text = GMPSuccText(counted_text)()
                    remaining = M.Tail(remaining)()
        self.result = M.EmptyList
        if M.IdentityCompare(all_digits, M.truth_value)() is M.truth_value:
            if GMPLessText("1", counted_text)() is M.truth_value:
                self.result = MineNatFromGMPRep(M.GMPRep(digits_text))()
        super().__init__(
            inputs=M.Pair(chain, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceJoinDigitWords(M.Edge):
    """Fold runs of adjacent digit words into single multi-digit numerals.

    The tokenizer rewrites each digit of a numeral separately, so "64"
    arrives as "six four". No correspondence law relates two number words
    standing side by side, so every multi-digit numeral was unevaluable --
    "sqrt(64)" and "(64)" alike -- and the failure was reported as
    unbalanced parentheses. This is the inverse of RenderNatSurface, which
    already turns a Nat into a chain of digit words.

    A run of one word is left exactly as it was, so single digits and every
    documented spelled-out form are untouched. Only runs of two or more are
    joined, and the join is the concatenation of their digit characters.
    """

    def __init__(self, chain, digit_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_output = M.EmptyList
        pending_text = ""
        pending_words = M.EmptyList
        scan_text = "0"
        remaining = chain
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                word = M.Head(remaining)()
                digit = SurfaceDigitOfWord(word, digit_words)()
                if M.IdentityCompare(digit, M.EmptyList)() is M.false_value:
                    pending_text = pending_text + digit()
                    pending_words = M.Pair(word, pending_words)
                else:
                    reversed_output = SurfaceFlushDigits(
                        reversed_output,
                        pending_text,
                        pending_words,
                    )()
                    pending_text = ""
                    pending_words = M.EmptyList
                    reversed_output = M.Pair(word, reversed_output)
                remaining = M.Tail(remaining)()
        reversed_output = SurfaceFlushDigits(
            reversed_output,
            pending_text,
            pending_words,
        )()
        self.result = Reverse(reversed_output)()
        super().__init__(
            inputs=M.Pair(chain, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceDigitOfWord(M.Edge):
    """The digit character a number word names, or EmptyList."""

    def __init__(self, word, digit_words):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = M.EmptyList
        scan_text = "0"
        remaining = digit_words
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                entry = M.Head(remaining)()
                if M.Compare(M.Head(M.Tail(entry)())(), word)() is M.truth_value:
                    self.result = M.Head(entry)()
                    remaining = M.EmptyList
                else:
                    remaining = M.Tail(remaining)()
        super().__init__(
            inputs=M.Pair(word, M.Pair(digit_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceFlushDigits(M.Edge):
    """Emit a pending digit run: joined when several, verbatim when one."""

    def __init__(self, reversed_output, pending_text, pending_words):
        self.result = reversed_output
        if M.IdentityCompare(pending_words, M.EmptyList)() is M.false_value:
            single = M.IdentityCompare(M.Tail(pending_words)(), M.EmptyList)()
            if M.IdentityCompare(single, M.truth_value)() is M.truth_value:
                self.result = M.Pair(M.Head(pending_words)(), reversed_output)
            else:
                self.result = M.Pair(M.Char(pending_text), reversed_output)
        super().__init__(
            inputs=M.Pair(reversed_output, M.Pair(pending_words, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceReduceGroups(M.Edge):
    """Reduce innermost parenthesis groups to their evaluated Nat values.

    Each pass finds one innermost balanced group, evaluates its group-free
    chain through ConverseValue, and splices the Nat back into the sentence.
    Unbalanced or unparseable groups return EmptyList explicitly.
    """

    def __init__(self, vocabulary, surface_term, registry):
        self.unevaluated = M.EmptyList
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        open_symbol = M.Char("(")
        close_symbol = M.Char(")")
        chain = M.Head(M.Tail(surface_term)())()
        # The correspondence laws are binary, so an unparenthesized chain
        # like "two times two times two" has no interpretation at all.
        # Left-associate it into the grouping the reader would otherwise
        # have to type; the loop below then reduces those groups normally.
        operator_words = SurfaceOperatorWords(vocabulary)()
        fold_text = "0"
        folding = M.truth_value
        while M.IdentityCompare(folding, M.truth_value)() is M.truth_value:
            folding = M.false_value
            if GMPLessText(fold_text, cap_text)() is M.truth_value:
                fold_text = GMPSuccText(fold_text)()
                folded = SurfaceFoldChainedOperator(chain, operator_words)()
                if M.TermEqual(folded, chain)() is M.false_value:
                    chain = folded
                    folding = M.truth_value
        failed = M.false_value
        # Distinguish a bracket-matching failure from a group whose contents
        # simply could not be evaluated. Both used to surface as "your
        # parentheses do not balance", which is false whenever the brackets
        # are fine and merely their contents are not understood.
        value_failed = M.false_value
        pass_text = "0"
        reducing = M.truth_value
        while M.IdentityCompare(reducing, M.truth_value)() is M.truth_value:
            if GMPEqualText(pass_text, cap_text)() is M.truth_value:
                failed = M.truth_value
                reducing = M.false_value
            else:
                pass_text = GMPSuccText(pass_text)()
                reversed_before = M.EmptyList
                reversed_inner = M.EmptyList
                open_atom = M.EmptyList
                seen_open = M.false_value
                reduced_once = M.false_value
                scan_text = "0"
                remaining = chain
                while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                        failed = M.truth_value
                        remaining = M.EmptyList
                    else:
                        scan_text = GMPSuccText(scan_text)()
                        element = M.Head(remaining)()
                        if M.Compare(element, open_symbol)() is M.truth_value:
                            if M.IdentityCompare(
                                seen_open,
                                M.truth_value,
                            )() is M.truth_value:
                                reversed_before = M.Pair(
                                    open_atom,
                                    reversed_before,
                                )
                                flush = M.Reverse(reversed_inner)()
                                while M.IdentityCompare(
                                    flush,
                                    M.EmptyList,
                                )() is M.false_value:
                                    reversed_before = M.Pair(
                                        M.Head(flush)(),
                                        reversed_before,
                                    )
                                    flush = M.Tail(flush)()
                            open_atom = element
                            seen_open = M.truth_value
                            reversed_inner = M.EmptyList
                            remaining = M.Tail(remaining)()
                        elif M.Compare(element, close_symbol)() is M.truth_value:
                            if M.IdentityCompare(
                                seen_open,
                                M.false_value,
                            )() is M.truth_value:
                                failed = M.truth_value
                                remaining = M.EmptyList
                            else:
                                inner_chain = M.Reverse(reversed_inner)()
                                has_comma = M.false_value
                                comma_scan = inner_chain
                                while M.IdentityCompare(
                                    comma_scan,
                                    M.EmptyList,
                                )() is M.false_value:
                                    if M.Compare(
                                        M.Head(comma_scan)(),
                                        M.Char(","),
                                    )() is M.truth_value:
                                        has_comma = M.truth_value
                                        comma_scan = M.EmptyList
                                    else:
                                        comma_scan = M.Tail(comma_scan)()
                                if M.IdentityCompare(
                                    has_comma,
                                    M.truth_value,
                                )() is M.truth_value:
                                    # A comma marks an argument list, not a
                                    # grouping: "( three , sqrt seven )" is
                                    # the tail of "mul ( ... )" and only
                                    # means anything WITH its function word
                                    # and brackets. Reducing the whole group
                                    # destroyed the shape the formal
                                    # template matches. Instead, reduce each
                                    # comma-separated ARGUMENT to a single
                                    # term and keep the brackets and commas,
                                    # so "mul ( three , sqrt seven )"
                                    # becomes "mul ( three , <Sqrt(7)> )"
                                    # and the binary template binds cleanly.
                                    changed = M.false_value
                                    arg_failed = M.false_value
                                    reversed_args = M.EmptyList
                                    reversed_segment = M.EmptyList
                                    seg_scan = inner_chain
                                    while M.IdentityCompare(
                                        seg_scan,
                                        M.EmptyList,
                                    )() is M.false_value:
                                        piece = M.Head(seg_scan)()
                                        if M.Compare(
                                            piece,
                                            M.Char(","),
                                        )() is M.truth_value:
                                            reversed_args = M.Pair(
                                                M.Reverse(reversed_segment)(),
                                                reversed_args,
                                            )
                                            reversed_segment = M.EmptyList
                                        else:
                                            reversed_segment = M.Pair(
                                                piece,
                                                reversed_segment,
                                            )
                                        seg_scan = M.Tail(seg_scan)()
                                    reversed_args = M.Pair(
                                        M.Reverse(reversed_segment)(),
                                        reversed_args,
                                    )
                                    segments = M.Reverse(reversed_args)()
                                    reversed_rebuilt_args = M.EmptyList
                                    seg_walk = segments
                                    while M.IdentityCompare(
                                        seg_walk,
                                        M.EmptyList,
                                    )() is M.false_value:
                                        segment = M.Head(seg_walk)()
                                        single = M.false_value
                                        if M.IdentityCompare(
                                            segment,
                                            M.EmptyList,
                                        )() is M.false_value:
                                            if M.IdentityCompare(
                                                M.Tail(segment)(),
                                                M.EmptyList,
                                            )() is M.truth_value:
                                                single = M.truth_value
                                        if M.IdentityCompare(
                                            single,
                                            M.truth_value,
                                        )() is M.truth_value:
                                            reversed_rebuilt_args = M.Pair(
                                                segment,
                                                reversed_rebuilt_args,
                                            )
                                        else:
                                            valued = ConverseValue(
                                                vocabulary,
                                                Surface(segment)(),
                                                registry,
                                            )()
                                            seg_value = M.Head(valued)()
                                            registry = M.Head(
                                                M.Tail(valued)(),
                                            )()
                                            if M.IdentityCompare(
                                                seg_value,
                                                M.EmptyList,
                                            )() is M.truth_value:
                                                seg_readings = ConverseInterpretations(
                                                    vocabulary,
                                                    Surface(segment)(),
                                                    registry,
                                                )()
                                                seg_list = M.Head(
                                                    seg_readings,
                                                )()
                                                registry = M.Head(
                                                    M.Tail(seg_readings)(),
                                                )()
                                                if M.IdentityCompare(
                                                    seg_list,
                                                    M.EmptyList,
                                                )() is M.false_value:
                                                    if M.IdentityCompare(
                                                        M.Tail(seg_list)(),
                                                        M.EmptyList,
                                                    )() is M.truth_value:
                                                        seg_meaning = M.Head(
                                                            M.Head(
                                                                seg_list,
                                                            )(),
                                                        )()
                                                        seg_value = M.Head(
                                                            M.Tail(
                                                                seg_meaning,
                                                            )(),
                                                        )()
                                            if M.IdentityCompare(
                                                seg_value,
                                                M.EmptyList,
                                            )() is M.truth_value:
                                                arg_failed = M.truth_value
                                            else:
                                                reversed_rebuilt_args = M.Pair(
                                                    M.Pair(
                                                        seg_value,
                                                        M.EmptyList,
                                                    ),
                                                    reversed_rebuilt_args,
                                                )
                                                changed = M.truth_value
                                        seg_walk = M.Tail(seg_walk)()
                                    if M.IdentityCompare(
                                        arg_failed,
                                        M.false_value,
                                    )() is M.truth_value:
                                        if M.IdentityCompare(
                                            changed,
                                            M.truth_value,
                                        )() is M.truth_value:
                                            rebuilt_args = M.Reverse(
                                                reversed_rebuilt_args,
                                            )()
                                            rebuilt = M.Tail(remaining)()
                                            rebuilt = M.Pair(element, rebuilt)
                                            reversed_group = M.EmptyList
                                            arg_walk = rebuilt_args
                                            first_arg = M.truth_value
                                            while M.IdentityCompare(
                                                arg_walk,
                                                M.EmptyList,
                                            )() is M.false_value:
                                                if M.IdentityCompare(
                                                    first_arg,
                                                    M.false_value,
                                                )() is M.truth_value:
                                                    reversed_group = M.Pair(
                                                        M.Char(","),
                                                        reversed_group,
                                                    )
                                                first_arg = M.false_value
                                                seg_flush = M.Head(arg_walk)()
                                                while M.IdentityCompare(
                                                    seg_flush,
                                                    M.EmptyList,
                                                )() is M.false_value:
                                                    reversed_group = M.Pair(
                                                        M.Head(seg_flush)(),
                                                        reversed_group,
                                                    )
                                                    seg_flush = M.Tail(
                                                        seg_flush,
                                                    )()
                                                arg_walk = M.Tail(arg_walk)()
                                            group_walk = reversed_group
                                            while M.IdentityCompare(
                                                group_walk,
                                                M.EmptyList,
                                            )() is M.false_value:
                                                rebuilt = M.Pair(
                                                    M.Head(group_walk)(),
                                                    rebuilt,
                                                )
                                                group_walk = M.Tail(
                                                    group_walk,
                                                )()
                                            rebuilt = M.Pair(
                                                open_atom,
                                                rebuilt,
                                            )
                                            spliced = reversed_before
                                            while M.IdentityCompare(
                                                spliced,
                                                M.EmptyList,
                                            )() is M.false_value:
                                                rebuilt = M.Pair(
                                                    M.Head(spliced)(),
                                                    rebuilt,
                                                )
                                                spliced = M.Tail(spliced)()
                                            chain = rebuilt
                                            reduced_once = M.truth_value
                                            remaining = M.EmptyList
                                        else:
                                            # All arguments already single:
                                            # nothing to do here. Flush the
                                            # group into 'before' untouched
                                            # so the scan can continue past
                                            # it without reporting failure.
                                            reversed_before = M.Pair(
                                                open_atom,
                                                reversed_before,
                                            )
                                            flush = inner_chain
                                            while M.IdentityCompare(
                                                flush,
                                                M.EmptyList,
                                            )() is M.false_value:
                                                reversed_before = M.Pair(
                                                    M.Head(flush)(),
                                                    reversed_before,
                                                )
                                                flush = M.Tail(flush)()
                                            reversed_before = M.Pair(
                                                element,
                                                reversed_before,
                                            )
                                            seen_open = M.false_value
                                            reversed_inner = M.EmptyList
                                            remaining = M.Tail(remaining)()
                                    else:
                                        failed = M.truth_value
                                        value_failed = M.truth_value
                                        self.unevaluated = Surface(
                                            inner_chain,
                                        )()
                                        remaining = M.EmptyList
                                elif M.IdentityCompare(
                                    inner_chain,
                                    M.EmptyList,
                                )() is M.truth_value:
                                    failed = M.truth_value
                                    remaining = M.EmptyList
                                else:
                                    valued = ConverseValue(
                                        vocabulary,
                                        Surface(inner_chain)(),
                                        registry,
                                    )()
                                    value = M.Head(valued)()
                                    registry = M.Head(M.Tail(valued)())()
                                    if M.IdentityCompare(
                                        value,
                                        M.EmptyList,
                                    )() is M.truth_value:
                                        # "64" reaches here as "six four":
                                        # the tokenizer splits every digit and
                                        # no law relates two number words side
                                        # by side. A run of digit words has a
                                        # direct reading as one numeral.
                                        value = SurfaceDigitRunValue(
                                            inner_chain,
                                            M.Head(
                                                M.Tail(M.Tail(vocabulary)())(),
                                            )(),
                                        )()
                                    if M.IdentityCompare(
                                        value,
                                        M.EmptyList,
                                    )() is M.truth_value:
                                        # A group need not denote a number.
                                        # "sqrt ( three )" has no value, but it
                                        # does have a meaning, and the sentence
                                        # around it wants a term in that slot.
                                        # Splice the term so nesting reads the
                                        # same as any other radicand.
                                        inner_readings = ConverseInterpretations(
                                            vocabulary,
                                            Surface(inner_chain)(),
                                            registry,
                                        )()
                                        inner_list = M.Head(inner_readings)()
                                        registry = M.Head(
                                            M.Tail(inner_readings)(),
                                        )()
                                        if M.IdentityCompare(
                                            inner_list,
                                            M.EmptyList,
                                        )() is M.false_value:
                                            if M.IdentityCompare(
                                                M.Tail(inner_list)(),
                                                M.EmptyList,
                                            )() is M.truth_value:
                                                only = M.Head(inner_list)()
                                                reading = M.Head(only)()
                                                value = M.Head(
                                                    M.Tail(reading)(),
                                                )()
                                    if M.IdentityCompare(
                                        value,
                                        M.EmptyList,
                                    )() is M.truth_value:
                                        failed = M.truth_value
                                        value_failed = M.truth_value
                                        self.unevaluated = Surface(inner_chain)()
                                        remaining = M.EmptyList
                                    else:
                                        rebuilt = M.Tail(remaining)()
                                        spliced = M.Pair(value, reversed_before)
                                        while M.IdentityCompare(
                                            spliced,
                                            M.EmptyList,
                                        )() is M.false_value:
                                            rebuilt = M.Pair(
                                                M.Head(spliced)(),
                                                rebuilt,
                                            )
                                            spliced = M.Tail(spliced)()
                                        chain = rebuilt
                                        reduced_once = M.truth_value
                                        remaining = M.EmptyList
                        else:
                            if M.IdentityCompare(
                                seen_open,
                                M.truth_value,
                            )() is M.truth_value:
                                reversed_inner = M.Pair(element, reversed_inner)
                            else:
                                reversed_before = M.Pair(element, reversed_before)
                            remaining = M.Tail(remaining)()
                if M.IdentityCompare(failed, M.truth_value)() is M.truth_value:
                    reducing = M.false_value
                elif M.IdentityCompare(reduced_once, M.false_value)() is M.truth_value:
                    if M.IdentityCompare(seen_open, M.truth_value)() is M.truth_value:
                        failed = M.truth_value
                    reducing = M.false_value

        reduced_surface = M.EmptyList
        if M.IdentityCompare(failed, M.false_value)() is M.truth_value:
            reduced_surface = Surface(chain)()
        self.value_failed = value_failed
        self.result = M.Pair(reduced_surface, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Understood(M.Edge):
    """A successful interpretation: surface, meaning, law, and answer."""

    def __init__(self, surface_term, meaning_term, law, answer_surface):
        self.result = M.Pair(
            Lmod.UnderstoodLabel,
            M.Pair(
                surface_term,
                M.Pair(
                    meaning_term,
                    M.Pair(law, M.Pair(answer_surface, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                surface_term,
                M.Pair(
                    meaning_term,
                    M.Pair(law, M.Pair(answer_surface, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class NotUnderstood(M.Edge):
    """An explicit interpretation failure carrying its structured reason."""

    def __init__(self, surface_term, reason):
        self.result = M.Pair(
            Lmod.NotUnderstoodLabel,
            M.Pair(surface_term, M.Pair(reason, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(surface_term, M.Pair(reason, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class AmbiguousResult(M.Edge):
    """Distinct disagreeing interpretations retained, none chosen."""

    def __init__(self, surface_term, interpretations):
        self.result = M.Pair(
            Lmod.AmbiguousLabel,
            M.Pair(surface_term, M.Pair(interpretations, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(surface_term, M.Pair(interpretations, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceUnknownWords(M.Edge):
    """Words of a Surface chain with no entry, template mention, or grouping."""

    def __init__(self, vocabulary, surface_term, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        templates = M.Head(vocabulary)()
        word_entries = M.Head(M.Tail(vocabulary)())()

        reversed_known = M.EmptyList
        entry_scan_text = "0"
        remaining_entries = word_entries
        while M.IdentityCompare(remaining_entries, M.EmptyList)() is M.false_value:
            if GMPEqualText(entry_scan_text, cap_text)() is M.truth_value:
                remaining_entries = M.EmptyList
            else:
                entry_scan_text = GMPSuccText(entry_scan_text)()
                reversed_known = M.Pair(
                    M.Head(M.Head(remaining_entries)())(),
                    reversed_known,
                )
                remaining_entries = M.Tail(remaining_entries)()
        template_scan_text = "0"
        remaining_templates = templates
        while M.IdentityCompare(remaining_templates, M.EmptyList)() is M.false_value:
            if GMPEqualText(template_scan_text, cap_text)() is M.truth_value:
                remaining_templates = M.EmptyList
            else:
                template_scan_text = GMPSuccText(template_scan_text)()
                law = M.Head(remaining_templates)()
                left_nodes = GraphNodes(LawLeft(law)())()
                if M.IdentityCompare(left_nodes, M.EmptyList)() is M.false_value:
                    pattern = M.Head(left_nodes)()
                    if M.IsPair(pattern)() is M.truth_value:
                        chain = M.Head(M.Tail(pattern)())()
                        word_scan_text = "0"
                        while M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
                            if GMPEqualText(
                                word_scan_text,
                                cap_text,
                            )() is M.truth_value:
                                chain = M.EmptyList
                            else:
                                word_scan_text = GMPSuccText(word_scan_text)()
                                element = M.Head(chain)()
                                if P.IsVarPattern(element)() is M.false_value:
                                    reversed_known = M.Pair(element, reversed_known)
                                chain = M.Tail(chain)()
                remaining_templates = M.Tail(remaining_templates)()
        known = M.Pair(
            M.Char("("),
            M.Pair(M.Char(")"), M.Reverse(reversed_known)()),
        )

        reversed_unknown = M.EmptyList
        scan_text = "0"
        remaining = M.Head(M.Tail(surface_term)())()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                word = M.Head(remaining)()
                if M.IsNat(word, registry)() is M.false_value:
                    found = M.false_value
                    check_text = "0"
                    checking = known
                    while M.IdentityCompare(checking, M.EmptyList)() is M.false_value:
                        if GMPEqualText(check_text, cap_text)() is M.truth_value:
                            checking = M.EmptyList
                        else:
                            check_text = GMPSuccText(check_text)()
                            if M.Compare(M.Head(checking)(), word)() is M.truth_value:
                                found = M.truth_value
                                checking = M.EmptyList
                            else:
                                checking = M.Tail(checking)()
                    if M.IdentityCompare(found, M.false_value)() is M.truth_value:
                        reversed_unknown = M.Pair(word, reversed_unknown)
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_unknown)()
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class Converse(M.Edge):
    """Interpret a Surface sentence and return an explicit result term.

    Parenthesis groups reduce innermost-first through the same laws before
    the sentence templates run. Returns Pair(result_term, Pair(registry,
    EmptyList)) where result_term is Understood, NotUnderstood with a
    structured reason, or Ambiguous with every disagreeing interpretation.
    Nothing is guessed and no interpretation is silently discarded.
    """

    def __init__(self, vocabulary, surface_term, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        word_entries = M.Head(M.Tail(vocabulary)())()
        digit_words = M.Head(M.Tail(M.Tail(vocabulary)())())()

        unknown_words = SurfaceUnknownWords(vocabulary, surface_term, registry)()
        outcome = M.EmptyList
        if M.IdentityCompare(unknown_words, M.EmptyList)() is M.false_value:
            outcome = NotUnderstood(
                surface_term,
                M.Pair(
                    Lmod.ReasonUnknownWordLabel,
                    M.Pair(unknown_words, M.EmptyList),
                ),
            )()

        if M.IdentityCompare(outcome, M.EmptyList)() is M.truth_value:
            direct = ConverseInterpretations(vocabulary, surface_term, registry)()
            direct_interpretations = M.Head(direct)()
            registry = M.Head(M.Tail(direct)())()
            reduced_surface = surface_term
            group_value_failed = M.false_value
            unevaluated_group = M.EmptyList
            if M.IdentityCompare(
                direct_interpretations,
                M.EmptyList,
            )() is M.truth_value:
                reducer = SurfaceReduceGroups(
                    vocabulary,
                    surface_term,
                    registry,
                )
                reduced = reducer()
                reduced_surface = M.Head(reduced)()
                registry = M.Head(M.Tail(reduced)())()
                group_value_failed = reducer.value_failed
                unevaluated_group = reducer.unevaluated
            if M.IdentityCompare(reduced_surface, M.EmptyList)() is M.truth_value:
                # Balanced brackets whose contents did not evaluate are a
                # different failure from brackets that do not match, and
                # saying the wrong one sends the reader hunting a typo that
                # is not there.
                group_reason = M.Pair(
                    Lmod.ReasonGroupLabel,
                    M.Pair(surface_term, M.EmptyList),
                )
                if M.IdentityCompare(
                    group_value_failed,
                    M.truth_value,
                )() is M.truth_value:
                    group_reason = M.Pair(
                        Lmod.ReasonGroupValueLabel,
                        M.Pair(unevaluated_group, M.EmptyList),
                    )
                outcome = NotUnderstood(surface_term, group_reason)()
            else:
                interpretations = direct_interpretations
                if M.IdentityCompare(
                    interpretations,
                    M.EmptyList,
                )() is M.truth_value:
                    interpreted = ConverseInterpretations(
                        vocabulary,
                        reduced_surface,
                        registry,
                    )()
                    interpretations = M.Head(interpreted)()
                    registry = M.Head(M.Tail(interpreted)())()
                if M.IdentityCompare(
                    interpretations,
                    M.EmptyList,
                )() is M.truth_value:
                    proposition = ConversePropositionInterpretations(
                        vocabulary,
                        reduced_surface,
                        registry,
                    )()
                    interpretations = M.Head(proposition)()
                    registry = M.Head(M.Tail(proposition)())()
                if M.IdentityCompare(
                    interpretations,
                    M.EmptyList,
                )() is M.truth_value:
                    outcome = NotUnderstood(
                        surface_term,
                        M.Pair(
                            Lmod.ReasonNoCorrespondenceLabel,
                            M.Pair(reduced_surface, M.EmptyList),
                        ),
                    )()
                if M.IdentityCompare(outcome, M.EmptyList)() is M.truth_value:
                    task_scan_text = "0"
                    remaining_tasks = interpretations
                    while M.IdentityCompare(
                        remaining_tasks,
                        M.EmptyList,
                    )() is M.false_value:
                        if GMPEqualText(
                            task_scan_text,
                            cap_text,
                        )() is M.truth_value:
                            remaining_tasks = M.EmptyList
                        else:
                            task_scan_text = GMPSuccText(task_scan_text)()
                            interpretation = M.Head(remaining_tasks)()
                            meaning = M.Head(interpretation)()
                            body = M.Head(M.Tail(meaning)())()
                            if M.IsPair(body)() is M.truth_value:
                                if M.TermEqual(
                                    M.Head(body)(),
                                    Lmod.TaskLabel,
                                )() is M.truth_value:
                                    outcome = Understood(
                                        surface_term,
                                        meaning,
                                        M.Head(M.Tail(interpretation)())(),
                                        M.EmptyList,
                                    )()
                                    remaining_tasks = M.EmptyList
                                elif M.TermEqual(
                                    M.Head(body)(),
                                    M.IsRealLabel,
                                )() is M.truth_value:
                                    outcome = Understood(
                                        surface_term,
                                        meaning,
                                        M.Head(M.Tail(interpretation)())(),
                                        M.EmptyList,
                                    )()
                                    remaining_tasks = M.EmptyList
                            if M.IdentityCompare(
                                remaining_tasks,
                                M.EmptyList,
                            )() is M.false_value:
                                remaining_tasks = M.Tail(remaining_tasks)()
                if M.IdentityCompare(outcome, M.EmptyList)() is M.truth_value:
                    value = M.EmptyList
                    chosen = M.EmptyList
                    conflicted = M.false_value
                    reversed_valued = M.EmptyList
                    scan_text = "0"
                    remaining = interpretations
                    while M.IdentityCompare(
                        remaining,
                        M.EmptyList,
                    )() is M.false_value:
                        if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                            remaining = M.EmptyList
                        else:
                            scan_text = GMPSuccText(scan_text)()
                            interpretation = M.Head(remaining)()
                            meaning = M.Head(interpretation)()
                            evaluated = PropositionEvaluate(
                                meaning,
                                word_entries,
                                registry,
                            )()
                            candidate = M.Head(evaluated)()
                            registry = M.Head(M.Tail(evaluated)())()
                            if M.IdentityCompare(
                                candidate,
                                M.EmptyList,
                            )() is M.truth_value:
                                evaluated = MeaningEvaluate(
                                    meaning,
                                    word_entries,
                                    registry,
                                )()
                                candidate = M.Head(evaluated)()
                                registry = M.Head(M.Tail(evaluated)())()
                            if M.IdentityCompare(
                                candidate,
                                M.EmptyList,
                            )() is M.false_value:
                                reversed_valued = M.Pair(
                                    interpretation,
                                    reversed_valued,
                                )
                                if M.IdentityCompare(
                                    value,
                                    M.EmptyList,
                                )() is M.truth_value:
                                    value = candidate
                                    chosen = interpretation
                                elif M.IdentityCompare(
                                    value,
                                    M.truth_value,
                                )() is M.truth_value:
                                    if M.IdentityCompare(
                                        value,
                                        candidate,
                                    )() is M.false_value:
                                        conflicted = M.truth_value
                                elif M.IdentityCompare(
                                    value,
                                    M.false_value,
                                )() is M.truth_value:
                                    if M.IdentityCompare(
                                        value,
                                        candidate,
                                    )() is M.false_value:
                                        conflicted = M.truth_value
                                elif M.NatEq(
                                    value,
                                    candidate,
                                    registry,
                                )() is M.false_value:
                                    conflicted = M.truth_value
                            remaining = M.Tail(remaining)()
                    if M.IdentityCompare(conflicted, M.truth_value)() is M.truth_value:
                        outcome = AmbiguousResult(
                            surface_term,
                            M.Reverse(reversed_valued)(),
                        )()
                    elif M.IdentityCompare(value, M.EmptyList)() is M.truth_value:
                        outcome = NotUnderstood(
                            surface_term,
                            M.Pair(
                                Lmod.ReasonEvaluationLabel,
                                M.Pair(interpretations, M.EmptyList),
                            ),
                        )()
                    else:
                        answer = M.EmptyList
                        if M.IdentityCompare(
                            value,
                            M.truth_value,
                        )() is M.truth_value:
                            answer = RenderPropositionSurface(value)()
                        elif M.IdentityCompare(
                            value,
                            M.false_value,
                        )() is M.truth_value:
                            answer = RenderPropositionSurface(value)()
                        else:
                            answer = RenderNatSurface(value, digit_words, registry)()
                        outcome = Understood(
                            surface_term,
                            M.Head(chosen)(),
                            M.Head(M.Tail(chosen)())(),
                            answer,
                        )()

        self.result = M.Pair(outcome, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SurfaceEqualSplit(M.Edge):
    """Split a Surface chain at its first `equal to` marker."""

    def __init__(self, chain):
        self.result = M.EmptyList
        if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
            element = M.Head(chain)()
            remaining = M.Tail(chain)()
            if M.Compare(element, M.Char("equal"))() is M.truth_value:
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    if M.Compare(M.Head(remaining)(), M.Char("to"))() is M.truth_value:
                        right = M.Tail(remaining)()
                        if M.IdentityCompare(right, M.EmptyList)() is M.false_value:
                            self.result = M.Pair(
                                M.EmptyList,
                                M.Pair(right, M.EmptyList),
                            )
            else:
                split = SurfaceEqualSplit(remaining)()
                if M.IdentityCompare(split, M.EmptyList)() is M.false_value:
                    left = M.Head(split)()
                    right = M.Head(M.Tail(split)())()
                    self.result = M.Pair(
                        M.Pair(element, left),
                        M.Pair(right, M.EmptyList),
                    )
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ConversePropositionInterpretations(M.Edge):
    """Interpret an equality question with independently parsed clauses."""

    def __init__(self, vocabulary, surface_term, registry):
        self.result = M.EmptyList
        chain = M.Head(M.Tail(surface_term)())()
        if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
            if M.Compare(M.Head(chain)(), M.Char("is"))() is M.truth_value:
                split = SurfaceEqualSplit(M.Tail(chain)())()
                if M.IdentityCompare(split, M.EmptyList)() is M.false_value:
                    left_chain = M.Head(split)()
                    right_chain = M.Head(M.Tail(split)())()
                    left = Converse(
                        vocabulary,
                        Surface(left_chain)(),
                        registry,
                    )()
                    left_outcome = M.Head(left)()
                    registry = M.Head(M.Tail(left)())()
                    right = Converse(
                        vocabulary,
                        Surface(right_chain)(),
                        registry,
                    )()
                    right_outcome = M.Head(right)()
                    registry = M.Head(M.Tail(right)())()
                    if M.IdentityCompare(
                        M.Head(left_outcome)(),
                        Lmod.UnderstoodLabel,
                    )() is M.truth_value:
                        if M.IdentityCompare(
                            M.Head(right_outcome)(),
                            Lmod.UnderstoodLabel,
                        )() is M.truth_value:
                            left_meaning = M.Head(
                                M.Tail(M.Tail(left_outcome)())(),
                            )()
                            right_meaning = M.Head(
                                M.Tail(M.Tail(right_outcome)())(),
                            )()
                            meaning = Meaning(
                                M.Pair(
                                    Lmod.EqualLabel,
                                    M.Pair(
                                        left_meaning,
                                        M.Pair(right_meaning, M.EmptyList),
                                    ),
                                ),
                            )()
                            self.result = M.Pair(
                                M.Pair(
                                    meaning,
                                    M.Pair(M.EmptyList, M.EmptyList),
                                ),
                                M.EmptyList,
                            )
        self.registry = registry
        super().__init__(
            inputs=M.Pair(
                vocabulary,
                M.Pair(surface_term, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return M.Pair(self.result, M.Pair(self.registry, M.EmptyList))


class PropositionEvaluate(M.Edge):
    """Evaluate a proposition Meaning to the machine truth atoms.

    Even/Odd propositions evaluate through WitnessSearchEven: the verdict
    arrives with first-class evidence (Confirmed with a Witness, or
    Refuted with a reason), retained on self.evidence for the caller."""

    def __init__(self, meaning_term, word_entries, registry):
        value = M.EmptyList
        self.evidence = M.EmptyList
        body = meaning_term
        if M.IsPair(body)() is M.truth_value:
            if M.TermEqual(M.Head(body)(), Lmod.MeaningLabel)() is M.truth_value:
                body = M.Head(M.Tail(body)())()
        if M.IsPair(body)() is M.truth_value:
            is_even_prop = M.TermEqual(M.Head(body)(), Lmod.EvenPropLabel)()
            is_odd_prop = M.TermEqual(M.Head(body)(), Lmod.OddPropLabel)()
            if M.OrAtom(is_even_prop, is_odd_prop)() is M.truth_value:
                evaluated = MeaningEvaluate(
                    M.Head(M.Tail(body)())(),
                    word_entries,
                    registry,
                )()
                subject = M.Head(evaluated)()
                registry = M.Head(M.Tail(evaluated)())()
                if M.IdentityCompare(subject, M.EmptyList)() is M.false_value:
                    searched = WitnessSearchEven(
                        body,
                        subject,
                        registry,
                        odd=is_odd_prop,
                    )()
                    value = M.Head(searched)()
                    self.evidence = M.Head(M.Tail(searched)())()
                    registry = M.Head(M.Tail(M.Tail(searched)())())()
                self.result = M.Pair(value, M.Pair(registry, M.EmptyList))
                super().__init__(
                    inputs=M.Pair(
                        meaning_term,
                        M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
                    ),
                    results=self.result,
                )
                return
            if M.TermEqual(M.Head(body)(), Lmod.EqualLabel)() is M.truth_value:
                arguments = M.Tail(body)()
                left = MeaningEvaluate(
                    M.Head(arguments)(),
                    word_entries,
                    registry,
                )()
                left_value = M.Head(left)()
                registry = M.Head(M.Tail(left)())()
                right = MeaningEvaluate(
                    M.Head(M.Tail(arguments)())(),
                    word_entries,
                    registry,
                )()
                right_value = M.Head(right)()
                registry = M.Head(M.Tail(right)())()
                if M.IdentityCompare(left_value, M.EmptyList)() is M.false_value:
                    if M.IdentityCompare(right_value, M.EmptyList)() is M.false_value:
                        value = M.NatEq(left_value, right_value, registry)()
        self.result = M.Pair(value, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                meaning_term,
                M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RenderPropositionSurface(M.Edge):
    """Render a machine truth atom as the answer Surface `yes` or `no`."""

    def __init__(self, value):
        self.result = M.EmptyList
        if M.IdentityCompare(value, M.truth_value)() is M.truth_value:
            self.result = Surface(M.Pair(M.Char("yes"), M.EmptyList))()
        elif M.IdentityCompare(value, M.false_value)() is M.truth_value:
            self.result = Surface(M.Pair(M.Char("no"), M.EmptyList))()
        super().__init__(inputs=M.Pair(value, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


CORRESPONDENCE_INDUCTION_CAP = M.GMPRep("10")


class CorrespondenceExample(M.Edge):
    """One recorded Surface/Meaning pair with its evidence tag."""

    def __init__(self, surface_term, meaning_term, evidence):
        self.result = M.Pair(
            Lmod.CorrespondenceExampleLabel,
            M.Pair(
                surface_term,
                M.Pair(meaning_term, M.Pair(evidence, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                surface_term,
                M.Pair(meaning_term, M.Pair(evidence, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CorrespondenceExampleSurface(M.Edge):
    def __init__(self, example):
        self.result = M.Head(M.Tail(example)())()
        super().__init__(inputs=M.Pair(example, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CorrespondenceExampleMeaning(M.Edge):
    def __init__(self, example):
        self.result = M.Head(M.Tail(M.Tail(example)())())()
        super().__init__(inputs=M.Pair(example, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class CorrespondenceExampleEvidence(M.Edge):
    def __init__(self, example):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(example)())())())()
        super().__init__(inputs=M.Pair(example, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AntiUnifyCorrespondence(M.Edge):
    """Bounded structural anti-unification of two correspondence examples.

    Differing aligned surface words become shared variables; differing
    aligned meaning subterms must resolve to the same word differences and
    become Surface holes over the same variables. Returns Pair(parse_law,
    Pair(render_law, EmptyList)) or EmptyList when no lawful shared
    generalization exists. No repair, no guessing.
    """

    def __init__(self, example_a, example_b, word_entries):
        self.word_entries = word_entries
        self.cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        self.result = self._induce(example_a, example_b)
        super().__init__(
            inputs=M.Pair(
                example_a,
                M.Pair(example_b, M.Pair(word_entries, M.EmptyList)),
            ),
            results=self.result,
        )

    def _induce(self, example_a, example_b):
        surface_a = CorrespondenceExampleSurface(example_a)()
        surface_b = CorrespondenceExampleSurface(example_b)()
        chain_a = M.Head(M.Tail(surface_a)())()
        chain_b = M.Head(M.Tail(surface_b)())()

        reversed_general = M.EmptyList
        diffs = M.EmptyList
        var_index_text = "0"
        scan_text = "0"
        while M.IdentityCompare(chain_a, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, self.cap_text)() is M.truth_value:
                return M.EmptyList
            scan_text = GMPSuccText(scan_text)()
            if M.IdentityCompare(chain_b, M.EmptyList)() is M.truth_value:
                return M.EmptyList
            word_a = M.Head(chain_a)()
            word_b = M.Head(chain_b)()
            if M.Compare(word_a, word_b)() is M.truth_value:
                reversed_general = M.Pair(word_a, reversed_general)
            else:
                variable = M.EmptyList
                check_text = "0"
                remaining_diffs = diffs
                while M.IdentityCompare(
                    remaining_diffs,
                    M.EmptyList,
                )() is M.false_value:
                    if GMPEqualText(check_text, self.cap_text)() is M.truth_value:
                        remaining_diffs = M.EmptyList
                    else:
                        check_text = GMPSuccText(check_text)()
                        diff = M.Head(remaining_diffs)()
                        same_a = M.Compare(M.Head(diff)(), word_a)()
                        same_b = M.Compare(M.Head(M.Tail(diff)())(), word_b)()
                        if M.AndAtom(same_a, same_b)() is M.truth_value:
                            variable = M.Head(M.Tail(M.Tail(diff)())())()
                            remaining_diffs = M.EmptyList
                        else:
                            remaining_diffs = M.Tail(remaining_diffs)()
                if M.IdentityCompare(variable, M.EmptyList)() is M.truth_value:
                    variable = M.Pair(
                        M.VarTag,
                        M.Pair(M.Char("?g" + var_index_text), M.EmptyList),
                    )
                    var_index_text = GMPSuccText(var_index_text)()
                    diffs = M.Pair(
                        M.Pair(
                            word_a,
                            M.Pair(word_b, M.Pair(variable, M.EmptyList)),
                        ),
                        diffs,
                    )
                reversed_general = M.Pair(variable, reversed_general)
            chain_a = M.Tail(chain_a)()
            chain_b = M.Tail(chain_b)()
        if M.IdentityCompare(chain_b, M.EmptyList)() is M.false_value:
            return M.EmptyList
        if M.IdentityCompare(diffs, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        meaning_a = CorrespondenceExampleMeaning(example_a)()
        meaning_b = CorrespondenceExampleMeaning(example_b)()
        generalized = self._general(
            M.Head(M.Tail(meaning_a)())(),
            M.Head(M.Tail(meaning_b)())(),
            diffs,
            "0",
        )
        if M.IdentityCompare(M.Head(generalized)(), M.false_value)() is M.truth_value:
            return M.EmptyList

        general_surface = Surface(M.Reverse(reversed_general)())()
        general_meaning = Meaning(M.Tail(generalized)())()
        parse_law = CompileRuleToLaw(P.Rule(general_surface, general_meaning))()
        render_law = CompileRuleToLaw(P.Rule(general_meaning, general_surface))()
        if M.IdentityCompare(parse_law, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(render_law, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Pair(parse_law, M.Pair(render_law, M.EmptyList))

    def _general(self, term_a, term_b, diffs, depth_text):
        if GMPEqualText(depth_text, self.cap_text)() is M.truth_value:
            return M.Pair(M.false_value, M.EmptyList)
        next_depth = GMPSuccText(depth_text)()
        if M.Compare(term_a, term_b)() is M.truth_value:
            return M.Pair(M.truth_value, term_a)

        check_text = "0"
        remaining_diffs = diffs
        while M.IdentityCompare(remaining_diffs, M.EmptyList)() is M.false_value:
            if GMPEqualText(check_text, self.cap_text)() is M.truth_value:
                remaining_diffs = M.EmptyList
            else:
                check_text = GMPSuccText(check_text)()
                diff = M.Head(remaining_diffs)()
                word_a = M.Head(diff)()
                word_b = M.Head(M.Tail(diff)())()
                variable = M.Head(M.Tail(M.Tail(diff)())())()
                if M.AndAtom(
                    self._names(term_a, word_a),
                    self._names(term_b, word_b),
                )() is M.truth_value:
                    return M.Pair(
                        M.truth_value,
                        Surface(M.Pair(variable, M.EmptyList))(),
                    )
                remaining_diffs = M.Tail(remaining_diffs)()

        both_pairs = M.AndAtom(M.IsPair(term_a)(), M.IsPair(term_b)())()
        if M.IdentityCompare(both_pairs, M.truth_value)() is M.truth_value:
            head_general = self._general(
                M.Head(term_a)(),
                M.Head(term_b)(),
                diffs,
                next_depth,
            )
            if M.IdentityCompare(
                M.Head(head_general)(),
                M.false_value,
            )() is M.truth_value:
                return M.Pair(M.false_value, M.EmptyList)
            tail_general = self._general(
                M.Tail(term_a)(),
                M.Tail(term_b)(),
                diffs,
                next_depth,
            )
            if M.IdentityCompare(
                M.Head(tail_general)(),
                M.false_value,
            )() is M.truth_value:
                return M.Pair(M.false_value, M.EmptyList)
            return M.Pair(
                M.truth_value,
                M.Pair(M.Tail(head_general)(), M.Tail(tail_general)()),
            )
        return M.Pair(M.false_value, M.EmptyList)

    def _names(self, meaning_part, word):
        if M.Compare(meaning_part, word)() is M.truth_value:
            return M.truth_value
        if M.Compare(
            meaning_part,
            Surface(M.Pair(word, M.EmptyList))(),
        )() is M.truth_value:
            return M.truth_value
        resolved = CorrespondenceResolveWord(
            self.word_entries,
            Surface(M.Pair(word, M.EmptyList))(),
        )()
        if M.IdentityCompare(resolved, M.EmptyList)() is M.false_value:
            if M.Compare(meaning_part, resolved)() is M.truth_value:
                return M.truth_value
        return M.false_value

    def __call__(self):
        return self.result


class ValidateCorrespondenceLaws(M.Edge):
    """Check induced parse and render laws against every recorded example.

    Accepted examples the parse law matches must agree in evaluated value
    with their recorded meaning and round-trip through the render law;
    accepted examples it does not match are evidence for other
    constructions and are skipped. The law must cover at least two
    accepted examples. Rejected examples must never match. Returns
    Pair(verdict, Pair(registry, EmptyList)).
    """

    def __init__(self, parse_law, render_law, examples, word_entries, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        verdict = M.truth_value
        covered_text = "0"
        scan_text = "0"
        remaining = examples
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                verdict = M.false_value
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                example = M.Head(remaining)()
                surface = CorrespondenceExampleSurface(example)()
                evidence = CorrespondenceExampleEvidence(example)()
                parsed = CorrespondenceApply(parse_law, surface)()
                if M.Compare(evidence, M.Char("rejected"))() is M.truth_value:
                    if M.IdentityCompare(parsed, M.EmptyList)() is M.false_value:
                        verdict = M.false_value
                        remaining = M.EmptyList
                else:
                    if M.IdentityCompare(parsed, M.EmptyList)() is M.truth_value:
                        pass
                    else:
                        covered_text = GMPSuccText(covered_text)()
                        parsed_value = MeaningEvaluate(
                            parsed,
                            word_entries,
                            registry,
                        )()
                        left_value = M.Head(parsed_value)()
                        registry = M.Head(M.Tail(parsed_value)())()
                        recorded_value = MeaningEvaluate(
                            CorrespondenceExampleMeaning(example)(),
                            word_entries,
                            registry,
                        )()
                        right_value = M.Head(recorded_value)()
                        registry = M.Head(M.Tail(recorded_value)())()
                        rendered = CorrespondenceApply(render_law, parsed)()
                        if M.IdentityCompare(
                            left_value,
                            M.EmptyList,
                        )() is M.truth_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                        elif M.IdentityCompare(
                            right_value,
                            M.EmptyList,
                        )() is M.truth_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                        elif self._values_agree(
                            left_value,
                            right_value,
                            registry,
                        ) is M.false_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                        elif M.IdentityCompare(
                            rendered,
                            M.EmptyList,
                        )() is M.truth_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                        elif M.Compare(rendered, surface)() is M.false_value:
                            verdict = M.false_value
                            remaining = M.EmptyList
                if M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
                    remaining = M.Tail(remaining)()
        if GMPLessText(covered_text, "2")() is M.truth_value:
            verdict = M.false_value
        self.result = M.Pair(verdict, M.Pair(registry, M.EmptyList))
        super().__init__(
            inputs=M.Pair(
                parse_law,
                M.Pair(
                    render_law,
                    M.Pair(
                        examples,
                        M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def _values_agree(self, left_value, right_value, registry):
        # Nats compare by NatEq; symbolic values (Sqrt(7), Mul(three,
        # Sqrt(7))) have no Nat reading and compare structurally. Mixed
        # kinds disagree.
        left_nat = M.IsNat(left_value, registry)()
        right_nat = M.IsNat(right_value, registry)()
        if M.AndAtom(left_nat, right_nat)() is M.truth_value:
            return M.NatEq(left_value, right_value, registry)()
        if M.OrAtom(left_nat, right_nat)() is M.truth_value:
            return M.false_value
        return M.Compare(left_value, right_value)()

    def __call__(self):
        return self.result


class GenerateCorrespondenceProposals(M.Edge):
    """Induce, validate, and submit correspondence laws as pending proposals.

    Accepted example pairs are anti-unified within bounded scans; validated
    candidates are submitted with the render law and source examples as
    JustifiedBy evidence. Nothing is approved or activated here.
    """

    def __init__(self, proposal_store, examples, word_entries, registry):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        proposal_cap_text = M.GMPRepText(CORRESPONDENCE_INDUCTION_CAP)()
        current_store = proposal_store
        submitted_text = "0"
        seen_candidates = M.EmptyList

        outer_text = "0"
        remaining_a = examples
        while M.IdentityCompare(remaining_a, M.EmptyList)() is M.false_value:
            if GMPEqualText(outer_text, cap_text)() is M.truth_value:
                remaining_a = M.EmptyList
            elif GMPEqualText(submitted_text, proposal_cap_text)() is M.truth_value:
                remaining_a = M.EmptyList
            else:
                outer_text = GMPSuccText(outer_text)()
                example_a = M.Head(remaining_a)()
                inner_text = "0"
                remaining_b = M.Tail(remaining_a)()
                while M.IdentityCompare(remaining_b, M.EmptyList)() is M.false_value:
                    if GMPEqualText(inner_text, cap_text)() is M.truth_value:
                        remaining_b = M.EmptyList
                    elif GMPEqualText(
                        submitted_text,
                        proposal_cap_text,
                    )() is M.truth_value:
                        remaining_b = M.EmptyList
                    else:
                        inner_text = GMPSuccText(inner_text)()
                        example_b = M.Head(remaining_b)()
                        rejected_a = M.Compare(
                            CorrespondenceExampleEvidence(example_a)(),
                            M.Char("rejected"),
                        )()
                        rejected_b = M.Compare(
                            CorrespondenceExampleEvidence(example_b)(),
                            M.Char("rejected"),
                        )()
                        if M.OrAtom(rejected_a, rejected_b)() is M.false_value:
                            induced = AntiUnifyCorrespondence(
                                example_a,
                                example_b,
                                word_entries,
                            )()
                            if M.IdentityCompare(
                                induced,
                                M.EmptyList,
                            )() is M.false_value:
                                parse_law = M.Head(induced)()
                                render_law = M.Head(M.Tail(induced)())()
                                duplicate = M.false_value
                                check_text = "0"
                                checking = seen_candidates
                                while M.IdentityCompare(
                                    checking,
                                    M.EmptyList,
                                )() is M.false_value:
                                    if GMPEqualText(
                                        check_text,
                                        cap_text,
                                    )() is M.truth_value:
                                        checking = M.EmptyList
                                    else:
                                        check_text = GMPSuccText(check_text)()
                                        if M.Compare(
                                            M.Head(checking)(),
                                            parse_law,
                                        )() is M.truth_value:
                                            duplicate = M.truth_value
                                            checking = M.EmptyList
                                        else:
                                            checking = M.Tail(checking)()
                                if M.IdentityCompare(
                                    duplicate,
                                    M.false_value,
                                )() is M.truth_value:
                                    seen_candidates = M.Pair(
                                        parse_law,
                                        seen_candidates,
                                    )
                                    validated = ValidateCorrespondenceLaws(
                                        parse_law,
                                        render_law,
                                        examples,
                                        word_entries,
                                        registry,
                                    )()
                                    registry = M.Head(M.Tail(validated)())()
                                    if M.IdentityCompare(
                                        M.Head(validated)(),
                                        M.truth_value,
                                    )() is M.truth_value:
                                        proposal = Proposal(
                                            parse_law,
                                            M.Char("induced-correspondence"),
                                        )()
                                        evidence = M.Pair(
                                            render_law,
                                            M.Pair(
                                                example_a,
                                                M.Pair(example_b, M.EmptyList),
                                            ),
                                        )
                                        current_store = ProposalStoreSubmit(
                                            current_store,
                                            proposal,
                                        )()
                                        current_store = ProposalStoreAttach(
                                            current_store,
                                            proposal,
                                            JustifiedBy(proposal, evidence)(),
                                        )()
                                        submitted_text = GMPSuccText(
                                            submitted_text,
                                        )()
                        remaining_b = M.Tail(remaining_b)()
                remaining_a = M.Tail(remaining_a)()

        self.result = M.Pair(
            current_store,
            M.Pair(
                MineNatFromGMPRep(M.GMPRep(submitted_text))(),
                M.Pair(registry, M.EmptyList),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                proposal_store,
                M.Pair(
                    examples,
                    M.Pair(word_entries, M.Pair(registry, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstalledCorrespondenceLaws(M.Edge):
    """Installed laws whose left pattern is a Surface term."""

    def __init__(self, graph_version):
        cap_text = M.GMPRepText(CORRESPONDENCE_SCAN_CAP)()
        reversed_laws = M.EmptyList
        scan_text = "0"
        remaining = InstalledLaws(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            if GMPEqualText(scan_text, cap_text)() is M.truth_value:
                remaining = M.EmptyList
            else:
                scan_text = GMPSuccText(scan_text)()
                law = M.Head(remaining)()
                left_nodes = GraphNodes(LawLeft(law)())()
                if M.IdentityCompare(left_nodes, M.EmptyList)() is M.false_value:
                    pattern = M.Head(left_nodes)()
                    if M.IsPair(pattern)() is M.truth_value:
                        if M.TermEqual(
                            M.Head(pattern)(),
                            Lmod.SurfaceLabel,
                        )() is M.truth_value:
                            reversed_laws = M.Pair(law, reversed_laws)
                remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_laws)()
        super().__init__(inputs=M.Pair(graph_version, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


WITNESS_SEARCH_CAP = M.GMPRep("50")


class WitnessSearchDivides(M.Edge):
    """Bounded witness search for Divides(d, n): find k with d*k = n.

    Returns Pair(verdict, Pair(evidence, Pair(registry, EmptyList))),
    the WitnessSearchEven contract exactly: verdict truth/false/Empty,
    evidence Confirmed(prop, Witness(k)) or Refuted(prop, no-witness),
    refutation exact (candidates d*k grow monotonically past n), a cap
    hit answering EmptyList because absence of search is not absence
    of witness. d = 0 answers only when n = 0 (witness 0); the
    candidate never grows, so the walk is capped rather than watched.
    """

    def __init__(self, prop_term, divisor, n, registry):
        cap_text = M.GMPRepText(WITNESS_SEARCH_CAP)()
        d_rep = M.NatRepOf(divisor, registry)()
        n_rep = M.NatRepOf(n, registry)()
        verdict = M.EmptyList
        evidence = M.EmptyList
        if M.IdentityCompare(d_rep, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(n_rep, M.EmptyList)() is M.false_value:
                d_text = M.GMPRepText(d_rep)()
                n_text = M.GMPRepText(n_rep)()
                k_text = "0"
                candidate_text = "0"
                searching = M.truth_value
                while M.IdentityCompare(
                    searching, M.truth_value,
                )() is M.truth_value:
                    searching = M.false_value
                    if GMPEqualText(k_text, cap_text)() is M.truth_value:
                        pass
                    elif GMPEqualText(candidate_text, n_text)() is M.truth_value:
                        witness_pair = M.NatFromRep(
                            M.GMPRep(k_text), registry,
                        )()
                        witness_nat = M.Head(witness_pair)()
                        registry = M.Head(M.Tail(witness_pair)())()
                        verdict = M.truth_value
                        evidence = M.Pair(
                            Lmod.ConfirmedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(
                                    M.Pair(
                                        Lmod.WitnessLabel,
                                        M.Pair(witness_nat, M.EmptyList),
                                    ),
                                    M.EmptyList,
                                ),
                            ),
                        )
                    elif GMPLessText(n_text, candidate_text)() is M.truth_value:
                        verdict = M.false_value
                        evidence = M.Pair(
                            Lmod.RefutedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(M.Char("no-witness"), M.EmptyList),
                            ),
                        )
                    elif GMPEqualText(d_text, "0")() is M.truth_value:
                        # 0*k never grows: n != 0 is refuted now, not
                        # at the cap.
                        verdict = M.false_value
                        evidence = M.Pair(
                            Lmod.RefutedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(M.Char("no-witness"), M.EmptyList),
                            ),
                        )
                    else:
                        k_text = GMPSuccText(k_text)()
                        candidate_text = GMPAddText(candidate_text, d_text)()
                        searching = M.truth_value
        self.result = M.Pair(
            verdict,
            M.Pair(evidence, M.Pair(registry, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(
                prop_term,
                M.Pair(divisor, M.Pair(n, M.Pair(registry, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ExactDivisorRestriction(M.Edge):
    """Check every divisor of n lies in the allowed chain.

    The primality shape, spoken generally: the parsed definition says
    'Divides restricted to exactly these fillers', and this edge asks
    whether n satisfies it. Walks d = 1..n under WITNESS_SEARCH_CAP;
    d divides n is decided by the same monotone multiple-walk as
    WitnessSearchDivides; a divisor outside `allowed_nats` refutes with
    that divisor as witness -- the counterexample is evidence, not a
    silent false. All divisors allowed confirms. n's rep missing or
    the cap reached before n answers EmptyList: not knowing is not no.

    Returns Pair(verdict, Pair(evidence, Pair(registry, EmptyList))).
    """

    def __init__(self, prop_term, n, allowed_nats, registry):
        cap_text = M.GMPRepText(WITNESS_SEARCH_CAP)()
        n_rep = M.NatRepOf(n, registry)()
        verdict = M.EmptyList
        evidence = M.EmptyList
        if M.IdentityCompare(n_rep, M.EmptyList)() is M.false_value:
            n_text = M.GMPRepText(n_rep)()
            allowed_texts = M.EmptyList
            allowed_walker = allowed_nats
            while M.IdentityCompare(
                allowed_walker, M.EmptyList,
            )() is M.false_value:
                allowed_rep = M.NatRepOf(M.Head(allowed_walker)(), registry)()
                if M.IdentityCompare(allowed_rep, M.EmptyList)() is M.false_value:
                    allowed_texts = M.Pair(
                        M.Char(M.GMPRepText(allowed_rep)()), allowed_texts,
                    )
                allowed_walker = M.Tail(allowed_walker)()
            d_text = "1"
            counterexample_text = ""
            complete = M.false_value
            walking = M.truth_value
            while M.IdentityCompare(walking, M.truth_value)() is M.truth_value:
                walking = M.false_value
                if GMPEqualText(d_text, cap_text)() is M.truth_value:
                    pass
                elif GMPLessText(n_text, d_text)() is M.truth_value:
                    complete = M.truth_value
                else:
                    multiple_text = d_text
                    divides = M.false_value
                    stepping = M.truth_value
                    while M.IdentityCompare(
                        stepping, M.truth_value,
                    )() is M.truth_value:
                        stepping = M.false_value
                        if GMPEqualText(multiple_text, n_text)() is M.truth_value:
                            divides = M.truth_value
                        elif GMPLessText(multiple_text, n_text)() is M.truth_value:
                            multiple_text = GMPAddText(multiple_text, d_text)()
                            stepping = M.truth_value
                    if M.IdentityCompare(divides, M.truth_value)() is M.truth_value:
                        allowed_here = M.false_value
                        allowed_probe = allowed_texts
                        while M.IdentityCompare(
                            allowed_probe, M.EmptyList,
                        )() is M.false_value:
                            if M.Compare(
                                M.Head(allowed_probe)(), M.Char(d_text),
                            )() is M.truth_value:
                                allowed_here = M.truth_value
                                allowed_probe = M.EmptyList
                            else:
                                allowed_probe = M.Tail(allowed_probe)()
                        if M.IdentityCompare(
                            allowed_here, M.false_value,
                        )() is M.truth_value:
                            counterexample_text = d_text
                    if counterexample_text == "":
                        d_text = GMPSuccText(d_text)()
                        walking = M.truth_value
            if counterexample_text != "":
                witness_pair = M.NatFromRep(
                    M.GMPRep(counterexample_text), registry,
                )()
                witness_nat = M.Head(witness_pair)()
                registry = M.Head(M.Tail(witness_pair)())()
                verdict = M.false_value
                evidence = M.Pair(
                    Lmod.RefutedLabel,
                    M.Pair(
                        prop_term,
                        M.Pair(
                            M.Pair(
                                Lmod.WitnessLabel,
                                M.Pair(witness_nat, M.EmptyList),
                            ),
                            M.EmptyList,
                        ),
                    ),
                )
            elif M.IdentityCompare(complete, M.truth_value)() is M.truth_value:
                verdict = M.truth_value
                evidence = M.Pair(
                    Lmod.ConfirmedLabel,
                    M.Pair(
                        prop_term,
                        M.Pair(M.Char("all-divisors-allowed"), M.EmptyList),
                    ),
                )
        self.result = M.Pair(
            verdict,
            M.Pair(evidence, M.Pair(registry, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(
                prop_term,
                M.Pair(n, M.Pair(allowed_nats, M.Pair(registry, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class WitnessSearchEven(M.Edge):
    """Bounded witness search for Even(n): find k with k+k = n.

    Returns Pair(verdict, Pair(evidence, Pair(registry, EmptyList))).
    verdict is truth/false; evidence is Confirmed(prop, Witness(k)) or
    Refuted(prop, no-witness) -- first-class terms, not silent absences.
    The search walks k = 0,1,2,... under WITNESS_SEARCH_CAP; a cap hit
    refutes nothing and returns EmptyList verdict (the machine does not
    know), because absence of search is not absence of witness.
    """

    def __init__(self, prop_term, n, registry, odd=M.false_value):
        cap_text = M.GMPRepText(WITNESS_SEARCH_CAP)()
        n_rep = M.NatRepOf(n, registry)()
        verdict = M.EmptyList
        evidence = M.EmptyList
        if M.IdentityCompare(n_rep, M.EmptyList)() is M.false_value:
            n_text = M.GMPRepText(n_rep)()
            k_text = "0"
            searching = M.truth_value
            while M.IdentityCompare(searching, M.truth_value)() is M.truth_value:
                searching = M.false_value
                if GMPEqualText(k_text, cap_text)() is M.truth_value:
                    pass
                else:
                    double_text = GMPAddText(k_text, k_text)()
                    candidate_text = double_text
                    if M.IdentityCompare(odd, M.truth_value)() is M.truth_value:
                        candidate_text = GMPSuccText(double_text)()
                    if GMPEqualText(candidate_text, n_text)() is M.truth_value:
                        witness_pair = M.NatFromRep(
                            M.GMPRep(k_text),
                            registry,
                        )()
                        witness_nat = M.Head(witness_pair)()
                        registry = M.Head(M.Tail(witness_pair)())()
                        verdict = M.truth_value
                        evidence = M.Pair(
                            Lmod.ConfirmedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(
                                    M.Pair(
                                        Lmod.WitnessLabel,
                                        M.Pair(witness_nat, M.EmptyList),
                                    ),
                                    M.EmptyList,
                                ),
                            ),
                        )
                    elif GMPLessText(n_text, candidate_text)() is M.truth_value:
                        # Candidates grow monotonically; passing n proves
                        # no witness exists. This refutation is exact, not
                        # a cap artifact.
                        verdict = M.false_value
                        evidence = M.Pair(
                            Lmod.RefutedLabel,
                            M.Pair(
                                prop_term,
                                M.Pair(M.Char("no-witness"), M.EmptyList),
                            ),
                        )
                    else:
                        k_text = GMPSuccText(k_text)()
                        searching = M.truth_value
        self.result = M.Pair(
            verdict,
            M.Pair(evidence, M.Pair(registry, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(
                prop_term,
                M.Pair(n, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result



class DefinitionBodyReading(M.Edge):
    """The Meaning a definition body parses to, through the ordinary templates.

    The body is a sentence and is read like one: ConverseInterpretations
    runs the correspondence templates against it, and the definition-body
    templates in the vocabulary turn "a polygon with three sides" into
    DefinitionCounted(polygon, three, sides) and "a shape" into
    DefinitionGenus(shape). A body with no reading, or with disagreeing
    readings, yields EmptyList -- the machine does not pick one for the
    trainer.

    This replaces a host-side word list and a hand-written state machine.
    A new phrasing is now a new template law, not a new branch.
    """

    def __init__(self, definition, vocabulary, registry):
        self.result = M.EmptyList
        body = DefinitionBody(definition)()
        readings = M.Head(
            ConverseInterpretations(vocabulary, body, registry)(),
        )()
        if M.IdentityCompare(readings, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(
                M.Tail(readings)(), M.EmptyList,
            )() is M.truth_value:
                self.result = M.Head(M.Head(readings)())()
        super().__init__(
            inputs=M.Pair(
                definition,
                M.Pair(vocabulary, M.Pair(registry, M.EmptyList)),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReadingWordConstructor(M.Edge):
    """The constructor a slot of a parsed reading names, or EmptyList.

    A template slot holds a Surface of one word. The word denotes pack
    structure when a bridge links it -- directly, or through its singular,
    so "sides" grounds on "side".
    """

    def __init__(self, graph_version, slot):
        self.result = M.EmptyList
        chain = M.Head(M.Tail(slot)())()
        if M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
            word = M.Head(chain)()
            bridge = BridgeFor(graph_version, word)()
            if M.IdentityCompare(bridge, M.EmptyList)() is M.truth_value:
                singular = WordSingular(word)()
                if M.IdentityCompare(
                    singular, M.EmptyList,
                )() is M.false_value:
                    bridge = BridgeFor(graph_version, singular)()
            if M.IdentityCompare(bridge, M.EmptyList)() is M.false_value:
                self.result = BridgeConstructor(bridge)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(slot, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ReadingWordNat(M.Edge):
    """The Nat a slot of a parsed reading names, or EmptyList."""

    def __init__(self, slot, word_entries):
        self.result = CorrespondenceResolveWord(word_entries, slot)()
        super().__init__(
            inputs=M.Pair(slot, M.Pair(word_entries, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class CompileDefinitionToLaws(M.Edge):
    """A taught definition becomes the same rule shape the packs author.

    "a triangle is a figure with three sides" is not prose to be recited.
    Its subject bridges to TriangleLabel and its body names constructors
    through their own bridges, so the definition asserts that whatever is
    a triangle is also each of those things. That is exactly the pack
    ontology's own form:

        pattern      Triangle(?shape)
        replacement  Polygon(?shape)

    One rule per named body constructor, each compiled through the same
    CompileRuleToLaw the packs go through, so a taught concept enters the
    rule graph as structure rather than as a sentence. Returns EmptyList
    when the subject has no bridge or the body names nothing: a definition
    the machine cannot ground stays a definition and is not guessed at.
    """

    def __init__(self, graph_version, definition,
                 vocabulary=M.EmptyList, registry=M.EmptyList):
        word_entries = M.EmptyList
        if M.IdentityCompare(vocabulary, M.EmptyList)() is M.false_value:
            word_entries = M.Head(M.Tail(vocabulary)())()
        self.result = M.EmptyList
        subject_bridge = BridgeFor(
            graph_version,
            DefinitionTerm(definition)(),
        )()
        if M.IdentityCompare(
            subject_bridge, M.EmptyList,
        )() is M.false_value:
            subject = BridgeConstructor(subject_bridge)()
            shape = M.Pair(
                M.VarTag,
                M.Pair(M.Char("shape"), M.EmptyList),
            )
            pattern = M.Pair(subject, M.Pair(shape, M.EmptyList))
            reversed_laws = M.EmptyList
            reversed_premises = M.EmptyList
            # The body is read by the ordinary correspondence templates,
            # so what arrives here is a Meaning term -- a graph -- not a
            # chain of words to scan. DefinitionGenus(x) says the subject
            # IS an x; DefinitionCounted(x, n, y) says it is an x with n
            # y's. Each becomes a forward rule over a shared ?shape.
            reading = DefinitionBodyReading(
                definition,
                vocabulary,
                registry,
            )()
            if M.IdentityCompare(reading, M.EmptyList)() is M.false_value:
                body_term = M.Head(M.Tail(reading)())()
                reading_head = M.Head(body_term)()
                genus_slot = M.Head(M.Tail(body_term)())()
                genus = ReadingWordConstructor(graph_version, genus_slot)()
                if M.IdentityCompare(genus, M.EmptyList)() is M.false_value:
                    replacement = M.Pair(genus, M.Pair(shape, M.EmptyList))
                    reversed_premises = M.Pair(
                        replacement, reversed_premises,
                    )
                    rule = P.Rule(pattern, replacement)
                    law = CompileRuleToLaw(rule)()
                    if M.IdentityCompare(
                        law, M.EmptyList,
                    )() is M.false_value:
                        # Carry the rule beside its law: a version stores
                        # laws and a runtime fires rules, and nothing
                        # decompiles one into the other.
                        reversed_laws = M.Pair(
                            M.Pair(law, M.Pair(rule, M.EmptyList)),
                            reversed_laws,
                        )
                if M.IdentityCompare(
                    reading_head, M.DefinitionCountedLabel,
                )() is M.truth_value:
                    rest = M.Tail(M.Tail(body_term)())()
                    count_slot = M.Head(rest)()
                    noun_slot = M.Head(M.Tail(rest)())()
                    counted = ReadingWordNat(count_slot, word_entries)()
                    noun = ReadingWordConstructor(graph_version, noun_slot)()
                    if M.IdentityCompare(
                        counted, M.EmptyList,
                    )() is M.false_value:
                        if M.IdentityCompare(
                            noun, M.EmptyList,
                        )() is M.false_value:
                            replacement = M.Pair(
                                noun,
                                M.Pair(
                                    shape,
                                    M.Pair(counted, M.EmptyList),
                                ),
                            )
                            reversed_premises = M.Pair(
                                replacement, reversed_premises,
                            )
                            rule = P.Rule(pattern, replacement)
                            law = CompileRuleToLaw(rule)()
                            if M.IdentityCompare(
                                law, M.EmptyList,
                            )() is M.false_value:
                                reversed_laws = M.Pair(
                                    M.Pair(law, M.Pair(rule, M.EmptyList)),
                                    reversed_laws,
                                )
            # A definition is a biconditional. The forward arrows above say
            # what a triangle is; this is the arrow back -- from a polygon
            # that has three edges, conclude a triangle. It is genuinely
            # multi-premise, which is why the conjunctive compiler exists.
            premises = M.Reverse(reversed_premises)()
            if M.IdentityCompare(premises, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(
                    M.Tail(premises)(), M.EmptyList,
                )() is M.false_value:
                    converse = P.MultiRule(premises, pattern)
                    converse_law = CompileMultiRuleToLaw(converse)()
                    if M.IdentityCompare(
                        converse_law, M.EmptyList,
                    )() is M.false_value:
                        reversed_laws = M.Pair(
                            M.Pair(
                                converse_law,
                                M.Pair(converse, M.EmptyList),
                            ),
                            reversed_laws,
                        )
            self.result = M.Reverse(reversed_laws)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(definition, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallDefinitionLaws(M.Edge):
    """Install every law a definition compiles to; return the new version.

    The version is threaded through InstallLaw one law at a time, so a
    taught concept lands in the same place pack laws land and the search
    considers it on the same terms. A definition that compiles to nothing
    leaves the version untouched.
    """

    def __init__(self, graph_version, definition,
                 vocabulary=M.EmptyList, registry=M.EmptyList):
        current = graph_version
        installed_count = M.Zero
        remaining = CompileDefinitionToLaws(
            graph_version, definition, vocabulary, registry,
        )()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            current = InstallLaw(current, M.Head(M.Head(remaining)())())()
            stepped = M.Succ(installed_count, M.AllConstructors)()
            installed_count = M.Head(stepped)()
            remaining = M.Tail(remaining)()
        self.result = M.Pair(current, M.Pair(installed_count, M.EmptyList))
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(definition, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class DefinitionRulesFor(M.Edge):
    """The rewrite rules a definition compiles to, without installing them.

    A version stores laws; a proof runtime fires rules. Both come from the
    same compilation, so this hands the rule side to whoever needs to
    teach a runtime what the trainer taught the conversation.
    """

    def __init__(self, graph_version, definition,
                 vocabulary=M.EmptyList, registry=M.EmptyList):
        reversed_rules = M.EmptyList
        remaining = CompileDefinitionToLaws(
            graph_version, definition, vocabulary, registry,
        )()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            pair = M.Head(remaining)()
            reversed_rules = M.Pair(M.Head(M.Tail(pair)())(), reversed_rules)
            remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_rules)()
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(definition, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class TaughtDefinitionRules(M.Edge):
    """Every rule every installed Definition in a version compiles to.

    The conversation and the prover kept two rule sets: laws taught here
    never reached the pack-booted runtime that answers 'solve the tao
    triangle problem', so a taught concept could not participate in a
    proof. This is the whole taught ontology in the form a runtime
    accepts, so the two sets can be made one.
    """

    def __init__(self, graph_version,
                 vocabulary=M.EmptyList, registry=M.EmptyList):
        reversed_rules = M.EmptyList
        remaining = InstalledDefinitions(graph_version)()
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            definition = M.Head(remaining)()
            rules = DefinitionRulesFor(
                graph_version, definition, vocabulary, registry,
            )()
            while M.IdentityCompare(rules, M.EmptyList)() is M.false_value:
                reversed_rules = M.Pair(M.Head(rules)(), reversed_rules)
                rules = M.Tail(rules)()
            remaining = M.Tail(remaining)()
        self.result = M.Reverse(reversed_rules)()
        super().__init__(
            inputs=M.Pair(graph_version, M.EmptyList),
            results=self.result,
        )

    def __call__(self):
        return self.result


class InstallDefinition(M.Edge):
    """Splice a Definition node into the version; append-only Next history.

    Returns Pair(new_version, EmptyList). A definition for an
    already-defined term returns the version unchanged and the existing
    Definition at the head of the tail for the caller to report.
    """

    def __init__(self, graph_version, definition):
        existing = DefinitionFor(
            graph_version,
            DefinitionTerm(definition)(),
        )()
        if M.IdentityCompare(existing, M.EmptyList)() is M.false_value:
            self.result = M.Pair(graph_version, M.Pair(existing, M.EmptyList))
        else:
            next_version = GraphVersion(
                M.Pair(definition, GraphNodes(graph_version)()),
                GraphEdges(graph_version)(),
                GraphVersionInvariants(graph_version)(),
            )()
            self.result = M.Pair(next_version, M.EmptyList)
        super().__init__(
            inputs=M.Pair(graph_version, M.Pair(definition, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class VocabularyWithTemplates(M.Edge):
    """Extend a vocabulary's template chain with additional compiled laws."""

    def __init__(self, vocabulary, extra_laws):
        templates = M.Head(vocabulary)()
        reversed_templates = M.Reverse(templates)()
        remaining = extra_laws
        while M.IdentityCompare(remaining, M.EmptyList)() is M.false_value:
            reversed_templates = M.Pair(M.Head(remaining)(), reversed_templates)
            remaining = M.Tail(remaining)()
        self.result = M.Pair(
            M.Reverse(reversed_templates)(),
            M.Tail(vocabulary)(),
        )
        super().__init__(
            inputs=M.Pair(vocabulary, M.Pair(extra_laws, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result





__all__ = [name for name in globals() if not name.startswith("_")]
