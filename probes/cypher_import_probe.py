"""Regression probe: cypher-export import, checked by content and not by count.

The CSV round-trip probe asserts counts. Counts passed on the first cypher run
while the graph was silently disconnected -- apoc's own `id: 42` property was
overwriting the node reference, so every node symbol became a bare number while
relationship endpoints kept naming `p0` and `h3`, and no edge resolved to any
node. Nothing counted wrong. This probe therefore asserts three things a count
cannot fake:

  * a property VALUE survives, checked with Compare against the expected Char;
  * a node introduced only as a relationship endpoint is present in the nodes
    chain, so edges are not dangling;
  * the counts, with NatEq against machine nats as elsewhere.

Usage:
    python probes/cypher_import_probe.py [RELATIONS]
"""

import os
import subprocess
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ROOT))

from cat_theo_machine import machine as M
from cat_theo_machine import main as _Main
from cat_theo_machine import runtime as _Runtime

IMPORTER = os.path.join(_ROOT, "importers", "cypher_to_hypergraph.py")
PERSONS = 200
HOUSES = 50


def count_of(chain, registry):
    return M.Head(M.NatFromRep(M.CountRep(chain)(), registry)())()


def text_of(nat, registry):
    return M.GMPRepText(M.NatRepOf(nat, registry)())()


def nat_from_host(value, registry):
    return M.Head(M.NatFromRep(M.GMPRep(value), registry)())()


def write_script(path, relations):
    handle = open(path, "w", encoding="utf-8")
    try:
        index = 0
        while index < PERSONS:
            handle.write(
                "CREATE (p%d:Person:Author {id: %d, name: 'person-%d', note: 'note text %d'});\n"
                % (index, index, index, index)
            )
            index += 1
        index = 0
        while index < relations:
            house = (index * 7) % HOUSES
            handle.write(
                "MATCH (p%d:Person {id: %d}), (h%d:House {id: %d}) "
                "CREATE (p%d)-[:LIVES_IN {since: 1843}]->(h%d);\n"
                % (index % PERSONS, index % PERSONS, house, house,
                   index % PERSONS, house)
            )
            index += 1
    finally:
        handle.close()


def main():
    argv = sys.argv
    relations = 2000
    if len(argv) > 1:
        relations = int(argv[1])
    failures = 0

    work = tempfile.mkdtemp(prefix="cypher-probe-")
    script = os.path.join(work, "export.cypher")
    snapshot = os.path.join(work, "from_cypher.json")
    write_script(script, relations)

    started = time.monotonic()
    proc = subprocess.run(
        [sys.executable, IMPORTER, script, snapshot],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.returncode != 0:
        print("IMPORT FAILED rc=%d" % proc.returncode)
        print(proc.stdout)
        return 1
    imported = time.monotonic()

    runtime = _Runtime.boot_from_snapshot(snapshot, _Main._runtime_namespace())
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    loaded = time.monotonic()

    name_symbol = M.Char("name")
    person_zero = M.Char("p0")
    house_three = M.Char("h3")
    expected_value = M.Char("person-0")
    name_edges = M.EmptyList
    value_intact = M.false_value
    cursor = graph.edges
    while (
        M.IdentityCompare(cursor, M.EmptyList)() is M.false_value
        and M.IsPair(cursor)() is M.truth_value
    ):
        candidate = M.Head(cursor)()
        if M.Compare(M.Head(candidate)(), name_symbol)() is M.truth_value:
            name_edges = M.Pair(candidate, name_edges)
            subject = M.Head(M.Tail(candidate)())()
            if M.Compare(subject, person_zero)() is M.truth_value:
                value = M.Head(M.Tail(M.Tail(candidate)())())()
                if M.Compare(value, expected_value)() is M.truth_value:
                    value_intact = M.truth_value
        cursor = M.Tail(cursor)()

    endpoint_person = M.false_value
    endpoint_house = M.false_value
    cursor = graph.nodes
    while (
        M.IdentityCompare(cursor, M.EmptyList)() is M.false_value
        and M.IsPair(cursor)() is M.truth_value
    ):
        candidate = M.Head(cursor)()
        if M.Compare(candidate, person_zero)() is M.truth_value:
            endpoint_person = M.truth_value
        if M.Compare(candidate, house_three)() is M.truth_value:
            endpoint_house = M.truth_value
        cursor = M.Tail(cursor)()

    expected_edges = relations + relations + PERSONS * 4 + HOUSES * 2
    checks = (
        ("nodes", count_of(graph.nodes, registry), PERSONS + HOUSES),
        ("edges", count_of(graph.edges, registry), expected_edges),
        ("name_edges", count_of(name_edges, registry), PERSONS),
    )
    for name, counted, expected in checks:
        rendered = text_of(counted, registry)
        if M.NatEq(counted, nat_from_host(expected, registry), registry)() is M.truth_value:
            print("PASS %s=%s" % (name, rendered))
        else:
            failures += 1
            print("FAIL %s expected %d got %s" % (name, expected, rendered))

    for name, flag in (
        ("value_intact", value_intact),
        ("endpoint_declared", endpoint_person),
        ("endpoint_implicit", endpoint_house),
    ):
        if flag is M.truth_value:
            print("PASS %s" % name)
        else:
            failures += 1
            print("FAIL %s" % name)

    print(
        "import %.2fs load %.2fs bytes=%d failures=%d"
        % (imported - started, loaded - imported, os.path.getsize(snapshot), failures),
        flush=True,
    )
    return failures


if __name__ == "__main__":
    sys.exit(main())
