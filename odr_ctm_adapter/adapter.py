"""Narrow CTM-to-checker-A integration adapter.

This package is intentionally outside ``odr_checker_a``.  It may inspect CTM
runtime objects, while the checker remains incapable of importing or invoking
CTM proof production.  The adapter performs representation conversion only;
it does not search, replay, or decide trust.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional, Sequence, Tuple

from cat_theo_machine import core as Core
from cat_theo_machine import gmprep as Gmp
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine.odr_checker_a import (
    Application,
    Atom,
    CandidateScope,
    CheckPolicy,
    ProofReceipt,
    ProofStep,
    RuleSpec,
    TrustedRuleSet,
    Variable,
    ruleset_digest,
)

PAIR_HEAD = Atom("ctm.Pair")
CONSTRUCTED_HEAD = Atom("ctm.Constructed")
MAX_ADAPTER_DEPTH = 128
MAX_ADAPTER_NODES = 20_000
MAX_CHAIN_ITEMS = 20_000


class AdaptationError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True, slots=True)
class SymbolBinding:
    """Authority-assigned stable name for one identity-sensitive CTM atom."""

    name: str
    value: object


class SymbolAuthority:
    """Explicit stable names for opaque CTM atoms.

    Anonymous CTM atoms are not serialized using UUIDs or memory addresses.
    They must be named by the integrating authority or adaptation fails.
    """

    def __init__(self, bindings: Iterable[SymbolBinding]):
        by_identity: dict[int, str] = {}
        names: set[str] = set()
        for binding in bindings:
            if not binding.name:
                raise AdaptationError("INVALID_SYMBOL_AUTHORITY", "symbol name is empty")
            if binding.name in names:
                raise AdaptationError(
                    "INVALID_SYMBOL_AUTHORITY",
                    f"duplicate symbol name: {binding.name}",
                )
            identity = id(binding.value)
            if identity in by_identity:
                raise AdaptationError(
                    "INVALID_SYMBOL_AUTHORITY",
                    f"one CTM atom has multiple names: {by_identity[identity]}, {binding.name}",
                )
            names.add(binding.name)
            by_identity[identity] = binding.name
        self._by_identity = by_identity

    @classmethod
    def from_mapping(cls, symbols: Mapping[str, object]) -> "SymbolAuthority":
        return cls(SymbolBinding(name, value) for name, value in sorted(symbols.items()))

    @classmethod
    def from_namespace(cls, namespace: Mapping[str, object]) -> "SymbolAuthority":
        """Build a deterministic authority from a frozen CTM runtime namespace.

        Aliases are resolved by choosing the lexicographically first public
        name for each atom identity. Pair cells and value-semantic Char/GMPRep
        atoms are encoded structurally and therefore excluded.
        """

        bindings = []
        seen: set[int] = set()
        for name, value in sorted(namespace.items()):
            if name.startswith("_") or not isinstance(value, Core.Atom):
                continue
            if isinstance(value, (Core.Pair, Core.Char, Gmp.GMPRep)):
                continue
            identity = id(value)
            if identity in seen:
                continue
            seen.add(identity)
            bindings.append(SymbolBinding(name, value))
        return cls(bindings)

    def name_of(self, value: object) -> Optional[str]:
        return self._by_identity.get(id(value))


@dataclass(frozen=True, slots=True)
class ExpandedCTMStep:
    rule_id: str
    premise_refs: Tuple[str, ...]
    conclusion: object


@dataclass(slots=True)
class _Budget:
    nodes: int = 0


class CTMAdapter:
    def __init__(self, authority: SymbolAuthority):
        self.authority = authority

    def _fail(self, code: str, message: str) -> None:
        raise AdaptationError(code, message)

    def _is_var_pattern(self, value: object) -> bool:
        if not isinstance(value, Core.Pair):
            return False
        if Core.Head(value)() is not M.VarTag:
            return False
        tail = Core.Tail(value)()
        return (
            isinstance(tail, Core.Pair)
            and Core.Tail(tail)() is M.EmptyList
        )

    def _variable_key(self, value: object) -> int:
        # The complete VarTag pair is the binding key used by CTM Match.
        return id(value)

    def adapt_term(self, value: object, *, variables_allowed: bool = False):
        variables: dict[int, str] = {}
        return self._adapt_term(
            value,
            variables=variables,
            variables_allowed=variables_allowed,
            budget=_Budget(),
            active=set(),
            depth=0,
        )

    def _adapt_term(
        self,
        value: object,
        *,
        variables: dict[int, str],
        variables_allowed: bool,
        budget: _Budget,
        active: set[int],
        depth: int,
    ):
        if depth > MAX_ADAPTER_DEPTH:
            self._fail("ADAPTER_DEPTH_LIMIT", f"CTM term exceeds depth {MAX_ADAPTER_DEPTH}")
        budget.nodes += 1
        if budget.nodes > MAX_ADAPTER_NODES:
            self._fail("ADAPTER_NODE_LIMIT", f"CTM term exceeds {MAX_ADAPTER_NODES} nodes")

        if self._is_var_pattern(value):
            if not variables_allowed:
                self._fail("VARIABLE_NOT_ALLOWED", "concrete CTM term contains a variable")
            key = self._variable_key(value)
            name = variables.get(key)
            if name is None:
                name = f"v{len(variables)}"
                variables[key] = name
            return Variable(name)

        identity = id(value)
        if identity in active:
            self._fail("CYCLIC_TERM", "CTM term contains a cycle")

        if isinstance(value, Core.Pair):
            active.add(identity)
            try:
                head = self._adapt_term(
                    Core.Head(value)(),
                    variables=variables,
                    variables_allowed=variables_allowed,
                    budget=budget,
                    active=active,
                    depth=depth + 1,
                )
                tail = self._adapt_term(
                    Core.Tail(value)(),
                    variables=variables,
                    variables_allowed=variables_allowed,
                    budget=budget,
                    active=active,
                    depth=depth + 1,
                )
            finally:
                active.remove(identity)
            return Application(PAIR_HEAD, (head, tail))

        authority_name = self.authority.name_of(value)
        if authority_name is not None:
            return Atom("ctm.Symbol:" + authority_name)

        if isinstance(value, Core.Char):
            return Atom("ctm.Char:" + value.symbol)
        if isinstance(value, Gmp.GMPRep):
            return Atom("ctm.GMPRep:" + str(value()))

        constructor = getattr(value, "constructor", None)
        if constructor is not None:
            active.add(identity)
            try:
                encoded = self._adapt_term(
                    constructor,
                    variables=variables,
                    variables_allowed=variables_allowed,
                    budget=budget,
                    active=active,
                    depth=depth + 1,
                )
            finally:
                active.remove(identity)
            return Application(CONSTRUCTED_HEAD, (encoded,))

        self._fail(
            "UNNAMED_ATOM",
            f"CTM atom of type {type(value).__name__} lacks an authority-assigned stable name",
        )

    def _machine_chain(self, chain: object, location: str) -> tuple[object, ...]:
        result = []
        current = chain
        seen: set[int] = set()
        while current is not M.EmptyList:
            if len(result) >= MAX_CHAIN_ITEMS:
                self._fail("CHAIN_LIMIT", f"{location} exceeds {MAX_CHAIN_ITEMS} entries")
            if not isinstance(current, Core.Pair):
                self._fail("IMPROPER_CHAIN", f"{location} is not a proper CTM list")
            identity = id(current)
            if identity in seen:
                self._fail("CYCLIC_CHAIN", f"{location} contains a cycle")
            seen.add(identity)
            result.append(Core.Head(current)())
            current = Core.Tail(current)()
        return tuple(result)

    def adapt_rule(self, rule_id: str, rule: object) -> RuleSpec:
        if not rule_id:
            self._fail("INVALID_RULE_ID", "trusted CTM rule ID is empty")
        raw = P.CompiledRuleRaw(rule)()
        premises_raw = self._machine_chain(P.RulePremises(raw)(), f"rule {rule_id} premises")
        replacement = P.RuleReplacement(raw)()
        if P.ReplacementIsFactList(raw)() is M.truth_value:
            replacements = self._machine_chain(replacement, f"rule {rule_id} replacement")
            if len(replacements) != 1:
                self._fail(
                    "MULTIPLE_CONCLUSIONS_UNSUPPORTED",
                    f"rule {rule_id} has {len(replacements)} replacement facts",
                )
            replacement = replacements[0]

        # One variable map is shared across all patterns and the conclusion so
        # repeated CTM variable identities retain their binding relationship.
        variables: dict[int, str] = {}
        budget = _Budget()
        premises = tuple(
            self._adapt_term(
                premise,
                variables=variables,
                variables_allowed=True,
                budget=budget,
                active=set(),
                depth=0,
            )
            for premise in premises_raw
        )
        conclusion = self._adapt_term(
            replacement,
            variables=variables,
            variables_allowed=True,
            budget=budget,
            active=set(),
            depth=0,
        )
        return RuleSpec(rule_id, premises, conclusion)

    def adapt_ruleset(self, entries: Sequence[tuple[str, object]]) -> TrustedRuleSet:
        return TrustedRuleSet(tuple(self.adapt_rule(rule_id, rule) for rule_id, rule in entries))

    def adapt_policy(
        self,
        *,
        session_id: str,
        goal: object,
        premises: Sequence[object],
        admitted_candidate_ids: Sequence[str] = (),
        require_candidate_scope: bool = False,
    ) -> CheckPolicy:
        return CheckPolicy(
            session_id=session_id,
            goal=self.adapt_term(goal),
            premises=tuple(self.adapt_term(item) for item in premises),
            admitted_candidate_ids=tuple(admitted_candidate_ids),
            require_candidate_scope=require_candidate_scope,
        )

    def adapt_proof(
        self,
        *,
        session_id: str,
        trusted_rules: TrustedRuleSet,
        goal: object,
        premises: Sequence[object],
        steps: Sequence[ExpandedCTMStep],
        final_ref: str,
        candidate_id: str | None = None,
    ) -> ProofReceipt:
        digest = ruleset_digest(trusted_rules)
        scope = None
        if candidate_id is not None:
            scope = CandidateScope(candidate_id, session_id, digest)
        return ProofReceipt(
            session_id=session_id,
            ruleset_digest=digest,
            goal=self.adapt_term(goal),
            premises=tuple(self.adapt_term(item) for item in premises),
            steps=tuple(
                ProofStep(
                    step.rule_id,
                    tuple(step.premise_refs),
                    self.adapt_term(step.conclusion),
                )
                for step in steps
            ),
            final_ref=final_ref,
            candidate_scope=scope,
        )
