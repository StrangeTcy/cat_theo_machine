"""INV-0: inert, root-list rewriting laboratory, not a live knowledge service.

All semantic records/lists are machine Pair terms. Python containers occur at
JSON, hashing, CLI/report, and term-construction boundaries only. Shared kernel
Match/Instantiate are used only on unconstructed Pair/Char templates. No global
constructor registry is written. The small checker is deliberately incomplete.

Record fields (zero based, excluding tag) are specified at their constructors.
A hash is a content identifier, NOT a signature or an authority to admit laws.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from . import machine as M
from . import proof as P
from . import labels as L

E = M.EmptyList
# Codec interning table: serialization identity, not a semantic dispatch table.
_SYMBOLS = {}
_VARIABLES = {}


def symbol(text):
    if text not in _SYMBOLS:
        _SYMBOLS[text] = M.Char(text)
    return _SYMBOLS[text]


def chain(*items):
    """Term-construction boundary: never put the host args tuple in a term."""
    result = E
    for item in reversed(items):
        result = M.Pair(item, result)
    return result


def record(tag, *fields):
    return M.Pair(tag, chain(*fields))


def head(term):
    return M.Head(term)()


def tail(term):
    return M.Tail(term)()


def items(terms):
    while terms is not E:
        if not isinstance(terms, M.Pair):
            raise ValueError('improper structural list')
        yield head(terms)
        terms = tail(terms)


def field(term, index):
    term = tail(term)
    while index:
        term = tail(term)
        index -= 1
    return head(term)


def tagged(term, tag):
    return isinstance(term, M.Pair) and head(term) is tag


def has_fields(term, count):
    if not isinstance(term, M.Pair):
        return False
    rest = tail(term)
    while count:
        if not isinstance(rest, M.Pair):
            return False
        rest = tail(rest)
        count -= 1
    return rest is E


def reverse(terms):
    result = E
    for term in items(terms):
        result = M.Pair(term, result)
    return result


def equal(a, b):
    pending = chain(M.Pair(a, b))
    while pending is not E:
        pair = head(pending)
        pending = tail(pending)
        a, b = head(pair), tail(pair)
        if a is b:
            continue
        if isinstance(a, M.Pair) and isinstance(b, M.Pair):
            pending = M.Pair(M.Pair(head(a), head(b)),
                             M.Pair(M.Pair(tail(a), tail(b)), pending))
        elif type(a) is P.Rule and type(b) is P.Rule:
            pending = M.Pair(M.Pair(a.inputs, b.inputs), pending)
        else:
            return False
    return True


def contains(terms, term):
    return any(equal(t, term) for t in items(terms))


ATTEMPT = symbol('inv0/TransitionAttempt')
PROPOSAL = symbol('inv0/ProposedTransition')
CHECKED = symbol('inv0/CheckedTransition')
REJECTED = symbol('inv0/RejectedTransition')
OPEN = symbol('inv0/OpenTransition')
FAILURE = symbol('inv0/ExecutionFailure')
TRANSITION_PROOF = symbol('inv0/TransitionProof')
RULE_ENTRY = symbol('inv0/RuleEntry')
LENGTH = symbol('inv0/LengthOperator')
MOD = symbol('inv0/ModuloOperator')
PRESERVED = symbol('inv0/PreservedOn')
BROKEN = symbol('inv0/BrokenOn')
CANDIDATE = symbol('inv0/InvariantCandidate')
PROPOSED = symbol('inv0/Proposed')
REFUTED = symbol('inv0/Refuted')
UNRESOLVED = symbol('inv0/Unresolved')
MINING = symbol('inv0/MiningResult')
AFFINE = symbol('inv0/AffineLength')
RULE_PROOF = symbol('inv0/RulePreservationProof')
PROVED = symbol('inv0/Proved')
UNSUPPORTED = symbol('inv0/Unsupported')
CERTIFICATE = symbol('inv0/InvariantCertificate')
UNREACHABLE = symbol('inv0/CheckedUnreachable')
UNKNOWN = symbol('inv0/Unknown')
INVALID = symbol('inv0/InvalidCertificate')
SCOPE = symbol('inv0/ScopeMismatch')
FOUND = symbol('inv0/CheckedReachable')
BUDGET = symbol('inv0/BudgetExhausted')
EXHAUSTED = symbol('inv0/SearchExhaustedUnknown')
SEARCH = symbol('inv0/SearchResult')
QUEUE_NODE = symbol('inv0/QueueNode')
DOMAIN = symbol('inv0/FiniteOpaqueTokenLists-root-rewrite-v1')
VERSION = symbol('inv0/structural-affine-kernel-v1')
ASSUMPTIONS = chain(DOMAIN, symbol('inv0/finite-acyclic-well-typed-matches'))
DEPENDENCIES = chain(VERSION, symbol('inv0/Pair-position-count'),
                     symbol('inv0/root-step-induction-reflexive-transitive-closure'))
TOKEN_A = symbol('token/A')
TOKEN_B = symbol('token/B')


def succ(n):
    return record(L.SuccLabel, n)


def natural(n):
    """Host-number conversion boundary (budgets/reports/tests)."""
    if type(n) is not int or n < 0:
        raise ValueError('expected nonnegative integer')
    result = M.Zero
    for _ in range(n):
        result = succ(result)
    return result


def integer(n):
    result = 0
    while n is not M.Zero:
        if not tagged(n, L.SuccLabel) or tail(tail(n)) is not E:
            raise ValueError('not a structural natural')
        result += 1
        n = field(n, 0)
    return result


def parity(n):
    result = M.Zero
    while n is not M.Zero:
        if not tagged(n, L.SuccLabel):
            raise ValueError('not a natural')
        result = succ(M.Zero) if result is M.Zero else M.Zero
        n = field(n, 0)
    return result


def token(t):
    return type(t) is M.Char and t.symbol.startswith('token/')


def valid_state(state):
    # Cycle detection is done at the JSON boundary; in-memory terms are finite.
    try:
        return all(token(t) for t in items(state))
    except (ValueError, AttributeError):
        return False


def length(state):
    if not valid_state(state):
        raise ValueError('outside state domain')
    result = M.Zero
    for _ in items(state):
        result = succ(result)
    return result


def state(n):
    """Deterministic construction boundary: A,B,A,B,... of length n."""
    result = E
    for i in reversed(range(n)):
        result = M.Pair(TOKEN_A if i % 2 == 0 else TOKEN_B, result)
    return result


def variable(name):
    return intern_variable(symbol('variable/' + name))


def intern_variable(name):
    # Serialization identity boundary: Match/Instantiate bind variable objects.
    if name.symbol not in _VARIABLES:
        _VARIABLES[name.symbol] = record(M.VarTag, name)
    return _VARIABLES[name.symbol]


def is_variable(t):
    return (tagged(t, M.VarTag) and isinstance(tail(t), M.Pair)
            and tail(tail(t)) is E and type(field(t, 0)) is M.Char)


def encode(term):
    """Restricted canonical JSON boundary; no arbitrary object deserialization."""
    if term is E:
        return ['empty']
    if term is M.Zero:
        return ['zero']
    if term is M.VarTag:
        return ['var-tag']
    if term is L.SuccLabel:
        return ['succ-tag']
    if tagged(term, L.SuccLabel):
        return ['nat', integer(term)]
    if type(term) is M.Char:
        return ['atom', term.symbol]
    if type(term) is P.Rule:
        validate_rule(term)
        return ['rule', encode(P.RulePattern(term)()), encode(P.RuleReplacement(term)())]
    if isinstance(term, M.Pair):
        return ['pair', encode(head(term)), encode(tail(term))]
    raise ValueError('unsupported term in codec')


def decode(data):
    if type(data) is not list or not data:
        raise ValueError('invalid encoding')
    tag = data[0]
    if data == ['empty']:
        return E
    if data == ['zero']:
        return M.Zero
    if data == ['var-tag']:
        return M.VarTag
    if data == ['succ-tag']:
        return L.SuccLabel
    if tag == 'nat' and len(data) == 2 and type(data[1]) is int and 0 <= data[1] <= 10000:
        return natural(data[1])
    if tag == 'atom' and len(data) == 2 and type(data[1]) is str:
        return symbol(data[1])
    if tag == 'pair' and len(data) == 3:
        result = M.Pair(decode(data[1]), decode(data[2]))
        return intern_variable(field(result, 0)) if is_variable(result) else result
    if tag == 'rule' and len(data) == 3:
        return P.Rule(decode(data[1]), decode(data[2]))
    raise ValueError('invalid encoding')


def canonical(term):
    return json.dumps(encode(term), separators=(',', ':'), ensure_ascii=True)


def digest(term):
    return symbol('sha256/' + hashlib.sha256(canonical(term).encode()).hexdigest())


def save(path, term):
    Path(path).write_text(canonical(term) + '\n', encoding='utf-8')


def load(path):
    return decode(json.loads(Path(path).read_text(encoding='utf-8')))


def validate_rule(rule):
    if type(rule) is not P.Rule or rule.results is not E:
        raise ValueError('not an unconditional unary Rule')
    rebuilt = P.Rule(P.RulePattern(rule)(), P.RuleReplacement(rule)())
    if not equal(rule.inputs, rebuilt.inputs):
        raise ValueError('malformed unary Rule')


def rule_id(rule):
    return digest(record(VERSION, rule))


def entry(label, rule):
    # display label, semantic Rule. Display label is NEVER used for dispatch.
    return record(RULE_ENTRY, symbol('display/' + label), rule)


def rule_set(plus=False, rename=False):
    r = variable('tail-renamed' if rename else 'rest')
    x = variable('u' if rename else 'x')
    y = variable('v' if rename else 'y')
    add = P.Rule(r, M.Pair(TOKEN_A, M.Pair(TOKEN_B, r)))
    remove = P.Rule(M.Pair(x, M.Pair(y, r)), r)
    swap = P.Rule(M.Pair(x, M.Pair(y, r)), M.Pair(y, M.Pair(x, r)))
    rules = chain(entry('q7' if rename else 'AddPair', add),
                  entry('q8' if rename else 'RemovePair', remove),
                  entry('q9' if rename else 'SwapPair', swap))
    if plus:
        rules = append(rules, chain(entry('q10' if rename else 'AddOne',
                                         P.Rule(r, M.Pair(TOKEN_A, r)))))
    return rules


def append(a, b):
    for t in items(reverse(a)):
        b = M.Pair(t, b)
    return b


def structures(rules):
    result = E
    for ent in items(rules):
        if not tagged(ent, RULE_ENTRY) or not has_fields(ent, 2) or type(field(ent, 1)) is not P.Rule:
            raise ValueError('unsupported rule entry')
        validate_rule(field(ent, 1))
        result = M.Pair(field(ent, 1), result)
    return reverse(result)


def scope_id(rules):
    return digest(record(VERSION, DOMAIN, structures(rules)))


def lookup_rule(rules, identity):
    for rule in items(structures(rules)):
        if equal(rule_id(rule), identity):
            return rule
    raise ValueError('unknown rule identity')


def make_attempt(before, rule, rules, budget=512, obligations=E):
    rule_id(rule)  # validate supported raw structure before invoking the kernel
    match = M.Match(P.RulePattern(rule)(), before)()
    binds = tail(match) if head(match) is M.truth_value else E
    # id, before, rule id, scope, substitution, assumptions, obligations, budget
    body = chain(before, rule_id(rule), scope_id(rules), binds,
                 ASSUMPTIONS, obligations, natural(budget))
    return M.Pair(ATTEMPT, M.Pair(digest(body), body))


def produce(attempt, rules):
    """Untrusted producer. A proposal's claimed status is not checked evidence."""
    aid = field(attempt, 0)
    try:
        if integer(field(attempt, 7)) == 0:
            return record(OPEN, aid, chain(symbol('inv0/rewrite-budget')))
        if field(attempt, 6) is not E:
            return record(OPEN, aid, field(attempt, 6))
        rule = lookup_rule(rules, field(attempt, 2))
        match = M.Match(P.RulePattern(rule)(), field(attempt, 1))()
        if head(match) is not M.truth_value:
            return record(REJECTED, aid, symbol('inv0/pattern-mismatch'))
        after = head(M.Instantiate(P.RuleReplacement(rule)(), field(attempt, 4))())
        return record(PROPOSAL, attempt, after)
    except TimeoutError:
        return record(OPEN, aid, chain(symbol('inv0/producer-timeout')))
    except Exception as exc:
        return record(FAILURE, aid, symbol('inv0/producer-' + type(exc).__name__))


