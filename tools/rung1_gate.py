"""Rung 1 gate: every number-theory lemma is exercised and passes.

Closure lemmas (translation into divisibility, transitivity, gcd
projection) prove through the ordinary search: their consequences over
a fixed board are finite. Generative lemmas (divides_sum,
divides_product) MINT terms -- Divides(3, 6+9) enables
Divides(3, 6+(6+9)) without end -- so saturating search over them
diverges by construction (measured: OOM at 4 GB). They are exercised
by directed application instead: one JoinPremises, one
ApplyKnowledgeRewrite, goal coverage checked -- the consumption
pattern rung 2's obligation discharge will use.

Usage: PYTHONPATH=<repo parent> python3 tools/rung1_gate.py
"""
import sys
import time

sys.setrecursionlimit(200000)

import cat_theo_machine.machine as M
import cat_theo_machine.proof as P
import cat_theo_machine.graph as graph
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
from cat_theo_machine.runtime import boot_from_packs

# Search exercises run against the full closure chain -- the four
# non-generative lemmas together, the way a session would hold them.
CLOSURE_CHAIN = [
    "even_means_two_divides",
    "divides_transitive",
    "zero_remainder_means_divides",
    "gcd_divides_both",
]

SEARCH_EXERCISES = (
    "nt_even_to_divides",
    "nt_divides_transitive",
    "nt_mod_zero_to_divides",
    "nt_gcd_divides_both",
    "nt_even_chain",
    "nt_mod_chain",
)

DIRECTED_EXERCISES = (
    ("nt_divides_sum", "divides_sum"),
    ("nt_divides_product", "divides_product"),
)


def chain_of(pack, ids):
    rules = M.EmptyList
    for rid in reversed(ids):
        rules = M.Pair(pack.rule_map[rid], rules)
    return rules


def _fresh():
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    runtime.graph._search_disable_console = M.truth_value
    return runtime, packs.by_name("number-theory")


def main():
    P.SetDebugTrace(M.false_value)()
    graph._search_disable_console = M.truth_value
    passed = 0
    total = 0

    for example_id in SEARCH_EXERCISES:
        total += 1
        # Fresh runtime per exercise: proofs always cold-boot (the
        # 73efb13 invariant), and a runtime that has already proved
        # carries memoized state the next proof must not inherit
        # (BuildDerivation crashes on a reused runtime with a changed
        # rule chain).
        runtime, pack = _fresh()
        closure = chain_of(pack, CLOSURE_CHAIN)
        start, goal = pack.examples[example_id]
        t0 = time.time()
        derivation = runtime.prove(start, goal, rules=closure, phi=pack.phi)
        elapsed = time.time() - t0
        ok = M.IdentityCompare(derivation, M.EmptyList)() is M.false_value
        steps = 0
        if ok:
            reg = M.FromContextGetConstructors(runtime.graph)()
            chain = P.DerivationSteps(derivation, reg)()
            while M.IdentityCompare(chain, M.EmptyList)() is M.false_value:
                steps += 1
                chain = M.Tail(chain)()
            passed += 1
        print(example_id, "| search |", "PASS" if ok else "FAIL",
              "|", round(elapsed, 2), "s |", steps, "steps", flush=True)

    runtime, pack = _fresh()
    registry = M.FromContextGetConstructors(runtime.graph)()
    for example_id, rid in DIRECTED_EXERCISES:
        total += 1
        start, goal = pack.examples[example_id]
        compiled = P.CompileRuleChain(
            M.Pair(pack.rule_map[rid], M.EmptyList), registry,
        )()
        rule = M.Head(compiled)()
        state = P.NormalizeKnowledge(start, registry)()
        goal_state = P.NormalizeKnowledge(goal, registry)()
        t0 = time.time()
        matches = P.JoinPremises(
            P.RulePremises(rule)(), P.KnowledgeFacts(state)(), M.EmptyList,
        )()
        ok = M.false_value
        while M.IdentityCompare(matches, M.EmptyList)() is M.false_value:
            stepped = P.ApplyKnowledgeRewrite(state, rule, M.Head(matches)())()
            covered = P.FactsCover(
                P.KnowledgeFacts(goal_state)(), P.KnowledgeFacts(stepped)(),
            )()
            if covered is M.truth_value:
                ok = M.truth_value
                matches = M.EmptyList
            else:
                matches = M.Tail(matches)()
        elapsed = time.time() - t0
        if ok is M.truth_value:
            passed += 1
        print(example_id, "| directed |",
              "PASS" if ok is M.truth_value else "FAIL",
              "|", round(elapsed, 2), "s", flush=True)

    # nt_gcd_sum_chain: directed two-step -- gcd projection, then the
    # sum lemma over its output.
    total += 1
    start, goal = pack.examples["nt_gcd_sum_chain"]
    state = P.NormalizeKnowledge(start, registry)()
    goal_state = P.NormalizeKnowledge(goal, registry)()
    t0 = time.time()
    ok = M.false_value
    for rid in ("gcd_divides_both", "divides_sum"):
        compiled = P.CompileRuleChain(
            M.Pair(pack.rule_map[rid], M.EmptyList), registry,
        )()
        rule = M.Head(compiled)()
        matches = P.JoinPremises(
            P.RulePremises(rule)(), P.KnowledgeFacts(state)(), M.EmptyList,
        )()
        if M.IdentityCompare(matches, M.EmptyList)() is M.truth_value:
            break
        state = P.ApplyKnowledgeRewrite(state, rule, M.Head(matches)())()
    covered = P.FactsCover(
        P.KnowledgeFacts(goal_state)(), P.KnowledgeFacts(state)(),
    )()
    if covered is M.truth_value:
        ok = M.truth_value
        passed += 1
    print("nt_gcd_sum_chain | directed |",
          "PASS" if ok is M.truth_value else "FAIL",
          "|", round(time.time() - t0, 2), "s", flush=True)

    print("rung 1:", passed, "/", total)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
