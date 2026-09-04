"""Focused semantic gate for the compose fix (SBJ+PREDNOM->DEF).

Drives the DefinitionFragment line
    "definition: a composite number is a natural number that is not prime"
through RecogniseForms with the lexical-gap loop, then measures the
concluded definition node against the contract:

  - the span flips: DEF SPANS after N gap rounds (not the old stall);
  - definiendum carries the measured Hole('composite') and the
    Category('nat') term;
  - exactly one fresh self binds the node;
  - conditions include the natural-category predicate on self and
    Not(Hole('prime', ..., NoDefinitionInstalled)) applied to self;
  - DefinitionNodeOpenDependencies reports 'prime' from inside the
    Not-wrapped applied condition;
  - nothing fabricated: no RestrictionLabel anywhere in the conditions,
    no invented predicate over 'prime' -- the only 'prime' term is the
    minted Hole under Not;
  - the A/B/C dependency-descent probes all report.

Prints each measurement; exits 0 only when every one holds.

Usage: PYTHONPATH=<repo parent> python3 tools/compose_gate.py
Before the fix: "STALL" and exit 1. After: "GATE PASS" and exit 0.
"""
import sys

sys.setrecursionlimit(200000)

import cat_theo_machine.machine as M
import cat_theo_machine.graph as G
import cat_theo_machine.labels as Lmod

empty = M.EmptyList
failures = 0


def check(name, held):
    global failures
    if held:
        print("PASS", name)
    else:
        print("FAIL", name)
        failures += 1


def nth(pair, n):
    walker = pair
    i = 0
    while i < n:
        walker = M.Tail(walker)()
        i += 1
    return M.Head(walker)()


def is_head(term, label):
    if M.IsPair(term)() is M.false_value:
        return False
    return M.IdentityCompare(M.Head(term)(), label)() is M.truth_value


def scan(term, seen):
    """Count label heads and Hole words in a condition subtree."""
    if M.IsPair(term)() is M.false_value:
        return
    head = M.Head(term)()
    if M.IdentityCompare(head, M.VarTag)() is M.truth_value:
        return
    if M.IdentityCompare(head, Lmod.HoleLabel)() is M.truth_value:
        word = M.Head(M.Tail(term)())()
        seen["holes"].append(word() if word() is not None else "<atom>")
    if M.IdentityCompare(head, Lmod.RestrictionLabel)() is M.truth_value:
        seen["restrictions"] += 1
    if M.IdentityCompare(head, Lmod.NotLabel)() is M.truth_value:
        seen["nots"] += 1
    walker = term
    while M.IdentityCompare(walker, empty)() is M.false_value:
        scan(M.Head(walker)(), seen)
        walker = M.Tail(walker)()


# --- drive the engine over the definition line
bundle = G.DefinitionFragment()()
arcs = M.Head(bundle)()
senses = M.Head(M.Tail(bundle)())()
productions = M.Head(M.Tail(M.Tail(bundle)())())()
root = M.Head(M.Tail(M.Tail(M.Tail(bundle)())())())()
def_cat = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())()
alphabet = nth(bundle, 9)
spc = nth(bundle, 10)

symbols = {}
walker = alphabet
while M.IdentityCompare(walker, empty)() is M.false_value:
    symbol = M.Head(walker)()
    symbols[str(symbol())] = symbol
    walker = M.Tail(walker)()

line = "definition: a composite number is a natural number that is not prime"
engine = G.RecogniseForms(empty, arcs, senses, root, productions)
cursors = {}
for index, character in enumerate(line):
    cursors.setdefault(index, M.GMPRep(str(index)))
    cursors.setdefault(index + 1, M.GMPRep(str(index + 1)))
    engine.Observe(
        M.Char(line), cursors[index], symbols[character], cursors[index + 1],
    )
engine.Drain()

gap_rounds = 0
spanned = False
for round_number in range(4):
    top = G.SpanningDefinitionReading(
        M.Head(engine.result)(), def_cat, cursors[0], cursors[len(line)],
    )()
    if M.IdentityCompare(top, empty)() is M.false_value:
        spanned = True
        gap_rounds = round_number
        break
    gap = G.LexicalGap(
        M.Head(engine.result)(), productions, spc, cursors[len(line)],
    )()
    if M.IdentityCompare(gap, empty)() is M.truth_value:
        break
    gap_start = int(M.GMPRepText(M.Head(gap)())())
    gap_end = int(M.GMPRepText(M.Head(M.Tail(gap)())())())
    gap_category = M.Head(M.Tail(M.Tail(gap)())())()
    reversed_symbols = empty
    for index in range(gap_end - 1, gap_start - 1, -1):
        reversed_symbols = M.Pair(symbols[line[index]], reversed_symbols)
    provisional = G.ProvisionalWord(
        root, reversed_symbols, gap_category, M.Char(line[gap_start:gap_end]),
    )()
    engine.Learn(
        M.Head(provisional)(),
        M.Pair(M.Head(M.Tail(provisional)())(), empty),
    )

if spanned:
    print("DEF SPANS after", gap_rounds, "gap rounds")
else:
    print("STALL: SBJ+PREDNOM->DEF never concluded")
check("span flipped", spanned)