def check_transition(proposal, rules, timeout=False):
    """Recompute scope, match, bindings, instantiated output and evidence hash.

    A zero budget/injected timeout is Open, never a mathematical refutation.
    Exact transition budget counts input/output cells plus structural rule cells.
    """
    aid = E
    try:
        if not (tagged(proposal, PROPOSAL) or tagged(proposal, CHECKED)):
            raise ValueError('not transition evidence')
        if not has_fields(proposal, 3 if tagged(proposal, CHECKED) else 2):
            raise ValueError('transition record shape')
        attempt = field(proposal, 0)
        aid = field(attempt, 0)
        if not tagged(attempt, ATTEMPT) or not has_fields(attempt, 8) or not equal(aid, digest(tail(tail(attempt)))):
            raise ValueError('attempt identity')
        if timeout:
            return record(OPEN, aid, chain(symbol('inv0/verifier-timeout')))
        if not equal(field(attempt, 3), scope_id(rules)):
            raise ValueError('rule-set identity')
        if not equal(field(attempt, 5), ASSUMPTIONS):
            raise ValueError('assumptions')
        if field(attempt, 6) is not E:
            return record(OPEN, aid, field(attempt, 6))
        before = field(attempt, 1)
        if not valid_state(before):
            raise ValueError('before domain')
        rule = lookup_rule(rules, field(attempt, 2))
        if integer(field(attempt, 7)) < work_size(before) + work_size(rule):
            return record(OPEN, aid, chain(symbol('inv0/check-budget')))
        match = M.Match(P.RulePattern(rule)(), before)()
        if head(match) is not M.truth_value:
            raise ValueError('pattern mismatch')
        if not equal(tail(match), field(attempt, 4)):
            raise ValueError('substitution')
        after = head(M.Instantiate(P.RuleReplacement(rule)(), tail(match))())
        if not valid_state(after) or not equal(after, field(proposal, 1)):
            raise ValueError('after-state')
        if integer(field(attempt, 7)) < work_size(before) + work_size(rule) + work_size(after):
            return record(OPEN, aid, chain(symbol('inv0/check-budget')))
        cert = record(TRANSITION_PROOF, VERSION, scope_id(rules), digest(chain(attempt, after)))
        result = record(CHECKED, attempt, after, cert)
        if tagged(proposal, CHECKED) and not equal(result, proposal):
            raise ValueError('transition certificate')
        return result
    except TimeoutError:
        return record(OPEN, aid, chain(symbol('inv0/verifier-timeout')))
    except (ValueError, AttributeError, TypeError) as exc:
        return record(REJECTED, aid, symbol('inv0/integrity-' + str(exc)))
    except Exception as exc:
        return record(FAILURE, aid, symbol('inv0/checker-' + type(exc).__name__))


