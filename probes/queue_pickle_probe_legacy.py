import traceback
from multiprocessing import reduction

from hyge.runtime import boot_from_packs
from hyge.main import PACK_PATHS, _runtime_namespace
from hyge import machine as M
from hyge import labels as Lmod
from hyge import proof as Pmod
from hyge import search as Smod

runtime, packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
registry = M.FromContextGetConstructors(runtime.graph)()
runtime.graph._search_disable_console = M.truth_value

triangle = Lmod.TaoProblem11TriangleLabel
facts = M.Pair(
    M.Pair(
        Lmod.GivenLabel,
        M.Pair(
            M.Pair(Lmod.TriangleLabel, M.Pair(triangle, M.EmptyList)),
            M.EmptyList,
        ),
    ),
    M.Pair(
        M.Pair(
            Lmod.NeedLabel,
            M.Pair(
                M.Pair(Lmod.SideLengthsLabel, M.Pair(triangle, M.EmptyList)),
                M.EmptyList,
            ),
        ),
        M.Pair(
            M.Pair(
                Lmod.NeedLabel,
                M.Pair(
                    M.Pair(Lmod.AnglesLabel, M.Pair(triangle, M.EmptyList)),
                    M.EmptyList,
                ),
            ),
            M.Pair(
                M.Pair(
                    Lmod.GivenLabel,
                    M.Pair(
                        M.Pair(
                            Lmod.ArithmeticProgressionLabel,
                            M.Pair(
                                M.Pair(Lmod.SideLengthsLabel, M.Pair(triangle, M.EmptyList)),
                                M.EmptyList,
                            ),
                        ),
                        M.EmptyList,
                    ),
                ),
                M.Pair(
                    M.Pair(
                        Lmod.GivenLabel,
                        M.Pair(
                            M.Pair(
                                Lmod.CommonDifferenceLabel,
                                M.Pair(
                                    M.Pair(Lmod.SideLengthsLabel, M.Pair(triangle, M.EmptyList)),
                                    M.EmptyList,
                                ),
                            ),
                            M.EmptyList,
                        ),
                    ),
                    M.Pair(
                        M.Pair(
                            Lmod.GivenLabel,
                            M.Pair(
                                M.Pair(Lmod.AreaLabel, M.Pair(triangle, M.EmptyList)),
                                M.EmptyList,
                            ),
                        ),
                        M.EmptyList,
                    ),
                ),
            ),
        ),
    ),
)
start = M.Knowledge(facts)()
goal = M.Pair(
    Lmod.SolvedLabel,
    M.Pair(
        M.Pair(Lmod.TriangleLabel, M.Pair(triangle, M.EmptyList)),
        M.EmptyList,
    ),
)

left = M.EmptyList
right = M.EmptyList
for _ in range(220):
    left = M.Pair(M.one, left)
    right = M.Pair(M.one, right)

deep_state = M.SearchState(left, M.EmptyList, M.EmptyList, M.one)()
deep_packet = Smod.SearchFrontierStatePacket(deep_state)()
deep_frontier = M.Pair(deep_state, M.Pair(deep_state, M.EmptyList))
deep_job = M.SearchJob(
    left,
    right,
    M.EmptyList,
    runtime.theorem_heuristic,
    M.SearchRunningLabel,
    deep_frontier,
    M.one,
    M.one,
    M.two,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.two,
)()
deep_result = Smod.SearchWorkerResult(
    M.DFSLabel,
    M.SearchRunningLabel,
    M.Zero,
    M.Zero,
    M.Zero,
    M.one,
    M.one,
    M.two,
    M.Zero,
    deep_job,
    M.EmptyList,
    M.Pair(deep_packet, M.EmptyList),
    M.one,
    M.EmptyList,
    M.one,
)()

tao_state = M.SearchState(start, M.EmptyList, M.EmptyList, M.one)()
tao_packet = Smod.SearchFrontierStatePacket(tao_state)()
tao_frontier = M.Pair(tao_state, M.Pair(tao_state, M.EmptyList))
tao_job = M.SearchJob(
    start,
    goal,
    runtime.ordered_rules(),
    runtime.theorem_heuristic,
    M.SearchRunningLabel,
    tao_frontier,
    M.one,
    M.one,
    M.two,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.EmptyList,
    M.two,
)()
tao_result = Smod.SearchWorkerResult(
    M.DFSLabel,
    M.SearchRunningLabel,
    M.Zero,
    M.Zero,
    M.Zero,
    M.one,
    M.one,
    M.two,
    M.Zero,
    tao_job,
    M.EmptyList,
    M.Pair(tao_packet, M.EmptyList),
    M.one,
    M.EmptyList,
    M.one,
)()

