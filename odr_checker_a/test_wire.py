from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
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
    ruleset_digest,
)
from odr_checker_a.wire import (
    MAX_FILE_BYTES,
    MAX_STEPS,
    POLICY_SCHEMA,
    PROOF_SCHEMA,
    WireFormatError,
    decode_checker_receipt,
    decode_policy,
    decode_proof,
    decode_ruleset,
    loads_strict,
    policy_data,
    proof_wire_data,
    ruleset_wire_data,
    write_json,
)


def atom(name: str) -> Atom:
    return Atom(name)


def app(head: str, *arguments) -> Application:
    return Application(atom(head), tuple(arguments))


X = Variable("x")
Y = Variable("y")
PARENT_RULE = RuleSpec(
    "parent_implies_ancestor",
    (app("parent", X, Y),),
    app("ancestor", X, Y),
)
RULESET = TrustedRuleSet((PARENT_RULE,))
DIGEST = ruleset_digest(RULESET)
ALICE = atom("alice")
BOB = atom("bob")
PARENT_AB = app("parent", ALICE, BOB)
ANCESTOR_AB = app("ancestor", ALICE, BOB)
POLICY = CheckPolicy(
    "wire-session",
    ANCESTOR_AB,
    (PARENT_AB,),
    ("candidate-wire",),
    True,
)
PROOF = ProofReceipt(
    "wire-session",
    DIGEST,
    ANCESTOR_AB,
    (PARENT_AB,),
    (ProofStep("parent_implies_ancestor", ("p0",), ANCESTOR_AB),),
    "s0",
    CandidateScope("candidate-wire", "wire-session", DIGEST),
)


