#!/usr/bin/env python3
"""cur_artifact_schema.py — executable raw-artifact schema checker + G-ENG schema emitter.

The frozen G-ENG evaluator lane is:

    bundle -> tools/cur_extract_evidence.py -> evidence manifest
           -> tools/cur_grade_artifact.py     -> C1..C6 verdicts

This module is the *schema* layer that sits in front of the extractor. It validates a raw
frozen bundle's *structure* before the extractor runs, and emits a machine-readable schema
(and the Markdown specification) from ONE declarative field-definition table.

SCOPE / HOST TOOL BOUNDARY
--------------------------
Host-side tooling under tools/, exactly like the extractor and grader. It does NOT construct
machine values or machine terms and is NOT part of the machine runtime (core.py / labels.py /
packs). The standing constraints on machine-native code (no Python lists/dicts/bools AS MACHINE
VALUES; no isinstance/type/getattr/callable in the ENGINE) govern the machine implementation, not
this evaluator. Like the grader it deliberately avoids isinstance/type/getattr/callable and uses
only identity / attribute-availability checks. It never reads a grader-pinned expected table, and
it never claims a mathematical result.

CAPABILITY CEILING (stated plainly, because it is load-bearing)
---------------------------------------------------------------
Schema validity NEVER implies mathematical validity. This module establishes, at most:

  SCHEMA_VALID              - the top-level shape, id uniqueness, citation arrays, collection
                              shapes, numeric domains, and declared canonical move forms all hold.
  CHECKABLE_CONTENT_PRESENT - (reported as metadata, never as a verdict) whether the payload
                              fields a given check C1..C6 needs are present and well-formed, so the
                              extractor handler has something to compute on rather than empty input.

It NEVER establishes:

  CHECK_ESTABLISHED - an evidence bit set by actual computation against the pinned problem. That is
                      the extractor's checked handlers' job, not this module's.
  PROOF_REPLAYED    - tier-3 full proof-checker replay of arbitrary cited nodes. This lane is
                      tier-2.5 (re-derives pinned E3/E4/E7 facts by fixed computation); it does not
                      and cannot replay an arbitrary proof.

So a bundle can be SCHEMA_VALID yet produce CANNOT_DETERMINE downstream when the required payload
is absent, empty, or unrelated. A bundle that is SCHEMA_VALID is not therefore true or even
checkable; it is merely structurally well formed.

COMMANDS
--------
  check <bundle.json|bundle_dir>
      Validate structure. Exit 0 = schema valid; exit 2 = malformed / unsupported /
      contradictory. Prints a JSON report (deterministic, no timestamps).
  emit-json
      Write the machine-readable schema to stdout (deterministic, no timestamps).
  emit-markdown
      Write the Markdown specification to stdout (deterministic, no timestamps).

Both emitted forms are generated from the single FIELD_TABLE below, never by hand.

DERIVATION PROMISE
------------------
Every field record below is derived from what *tools/cur_extract_evidence.py*'s checked handlers
(and the shared support-resolution) reads. Role names only select a handler; a field is
listed because a handler reads it by name. Unknown keys are tolerated by the extractor (they are
ignored), so this checker reports presence/validity of the *known* fields rather than rejecting
unknown fields — matching extractor semantics.
"""

import importlib
import json
import os
import sys

# --------------------------------------------------------------------- pinned identities
# Pin to the extractor/grader identities so the emitted schema and the drift test agree with the
# implementations they describe. Importing cur_grade_artifact (as the extractor does) gives the
# grader-side constants; importing cur_extract_evidence gives the extractor-side constants. Both are
# host tools under tools/ and are load-bearing inputs to this spec, not machine code.
_GRADER = importlib.import_module("cur_grade_artifact")
_EXTRACTOR = importlib.import_module("cur_extract_evidence")

SCHEMA_VERSION = _GRADER.SCHEMA_VERSION
RULESET_ID = _GRADER.RULESET_ID
BUNDLE_SCHEMA = _EXTRACTOR.BUNDLE_SCHEMA
EXTRACTOR_VERSION = _EXTRACTOR.EXTRACTOR_VERSION
CONTRACT_SET = ("E3", "E4", "E7")
CHECKS = ("C1", "C2", "C3", "C4", "C5", "C6")

# Pinned source identities the ruleset/spec were derived from (grader + extractor side).
PINNED_CONTRACT_REFS = _GRADER.PINNED_CONTRACT_REFS
PINNED_CONTRACT_COMMITS = _EXTRACTOR.PINNED_CONTRACT_COMMITS
PINNED_CONTRACT_DIGESTS = _EXTRACTOR.PINNED_CONTRACT_DIGESTS
PINNED_CONTRACT_IN_TREE = _EXTRACTOR.PINNED_CONTRACT_IN_TREE
PINNED_RUBRIC_REF = _GRADER.PINNED_RUBRIC_REF
PINNED_RUBRIC_COMMIT = _EXTRACTOR.PINNED_RUBRIC_COMMIT
PINNED_RUBRIC_DIGEST = _EXTRACTOR.PINNED_RUBRIC_DIGEST

# Pinned canonical constants from the extractor handlers (single source of truth for the spec).
E3_N = _EXTRACTOR.E3_N
E3_MOVE_PAIRS = list(_EXTRACTOR.E3_MOVE_PAIRS)
E3_ODD_N = _EXTRACTOR.E3_ODD_N
E4_TWO_HOUSES = _EXTRACTOR.E4_TWO_HOUSES
E4_MAX_DEGREE = _EXTRACTOR.E4_MAX_DEGREE
E7_WINDOW = _EXTRACTOR.E7_WINDOW
E7_MODULUS = _EXTRACTOR.E7_MODULUS
E7_ODD_WINDOW = _EXTRACTOR.E7_ODD_WINDOW


# --------------------------------------------------------------------- JSON shape probes
# Same style as the extractor/grader: identity + attribute-availability checks, never isinstance.
def _is_mapping(value):
    if value is True or value is False or value is None:
        return False
    try:
        value.keys
    except AttributeError:
        return False
    return True


def _is_array(value):
    if value is True or value is False or value is None:
        return False
    if _is_mapping(value):
        return False
    try:
        value.append
    except AttributeError:
        return False
    return True


def _is_str(value):
    if value is True or value is False or value is None:
        return False
    if _is_mapping(value) or _is_array(value):
        return False
    try:
        value.lower
    except AttributeError:
        return False
    return True


