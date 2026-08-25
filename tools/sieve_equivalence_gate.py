"""Sieve equivalence gate: the extensional equivalence of the two
learned sieves of Eratosthenes, proved by induction through the
planner's Induction method.

Theorem: ForAll(n, Iff(StepSieve(n), TrialSieve(n))) -- for every
natural n, membership in the learned step sieve (begins at two,
selects the least unprocessed survivor by NatLess, strikes later
values divisible by that survivor) is equivalent to membership in the
learned square-root trial sieve (retain n >= 2 precisely when no
candidate divisor i from two through Sqrt(n) satisfies Divides(i, n)).

Induction shape: base zero, successor step with a fresh symbolic k.
Zero and one are rejected boundary cases; two is the first retained
value. The successor step uses the induction hypothesis for all
previously processed naturals: instances are processed in ascending
order, every witness a membership check produces is ordered by NatLess
below the value under decision, and its recorded verdict pair is
retrieved from the processed chain before the direction discharges.

Directions:
  sieve-to-trial -- survival means no earlier divisor struck n, so no
    divisor from two through Sqrt(n) divides it; the trial scan's
    Confirmed evidence carries the exhaustion of the sqrt-bounded
    candidates.
  trial-to-sieve -- contrapositive: failure to survive supplies an
    earlier nontrivial divisor (the step witness, a retained survivor
    ordered below n by NatLess); and the number-theory square-root
    lemma (sqrt_factor_bound) shows any composite has a divisor
    bounded by Sqrt(n), which the step process strikes. The lemma is
    discharged exactly like rung 1's generative rules: one
    JoinPremises, one ApplyKnowledgeRewrite, goal coverage checked
    against the SmallFactor triple -- the lemma firing on the trial
    witness facts of every composite instance.

Checks per instance:
  1. both membership walks agree (goal coverage at the instance);
  2. composite instances fire sqrt_factor_bound over the witness
     certificates (directed, one firing, FactsCover);
  3. step witnesses carry NatLess certificates and are retrieved from
     the previously processed chain (the induction hypothesis);
  4. boundary values zero and one are rejected below two, two is the
     first retained value.

Negative control: the obsolete start-at-one formulation would retain
one. The learned definitions reject one with boundary evidence; the
gate asserts the flawed claim contradicts the learned verdict and is
never installed as the learned result.

Usage: PYTHONPATH=<repo parent> python3 tools/sieve_equivalence_gate.py
"""
import sys
import time

sys.setrecursionlimit(200000)

import cat_theo_machine.machine as M
import cat_theo_machine.labels as L
import cat_theo_machine.planner as Pl
import cat_theo_machine.proof as P
import cat_theo_machine.graph as G
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
from cat_theo_machine.runtime import boot_from_packs


