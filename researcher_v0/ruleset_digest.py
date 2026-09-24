"""Researcher-v0 — ruleset-content fingerprint (A1.2 / A2.2).

The fingerprint answers one question: *which rules, by content, is this talk
about?* Renaming a display label must not change the answer; changing `Add2`
into `Add1`, changing a legality precondition, or changing a semantic constant
must.

Declared semantic / display partition for the token domain
----------------------------------------------------------

HASHED — the semantic content of a rule (`proof.RulePremises` +
`proof.RuleReplacement` + `proof.RuleIsUnary`, i.e. the rule *term*):

* the `Pair` skeleton: premise count and order, replacement shape, arity;
* every atom that carries a payload, by its **payload text** — payloads are
  compared by value in `constructors.Compare` (its last branch equates
  constructor-less atoms with equal payloads), so a different payload is a
  different constant: `Char("Tokens")` is not `Char("Token")`;
* every declared value-less singleton by its **declared name**
  (`EmptyList`, `Truth`, `False`, `VarTag`, `ZeroLabel`, `SuccLabel`); the
  whitelist is part of this fingerprint spec;
* variable **sharing**: each variable pattern is encoded by its
  first-encounter traversal index, so `Tokens(x) -> Tokens(Succ(x))` differs
  from `Tokens(x) -> Tokens(Succ(y))`. Sharing is semantic: `machine.Match`
  binds through `FindBinding`, which compares the variable atom by identity
  (`machine.py:213`), so a replacement that does not share the premise
  variable instantiates to a different successor state. `Preserves` matching
  depends on exactly this.

NOT HASHED — display-only, and only these:

1. the `display` atom of a rule spec, which lives in a declared slot outside
   the content term (`token_domain.RuleDisplay`) and is checked absent from
   every premise and replacement by the partition test;
2. variable **name** payloads: `machine.Match._is_var_pattern` reads only the
   `VarTag` head and the one-element tail, never the name slot, so the name
   text cannot affect matching, readings or legality. Sharing is still hashed.

Rule *order* is not hashed: the version is taken over the **sorted** per-rule
digests, so permuting a ruleset is declared equivalent (A2.2).

Encoding and residual limits
----------------------------

Each term becomes canonical ASCII text — `(pair A B)`, `(atom s6:Tokens)`,
`(const EmptyList)`, `(var 0)`, `(cons LBL ARGS)` — with payloads
length-prefixed as `s<len>:<text>`, so the encoding is injective and
delimiter-safe. A value-less atom outside the declared singleton list is
refused (`UnsupportedTermContent`) rather than hashed by object identity: a
fingerprint that cannot be reproduced in another process must fail loudly,
not silently differ.

No Python class name is inspected anywhere in this package; the atom encoding
is payload-only. For this domain every payload-carrying atom is `core.Char`,
and the domain test asserts that states and rules contain no other
payload-carrying atom. For an atom that carries a constructor slot
(`constructors.ConstructedBy`, `constructors.py:175`) the label and arguments
are hashed and the cached payload is ignored; this domain uses none.

`prettyprinting.PrettyTerm` is never used: it renders display text and must
not enter a content digest (inspection §3b).

Comparison discipline: terms are compared with `machine.Compare`, emptiness of
`EmptyList` with `machine.IdentityCompare` (as `machine.py` and `proof.py` do),
and predicate results by identity to `machine.truth_value` / `false_value`.
Python identity is never used on a term, and an index or count never occupies a
term slot — a search that reports a position carries it inside a term.
"""

from __future__ import annotations

import hashlib

from .. import machine as M
from .. import proof as P
from ..labels import SuccLabel, ZeroLabel
from .chains import ChainLength, ChainSortText, IsEmptyTerm

FINGERPRINT_SPEC_VERSION = 1
DOMAIN_TAG_TEXT = "researcher-v0-ruleset/1"


class UnsupportedTermContent(Exception):
    """The term holds content this fingerprint spec cannot encode."""