def _is_json_bool(value):
    return value is True or value is False


def _is_number(value):
    if _is_json_bool(value) or value is None:
        return False
    if _is_mapping(value) or _is_array(value) or _is_str(value):
        return False
    return True


# --------------------------------------------------------------------- declarative field table
# ONE source of truth for both emit-json and emit-markdown. Each record describes one field the
# extractor's handlers (or the shared support resolution) reads. 'checks' lists which
# grader checks the field feeds (or 'structural' when it only shapes resolution).
FIELD_TABLE = [
    # ---------------- global / structural ----------------
    {
        "field": "schema",
        "scope": "bundle",
        "roles": [],
        "contracts": ("E3", "E4", "E7"),
        "shape": "string",
        "required": True,
        "checks": ("structural",),
        "domain": 'must equal "geng-bundle/v2"',
        "cd_when_absent": "extractor exit 2 (unsupported bundle schema); no manifest",
        "canonical": 'BUNDLE_SCHEMA = "geng-bundle/v2"',
        "limit": "equality to the fixed literal; no schema negotiation",
    },
    {
        "field": "contract",
        "scope": "bundle",
        "roles": [],
        "contracts": ("E3", "E4", "E7"),
        "shape": "string",
        "required": True,
        "checks": ("structural",),
        "domain": "member of {E3, E4, E7}",
        "cd_when_absent": "extractor exit 2 (unsupported contract); no manifest",
        "canonical": "one of E3 / E4 / E7",
        "limit": "family fixed to the three glued contracts",
    },
    {
        "field": "candidate.id",
        "scope": "bundle",
        "roles": ["candidate"],
        "contracts": ("E3", "E4", "E7"),
        "shape": "string",
        "required": True,
        "checks": ("structural",),
        "domain": "non-empty string",
        "cd_when_absent": "extractor exit 2 (candidate must have a string id); no manifest",
        "canonical": "candidate id",
        "limit": "must be unique across claims+candidate+nodes+records",
    },
    {
        "field": "candidate.cites",
        "scope": "bundle",
        "roles": ["candidate"],
        "contracts": ("E3", "E4", "E7"),
        "shape": "array<id>",
        "required": False,
        "checks": ("structural",),
        "domain": "array of string ids",
        "cd_when_absent": "candidate support not traced -> support-dependent checks stay CD",
        "canonical": "array of cites/refs ids",
        "limit": "only string ids validated; an unresolved ref -> CD, not a schema reject",
    },
    {
        "field": "claims",
        "scope": "bundle",
        "roles": [],
        "contracts": ("E3", "E4", "E7"),
        "shape": "array<object>",
        "required": False,
        "checks": ("structural",),
        "domain": "array; each has a string 'id' and optional 'kind'/'text'",
        "cd_when_absent": "assumptions absent -> no top-level support to resolve",
        "canonical": "array of assumption records",
        "limit": "ids are pooled for uniqueness but absent claims are not a reject",
    },
    {
        "field": "nodes",
        "scope": "bundle",
        "roles": [],
        "contracts": ("E3", "E4", "E7"),
        "shape": "array<object>",
        "required": True,
        "checks": ("structural",),
        "domain": "array; each node has a string 'id', optional 'role'/'kind'/'cites'/'payload'",
        "cd_when_absent": "extractor exit 2 (nodes must be an array); no manifest",
        "canonical": "array of node records",
        "limit": "a node with no payload is schema-valid (role-only) but not checkable",
    },
    {
        "field": "records",
        "scope": "bundle",
        "roles": [],
        "contracts": ("E3", "E4", "E7"),
        "shape": "object<name, array<object>>",
        "required": False,
        "checks": ("structural",),
        "domain": "mapping name -> array; each record has 'id'/'role'/'cites'/'payload'",
        "cd_when_absent": "no named record collections; handler falls back to node roles",
        "canonical": "object of named record arrays",
        "limit": "record ids pooled for uniqueness; absent records are not a reject",
    },
    {
        "field": "node.cites / node.refs",
        "scope": "node",
        "roles": [],
        "contracts": ("E3", "E4", "E7"),
        "shape": "array<id>",
        "required": False,
        "checks": ("structural",),
        "domain": "array of string ids ('cites' preferred, 'refs' accepted as alias)",
        "cd_when_absent": "derived with no support -> upstream, CD for dependent bits",
        "canonical": "array of support ids",
        "limit": "unresolved/self/circular refs are CD, not schema rejects",
    },
    {
        "field": "node.kind",
        "scope": "node",
        "roles": [],
        "contracts": ("E3", "E4", "E7"),
        "shape": "string",
        "required": False,
        "checks": ("structural",),
        "domain": "'assumption' or 'derived'; absent defaults to derived",
        "cd_when_absent": "treated as derived (assumption only if kind == assumption)",
        "canonical": "'assumption' or 'derived'",
        "limit": "controls resolution classification only; never sets an evidence bit",
    },
    {
        "field": "node.payload",
        "scope": "node",
        "roles": [],
        "contracts": ("E3", "E4", "E7"),
        "shape": "object",
        "required": False,
        "checks": ("structural",),
        "domain": "object if present",
        "cd_when_absent": "role-only node -> all dependent checks CANNOT_DETERMINE",
        "canonical": "object of named payload fields",
        "limit": "an empty/absent payload is schema-valid but not checkable",
    },

    # ---------------- E3 payload fields ----------------
    {
        "field": "weights.vector",
        "scope": "payload",
        "roles": ["weights"],
        "contracts": ("E3",),
        "shape": "array<number>",
        "required": True,
        "checks": ("C1", "C2", "C3"),
        "domain": "length == E3_N (6); every element an integer",
        "cd_when_absent": "C1/C2/C3 CANNOT_DETERMINE (no vector to check)",
        "canonical": "length-6 integer vector",
        "limit": "checker verifies shape/length/numeric; kernel membership is computed by the extractor",
    },
    {
        "field": "weights.provenance",
        "scope": "payload",
        "roles": ["weights"],
        "contracts": ("E3",),
        "shape": "string",
        "required": True,
        "checks": ("C6",),
        "domain": "'derived' or 'supplied'",
        "cd_when_absent": "C6 CANNOT_DETERMINE (no provenance to classify)",
        "canonical": "'derived'",
        "limit": "string equality only; no semantic check of how it was derived",
    },
    {
        "field": "moves.pairs",
        "scope": "payload",
        "roles": ["moves"],
        "contracts": ("E3",),
        "shape": "array<[integer, integer]>",
        "required": True,
        "checks": ("C1", "C2"),
        "domain": "length == E3_N; pairs are adjacent sectors of the 6-cycle",
        "cd_when_absent": "move family undetermined -> C1/C2 stay CD",
        "canonical": "E3_MOVE_PAIRS (the pinned 6-cycle)",
        "limit": "checker validates shape; the extractor compares to the pinned family for family_ok",
    },
    {
        "field": "start.vector",
        "scope": "payload",
        "roles": ["start"],
        "contracts": ("E3",),
        "shape": "array<number>",
        "required": True,
        "checks": ("C3",),
        "domain": "length == E3_N (6); every element an integer",
        "cd_when_absent": "C3 CANNOT_DETERMINE (no start vector)",
        "canonical": "length-6 integer start vector",
        "limit": "checker validates shape, not the reading value",
    },
    {
        "field": "odd-control.target_n",
        "scope": "payload",
        "roles": ["odd-control"],
        "contracts": ("E3",),
        "shape": "number",
        "required": True,
        "checks": ("C4",),
        "domain": "== E3_ODD_N (5)",
        "cd_when_absent": "C4 CANNOT_DETERMINE (no odd-control size)",
        "canonical": "target_n = 5",
        "limit": "checker validates numeric equality to the pinned odd size; kernel dim is computed",
    },
    {
        "field": "generation.on_candidate",
        "scope": "payload",
        "roles": ["generation"],
        "contracts": ("E3",),
        "shape": "array<number>",
        "required": True,
        "checks": ("C5",),
        "domain": "length == E3_N (6)",
        "cd_when_absent": "C5 CANNOT_DETERMINE (no candidate-on reading)",
        "canonical": "length-6 integer reading",
        "limit": "checker validates shape; same-line check is computed by the extractor",
    },
    {
        "field": "generation.off_candidate",
        "scope": "payload",
        "roles": ["generation"],
        "contracts": ("E3",),
        "shape": "array<number> | null",
        "required": False,
        "checks": ("C5",),
        "domain": "null/empty (candidate removed) or array",
        "cd_when_absent": "defaults to candidate survives -> C5 can FAIL",
        "canonical": "null (removed) or empty array",
        "limit": "checker validates shape; deciding removal is the extractor's job",
    },

    # ---------------- E4 payload fields ----------------
    {
        "field": "params.houses",
        "scope": "payload",
        "roles": ["params", "hypothesis"],
        "contracts": ("E4",),
        "shape": "integer",
        "required": True,
        "checks": ("C2",),
        "domain": "== E4_TWO_HOUSES (2)",
        "cd_when_absent": "C2 CANNOT_DETERMINE (no house target)",
        "canonical": "houses = 2",
        "limit": "checker validates integer/equality; the partition claim is the extractor's",
    },
    {
        "field": "params.degree_bound",
        "scope": "payload",
        "roles": ["params", "hypothesis"],
        "contracts": ("E4",),
        "shape": "integer",
        "required": True,
        "checks": ("C1",),
        "domain": "<= E4_MAX_DEGREE (3)",
        "cd_when_absent": "C1 FAIL if a descent argument is present, else CANNOT_DETERMINE",
        "canonical": "degree_bound = 3",
        "limit": "checker validates integer/ordering; a descent-from-e_in-alone claim is graded by the extractor",
    },
    {
        "field": "moves.moves",
        "scope": "payload",
        "roles": ["moves"],
        "contracts": ("E4",),
        "shape": "array<move>",
        "required": True,
        "checks": ("C3",),
        "domain": "each move is a record; see canonical move forms below",
        "cd_when_absent": "C3 CANNOT_DETERMINE (no move record)",
        "canonical": "canonical form is {e_in, e_out}; {d, s} accepted as a documented alternate",
        "limit": "checker validates shape and dual-form equivalence; descent delta computed by the extractor",
    },
    {
        "field": "move.e_in",
        "scope": "payload",
        "roles": ["moves"],
        "contracts": ("E4",),
        "shape": "integer",
        "required": True,
        "checks": ("C3",),
        "domain": ">= 0; legal move requires e_in >= 2",
        "cd_when_absent": "move not parseable -> C3 may stay CD / FAIL",
        "canonical": "e_in (enemies in own house)",
        "limit": "checker validates non-negative integer",
    },
    {
        "field": "move.e_out",
        "scope": "payload",
        "roles": ["moves"],
        "contracts": ("E4",),
        "shape": "integer",
        "required": True,
        "checks": ("C3",),
        "domain": ">= 0",
        "cd_when_absent": "move not parseable -> C3 may stay CD / FAIL",
        "canonical": "e_out (enemies in the other house)",
        "limit": "checker validates non-negative integer",
    },
    {
        "field": "move.d / move.s",
        "scope": "payload",
        "roles": ["moves"],
        "contracts": ("E4",),
        "shape": "integer",
        "required": False,
        "checks": ("C3",),
        "domain": "d = e_in + e_out, s = e_in (documented alternate)",
        "cd_when_absent": "allowed; only the canonical e_in/e_out form is required",
        "canonical": "d = degree, s = same-house; e_in = s, e_out = d - s",
        "limit": "if both forms appear and disagree -> contradiction (schema reject)",
    },
    {
        "field": "bound.lower_bound",
        "scope": "payload",
        "roles": ["bound", "wellfounded"],
        "contracts": ("E4",),
        "shape": "integer",
        "required": True,
        "checks": ("C4",),
        "domain": ">= 0",
        "cd_when_absent": "C4 CANNOT_DETERMINE (no lower bound claimed)",
        "canonical": "lower_bound = 0",
        "limit": "checker validates integer/ordering",
    },
    {
        "field": "terminal.claim",
        "scope": "payload",
        "roles": ["terminal", "terminus"],
        "contracts": ("E4",),
        "shape": "string",
        "required": True,
        "checks": ("C5",),
        "domain": "'no_legal_move' or 'global_min'",
        "cd_when_absent": "C5 CANNOT_DETERMINE (no termination claim)",
        "canonical": "'no_legal_move'",
        "limit": "checker validates membership; the global-min overclaim is the extractor's",
    },
    {
        "field": "measure.provenance",
        "scope": "payload",
        "roles": ["measure", "monovariant"],
        "contracts": ("E4",),
        "shape": "string",
        "required": True,
        "checks": ("C6",),
        "domain": "'derived' or 'supplied'",
        "cd_when_absent": "C6 CANNOT_DETERMINE (no measure provenance)",
        "canonical": "'derived'",
        "limit": "string equality only",
    },

    # ---------------- E7 payload fields ----------------
    {
        "field": "params.window_width",
        "scope": "payload",
        "roles": ["params"],
        "contracts": ("E7",),
        "shape": "integer",
        "required": True,
        "checks": ("C1",),
        "domain": "== E7_WINDOW (4)",
        "cd_when_absent": "C1 CANNOT_DETERMINE (no family width)",
        "canonical": "window_width = 4",
        "limit": "checker validates integer/equality; derivation is the extractor's",
    },
    {
        "field": "params.modulus",
        "scope": "payload",
        "roles": ["params"],
        "contracts": ("E7",),
        "shape": "integer",
        "required": True,
        "checks": ("C1", "C2", "C4"),
        "domain": "== E7_MODULUS (4)",
        "cd_when_absent": "residue arithmetic undetermined -> dependent checks CD",
        "canonical": "modulus = 4",
        "limit": "checker validates integer/equality",
    },
    {
        "field": "samples.sequences",
        "scope": "payload",
        "roles": ["samples"],
        "contracts": ("E7",),
        "shape": "array<array<number>>",
        "required": True,
        "checks": ("C2",),
        "domain": "each sequence length >= declared window width (else window undefined)",
        "cd_when_absent": "C2 CANNOT_DETERMINE (no sample sequence)",
        "canonical": "array of numeric sequences of length >= window_width",
        "limit": "checker validates sequence shape + length-vs-width; residue delta computed by the extractor",
    },
    {
        "field": "samples.window_width",
        "scope": "payload",
        "roles": ["samples"],
        "contracts": ("E7",),
        "shape": "integer",
        "required": False,
        "checks": ("C2",),
        "domain": ">= 1; per-record override of the family width",
        "cd_when_absent": "falls back to params.window_width",
        "canonical": "per-record width, or the family width when absent",
        "limit": "a non-canonical width is graded by the extractor (width-not-4 FAIL), not a schema reject",
    },
    {
        "field": "separation.target_residue",
        "scope": "payload",
        "roles": ["separate", "separation"],
        "contracts": ("E7",),
        "shape": "integer",
        "required": True,
        "checks": ("C3",),
        "domain": "integer residue",
        "cd_when_absent": "C3 CANNOT_DETERMINE (no separation target)",
        "canonical": "target_residue != 0 when 4 does not divide n",
        "limit": "checker validates integer; the divide-4 separation is the extractor's",
    },
    {
        "field": "separation.start_residue",
        "scope": "payload",
        "roles": ["separate", "separation"],
        "contracts": ("E7",),
        "shape": "integer",
        "required": False,
        "checks": ("C3",),
        "domain": "integer residue",
        "cd_when_absent": "C3 uses target residue + n when present",
        "canonical": "integer start residue",
        "limit": "checker validates integer, not the residue relationship",
    },
    {
        "field": "separation.n",
        "scope": "payload",
        "roles": ["separate", "separation"],
        "contracts": ("E7",),
        "shape": "integer",
        "required": True,
        "checks": ("C3",),
        "domain": "integer length; separation requires n % 4 != 0",
        "cd_when_absent": "C3 CANNOT_DETERMINE (no length to divide)",
        "canonical": "n not divisible by 4",
        "limit": "checker validates integer; divisibility is the extractor's",
    },
    {
        "field": "odd-control.sample",
        "scope": "payload",
        "roles": ["control", "odd-control"],
        "contracts": ("E7",),
        "shape": "array<number>",
        "required": True,
        "checks": ("C4",),
        "domain": "numeric sequence; length >= E7_ODD_WINDOW (3)",
        "cd_when_absent": "C4 CANNOT_DETERMINE (no odd-width control sample)",
        "canonical": "length->=3 numeric sequence",
        "limit": "checker validates shape; the width-3 delta == {2} is computed by the extractor",
    },
    {
        "field": "rejected.candidates",
        "scope": "payload",
        "roles": ["rejected"],
        "contracts": ("E7",),
        "shape": "array<object>",
        "required": True,
        "checks": ("C5",),
        "domain": "each has 'name' and 'class' in the allowed set",
        "cd_when_absent": "C5 CANNOT_DETERMINE (no rejected-candidate classification)",
        "canonical": "class in {'not_invariant','preserved_but_non_separating','invariant','separating'}",
        "limit": "checker validates membership; the misclassification is the extractor's",
    },
    {
        "field": "observable.provenance",
        "scope": "payload",
        "roles": ["observable", "measure"],
        "contracts": ("E7",),
        "shape": "string",
        "required": True,
        "checks": ("C1", "C6"),
        "domain": "'derived' or 'supplied'",
        "cd_when_absent": "C1/C6 CANNOT_DETERMINE (no derived observable)",
        "canonical": "'derived'",
        "limit": "string equality only",
    },
]

