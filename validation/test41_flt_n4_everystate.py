"""W29: retry W6's missing list after W21-W23; precise negative outcome.

No quartic, parametrisation or square-factor schema is authored. Existing
modules/packs and test26 are consumed unchanged. A full registered-rule audit
pins the missing EveryStateMoves producer; bounded smoke searches are labelled
as such, not used as a proof of impossibility. The symbol-absence argument is
scoped to these ordinary knowledge-rewrite rules, not arbitrary future code.

Progress is real but limited: anonymous witnesses allocate, both W6 polynomial
identities have Checker-B grid proofs, and a predecessor of an actual family
measure has a Peano proof from a computed successor premise. Atom identity
blocks transporting even that one-step order fact to its independently computed
arithmetic endpoint. None constructs a smaller solution or proves a universal
descent. The ledger must not promote it.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cat_theo_machine import machine as M, labels as L, proof as P
from cat_theo_machine import runtime, main as main_mod, graph_task as GT
from cat_theo_machine import playground as PG, checker_b as CB, dialogue as D
from cat_theo_machine import evaluator as Eval, promotion_ledger as Ledger
from cat_theo_machine import invariance as Inv, rewrite_rules as RR
from cat_theo_machine.math import arithmetic as A

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def chain(*items):
    result = M.EmptyList
    for item in reversed(items):
        result = M.Pair(item, result)
    return result


def fact(label, *args):
    return M.Pair(label, chain(*args))


def field(record, index):
    rest = M.Tail(record)()
    for _ in range(index):
        rest = M.Tail(rest)()
    return M.Head(rest)()


def contains_symbol(term, symbol, registry):
    """Machine structural audit, including constructors hidden behind atoms.

    This audits acyclic pack terms, not arbitrary cyclic snapshot contents.
    It never reads a label name or an atom's host representation.
    """
    if M.IdentityCompare(term, symbol)() is M.truth_value:
        return M.truth_value
    if M.IsPair(term)() is M.truth_value:
        return M.OrAtom(contains_symbol(M.Head(term)(), symbol, registry),
                        contains_symbol(M.Tail(term)(), symbol, registry))()
    constructor = M.GetConstructor(term, registry)()
    if M.IdentityCompare(constructor, M.EmptyList)() is M.truth_value:
        return M.false_value
    return contains_symbol(constructor, symbol, registry)


def main():
    t0 = time.monotonic()
    checks = 0

    def check(name, ok):
        nonlocal checks
        assert ok, name
        checks += 1
        print('PASS', name, flush=True)

    print('=== TEST 41: W29 EveryStateMoves retry ===', flush=True)
    rt, loaded = runtime.boot_from_packs(main_mod.PACK_PATHS, main_mod._runtime_namespace())
    reg = M.FromContextGetConstructors(rt.graph)()
    rules = rt.flat_rules()
    check('audit loads every registered pack, not only the old two', len(loaded.packs) == len(main_mod.PACK_PATHS) and len(loaded.packs) > 2)
    check('withdrawn quartic pack is not present', not os.path.exists(os.path.join(REPO, 'packs', 'flt-quartic.pack.yaml')))

    def take(result):
        nonlocal reg
        reg = M.Head(M.Tail(result)())()
        return M.Head(result)()

    def nat(n):
        return take(M.NatFromRep(M.GMPRep(str(n)), reg)())

    def same_number(a, b):
        return M.NatEq(a, b, reg)() is M.truth_value

    add = lambda a, b: fact(L.ExprAddLabel, a, b)
    mul = lambda a, b: fact(L.ExprMulLabel, a, b)
    pw = lambda a, n: fact(L.ExprPowLabel, a, n)
    four = nat(4)
    process, measure = M.Char('w29-primitive-solutions'), M.Char('w29-size')
    every = fact(L.EveryStateMovesLabel, process)
    every_goal = P.Knowledge(chain(every))()
    no_states_goal = P.Knowledge(chain(fact(L.NoStatesLabel, process)))()
    x, y, z = M.Char('x'), M.Char('y'), M.Char('z')
    # A symbolic hypothesis, not an asserted numeric counterexample or a rule.
    source_equation = fact(L.ExprEqLabel, add(pw(x, four), pw(y, four)), pw(z, M.two))
    strategy_hypotheses = chain(fact(L.MonovariantLabel, process, measure),
        fact(L.AllMovesDecreaseLabel, process, measure), fact(L.BoundedBelowLabel, measure, M.Zero))
    source_facts = M.Pair(source_equation, M.Pair(fact(L.CoprimeLabel, x, y),
        M.Pair(fact(L.PositiveLabel, x), M.Pair(fact(L.PositiveLabel, y), strategy_hypotheses))))
    source_start = P.Knowledge(source_facts)()
    check('symbolic source hypotheses do not smuggle EveryStateMoves', contains_symbol(source_start, L.EveryStateMovesLabel, reg) is M.false_value)

    print('[1] W21: allocating witnesses is not solving arithmetic constraints', flush=True)
    vx = M.Pair(M.VarTag, chain(M.Var()))
    vy = M.Pair(M.VarTag, chain(M.Var()))
    opaque_relation = M.Thingy()
    template = fact(opaque_relation, vx, vy)
    minted = GT.MintUnboundWitnesses(template)()
    ground, bindings = M.Head(minted)(), M.Tail(minted)()
    u, v = field(ground, 0), field(ground, 1)
    check('witness allocation removes unbound variables', P.ContainsVar(ground)() is M.false_value)
    check('two unbound variables obtain distinct handles', M.IdentityCompare(u, v)() is M.false_value)
    check('witness introductions are recorded', bindings is not M.EmptyList)
    second_mint = M.Head(GT.MintUnboundWitnesses(template)())()
    check('another introduction does not reuse the handles', M.Compare(ground, second_mint)() is M.false_value)
    check('fresh handles are not natural arithmetic witnesses', A.IsNat(u, reg)() is M.false_value and A.IsNat(v, reg)() is M.false_value)
    check('subtraction cannot ground an anonymous witness', take(A.NatSubtract(u, M.Zero, reg)()) is M.EmptyList)
    check('gcd cofactors cannot ground anonymous witnesses', take(A.CoprimeCofactors(u, v, reg)()) is M.EmptyList)
    check('minting introduces no universal move assertion', contains_symbol(ground, L.EveryStateMovesLabel, reg) is M.false_value)

    print('[2] W22: the W6 identities now have checked grid derivations', flush=True)
    p, n = M.Char('p'), M.Char('n')
    left = add(pw(p, M.two), mul(mul(four, add(p, pw(n, M.two))), pw(n, M.two)))
    right = pw(add(p, mul(M.two, pw(n, M.two))), M.two)
    grid_rules = chain(L.PolynomialGridRuleLabel)
    for lhs, rhs, variables, name in (
        (left, right, chain(p, n), 'additive square identity'),
        (pw(x, four), pw(pw(x, M.two), M.two), chain(x), 'power composition identity'),
    ):
        result = PG.PolynomialGridDerivation(lhs, rhs, variables, reg)()
        record = M.Head(result)()
        proof = M.Head(M.Tail(result)())()
        reg = M.Head(M.Tail(M.Tail(result)())())()
        check(name + ': grid verdict true', field(record, 5) is M.truth_value)
        check(name + ': Checker B verifies the certificate', M.Head(CB.VerifyDerivation(proof, lhs, rhs, grid_rules, reg)())() is L.DerivationVerifiedLabel)
        check(name + ': the same proof does not certify EveryStateMoves', M.Head(CB.VerifyDerivation(proof, lhs, every_goal, grid_rules, reg)())() is L.GoalMismatchLabel)
    check('legacy symbolic normalisation remains a distinct missing ability', Inv.RewriteEquals(left, right, RR.build_default_rewrite_rule_chain(), reg)() is M.false_value)

    print('[3] W23: gcd extraction is not a square-root existence derivation', flush=True)
    # Concrete inputs are test data only. They are not a universal square lemma.
    a, b = nat(4), nat(9)
    product = take(A.Multiply(a, b, reg)())
    square = take(A.Multiply(nat(6), nat(6), reg)())
    check('positive control has a square product', same_number(product, square))
    record = take(A.CoprimeCofactors(a, b, reg)())
    check('cofactor extraction is available', M.Head(record)() is L.CoprimeCofactorsLabel)
    check('coprime inputs keep gcd one', same_number(field(record, 2), M.one))
    check('cofactors remain 4 and 9, not extracted roots 2 and 3', same_number(field(record, 3), a) and same_number(field(record, 4), b))
    check('cofactor record contains no existential root assertion', contains_symbol(record, L.ExistsLabel, reg) is M.false_value)
    decoy = take(A.CoprimeCofactors(nat(2), nat(8), reg)())
    check('noncoprime square-product decoy retains gcd two', same_number(field(decoy, 2), M.two))

    print('[4] W23: concrete measure retry exposes endpoint value/identity mismatch', flush=True)
    # The smallest coprime opposite-parity parameter pair used in W6. This is
    # a human-selected arithmetic instance, NOT a discovered parametrisation.
    aa, bb = M.two, M.one
    aa2 = take(A.Multiply(aa, aa, reg)())
    bb2 = take(A.Multiply(bb, bb, reg)())
    smaller_measure = take(A.Add(aa2, bb2, reg)())
    ab = take(A.Multiply(aa, bb, reg)())
    twice_ab = take(A.Add(ab, ab, reg)())
    small_squared = take(A.Multiply(smaller_measure, smaller_measure, reg)())
    leg_squared = take(A.Multiply(twice_ab, twice_ab, reg)())
    larger_measure = take(A.Add(small_squared, leg_squared, reg)())
    gap = take(A.NatSubtract(larger_measure, smaller_measure, reg)())
    check('candidate measures are computed as 5 and 41', same_number(smaller_measure, nat(5)) and same_number(larger_measure, nat(41)))
    check('the gap is computed, not authored as an order premise', same_number(gap, nat(36)))
    check('machine comparison sees 5<41, but this verdict is not a derivation', M.NatLess(smaller_measure, larger_measure, reg)() is M.truth_value)
    # Retry even the immediate-predecessor decrease of this computed upper
    # measure. No expensive full successor chain is needed to expose the
    # grounding/transport failure; the family-wide decrease remains evidence.
    predecessor_record = take(A.NatPredecessorFact(larger_measure, reg)())
    predecessor = field(predecessor_record, 0)
    canonical_predecessor = take(A.NatSubtract(larger_measure, M.one, reg)())
    check('predecessor adapter and subtraction agree by NatEq', same_number(predecessor, canonical_predecessor))
    check('both predecessor values are 40', same_number(predecessor, nat(40)))
    check('but predecessor and arithmetic endpoint are distinct atoms', M.IdentityCompare(predecessor, canonical_predecessor)() is M.false_value)
    order_pack = loaded.by_name('nat-order')
    successor_rule = order_pack.rule_map['successor_strict_order']
    matched = M.Match(P.RulePattern(successor_rule)(), predecessor_record)()
    check('generic successor schema matches the computed fact', M.Head(matched)() is M.truth_value)
    order_plan = chain(P.TheoremAction(successor_rule, M.Tail(matched)())())
    order_start = P.Knowledge(chain(predecessor_record))()
    order_goal = P.Knowledge(chain(fact(L.NatLessLabel, predecessor, larger_measure)))()
    order_proof = take(P.BuildDerivation(order_start, order_plan, reg)())
    check('Checker B verifies the predecessor-endpoint order fact', M.Head(CB.VerifyDerivation(order_proof, order_start, order_goal, order_pack.rule_chain, reg)())() is L.DerivationVerifiedLabel)
    exact_order_goal = P.Knowledge(chain(fact(L.NatLessLabel, canonical_predecessor, larger_measure)))()
    check('same proof does not cover the independently computed endpoint', M.Head(CB.VerifyDerivation(order_proof, order_start, exact_order_goal, order_pack.rule_chain, reg)())() is L.GoalMismatchLabel)
    backwards = P.Knowledge(chain(fact(L.NatLessLabel, larger_measure, predecessor)))()
    check('same predecessor proof cannot establish reversed order', M.Head(CB.VerifyDerivation(order_proof, order_start, backwards, order_pack.rule_chain, reg)())() is L.GoalMismatchLabel)
    check('predecessor proof cannot establish universal movement', M.Head(CB.VerifyDerivation(order_proof, order_start, every_goal, order_pack.rule_chain, reg)())() is L.GoalMismatchLabel)

    print('[5] Full registered-rule audit: the universal conclusion has no producer', flush=True)
    audited = 0
    every_producers = 0
    exists_producers = 0
    cursor = rules
    while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
        replacement = P.RuleReplacement(M.Head(cursor)())()
        if contains_symbol(replacement, L.EveryStateMovesLabel, reg) is M.truth_value:
            every_producers += 1
        if contains_symbol(replacement, L.ExistsLabel, reg) is M.truth_value:
            exists_producers += 1
        audited += 1  # harness measurement, never a machine quantity
        cursor = M.Tail(cursor)()
    expected_rules = sum(len(pack.rule_map) for pack in loaded.packs)
    check('every loaded raw rule was audited', audited == expected_rules and audited > 0)
    check('no replacement contains EveryStateMoves (not merely a fuel timeout)', every_producers == 0)
    check('no registered knowledge rule constructs an Exists fact either', exists_producers == 0)
    print('AUDIT: %d packs / %d rules / %d EveryStateMoves producers / %d Exists producers' % (len(loaded.packs), audited, every_producers, exists_producers), flush=True)
    # Ordinary forward rewriting substitutes start subterms or fresh handles;
    # it cannot invent this absent label from these replacement templates.
    # This is a structural obstruction in this rule set, not a formal theorem
    # of unprovability across arbitrary tactics, planner methods or future code.
    closure = GT.ForwardDeriveFacts(source_facts, rules, M.one, reg)()
    check('full-rule forward smoke retry does not introduce the movement label', contains_symbol(closure, L.EveryStateMovesLabel, reg) is M.false_value)
    check('full-rule one-step search does not find the missing universal', take(D.SearchKnowledgeDerivation(source_start, every_goal, rules, M.one, reg)()) is M.EmptyList)
    root_obligation = P.Knowledge(chain(fact(L.ExistsLabel,
        chain(fact(L.ExprEqLabel, pw(vx, M.two), a), fact(L.ExprEqLabel, pw(vy, M.two), b)))))()
    arithmetic_facts = chain(record, fact(L.ExprEqLabel, mul(a, b), square))
    check('cofactor-plus-square-product one-step retry does not solve root existence', take(D.SearchKnowledgeDerivation(P.Knowledge(arithmetic_facts)(), root_obligation, rules, M.one, reg)()) is M.EmptyList)

    print('[6] The descent skeleton remains conditional; receipt scope cannot be erased', flush=True)
    monovariant_rule = loaded.by_name('engel-strategies').rule_map['monovariant_terminates']
    descent_rule = loaded.by_name('infinite-descent').rule_map['infinite_descent']
    strategy_rules = chain(monovariant_rule, descent_rule)
    conditional_facts = M.Pair(every, strategy_hypotheses)
    conditional_start = P.Knowledge(conditional_facts)()
    skeleton = take(D.SearchKnowledgeDerivation(conditional_start, no_states_goal, strategy_rules, M.two, reg)())
    check('the explicitly conditional skeleton still has a derivation', skeleton is not M.EmptyList)
    check('Checker B verifies only that conditional implication', M.Head(CB.VerifyDerivation(skeleton, conditional_start, no_states_goal, strategy_rules, reg)())() is L.DerivationVerifiedLabel)
    without_every = P.Knowledge(strategy_hypotheses)()
    check('remove EveryStateMoves and the skeleton no longer closes', take(D.SearchKnowledgeDerivation(without_every, no_states_goal, strategy_rules, M.three, reg)()) is M.EmptyList)
    session = M.Char('w29-conditional-only')
    receipt = fact(L.ProofReceiptLabel, session, conditional_start, no_states_goal, skeleton)
    policy = fact(L.CheckPolicyLabel, session, conditional_start, no_states_goal)
    check('conditional receipt verifies in its original policy', M.Head(CB.VerifyProofReceipt(receipt, policy, strategy_rules, reg)())() is L.DerivationVerifiedLabel)
    unconditional_policy = fact(L.CheckPolicyLabel, session, without_every, no_states_goal)
    check('conditional receipt cannot be relabelled as unconditional', M.Head(CB.VerifyProofReceipt(receipt, unconditional_policy, strategy_rules, reg)())() is L.PremiseMismatchLabel)

    print('[7] The actual missing claim and an attempted skeleton replay are refused by promotion', flush=True)
    ledger = Ledger.EmptyPromotionLedger(reg)()
    zero_cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
    skeleton_plan = chain(P.TheoremAction(monovariant_rule)(), P.TheoremAction(descent_rule)())
    for name, start, goal, candidate_plan in (
        ('missing-universal', source_start, every_goal, M.EmptyList),
        ('missing-premise-skeleton', without_every, no_states_goal, skeleton_plan),
    ):
        candidate = Eval.CandidateMacro(M.Char(name), start, goal, candidate_plan)()
        verdict = Eval.EvaluateCandidateProof(candidate, start, goal, rules, reg)()
        check(name + ': evaluator refuses with GoalMismatch', M.Head(verdict)() is L.GoalMismatchLabel)
        promotion = Ledger.SubmitCandidateForPromotion(ledger, candidate, L.ProofSchemaPromotionLabel,
            start, goal, zero_cost, M.EmptyList, M.EmptyList, rules, reg)()
        check(name + ': ledger refuses, not a simulated promotion', M.Head(promotion)() is L.PromotionRejectedLabel)
        check(name + ': stated rejection reason is GoalMismatch', M.Head(M.Tail(promotion)())() is L.GoalMismatchLabel)
    check('ledger remains at version zero', same_number(Ledger.PromotionLedgerVersion(ledger)(), M.Zero))
    check('no active domain promotion was added', Ledger.QueryActivePromotions(ledger, L.ProofSchemaPromotionLabel, reg)() is M.EmptyList)

    print('TEST 41: %d/%d checks passed (%.1fs).' % (checks, checks, time.monotonic() - t0), flush=True)
    print('W29 OUTCOME: PRECISE NEGATIVE. EveryStateMoves remains undischarged; ledger version 0.', flush=True)
    print('Available: handle allocation, verified grid identities, gcd extraction, one computed predecessor order fact.', flush=True)
    print('Missing: arithmetic witness solving, parametrisation completeness, coprime-square-factor proof,', flush=True)
    print('value-equality transport for order facts, and a verified construction/coverage argument', flush=True)
    print('linking each source solution to a smaller solution.', flush=True)
    print('No quartic rule, square lemma, parameterisation or domain constant was authored into a rule.', flush=True)


if __name__ == '__main__':
    main()
