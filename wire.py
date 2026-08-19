"""Step 42: deterministic canonical byte encoding for machine terms.

WIRE FORMAT (version WIRE1), one UTF-8 line per section:
  term      := atom | "(" term " " term ")"        (a Pair is "(head tail)")
  atom      := "E"                                 M.EmptyList
             | "T" | "F"                           M.truth_value / M.false_value
             | "Z"                                 M.Zero
             | "V"                                 M.VarTag
             | "L:" name                           labels-module singleton
             | "C:" pct                            M.Char (percent-encoded symbol)
             | "G:" digits                         M.GMPRep (decimal text)
             | "A:" index                          anonymous atom (Thingy et al.)
Anonymous atoms are numbered by first appearance in head-first traversal
order, so identity sharing inside one blob is preserved and re-serializing
a deserialized blob reproduces the bytes exactly (canonical fixed point).
Anonymous atoms deserialize as fresh Thingy objects: sharing inside one
blob survives, identity across blobs does not — durable structures should
carry labeled nodes. Char and GMPRep tokens are interned per blob so
structural equality of the rebuilt term matches the original.
Traversal and parsing are iterative: no recursion limits on deep chains.
Checkpoints (save_checkpoint/load_checkpoint) store version, proposal
store, and ledger records/misses as one WIRE1 document of four sections.
This module is substrate-only: it must never import from search/.
"""

from __future__ import annotations

import os
import urllib.parse

from . import machine as M
from . import labels as Lmod

_WIRE_HEADER = "WIRE1"


def _label_map():
    mapping = {}
    for name in sorted(vars(Lmod)):
        if name.endswith("Label") and name != "ConstructorLabel":
            value = getattr(Lmod, name)
            if getattr(value, "id", None) is not None:
                mapping[value] = name
    return mapping


def _special_atoms():
    return {
        M.EmptyList: "E",
        M.truth_value: "T",
        M.false_value: "F",
        M.Zero: "Z",
        M.VarTag: "V",
    }


def serialize_term(term):
    labels = _label_map()
    specials = _special_atoms()
    anonymous = {}
    pieces = []
    close_marker = object()
    work = [term]
    while work:
        current = work.pop()
        if current is close_marker:
            pieces.append(")")
            continue
        if current in specials:
            pieces.append(specials[current])
            continue
        if M.IsPair(current)() is M.truth_value:
            pieces.append("(")
            work.append(close_marker)
            work.append(M.Tail(current)())
            work.append(M.Head(current)())
            continue
        if current in labels:
            pieces.append("L:" + labels[current])
            continue
        symbol = getattr(current, "symbol", None)
        if symbol is not None:
            pieces.append("C:" + urllib.parse.quote(symbol, safe=""))
            continue
        if getattr(current, "_mpz_value", None) is not None:
            pieces.append("G:" + str(current()))
            continue
        if current not in anonymous:
            anonymous[current] = len(anonymous)
        pieces.append("A:" + str(anonymous[current]))
    return " ".join(pieces).encode("utf-8")


def deserialize_term(blob):
    text = blob.decode("utf-8")
    tokens = text.replace("(", " ( ").replace(")", " ) ").split()
    anonymous = {}
    interned = {}
    stack = [[]]
    for token in tokens:
        if token == "(":
            stack.append([])
            continue
        if token == ")":
            frame = stack.pop()
            stack[-1].append(M.Pair(frame[0], frame[1]))
            continue
        if token == "E":
            value = M.EmptyList
        elif token == "T":
            value = M.truth_value
        elif token == "F":
            value = M.false_value
        elif token == "Z":
            value = M.Zero
        elif token == "V":
            value = M.VarTag
        elif token.startswith("L:"):
            value = getattr(Lmod, token[2:])
        elif token.startswith("C:"):
            if token not in interned:
                interned[token] = M.Char(urllib.parse.unquote(token[2:]))
            value = interned[token]
        elif token.startswith("G:"):
            if token not in interned:
                interned[token] = M.GMPRep(token[2:])
            value = interned[token]
        else:
            index = token[2:]
            if index not in anonymous:
                anonymous[index] = M.Thingy()
            value = anonymous[index]
        stack[-1].append(value)
    return stack[0][0]


def serialize_version(graph_version):
    return serialize_term(graph_version)


def deserialize_version(blob):
    return deserialize_term(blob)


def serialize_proposal_store(proposal_store):
    return serialize_term(proposal_store)


def deserialize_proposal_store(blob):
    return deserialize_term(blob)


def serialize_ledger(ledger):
    bundle = M.Pair(ledger.records, M.Pair(ledger.misses, M.EmptyList))
    return serialize_term(bundle)


def deserialize_ledger(blob, registry=M.EmptyList):
    from .graph import FiringLedger

    bundle = deserialize_term(blob)
    ledger = FiringLedger(registry)
    ledger.records = M.Head(bundle)()
    ledger.results = ledger.records
    ledger.misses = M.Head(M.Tail(bundle)())()
    return ledger


def save_checkpoint(path, graph_version, proposal_store, ledger):
    lines = [
        _WIRE_HEADER,
        serialize_version(graph_version).decode("utf-8"),
        serialize_proposal_store(proposal_store).decode("utf-8"),
        serialize_ledger(ledger).decode("utf-8"),
    ]
    payload = "\n".join(lines) + "\n"
    temporary = path + ".tmp"
    with open(temporary, "w", encoding="utf-8") as handle:
        handle.write(payload)
    os.replace(temporary, path)
    return path


def load_checkpoint(path, registry=M.EmptyList):
    with open(path, "r", encoding="utf-8") as handle:
        lines = handle.read().splitlines()
    if lines[0] != _WIRE_HEADER:
        return M.EmptyList
    graph_version = deserialize_version(lines[1].encode("utf-8"))
    proposal_store = deserialize_proposal_store(lines[2].encode("utf-8"))
    ledger = deserialize_ledger(lines[3].encode("utf-8"), registry)
    return M.Pair(
        graph_version,
        M.Pair(proposal_store, M.Pair(ledger, M.EmptyList)),
    )
