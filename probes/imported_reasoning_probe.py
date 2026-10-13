"""Regression probe: imported graph content is reasoning-accessible, not inert.

The round-trip probe shows imported nodes and edges survive a save and a load.
That is a storage claim. This one makes the stronger claim the acceptance
criterion actually asks for: the Machine's own matching and rewriting machinery
can consume the imported payload and derive new facts from it, and those derived
facts persist and reload like any other content.

The rule inverts an imported relationship:

    lives_in(SRC, DST)  ->  resident_of(DST, SRC)

It is a real `proof.Rule`, applied through `matching.Rewrite`, so the pattern is
extracted by `RulePattern` and matched by `M.Match` -- the same path the kernel
uses. Property edges (`label`, `note`) must NOT fire, which is what makes the
count a real discriminator rather than a tally of everything.

Finally the 20,000 derived edges are stored under `edges`, saved, reloaded, and
re-counted, closing the loop: import -> match -> derive -> persist -> reload.

Usage:
    python probes/imported_reasoning_probe.py [RELATIONS]
"""

import os
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ROOT))

from cat_theo_machine import machine as M
from cat_theo_machine import main as _Main
from cat_theo_machine import matching as _Matching
from cat_theo_machine import proof as P
from cat_theo_machine import runtime as _Runtime
from cat_theo_machine.core import VarTag
from cat_theo_machine.importers import csv_to_hypergraph as _Importer


def var(name):
    """A metavariable pattern: Pair(VarTag, Pair(name, EmptyList))."""
    return M.Pair(VarTag, M.Pair(M.Char(name), M.EmptyList))


def count_of(chain, registry):
    return M.Head(M.NatFromRep(M.CountRep(chain)(), registry)())()


def nat_from_host(value, registry):
    return M.Head(M.NatFromRep(M.GMPRep(value), registry)())()


def count_text(chain, registry):
    return M.GMPRepText(M.NatRepOf(count_of(chain, registry), registry)())()


def write_csv(path, header, rows):
    handle = open(path, "w", encoding="utf-8")
    try:
        handle.write(header)
        for row in rows:
            handle.write(row)
    finally:
        handle.close()