# Per-contract, per-check payload-requirement map used only to compute CHECKABLE_CONTENT_PRESENT
# metadata (never a verdict). A key is the checks label; value is a list of (roles, field) that a
# handler needs present to have something to compute on.
CHECKABLE_CONTENT = {
    "E3": {
        "C1": (("weights", "vector"), ("moves", "pairs")),
        "C2": (("weights", "vector"), ("moves", "pairs")),
        "C3": (("weights", "vector"), ("start", "vector")),
        "C4": (("odd-control", "target_n"),),
        "C5": (("generation", "on_candidate"),),
        "C6": (("weights", "provenance"),),
    },
    "E4": {
        "C1": (("params", "degree_bound"),),
        "C2": (("params", "houses"),),
        "C3": (("moves", "moves"),),
        "C4": (("bound", "lower_bound"),),
        "C5": (("terminal", "claim"),),
        "C6": (("measure", "provenance"),),
    },
    "E7": {
        "C1": (("params", "window_width"), ("observable", "provenance")),
        "C2": (("samples", "sequences"),),
        "C3": (("separate", "target_residue"), ("separate", "n")),
        "C4": (("control", "sample"),),
        "C5": (("rejected", "candidates"),),
        "C6": (("observable", "provenance"),),
    },
}

# Allowed classification strings for E7 rejected candidates.
E7_REJECTED_CLASSES = (
    "not_invariant",
    "preserved_but_non_separating",
    "invariant",
    "separating",
)