def work_size(term):
    if type(term) is P.Rule:
        return 1 + work_size(P.RulePattern(term)()) + work_size(P.RuleReplacement(term)())
    if isinstance(term, M.Pair):
        return 1 + work_size(head(term)) + work_size(tail(term))
    return 1


def checked_step(before, rule, rules):
    attempt = make_attempt(before, rule, rules)
    proposal = produce(attempt, rules)
    return check_transition(proposal, rules) if tagged(proposal, PROPOSAL) else proposal


def training(rules):
    """Five laboratory lists, lengths 0..4; all three rules attempted per list."""
    attempts = outcomes = E
    for n in range(5):
        for rule in items(structures(rules)):
            a = make_attempt(state(n), rule, rules)
            p = produce(a, rules)
            if tagged(p, PROPOSAL):
                p = check_transition(p, rules)
                if tagged(p, CHECKED):
                    p = check_transition(p, rules)  # independently replay successes
            attempts = M.Pair(a, attempts)
            outcomes = M.Pair(p, outcomes)
    return record(symbol('inv0/Corpus'), reverse(attempts), reverse(outcomes))


def observer_grammar():
    return chain(record(LENGTH), record(MOD, natural(2), record(LENGTH)))


def supported_observer(observer):
    return equal(observer, record(LENGTH)) or equal(observer, record(MOD, natural(2), record(LENGTH)))


