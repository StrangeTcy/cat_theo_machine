"""Parse one sentence in a fresh process and print the parsed term.

    python3 tools/preflight_decoy_shape.py "<sentence>"

Preflight item 3. One sentence, one process, one printed term. Two
invocations of this tool are the two "fresh parser processes" the ruling
asks for; nothing is shared between them and neither runs a search.

Printing uses the machine's own predicates (IsPair / IsAtom) rather than
host type tests, and renders the term as an s-expression so the two
sentences can be compared structurally by eye and by diff.
"""
import sys

sys.path.insert(0, "/home/user")

import cat_theo_machine.machine as M


def show(term):
    if term is M.EmptyList:
        return "()"
    if M.IsPair(term)() is M.truth_value:
        parts = []
        current = term
        while M.IsPair(current)() is M.truth_value:
            parts.append(show(current.head.value))
            current = current.tail.value
        if current is not M.EmptyList:
            parts.append("." + show(current))
        return "(" + " ".join(parts) + ")"
    # Char carries its text in .symbol and returns it from __call__.
    return str(term())


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    text = sys.argv[1]
    import cat_theo_machine.main as app

    term, error = app._research_parse_sentence(text)
    print("sentence: " + text)
    if error is not None:
        print("parse error: " + error)
        return 1
    print("term: " + show(term))
    return 0


if __name__ == "__main__":
    sys.exit(main())