# --------------------------------------------------------------------- bundle traversal
def _iter_role_items(bundle):
    """Yield (id, role, payload, kind, cites) for every node and every record entry."""
    for nd in (bundle.get("nodes") or []):
        if not _is_mapping(nd):
            continue
        cite_field = nd.get("cites")
        if cite_field is None:
            cite_field = nd.get("refs")
        yield (nd.get("id"), nd.get("role"), nd.get("payload"),
               nd.get("kind"), cite_field)
    records = bundle.get("records")
    if _is_mapping(records):
        for rname, arr in records.items():
            if not _is_array(arr):
                continue
            for r in arr:
                if not _is_mapping(r):
                    continue
                cite_field = r.get("cites")
                if cite_field is None:
                    cite_field = r.get("refs")
                yield (r.get("id"), r.get("role"), r.get("payload"),
                       r.get("kind"), cite_field)


def _roles_with_payload(bundle, contract):
    """Return {role: payload} for role items that carry a mapping payload."""
    out = {}
    for rid, role, payload, kind, cites in _iter_role_items(bundle):
        if not _is_str(role):
            continue
        if not _is_mapping(payload):
            continue
        if role not in out:
            out[role] = payload
    return out


# --------------------------------------------------------------------- structural validation
def _validate_structure(bundle, contract, errors):
    """Structural checks that mirror the extractor's _validate_bundle, plus id uniqueness."""
    if not _is_mapping(bundle):
        errors.append("bundle must be a JSON object")
        return

    if bundle.get("schema") != BUNDLE_SCHEMA:
        errors.append("unsupported bundle schema: %r" % (bundle.get("schema"),))

    if not _is_str(contract) or contract not in CONTRACT_SET:
        errors.append("unsupported contract: %r (expected E3/E4/E7)" % (contract,))

    cand = bundle.get("candidate")
    if not _is_mapping(cand):
        errors.append("bundle must have a 'candidate' object")
    elif not _is_str(cand.get("id")):
        errors.append("candidate must have a string 'id'")
    cand_cites = cand.get("cites") if _is_mapping(cand) else None
    if cand_cites is None and _is_mapping(cand):
        cand_cites = cand.get("refs")
    if _is_mapping(cand) and cand_cites is not None and not _is_array(cand_cites):
        errors.append("candidate.cites must be an array")

    claims = bundle.get("claims")
    if claims is not None and not _is_array(claims):
        errors.append("'claims' must be an array")

    nodes = bundle.get("nodes")
    if not _is_array(nodes):
        errors.append("'nodes' must be an array")
    else:
        for nd in nodes:
            if not _is_mapping(nd):
                errors.append("node must be an object")
                continue
            if not _is_str(nd.get("id")):
                errors.append("node must have a string 'id'")
            _check_cites_and_payload(nd, errors)

    records = bundle.get("records")
    if records is not None and not _is_mapping(records):
        errors.append("'records' must be an object")
    elif _is_mapping(records):
        for rname, arr in records.items():
            if not _is_array(arr):
                errors.append("records.%s must be an array" % (rname,))
                continue
            for r in arr:
                if not _is_mapping(r):
                    errors.append("records.%s entry must be an object" % (rname,))
                    continue
                _check_cites_and_payload(r, errors)

    # id uniqueness across claims + candidate + nodes + records.
    seen = set()
    for c in (claims or []):
        if _is_mapping(c) and _is_str(c.get("id")):
            _note_id(c["id"], seen, errors)
    if _is_mapping(cand) and _is_str(cand.get("id")):
        _note_id(cand["id"], seen, errors)
    for rid, role, payload, kind, cites in _iter_role_items(bundle):
        if _is_str(rid):
            _note_id(rid, seen, errors)


