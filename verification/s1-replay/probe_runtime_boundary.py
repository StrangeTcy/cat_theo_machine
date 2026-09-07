#!/usr/bin/env python3
"""Batch-B runtime-boundary probes (canonical S1 = 897c07c, adapted).

Three direct boundary checks, independent of the named-test runner:

  P1  construct and retrieve a source-bearing contract record.
  P2  a refused input (variable in relation position/slot) cannot become
      an accepted contract fact.
  P3  contract insertion installs a fact, not a proof rule.

Usage mirrors run_batch_b_tests.py (checkout must be importable as the
`cat_theo_machine` package).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(ROOT))

from cat_theo_machine.runtime import boot_from_packs
from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
import cat_theo_machine.machine as M
import cat_theo_machine.graph as G
import cat_theo_machine.labels as L
import cat_theo_machine.knowledge as K


def main():
    runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    graph = runtime.graph
    graph._search_disable_console = M.truth_value
    empty = M.EmptyList
    registry = M.FromContextGetConstructors(graph)()

    # --- P1: construct and retrieve a source-bearing contract record ---
    name = M.Char("divides")
    arity_atom = G.RelationContractArity(name, M.two)()
    ext_atom = G.RelationContractExtensionalAt(name, M.one)()
    source = M.Char("operator-session-2026-09-05")
    record = G.RelationContracts(M.Pair(arity_atom, M.Pair(ext_atom, empty)), source)()

    src = G.RelationContractsSource(record)()
    prov = G.RelationContractsProvenance(record)()
    atoms = G.RelationContractsAtoms(record)()

    print("P1 source retrieves (same object):",
          M.IdentityCompare(src, source)() is M.truth_value)
    print("P1 atoms-head == arity_atom:",
          M.IdentityCompare(M.Head(atoms)(), arity_atom)() is M.truth_value)
    print("P1 provenance == ContractFactLabel:",
          M.IdentityCompare(prov, L.ContractFactLabel)() is M.truth_value)
    print("P1 note: source retrieval is BY IDENTITY; M.Char does not intern,")
    print("    so a freshly-constructed Char of the same text compares unequal.")

    # --- P2: a refused input cannot become an accepted contract ---
    var = M.Pair(M.VarTag, M.Pair(M.Char("?r"), empty))
    refused = G.RelationContractArity(var, M.two)()
    print("P2 refused atom is EmptyList:",
          M.IdentityCompare(refused, empty)() is M.truth_value)
    bad_record = G.RelationContracts(M.Pair(refused, empty), M.Char("bad-source"))()
    loaded = G.RelationContractsInsert(M.EmptyTree, bad_record, registry)()
    has_refused = K.KnowledgeTrieHasFact(loaded, refused, registry)()
    print("P2 refused atom NOT a fact after insert:", has_refused is M.false_value)

    # --- P3: contract insertion installs a fact, not a proof rule ---
    print("P3 contract atom IsLawTerm false:", G.IsLawTerm(arity_atom)() is M.false_value)
    good_loaded = G.RelationContractsInsert(M.EmptyTree, record, registry)()
    print("P3 inserted atom IS a fact:",
          K.KnowledgeTrieHasFact(good_loaded, arity_atom, registry)() is M.truth_value)
    print("P3 inserted atom still not a law:", G.IsLawTerm(arity_atom)() is M.false_value)


if __name__ == "__main__":
    main()