def observe(observer, state_term):
    if equal(observer, record(LENGTH)):
        return length(state_term)
    if equal(observer, record(MOD, natural(2), record(LENGTH))):
        return parity(observe(field(observer, 1), state_term))
    raise ValueError('unsupported observer expression')


def transition_id(checked):
    return field(field(checked, 0), 0)


def mine(outcomes, rules, retained=E, timeout=False):
    """Evaluate EVERY grammar expression; reuse only replayed counterexamples.

    Retained evidence contains checked transitions, not trusted verdicts. A
    replay timeout is unresolved. A broken observer is never inferred from a
    transition rejection/failure. Returns candidates, observations, retained
    counterexamples, observer evaluations, reused counterexample count.
    """
    candidates = observations = counterexamples = E
    evaluations = reused = 0
    for observer in items(observer_grammar()):
        supports = breaks = E
        pending = False
        reused_this = False
        for old in items(retained):
            if not tagged(old, BROKEN) or not equal(field(old, 0), observer):
                continue
            checked = check_transition(field(old, 1), rules, timeout=timeout)
            if tagged(checked, OPEN) or tagged(checked, FAILURE):
                pending = True
                continue
            if not tagged(checked, CHECKED):
                continue
            before = observe(observer, field(field(checked, 0), 1))
            after = observe(observer, field(checked, 1))
            evaluations += 2
            if not equal(before, after):
                witness = record(BROKEN, observer, checked, before, after)
                counterexamples = M.Pair(witness, counterexamples)
                breaks = M.Pair(transition_id(checked), breaks)
                reused += 1
                reused_this = True
                break
        if not reused_this:
            for outcome in items(outcomes):
                if tagged(outcome, OPEN) or tagged(outcome, FAILURE):
                    pending = True
                if not tagged(outcome, CHECKED):
                    continue
                checked = check_transition(outcome, rules, timeout=timeout)
                if not tagged(checked, CHECKED):
                    pending = True
                    continue
                before = observe(observer, field(field(checked, 0), 1))
                after = observe(observer, field(checked, 1))
                evaluations += 2
                if equal(before, after):
                    observations = M.Pair(record(PRESERVED, observer, transition_id(checked)), observations)
                    supports = M.Pair(transition_id(checked), supports)
                else:
                    witness = record(BROKEN, observer, checked, before, after)
                    observations = M.Pair(witness, observations)
                    breaks = M.Pair(transition_id(checked), breaks)
                    # One replayable witness per rejected candidate suffices.
                    if not any(equal(field(w, 0), observer) for w in items(counterexamples)):
                        counterexamples = M.Pair(witness, counterexamples)
        status = REFUTED if breaks is not E else (UNRESOLVED if pending or supports is E else PROPOSED)
        candidates = M.Pair(record(CANDIDATE, observer, scope_id(rules), reverse(supports),
                                   reverse(breaks), status), candidates)
    return record(MINING, reverse(candidates), reverse(observations), reverse(counterexamples),
                  natural(evaluations), natural(reused))