if spanned:
    node = G.SpanningDefinitionReading(
        M.Head(engine.result)(), def_cat, cursors[0], cursors[len(line)],
    )()
    check("node is a DefinitionNode", is_head(node, Lmod.DefinitionNodeLabel)
          if M.IsPair(node)() is M.truth_value else False)

    definiendum = G.DefinitionNodeDefiniendum(node)()
    concept = M.Head(M.Tail(definiendum)())()
    category = M.Head(M.Tail(M.Tail(definiendum)())())()
    concept_ok = is_head(concept, Lmod.HoleLabel) and (
        M.Head(M.Tail(concept)())()() == "composite"
    )
    category_ok = is_head(category, Lmod.CategoryLabel) and (
        M.Head(M.Tail(category)())()() == "nat"
    )
    check("definiendum concept is the measured composite Hole", concept_ok)
    check("definiendum category is the measured Category(nat)", category_ok)

    binder = G.DefinitionNodeBinder(node)()
    self_variable = G.BinderSelf(binder)()
    conditions = G.DefinitionNodeConditions(node)()

    natural_condition = M.Head(conditions)()
    natural_head = M.Head(natural_condition)()
    natural_ok = M.IsPair(natural_head)() is M.false_value and (
        natural_head() == "natural"
    ) and M.IdentityCompare(
        M.Head(M.Tail(natural_condition)())(), self_variable,
    )() is M.truth_value
    check("natural-category predicate applied to the fresh self", natural_ok)

    not_condition = empty
    walker = conditions
    while M.IdentityCompare(walker, empty)() is M.false_value:
        candidate = M.Head(walker)()
        if is_head(candidate, Lmod.NotLabel):
            not_condition = candidate
            walker = empty
        else:
            walker = M.Tail(walker)()
    not_ok = M.IdentityCompare(not_condition, empty)() is M.false_value
    if not_ok:
        application = M.Head(M.Tail(not_condition)())()
        if M.IsPair(application)() is M.false_value:
            not_ok = False
        else:
            hole = M.Head(application)()
            applied_arg = M.Head(M.Tail(application)())()
            not_ok = is_head(hole, Lmod.HoleLabel)
            if not_ok:
                word = M.Head(M.Tail(hole)())()
                not_ok = word() == "prime" and word is not None
            if not_ok:
                marker = M.Head(M.Tail(M.Tail(M.Tail(hole)())())())()
                not_ok = M.IdentityCompare(
                    marker, Lmod.NoDefinitionInstalledLabel,
                )() is M.truth_value
            if not_ok:
                not_ok = M.IdentityCompare(
                    applied_arg, self_variable,
                )() is M.truth_value
    check("Not(Hole('prime', NoDefinitionInstalled)) applied to the fresh self",
          not_ok)

    deps = G.DefinitionNodeOpenDependencies(node)()
    dep_texts = []
    walker = deps
    while M.IdentityCompare(walker, empty)() is M.false_value:
        value = M.Head(walker)()
        dep_texts.append(value() if value() is not None else "<atom>")
        walker = M.Tail(walker)()
    print("open dependencies:", dep_texts)
    check("open dependencies report prime", dep_texts == ["prime"])

    seen = {"holes": [], "restrictions": 0, "nots": 0}
    walker = conditions
    while M.IdentityCompare(walker, empty)() is M.false_value:
        scan(M.Head(walker)(), seen)
        walker = M.Tail(walker)()
    print("condition scan:", seen)
    check("no Restriction wrapper anywhere", seen["restrictions"] == 0)
    check("no fabricated predicate: only 'prime' term is the minted Hole",
          seen["holes"] == ["prime"])

# --- A/B/C dependency-descent probes
hole_prime = M.Pair(
    Lmod.HoleLabel,
    M.Pair(M.Char("prime"),
           M.Pair(empty, M.Pair(Lmod.NoDefinitionInstalledLabel, empty))),
)
scope = M.GMPRep("0")
self_var = M.Pair(M.VarTag, M.Pair(scope, M.Pair(M.Char("?self"), empty)))
c_natural = M.Pair(M.Char("natural"), M.Pair(self_var, empty))
c_not = M.Pair(
    Lmod.NotLabel,
    M.Pair(M.Pair(hole_prime, M.Pair(self_var, empty)), empty),
)
definiendum = M.Pair(
    Lmod.DefiniendumLabel,
    M.Pair(M.Char("composite"), M.Pair(M.Char("nat"), empty)),
)


def report(name, conditions):
    node_probe = G.DefinitionNode(
        definiendum, G.Binder(scope, self_var)(), conditions,
    )()
    deps_probe = G.DefinitionNodeOpenDependencies(node_probe)()
    texts = []
    walker = deps_probe
    while M.IdentityCompare(walker, empty)() is M.false_value:
        value = M.Head(walker)()
        texts.append(value() if value() is not None else "<atom>")
        walker = M.Tail(walker)()
    print(name, "->", texts)
    return texts == ["prime"]


check("A Not-wrapped hole reports", report(
    "A", M.Pair(c_natural, M.Pair(c_not, empty))))
check("B bare hole still reports", report(
    "B", M.Pair(c_natural, M.Pair(hole_prime, empty))))
check("C applied hole reports", report(
    "C", M.Pair(c_natural,
                M.Pair(M.Pair(hole_prime, M.Pair(self_var, empty)), empty))))

if failures == 0:
    print("GATE PASS")
    sys.exit(0)
print("GATE FAIL:", failures, "failed checks")
sys.exit(1)
