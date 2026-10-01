"""Isolated INV-0 validation. Run with /usr/bin/python3, no runtime activation.

--artifacts writes the bounded laboratory outputs after running every test.
"""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
I = importlib.import_module(ROOT.name + '.invariant_experiment')
M = I.M
P = I.P


def replace(term, index, value):
    fields = list(I.items(I.tail(term)))
    fields[index] = value
    return I.record(I.head(term), *fields)


def resign_attempt(attempt):
    return replace(attempt, 0, I.digest(I.tail(I.tail(attempt))))


def resign_certificate(cert):
    return replace(cert, 0, I.digest(I.tail(I.tail(cert))))


def replay_process(term, operation='replay', plus=False):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'evidence.json'
        I.save(path, term)
        cmd = ['/usr/bin/python3', '-B', '-m', ROOT.name + '.invariant_experiment', operation, str(path)]
        if plus:
            cmd.append('--plus')
        return subprocess.run(cmd, cwd=ROOT.parent, capture_output=True, text=True,
                              timeout=30, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))


def setup_experiment():
    rules = I.rule_set()
    corpus = I.training(rules)
    mining = I.mine(I.field(corpus, 1), rules)
    candidates = list(I.items(I.field(mining, 0)))
    cert = I.certify(candidates[1], rules, I.field(mining, 2))
    checked = next(t for t in I.items(I.field(corpus, 1)) if I.tagged(t, I.CHECKED))
    return rules, corpus, mining, candidates, cert, checked