action_rule = M.Rule(start, goal)
action = Pmod.TheoremAction(action_rule)()

trace_path = "/home/user/queue_pickle_probe_traceback.txt"
trace_file = open(trace_path, "w", encoding="utf-8")
trace_file.write("queue pickle probe\n")

try:
    reduction.ForkingPickler.dumps(deep_state)
    print("deep-state: PASS")
    trace_file.write("deep-state: PASS\n")
except Exception:
    print("deep-state: FAIL")
    trace_file.write("deep-state: FAIL\n")
    trace_file.write(traceback.format_exc())

try:
    reduction.ForkingPickler.dumps(deep_packet)
    print("deep-packet: PASS")
    trace_file.write("deep-packet: PASS\n")
except Exception:
    print("deep-packet: FAIL")
    trace_file.write("deep-packet: FAIL\n")
    trace_file.write(traceback.format_exc())

try:
    reduction.ForkingPickler.dumps(deep_job)
    print("deep-job: PASS")
    trace_file.write("deep-job: PASS\n")
except Exception:
    print("deep-job: FAIL")
    trace_file.write("deep-job: FAIL\n")
    trace_file.write(traceback.format_exc())

try:
    reduction.ForkingPickler.dumps(deep_result)
    print("deep-result: PASS")
    trace_file.write("deep-result: PASS\n")
except Exception:
    print("deep-result: FAIL")
    trace_file.write("deep-result: FAIL\n")
    trace_file.write(traceback.format_exc())

try:
    reduction.ForkingPickler.dumps(tao_state)
    print("tao-state: PASS")
    trace_file.write("tao-state: PASS\n")
except Exception:
    print("tao-state: FAIL")
    trace_file.write("tao-state: FAIL\n")
    trace_file.write(traceback.format_exc())

try:
    reduction.ForkingPickler.dumps(tao_packet)
    print("tao-packet: PASS")
    trace_file.write("tao-packet: PASS\n")
except Exception:
    print("tao-packet: FAIL")
    trace_file.write("tao-packet: FAIL\n")
    trace_file.write(traceback.format_exc())

try:
    reduction.ForkingPickler.dumps(tao_job)
    print("tao-job: PASS")
    trace_file.write("tao-job: PASS\n")
except Exception:
    print("tao-job: FAIL")
    trace_file.write("tao-job: FAIL\n")
    trace_file.write(traceback.format_exc())

try:
    reduction.ForkingPickler.dumps(tao_result)
    print("tao-result: PASS")
    trace_file.write("tao-result: PASS\n")
except Exception:
    print("tao-result: FAIL")
    trace_file.write("tao-result: FAIL\n")
    trace_file.write(traceback.format_exc())

for depth in (1, 5, 10, 20, 40, 80, 160, 320, 640, 960):
    plan = M.EmptyList
    seen = M.EmptyList
    for _ in range(depth):
        plan = M.Pair(action, plan)
        seen = M.Pair(start, seen)
    frontier_state = M.SearchState(start, plan, seen, M.one)()
    frontier = M.Pair(frontier_state, M.Pair(frontier_state, M.EmptyList))
    result_job = M.SearchJob(
        start,
        goal,
        runtime.ordered_rules(),
        runtime.theorem_heuristic,
        M.SearchRunningLabel,
        frontier,
        M.one,
        M.one,
        M.two,
        M.EmptyList,
        M.EmptyList,
        M.EmptyList,
        M.EmptyList,
        M.two,
    )()
    result_packet = Smod.SearchFrontierStatePacket(frontier_state)()
    result_value = Smod.SearchWorkerResult(
        M.DFSLabel,
        M.SearchRunningLabel,
        M.Zero,
        M.Zero,
        M.Zero,
        M.one,
        M.one,
        M.two,
        M.Zero,
        result_job,
        M.EmptyList,
        M.Pair(result_packet, M.EmptyList),
        M.one,
        M.EmptyList,
        M.one,
    )()
    try:
        reduction.ForkingPickler.dumps(result_value)
        print("plan-seen-depth", depth, ": PASS")
        trace_file.write("plan-seen-depth ")
        trace_file.write(str(depth))
        trace_file.write(": PASS\n")
    except Exception:
        print("plan-seen-depth", depth, ": FAIL")
        trace_file.write("plan-seen-depth ")
        trace_file.write(str(depth))
        trace_file.write(": FAIL\n")
        trace_file.write(traceback.format_exc())
        break

trace_file.close()
print("traceback-saved:", trace_path)