def affine_shape(template, bound_tokens=E, bound_tail=E, lhs=True):
    """Typed affine fragment: a finite token prefix followed by one list var.

    Prefix token variables are universally quantified opaque atoms; their
    identities do not enter length. Repeated LHS variables are deliberately
    unsupported. RHS variables must preserve their LHS sort. No nested lists,
    unbound variables, arbitrary constructors, or conditional rules pass.
    Returns prefix length, tail variable, token-variable list.
    """
    count = M.Zero
    tokens = bound_tokens
    while template is not E and not is_variable(template):
        if not isinstance(template, M.Pair):
            raise ValueError('non-list template')
        t = head(template)
        if is_variable(t):
            if lhs:
                if contains(tokens, t):
                    raise ValueError('repeated lhs variable unsupported')
                tokens = M.Pair(t, tokens)
            elif not contains(bound_tokens, t):
                raise ValueError('unbound or ill-sorted token variable')
        elif not token(t):
            raise ValueError('non-token head')
        count = succ(count)
        template = tail(template)
    if template is not E:
        if lhs and contains(tokens, template):
            raise ValueError('variable used at two sorts')
        if not lhs and not equal(template, bound_tail):
            raise ValueError('unbound or changed tail variable')
    return record(AFFINE, count, template, tokens)


