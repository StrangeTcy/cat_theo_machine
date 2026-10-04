from __future__ import annotations

from pathlib import Path
import unittest

from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine.odr_checker_a import check_proof, ruleset_digest
from cat_theo_machine.odr_ctm_adapter import (
    AdaptationError,
    CTMAdapter,
    ExpandedCTMStep,
    SymbolAuthority,
)


def chain(*items):
    result = M.EmptyList
    for item in reversed(items):
        result = M.Pair(item, result)
    return result


def call(head, *arguments):
    return M.Pair(head, chain(*arguments))


def variable(name: str):
    return M.Pair(M.VarTag, M.Pair(M.Char(name), M.EmptyList))


class AdapterFixture:
    def __init__(self):
        self.parent = M.Thingy()
        self.ancestor = M.Thingy()
        self.grandparent = M.Thingy()
        self.alice = M.Thingy()
        self.bob = M.Thingy()
        self.carol = M.Thingy()
        self.authority = SymbolAuthority.from_mapping(
            {
                "EmptyList": M.EmptyList,
                "Parent": self.parent,
                "Ancestor": self.ancestor,
                "Grandparent": self.grandparent,
                "alice": self.alice,
                "bob": self.bob,
                "carol": self.carol,
            }
        )
        self.adapter = CTMAdapter(self.authority)


class CTMAdapterTests(unittest.TestCase):
    def setUp(self):
        self.fixture = AdapterFixture()

    def test_adapts_real_ctm_rule_and_checks_expanded_proof(self):
        f = self.fixture
        x = variable("x")
        y = variable("y")
        pattern = call(f.parent, x, y)
        replacement = call(f.ancestor, x, y)
        ctm_rule = P.Rule(pattern, replacement)
        ruleset = f.adapter.adapt_ruleset((('parent_implies_ancestor', ctm_rule),))

        premise = call(f.parent, f.alice, f.bob)
        conclusion = call(f.ancestor, f.alice, f.bob)
        policy = f.adapter.adapt_policy(
            session_id="adapter-session",
            goal=conclusion,
            premises=(premise,),
            admitted_candidate_ids=("candidate-a",),
            require_candidate_scope=True,
        )
        proof = f.adapter.adapt_proof(
            session_id="adapter-session",
            trusted_rules=ruleset,
            goal=conclusion,
            premises=(premise,),
            steps=(ExpandedCTMStep("parent_implies_ancestor", ("p0",), conclusion),),
            final_ref="s0",
            candidate_id="candidate-a",
        )
        receipt = check_proof(proof, ruleset, policy)
        self.assertTrue(receipt.accepted, receipt)

    def test_preserves_repeated_variable_identity_in_multi_rule(self):
        f = self.fixture
        x = variable("x")
        y = variable("y")
        z = variable("z")
        premises = chain(call(f.parent, x, y), call(f.parent, y, z))
        ctm_rule = P.MultiRule(premises, call(f.grandparent, x, z))
        ruleset = f.adapter.adapt_ruleset((('grandparent', ctm_rule),))

        first = call(f.parent, f.alice, f.bob)
        second = call(f.parent, f.bob, f.carol)
        conclusion = call(f.grandparent, f.alice, f.carol)
        policy = f.adapter.adapt_policy(
            session_id="repeated-variable",
            goal=conclusion,
            premises=(first, second),
        )
        proof = f.adapter.adapt_proof(
            session_id="repeated-variable",
            trusted_rules=ruleset,
            goal=conclusion,
            premises=(first, second),
            steps=(ExpandedCTMStep("grandparent", ("p0", "p1"), conclusion),),
            final_ref="s0",
        )
        self.assertTrue(check_proof(proof, ruleset, policy).accepted)

        wrong_second = call(f.parent, f.carol, f.alice)
        wrong_goal = call(f.grandparent, f.alice, f.alice)
        wrong_policy = f.adapter.adapt_policy(
            session_id="wrong-binding",
            goal=wrong_goal,
            premises=(first, wrong_second),
        )
        wrong_proof = f.adapter.adapt_proof(
            session_id="wrong-binding",
            trusted_rules=ruleset,
            goal=wrong_goal,
            premises=(first, wrong_second),
            steps=(
                ExpandedCTMStep(
                    "grandparent",
                    ("p0", "p1"),
                    call(f.grandparent, f.alice, f.alice),
                ),
            ),
            final_ref="s0",
        )
        rejected = check_proof(wrong_proof, ruleset, wrong_policy)
        self.assertFalse(rejected.accepted)
        self.assertEqual(rejected.code, "PREMISE_PATTERN_MISMATCH")

    def test_rule_digest_is_stable_across_fresh_variable_objects(self):
        f = self.fixture

        def build_rule():
            x = variable("any-host-name")
            y = variable("another-host-name")
            return P.Rule(call(f.parent, x, y), call(f.ancestor, x, y))

        first = f.adapter.adapt_ruleset((('r', build_rule()),))
        second = f.adapter.adapt_ruleset((('r', build_rule()),))
        self.assertEqual(first, second)
        self.assertEqual(ruleset_digest(first), ruleset_digest(second))

    def test_distinct_char_atoms_with_same_value_have_same_encoding(self):
        f = self.fixture
        self.assertEqual(f.adapter.adapt_term(M.Char("same")), f.adapter.adapt_term(M.Char("same")))

    def test_rejects_unnamed_identity_sensitive_atom(self):
        with self.assertRaises(AdaptationError) as caught:
            self.fixture.adapter.adapt_term(M.Thingy())
        self.assertEqual(caught.exception.code, "UNNAMED_ATOM")

    def test_rejects_variable_in_concrete_task_term(self):
        with self.assertRaises(AdaptationError) as caught:
            self.fixture.adapter.adapt_term(variable("x"))
        self.assertEqual(caught.exception.code, "VARIABLE_NOT_ALLOWED")

    def test_rejects_improper_premise_chain(self):
        f = self.fixture
        bad_rule = P.MultiRule(M.Pair(call(f.parent, f.alice, f.bob), f.alice), call(f.ancestor, f.alice, f.bob))
        with self.assertRaises(AdaptationError) as caught:
            f.adapter.adapt_rule("bad", bad_rule)
        self.assertEqual(caught.exception.code, "IMPROPER_CHAIN")

    def test_rejects_ambiguous_symbol_authority(self):
        atom = M.Thingy()
        with self.assertRaises(AdaptationError) as caught:
            SymbolAuthority.from_mapping({"first": atom, "second": atom})
        self.assertEqual(caught.exception.code, "INVALID_SYMBOL_AUTHORITY")

    def test_adapts_rule_from_real_arithmetic_pack(self):
        from cat_theo_machine.main import _runtime_namespace
        from cat_theo_machine.runtime import boot_from_packs

        repository = Path(__file__).resolve().parents[1]
        namespace = _runtime_namespace()
        _runtime, packs = boot_from_packs(
            (str(repository / "packs" / "arithmetic.pack.yaml"),),
            namespace,
        )
        arithmetic = packs.by_name("arithmetic")
        adapter = CTMAdapter(SymbolAuthority.from_namespace(namespace))
        rule = adapter.adapt_rule(
            "arithmetic_add_commutes",
            arithmetic.rule_map["arithmetic_add_commutes"],
        )
        self.assertEqual(rule.rule_id, "arithmetic_add_commutes")
        self.assertEqual(len(rule.premises), 1)
        self.assertNotEqual(rule.premises[0], rule.conclusion)


if __name__ == "__main__":
    unittest.main()