class INV0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules, cls.corpus, cls.mining, cls.candidates, cls.cert, cls.checked = setup_experiment()

    def assertTag(self, term, tag):
        self.assertTrue(I.tagged(term, tag), I.canonical(term)[:1500])

    def test_checked_transition_round_trip(self):
        result = replay_process(self.checked)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertTag(I.decode(json.loads(result.stdout)), I.CHECKED)
        self.assertEqual(replay_process(self.cert, 'certificate').returncode, 0)

    def test_tampered_after_state_rejected(self):
        bad = replace(self.checked, 1, I.state(1))
        self.assertEqual(replay_process(bad).returncode, 1)
        self.assertTag(I.check_transition(bad, self.rules), I.REJECTED)

    def tampered_attempt(self, index, value):
        # Recompute the attempt hash so tests also exercise semantic checking,
        # rather than relying solely on a content hash mismatch.
        a = resign_attempt(replace(I.field(self.checked, 0), index, value))
        return replace(self.checked, 0, a)

    def test_tampered_rule_rejected(self):
        other = list(I.items(I.structures(self.rules)))[1]
        bad = self.tampered_attempt(2, I.rule_id(other))
        self.assertEqual(replay_process(bad).returncode, 1)
        self.assertTag(I.check_transition(bad, self.rules), I.REJECTED)

    def test_tampered_substitution_rejected(self):
        bad = self.tampered_attempt(4, I.E)
        self.assertEqual(replay_process(bad).returncode, 1)
        self.assertTag(I.check_transition(bad, self.rules), I.REJECTED)

    def test_tampered_rule_set_rejected(self):
        bad = self.tampered_attempt(3, I.scope_id(I.rule_set(True)))
        self.assertEqual(replay_process(bad).returncode, 1)
        self.assertTag(I.check_transition(bad, self.rules), I.REJECTED)

    def test_length_candidate_has_checked_counterexample(self):
        self.assertIs(I.field(self.candidates[0], 4), I.REFUTED)
        w = I.head(I.field(self.mining, 2))
        self.assertTag(w, I.BROKEN)
        self.assertTag(I.check_transition(I.field(w, 1), self.rules), I.CHECKED)
        self.assertEqual(I.integer(I.field(w, 2)), 0)
        self.assertEqual(I.integer(I.field(w, 3)), 2)

    def test_parity_candidate_emerges_from_observer_grammar(self):
        self.assertIs(I.field(self.candidates[1], 4), I.PROPOSED)
        self.assertEqual(len(list(I.items(I.field(self.candidates[1], 2)))), 11)
        self.assertIs(I.field(self.candidates[1], 3), I.E)

    def test_timeout_is_not_counterexample(self):
        result = I.mine(I.field(self.corpus, 1), self.rules, timeout=True)
        self.assertIs(I.field(result, 2), I.E)
        self.assertTrue(all(I.field(c, 4) is I.UNRESOLVED for c in I.items(I.field(result, 0))))
        result = I.mine(I.field(self.corpus, 1), self.rules, I.field(self.mining, 2), timeout=True)
        self.assertIs(I.field(result, 2), I.E)
        self.assertTrue(all(I.field(c, 4) is I.UNRESOLVED for c in I.items(I.field(result, 0))))

    def test_alpha_renaming_does_not_change_candidate(self):
        renamed = I.rule_set(rename=True)
        corpus = I.training(renamed)
        mined = I.mine(I.field(corpus, 1), renamed)
        self.assertEqual([I.field(c, 4) for c in I.items(I.field(mined, 0))],
                         [I.field(c, 4) for c in self.candidates])
        self.assertTag(I.preservation(I.field(self.candidates[1], 0), renamed), I.PROVED)
        # Display-only rename leaves exact semantic identity unchanged.
        labels = I.chain(*(I.entry('unrelated' + str(i), r)
                           for i, r in enumerate(I.items(I.structures(self.rules)))))
        self.assertTrue(I.equal(I.scope_id(labels), I.scope_id(self.rules)))

    def test_retained_counterexample_reused(self):
        result = I.mine(I.field(self.corpus, 1), self.rules, I.field(self.mining, 2))
        self.assertEqual(I.integer(I.field(result, 4)), 1)
        self.assertEqual(I.integer(I.field(result, 3)), 24)
        self.assertIs(I.field(I.head(I.field(result, 0)), 4), I.REFUTED)

    def check_delta(self, index, expected):
        proofs = list(I.items(I.field(self.cert, 5)))
        self.assertEqual(len(proofs), 3)
        difference = list(I.items(I.field(proofs[index], 3)))
        self.assertEqual(I.integer(difference[0]) - I.integer(difference[1]), expected)
        self.assertIs(I.verify_certificate(self.cert, self.rules), I.PROVED)

    def test_parity_certificate_covers_add_pair(self):
        self.check_delta(0, 2)

    def test_parity_certificate_covers_remove_pair(self):
        self.check_delta(1, -2)

    def test_parity_certificate_covers_swap_pair(self):
        self.check_delta(2, 0)

    def test_trace_agreement_alone_is_not_certificate(self):
        self.assertIs(I.verify_certificate(self.candidates[1], self.rules), I.INVALID)
        forged = resign_certificate(replace(self.cert, 5, I.E))
        self.assertIs(I.verify_certificate(forged, self.rules), I.INVALID)
        # A forged candidate supported by even-only traces cannot certify R_plus.
        fake = replace(self.candidates[1], 1, I.scope_id(I.rule_set(True)))
        self.assertTag(I.certify(fake, I.rule_set(True)), I.REFUTED)

    def test_unsupported_rule_shape_does_not_pass(self):
        r = I.variable('unsupported-rest')
        x = I.variable('unsupported-x')
        bad_shapes = [P.Rule(r, M.Pair(r, r)), P.Rule(r, x),
                      P.Rule(M.Pair(x, r), M.Pair(r, x)),
                      P.Rule(M.Pair(x, M.Pair(x, r)), r),
                      P.Rule(r, I.E), P.Rule(M.Pair(I.E, r), r)]
        for rule in bad_shapes:
            with self.subTest(shape=I.canonical(rule)):
                rules = I.chain(I.entry('arbitrary', rule))
                self.assertTag(I.preservation(I.field(self.cert, 1), rules), I.UNSUPPORTED)
        malformed = P.Rule(r, r)
        malformed.inputs = I.chain(I.chain(r, r), r)
        self.assertTag(I.preservation(I.field(self.cert, 1), I.chain(I.entry('bad', malformed))), I.UNSUPPORTED)

    def test_odd_goal_checked_unreachable(self):
        for start, goal in [(0, 5), (2, 7), (4, 9)]:
            out = I.check_reachability_obstruction(self.cert, I.state(start), I.state(goal), self.rules)
            self.assertTag(out, I.UNREACHABLE)
            result = I.bfs(I.state(start), I.state(goal), self.rules, certificate=self.cert)
            self.assertIs(I.field(result, 0), I.UNREACHABLE)
            self.assertEqual(I.integer(I.field(result, 1)), 0)

    def test_equal_parity_returns_unknown_not_reachable(self):
        self.assertTag(I.check_reachability_obstruction(self.cert, I.state(0), I.state(4), self.rules), I.UNKNOWN)
        self.assertTag(I.check_reachability_obstruction(self.cert, I.state(0), I.state(0), self.rules), I.UNKNOWN)

    def test_reachable_even_goal_not_pruned(self):
        result = I.bfs(I.state(0), I.state(4), self.rules, certificate=self.cert)
        self.assertIs(I.field(result, 0), I.FOUND)
        self.assertTrue(I.check_path(I.field(result, 2), I.state(0), I.state(4), self.rules))
        self.assertEqual(len(list(I.items(I.field(result, 2)))), 2)

    def test_old_certificate_rejected_for_r_plus(self):
        before = I.canonical(self.cert)
        self.assertIs(I.verify_certificate(self.cert, I.rule_set(True)), I.SCOPE)
        self.assertEqual(replay_process(self.cert, 'certificate', True).returncode, 1)
        self.assertTag(I.check_reachability_obstruction(self.cert, I.state(0), I.state(1), I.rule_set(True)), I.SCOPE)
        self.assertEqual(I.canonical(self.cert), before)
        self.assertIs(I.verify_certificate(self.cert, self.rules), I.PROVED)

    def test_add_one_breaks_parity(self):
        rules = I.rule_set(True)
        proof = I.preservation(I.field(self.cert, 1), rules)
        self.assertTag(proof, I.REFUTED)
        w = I.field(proof, 0)
        self.assertTag(w, I.BROKEN)
        self.assertTag(I.check_transition(I.field(w, 1), rules), I.CHECKED)
        self.assertNotEqual(I.integer(I.field(w, 2)), I.integer(I.field(w, 3)))
        self.assertIs(I.field(I.field(I.field(w, 1), 0), 1), I.E)

    def test_odd_goal_reachable_under_r_plus(self):
        rules = I.rule_set(True)
        result = I.bfs(I.state(0), I.state(1), rules, certificate=self.cert)
        self.assertIs(I.field(result, 0), I.FOUND)
        self.assertTag(I.field(result, 3), I.SCOPE)
        self.assertEqual(len(list(I.items(I.field(result, 2)))), 1)
        self.assertTrue(I.check_path(I.field(result, 2), I.state(0), I.state(1), rules))

    def test_candidate_is_inert(self):
        with patch.object(I, 'check_reachability_obstruction', side_effect=AssertionError('implicit activation')):
            I.mine(I.field(self.corpus, 1), self.rules)
            I.certify(self.candidates[1], self.rules)
            baseline = I.bfs(I.state(0), I.state(5), self.rules, budget=1)
        self.assertIs(I.field(baseline, 0), I.BUDGET)

    def test_no_live_knowledge_mutation(self):
        C = importlib.import_module(ROOT.name + '.constructors')
        registry = C.AllConstructors
        # Snapshot all reachable public structural slots, including registry tree.
        def fingerprint(root):
            seen = set()
            pending = [root]
            rows = []
            while pending:
                obj = pending.pop()
                if id(obj) in seen or not hasattr(obj, '__dict__'):
                    continue
                seen.add(id(obj))
                fields = []
                for name, value in vars(obj).items():
                    fields.append((name, id(value)))
                    if hasattr(value, '__dict__'):
                        pending.append(value)
                rows.append((id(obj), tuple(sorted(fields))))
            return sorted(rows)
        baseline = fingerprint(registry)
        zero_value = M.Zero.value
        with patch.object(C, 'set_all_constructors', side_effect=AssertionError('global registry write')):
            rules, corpus, mining, candidates, cert, checked = setup_experiment()
            I.verify_certificate(cert, rules)
            I.bfs(I.state(0), I.state(4), rules, certificate=cert)
            self.assertTag(I.check_transition(I.decode(I.encode(checked)), rules), I.CHECKED)
        self.assertIs(C.AllConstructors, registry)
        self.assertIs(M.Zero.value, zero_value)
        self.assertEqual(fingerprint(registry), baseline)

    def test_performance_work_counters(self):
        for start, goal in [(0, 5), (2, 7), (4, 9)]:
            result = I.bfs(I.state(start), I.state(goal), self.rules)
            self.assertIs(I.field(result, 0), I.BUDGET)
            self.assertEqual(I.integer(I.field(result, 1)), 64)
        proof = I.preservation(I.field(self.cert, 1), self.rules)
        self.assertGreater(I.integer(I.field(proof, 1)), 0)
        self.assertEqual(I.integer(I.field(self.mining, 3)), 44)

    def test_failure_and_open_outcomes_not_refutations(self):
        rule = I.head(I.structures(self.rules))
        for budget, obligations in [(0, I.E), (512, I.chain(I.symbol('pending/test')))]:
            a = I.make_attempt(I.E, rule, self.rules, budget, obligations)
            self.assertTag(I.produce(a, self.rules), I.OPEN)
            self.assertTag(I.check_transition(I.record(I.PROPOSAL, a, I.state(2)), self.rules), I.OPEN)
        a = I.make_attempt(I.E, rule, self.rules)
        with patch.object(M, 'Instantiate', side_effect=RuntimeError('injected crash')):
            failed = I.produce(a, self.rules)
        self.assertTag(failed, I.FAILURE)
        mined = I.mine(I.chain(failed), self.rules)
        self.assertIs(I.field(mined, 2), I.E)
        self.assertTrue(all(I.field(c, 4) is I.UNRESOLVED for c in I.items(I.field(mined, 0))))

    def test_position_counting_and_arbitrary_opaque_tokens(self):
        opaque = I.symbol('token/neither-A-nor-B')
        repeated = I.chain(opaque, opaque, opaque)
        self.assertEqual(I.integer(I.length(repeated)), 3)
        for rule in I.items(I.structures(self.rules)):
            checked = I.checked_step(repeated, rule, self.rules)
            self.assertTag(checked, I.CHECKED)
            self.assertTrue(I.equal(I.observe(I.field(self.cert, 1), repeated),
                                    I.observe(I.field(self.cert, 1), I.field(checked, 1))))

    def test_certificate_forgery_rejected_after_rehash(self):
        for index, value in [(1, I.record(I.LENGTH)), (2, I.symbol('other-domain')),
                             (4, I.E), (5, I.tail(I.field(self.cert, 5))), (6, I.E)]:
            bad = resign_certificate(replace(self.cert, index, value))
            self.assertIs(I.verify_certificate(bad, self.rules), I.INVALID)
        bad_scope = resign_certificate(replace(self.cert, 3, I.scope_id(I.rule_set(True))))
        self.assertIs(I.verify_certificate(bad_scope, I.rule_set(True)), I.INVALID)

    def test_invalid_domain_and_malformed_codec(self):
        self.assertTag(I.check_reachability_obstruction(self.cert, I.TOKEN_A, I.E, self.rules), I.UNKNOWN)
        for payload in [None, {}, ['nat', -1], ['nat', True], ['atom', []], ['execute', 'anything']]:
            with self.assertRaises(ValueError):
                I.decode(payload)

    def test_rule_round_trip_preserves_binding_identity(self):
        rules = I.decode(I.encode(self.rules))
        self.assertTag(I.checked_step(I.E, I.head(I.structures(rules)), rules), I.CHECKED)
        self.assertIs(I.verify_certificate(self.cert, rules), I.PROVED)

    def test_checker_crash_and_actual_timeout_are_unresolved(self):
        for error, tag in [(TimeoutError('injected'), I.OPEN),
                           (RuntimeError('injected'), I.FAILURE),
                           (RecursionError('injected'), I.FAILURE)]:
            with patch.object(M, 'Match', side_effect=error):
                outcome = I.check_transition(self.checked, self.rules)
                self.assertTag(outcome, tag)
                mined = I.mine(I.chain(self.checked), self.rules)
            self.assertIs(I.field(mined, 2), I.E)
            self.assertTrue(all(I.field(c, 4) is I.UNRESOLVED for c in I.items(I.field(mined, 0))))

    def test_retained_evidence_is_rechecked_after_reload(self):
        retained = I.decode(I.encode(I.field(self.mining, 2)))
        result = I.mine(I.E, self.rules, retained)
        self.assertIs(I.field(I.head(I.field(result, 0)), 4), I.REFUTED)
        witness = I.head(retained)
        forged_step = replace(I.field(witness, 1), 1, I.state(1))
        forged_witness = replace(witness, 1, forged_step)
        result = I.mine(I.E, self.rules, I.chain(forged_witness))
        self.assertIs(I.field(result, 2), I.E)
        self.assertTrue(all(I.field(c, 4) is I.UNRESOLVED for c in I.items(I.field(result, 0))))

    def test_structural_rule_change_invalidates_without_renaming(self):
        rules = I.rule_set()
        first = I.head(I.structures(rules))
        r = P.RulePattern(first)()
        first.inputs = P.Rule(r, M.Pair(I.TOKEN_A, r)).inputs
        self.assertFalse(I.equal(I.scope_id(rules), I.scope_id(self.rules)))
        self.assertIs(I.verify_certificate(self.cert, rules), I.SCOPE)
        self.assertTag(I.preservation(I.field(self.cert, 1), rules), I.REFUTED)

    def test_tampering_cannot_be_hidden_by_rehashing_transition(self):
        attempt = I.field(self.checked, 0)
        bad_after = I.state(1)
        forged_proof = I.record(I.TRANSITION_PROOF, I.VERSION, I.scope_id(self.rules),
                                I.digest(I.chain(attempt, bad_after)))
        forged = I.record(I.CHECKED, attempt, bad_after, forged_proof)
        self.assertTag(I.check_transition(forged, self.rules), I.REJECTED)

    def test_malformed_evidence_shapes_fail_closed(self):
        for term in [I.record(I.CHECKED),
                     I.append(self.checked, I.chain(I.TOKEN_A))]:
            self.assertTag(I.check_transition(term, self.rules), I.REJECTED)
        bad = resign_certificate(I.append(self.cert, I.chain(I.TOKEN_A)))
        self.assertIs(I.verify_certificate(bad, self.rules), I.INVALID)
        self.assertTag(I.certify(I.record(I.CANDIDATE), self.rules), I.UNRESOLVED)