def preservation(observer, rules):
    """Independent schema proof. No trace parameter and no sampled-state test.

    Structural induction on each prefix gives |template| = prefix + |tail|.
    Equal symbolic tails cancel. Equality of prefixes (or their residues)
    proves preservation for ALL admissible substitutions. Signed delta is
    represented as (after_prefix, before_prefix), not a trusted host integer.
    """
    proofs = E
    work = 0
    if not supported_observer(observer):
        return record(UNSUPPORTED, symbol('inv0/observer-fragment'), natural(work))
    try:
        if rules is E:
            raise ValueError('empty rule set not in experiment fragment')
        for rule in items(structures(rules)):
            work += work_size(rule)
            before = affine_shape(P.RulePattern(rule)())
            after = affine_shape(P.RuleReplacement(rule)(), field(before, 2), field(before, 1), False)
            if not equal(field(before, 1), field(after, 1)):
                raise ValueError('noncancelling symbolic tails')
            b = field(before, 0)
            a = field(after, 0)
            if tagged(observer, MOD):
                b, a = parity(b), parity(a)
            proof = record(RULE_PROOF, rule_id(rule), before, after,
                           chain(field(after, 0), field(before, 0)), observer)
            if not equal(a, b):
                # Refutation is backed by an actually checked, typed witness.
                sample = instantiate_sample(P.RulePattern(rule)())
                witness = checked_step(sample, rule, rules)
                if not tagged(witness, CHECKED):
                    raise ValueError('counterexample could not be checked')
                bv = observe(observer, sample)
                av = observe(observer, field(witness, 1))
                if equal(bv, av):
                    raise ValueError('symbolic counterexample mismatch')
                return record(REFUTED, record(BROKEN, observer, witness, bv, av), natural(work))
            proofs = M.Pair(proof, proofs)
        return record(PROVED, reverse(proofs), natural(work))
    except (ValueError, AttributeError, TypeError, RecursionError) as exc:
        return record(UNSUPPORTED, symbol('inv0/' + str(exc)), natural(work))


def instantiate_sample(pattern):
    if is_variable(pattern) or pattern is E:
        return E
    t = head(pattern)
    return M.Pair(TOKEN_A if is_variable(t) else t, instantiate_sample(tail(pattern)))


def certify(candidate, rules, counterexamples=E):
    if not tagged(candidate, CANDIDATE) or not has_fields(candidate, 5) or field(candidate, 4) is not PROPOSED:
        return record(UNRESOLVED, symbol('inv0/not-proposed-candidate'))
    if not equal(field(candidate, 1), scope_id(rules)):
        return record(SCOPE)
    proof = preservation(field(candidate, 0), rules)
    if not tagged(proof, PROVED):
        return proof
    # id, observer, domain, exact scope, assumptions, per-rule proofs,
    # dependencies, supporting ids, rejected-candidate counterexamples
    body = chain(field(candidate, 0), DOMAIN, scope_id(rules), ASSUMPTIONS,
                 field(proof, 0), DEPENDENCIES, field(candidate, 2), counterexamples)
    return M.Pair(CERTIFICATE, M.Pair(digest(body), body))