def _check_cites_and_payload(obj, errors):
    cites = obj.get("cites")
    if cites is None:
        cites = obj.get("refs")
    if cites is not None and not _is_array(cites):
        errors.append("cites must be an array (node %s)" % (obj.get("id"),))
    elif _is_array(cites):
        for c in cites:
            if not _is_str(c):
                errors.append("cite must be a string id (node %s)" % (obj.get("id"),))
    if obj.get("payload") is not None and not _is_mapping(obj.get("payload")):
        errors.append("payload must be an object (node %s)" % (obj.get("id"),))


def _note_id(oid, seen, errors):
    if oid in seen:
        errors.append("duplicate id %r" % (oid,))
    seen.add(oid)


def _read_int(payload, key):
    if not _is_mapping(payload):
        return None
    v = payload.get(key)
    if not _is_number(v):
        return None
    return int(v)


# --------------------------------------------------------------------- contract-specific checks
def _validate_contract(contract, bundle, errors):
    roles = _roles_with_payload(bundle, contract)

    if contract == "E3":
        _validate_e3(roles, errors)
    elif contract == "E4":
        _validate_e4(roles, errors)
    elif contract == "E7":
        _validate_e7(roles, errors)


def _validate_e3(roles, errors):
    w = roles.get("weights")
    if _is_mapping(w) and "vector" in w:
        vec = w["vector"]
        if not _is_array(vec) or not all(_is_number(x) for x in vec):
            errors.append("E3 weights.vector must be an array of numbers")
        elif len(vec) != E3_N:
            errors.append("E3 weights.vector length %s != pinned %s" % (len(vec), E3_N))
    m = roles.get("moves")
    if _is_mapping(m) and "pairs" in m:
        pairs = m["pairs"]
        if not _is_array(pairs):
            errors.append("E3 moves.pairs must be an array")
        else:
            for p in pairs:
                if not (_is_array(p) and len(p) == 2 and _is_number(p[0]) and _is_number(p[1])):
                    errors.append("E3 moves.pairs entry must be [integer, integer]")
    s = roles.get("start")
    if _is_mapping(s) and "vector" in s:
        sv = s["vector"]
        if not _is_array(sv) or not all(_is_number(x) for x in sv):
            errors.append("E3 start.vector must be an array of numbers")
        elif len(sv) != E3_N:
            errors.append("E3 start.vector length %s != pinned %s" % (len(sv), E3_N))
    oc = roles.get("odd-control")
    if _is_mapping(oc) and "target_n" in oc:
        t = _read_int(oc, "target_n")
        if t is None:
            errors.append("E3 odd-control.target_n must be an integer")
        elif t != E3_ODD_N:
            errors.append("E3 odd-control.target_n %s != pinned %s" % (t, E3_ODD_N))


