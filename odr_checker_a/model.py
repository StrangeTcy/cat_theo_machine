"""Immutable, search-free data model for ODR independent checker A.

The checker intentionally uses an inert term representation.  An integration
adapter may translate live CTM terms into these records, but no live rule,
search object, or candidate implementation crosses the checker boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union


@dataclass(frozen=True, slots=True)
class Atom:
    """A concrete atomic symbol."""

    name: str


@dataclass(frozen=True, slots=True)
class Variable:
    """A variable permitted in trusted rule patterns only."""

    name: str


@dataclass(frozen=True, slots=True)
class Application:
    """A first-order term with an atomic head and ordered arguments."""

    head: Atom
    arguments: Tuple["Term", ...] = ()


Term = Union[Atom, Variable, Application]
ConcreteTerm = Union[Atom, Application]


@dataclass(frozen=True, slots=True)
class RuleSpec:
    """An inert snapshot of one trusted rule."""

    rule_id: str
    premises: Tuple[Term, ...]
    conclusion: Term


@dataclass(frozen=True, slots=True)
class TrustedRuleSet:
    """The exact trusted rules against which a receipt is checked."""

    rules: Tuple[RuleSpec, ...]


@dataclass(frozen=True, slots=True)
class CandidateScope:
    """Session-local provenance for an untrusted, already-expanded candidate."""

    candidate_id: str
    session_id: str
    ruleset_digest: str


@dataclass(frozen=True, slots=True)
class CheckPolicy:
    """Evaluator-owned task/admission context; never supplied by the producer."""

    session_id: str
    goal: ConcreteTerm
    premises: Tuple[ConcreteTerm, ...]
    admitted_candidate_ids: Tuple[str, ...] = ()
    require_candidate_scope: bool = False


@dataclass(frozen=True, slots=True)
class ProofStep:
    """One expanded inference using a named trusted rule.

    ``premise_refs`` address either declared premises (``p0``, ``p1``, ...)
    or earlier steps (``s0``, ``s1``, ...).  The checker infers substitutions
    itself; a producer cannot supply trusted bindings.
    """

    rule_id: str
    premise_refs: Tuple[str, ...]
    conclusion: ConcreteTerm


@dataclass(frozen=True, slots=True)
class ProofReceipt:
    session_id: str
    ruleset_digest: str
    goal: ConcreteTerm
    premises: Tuple[ConcreteTerm, ...]
    steps: Tuple[ProofStep, ...]
    final_ref: str
    candidate_scope: Optional[CandidateScope] = None


@dataclass(frozen=True, slots=True)
class CheckerReceipt:
    accepted: bool
    code: str
    message: str
    checked_goal_digest: str
    ruleset_digest: str
    proof_digest: str
    checked_steps: int
    checker_id: str
