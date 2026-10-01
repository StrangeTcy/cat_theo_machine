"""Run one deterministic round-robin shard of the default test suite.

Usage: python3 tools/shard_suite.py <shard_index> <shard_count>
Run two shards concurrently (0 2 and 1 2) to halve suite wall time.
"""
import sys, time

def main():
    import cat_theo_machine.machine as M
    import cat_theo_machine.proof as P
    import cat_theo_machine.graph as Gmod
    from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
    from cat_theo_machine.runtime import boot_from_packs
    from cat_theo_machine.testsuite import install_default_tests

    shard_index = int(sys.argv[1])
    shard_count = int(sys.argv[2])
    P.SetDebugTrace(M.false_value)()
    runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    runtime.graph._search_disable_console = M.truth_value
    index_nat = M.Zero
    i = 0
    registry = M.FromContextGetConstructors(runtime.graph)()
    while i < shard_index:
        pair = M.Succ(index_nat, registry)()
        index_nat = M.Head(pair)()
        registry = M.Head(M.Tail(pair)())()
        i += 1
    count_nat = M.Zero
    i = 0
    while i < shard_count:
        pair = M.Succ(count_nat, registry)()
        count_nat = M.Head(pair)()
        registry = M.Head(M.Tail(pair)())()
        i += 1
    runtime.graph._replace_context(constructors=registry)
    Gmod.TestShardConfigure(runtime.graph, index_nat, count_nat)()
    start = time.time()
    install_default_tests(runtime.graph)
    report = runtime.run_tests_report()
    print("SHARD", shard_index, "elapsed", time.time() - start)
    print(report)

if __name__ == "__main__":
    main()
