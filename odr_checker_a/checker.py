"""Independent, deterministic verifier for expanded first-order proofs.

This module deliberately does not import CTM proof search, planner, packs, or
candidate-generation code.  It checks only an inert trusted-rule snapshot and
an expanded receipt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Set

from .canonical import proof_digest, ruleset_digest, term_digest
from .model import (
    Application,
    Atom,
    CheckPolicy,
    CheckerReceipt,
    ConcreteTerm,
    ProofReceipt,
    RuleSpec,
    Term,
    TrustedRuleSet,
    Variable,
)

CHECKER_ID = "ctm-odr-checker-a/v1"


@dataclass(frozen=True, slots=True)
class _Failure:
    code: str
    message: str


def _walk(term: Term) -> Iterable[Term]:
    yield term
    if isinstance(term, Application):
        for argument in term.arguments:
            yield from _walk(argument)


def _is_well_formed(term: Term, *, variables_allowed: bool) -> bool:
    for item in _walk(term):
        if isinstance(item, Atom):
            if not item.name:
                return False
        elif isinstance(item, Variable):
            if not variables_allowed or not item.name:
                return False
        elif isinstance(item, Application):
            if not isinstance(item.head, Atom) or not item.head.name:
                return False
        else:
            return False
    return True


def _variables(term: Term) -> Set[str]:
    return {item.name for item in _walk(term) if isinstance(item, Variable)}


def _validate_ruleset(ruleset: TrustedRuleSet) -> Optional[_Failure]:
    identifiers: Set[str] = set()
    for rule in ruleset.rules:
        if not rule.rule_id:
            return _Failure("RULESET_INVALID", "trusted rule has an empty identifier")
        if rule.rule_id in identifiers:
            return _Failure("RULESET_INVALID", f"duplicate trusted rule identifier: {rule.rule_id}")
        identifiers.add(rule.rule_id)
        for premise in rule.premises:
            if not _is_well_formed(premise, variables_allowed=True):
                return _Failure("RULESET_INVALID", f"malformed premise in trusted rule: {rule.rule_id}")
        if not _is_well_formed(rule.conclusion, variables_allowed=True):
            return _Failure("RULESET_INVALID", f"malformed conclusion in trusted rule: {rule.rule_id}")
        premise_variables: Set[str] = set()
        for premise in rule.premises:
            premise_variables.update(_variables(premise))
        unbound = _variables(rule.conclusion) - premise_variables
        if unbound:
            names = ", ".join(sorted(unbound))
            return _Failure(
                "RULESET_INVALID",
                f"trusted rule {rule.rule_id} has conclusion-only variables: {names}",
            )
    return None


def _match(pattern: Term, concrete: ConcreteTerm, bindings: Dict[str, ConcreteTerm]) -> bool:
    if isinstance(pattern, Variable):
        previous = bindings.get(pattern.name)
        if previous is None:
            bindings[pattern.name] = concrete
            return True
        return previous == concrete
    if isinstance(pattern, Atom):
        return pattern == concrete
    if not isinstance(pattern, Application) or not isinstance(concrete, Application):
        return False
    if pattern.head != concrete.head or len(pattern.arguments) != len(concrete.arguments):
        return False
    return all(
        _match(pattern_arg, concrete_arg, bindings)
        for pattern_arg, concrete_arg in zip(pattern.arguments, concrete.arguments)
    )


def _instantiate(pattern: Term, bindings: Mapping[str, ConcreteTerm]) -> ConcreteTerm | None:
    if isinstance(pattern, Variable):
        return bindings.get(pattern.name)
    if isinstance(pattern, Atom):
        return pattern
    if isinstance(pattern, Application):
        arguments = []
        for argument in pattern.arguments:
            instantiated = _instantiate(argument, bindings)
            if instantiated is None:
                return None
            arguments.append(instantiated)
        return Application(pattern.head, tuple(arguments))
    return None


def _receipt(
    accepted: bool,
    code: str,
    message: str,
    proof: ProofReceipt,
    checked_steps: int,
) -> CheckerReceipt:
    try:
        goal_hash = term_digest(proof.goal)
        proof_hash = proof_digest(proof)
    except (TypeError, ValueError):
        goal_hash = "INVALID"
        proof_hash = "INVALID"
    return CheckerReceipt(
        accepted=accepted,
        code=code,
        message=message,
        checked_goal_digest=goal_hash,
        ruleset_digest=proof.ruleset_digest,
        proof_digest=proof_hash,
        checked_steps=checked_steps,
        checker_id=CHECKER_ID,
    )


def _reject(code: str, message: str, proof: ProofReceipt, checked_steps: int = 0) -> CheckerReceipt:
    return _receipt(False, code, message, proof, checked_steps)


def check_proof(
    proof: ProofReceipt,
    trusted_rules: TrustedRuleSet,
    policy: CheckPolicy | None = None,
) -> CheckerReceipt:
    """Check an expanded proof without invoking any proof-producing component.

    Candidate-bearing receipts require an evaluator-owned ``CheckPolicy`` so
    the producer cannot admit its own candidate merely by naming the current
    session in the receipt.
    """

    ruleset_failure = _validate_ruleset(trusted_rules)
    if ruleset_failure is not None:
        return _reject(ruleset_failure.code, ruleset_failure.message, proof)

    actual_ruleset_digest = ruleset_digest(trusted_rules)
    if proof.ruleset_digest != actual_ruleset_digest:
        return _reject("RULESET_DIGEST_MISMATCH", "proof names a different trusted ruleset", proof)
    if policy is None:
        return _reject(
            "MISSING_CHECK_POLICY",
            "proof lacks evaluator-owned task and admission policy",
            proof,
        )
    if not proof.session_id:
        return _reject("INVALID_SESSION", "proof session identifier is empty", proof)
    if not policy.session_id:
        return _reject("INVALID_CHECK_POLICY", "admitted session identifier is empty", proof)
    if len(set(policy.admitted_candidate_ids)) != len(policy.admitted_candidate_ids):
        return _reject("INVALID_CHECK_POLICY", "admitted candidate identifiers are duplicated", proof)
    if any(not candidate_id for candidate_id in policy.admitted_candidate_ids):
        return _reject("INVALID_CHECK_POLICY", "an admitted candidate identifier is empty", proof)
    if not _is_well_formed(policy.goal, variables_allowed=False):
        return _reject("INVALID_CHECK_POLICY", "admitted goal is not concrete", proof)
    if any(not _is_well_formed(item, variables_allowed=False) for item in policy.premises):
        return _reject("INVALID_CHECK_POLICY", "an admitted premise is not concrete", proof)
    if proof.session_id != policy.session_id:
        return _reject("PROOF_SESSION_MISMATCH", "proof belongs to another admitted session", proof)
    if proof.goal != policy.goal:
        return _reject("TASK_GOAL_MISMATCH", "proof goal differs from the evaluator-owned task", proof)
    if proof.premises != policy.premises:
        return _reject("TASK_PREMISES_MISMATCH", "proof premises differ from the evaluator-owned task", proof)
    if not _is_well_formed(proof.goal, variables_allowed=False):
        return _reject("NON_CONCRETE_GOAL", "goal is malformed or contains a variable", proof)
    for index, premise in enumerate(proof.premises):
        if not _is_well_formed(premise, variables_allowed=False):
            return _reject(
                "NON_CONCRETE_PREMISE",
                f"declared premise p{index} is malformed or contains a variable",
                proof,
            )

    scope = proof.candidate_scope
    if scope is None:
        if policy is not None and policy.require_candidate_scope:
            return _reject("CANDIDATE_SCOPE_REQUIRED", "the admitted run requires candidate provenance", proof)
    else:
        if policy is None:
            return _reject(
                "MISSING_CHECK_POLICY",
                "candidate-bearing proof lacks evaluator-owned admission policy",
                proof,
            )
        if not scope.candidate_id:
            return _reject("INVALID_CANDIDATE_SCOPE", "candidate identifier is empty", proof)
        if scope.candidate_id not in policy.admitted_candidate_ids:
            return _reject("CANDIDATE_NOT_ADMITTED", "candidate is not admitted by the evaluator", proof)
        if scope.session_id != proof.session_id:
            return _reject("CANDIDATE_SESSION_MISMATCH", "candidate belongs to another session", proof)
        if scope.ruleset_digest != actual_ruleset_digest:
            return _reject("CANDIDATE_RULESET_MISMATCH", "candidate was sealed for another ruleset", proof)

    rules = {rule.rule_id: rule for rule in trusted_rules.rules}
    available: Dict[str, ConcreteTerm] = {
        f"p{index}": premise for index, premise in enumerate(proof.premises)
    }

    for index, step in enumerate(proof.steps):
        step_ref = f"s{index}"
        if not _is_well_formed(step.conclusion, variables_allowed=False):
            return _reject(
                "NON_CONCRETE_CONCLUSION",
                f"step {step_ref} conclusion is malformed or contains a variable",
                proof,
                index,
            )
        rule = rules.get(step.rule_id)
        if rule is None:
            return _reject(
                "UNKNOWN_RULE",
                f"step {step_ref} names untrusted rule: {step.rule_id}",
                proof,
                index,
            )
        if len(step.premise_refs) != len(rule.premises):
            return _reject(
                "PREMISE_COUNT_MISMATCH",
                f"step {step_ref} supplies {len(step.premise_refs)} references; rule requires {len(rule.premises)}",
                proof,
                index,
            )

        bindings: Dict[str, ConcreteTerm] = {}
        for premise_index, (pattern, reference) in enumerate(zip(rule.premises, step.premise_refs)):
            concrete = available.get(reference)
            if concrete is None:
                return _reject(
                    "UNAVAILABLE_PREMISE",
                    f"step {step_ref} premise {premise_index} references unavailable fact: {reference}",
                    proof,
                    index,
                )
            if not _match(pattern, concrete, bindings):
                return _reject(
                    "PREMISE_PATTERN_MISMATCH",
                    f"step {step_ref} premise {premise_index} does not match rule {rule.rule_id}",
                    proof,
                    index,
                )

        expected = _instantiate(rule.conclusion, bindings)
        if expected is None:
            return _reject(
                "UNBOUND_CONCLUSION_VARIABLE",
                f"step {step_ref} leaves a conclusion variable unbound",
                proof,
                index,
            )
        if expected != step.conclusion:
            return _reject(
                "CONCLUSION_MISMATCH",
                f"step {step_ref} conclusion is not the instantiated rule conclusion",
                proof,
                index,
            )
        available[step_ref] = step.conclusion

    final = available.get(proof.final_ref)
    if final is None:
        return _reject(
            "UNAVAILABLE_FINAL_REFERENCE",
            f"final reference is unavailable: {proof.final_ref}",
            proof,
            len(proof.steps),
        )
    if final != proof.goal:
        return _reject(
            "FOREIGN_GOAL",
            "final derived term does not equal the requested goal",
            proof,
            len(proof.steps),
        )
    return _receipt(True, "ACCEPTED", "expanded proof is valid", proof, len(proof.steps))