def _validate_e4(roles, errors):
    # C1/C2 params.
    params = roles.get("params")
    if params is None:
        params = roles.get("hypothesis")
    if _is_mapping(params):
        if "houses" in params:
            h = _read_int(params, "houses")
            if h is None:
                errors.append("E4 params.houses must be an integer")
        if "degree_bound" in params:
            db = _read_int(params, "degree_bound")
            if db is None:
                errors.append("E4 params.degree_bound must be an integer")
            elif db > E4_MAX_DEGREE:
                errors.append("E4 params.degree_bound %s > pinned max %s" % (db, E4_MAX_DEGREE))

    # C3 moves: dual-form equivalence, else reject.
    moves = roles.get("moves")
    if _is_mapping(moves) and "moves" in moves:
        arr = moves["moves"]
        if not _is_array(arr):
            errors.append("E4 moves.moves must be an array")
        else:
            for mv in arr:
                if not _is_mapping(mv):
                    errors.append("E4 move must be an object")
                    continue
                has_e = ("e_in" in mv) and ("e_out" in mv)
                has_ds = ("d" in mv) and ("s" in mv)
                if not has_e and not has_ds:
                    errors.append("E4 move must have {e_in,e_out} or {d,s}")
                    continue
                e_in = _read_int(mv, "e_in")
                e_out = _read_int(mv, "e_out")
                d = _read_int(mv, "d")
                s = _read_int(mv, "s")
                if has_e and (e_in is None or e_out is None):
                    errors.append("E4 move e_in/e_out must be integers")
                if has_ds and (d is None or s is None):
                    errors.append("E4 move d/s must be integers")
                # dual-form contradiction check when both present.
                if has_e and has_ds:
                    if s != e_in or d != e_in + e_out:
                        errors.append(
                            "E4 move has contradictory e_in/e_out vs d/s "
                            "(s=%s e_in=%s d=%s sum=%s)" % (s, e_in, d, e_in + e_out))
                elif has_e:
                    if e_in < 0 or e_out < 0:
                        errors.append("E4 move e_in/e_out must be non-negative")
                elif has_ds:
                    if d < 0 or s < 0 or s > d:
                        errors.append("E4 move d/s invalid (0 <= s <= d)")

    # C4 bound.
    bound = roles.get("bound")
    if bound is None:
        bound = roles.get("wellfounded")
    if _is_mapping(bound) and "lower_bound" in bound:
        lb = _read_int(bound, "lower_bound")
        if lb is None:
            errors.append("E4 bound.lower_bound must be an integer")
        elif lb < 0:
            errors.append("E4 bound.lower_bound must be >= 0")

    # C5 terminal claim.
    terminal = roles.get("terminal")
    if terminal is None:
        terminal = roles.get("terminus")
    if _is_mapping(terminal) and "claim" in terminal:
        claim = terminal["claim"]
        if not _is_str(claim) or claim not in ("no_legal_move", "global_min"):
            errors.append("E4 terminal.claim must be 'no_legal_move' or 'global_min'")


def _validate_e7(roles, errors):
    params = roles.get("params")
    if _is_mapping(params):
        ww = _read_int(params, "window_width")
        if "window_width" in params and ww is None:
            errors.append("E7 params.window_width must be an integer")
        elif ww is not None and ww != E7_WINDOW:
            errors.append("E7 params.window_width %s != pinned %s" % (ww, E7_WINDOW))
        md = _read_int(params, "modulus")
        if "modulus" in params and md is None:
            errors.append("E7 params.modulus must be an integer")
        elif md is not None and md != E7_MODULUS:
            errors.append("E7 params.modulus %s != pinned %s" % (md, E7_MODULUS))

    # C2 samples: every sequence must be at least as long as its window width.
    samples = roles.get("samples")
    if _is_mapping(samples) and "sequences" in samples:
        seqs = samples["sequences"]
        if not _is_array(seqs):
            errors.append("E7 samples.sequences must be an array")
        else:
            declared_width = _read_int(samples, "window_width")
            family_width = declared_width if declared_width is not None else E7_WINDOW
            for seq in seqs:
                if not _is_array(seq) or not all(_is_number(x) for x in seq):
                    errors.append("E7 sample sequence must be an array of numbers")
                    continue
                if len(seq) < family_width:
                    errors.append(
                        "E7 sample sequence length %s < declared window width %s" % (
                            len(seq), family_width))

    # C3 separation.
    sep = roles.get("separate")
    if sep is None:
        sep = roles.get("separation")
    if _is_mapping(sep):
        for key in ("target_residue", "n"):
            if key in sep and _read_int(sep, key) is None:
                errors.append("E7 separation.%s must be an integer" % (key,))

    # C4 odd-width control.
    control = roles.get("control")
    if control is None:
        control = roles.get("odd-control")
    if _is_mapping(control) and "sample" in control:
        smp = control["sample"]
        if not _is_array(smp) or not all(_is_number(x) for x in smp):
            errors.append("E7 odd-control.sample must be an array of numbers")

    # C5 rejected classification.
    rejected = roles.get("rejected")
    if _is_mapping(rejected) and "candidates" in rejected:
        cands = rejected["candidates"]
        if not _is_array(cands):
            errors.append("E7 rejected.candidates must be an array")
        else:
            for c in cands:
                if not _is_mapping(c):
                    errors.append("E7 rejected candidate must be an object")
                    continue
                cls = c.get("class")
                if not _is_str(cls) or cls not in E7_REJECTED_CLASSES:
                    errors.append("E7 rejected candidate class %r not in allowed set" % (cls,))


# --------------------------------------------------------------------- checkable-content metadata
def _compute_checkable(contract, bundle):
    """Return {check: bool} whether the handler's payload fields are present, per contract."""
    roles = _roles_with_payload(bundle, contract)
    needs = CHECKABLE_CONTENT.get(contract, {})
    out = {}
    for check in CHECKS:
        reqs = needs.get(check, ())
        present = True
        for role, field in reqs:
            if role not in roles:
                present = False
                break
            payload = roles[role]
            # For checks keyed on a single field, require it present.
            if field and field not in payload:
                present = False
                break
            # sequences / moves / candidates are required to be non-empty arrays.
            if field in ("sequences", "moves", "candidates"):
                val = payload.get(field)
                if not _is_array(val) or len(val) == 0:
                    present = False
                    break
        out[check] = present
    return out


