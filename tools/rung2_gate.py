"""Rung 2 gate: universally quantified divisibility by trainer-hinted
induction through the planner's Induction method.

Theorem family: for every Nat n >= 1, Divides(d, Mul(d, n)) -- proved
for d = two and d = three. The Induction method splits the goal into a
BaseCase and a StepCase obligation (planner.InductionObligations); each
obligation is discharged by DIRECTED application of pack lemmas (one
JoinPremises + one ApplyKnowledgeRewrite per step, goal coverage
checked), because the fold lemmas are generative and saturating over
them diverges (rung-1 measurement). No kernel: acceptance is goal
coverage plus the numeric instance checks, the TrainingRecord
discipline.

Checks per theorem:
  1. freshness: the step symbol appears nowhere in the problem terms;
  2. base case: Divides(d, Mul(d, 1)) from Divides(d, d) via
     mul_one_fold;
  3. step case: hypothesis Divides(d, Mul(d, k)) plus Divides(d, d)
     reach Divides(d, Mul(d, Succ(k))) via divides_sum then
     mul_succ_fold;
  4. instance checks: the property holds numerically at n = 1, 2, 3
     (host arithmetic at the gate boundary, standing where trust
     stands in TrainingRecords).

Usage: PYTHONPATH=<repo parent> python3 tools/rung2_gate.py
"""
import sys
import time

sys.setrecursionlimit(200000)

import cat_theo_machine.machine as M
import cat_theo_machine.labels as L
import cat_theo_machine.planner as Pl
import cat_theo_machine.proof as P
import cat_theo_machine.graph as graph
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
from cat_theo_machine.runtime import boot_from_packs
from cat_theo_machine.training import char_chain


def term_mentions(term, atom):
    stack = M.Pair(term, M.EmptyList)
    while M.IdentityCompare(stack, M.EmptyList)() is M.false_value:
        current = M.Head(stack)()
        stack = M.Tail(stack)()
        if current is atom:
            return True
        if M.IsPair(current)() is M.truth_value:
            stack = M.Pair(M.Head(current)(), M.Pair(M.Tail(current)(), stack))
    return False


def directed_discharge(pack, registry, facts, lemma_ids, goal_fact):
    """Apply the named lemmas in order, one directed step per lemma,
    branching over every premise match (a join can bind the premises
    to the board in several ways; the discharge is sound for any of
    them, so all are candidate branches). Returns (ok, steps): steps
    counts lemmas applied on the succeeding branch."""
    goal_state = P.Knowledge(M.Pair(goal_fact, M.EmptyList))()
    goal_facts = P.KnowledgeFacts(goal_state)()

    def matches_of(state, rid):
        compiled = P.CompileRuleChain(
            M.Pair(pack.rule_map[rid], M.EmptyList), registry,
        )()
        rule = M.Head(compiled)()
        found = P.JoinPremises(
            P.RulePremises(rule)(), P.KnowledgeFacts(state)(), M.EmptyList,
        )()
        out = M.EmptyList
        while M.IdentityCompare(found, M.EmptyList)() is M.false_value:
            out = M.Pair(M.Pair(rule, M.Pair(M.Head(found)(), M.EmptyList)), out)
            found = M.Tail(found)()
        return out

    def walk(state, remaining):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            covered = P.FactsCover(
                goal_facts, P.KnowledgeFacts(state)(),
            )()
            return covered is M.truth_value
        lemma_id = ""
        id_chars = M.Head(remaining)()
        while M.IdentityCompare(id_chars, M.EmptyList)() is M.false_value:
            lemma_id = lemma_id + str(M.Head(id_chars)()())
            id_chars = M.Tail(id_chars)()
        candidates = matches_of(state, lemma_id)
        while M.IdentityCompare(candidates, M.EmptyList)() is M.false_value:
            entry = M.Head(candidates)()
            rule = M.Head(entry)()
            bindings = M.Head(M.Tail(entry)())()
            stepped = P.ApplyKnowledgeRewrite(state, rule, bindings)()
            if walk(stepped, M.Tail(remaining)()):
                return True
            candidates = M.Tail(candidates)()
        return False

    ok = walk(P.Knowledge(facts)(), lemma_ids)
    steps = 0
    counting = lemma_ids
    while M.IdentityCompare(counting, M.EmptyList)() is M.false_value:
        steps = steps + 1
        counting = M.Tail(counting)()
    return ok, steps if ok else 0


def nat_value(term, registry):
    rep = M.NatRepOf(term, registry)()
    if M.IdentityCompare(rep, M.EmptyList)() is M.truth_value:
        return None
    return int(rep())


