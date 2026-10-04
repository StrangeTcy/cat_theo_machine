"""ODR independent proof checker A.

The public surface is intentionally small: inert record types, canonical
ruleset hashing, and one deterministic checking function.
"""

from .canonical import proof_digest, ruleset_digest, term_digest
from .checker import CHECKER_ID, check_proof
from .model import (
    Application,
    Atom,
    CandidateScope,
    CheckPolicy,
    CheckerReceipt,
    ProofReceipt,
    ProofStep,
    RuleSpec,
    TrustedRuleSet,
    Variable,
)

__all__ = (
    "Application",
    "Atom",
    "CandidateScope",
    "CheckPolicy",
    "CheckerReceipt",
    "ProofReceipt",
    "ProofStep",
    "RuleSpec",
    "TrustedRuleSet",
    "Variable",
    "CHECKER_ID",
    "check_proof",
    "proof_digest",
    "ruleset_digest",
    "term_digest",
)
