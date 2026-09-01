"""In-repo self-tests for the provenance/origin/policy/audit instrument.

The harness here is host I/O (asserts, a main entry) like the other
*_selftest modules; every value under test is a machine term produced by
machine edges. No theorem or benchmark is named; tests exercise the
machinery generically with stand-in rule atoms.

    LearningModeExcludesDemoRulesTest
    ColdPolicyForbidsCachesAndDemoTest
    RuleOriginRoundTripTest
    ProofAuditClassifiesSourceTest
"""
from __future__ import annotations

from . import machine as M
from . import proof as P
from . import provenance as Prov


def _check(name, condition):
    if condition is not M.truth_value:
        raise AssertionError(name + ": expected truth_value")
    return name + ": ok"


def _rule(label_text):
    # A minimal stand-in "rule": a single fact-like term (Pair(Char, args)).
    label = M.Char(label_text)
    return M.Pair(label, M.EmptyList)


def source_freeze_test():
    """SourceFreezeTest: a learning-instrument transaction mutates only
    graph/checkpoint state, never executable source.

    Hashes every package .py file, runs the machine operations a lesson
    performs on checkpoint state (tag origins, set the cold policy, filter
    rules, build an audit, record provenance), then re-hashes and requires
    every file identical. Host code here only reads files and asserts.
    """
    import hashlib
    import os

    import cat_theo_machine as pkg
    pkg_dir = os.path.dirname(pkg.__file__)

    def hash_sources():
        digest_map = {}
        for entry in sorted(os.listdir(pkg_dir)):
            if not entry.endswith(".py"):
                continue
            path = os.path.join(pkg_dir, entry)
            with open(path, "rb") as stream:
                digest_map[entry] = hashlib.sha256(stream.read()).hexdigest()
        return digest_map

    before = hash_sources()

    # Machine-only state change: the operations a live lesson performs on
    # the checkpoint (no source file is opened for writing).
    registry = M.AllConstructors
    g_origins = Prov.RuleOriginTreeEmpty()()
    learned_rule = _rule("learned-rule")
    demo_rule = _rule("demo-rule")
    g_origins = Prov.TagRuleOrigin(g_origins, learned_rule, Prov.LearnedTag)()
    g_origins = Prov.TagRuleOrigin(g_origins, demo_rule,
                                   Prov.DemoSpecializedTag)()
    policy = Prov.ColdLearningPolicy()()
    chain = M.Pair(learned_rule, M.Pair(demo_rule, M.EmptyList))
    kept = Prov.FilterRulesByPolicy(chain, g_origins, policy, registry)()
    n = M.GMPRepText(Prov.CountChain(kept)())()
    audit = Prov.BuildProofAudit(
        policy, g_origins, kept, M.GMPRep("2"), M.GMPRep("2"),
        M.false_value, M.false_value, M.false_value, M.truth_value,
        registry)()
    _ = Prov.ProofAuditText(audit, registry)()
    assert n == "1", "cold policy must drop the demo-specialized rule"

    after = hash_sources()
    assert before == after, "source changed during a learning transaction"
    return "SourceFreezeTest: ok (" + str(len(before)) + " .py files unchanged)"