# --------------------------------------------------------------------- checker CLI
def check_bundle(bundle, contract_hint=None):
    """Return (ok, report). ok is True iff schema-valid; report is a JSON-safe dict."""
    errors = []
    contract = contract_hint if contract_hint is not None else bundle.get("contract")
    _validate_structure(bundle, contract, errors)
    if _is_str(contract) and contract in CONTRACT_SET:
        _validate_contract(contract, bundle, errors)
    checkable = _compute_checkable(contract, bundle) if _is_str(contract) and contract in CONTRACT_SET else {}
    report = {
        "schema_valid": len(errors) == 0,
        "contract": contract,
        "errors": errors,
        "states": {
            "SCHEMA_VALID": len(errors) == 0,
            "CHECKABLE_CONTENT_PRESENT": checkable,
            "CHECK_ESTABLISHED": False,
            "PROOF_REPLAYED": False,
        },
        "checkable_content": checkable,
    }
    return len(errors) == 0, report


def main(argv):
    if len(argv) < 2:
        sys.stderr.write(_USAGE + "\n")
        return 2
    cmd = argv[1]

    if cmd == "emit-json":
        sys.stdout.write(json.dumps(_build_schema_json(), sort_keys=True, separators=(",", ":")))
        sys.stdout.write("\n")
        return 0
    if cmd == "emit-markdown":
        sys.stdout.write(_build_schema_markdown())
        return 0
    if cmd == "check":
        if len(argv) < 3:
            sys.stderr.write(_USAGE + "\n")
            return 2
        src = argv[2]
        if os.path.isdir(src):
            jsons = sorted(f for f in os.listdir(src) if f.endswith(".json"))
            if len(jsons) != 1:
                sys.stderr.write("schema: directory must contain exactly one bundle json\n")
                return 2
            src = os.path.join(src, jsons[0])
        try:
            with open(src, "r", encoding="utf-8") as f:
                bundle = json.load(f)
        except OSError as e:
            sys.stderr.write("schema: cannot read bundle: %s\n" % (e,))
            return 2
        except ValueError as e:
            sys.stderr.write("schema: invalid JSON: %s\n" % (e,))
            return 2
        ok, report = check_bundle(bundle)
        sys.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")))
        sys.stdout.write("\n")
        return 0 if ok else 2

    sys.stderr.write(_USAGE + "\n")
    sys.stderr.write("schema: unknown command: %s\n" % (cmd,))
    return 2


_USAGE = (
    "usage: cur_artifact_schema.py <check <bundle.json|bundle_dir> | emit-json | emit-markdown>"
)


# --------------------------------------------------------------------- emitted schema (json + md)
def _build_schema_json():
    """Machine-readable schema, deterministic (no timestamps, sort_keys)."""
    contract_fields = {}
    for c in CONTRACT_SET:
        cfields = []
        for rec in FIELD_TABLE:
            if c in rec["contracts"]:
                cfields.append(rec)
        contract_fields[c] = cfields
    return {
        "spec": "G-ENG-ARTIFACT-SCHEMA",
        "schema_version": SCHEMA_VERSION,
        "ruleset_id": RULESET_ID,
        "bundle_schema": BUNDLE_SCHEMA,
        "extractor_version": EXTRACTOR_VERSION,
        "contracts": list(CONTRACT_SET),
        "checks": list(CHECKS),
        "pinned": {
            "contract_refs": PINNED_CONTRACT_REFS,
            "contract_commits": PINNED_CONTRACT_COMMITS,
            "contract_digests": PINNED_CONTRACT_DIGESTS,
            "contract_in_tree": PINNED_CONTRACT_IN_TREE,
            "rubric_ref": PINNED_RUBRIC_REF,
            "rubric_commit": PINNED_RUBRIC_COMMIT,
            "rubric_digest": PINNED_RUBRIC_DIGEST,
        },
        "canonical_constants": {
            "E3_N": E3_N,
            "E3_ODD_N": E3_ODD_N,
            "E4_TWO_HOUSES": E4_TWO_HOUSES,
            "E4_MAX_DEGREE": E4_MAX_DEGREE,
            "E7_WINDOW": E7_WINDOW,
            "E7_MODULUS": E7_MODULUS,
            "E7_ODD_WINDOW": E7_ODD_WINDOW,
        },
        "capability_ceiling": {
            "SCHEMA_VALID": "structure holds",
            "CHECKABLE_CONTENT_PRESENT": "payload present (metadata only)",
            "CHECK_ESTABLISHED": "not established by this module",
            "PROOF_REPLAYED": "not supported (tier-2.5 lane)",
        },
        "states": ["SCHEMA_VALID", "CHECKABLE_CONTENT_PRESENT", "CHECK_ESTABLISHED", "PROOF_REPLAYED"],
        "fields": FIELD_TABLE,
        "contract_fields": contract_fields,
    }


