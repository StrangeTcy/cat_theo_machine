"""Preflight item 2 — A1 producer/consumer selection probe.

    python3 tools/preflight_a1_selection.py

Compiles the nosolutions producer and consumer through the real rule
compiler, confirms both are MultiRule, then runs candidate selection of the
producer against the toy goal in an isolated, session-only rule pool.

Nothing here is persisted: no pack is written, nothing is installed into
FireAny, and no domain content is created. The pool exists only for this
process. The goal is expected to remain unclosed — this is a selection
probe, not a theorem.

Printed: MultiRule confirmation, candidate partial-match count, selected
rule identity, whether the goal closed, and the attempt records with their
matched and unmatched premises.
"""
import sys

sys.path.insert(0, "/home/user")

import cat_theo_machine.machine as M
import cat_theo_machine.research as Rmod

G_TEXT = "(nosolutions positive-integers (unknowns x) (eq (plus x 1) x))"
P_TEXT = "(a1-producer-premise " + G_TEXT + ")"
C_TEXT = "(a1-consumer-result " + G_TEXT + ")"

PRODUCER_RULE = "(rule (premises " + P_TEXT + ") (conclusion " + G_TEXT + "))"
CONSUMER_RULE = "(rule (premises " + G_TEXT + ") (conclusion " + C_TEXT + "))"


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
    return str(term())


def walk(chain):
    out = ()
    current = chain
    while M.IsPair(current)() is M.truth_value:
        out = out + (current.head.value,)
        current = current.tail.value
    return out


def multirule_shape(rule):
    """A MultiRule is an Edge whose inputs are Pair(premises, Pair(replacement,
    EmptyList)) and whose results are EmptyList. Check that shape rather than
    naming the class, and report the object's own rendering alongside."""
    inputs = rule.inputs
    results = rule.results
    inputs_is_pair = M.IsPair(inputs)() is M.truth_value
    results_empty = M.IdentityCompare(results, M.EmptyList)() is M.truth_value
    shape_ok = (
        inputs_is_pair
        and results_empty
        and M.IsPair(M.Tail(inputs)())() is M.truth_value
        and M.IdentityCompare(M.Tail(M.Tail(inputs)())(), M.EmptyList)()
        is M.truth_value
    )
    return {
        "shape_ok": shape_ok,
        "inputs_is_pair": inputs_is_pair,
        "results_empty": results_empty,
        "premises": show(M.Head(inputs)()) if inputs_is_pair else "<n/a>",
        "replacement": show(M.Head(M.Tail(inputs)())()) if inputs_is_pair else "<n/a>",
        "repr": repr(rule),
    }


def main():
    from cat_theo_machine.main import _research_parse, _research_parse_rule
    from cat_theo_machine.runtime import make_fresh_runtime

    graph = make_fresh_runtime().graph

    goal, err = _research_parse(G_TEXT)
    if err is not None:
        print("cannot parse goal: " + err)
        return 1

    producer_formal, err = _research_parse_rule(PRODUCER_RULE)
    if err is not None:
        print("cannot parse producer rule: " + err)
        return 1
    consumer_formal, err = _research_parse_rule(CONSUMER_RULE)
    if err is not None:
        print("cannot parse consumer rule: " + err)
        return 1

    producer = Rmod.compile_formal_rule(producer_formal)
    consumer = Rmod.compile_formal_rule(consumer_formal)

    print("=" * 70)
    print("goal   G = " + show(goal))
    print("marker P = " + P_TEXT)
    print("marker C = " + C_TEXT)
    print("=" * 70)
    print("")

    for name, rule in (("producer", producer), ("consumer", consumer)):
        info = multirule_shape(rule)
        print("%s:" % name)
        print("  MultiRule shape: %s" % ("YES" if info["shape_ok"] else "NO"))
        print("  inputs is Pair:  %s   results EmptyList: %s"
              % (info["inputs_is_pair"], info["results_empty"]))
        print("  premises slot:   %s" % info["premises"])
        print("  replacement slot %s" % info["replacement"])
        print("  object:          %s" % info["repr"])
        print("")

    # isolated, session-only pool: the producer and nothing else
    pool = M.Pair(producer, M.EmptyList)
    print("session-only pool: 1 rule (the producer); not installed into FireAny")
    print("")

    outcome = Rmod.attempt_goal(
        graph, Rmod.axiom_facts(graph), M.Pair(goal, M.EmptyList), pool
    )

    attempts = walk(getattr(graph, "research_attempts", M.EmptyList))
    print("candidate partial-match count: %d" % len(attempts))
    for attempt in attempts:
        rule_obj = Rmod.AttemptedRuleId(attempt)()
        identity = "producer" if rule_obj is producer else "other@%x" % (
            id(rule_obj) & 0xFFFFFFFF,
        )
        origin = "<unreadable>"
        try:
            origin = show(Rmod.AttemptedRuleOrigin(attempt)())
        except Exception:
            pass
        print("  selected rule identity: %s" % identity)
        print("  rule origin:            %s" % origin)
        print("  attempt record:         %s" % show(attempt))

    closed = Rmod.ForwardSearchClosed(outcome)()
    print("")
    print("goal closed: %s" % ("YES" if closed is M.truth_value else "NO"))
    print("forward search cost: %s" % show(Rmod.ForwardSearchCost(outcome)()))
    print("")
    print("expected: producer candidate count >= 1; unmatched premise P; goal not closed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
