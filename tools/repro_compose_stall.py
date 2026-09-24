"""Reproduction: SBJ+PREDNOM composition never concludes DEF.

Handover to the fragment-engine line (RecogniseForms, 744dd39). The
line "definition: a composite number is a natural number that is not
prime", after two gap rounds learn 'composite' and 'prime':

  - Reading SBJ 0..34 exists,
  - Reading PREDNOM 34..68 exists,
  - BinaryProduction (SBJ, PREDNOM, DEF, kind-definition) exists,
  - the production is found via production_right_index_spec,
  - the SBJ reading is found via reading_end_index_spec,
  - SBJ's end cursor IS PREDNOM's start cursor (identity verified),

yet no DEF reading forms; the spanning check fails and the definition
is refused. Engine counters at the stall: 423 facts, 202 conclusions
attempted, 154 new. The missing conclusion dies inside the plan
interpreter -- everything the plans consult is verifiably in place.

The grammar additions this line needs (natural/that/not lexicon, the
relative-clause productions, LexicalGap's caller-supplied line-end
cursor) are all in the tree and working: both unknown words learn,
RELPRED 51..68 and PREDNOM 34..68 form. Only the final composition is
missing.

Usage: PYTHONPATH=<repo parent> python3 tools/repro_compose_stall.py
Expected today: "STALL REPRODUCED". After the fix: "DEF SPANS".
"""
import sys

sys.setrecursionlimit(200000)

import cat_theo_machine.machine as M
import cat_theo_machine.graph as G


def main():
    bundle = G.DefinitionFragment()()
    arcs = M.Head(bundle)()
    senses = M.Head(M.Tail(bundle)())()
    productions = M.Head(M.Tail(M.Tail(bundle)())())()
    root = M.Head(M.Tail(M.Tail(M.Tail(bundle)())())())()
    def_cat = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())()
    alphabet = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())())())())())())()
    spc = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(bundle)())())())())())())())())())())()
    symbols = {}
    walker = alphabet
    while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
        symbol = M.Head(walker)()
        symbols[str(symbol())] = symbol
        walker = M.Tail(walker)()

    line = "definition: a composite number is a natural number that is not prime"
    engine = G.RecogniseForms(M.EmptyList, arcs, senses, root, productions)
    cursors = {}
    for index, character in enumerate(line):
        cursors.setdefault(index, M.GMPRep(str(index)))
        cursors.setdefault(index + 1, M.GMPRep(str(index + 1)))
        engine.Observe(
            M.Char(line), cursors[index], symbols[character],
            cursors[index + 1],
        )
    engine.Drain()

    for round_number in range(4):
        top = G.SpanningDefinitionReading(
            M.Head(engine.result)(), def_cat,
            cursors[0], cursors[len(line)],
        )()
        if M.IdentityCompare(top, M.EmptyList)() is M.false_value:
            print("DEF SPANS after", round_number, "gap rounds")
            return 0
        gap = G.LexicalGap(
            M.Head(engine.result)(), productions, spc,
            cursors[len(line)],
        )()
        if M.IdentityCompare(gap, M.EmptyList)() is M.truth_value:
            break
        gap_start = int(M.GMPRepText(M.Head(gap)())())
        gap_end = int(M.GMPRepText(M.Head(M.Tail(gap)())())())
        gap_category = M.Head(M.Tail(M.Tail(gap)())())()
        print("learned:", line[gap_start:gap_end], "as", gap_category())
        reversed_symbols = M.EmptyList
        for index in range(gap_end - 1, gap_start - 1, -1):
            reversed_symbols = M.Pair(symbols[line[index]], reversed_symbols)
        provisional = G.ProvisionalWord(
            root, reversed_symbols, gap_category,
            M.Char(line[gap_start:gap_end]),
        )()
        engine.Learn(
            M.Head(provisional)(),
            M.Pair(M.Head(M.Tail(provisional)())(), M.EmptyList),
        )

    # the stall: verify the pieces the composition needs are all present
    sbj = prednom = None
    walker = M.Head(engine.result)()
    while M.IdentityCompare(walker, M.EmptyList)() is M.false_value:
        reading = M.Head(walker)()
        category = M.Head(M.Tail(reading)())()
        if M.IsPair(category)() is M.false_value:
            start_text = M.GMPRepText(M.Head(M.Tail(M.Tail(reading)())())())()
            end_text = M.GMPRepText(
                M.Head(M.Tail(M.Tail(M.Tail(reading)())())())(),
            )()
            if category() == "SBJ" and start_text == "0" and end_text == "34":
                sbj = reading
            if category() == "PREDNOM" and start_text == "34" and end_text == "68":
                prednom = reading
        walker = M.Tail(walker)()
    print("SBJ 0..34 present:", sbj is not None)
    print("PREDNOM 34..68 present:", prednom is not None)
    if sbj is not None and prednom is not None:
        sbj_end = M.Head(M.Tail(M.Tail(M.Tail(sbj)())())())()
        prednom_start = M.Head(M.Tail(M.Tail(prednom)())())()
        print("cursor identity across the join:", sbj_end is prednom_start)
    print("facts:", engine.facts_inserted_text,
          "| attempted:", engine.conclusions_attempted_text,
          "| new:", engine.new_conclusions_text)
    print("STALL REPRODUCED: SBJ+PREDNOM->DEF never concluded")
    return 1


if __name__ == "__main__":
    sys.exit(main())