def main():
    results = []
    registry = M.AllConstructors

    # --- Rule origin tag/lookup round trip -------------------------------
    r_demo = _rule("demo-rule")
    r_prim = _rule("prim-rule")
    r_taught = _rule("taught-rule")
    origins = Prov.RuleOriginTreeEmpty()()
    origins = Prov.TagRuleOrigin(origins, r_demo, Prov.DemoSpecializedTag)()
    origins = Prov.TagRuleOrigin(origins, r_prim, Prov.PrimitiveTag)()
    origins = Prov.TagRuleOrigin(origins, r_taught, Prov.TaughtTag)()

    results.append(_check(
        "RuleOriginRoundTripTest/demo",
        Prov.IsRuleOrigin(Prov.DemoSpecializedTag)()))
    od = Prov.LookupRuleOrigin(origins, r_demo, registry)()
    op = Prov.LookupRuleOrigin(origins, r_prim, registry)()
    ot = Prov.LookupRuleOrigin(origins, r_taught, registry)()
    results.append("demo lookup: " + od())
    results.append("prim lookup: " + op())
    results.append("taught lookup: " + ot())
    assert od() == "demo-specialized", od()
    assert op() == "primitive", op()
    assert ot() == "taught", ot()
    # An un-tagged rule defaults to primitive (safe admissible origin).
    assert Prov.LookupRuleOrigin(origins, _rule("untagged"), registry)()() == "primitive"

    # --- Cold policy forbids caches and demo; admits primitive/taught -----
    cold = Prov.ColdLearningPolicy()()
    results.append(_check("ColdPolicy/exact-cache-off",
        M.NotAtom(Prov.PolicyAllowExactCache(cold)())()))
    results.append(_check("ColdPolicy/comparison-off",
        M.NotAtom(Prov.PolicyAllowSearchComparison(cold)())()))
    results.append(_check("ColdPolicy/schema-off",
        M.NotAtom(Prov.PolicyAllowSchemaReplay(cold)())()))
    results.append(_check("ColdPolicy/demo-off",
        M.NotAtom(Prov.PolicyAllowDemoSpecializedRules(cold)())()))
    results.append(_check("ColdPolicy/taught-on",
        Prov.PolicyAllowTaughtRules(cold)()))
    results.append(_check("ColdPolicy/provenance-on",
        Prov.PolicyRecordProvenance(cold)()))

    default = Prov.DefaultProofPolicy()()
    results.append(_check("DefaultPolicy/exact-cache-on",
        Prov.PolicyAllowExactCache(default)()))
    results.append(_check("DefaultPolicy/demo-on",
        Prov.PolicyAllowDemoSpecializedRules(default)()))

    # --- FilterRulesByPolicy excludes demo under cold, keeps under default -
    rules = M.Pair(r_demo, M.Pair(r_prim, M.Pair(r_taught, M.EmptyList)))
    kept_cold = Prov.FilterRulesByPolicy(rules, origins, cold, registry)()
    n_cold = M.GMPRepText(Prov.CountChain(kept_cold)())()
    kept_default = Prov.FilterRulesByPolicy(rules, origins, default, registry)()
    n_default = M.GMPRepText(Prov.CountChain(kept_default)())()
    results.append("LearningModeExcludesDemoRulesTest: cold keeps "
                   + n_cold + " of " + n_default + " (1 demo dropped)")
    assert n_cold == "2", n_cold
    assert n_default == "3", n_default

    # --- ProofAudit classifies source honestly ---------------------------
    one = M.GMPRep("1"); three = M.GMPRep("3")
    # fresh search, no cache/comparison/demo, success
    audit_search = Prov.BuildProofAudit(
        cold, origins, M.Pair(r_prim, M.EmptyList),
        three, three, M.false_value, M.false_value, M.false_value,
        M.truth_value, registry)()
    text_search = Prov.ProofAuditText(audit_search, registry)()
    results.append("fresh-search audit:\n" + text_search)
    assert "Solved by fresh search" in text_search
    assert "demo-rule-used:      no" in text_search

    # exact cache hit under a permissive policy => disclosed as retrieval
    audit_cache = Prov.BuildProofAudit(
        default, origins, M.Pair(r_prim, M.EmptyList),
        one, one, M.truth_value, M.false_value, M.false_value,
        M.truth_value, registry)()
    text_cache = Prov.ProofAuditText(audit_cache, registry)()
    results.append("cache-hit audit:\n" + text_cache)
    assert "Solved by exact episodic retrieval" in text_cache
    assert "exact-cache-hit:     yes" in text_cache

    # a cache hit reported while the cold policy forbids it => masked to no
    audit_masked = Prov.BuildProofAudit(
        cold, origins, M.Pair(r_prim, M.EmptyList),
        one, one, M.truth_value, M.false_value, M.false_value,
        M.truth_value, registry)()
    text_masked = Prov.ProofAuditText(audit_masked, registry)()
    results.append("cold-policy cache mask audit:\n" + text_masked)
    assert "exact-cache-hit:     no" in text_masked
    assert "Solved by fresh search" in text_masked

    # --- Promotion admission gates ---------------------------------------
    good = P.MultiRule(
        M.Pair(_rule("prem-a"), M.Pair(_rule("prem-b"), M.EmptyList)),
        _rule("conclusion-binds-its-vars"))()
    bad_empty = P.MultiRule(M.EmptyList, _rule("asserted-target"))()
    # Fresh-variable rule: a conclusion atom that no premise names. The
    # premise chain and conclusion are stand-in facts (Pair(Char, args)).
    fresh_atom = M.Char("fresh-conclusion-var")
    bad_fresh = P.MultiRule(
        M.Pair(M.Pair(M.Char("prem-only"), M.EmptyList), M.EmptyList),
        M.Pair(M.Char("conclusion-with-fresh"),
               M.Pair(fresh_atom, M.EmptyList)))()
    results.append(_check(
        "Promotion/nonempty-premise-good",
        Prov.RuleHasNoEmptyPremise(good)()))
    results.append(_check(
        "Promotion/empty-premise-rejected",
        M.NotAtom(Prov.RuleHasNoEmptyPremise(bad_empty)())()))
    gate_good = Prov.PromotionAdmissible(
        good, M.truth_value, M.truth_value, M.truth_value)()
    gate_no_cert = Prov.PromotionAdmissible(
        good, M.false_value, M.truth_value, M.truth_value)()
    gate_empty = Prov.PromotionAdmissible(
        bad_empty, M.truth_value, M.truth_value, M.truth_value)()
    results.append(_check("Promotion/good-passes", gate_good))
    results.append(_check(
        "Promotion/no-certificate-fails", M.NotAtom(gate_no_cert)()))
    results.append(_check(
        "Promotion/empty-premise-fails", M.NotAtom(gate_empty)()))

    # --- Counterfactual utility (section 5C) ------------------------------
    util_closes = Prov.CounterfactualUtility(
        M.false_value, M.truth_value, M.GMPRep("12"), M.GMPRep("7"))()
    util_useless = Prov.CounterfactualUtility(
        M.false_value, M.false_value, M.GMPRep("12"), M.GMPRep("12"))()
    util_cheaper = Prov.CounterfactualUtility(
        M.truth_value, M.truth_value, M.GMPRep("12"), M.GMPRep("7"))()
    util_notcheaper = Prov.CounterfactualUtility(
        M.truth_value, M.truth_value, M.GMPRep("7"), M.GMPRep("12"))()
    results.append(_check("Utility/closes-residual", util_closes))
    results.append(_check(
        "Utility/no-change-rejected", M.NotAtom(util_useless)()))
    results.append(_check("Utility/lower-cost", util_cheaper))
    results.append(_check(
        "Utility/higher-cost-rejected", M.NotAtom(util_notcheaper)()))

    report = "\n".join(results)
    print(report)
    print("\nPROVENANCE SELFTEST: all checks passed")
    return results


if __name__ == "__main__":
    main()
