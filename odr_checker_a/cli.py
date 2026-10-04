"""Cold-process command line boundary for ODR checker A."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .checker import check_proof
from .wire import (
    WireFormatError,
    decode_policy,
    decode_proof,
    decode_ruleset,
    load_file,
    write_content_addressed_receipt,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Verify one inert expanded-proof receipt")
    parser.add_argument("--policy", required=True, type=Path, help="evaluator-owned task policy JSON")
    parser.add_argument("--rules", required=True, type=Path, help="trusted ruleset snapshot JSON")
    parser.add_argument("--proof", required=True, type=Path, help="expanded proof receipt JSON")
    parser.add_argument("--output-dir", required=True, type=Path, help="content-addressed artifact directory")
    return parser


def _wire_error(error: WireFormatError) -> None:
    sys.stderr.write(
        json.dumps(
            {"accepted": False, "code": error.code, "message": error.message},
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        policy = load_file(args.policy, decode_policy)
        rules = load_file(args.rules, decode_ruleset)
        proof = load_file(args.proof, decode_proof)
        receipt = check_proof(proof, rules, policy)
        output_path = write_content_addressed_receipt(args.output_dir, receipt)
    except WireFormatError as error:
        _wire_error(error)
        return 2
    except OSError as error:
        _wire_error(WireFormatError("FILE_WRITE_ERROR", str(error)))
        return 2
    sys.stdout.write(str(output_path) + "\n")
    return 0 if receipt.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