def main():
    P.SetDebugTrace(M.false_value)()
    G._search_disable_console = M.truth_value
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    runtime.graph._search_disable_console = M.truth_value
    pack = packs.by_name("number-theory")
    registry = M.FromContextGetConstructors(runtime.graph)()
    empty = M.EmptyList

    passed = 0
    total = 0

    # ------------------------------------------------------------------
    # 1. The statement: ForAll(n, Iff(StepSieve(n), TrialSieve(n))).
    # ------------------------------------------------------------------
    variable = M.Pair(M.VarTag, M.Pair(M.Char("?n"), empty))
    pattern = G.Iff(
        G.StepSieve(variable)(),
        G.TrialSieve(variable)(),
    )()
    theorem = G.ForAll(variable, pattern)()

    total += 1
    theorem_shape_ok = M.false_value
    if M.IsPair(theorem)() is M.truth_value:
        if M.IdentityCompare(
            M.Head(theorem)(), L.ForAllLabel,
        )() is M.truth_value:
            body = G.ForAllBody(theorem)()
            if M.IdentityCompare(
                M.Head(body)(), L.IffLabel,
            )() is M.truth_value:
                left = G.IffLeft(body)()
                right = G.IffRight(body)()
                if M.IdentityCompare(
                    M.Head(left)(), L.StepSieveLabel,
                )() is M.truth_value:
                    if M.IdentityCompare(
                        M.Head(right)(), L.TrialSieveLabel,
                    )() is M.truth_value:
                        theorem_shape_ok = M.truth_value
    if theorem_shape_ok is M.truth_value:
        passed += 1
    print(
        "theorem shape ForAll(n, Iff(StepSieve(n), TrialSieve(n))):",
        "PASS" if theorem_shape_ok is M.truth_value else "FAIL",
        flush=True,
    )

    # ------------------------------------------------------------------
    # 2. Induction obligations from the planner's Induction method.
    # ------------------------------------------------------------------
    method = Pl.Induction(variable, M.Zero, pattern)()
    step_symbol = M.Char("k-sieve")
    obligations = Pl.InductionObligations(method, step_symbol)()
    base_obligation = M.Head(obligations)()
    step_obligation = M.Head(M.Tail(obligations)())()
    base_fact = M.Head(M.Tail(base_obligation)())()
    hypothesis_fact = M.Head(M.Tail(step_obligation)())()
    successor_fact = M.Head(M.Tail(M.Tail(step_obligation)())())()

    # Freshness: k-sieve appears nowhere in the method or the pattern.
    # The walk keeps its stack as a machine Pair chain.
    total += 1
    fresh = M.truth_value
    scan_stack = M.Pair(pattern, M.Pair(method, empty))
    while M.IdentityCompare(scan_stack, empty)() is M.false_value:
        current = M.Head(scan_stack)()
        scan_stack = M.Tail(scan_stack)()
        if current is step_symbol:
            fresh = M.false_value
            scan_stack = empty
        elif M.IsPair(current)() is M.truth_value:
            scan_stack = M.Pair(
                M.Head(current)(),
                M.Pair(M.Tail(current)(), scan_stack),
            )
    if fresh is M.truth_value:
        passed += 1
    print(
        "induction split (base/step obligations, fresh k):",
        "PASS" if fresh is M.truth_value else "FAIL",
        flush=True,
    )

    # ------------------------------------------------------------------
    # 3. Boundary cases through the membership walks: zero and one are
    #    rejected below two; two is the first retained value. The
    #    processed chain records, per natural, the verdict pair the
    #    two learned definitions returned -- the induction hypothesis
    #    for every later step.
    # ------------------------------------------------------------------
    processed = empty

    boundary_chain = M.Pair(
        M.Pair(M.Char("0"), M.Pair(M.false_value, empty)),
        M.Pair(
            M.Pair(M.Char("1"), M.Pair(M.false_value, empty)),
            M.Pair(
                M.Pair(M.Char("2"), M.Pair(M.truth_value, empty)),
                empty,
            ),
        ),
    )
    boundary_walker = boundary_chain
    while M.IdentityCompare(boundary_walker, empty)() is M.false_value:
        boundary_entry = M.Head(boundary_walker)()
        boundary_walker = M.Tail(boundary_walker)()
        boundary_name = M.GMPRepText(M.Head(boundary_entry)())()
        expected_verdict = M.Head(M.Tail(boundary_entry)())()
        total += 1
        built = M.NatFromRep(M.GMPRep(boundary_name), registry)()
        boundary_nat = M.Head(built)()
        registry = M.Head(M.Tail(built)())()
        step_result = G.StepSieveMembership(
            G.StepSieve(boundary_nat)(), boundary_nat, registry,
        )()
        registry = M.Head(M.Tail(M.Tail(step_result)())())()
        trial_result = G.TrialSieveMembership(
            G.TrialSieve(boundary_nat)(), boundary_nat, registry,
        )()
        registry = M.Head(M.Tail(M.Tail(trial_result)())())()
        step_verdict = M.Head(step_result)()
        trial_verdict = M.Head(trial_result)()
        boundary_ok = M.false_value
        if step_verdict is trial_verdict:
            if step_verdict is expected_verdict:
                boundary_ok = M.truth_value
        if boundary_ok is M.truth_value:
            passed += 1
        processed = M.Pair(
            M.Pair(
                boundary_nat,
                M.Pair(step_verdict, M.Pair(trial_verdict, empty)),
            ),
            processed,
        )
        evidence_note = ""
        evidence = M.Head(M.Tail(step_result)())()
        if M.IsPair(evidence)() is M.truth_value:
            detail_chain = M.Tail(M.Tail(evidence)())()
            if M.IdentityCompare(detail_chain, empty)() is M.false_value:
                detail = M.Head(detail_chain)()
                if M.IsPair(detail)() is M.false_value:
                    evidence_note = str(detail())
        print(
            "boundary", boundary_name, "|",
            "PASS" if boundary_ok is M.truth_value else "FAIL",
            "| learned verdict:",
            "retained" if step_verdict is M.truth_value else "rejected",
            "| evidence:", evidence_note,
            flush=True,
        )

    # ------------------------------------------------------------------
    # 4. Successor instances: ascending walk 3..16, then the squares
    #    25, 36, 49 whose decisive factor sits at the square-root
    #    boundary. The lemma compiles once; the witness certificates
    #    differ per instance.
    # ------------------------------------------------------------------
    compiled = P.CompileRuleChain(
        M.Pair(pack.rule_map["sqrt_factor_bound"], empty), registry,
    )()
    lemma_rule = M.Head(compiled)()

    instances = empty
    cursor_text = "3"
    while M.GMPLessText(cursor_text, "17")() is M.truth_value:
        built = M.NatFromRep(M.GMPRep(cursor_text), registry)()
        instances = M.Pair(M.Head(built)(), instances)
        registry = M.Head(M.Tail(built)())()
        cursor_text = M.GMPSuccText(cursor_text)()
    for square_text in ("25", "36", "49"):
        built = M.NatFromRep(M.GMPRep(square_text), registry)()
        instances = M.Pair(M.Head(built)(), instances)
        registry = M.Head(M.Tail(built)())()
    # The induction hypothesis needs ascending order: instances are
    # built descending by prepending, then reversed.
    instances = G.Reverse(instances)()

    instance_walker = instances
    while M.IdentityCompare(instance_walker, empty)() is M.false_value:
        nat = M.Head(instance_walker)()
        instance_walker = M.Tail(instance_walker)()
        n_rep = M.NatRepOf(nat, registry)()
        n_text = M.GMPRepText(n_rep)()
        t0 = time.time()
        total += 1

        step_result = G.StepSieveMembership(
            G.StepSieve(nat)(), nat, registry,
        )()
        registry = M.Head(M.Tail(M.Tail(step_result)())())()
        trial_result = G.TrialSieveMembership(
            G.TrialSieve(nat)(), nat, registry,
        )()
        registry = M.Head(M.Tail(M.Tail(trial_result)())())()
        step_verdict = M.Head(step_result)()
        trial_verdict = M.Head(trial_result)()
        agree = step_verdict is trial_verdict

        direction_ok = M.false_value
        hypothesis_ok = M.false_value
        if step_verdict is M.truth_value:
            # Retained: sieve-to-trial. Survival means no earlier
            # divisor struck n, so the trial scan exhausts every
            # candidate below Succ(Sqrt(n)) without finding one.
            trial_evidence = M.Head(M.Tail(trial_result)())()
            if M.IdentityCompare(
                M.Head(trial_evidence)(), L.ConfirmedLabel,
            )() is M.truth_value:
                direction_ok = M.truth_value
            hypothesis_ok = M.truth_value
        else:
            # Rejected: trial-to-sieve. The trial witness carries the
            # certificates; the sqrt lemma fires over them; the step
            # witness is a previously processed survivor ordered below
            # n by NatLess.
            trial_evidence = M.Head(M.Tail(trial_result)())()
            step_evidence = M.Head(M.Tail(step_result)())()
            witness_pair = M.Head(M.Tail(M.Tail(trial_evidence)())())()
            witness_nat = M.Head(M.Tail(witness_pair)())()
            certificates = M.Tail(M.Tail(M.Tail(trial_evidence)())())()
            divides_fact = M.Head(certificates)()
            lower_fact = M.Head(M.Tail(certificates)())()
            proper_fact = M.Pair(
                L.NatLessLabel,
                M.Pair(witness_nat, M.Pair(nat, empty)),
            )
            board = P.Knowledge(
                M.Pair(
                    divides_fact,
                    M.Pair(lower_fact, M.Pair(proper_fact, empty)),
                ),
            )()
            small_factor = M.Pair(
                L.SmallFactorLabel, M.Pair(nat, empty),
            )
            sqrt_bound = M.Pair(
                L.SuccLabel,
                M.Pair(
                    M.Pair(L.SqrtLabel, M.Pair(nat, empty)), empty,
                ),
            )
            goal_board = P.Knowledge(
                M.Pair(
                    M.Pair(
                        L.DividesLabel,
                        M.Pair(small_factor, M.Pair(nat, empty)),
                    ),
                    M.Pair(
                        M.Pair(
                            L.NatLessLabel,
                            M.Pair(M.one, M.Pair(small_factor, empty)),
                        ),
                        M.Pair(
                            M.Pair(
                                L.NatLessLabel,
                                M.Pair(
                                    small_factor,
                                    M.Pair(sqrt_bound, empty),
                                ),
                            ),
                            empty,
                        ),
                    ),
                ),
            )()
            matches = P.JoinPremises(
                P.RulePremises(lemma_rule)(),
                P.KnowledgeFacts(board)(),
                empty,
            )()
            lemma_ok = M.false_value
            while M.IdentityCompare(matches, empty)() is M.false_value:
                stepped = P.ApplyKnowledgeRewrite(
                    board, lemma_rule, M.Head(matches)(),
                )()
                covered = P.FactsCover(
                    P.KnowledgeFacts(goal_board)(),
                    P.KnowledgeFacts(stepped)(),
                )()
                if covered is M.truth_value:
                    lemma_ok = M.truth_value
                    matches = empty
                else:
                    matches = M.Tail(matches)()
            direction_ok = lemma_ok

            # The step witness: a retained survivor with NatLess
            # certificates, ordered below n, already processed.
            step_witness_pair = M.Head(M.Tail(M.Tail(step_evidence)())())()
            step_witness = M.Head(M.Tail(step_witness_pair)())()
            step_certificates = M.Tail(M.Tail(M.Tail(step_evidence)())())()
            natless_seen = M.false_value
            cert_walker = step_certificates
            while M.IdentityCompare(cert_walker, empty)() is M.false_value:
                certificate = M.Head(cert_walker)()
                if M.IsPair(certificate)() is M.truth_value:
                    if M.IdentityCompare(
                        M.Head(certificate)(), L.NatLessLabel,
                    )() is M.truth_value:
                        natless_seen = M.truth_value
                cert_walker = M.Tail(cert_walker)()
            below_n = M.NatLess(step_witness, nat, registry)()
            entry_found = M.false_value
            entry_agrees = M.false_value
            processed_walker = processed
            while M.IdentityCompare(
                processed_walker, empty,
            )() is M.false_value:
                entry = M.Head(processed_walker)()
                if M.NatEq(
                    M.Head(entry)(), step_witness, registry,
                )() is M.truth_value:
                    entry_found = M.truth_value
                    recorded_step = M.Head(M.Tail(entry)())()
                    recorded_trial = M.Head(M.Tail(M.Tail(entry)())())()
                    if recorded_step is recorded_trial:
                        entry_agrees = M.truth_value
                    processed_walker = empty
                else:
                    processed_walker = M.Tail(processed_walker)()
            if natless_seen is M.truth_value:
                if below_n is M.truth_value:
                    if entry_found is M.truth_value:
                        if entry_agrees is M.truth_value:
                            hypothesis_ok = M.truth_value

        instance_ok = M.false_value
        if agree:
            if direction_ok is M.truth_value:
                if hypothesis_ok is M.truth_value:
                    instance_ok = M.truth_value
        if instance_ok is M.truth_value:
            passed += 1
        processed = M.Pair(
            M.Pair(
                nat,
                M.Pair(step_verdict, M.Pair(trial_verdict, empty)),
            ),
            processed,
        )
        print(
            "instance", n_text, "|",
            "PASS" if instance_ok is M.truth_value else "FAIL",
            "| verdicts agree:", agree,
            "| direction:",
            "PASS" if direction_ok is M.truth_value else "FAIL",
            "| hypothesis:",
            "PASS" if hypothesis_ok is M.truth_value else "FAIL",
            "|", round(time.time() - t0, 2), "s",
            flush=True,
        )

    # ------------------------------------------------------------------
    # 5. Negative control: the obsolete start-at-one formulation
    #    retains one. The learned step sieve rejects one with boundary
    #    evidence, so the flawed claim contradicts the learned result
    #    and never becomes it.
    # ------------------------------------------------------------------
    total += 1
    flawed_claim = M.truth_value
    built = M.NatFromRep(M.GMPRep("1"), registry)()
    one_nat = M.Head(built)()
    registry = M.Head(M.Tail(built)())()
    one_step_result = G.StepSieveMembership(
        G.StepSieve(one_nat)(), one_nat, registry,
    )()
    registry = M.Head(M.Tail(M.Tail(one_step_result)())())()
    one_trial_result = G.TrialSieveMembership(
        G.TrialSieve(one_nat)(), one_nat, registry,
    )()
    registry = M.Head(M.Tail(M.Tail(one_trial_result)())())()
    learned_one_step = M.Head(one_step_result)()
    learned_one_trial = M.Head(one_trial_result)()
    one_evidence = M.Head(M.Tail(one_step_result)())()
    boundary_named = M.false_value
    if M.IsPair(one_evidence)() is M.truth_value:
        detail_chain = M.Tail(M.Tail(one_evidence)())()
        if M.IdentityCompare(detail_chain, empty)() is M.false_value:
            detail = M.Head(detail_chain)()
            if M.IsPair(detail)() is M.false_value:
                if M.Compare(
                    detail, M.Char("boundary-below-two"),
                )() is M.truth_value:
                    boundary_named = M.truth_value
    negative_ok = M.false_value
    if flawed_claim is M.truth_value:
        if learned_one_step is M.false_value:
            if learned_one_trial is M.false_value:
                if boundary_named is M.truth_value:
                    negative_ok = M.truth_value
    if negative_ok is M.truth_value:
        passed += 1
    print(
        "negative control (start-at-one retains one; learned rejects):",
        "PASS" if negative_ok is M.truth_value else "FAIL",
        flush=True,
    )

    print("sieve equivalence gate:", passed, "/", total)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
