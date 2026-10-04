from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
import unittest

from odr_checker_a import (
    Application,
    Atom,
    CandidateScope,
    CheckPolicy,
    ProofReceipt,
    ProofStep,
    RuleSpec,
    TrustedRuleSet,
    Variable,
    check_proof,
    proof_digest,
    ruleset_digest,
)


def atom(name: str) -> Atom:
    return Atom(name)


def app(head: str, *arguments) -> Application:
    return Application(atom(head), tuple(arguments))


X = Variable("x")
Y = Variable("y")
Z = Variable("z")

GRANDPARENT = RuleSpec(
    "grandparent",
    (
        app("parent", X, Y),
        app("parent", Y, Z),
    ),
    app("grandparent", X, Z),
)
ANCESTOR_BASE = RuleSpec(
    "ancestor_base",
    (app("parent", X, Y),),
    app("ancestor", X, Y),
)
ANCESTOR_STEP = RuleSpec(
    "ancestor_step",
    (
        app("ancestor", X, Y),
        app("parent", Y, Z),
    ),
    app("ancestor", X, Z),
)
RULESET = TrustedRuleSet((GRANDPARENT, ANCESTOR_BASE, ANCESTOR_STEP))
RULESET_DIGEST = ruleset_digest(RULESET)

ALICE = atom("alice")
BOB = atom("bob")
CAROL = atom("carol")
DAVE = atom("dave")
PARENT_AB = app("parent", ALICE, BOB)
PARENT_BC = app("parent", BOB, CAROL)
PARENT_CD = app("parent", CAROL, DAVE)
GRANDPARENT_AC = app("grandparent", ALICE, CAROL)
POLICY = CheckPolicy(
    "session-17",
    GRANDPARENT_AC,
    (PARENT_AB, PARENT_BC),
    ("candidate-4",),
    require_candidate_scope=True,
)


def valid_proof() -> ProofReceipt:
    return ProofReceipt(
        session_id="session-17",
        ruleset_digest=RULESET_DIGEST,
        goal=GRANDPARENT_AC,
        premises=(PARENT_AB, PARENT_BC),
        steps=(ProofStep("grandparent", ("p0", "p1"), GRANDPARENT_AC),),
        final_ref="s0",
        candidate_scope=CandidateScope("candidate-4", "session-17", RULESET_DIGEST),
    )


class CheckerAcceptanceTests(unittest.TestCase):
    def test_accepts_valid_expanded_proof(self):
        result = check_proof(valid_proof(), RULESET, POLICY)
        self.assertTrue(result.accepted)
        self.assertEqual(result.code, "ACCEPTED")
        self.assertEqual(result.checked_steps, 1)

    def test_accepts_valid_chained_proof(self):
        proof = ProofReceipt(
            session_id="session-chain",
            ruleset_digest=RULESET_DIGEST,
            goal=app("ancestor", ALICE, DAVE),
            premises=(PARENT_AB, PARENT_BC, PARENT_CD),
            steps=(
                ProofStep("ancestor_base", ("p0",), app("ancestor", ALICE, BOB)),
                ProofStep("ancestor_step", ("s0", "p1"), app("ancestor", ALICE, CAROL)),
                ProofStep("ancestor_step", ("s1", "p2"), app("ancestor", ALICE, DAVE)),
            ),
            final_ref="s2",
        )
        policy = CheckPolicy(
            "session-chain",
            proof.goal,
            proof.premises,
            require_candidate_scope=False,
        )
        result = check_proof(proof, RULESET, policy)
        self.assertTrue(result.accepted)
        self.assertEqual(result.checked_steps, 3)

    def test_receipts_and_digests_are_deterministic(self):
        proof = valid_proof()
        first = check_proof(proof, RULESET, POLICY)
        second = check_proof(proof, TrustedRuleSet(tuple(reversed(RULESET.rules))), POLICY)
        self.assertEqual(first, second)
        self.assertEqual(first.proof_digest, proof_digest(proof))