class DeclaredSingletonName(M.Edge):
    """Declared name of a value-less singleton, else EmptyList.

    A declared whitelist checked by identity — not an inference about a Python
    class. An atom outside the list has no name here.
    """

    def __init__(self, atom):
        if M.IdentityCompare(atom, M.EmptyList)() is M.truth_value:
            self.result = M.Char("EmptyList")
        elif M.IdentityCompare(atom, M.truth_value)() is M.truth_value:
            self.result = M.Char("Truth")
        elif M.IdentityCompare(atom, M.false_value)() is M.truth_value:
            self.result = M.Char("False")
        elif M.IdentityCompare(atom, M.VarTag)() is M.truth_value:
            self.result = M.Char("VarTag")
        elif M.IdentityCompare(atom, ZeroLabel)() is M.truth_value:
            self.result = M.Char("ZeroLabel")
        elif M.IdentityCompare(atom, SuccLabel)() is M.truth_value:
            self.result = M.Char("SuccLabel")
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(atom, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class IsVarPattern(M.Edge):
    """Is this term a variable pattern, exactly as `machine.Match` reads one?"""

    def __init__(self, term):
        if M.IsPair(term)() is M.false_value:
            self.result = M.false_value
        elif M.IdentityCompare(M.Head(term)(), M.VarTag)() is M.false_value:
            self.result = M.false_value
        elif M.IsPair(M.Tail(term)())() is M.false_value:
            self.result = M.false_value
        elif (
            M.IdentityCompare(M.Tail(M.Tail(term)())(), M.EmptyList)()
            is M.false_value
        ):
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class TextPayload(M.Edge):
    """Length-prefixed payload text of an atom: `s6:Tokens`."""

    def __init__(self, atom):
        text = "" if atom() is None else str(atom())
        self.result = M.Char("s" + str(len(text)) + ":" + text)
        super().__init__(inputs=M.Pair(atom, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ConstructorSlot(M.Edge):
    """The `constructor` slot of an atom, else EmptyList."""

    def __init__(self, atom):
        try:
            slot = atom.constructor
        except AttributeError:
            slot = M.EmptyList
        self.result = slot
        super().__init__(inputs=M.Pair(atom, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class VarIndex(M.Edge):
    """`Pair(index, Pair(bindings, EmptyList))` for a variable in context.

    Context is a chain of `Pair(variable, index)` in first-encounter order; a
    fresh variable is appended, so its index is the chain length. Sharing
    becomes visible in the digest because the second occurrence finds the
    first occurrence's index instead of allocating a new one.
    """

    def __init__(self, bindings, variable):
        self.variable = variable
        found = self._find(bindings)
        if IsEmptyTerm(found)() is M.false_value:
            self.result = M.Pair(M.Head(found)(), M.Pair(bindings, M.EmptyList))
        else:
            index = ChainLength(bindings)()
            self.result = M.Pair(
                index, M.Pair(M.Pair(M.Pair(variable, index), bindings), M.EmptyList)
            )
        super().__init__(
            inputs=M.Pair(bindings, M.Pair(variable, M.EmptyList)),
            results=self.result,
        )

    def _find(self, bindings):
        # A hit is carried as Pair(index, EmptyList), a miss as EmptyList, so
        # the emptiness question is asked of a term and the index never enters
        # an identity test.
        if M.IdentityCompare(bindings, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if M.IdentityCompare(M.Head(M.Head(bindings)())(), self.variable)() is M.truth_value:
            return M.Pair(M.Tail(M.Head(bindings)())(), M.EmptyList)
        return self._find(M.Tail(bindings)())

    def __call__(self):
        return self.result


class TermText(M.Edge):
    """`Pair(text, Pair(bindings, EmptyList))` — canonical text of a term."""

    def __init__(self, term, bindings):
        if M.IdentityCompare(term, M.EmptyList)() is M.truth_value:
            self.result = M.Pair(M.Char("(const EmptyList)"), M.Pair(bindings, M.EmptyList))
        elif IsVarPattern(term)() is M.truth_value:
            self.result = self._variable(term, bindings)
        elif M.IsPair(term)() is M.truth_value:
            self.result = self._pair(term, bindings)
        else:
            self.result = M.Pair(self._atom(term), M.Pair(bindings, M.EmptyList))
        super().__init__(
            inputs=M.Pair(term, M.Pair(bindings, M.EmptyList)), results=self.result
        )

    def _variable(self, term, bindings):
        indexed = VarIndex(bindings, term)()
        text = M.Char("(var " + str(M.Head(indexed)()) + ")")
        return M.Pair(text, M.Pair(M.Head(M.Tail(indexed)())(), M.EmptyList))

    def _pair(self, term, bindings):
        head = TermText(M.Head(term)(), bindings)()
        tail = TermText(M.Tail(term)(), M.Head(M.Tail(head)())())()
        body = "(pair " + M.Head(head)()() + " " + M.Head(tail)()() + ")"
        return M.Pair(M.Char(body), M.Pair(M.Head(M.Tail(tail)())(), M.EmptyList))

    def _atom(self, term):
        name = DeclaredSingletonName(term)()
        if M.IdentityCompare(name, M.EmptyList)() is M.false_value:
            return M.Char("(const " + TextPayload(name)()() + ")")
        slot = ConstructorSlot(term)()
        if M.IdentityCompare(slot, M.EmptyList)() is M.false_value:
            label = TermText(M.Head(slot)(), M.EmptyList)()
            args = TermText(M.Tail(slot)(), M.Head(M.Tail(label)())())()
            return M.Char(
                "(cons " + M.Head(label)()() + " " + M.Head(args)()() + ")"
            )
        if term() is None:
            raise UnsupportedTermContent(
                "value-less atom outside the declared singleton list; refusing to hash it"
            )
        return M.Char("(atom " + TextPayload(term)()() + ")")

    def __call__(self):
        return self.result


class RuleContentText(M.Edge):
    """Canonical text of one rule's content: premises, replacement, arity."""

    def __init__(self, rule_term):
        # One variable context spans premises *and* replacement: sharing across
        # the rule is what `machine.FindBinding` keys on, so it must be visible
        # in the digest. Two separate contexts would encode
        # `Tokens(x) -> Tokens(x)` and `Tokens(x) -> Tokens(y)` identically.
        premises = TermText(P.RulePremises(rule_term)(), M.EmptyList)()
        replacement = TermText(
            P.RuleReplacement(rule_term)(), M.Head(M.Tail(premises)())()
        )()
        unary = "unary" if P.RuleIsUnary(rule_term)() is M.truth_value else "multi"
        body = (
            "(rule spec " + str(FINGERPRINT_SPEC_VERSION)
            + " premise-count " + str(ChainLength(P.RulePremises(rule_term)())())
            + " premises " + M.Head(premises)()()
            + " replacement " + M.Head(replacement)()()
            + " arity " + unary
            + ")"
        )
        self.result = M.Char(body)
        super().__init__(inputs=M.Pair(rule_term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleContentDigest(M.Edge):
    """Digest of one rule's content: 64 hex characters."""

    def __init__(self, rule_term):
        text = RuleContentText(rule_term)()
        self.result = M.Char(
            hashlib.blake2b(text().encode("utf-8"), digest_size=32).hexdigest()
        )
        super().__init__(inputs=M.Pair(rule_term, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class RuleDigestChain(M.Edge):
    """Per-rule content digests, in the order the rule terms are given."""

    def __init__(self, rule_terms):
        self.result = self._collect(rule_terms, M.EmptyList)
        super().__init__(inputs=M.Pair(rule_terms, M.EmptyList), results=self.result)

    def _collect(self, remaining, built):
        if M.IdentityCompare(remaining, M.EmptyList)() is M.truth_value:
            return built
        return self._collect(
            M.Tail(remaining)(),
            M.Pair(RuleContentDigest(M.Head(remaining)())(), built),
        )

    def __call__(self):
        return self.result


class RulesetVersionText(M.Edge):
    """The domain-tagged canonical text a ruleset version is taken over."""

    def __init__(self, rule_terms):
        digests = ChainSortText(RuleDigestChain(rule_terms)())()
        self.result = M.Char(
            "(ruleset domain " + TextPayload(M.Char(DOMAIN_TAG_TEXT))()()
            + " spec " + str(FINGERPRINT_SPEC_VERSION)
            + " rule-count " + str(ChainLength(rule_terms)())
            + " sorted-digests " + self._joined(digests) + ")"
        )
        super().__init__(inputs=M.Pair(rule_terms, M.EmptyList), results=self.result)

    def _joined(self, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return ""
        head = TextPayload(M.Head(chain)())()()
        if M.IdentityCompare(M.Tail(chain)(), M.EmptyList)() is M.truth_value:
            return head
        return head + " " + self._joined(M.Tail(chain)())

    def __call__(self):
        return self.result


class RulesetVersion(M.Edge):
    """The A1.2/A2.2 ruleset content version of a chain of rule terms."""

    def __init__(self, rule_terms):
        text = RulesetVersionText(rule_terms)()
        self.result = M.Char(
            hashlib.blake2b(text().encode("utf-8"), digest_size=32).hexdigest()
        )
        super().__init__(inputs=M.Pair(rule_terms, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class ContainsAtom(M.Edge):
    """Is `atom` reachable from `term` by identity?"""

    def __init__(self, term, atom):
        self.result = self._walk(term, atom)
        super().__init__(
            inputs=M.Pair(term, M.Pair(atom, M.EmptyList)), results=self.result
        )

    def _walk(self, term, atom):
        if M.IdentityCompare(term, atom)() is M.truth_value:
            return M.truth_value
        if M.IsPair(term)() is M.false_value:
            return M.false_value
        if self._walk(M.Head(term)(), atom) is M.truth_value:
            return M.truth_value
        return self._walk(M.Tail(term)(), atom)

    def __call__(self):
        return self.result


class PayloadIsText(M.Edge):
    """Does the atom carry its payload as compared text (the `core.Char` shape)?

    `Compare` equates two constructor-less atoms when their payloads are `==`;
    an atom whose payload is not compared as text (a Python int, a bool, or no
    payload at all) fails this check against a text atom built from `str`.
    This is the domain's guard that no Python integer or bool hides inside a
    semantic state.
    """

    def __init__(self, atom):
        self.result = M.Compare(atom, M.Char(str(atom())))()
        super().__init__(inputs=M.Pair(atom, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class AtomsAreDeclaredOrText(M.Edge):
    """Every atom of the term is a declared singleton or carries text payload."""

    def __init__(self, term):
        self.result = self._walk(term)
        super().__init__(inputs=M.Pair(term, M.EmptyList), results=self.result)

    def _walk(self, term):
        if M.IsPair(term)() is M.false_value:
            if (
                M.IdentityCompare(DeclaredSingletonName(term)(), M.EmptyList)()
                is M.false_value
            ):
                return M.truth_value
            return PayloadIsText(term)()
        if self._walk(M.Head(term)()) is M.false_value:
            return M.false_value
        return self._walk(M.Tail(term)())

    def __call__(self):
        return self.result


class TextIsHex(M.Edge):
    """Is this text exactly 64 lowercase hex characters (the digest shape)?"""

    def __init__(self, text):
        if len(text) != 64:
            self.result = M.false_value
        else:
            self.result = self._scan(text, 0)
        super().__init__(inputs=M.Pair(M.Char(text), M.EmptyList), results=self.result)

    def _scan(self, text, position):
        if position == len(text):
            return M.truth_value
        if text[position] in "0123456789abcdef":
            return self._scan(text, position + 1)
        return M.false_value

    def __call__(self):
        return self.result
