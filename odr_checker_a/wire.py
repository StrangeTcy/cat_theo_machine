"""Strict, bounded JSON wire format for independent checker A.

Decoding is deliberately separate from checking.  This module rejects schema
ambiguity, duplicate/unknown fields, excessive nesting, and oversized record
collections before constructing checker records.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence, TypeVar

from .canonical import canonical_bytes, term_data
from .model import (
    Application,
    Atom,
    CandidateScope,
    CheckPolicy,
    CheckerReceipt,
    ProofReceipt,
    ProofStep,
    RuleSpec,
    Term,
    TrustedRuleSet,
    Variable,
)

POLICY_SCHEMA = "ctm.odr.checker-a.task-policy.v1"
RULESET_SCHEMA = "ctm.odr.checker-a.trusted-rules.v1"
PROOF_SCHEMA = "ctm.odr.checker-a.proof-receipt.v1"
CHECKER_RECEIPT_SCHEMA = "ctm.odr.checker-a.checker-receipt.v1"

MAX_FILE_BYTES = 2_000_000
MAX_STRING_BYTES = 1_024
MAX_TERM_DEPTH = 128
MAX_TERM_NODES = 20_000
MAX_RULES = 5_000
MAX_RULE_PREMISES = 256
MAX_TASK_PREMISES = 10_000
MAX_STEPS = 10_000
MAX_STEP_PREMISES = 256
MAX_CANDIDATES = 1_000


class WireFormatError(ValueError):
    """A deterministic rejection of malformed or over-budget wire data."""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(slots=True)
class _TermBudget:
    nodes: int = 0


T = TypeVar("T")


def _fail(code: str, message: str) -> None:
    raise WireFormatError(code, message)


def _expect_object(value: Any, location: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        _fail("EXPECTED_OBJECT", f"{location} must be an object")
    return value


def _expect_exact_fields(value: Mapping[str, Any], fields: Iterable[str], location: str) -> None:
    expected = set(fields)
    actual = set(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        _fail("MISSING_FIELD", f"{location} is missing: {', '.join(missing)}")
    if unknown:
        _fail("UNKNOWN_FIELD", f"{location} contains: {', '.join(unknown)}")


def _expect_string(value: Any, location: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        _fail("EXPECTED_STRING", f"{location} must be a string")
    if nonempty and not value:
        _fail("EMPTY_STRING", f"{location} must not be empty")
    if len(value.encode("utf-8")) > MAX_STRING_BYTES:
        _fail("STRING_LIMIT", f"{location} exceeds {MAX_STRING_BYTES} UTF-8 bytes")
    return value


def _expect_bool(value: Any, location: str) -> bool:
    if type(value) is not bool:
        _fail("EXPECTED_BOOLEAN", f"{location} must be a boolean")
    return value


def _expect_nonnegative_int(value: Any, location: str, maximum: int) -> int:
    if type(value) is not int or value < 0:
        _fail("EXPECTED_NONNEGATIVE_INTEGER", f"{location} must be a non-negative integer")
    if value > maximum:
        _fail("INTEGER_LIMIT", f"{location} exceeds {maximum}")
    return value


def _expect_list(value: Any, location: str, limit: int) -> Sequence[Any]:
    if not isinstance(value, list):
        _fail("EXPECTED_ARRAY", f"{location} must be an array")
    if len(value) > limit:
        _fail("COLLECTION_LIMIT", f"{location} exceeds {limit} entries")
    return value


def _expect_schema(obj: Mapping[str, Any], expected: str, location: str) -> None:
    actual = _expect_string(obj.get("schema"), f"{location}.schema")
    if actual != expected:
        _fail("SCHEMA_MISMATCH", f"{location} schema is {actual!r}; expected {expected!r}")


def _term_from_data(
    value: Any,
    location: str,
    budget: _TermBudget,
    *,
    variables_allowed: bool,
    depth: int = 0,
) -> Term:
    if depth > MAX_TERM_DEPTH:
        _fail("TERM_DEPTH_LIMIT", f"{location} exceeds depth {MAX_TERM_DEPTH}")
    budget.nodes += 1
    if budget.nodes > MAX_TERM_NODES:
        _fail("TERM_NODE_LIMIT", f"document exceeds {MAX_TERM_NODES} term nodes")
    obj = _expect_object(value, location)
    if len(obj) != 1:
        _fail("INVALID_TERM", f"{location} must have exactly one term discriminator")
    if "atom" in obj:
        return Atom(_expect_string(obj["atom"], f"{location}.atom"))
    if "var" in obj:
        if not variables_allowed:
            _fail("VARIABLE_NOT_ALLOWED", f"{location} must be concrete")
        return Variable(_expect_string(obj["var"], f"{location}.var"))
    if "app" not in obj:
        _fail("INVALID_TERM", f"{location} has no recognized term discriminator")
    app_obj = _expect_object(obj["app"], f"{location}.app")
    _expect_exact_fields(app_obj, ("head", "args"), f"{location}.app")
    head = _term_from_data(
        app_obj["head"],
        f"{location}.app.head",
        budget,
        variables_allowed=False,
        depth=depth + 1,
    )
    if not isinstance(head, Atom):
        _fail("INVALID_TERM_HEAD", f"{location}.app.head must be an atom")
    args_data = _expect_list(app_obj["args"], f"{location}.app.args", MAX_RULE_PREMISES)
    arguments = tuple(
        _term_from_data(
            item,
            f"{location}.app.args[{index}]",
            budget,
            variables_allowed=variables_allowed,
            depth=depth + 1,
        )
        for index, item in enumerate(args_data)
    )
    return Application(head, arguments)


def _decode_term_list(
    value: Any,
    location: str,
    limit: int,
    budget: _TermBudget,
    *,
    variables_allowed: bool,
) -> tuple[Term, ...]:
    items = _expect_list(value, location, limit)
    return tuple(
        _term_from_data(
            item,
            f"{location}[{index}]",
            budget,
            variables_allowed=variables_allowed,
        )
        for index, item in enumerate(items)
    )


def policy_data(policy: CheckPolicy) -> dict[str, Any]:
    return {
        "schema": POLICY_SCHEMA,
        "session_id": policy.session_id,
        "goal": term_data(policy.goal),
        "premises": [term_data(term) for term in policy.premises],
        "admitted_candidate_ids": list(policy.admitted_candidate_ids),
        "require_candidate_scope": policy.require_candidate_scope,
    }


def ruleset_wire_data(ruleset: TrustedRuleSet) -> dict[str, Any]:
    rules = []
    for rule in sorted(ruleset.rules, key=lambda item: item.rule_id):
        rules.append(
            {
                "rule_id": rule.rule_id,
                "premises": [term_data(term) for term in rule.premises],
                "conclusion": term_data(rule.conclusion),
            }
        )
    return {"schema": RULESET_SCHEMA, "rules": rules}


def proof_wire_data(proof: ProofReceipt) -> dict[str, Any]:
    scope = None
    if proof.candidate_scope is not None:
        scope = {
            "candidate_id": proof.candidate_scope.candidate_id,
            "session_id": proof.candidate_scope.session_id,
            "ruleset_digest": proof.candidate_scope.ruleset_digest,
        }
    return {
        "schema": PROOF_SCHEMA,
        "session_id": proof.session_id,
        "ruleset_digest": proof.ruleset_digest,
        "goal": term_data(proof.goal),
        "premises": [term_data(term) for term in proof.premises],
        "steps": [
            {
                "rule_id": step.rule_id,
                "premise_refs": list(step.premise_refs),
                "conclusion": term_data(step.conclusion),
            }
            for step in proof.steps
        ],
        "final_ref": proof.final_ref,
        "candidate_scope": scope,
    }


def checker_receipt_data(receipt: CheckerReceipt) -> dict[str, Any]:
    return {
        "schema": CHECKER_RECEIPT_SCHEMA,
        "accepted": receipt.accepted,
        "code": receipt.code,
        "message": receipt.message,
        "checked_goal_digest": receipt.checked_goal_digest,
        "ruleset_digest": receipt.ruleset_digest,
        "proof_digest": receipt.proof_digest,
        "checked_steps": receipt.checked_steps,
        "checker_id": receipt.checker_id,
    }


def decode_policy(value: Any) -> CheckPolicy:
    obj = _expect_object(value, "policy")
    _expect_exact_fields(
        obj,
        (
            "schema",
            "session_id",
            "goal",
            "premises",
            "admitted_candidate_ids",
            "require_candidate_scope",
        ),
        "policy",
    )
    _expect_schema(obj, POLICY_SCHEMA, "policy")
    budget = _TermBudget()
    goal = _term_from_data(obj["goal"], "policy.goal", budget, variables_allowed=False)
    premises = _decode_term_list(
        obj["premises"],
        "policy.premises",
        MAX_TASK_PREMISES,
        budget,
        variables_allowed=False,
    )
    candidates_data = _expect_list(
        obj["admitted_candidate_ids"],
        "policy.admitted_candidate_ids",
        MAX_CANDIDATES,
    )
    candidates = tuple(
        _expect_string(item, f"policy.admitted_candidate_ids[{index}]")
        for index, item in enumerate(candidates_data)
    )
    return CheckPolicy(
        session_id=_expect_string(obj["session_id"], "policy.session_id"),
        goal=goal,
        premises=premises,
        admitted_candidate_ids=candidates,
        require_candidate_scope=_expect_bool(
            obj["require_candidate_scope"],
            "policy.require_candidate_scope",
        ),
    )


def decode_ruleset(value: Any) -> TrustedRuleSet:
    obj = _expect_object(value, "ruleset")
    _expect_exact_fields(obj, ("schema", "rules"), "ruleset")
    _expect_schema(obj, RULESET_SCHEMA, "ruleset")
    rules_data = _expect_list(obj["rules"], "ruleset.rules", MAX_RULES)
    budget = _TermBudget()
    rules = []
    for index, item in enumerate(rules_data):
        location = f"ruleset.rules[{index}]"
        rule_obj = _expect_object(item, location)
        _expect_exact_fields(rule_obj, ("rule_id", "premises", "conclusion"), location)
        rules.append(
            RuleSpec(
                rule_id=_expect_string(rule_obj["rule_id"], f"{location}.rule_id"),
                premises=_decode_term_list(
                    rule_obj["premises"],
                    f"{location}.premises",
                    MAX_RULE_PREMISES,
                    budget,
                    variables_allowed=True,
                ),
                conclusion=_term_from_data(
                    rule_obj["conclusion"],
                    f"{location}.conclusion",
                    budget,
                    variables_allowed=True,
                ),
            )
        )
    return TrustedRuleSet(tuple(rules))


def decode_proof(value: Any) -> ProofReceipt:
    obj = _expect_object(value, "proof")
    _expect_exact_fields(
        obj,
        (
            "schema",
            "session_id",
            "ruleset_digest",
            "goal",
            "premises",
            "steps",
            "final_ref",
            "candidate_scope",
        ),
        "proof",
    )
    _expect_schema(obj, PROOF_SCHEMA, "proof")
    budget = _TermBudget()
    goal = _term_from_data(obj["goal"], "proof.goal", budget, variables_allowed=False)
    premises = _decode_term_list(
        obj["premises"],
        "proof.premises",
        MAX_TASK_PREMISES,
        budget,
        variables_allowed=False,
    )
    steps_data = _expect_list(obj["steps"], "proof.steps", MAX_STEPS)
    steps = []
    for index, item in enumerate(steps_data):
        location = f"proof.steps[{index}]"
        step_obj = _expect_object(item, location)
        _expect_exact_fields(step_obj, ("rule_id", "premise_refs", "conclusion"), location)
        refs_data = _expect_list(
            step_obj["premise_refs"],
            f"{location}.premise_refs",
            MAX_STEP_PREMISES,
        )
        steps.append(
            ProofStep(
                rule_id=_expect_string(step_obj["rule_id"], f"{location}.rule_id"),
                premise_refs=tuple(
                    _expect_string(ref, f"{location}.premise_refs[{ref_index}]")
                    for ref_index, ref in enumerate(refs_data)
                ),
                conclusion=_term_from_data(
                    step_obj["conclusion"],
                    f"{location}.conclusion",
                    budget,
                    variables_allowed=False,
                ),
            )
        )
    scope_data = obj["candidate_scope"]
    scope = None
    if scope_data is not None:
        scope_obj = _expect_object(scope_data, "proof.candidate_scope")
        _expect_exact_fields(
            scope_obj,
            ("candidate_id", "session_id", "ruleset_digest"),
            "proof.candidate_scope",
        )
        scope = CandidateScope(
            candidate_id=_expect_string(scope_obj["candidate_id"], "proof.candidate_scope.candidate_id"),
            session_id=_expect_string(scope_obj["session_id"], "proof.candidate_scope.session_id"),
            ruleset_digest=_expect_string(
                scope_obj["ruleset_digest"],
                "proof.candidate_scope.ruleset_digest",
            ),
        )
    return ProofReceipt(
        session_id=_expect_string(obj["session_id"], "proof.session_id"),
        ruleset_digest=_expect_string(obj["ruleset_digest"], "proof.ruleset_digest"),
        goal=goal,
        premises=premises,
        steps=tuple(steps),
        final_ref=_expect_string(obj["final_ref"], "proof.final_ref"),
        candidate_scope=scope,
    )


def decode_checker_receipt(value: Any) -> CheckerReceipt:
    obj = _expect_object(value, "checker_receipt")
    _expect_exact_fields(
        obj,
        (
            "schema",
            "accepted",
            "code",
            "message",
            "checked_goal_digest",
            "ruleset_digest",
            "proof_digest",
            "checked_steps",
            "checker_id",
        ),
        "checker_receipt",
    )
    _expect_schema(obj, CHECKER_RECEIPT_SCHEMA, "checker_receipt")
    return CheckerReceipt(
        accepted=_expect_bool(obj["accepted"], "checker_receipt.accepted"),
        code=_expect_string(obj["code"], "checker_receipt.code"),
        message=_expect_string(obj["message"], "checker_receipt.message"),
        checked_goal_digest=_expect_string(
            obj["checked_goal_digest"],
            "checker_receipt.checked_goal_digest",
        ),
        ruleset_digest=_expect_string(obj["ruleset_digest"], "checker_receipt.ruleset_digest"),
        proof_digest=_expect_string(obj["proof_digest"], "checker_receipt.proof_digest"),
        checked_steps=_expect_nonnegative_int(
            obj["checked_steps"],
            "checker_receipt.checked_steps",
            MAX_STEPS,
        ),
        checker_id=_expect_string(obj["checker_id"], "checker_receipt.checker_id"),
    )


def _reject_constant(value: str) -> None:
    _fail("INVALID_NUMBER", f"non-finite JSON number is forbidden: {value}")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("DUPLICATE_FIELD", f"duplicate JSON field: {key}")
        result[key] = value
    return result


def loads_strict(data: bytes, decoder: Callable[[Any], T]) -> T:
    if len(data) > MAX_FILE_BYTES:
        _fail("FILE_SIZE_LIMIT", f"document exceeds {MAX_FILE_BYTES} bytes")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        _fail("INVALID_UTF8", f"document is not UTF-8: {error.reason}")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except WireFormatError:
        raise
    except (json.JSONDecodeError, RecursionError) as error:
        _fail("INVALID_JSON", str(error))
    return decoder(value)


def load_file(path: Path, decoder: Callable[[Any], T]) -> T:
    try:
        with path.open("rb") as stream:
            data = stream.read(MAX_FILE_BYTES + 1)
    except OSError as error:
        _fail("FILE_READ_ERROR", f"cannot read {path}: {error.strerror or error}")
    return loads_strict(data, decoder)


def write_json(path: Path, value: Any) -> bytes:
    payload = canonical_bytes(value) + b"\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def write_content_addressed_receipt(directory: Path, receipt: CheckerReceipt) -> Path:
    payload = canonical_bytes(checker_receipt_data(receipt)) + b"\n"
    digest = hashlib.sha256(payload).hexdigest()
    path = directory / f"sha256-{digest}.checker-receipt.json"
    directory.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != payload:
        _fail("ARTIFACT_COLLISION", f"existing artifact differs: {path}")
    path.write_bytes(payload)
    return path