class CheckerMutationTests(unittest.TestCase):
    def assert_rejected(self, proof: ProofReceipt, code: str, ruleset=RULESET, policy=POLICY):
        result = check_proof(proof, ruleset, policy)
        self.assertFalse(result.accepted)
        self.assertEqual(result.code, code)

    def test_rejects_mutated_premise(self):
        proof = replace(valid_proof(), premises=(app("sibling", ALICE, BOB), PARENT_BC))
        self.assert_rejected(proof, "TASK_PREMISES_MISMATCH")

    def test_rejects_mutated_conclusion(self):
        bad_step = replace(valid_proof().steps[0], conclusion=app("grandparent", ALICE, DAVE))
        self.assert_rejected(replace(valid_proof(), steps=(bad_step,)), "CONCLUSION_MISMATCH")

    def test_rejects_wrong_repeated_variable_binding(self):
        bad_step = replace(valid_proof().steps[0], premise_refs=("p0", "p0"))
        self.assert_rejected(
            replace(valid_proof(), steps=(bad_step,)),
            "PREMISE_PATTERN_MISMATCH",
        )

    def test_rejects_fabricated_premise_reference(self):
        bad_step = replace(valid_proof().steps[0], premise_refs=("p0", "p99"))
        self.assert_rejected(replace(valid_proof(), steps=(bad_step,)), "UNAVAILABLE_PREMISE")

    def test_rejects_future_step_reference(self):
        bad_step = replace(valid_proof().steps[0], premise_refs=("p0", "s1"))
        self.assert_rejected(replace(valid_proof(), steps=(bad_step,)), "UNAVAILABLE_PREMISE")

    def test_rejects_goal_mutated_from_evaluator_task(self):
        proof = replace(valid_proof(), goal=app("grandparent", ALICE, DAVE))
        self.assert_rejected(proof, "TASK_GOAL_MISMATCH")

    def test_rejects_derivation_of_foreign_goal(self):
        foreign_goal = app("grandparent", ALICE, DAVE)
        proof = replace(valid_proof(), goal=foreign_goal)
        policy = replace(POLICY, goal=foreign_goal)
        self.assert_rejected(proof, "FOREIGN_GOAL", policy=policy)

    def test_rejects_unknown_candidate_macro_as_rule(self):
        bad_step = replace(valid_proof().steps[0], rule_id="candidate-4")
        self.assert_rejected(replace(valid_proof(), steps=(bad_step,)), "UNKNOWN_RULE")

    def test_rejects_wrong_candidate_session(self):
        scope = replace(valid_proof().candidate_scope, session_id="another-session")
        self.assert_rejected(replace(valid_proof(), candidate_scope=scope), "CANDIDATE_SESSION_MISMATCH")

    def test_rejects_candidate_without_evaluator_policy(self):
        result = check_proof(valid_proof(), RULESET)
        self.assertFalse(result.accepted)
        self.assertEqual(result.code, "MISSING_CHECK_POLICY")

    def test_rejects_candidate_not_admitted_by_evaluator(self):
        policy = replace(POLICY, admitted_candidate_ids=("some-other-candidate",))
        self.assert_rejected(valid_proof(), "CANDIDATE_NOT_ADMITTED", policy=policy)

    def test_rejects_proof_from_another_admitted_session(self):
        policy = replace(POLICY, session_id="session-18")
        self.assert_rejected(valid_proof(), "PROOF_SESSION_MISMATCH", policy=policy)

    def test_rejects_missing_candidate_scope_when_policy_requires_it(self):
        self.assert_rejected(
            replace(valid_proof(), candidate_scope=None),
            "CANDIDATE_SCOPE_REQUIRED",
        )

    def test_rejects_candidate_sealed_for_stale_ruleset(self):
        scope = replace(valid_proof().candidate_scope, ruleset_digest="sha256:stale")
        self.assert_rejected(replace(valid_proof(), candidate_scope=scope), "CANDIDATE_RULESET_MISMATCH")

    def test_rejects_stale_proof_ruleset(self):
        self.assert_rejected(
            replace(valid_proof(), ruleset_digest="sha256:stale"),
            "RULESET_DIGEST_MISMATCH",
        )

    def test_rejects_variable_in_concrete_conclusion(self):
        bad_step = replace(valid_proof().steps[0], conclusion=app("grandparent", X, CAROL))
        self.assert_rejected(replace(valid_proof(), steps=(bad_step,)), "NON_CONCRETE_CONCLUSION")

    def test_rejects_unbound_rule_conclusion_variable(self):
        unsafe = RuleSpec("unsafe", (app("parent", X, Y),), app("related", X, Z))
        ruleset = TrustedRuleSet((unsafe,))
        proof = replace(valid_proof(), ruleset_digest=ruleset_digest(ruleset), candidate_scope=None)
        self.assert_rejected(proof, "RULESET_INVALID", ruleset)

    def test_rejects_duplicate_rule_identifiers(self):
        duplicate = TrustedRuleSet((GRANDPARENT, GRANDPARENT))
        proof = replace(valid_proof(), ruleset_digest=ruleset_digest(duplicate))
        self.assert_rejected(proof, "RULESET_INVALID", duplicate)

    def test_rejects_wrong_number_of_premises(self):
        bad_step = replace(valid_proof().steps[0], premise_refs=("p0",))
        self.assert_rejected(replace(valid_proof(), steps=(bad_step,)), "PREMISE_COUNT_MISMATCH")

    def test_rejects_unavailable_final_reference(self):
        self.assert_rejected(replace(valid_proof(), final_ref="s99"), "UNAVAILABLE_FINAL_REFERENCE")


class IsolationTests(unittest.TestCase):
    def test_checker_package_has_no_proof_producing_imports(self):
        package = Path(__file__).resolve().parent
        forbidden_roots = {
            "search",
            "planner",
            "proof",
            "packs",
            "invariance",
            "researcher_v0",
        }
        violations = []
        for source_path in package.glob("*.py"):
            if source_path.name == "test_checker.py":
                continue
            tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    components = set(name.split("."))
                    if components & forbidden_roots:
                        violations.append(f"{source_path.name}: {name}")
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