def write_artifacts(directory):
    """Serialization/report boundary: host containers are appropriate here."""
    directory.mkdir(parents=True, exist_ok=True)
    rules, corpus, mined, candidates, cert, checked = setup_experiment()
    def save(name, term):
        I.save(directory / name, term)
    save('training_transitions.json', corpus)
    save('rejected_length_candidate.json', I.chain(candidates[0], I.field(mined, 2)))
    save('parity_candidate.json', candidates[1])
    save('parity_certificate.json', cert)
    save('checked_transition.json', checked)
    save('observer_observations.json', I.field(mined, 1))
    save('r_even_rules.json', rules)
    save('r_plus_rules.json', I.rule_set(True))
    proof = I.preservation(I.field(cert, 1), rules)
    evolved = I.preservation(I.field(cert, 1), I.rule_set(True))
    save('r_plus_counterexample.json', evolved)
    rerun = I.mine(I.field(corpus, 1), rules, I.field(mined, 2))
    save('mining_reuse.json', rerun)
    timeout = I.mine(I.field(corpus, 1), rules, timeout=True)
    save('mining_timeout.json', timeout)
    rule = I.head(I.structures(rules))
    open_attempt = I.make_attempt(I.E, rule, rules, obligations=I.chain(I.symbol('inv0/lab-residual')))
    budget_attempt = I.make_attempt(I.E, rule, rules, budget=0)
    with patch.object(M, 'Instantiate', side_effect=RuntimeError('injected crash')):
        failure = I.produce(I.field(checked, 0), rules)
    save('injected_outcomes.json', I.chain(
        I.chain(open_attempt, I.produce(open_attempt, rules)),
        I.chain(budget_attempt, I.produce(budget_attempt, rules)),
        I.check_transition(checked, rules, timeout=True), failure))
    valid = replay_process(checked)
    cert_replay = replay_process(cert, 'certificate')
    (directory / 'transition_replay.log').write_text(
        'Fresh /usr/bin/python3 -B -m ' + ROOT.name + '.invariant_experiment replay <checked_transition.json>; timeout=30s\n'
        + 'transition exit=' + str(valid.returncode) + '\n' + valid.stdout + valid.stderr
        + 'certificate exit=' + str(cert_replay.returncode) + '\n' + cert_replay.stdout)
    tamper_log = []
    for name, index, value in [('rule', 2, I.rule_id(list(I.items(I.structures(rules)))[1])),
                                ('substitution', 4, I.E), ('rule_set', 3, I.scope_id(I.rule_set(True)))]:
        attempt = resign_attempt(replace(I.field(checked, 0), index, value))
        bad = replace(checked, 0, attempt)
        result = replay_process(bad)
        assert result.returncode == 1
        tamper_log.append(name + ': REJECTED (fresh process exit=1; attempt hash recomputed)\n' + result.stdout)
        save('tampered_' + name + '.json', bad)
    bad = replace(checked, 1, I.state(1))
    result = replay_process(bad)
    assert result.returncode == 1
    tamper_log.append('after_state: REJECTED (fresh process exit=1)\n' + result.stdout)
    save('tampered_after_state.json', bad)
    (directory / 'tamper_rejections.log').write_text('\n'.join(tamper_log))
    tasks = []
    reach_log = []
    for start, goal in [(0, 5), (2, 7), (4, 9)]:
        baseline = I.bfs(I.state(start), I.state(goal), rules)
        assisted = I.bfs(I.state(start), I.state(goal), rules, certificate=cert)
        tasks.append({'start_length': start, 'goal_length': goal,
                      'baseline_status': I.field(baseline, 0).symbol,
                      'baseline_expansions': I.integer(I.field(baseline, 1)),
                      'assisted_status': I.field(assisted, 0).symbol,
                      'assisted_expansions': I.integer(I.field(assisted, 1))})
        reach_log.append(I.canonical(assisted))
    even = I.bfs(I.E, I.state(4), rules, certificate=cert)
    plus = I.bfs(I.E, I.state(1), I.rule_set(True), certificate=cert)
    save('reachable_even_path.json', I.field(even, 2))
    save('reachable_r_plus_path.json', I.field(plus, 2))
    (directory / 'r_even_reachability.log').write_text('\n'.join(reach_log) + '\n' + I.canonical(even) + '\n')
    (directory / 'r_plus_scope_invalidation.log').write_text(
        'old certificate: ' + I.verify_certificate(cert, I.rule_set(True)).symbol + '\n'
        + 'fresh preservation: ' + I.head(evolved).symbol + '\n'
        + 'historical certificate: ' + I.verify_certificate(cert, rules).symbol + '\n'
        + I.canonical(plus) + '\n')
    checked_terms = [t for t in I.items(I.field(corpus, 1)) if I.tagged(t, I.CHECKED)]
    checker_work = sum(I.work_size(I.field(I.field(t, 0), 1))
                       + I.work_size(I.lookup_rule(rules, I.field(I.field(t, 0), 2)))
                       + I.work_size(I.field(t, 1)) for t in checked_terms)
    performance = {
        'date': '2026-09-19', 'interpreter': sys.executable, 'python_version': sys.version,
        'base_sha': '428ecdc146e38de3481222bed7bddeb3c08e1b2d',
        'requested_reference_sha': '742c806505338525527219a4a94dde9b47df86e0',
        'training_state_count': 5, 'attempt_count': 15, 'checked_trace_count': len(checked_terms),
        'rejected_match_count': 4, 'candidate_count': 2,
        'retained_counterexamples_even': len(list(I.items(I.field(mined, 2)))),
        'retained_counterexamples_including_extension': 2,
        'schema_checker_structural_nodes': I.integer(I.field(proof, 1)),
        'transition_checker_nodes_per_full_corpus_replay': checker_work,
        'training_success_checker_passes': 2,
        'training_success_checker_nodes': 2 * checker_work,
        'mining_observer_evaluations': I.integer(I.field(mined, 3)),
        'mining_transition_replays': 2 * len(checked_terms),
        'mining_transition_checker_nodes': 2 * checker_work,
        'remining_observer_evaluations': I.integer(I.field(rerun, 3)),
        'reused_counterexamples': I.integer(I.field(rerun, 4)),
        'certificate_bytes': (directory / 'parity_certificate.json').stat().st_size,
        'holdouts': tasks,
        'reachable_control_expansions': I.integer(I.field(even, 1)),
        'reachable_control_path_steps': len(list(I.items(I.field(even, 2)))),
        'extension_control_expansions': I.integer(I.field(plus, 1)),
        'extension_control_path_steps': len(list(I.items(I.field(plus, 2)))),
        'metric_definition': 'One expansion pops a non-goal state and tries every rule; checker units count visited input/output/rule structural nodes. Not CPU instructions or timings.',
        'overhead_caveat': 'Canonical hashing, allocations, matching internals, and FIFO/seen scans are not included in node work units. Certificate replay includes schema checking and retained witness replay; storage bytes reported separately.',
        'serialized_term_artifact_bytes_excluding_performance_json': sum(p.stat().st_size for p in directory.iterdir() if p.suffix == '.json' and p.name != 'performance_comparison.json'),
    }
    witness = I.field(I.head(I.field(mined, 2)), 1)
    performance['certificate_replay_checker_nodes'] = I.integer(I.field(proof, 1)) + (
        I.work_size(I.field(I.field(witness, 0), 1))
        + I.work_size(I.lookup_rule(rules, I.field(I.field(witness, 0), 2)))
        + I.work_size(I.field(witness, 1)))
    (directory / 'performance_comparison.json').write_text(json.dumps(performance, indent=2) + '\n')


if __name__ == '__main__':
    artifacts = '--artifacts' in sys.argv
    if artifacts:
        sys.argv.remove('--artifacts')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(INV0Tests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.wasSuccessful() and artifacts:
        write_artifacts(ROOT / 'verification' / 'inv0_artifacts' / '2026-09-19')
    raise SystemExit(0 if result.wasSuccessful() else 1)
