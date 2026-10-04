"""Canonical encoding and content digests for checker A records."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .model import (
    Application,
    Atom,
    CandidateScope,
    ProofReceipt,
    ProofStep,
    RuleSpec,
    Term,
    TrustedRuleSet,
    Variable,
)


def term_data(term: Term) -> dict[str, Any]:
    if isinstance(term, Atom):
        return {"atom": term.name}
    if isinstance(term, Variable):
        return {"var": term.name}
    if isinstance(term, Application):
        return {
            "app": {
                "head": term_data(term.head),
                "args": [term_data(argument) for argument in term.arguments],
            }
        }
    raise TypeError(f"unsupported term type: {type(term).__name__}")


def rule_data(rule: RuleSpec) -> dict[str, Any]:
    return {
        "id": rule.rule_id,
        "premises": [term_data(term) for term in rule.premises],
        "conclusion": term_data(rule.conclusion),
    }


def ruleset_data(ruleset: TrustedRuleSet) -> dict[str, Any]:
    # Rule order has no logical meaning. Sorting makes independently assembled
    # snapshots agree while duplicate IDs remain visible to validation.
    return {"rules": [rule_data(rule) for rule in sorted(ruleset.rules, key=lambda item: item.rule_id)]}


def step_data(step: ProofStep) -> dict[str, Any]:
    return {
        "rule_id": step.rule_id,
        "premise_refs": list(step.premise_refs),
        "conclusion": term_data(step.conclusion),
    }


def candidate_scope_data(scope: CandidateScope | None) -> dict[str, Any] | None:
    if scope is None:
        return None
    return {
        "candidate_id": scope.candidate_id,
        "session_id": scope.session_id,
        "ruleset_digest": scope.ruleset_digest,
    }


def proof_data(receipt: ProofReceipt) -> dict[str, Any]:
    return {
        "session_id": receipt.session_id,
        "ruleset_digest": receipt.ruleset_digest,
        "goal": term_data(receipt.goal),
        "premises": [term_data(term) for term in receipt.premises],
        "steps": [step_data(step) for step in receipt.steps],
        "final_ref": receipt.final_ref,
        "candidate_scope": candidate_scope_data(receipt.candidate_scope),
    }


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest_data(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def term_digest(term: Term) -> str:
    return digest_data(term_data(term))


def ruleset_digest(ruleset: TrustedRuleSet) -> str:
    return digest_data(ruleset_data(ruleset))


def proof_digest(receipt: ProofReceipt) -> str:
    return digest_data(proof_data(receipt))
