import sys
import time

sys.path.insert(0, "/home/user")

from hyge.runtime import boot_from_packs
from hyge.main import PACK_PATHS, _runtime_namespace
from hyge.testsuite import install_default_tests
from hyge import machine as M
from hyge import graph as G


def run_one_shard(shard_index):
    runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
    runtime.graph._search_disable_console = M.truth_value
    G.TestShardConfigure(runtime.graph, shard_index, M.two)()
    install_default_tests(runtime.graph)
    started = time.time()
    report = runtime.run_tests_report()
    elapsed = time.time() - started
    return report, elapsed


def main():
    reports = []
    for index, nat in (("0", M.Zero), ("1", M.one)):
        print("SHARD", index, "START", flush=True)
        report, elapsed = run_one_shard(nat)
        print("SHARD", index, "ELAPSED", elapsed, flush=True)
        print("SHARD", index, "REPORT", report, flush=True)
        reports.append((index, elapsed, report))
    print("SUITE_DONE", flush=True)


if __name__ == "__main__":
    main()
