"""Run named tests from the default suite, by exact name.

    python3 tools/run_named_tests.py <name> [<name> ...]   only these
    python3 tools/run_named_tests.py --all                 no filter
    python3 tools/run_named_tests.py --fresh <name> ...    skip the packs

The suite's tests do their work in their constructors, so installing the
default tests builds all 305 of them even when one is wanted: a targeted
run used to cost the whole install. The name filter is applied at
registration, so an unselected test is never constructed, and a run of one
test costs one test.

Two things this tool is not:

- It is not a baseline. A filtered run says nothing about shards and is
  never evidence for a freeze; `tools/shard_suite.py` is the only thing
  that produces one.
- It does not move the shard cursor. Every guard still ticks, so the
  cursor pin means the same thing with and without a filter, and
  `test_shard_cursor_pin_test` passes in both modes.

`--fresh` boots a bare runtime instead of the packs. It is much faster and
is for tests that build their own state; a test that needs packs-loaded
state has to be run without it.
"""
import sys
import time

sys.path.insert(0, "/home/user")


def _m_list(names):
    import cat_theo_machine.machine as M

    chain = M.EmptyList
    for name in reversed(names):
        chain = M.Pair(M.Char(name), chain)
    return chain


def main():
    import cat_theo_machine.machine as M
    import cat_theo_machine.proof as P
    import cat_theo_machine.graph as Gmod
    from cat_theo_machine.testsuite import install_default_tests

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    fresh = "--fresh" in sys.argv[1:]
    use_all = "--all" in sys.argv[1:]

    if not args and not use_all:
        print(__doc__)
        return 2

    P.SetDebugTrace(M.false_value)()
    start = time.time()
    if fresh:
        from cat_theo_machine.runtime import make_fresh_runtime

        graph = make_fresh_runtime().graph
    else:
        from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
        from cat_theo_machine.runtime import boot_from_packs

        runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        graph = runtime.graph
    graph._search_disable_console = M.truth_value
    booted = time.time() - start

    if not use_all:
        Gmod.TestNameFilter(graph, _m_list(args))()

    install_start = time.time()
    install_default_tests(graph)
    installed = time.time() - install_start

    registered = 0
    walker = M.FromContextGetTests(graph)()
    while M.Compare(walker, M.EmptyList)() is M.false_value:
        registered += 1
        walker = M.Tail(walker)()

    run_start = time.time()
    Gmod.RunTests(graph)()
    ran = time.time() - run_start

    print(
        "boot %.1fs   install %.1fs   run %.1fs   total %.1fs"
        % (booted, installed, ran, time.time() - start)
    )
    print("registered %d tests" % registered)
    if not use_all and registered != len(args):
        print(
            "  WARNING: %d names were asked for and %d registered"
            % (len(args), registered)
        )
    print(Gmod.TestResultsSummary(graph)())
    print(Gmod.TestResultsReport(graph)())


if __name__ == "__main__":
    sys.exit(main())