def main():
    P.SetDebugTrace(M.false_value)()
    graph._search_disable_console = M.truth_value
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    runtime.graph._search_disable_console = M.truth_value
    pack = packs.by_name("number-theory")
    registry = M.FromContextGetConstructors(runtime.graph)()
    empty = M.EmptyList

    one_nat = M.Pair(L.SuccLabel, M.Pair(M.Zero, empty))
    passed = 0
    total = 0

    for divisor_name, divisor in (("two", M.two), ("three", M.three)):
        total += 1
        t0 = time.time()
        variable = M.Pair(M.VarTag, M.Pair(M.Char("?n"), empty))
        pattern = M.Pair(
            L.DividesLabel,
            M.Pair(divisor, M.Pair(
                M.Pair(M.ExprMulLabel, M.Pair(divisor, M.Pair(variable, empty))),
                empty,
            )),
        )
        method = Pl.Induction(variable, one_nat, pattern)()
        step_symbol = M.Char("k-" + divisor_name)
        obligations = Pl.InductionObligations(method, step_symbol)()

        base = M.Head(obligations)()
        step = M.Head(M.Tail(obligations)())()
        base_fact = M.Head(M.Tail(base)())()
        hypothesis = M.Head(M.Tail(step)())()
        successor_fact = M.Head(M.Tail(M.Tail(step)())())()

        # 1. freshness: the step symbol is nowhere in method or pattern
        fresh = not term_mentions(pattern, step_symbol) and not term_mentions(
            method, step_symbol,
        )

        # the axiom the trainer supplies: d divides d
        self_divides = M.Pair(
            L.DividesLabel, M.Pair(divisor, M.Pair(divisor, empty)),
        )

        # 2. base case: Divides(d, d) --mul_one_fold--> Divides(d, Mul(d, 1))
        base_ok, base_steps = directed_discharge(
            pack, registry,
            M.Pair(self_divides, empty),
            M.Pair(char_chain("mul_one_fold"), M.EmptyList),
            base_fact,
        )

        # 3. step case: hypothesis + Divides(d, d)
        #    --divides_sum--> Divides(d, Mul(d,k)+d)
        #    --mul_succ_fold--> Divides(d, Mul(d, Succ(k)))
        step_ok, step_steps = directed_discharge(
            pack, registry,
            M.Pair(hypothesis, M.Pair(self_divides, empty)),
            M.Pair(char_chain("divides_sum"), M.Pair(char_chain("mul_succ_fold"), M.EmptyList)),
            successor_fact,
        )

        # 4. numeric instance checks at n = 1, 2, 3
        d_value = nat_value(divisor, registry)
        instances_ok = d_value is not None and all(
            (d_value * n) % d_value == 0 for n in (1, 2, 3)
        )

        ok = fresh and base_ok and step_ok and instances_ok
        if ok:
            passed += 1
        print(
            "forall n>=1: Divides(", divisor_name, ", Mul(", divisor_name,
            ", n)) |", "PASS" if ok else "FAIL",
            "| fresh:", fresh,
            "| base:", base_ok, "(", base_steps, "step )",
            "| step:", step_ok, "(", step_steps, "steps )",
            "| instances:", instances_ok,
            "|", round(time.time() - t0, 2), "s",
            flush=True,
        )

    # negative control: a broken step chain must NOT discharge
    total += 1
    variable = M.Pair(M.VarTag, M.Pair(M.Char("?n"), empty))
    pattern = M.Pair(
        L.DividesLabel,
        M.Pair(M.two, M.Pair(
            M.Pair(M.ExprMulLabel, M.Pair(M.two, M.Pair(variable, empty))),
            empty,
        )),
    )
    method = Pl.Induction(variable, one_nat, pattern)()
    obligations = Pl.InductionObligations(method, M.Char("k-neg"))()
    step = M.Head(M.Tail(obligations)())()
    hypothesis = M.Head(M.Tail(step)())()
    successor_fact = M.Head(M.Tail(M.Tail(step)())())()
    # wrong axiom: three divides three cannot carry two's step case
    wrong_axiom = M.Pair(
        L.DividesLabel, M.Pair(M.three, M.Pair(M.three, empty)),
    )
    bad_ok, _ = directed_discharge(
        pack, registry,
        M.Pair(hypothesis, M.Pair(wrong_axiom, empty)),
        M.Pair(char_chain("divides_sum"), M.Pair(char_chain("mul_succ_fold"), M.EmptyList)),
        successor_fact,
    )
    if not bad_ok:
        passed += 1
    print("negative control (wrong axiom) refused:", not bad_ok, flush=True)

    print("rung 2:", passed, "/", total)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