def verify_certificate(cert, rules):
    try:
        if not tagged(cert, CERTIFICATE) or not has_fields(cert, 9):
            return INVALID
        if not equal(field(cert, 0), digest(tail(tail(cert)))):
            return INVALID
        if not equal(field(cert, 3), scope_id(rules)):
            return SCOPE
        if field(cert, 2) is not DOMAIN or not equal(field(cert, 4), ASSUMPTIONS):
            return INVALID
        if not equal(field(cert, 6), DEPENDENCIES):
            return INVALID
        proof = preservation(field(cert, 1), rules)
        if not tagged(proof, PROVED) or not equal(field(cert, 5), field(proof, 0)):
            return INVALID
        for witness in items(field(cert, 8)):
            if not tagged(witness, BROKEN):
                return INVALID
            checked = check_transition(field(witness, 1), rules)
            if not tagged(checked, CHECKED):
                return INVALID
            b = observe(field(witness, 0), field(field(checked, 0), 1))
            a = observe(field(witness, 0), field(checked, 1))
            if equal(b, a) or not equal(b, field(witness, 2)) or not equal(a, field(witness, 3)):
                return INVALID
        return PROVED
    except (ValueError, AttributeError, TypeError, RecursionError):
        return INVALID


def check_reachability_obstruction(cert, start, goal, rules):
    status = verify_certificate(cert, rules)
    if status is not PROVED:
        return record(status)
    if not valid_state(start) or not valid_state(goal):
        return record(UNKNOWN)
    before = observe(field(cert, 1), start)
    after = observe(field(cert, 1), goal)
    if equal(before, after):
        return record(UNKNOWN)
    return record(UNREACHABLE, field(cert, 0), scope_id(rules), start, goal, before, after)


def bfs(start, goal, rules, budget=64, certificate=None):
    """FIFO root-state BFS. Budget exhaustion is deliberately not a proof.

    SearchResult(status, expansions, checked path, obstruction-or-scope-status).
    Supplying a certificate is the ONLY way this search can use an invariant.
    """
    obstruction = record(UNKNOWN)
    if certificate is not None:
        obstruction = check_reachability_obstruction(certificate, start, goal, rules)
        if tagged(obstruction, UNREACHABLE):
            return record(SEARCH, UNREACHABLE, M.Zero, E, obstruction)
    if not valid_state(start) or not valid_state(goal):
        return record(SEARCH, UNKNOWN, M.Zero, E, obstruction)
    front = chain(record(QUEUE_NODE, start, E))
    back = E
    seen = chain(start)
    expanded = 0
    while front is not E or back is not E:
        if front is E:
            front, back = reverse(back), E
        node = head(front)
        front = tail(front)
        current, path = field(node, 0), field(node, 1)
        if equal(current, goal):
            return record(SEARCH, FOUND, natural(expanded), reverse(path), obstruction)
        if expanded >= budget:
            return record(SEARCH, BUDGET, natural(expanded), E, obstruction)
        expanded += 1
        for rule in items(structures(rules)):
            checked = checked_step(current, rule, rules)
            if not tagged(checked, CHECKED):
                continue
            after = field(checked, 1)
            if contains(seen, after):
                continue
            seen = M.Pair(after, seen)
            back = M.Pair(record(QUEUE_NODE, after, M.Pair(checked, path)), back)
    return record(SEARCH, EXHAUSTED, natural(expanded), E, obstruction)


def check_path(path, start, goal, rules):
    current = start
    for step in items(path):
        replay = check_transition(step, rules)
        if not tagged(replay, CHECKED) or not equal(field(field(replay, 0), 1), current):
            return False
        current = field(replay, 1)
    return equal(current, goal)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('replay', 'certificate'))
    parser.add_argument('path')
    parser.add_argument('--plus', action='store_true')
    args = parser.parse_args()
    try:
        term = load(args.path)
        rules = rule_set(args.plus)
        if args.operation == 'replay':
            result = check_transition(term, rules)
            print(canonical(result))
            return 0 if tagged(result, CHECKED) else 1
        status = verify_certificate(term, rules)
        print(status.symbol)
        return 0 if status is PROVED else 1
    except (ValueError, OSError, RecursionError) as exc:
        print('invalid serialized evidence: ' + str(exc))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