def _build_schema_markdown():
    """Markdown spec, deterministic (no timestamps)."""
    L = []
    L.append("# G-ENG-ARTIFACT-SCHEMA\n")
    L.append("Generated from the single declarative field table in `tools/cur_artifact_schema.py`, "
             "which is derived from what `tools/cur_extract_evidence.py`'s checked handlers read. "
             "It is the contract an author must satisfy before submitting a frozen artifact to the "
             "grader lane. No timestamps are embedded in this generated output.\n")
    L.append("- **Agent:** SCHEMA-eng")
    L.append("- **Evaluator-side, training-visible: no.**")
    L.append("- **Schema version:** `%d` (pinned to the grader `SCHEMA_VERSION`)." % SCHEMA_VERSION)
    L.append("- **Ruleset id:** `%s`" % RULESET_ID)
    L.append("- **Bundle schema:** `%s`" % BUNDLE_SCHEMA)
    L.append("- **Extractor version:** `%s`" % EXTRACTOR_VERSION)
    L.append("")

    L.append("## Capability ceiling (stated plainly)\n")
    L.append("This lane validates **checked, fixed-contract math**:\n")
    L.append("```text")
    L.append("frozen bundle -> cur_extract_evidence.py -> evidence manifest -> cur_grade_artifact.py")
    L.append("             -> C1..C6 verdicts")
    L.append("```")
    L.append("It is **tier-2.5**: it re-derives the pinned E3/E4/E7 facts (kernel, descent "
             "ΔH <= -1, mod-4 residue ΔS ≡ 0) by computation against the fixed problem. It does not "
             "read a bundle's self-declared verdict, and it does not tier-3 replay an arbitrary "
             "proof. A recognized role **never** establishes an evidence bit by itself — it only "
             "*selects* a handler.\n")
    L.append("The schema layer distinguishes four states and never conflates them:\n")
    L.append("| State | Meaning | Established by |")
    L.append("|---|---|---|")
    L.append("| `SCHEMA_VALID` | top-level shape, id uniqueness, citation arrays, collection shapes, numeric domains, and declared canonical move forms all hold | this module |")
    L.append("| `CHECKABLE_CONTENT_PRESENT` | the payload fields a check needs are present (metadata, never a verdict) | this module |")
    L.append("| `CHECK_ESTABLISHED` | an evidence bit set by actual computation against the pinned problem | the extractor's checked handlers |")
    L.append("| `PROOF_REPLAYED` | tier-3 full proof-checker replay of arbitrary cited nodes | **not supported** on this lane |")
    L.append("")
    L.append("**Schema validity never implies mathematical validity.** A bundle can be `SCHEMA_VALID` "
             "yet yield `CANNOT_DETERMINE` (or `FAIL`) downstream when its required payload is absent, "
             "empty, or unrelated.\n")

    L.append("## Global bundle shape\n")
    L.append("```json")
    L.append('{ "schema": "geng-bundle/v2", "contract": "E3 | E4 | E7",')
    L.append('  "candidate": { "id": "...", "role": "candidate", "cites": ["support-id", ...] },')
    L.append('  "claims": [ { "id": "...", "kind": "assumption", ... } ],')
    L.append('  "nodes": [ { "id": "...", "role": "...", "kind": "derived|assumption",')
    L.append('              "cites": ["support-id", ...], "payload": { ... } } ],')
    L.append('  "records": { "name": [ { "id": "...", "role": "...", "cites": [...], "payload": {...} } ] } }')
    L.append("```")
    L.append("**Required:** `schema` == `geng-bundle/v2`; `contract` in `{E3, E4, E7}`; a `candidate` "
             "object with a string `id`; `nodes` an array whose nodes have string `id`s, and (if "
             "present) string-array `cites`/`refs` and an object `payload`. **IDs must be unique** "
             "across `claims` + `candidate` + `nodes` + `records`.\n")
    L.append("Global malformations => `exit 2` (no manifest): duplicate id, non-array `cites`/"
             "`nodes`, non-object `payload`, unsupported schema, unsupported contract.\n")

    L.append("## Field definitions\n")
    L.append("Each record: field name (dotted), contract families, JSON shape, required/optional, "
             "numeric/domain constraint, checks fed, `CANNOT_DETERMINE`-when-absent effect, canonical "
             "representation, and the known validation limit of this schema layer.\n")
    for contract in CONTRACT_SET:
        L.append("### FIELDS `E%d` family\n" % _contract_num(contract))
        L.append("| field | contract | shape | required | domain | checks fed | CD-when-absent | canonical | validation limit |")
        L.append("|---|---|---|---|---|---|---|---|---|")
        for rec in FIELD_TABLE:
            if contract in rec["contracts"]:
                L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                    _mdfield(rec["field"]),
                    ", ".join(rec["contracts"]),
                    rec["shape"],
                    "yes" if rec["required"] else "no",
                    rec["domain"],
                    ", ".join(rec["checks"]),
                    rec["cd_when_absent"],
                    rec["canonical"],
                    rec["limit"],
                ))
        L.append("")

    L.append("## Canonical move forms\n")
    L.append("- **E3:** exact integer weights (length `E3_N` = `%d`), complete declared move family "
             "`E3_MOVE_PAIRS` = `%s`.\n" % (E3_N, _repr(E3_MOVE_PAIRS)))
    L.append("- **E4:** canonical move form is `{e_in, e_out}`; `{d, s}` (degree & same-house) is "
             "accepted only as a **documented alternate** (`e_in = s`, `e_out = d - s`). If both forms "
             "appear in one move and disagree, the schema is contradictory and rejected. Max degree "
             "`E4_MAX_DEGREE` = `%d`; `E4_TWO_HOUSES` = `%d`.\n" % (E4_MAX_DEGREE, E4_TWO_HOUSES))
    L.append("- **E7:** explicit sequence, window width `E7_WINDOW` = `%d`, modulus `E7_MODULUS` = "
             "`%d`, and flip samples; a sample sequence must be long enough to realize its window "
             "width (a shorter sequence with a declared width is a structural contradiction). Odd-width "
             "control uses `E7_ODD_WINDOW` = `%d`.\n" % (E7_WINDOW, E7_MODULUS, E7_ODD_WINDOW))

    L.append("## Pinned source identities\n")
    L.append("| identity | value |")
    L.append("|---|---|")
    L.append("| contract refs | %s |" % _repr(PINNED_CONTRACT_REFS))
    L.append("| contract commits | %s |" % _repr(PINNED_CONTRACT_COMMITS))
    L.append("| contract content digests | %s |" % _repr(PINNED_CONTRACT_DIGESTS))
    L.append("| in-tree contract paths | %s |" % _repr(PINNED_CONTRACT_IN_TREE))
    L.append("| rubric ref | `%s` (commit `%s`, digest `%s`) |" % (
        PINNED_RUBRIC_REF, PINNED_RUBRIC_COMMIT, PINNED_RUBRIC_DIGEST))

    L.append("\n## Notes\n")
    L.append("- A role only selects a handler; it does not itself assert a fact.")
    L.append("- Unknown payload keys are tolerated (ignored by the extractor); this layer reports "
             "known-field validity rather than rejecting unknown keys, matching extractor semantics.")
    L.append("- This generated output is deterministic: it embeds no timestamps and no run-specific "
             "state. Execution time and test results live in the separate verification artifact.")
    L.append("")
    return "\n".join(L)


def _contract_num(contract):
    return {"E3": 3, "E4": 4, "E7": 7}.get(contract)


def _mdfield(name):
    return "`%s`" % name


def _repr(value):
    return json.dumps(value, sort_keys=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