def main():
    argv = sys.argv
    relations = 20000
    if len(argv) > 1:
        relations = int(argv[1])
    nodes = relations // 10
    failures = 0

    work = tempfile.mkdtemp(prefix="reasoning-probe-")
    node_csv = os.path.join(work, "nodes.csv")
    edge_csv = os.path.join(work, "edges.csv")
    snapshot = os.path.join(work, "imported.json")
    derived_snapshot = os.path.join(work, "derived.json")

    node_rows = []
    for index in range(nodes):
        node_rows.append("n%d,Person,note-%d\n" % (index, index))
    edge_rows = []
    for index in range(relations):
        edge_rows.append("n%d,lives_in,n%d\n" % (index % nodes, (index * 7) % nodes))
    write_csv(node_csv, "id,label,note\n", node_rows)
    write_csv(edge_csv, "src,rel,dst\n", edge_rows)

    started = time.monotonic()
    runtime, _packs = _Runtime.boot_from_packs(
        _Main.PACK_PATHS, _Main._runtime_namespace()
    )
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    booted = time.monotonic()

    node_rows_read = _Importer.read_rows(node_csv)
    edge_rows_read = _Importer.read_rows(edge_csv)
    imported_nodes, imported_edges = _Importer.build_terms(
        node_rows_read, edge_rows_read
    )
    graph._replace_context(nodes=imported_nodes, edges=imported_edges)
    built = time.monotonic()

    # The metavariable terms must be the SAME objects in the pattern and in the
    # replacement: Instantiate resolves bindings against the pattern's var
    # terms, and a freshly built Char is never identity-equal to another. Building
    # them twice yields a rewrite that fires but substitutes nothing, which shows
    # up as a correct derived count with unswapped arguments.
    src_var = var("src")
    dst_var = var("dst")
    rule = P.Rule(
        M.Pair(
            M.Char("lives_in"),
            M.Pair(src_var, M.Pair(dst_var, M.EmptyList)),
        ),
        M.Pair(
            M.Char("resident_of"),
            M.Pair(dst_var, M.Pair(src_var, M.EmptyList)),
        ),
    )
    resident_symbol = M.Char("resident_of")

    derived = M.EmptyList
    sample_original = M.EmptyList
    sample_derived = M.EmptyList
    cursor = graph.edges
    while (
        M.IdentityCompare(cursor, M.EmptyList)() is M.false_value
        and M.IsPair(cursor)() is M.truth_value
    ):
        candidate = M.Head(cursor)()
        result_atom = M.Head(_Matching.Rewrite(rule, candidate, registry)())()
        if M.Compare(M.Head(result_atom)(), resident_symbol)() is M.truth_value:
            derived = M.Pair(result_atom, derived)
            if M.IdentityCompare(sample_derived, M.EmptyList)() is M.truth_value:
                sample_original = candidate
                sample_derived = result_atom
        cursor = M.Tail(cursor)()
    rewritten = time.monotonic()

    checks = (
        ("derived", count_of(derived, registry), relations),
        ("edges_untouched", count_of(graph.edges, registry), relations + nodes + nodes),
    )
    for name, counted, expected in checks:
        rendered = M.GMPRepText(M.NatRepOf(counted, registry)())()
        if M.NatEq(counted, nat_from_host(expected, registry), registry)() is M.truth_value:
            print("PASS %s=%s" % (name, rendered))
        else:
            failures += 1
            print("FAIL %s expected %d got %s" % (name, expected, rendered))

    # The inversion must actually swap the arguments, not just relabel the head.
    original_args = M.Tail(sample_original)()
    derived_args = M.Tail(sample_derived)()
    swapped_head = M.Compare(
        M.Head(derived_args)(), M.Head(M.Tail(original_args)())()
    )() is M.truth_value
    swapped_tail = M.Compare(
        M.Head(M.Tail(derived_args)())(), M.Head(original_args)()
    )() is M.truth_value
    if swapped_head and swapped_tail:
        print("PASS sample_args_swapped")
    else:
        failures += 1
        print("FAIL sample_args_swapped head=%s tail=%s" % (swapped_head, swapped_tail))

    graph._replace_context(edges=derived)
    _Runtime.save_runtime(runtime, derived_snapshot, _Main._runtime_namespace())
    saved = time.monotonic()

    reloaded = _Runtime.boot_from_snapshot(
        derived_snapshot, _Main._runtime_namespace()
    )
    reloaded_registry = M.FromContextGetConstructors(reloaded.graph)()
    found = M.EmptyList
    cursor = reloaded.graph.edges
    while (
        M.IdentityCompare(cursor, M.EmptyList)() is M.false_value
        and M.IsPair(cursor)() is M.truth_value
    ):
        candidate = M.Head(cursor)()
        if M.Compare(M.Head(candidate)(), resident_symbol)() is M.truth_value:
            found = M.Pair(candidate, found)
        cursor = M.Tail(cursor)()
    finished = time.monotonic()

    if M.NatEq(
        count_of(found, registry), nat_from_host(relations, reloaded_registry),
        reloaded_registry,
    )() is M.truth_value:
        print("PASS reloaded_derived=%s" % count_text(found, reloaded_registry))
    else:
        failures += 1
        print("FAIL reloaded_derived expected %d" % relations)

    print(
        "boot=%.2fs build=%.2fs rewrite=%.2fs save=%.2fs load=%.2fs bytes=%d failures=%d"
        % (
            booted - started, built - booted, rewritten - built,
            saved - rewritten, finished - saved,
            os.path.getsize(derived_snapshot), failures,
        ),
        flush=True,
    )
    return failures


if __name__ == "__main__":
    sys.exit(main())