def encoded(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


class WireRoundTripTests(unittest.TestCase):
    def test_round_trips_all_input_documents(self):
        self.assertEqual(loads_strict(encoded(policy_data(POLICY)), decode_policy), POLICY)
        self.assertEqual(loads_strict(encoded(ruleset_wire_data(RULESET)), decode_ruleset), RULESET)
        self.assertEqual(loads_strict(encoded(proof_wire_data(PROOF)), decode_proof), PROOF)

    def test_ruleset_wire_order_is_canonical(self):
        second = RuleSpec("a_first", (), atom("axiom"))
        forward = ruleset_wire_data(TrustedRuleSet((PARENT_RULE, second)))
        reverse = ruleset_wire_data(TrustedRuleSet((second, PARENT_RULE)))
        self.assertEqual(forward, reverse)


class StrictDecodingTests(unittest.TestCase):
    def assert_wire_error(self, data: bytes, decoder, code: str):
        with self.assertRaises(WireFormatError) as caught:
            loads_strict(data, decoder)
        self.assertEqual(caught.exception.code, code)

    def test_rejects_unknown_field(self):
        data = policy_data(POLICY)
        data["surprise"] = True
        self.assert_wire_error(encoded(data), decode_policy, "UNKNOWN_FIELD")

    def test_rejects_missing_field(self):
        data = proof_wire_data(PROOF)
        del data["final_ref"]
        self.assert_wire_error(encoded(data), decode_proof, "MISSING_FIELD")

    def test_rejects_duplicate_json_field(self):
        data = b'{"schema":"' + POLICY_SCHEMA.encode() + b'","schema":"x"}'
        self.assert_wire_error(data, decode_policy, "DUPLICATE_FIELD")

    def test_rejects_truncated_json(self):
        self.assert_wire_error(b'{"schema":', decode_proof, "INVALID_JSON")

    def test_rejects_wrong_schema_version(self):
        data = proof_wire_data(PROOF)
        data["schema"] = "ctm.odr.checker-a.proof-receipt.v999"
        self.assert_wire_error(encoded(data), decode_proof, "SCHEMA_MISMATCH")

    def test_rejects_variable_in_concrete_proof(self):
        data = proof_wire_data(PROOF)
        data["goal"] = {"var": "x"}
        self.assert_wire_error(encoded(data), decode_proof, "VARIABLE_NOT_ALLOWED")

    def test_rejects_excessive_term_depth(self):
        term = {"atom": "bottom"}
        for _ in range(130):
            term = {"app": {"head": {"atom": "nest"}, "args": [term]}}
        data = policy_data(POLICY)
        data["goal"] = term
        self.assert_wire_error(encoded(data), decode_policy, "TERM_DEPTH_LIMIT")

    def test_rejects_excessive_steps(self):
        data = proof_wire_data(PROOF)
        data["steps"] = [data["steps"][0]] * (MAX_STEPS + 1)
        self.assert_wire_error(encoded(data), decode_proof, "COLLECTION_LIMIT")

    def test_rejects_oversized_file_before_json_decode(self):
        self.assert_wire_error(b" " * (MAX_FILE_BYTES + 1), decode_proof, "FILE_SIZE_LIMIT")


class ColdProcessTests(unittest.TestCase):
    def _write_inputs(self, root: Path, proof: ProofReceipt = PROOF):
        policy_path = root / "policy.json"
        rules_path = root / "rules.json"
        proof_path = root / "proof.json"
        write_json(policy_path, policy_data(POLICY))
        write_json(rules_path, ruleset_wire_data(RULESET))
        write_json(proof_path, proof_wire_data(proof))
        return policy_path, rules_path, proof_path

    def _run(self, root: Path, output_name: str, proof: ProofReceipt = PROOF):
        policy_path, rules_path, proof_path = self._write_inputs(root, proof)
        output_dir = root / output_name
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        command = (
            sys.executable,
            "-m",
            "odr_checker_a.cli",
            "--policy",
            str(policy_path),
            "--rules",
            str(rules_path),
            "--proof",
            str(proof_path),
            "--output-dir",
            str(output_dir),
        )
        return subprocess.run(
            command,
            cwd=Path(__file__).resolve().parents[1],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        ), output_dir

    def test_cold_replay_is_deterministic_and_content_addressed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, first_dir = self._run(root, "first")
            second, second_dir = self._run(root, "second")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            first_files = list(first_dir.iterdir())
            second_files = list(second_dir.iterdir())
            self.assertEqual(len(first_files), 1)
            self.assertEqual(len(second_files), 1)
            self.assertEqual(first_files[0].name, second_files[0].name)
            self.assertEqual(first_files[0].read_bytes(), second_files[0].read_bytes())
            result = json.loads(first_files[0].read_text(encoding="utf-8"))
            replayed_receipt = loads_strict(first_files[0].read_bytes(), decode_checker_receipt)
            self.assertTrue(result["accepted"])
            self.assertEqual(result["code"], "ACCEPTED")
            self.assertTrue(replayed_receipt.accepted)
            self.assertEqual(replayed_receipt.code, "ACCEPTED")
            expected_name = (
                "sha256-"
                + hashlib.sha256(first_files[0].read_bytes()).hexdigest()
                + ".checker-receipt.json"
            )
            self.assertEqual(first_files[0].name, expected_name)

    def test_digest_tampering_returns_rejection_and_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tampered = replace(PROOF, ruleset_digest="sha256:tampered", candidate_scope=None)
            policy = replace(POLICY, require_candidate_scope=False)
            policy_path = root / "policy.json"
            rules_path = root / "rules.json"
            proof_path = root / "proof.json"
            write_json(policy_path, policy_data(policy))
            write_json(rules_path, ruleset_wire_data(RULESET))
            write_json(proof_path, proof_wire_data(tampered))
            output_dir = root / "out"
            result = subprocess.run(
                (
                    sys.executable,
                    "-m",
                    "odr_checker_a.cli",
                    "--policy",
                    str(policy_path),
                    "--rules",
                    str(rules_path),
                    "--proof",
                    str(proof_path),
                    "--output-dir",
                    str(output_dir),
                ),
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            artifact = next(output_dir.iterdir())
            receipt = json.loads(artifact.read_text(encoding="utf-8"))
            self.assertEqual(receipt["code"], "RULESET_DIGEST_MISMATCH")

    def test_corrupt_input_returns_format_error_without_artifact(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            policy_path, rules_path, proof_path = self._write_inputs(root)
            proof_path.write_text('{"schema":', encoding="utf-8")
            output_dir = root / "out"
            result = subprocess.run(
                (
                    sys.executable,
                    "-m",
                    "odr_checker_a.cli",
                    "--policy",
                    str(policy_path),
                    "--rules",
                    str(rules_path),
                    "--proof",
                    str(proof_path),
                    "--output-dir",
                    str(output_dir),
                ),
                cwd=Path(__file__).resolve().parents[1],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            error = json.loads(result.stderr)
            self.assertEqual(error["code"], "INVALID_JSON")
            self.assertFalse(output_dir.exists())


if __name__ == "__main__":
    unittest.main()
