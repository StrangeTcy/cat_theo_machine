from __future__ import annotations

import copyreg
import multiprocessing
import queue
import threading
import time

from .. import machine as M
from .. import heuristics as Hmod
from .. import labels as Lmod
from .. import proof as Pmod
from .. import context as Ctxmod
from .. import schemata as Smod
from .. import gmprep as Gmpmod
from .. import trees as Tmod
from .. import logic as Logicmod
from ..heuristics import *
from ..labels import *
from ..proof import *
from ..proof import _debug, _debug_term
from .chain_utils import *


class SearchRootRulePacket(M.Edge):
    def __init__(self, rule):
        self.result = M.Pair(SearchRootRulePacketLabel, M.Pair(rule, M.EmptyList))
        super().__init__(inputs=M.Pair(rule, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootRulePacketRule(M.Edge):
    def __init__(self, packet):
        self.result = SearchArgAt(packet, M.Zero)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchFrontierStatePacket(M.Edge):
    def __init__(self, state):
        self.result = M.Pair(SearchFrontierStatePacketLabel, M.Pair(state, M.EmptyList))
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchFrontierStatePacketState(M.Edge):
    def __init__(self, packet):
        self.result = SearchArgAt(packet, M.Zero)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerBaseline(M.Edge):
    def __init__(self, constructors, start, goal, rules, heuristic, rewrite_rules, generation):
        problem = SearchWorkerBaselineProblem(start, goal, rules, heuristic, rewrite_rules)()
        self.result = M.Pair(
            SearchWorkerBaselineLabel,
            M.Pair(
                constructors,
                M.Pair(problem, M.Pair(generation, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                constructors,
                M.Pair(
                    start,
                    M.Pair(
                        goal,
                        M.Pair(
                            rules,
                            M.Pair(
                                heuristic,
                                M.Pair(rewrite_rules, M.Pair(generation, M.EmptyList)),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerBaselineProblem(M.Edge):
    def __init__(self, start, goal, rules, heuristic, rewrite_rules):
        self.result = M.Pair(
            SearchWorkerBaselineProblemLabel,
            M.Pair(
                start,
                M.Pair(
                    goal,
                    M.Pair(
                        rules,
                        M.Pair(heuristic, M.Pair(rewrite_rules, M.EmptyList)),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                start,
                M.Pair(
                    goal,
                    M.Pair(
                        rules,
                        M.Pair(heuristic, M.Pair(rewrite_rules, M.EmptyList)),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerBaselineProblemBlock(M.Edge):
    def __init__(self, baseline):
        problem = SearchArgAt(baseline, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchWorkerBaselineProblemLabel)() is M.truth_value:
                self.result = problem
            else:
                self.result = SearchWorkerBaselineProblem(
                    problem,
                    SearchArgAt(baseline, M.two)(),
                    SearchArgAt(baseline, M.three)(),
                    SearchArgAt(baseline, M.four)(),
                    SearchArgAt(baseline, M.five)(),
                )()
        else:
            self.result = SearchWorkerBaselineProblem(
                problem,
                SearchArgAt(baseline, M.two)(),
                SearchArgAt(baseline, M.three)(),
                SearchArgAt(baseline, M.four)(),
                SearchArgAt(baseline, M.five)(),
            )()
        super().__init__(inputs=M.Pair(baseline, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerBaselineConstructors(M.Edge):
    def __init__(self, baseline):
        self.result = SearchArgAt(baseline, M.Zero)()
        super().__init__(inputs=M.Pair(baseline, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerBaselineStart(M.Edge):
    def __init__(self, baseline):
        problem = SearchArgAt(baseline, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchWorkerBaselineProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(problem, M.Zero)()
            else:
                self.result = problem
        else:
            self.result = problem
        super().__init__(inputs=M.Pair(baseline, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerBaselineGoal(M.Edge):
    def __init__(self, baseline):
        problem = SearchArgAt(baseline, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchWorkerBaselineProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(problem, M.one)()
            else:
                self.result = SearchArgAt(baseline, M.two)()
        else:
            self.result = SearchArgAt(baseline, M.two)()
        super().__init__(inputs=M.Pair(baseline, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerBaselineRules(M.Edge):
    def __init__(self, baseline):
        problem = SearchArgAt(baseline, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchWorkerBaselineProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(problem, M.two)()
            else:
                self.result = SearchArgAt(baseline, M.three)()
        else:
            self.result = SearchArgAt(baseline, M.three)()
        super().__init__(inputs=M.Pair(baseline, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerBaselineHeuristic(M.Edge):
    def __init__(self, baseline):
        problem = SearchArgAt(baseline, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchWorkerBaselineProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(problem, M.three)()
            else:
                self.result = SearchArgAt(baseline, M.four)()
        else:
            self.result = SearchArgAt(baseline, M.four)()
        super().__init__(inputs=M.Pair(baseline, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerBaselineRewriteRules(M.Edge):
    def __init__(self, baseline):
        problem = SearchArgAt(baseline, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchWorkerBaselineProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(problem, M.four)()
            else:
                self.result = SearchArgAt(baseline, M.five)()
        else:
            self.result = SearchArgAt(baseline, M.five)()
        super().__init__(inputs=M.Pair(baseline, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerBaselineGeneration(M.Edge):
    def __init__(self, baseline):
        problem = SearchArgAt(baseline, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchWorkerBaselineProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(baseline, M.two)()
            else:
                self.result = SearchArgAt(baseline, M.six)()
        else:
            self.result = SearchArgAt(baseline, M.six)()
        super().__init__(inputs=M.Pair(baseline, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerSetup(M.Edge):
    def __init__(self, mode, baseline):
        self.result = M.Pair(SearchWorkerSetupLabel, M.Pair(mode, M.Pair(baseline, M.EmptyList)))
        super().__init__(inputs=M.Pair(mode, M.Pair(baseline, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerSetupMode(M.Edge):
    def __init__(self, setup):
        self.result = SearchArgAt(setup, M.Zero)()
        super().__init__(inputs=M.Pair(setup, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerSetupBaseline(M.Edge):
    def __init__(self, setup):
        self.result = SearchArgAt(setup, M.one)()
        super().__init__(inputs=M.Pair(setup, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacket(M.Edge):
    def __init__(
        self,
        packet_descriptor,
        search_memo,
        visited,
        theorem_rule_cache,
        rewrite_rules,
        step_budget,
        debug_trace,
        ignore_root_fast_paths,
        discovery_mode,
        packet_token,
        generation,
    ):
        stores = SearchWorkerPacketStores(search_memo, visited, theorem_rule_cache, rewrite_rules)()
        controls = SearchWorkerPacketControls(
            step_budget,
            debug_trace,
            ignore_root_fast_paths,
            discovery_mode,
            packet_token,
            generation,
        )()
        self.result = M.Pair(
            SearchWorkerPacketLabel,
            M.Pair(
                packet_descriptor,
                M.Pair(stores, M.Pair(controls, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                packet_descriptor,
                M.Pair(
                    search_memo,
                    M.Pair(
                        visited,
                        M.Pair(
                            theorem_rule_cache,
                            M.Pair(
                                rewrite_rules,
                                M.Pair(
                                    step_budget,
                                    M.Pair(
                                        debug_trace,
                                        M.Pair(
                                            ignore_root_fast_paths,
                                            M.Pair(discovery_mode, M.Pair(packet_token, M.Pair(generation, M.EmptyList))),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerPacketStores(M.Edge):
    def __init__(self, search_memo, visited, theorem_rule_cache, rewrite_rules):
        self.result = M.Pair(
            SearchWorkerPacketStoresLabel,
            M.Pair(
                search_memo,
                M.Pair(
                    visited,
                    M.Pair(theorem_rule_cache, M.Pair(rewrite_rules, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                search_memo,
                M.Pair(
                    visited,
                    M.Pair(theorem_rule_cache, M.Pair(rewrite_rules, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerPacketStoresBlock(M.Edge):
    def __init__(self, packet):
        stores = SearchArgAt(packet, M.one)()
        if M.IsPair(stores)() is M.truth_value:
            if M.IdentityCompare(M.Head(stores)(), SearchWorkerPacketStoresLabel)() is M.truth_value:
                self.result = stores
            else:
                self.result = SearchWorkerPacketStores(
                    stores,
                    SearchArgAt(packet, M.two)(),
                    SearchArgAt(packet, M.three)(),
                    SearchArgAt(packet, M.four)(),
                )()
        else:
            self.result = SearchWorkerPacketStores(
                stores,
                SearchArgAt(packet, M.two)(),
                SearchArgAt(packet, M.three)(),
                SearchArgAt(packet, M.four)(),
            )()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketControls(M.Edge):
    def __init__(self, step_budget, debug_trace, ignore_root_fast_paths, discovery_mode, packet_token, generation):
        self.result = M.Pair(
            SearchWorkerPacketControlsLabel,
            M.Pair(
                step_budget,
                M.Pair(
                    debug_trace,
                    M.Pair(
                        ignore_root_fast_paths,
                        M.Pair(
                            discovery_mode,
                            M.Pair(packet_token, M.Pair(generation, M.EmptyList)),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                step_budget,
                M.Pair(
                    debug_trace,
                    M.Pair(
                        ignore_root_fast_paths,
                        M.Pair(
                            discovery_mode,
                            M.Pair(packet_token, M.Pair(generation, M.EmptyList)),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerPacketControlsBlock(M.Edge):
    def __init__(self, packet):
        controls = SearchArgAt(packet, M.two)()
        if M.IsPair(controls)() is M.truth_value:
            if M.IdentityCompare(M.Head(controls)(), SearchWorkerPacketControlsLabel)() is M.truth_value:
                self.result = controls
            else:
                self.result = SearchWorkerPacketControls(
                    SearchArgAt(packet, M.five)(),
                    SearchArgAt(packet, M.six)(),
                    SearchArgAt(packet, M.seven)(),
                    SearchArgAt(packet, M.eight)(),
                    SearchArgAt(packet, M.nine)(),
                    SearchChainAt(SearchArgsFrom(packet, M.nine)(), M.one)(),
                )()
        else:
            self.result = SearchWorkerPacketControls(
                SearchArgAt(packet, M.five)(),
                SearchArgAt(packet, M.six)(),
                SearchArgAt(packet, M.seven)(),
                SearchArgAt(packet, M.eight)(),
                SearchArgAt(packet, M.nine)(),
                SearchChainAt(SearchArgsFrom(packet, M.nine)(), M.one)(),
            )()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardPacket(M.Edge):
    def __init__(self, constructors, rules, current, debug_trace):
        self.result = M.Pair(
            constructors,
            M.Pair(
                rules,
                M.Pair(
                    current,
                    M.Pair(debug_trace, M.EmptyList),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                constructors,
                M.Pair(
                    rules,
                    M.Pair(
                        current,
                        M.Pair(debug_trace, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchRootWaveShardLaunch(M.Edge):
    def __init__(self, packet, slot):
        self.result = M.Pair(SearchRootWaveShardLaunchLabel, M.Pair(packet, M.Pair(slot, M.EmptyList)))
        super().__init__(inputs=M.Pair(packet, M.Pair(slot, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardLaunchPacket(M.Edge):
    def __init__(self, launch):
        self.result = SearchArgAt(launch, M.Zero)()
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardLaunchSlot(M.Edge):
    def __init__(self, launch):
        self.result = SearchArgAt(launch, M.one)()
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardPacketConstructors(M.Edge):
    def __init__(self, packet):
        self.result = SearchChainAt(packet, M.Zero)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardPacketRules(M.Edge):
    def __init__(self, packet):
        self.result = SearchChainAt(packet, M.one)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardPacketCurrent(M.Edge):
    def __init__(self, packet):
        self.result = SearchChainAt(packet, M.two)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardPacketDebugTrace(M.Edge):
    def __init__(self, packet):
        self.result = SearchChainAt(packet, M.three)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardResult(M.Edge):
    def __init__(self, immediate_rules, goal_rules, other_rules):
        self.result = M.Pair(immediate_rules, M.Pair(goal_rules, M.Pair(other_rules, M.EmptyList)))
        super().__init__(
            inputs=M.Pair(immediate_rules, M.Pair(goal_rules, M.Pair(other_rules, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchRootWaveShardResultImmediate(M.Edge):
    def __init__(self, result):
        self.result = SearchChainAt(result, M.Zero)()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardResultGoal(M.Edge):
    def __init__(self, result):
        self.result = SearchChainAt(result, M.one)()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRootWaveShardResultOther(M.Edge):
    def __init__(self, result):
        self.result = SearchChainAt(result, M.two)()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerLaunch(M.Edge):
    def __init__(self, mode, setup, payload, packet_state, launch_slot, launch_budget, branch_serial):
        dispatch = SearchWorkerLaunchDispatch(packet_state, launch_slot, launch_budget, branch_serial)()
        self.result = M.Pair(
            mode,
            M.Pair(
                setup,
                M.Pair(payload, M.Pair(dispatch, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                mode,
                M.Pair(
                    setup,
                    M.Pair(
                        payload,
                        M.Pair(
                            packet_state,
                            M.Pair(
                                launch_slot,
                                M.Pair(launch_budget, M.Pair(branch_serial, M.EmptyList)),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerLaunchDispatch(M.Edge):
    def __init__(self, packet_state, launch_slot, launch_budget, branch_serial):
        self.result = M.Pair(
            SearchWorkerLaunchDispatchLabel,
            M.Pair(
                packet_state,
                M.Pair(
                    launch_slot,
                    M.Pair(launch_budget, M.Pair(branch_serial, M.EmptyList)),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                packet_state,
                M.Pair(
                    launch_slot,
                    M.Pair(launch_budget, M.Pair(branch_serial, M.EmptyList)),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerLaunchDispatchBlock(M.Edge):
    def __init__(self, launch):
        dispatch = SearchChainAt(launch, M.three)()
        if M.IsPair(dispatch)() is M.truth_value:
            if M.IdentityCompare(M.Head(dispatch)(), SearchWorkerLaunchDispatchLabel)() is M.truth_value:
                self.result = dispatch
            else:
                self.result = SearchWorkerLaunchDispatch(
                    dispatch,
                    SearchChainAt(launch, M.four)(),
                    SearchChainAt(launch, M.five)(),
                    SearchChainAt(launch, M.six)(),
                )()
        else:
            self.result = SearchWorkerLaunchDispatch(
                dispatch,
                SearchChainAt(launch, M.four)(),
                SearchChainAt(launch, M.five)(),
                SearchChainAt(launch, M.six)(),
            )()
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketDescriptor(M.Edge):
    def __init__(self, packet):
        self.result = SearchArgAt(packet, M.Zero)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketSearchMemo(M.Edge):
    def __init__(self, packet):
        stores = SearchArgAt(packet, M.one)()
        if M.IsPair(stores)() is M.truth_value:
            if M.IdentityCompare(M.Head(stores)(), SearchWorkerPacketStoresLabel)() is M.truth_value:
                self.result = SearchArgAt(stores, M.Zero)()
            else:
                self.result = stores
        else:
            self.result = stores
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketVisited(M.Edge):
    def __init__(self, packet):
        stores = SearchArgAt(packet, M.one)()
        if M.IsPair(stores)() is M.truth_value:
            if M.IdentityCompare(M.Head(stores)(), SearchWorkerPacketStoresLabel)() is M.truth_value:
                self.result = SearchArgAt(stores, M.one)()
            else:
                self.result = SearchArgAt(packet, M.two)()
        else:
            self.result = SearchArgAt(packet, M.two)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketTheoremRuleCache(M.Edge):
    def __init__(self, packet):
        stores = SearchArgAt(packet, M.one)()
        if M.IsPair(stores)() is M.truth_value:
            if M.IdentityCompare(M.Head(stores)(), SearchWorkerPacketStoresLabel)() is M.truth_value:
                self.result = SearchArgAt(stores, M.two)()
            else:
                self.result = SearchArgAt(packet, M.three)()
        else:
            self.result = SearchArgAt(packet, M.three)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketRewriteRules(M.Edge):
    def __init__(self, packet):
        stores = SearchArgAt(packet, M.one)()
        if M.IsPair(stores)() is M.truth_value:
            if M.IdentityCompare(M.Head(stores)(), SearchWorkerPacketStoresLabel)() is M.truth_value:
                self.result = SearchArgAt(stores, M.three)()
            else:
                self.result = SearchArgAt(packet, M.four)()
        else:
            self.result = SearchArgAt(packet, M.four)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketStepBudget(M.Edge):
    def __init__(self, packet):
        controls = SearchArgAt(packet, M.two)()
        if M.IsPair(controls)() is M.truth_value:
            if M.IdentityCompare(M.Head(controls)(), SearchWorkerPacketControlsLabel)() is M.truth_value:
                self.result = SearchArgAt(controls, M.Zero)()
            else:
                self.result = SearchArgAt(packet, M.five)()
        else:
            self.result = SearchArgAt(packet, M.five)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketDebugTrace(M.Edge):
    def __init__(self, packet):
        controls = SearchArgAt(packet, M.two)()
        if M.IsPair(controls)() is M.truth_value:
            if M.IdentityCompare(M.Head(controls)(), SearchWorkerPacketControlsLabel)() is M.truth_value:
                self.result = SearchArgAt(controls, M.one)()
            else:
                self.result = SearchArgAt(packet, M.six)()
        else:
            self.result = SearchArgAt(packet, M.six)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketIgnoreRootFastPaths(M.Edge):
    def __init__(self, packet):
        controls = SearchArgAt(packet, M.two)()
        if M.IsPair(controls)() is M.truth_value:
            if M.IdentityCompare(M.Head(controls)(), SearchWorkerPacketControlsLabel)() is M.truth_value:
                self.result = SearchArgAt(controls, M.two)()
            else:
                self.result = SearchArgAt(packet, M.seven)()
        else:
            self.result = SearchArgAt(packet, M.seven)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketDiscoveryMode(M.Edge):
    def __init__(self, packet):
        controls = SearchArgAt(packet, M.two)()
        if M.IsPair(controls)() is M.truth_value:
            if M.IdentityCompare(M.Head(controls)(), SearchWorkerPacketControlsLabel)() is M.truth_value:
                self.result = SearchArgAt(controls, M.three)()
            else:
                self.result = SearchArgAt(packet, M.eight)()
        else:
            self.result = SearchArgAt(packet, M.eight)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketPacketToken(M.Edge):
    def __init__(self, packet):
        controls = SearchArgAt(packet, M.two)()
        if M.IsPair(controls)() is M.truth_value:
            if M.IdentityCompare(M.Head(controls)(), SearchWorkerPacketControlsLabel)() is M.truth_value:
                self.result = SearchArgAt(controls, M.four)()
            else:
                self.result = SearchArgAt(packet, M.nine)()
        else:
            self.result = SearchArgAt(packet, M.nine)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPacketGeneration(M.Edge):
    def __init__(self, packet):
        controls = SearchArgAt(packet, M.two)()
        if M.IsPair(controls)() is M.truth_value:
            if M.IdentityCompare(M.Head(controls)(), SearchWorkerPacketControlsLabel)() is M.truth_value:
                self.result = SearchArgAt(controls, M.five)()
            else:
                self.result = SearchChainAt(SearchArgsFrom(packet, M.nine)(), M.one)()
        else:
            self.result = SearchChainAt(SearchArgsFrom(packet, M.nine)(), M.one)()
        super().__init__(inputs=M.Pair(packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerStandalonePacket(M.Edge):
    def __init__(self, setup, packet):
        self.result = M.Pair(SearchWorkerStandalonePacketLabel, M.Pair(setup, M.Pair(packet, M.EmptyList)))
        super().__init__(inputs=M.Pair(setup, M.Pair(packet, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerStandalonePacketSetup(M.Edge):
    def __init__(self, standalone_packet):
        self.result = SearchArgAt(standalone_packet, M.Zero)()
        super().__init__(inputs=M.Pair(standalone_packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerStandalonePacketPayload(M.Edge):
    def __init__(self, standalone_packet):
        self.result = SearchArgAt(standalone_packet, M.one)()
        super().__init__(inputs=M.Pair(standalone_packet, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerLaunchMode(M.Edge):
    def __init__(self, launch):
        self.result = SearchChainAt(launch, M.Zero)()
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerLaunchPayload(M.Edge):
    def __init__(self, launch):
        self.result = SearchChainAt(launch, M.two)()
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerLaunchSetup(M.Edge):
    def __init__(self, launch):
        self.result = SearchChainAt(launch, M.one)()
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerLaunchPacketState(M.Edge):
    def __init__(self, launch):
        dispatch = SearchChainAt(launch, M.three)()
        if M.IsPair(dispatch)() is M.truth_value:
            if M.IdentityCompare(M.Head(dispatch)(), SearchWorkerLaunchDispatchLabel)() is M.truth_value:
                self.result = SearchArgAt(dispatch, M.Zero)()
            else:
                self.result = dispatch
        else:
            self.result = dispatch
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerLaunchSlot(M.Edge):
    def __init__(self, launch):
        dispatch = SearchChainAt(launch, M.three)()
        if M.IsPair(dispatch)() is M.truth_value:
            if M.IdentityCompare(M.Head(dispatch)(), SearchWorkerLaunchDispatchLabel)() is M.truth_value:
                self.result = SearchArgAt(dispatch, M.one)()
            else:
                self.result = SearchChainAt(launch, M.four)()
        else:
            self.result = SearchChainAt(launch, M.four)()
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerLaunchBudget(M.Edge):
    def __init__(self, launch):
        dispatch = SearchChainAt(launch, M.three)()
        if M.IsPair(dispatch)() is M.truth_value:
            if M.IdentityCompare(M.Head(dispatch)(), SearchWorkerLaunchDispatchLabel)() is M.truth_value:
                self.result = SearchArgAt(dispatch, M.two)()
            else:
                self.result = SearchChainAt(launch, M.five)()
        else:
            self.result = SearchChainAt(launch, M.five)()
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerLaunchBranchSerial(M.Edge):
    def __init__(self, launch):
        dispatch = SearchChainAt(launch, M.three)()
        if M.IsPair(dispatch)() is M.truth_value:
            if M.IdentityCompare(M.Head(dispatch)(), SearchWorkerLaunchDispatchLabel)() is M.truth_value:
                self.result = SearchArgAt(dispatch, M.three)()
            else:
                self.result = SearchChainAt(launch, M.six)()
        else:
            self.result = SearchChainAt(launch, M.six)()
        super().__init__(inputs=M.Pair(launch, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerMetrics(M.Edge):
    def __init__(self, total_value, proof_value, search_value, expanded, generated, frontier_peak, found_depth):
        self.result = M.Pair(
            SearchWorkerMetricsLabel,
            M.Pair(
                total_value,
                M.Pair(
                    proof_value,
                    M.Pair(
                        search_value,
                        M.Pair(
                            expanded,
                            M.Pair(generated, M.Pair(frontier_peak, M.Pair(found_depth, M.EmptyList))),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                total_value,
                M.Pair(
                    proof_value,
                    M.Pair(
                        search_value,
                        M.Pair(
                            expanded,
                            M.Pair(generated, M.Pair(frontier_peak, M.Pair(found_depth, M.EmptyList))),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerMetricsTotalValue(M.Edge):
    def __init__(self, metrics):
        self.result = SearchArgAt(metrics, M.Zero)()
        super().__init__(inputs=M.Pair(metrics, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerMetricsProofValue(M.Edge):
    def __init__(self, metrics):
        self.result = SearchArgAt(metrics, M.one)()
        super().__init__(inputs=M.Pair(metrics, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerMetricsSearchValue(M.Edge):
    def __init__(self, metrics):
        self.result = SearchArgAt(metrics, M.two)()
        super().__init__(inputs=M.Pair(metrics, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerMetricsExpanded(M.Edge):
    def __init__(self, metrics):
        self.result = SearchArgAt(metrics, M.three)()
        super().__init__(inputs=M.Pair(metrics, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerMetricsGenerated(M.Edge):
    def __init__(self, metrics):
        self.result = SearchArgAt(metrics, M.four)()
        super().__init__(inputs=M.Pair(metrics, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerMetricsFrontierPeak(M.Edge):
    def __init__(self, metrics):
        self.result = SearchArgAt(metrics, M.five)()
        super().__init__(inputs=M.Pair(metrics, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerMetricsFoundDepth(M.Edge):
    def __init__(self, metrics):
        self.result = SearchArgAt(metrics, M.six)()
        super().__init__(inputs=M.Pair(metrics, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPayload(M.Edge):
    def __init__(self, job, search_memo, ready_packets, ready_packet_count, registry, packet_token):
        self.result = M.Pair(
            SearchWorkerPayloadLabel,
            M.Pair(
                job,
                M.Pair(
                    search_memo,
                    M.Pair(
                        ready_packets,
                        M.Pair(ready_packet_count, M.Pair(registry, M.Pair(packet_token, M.EmptyList))),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                job,
                M.Pair(
                    search_memo,
                    M.Pair(
                        ready_packets,
                        M.Pair(ready_packet_count, M.Pair(registry, M.Pair(packet_token, M.EmptyList))),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerPayloadJob(M.Edge):
    def __init__(self, payload):
        self.result = SearchArgAt(payload, M.Zero)()
        super().__init__(inputs=M.Pair(payload, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPayloadSearchMemo(M.Edge):
    def __init__(self, payload):
        self.result = SearchArgAt(payload, M.one)()
        super().__init__(inputs=M.Pair(payload, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPayloadReadyPackets(M.Edge):
    def __init__(self, payload):
        self.result = SearchArgAt(payload, M.two)()
        super().__init__(inputs=M.Pair(payload, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPayloadReadyPacketCount(M.Edge):
    def __init__(self, payload):
        self.result = SearchArgAt(payload, M.three)()
        super().__init__(inputs=M.Pair(payload, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPayloadRegistry(M.Edge):
    def __init__(self, payload):
        self.result = SearchArgAt(payload, M.four)()
        super().__init__(inputs=M.Pair(payload, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerPayloadPacketToken(M.Edge):
    def __init__(self, payload):
        self.result = SearchArgAt(payload, M.five)()
        super().__init__(inputs=M.Pair(payload, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResult(M.Edge):
    def __init__(
        self,
        mode,
        status,
        total_value,
        proof_value,
        search_value,
        expanded,
        generated,
        frontier_peak,
        found_depth,
        job,
        search_memo,
        ready_packets,
        ready_packet_count,
        registry,
        packet_token,
    ):
        metrics = SearchWorkerMetrics(
            total_value,
            proof_value,
            search_value,
            expanded,
            generated,
            frontier_peak,
            found_depth,
        )()
        payload = SearchWorkerPayload(
            job,
            search_memo,
            ready_packets,
            ready_packet_count,
            registry,
            packet_token,
        )()
        self.result = M.Pair(
            mode,
            M.Pair(
                status,
                M.Pair(metrics, M.Pair(payload, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                mode,
                M.Pair(
                    status,
                    M.Pair(
                        total_value,
                        M.Pair(
                            proof_value,
                            M.Pair(
                                search_value,
                                M.Pair(
                                    expanded,
                                    M.Pair(
                                        generated,
                                        M.Pair(
                                            frontier_peak,
                                            M.Pair(
                                                found_depth,
                                                M.Pair(
                                                    job,
                                                    M.Pair(
                                                        search_memo,
                                                        M.Pair(
                                                            ready_packets,
                                                            M.Pair(ready_packet_count, M.Pair(registry, M.Pair(packet_token, M.EmptyList))),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchWorkerResultMetrics(M.Edge):
    def __init__(self, result):
        metrics = SearchChainAt(result, M.two)()
        if M.IsPair(metrics)() is M.truth_value:
            if M.IdentityCompare(M.Head(metrics)(), SearchWorkerMetricsLabel)() is M.truth_value:
                self.result = metrics
            else:
                self.result = SearchWorkerMetrics(
                    metrics,
                    SearchChainAt(result, M.three)(),
                    SearchChainAt(result, M.four)(),
                    SearchChainAt(result, M.five)(),
                    SearchChainAt(result, M.six)(),
                    SearchChainAt(result, M.seven)(),
                    SearchChainAt(result, M.eight)(),
                )()
        else:
            self.result = SearchWorkerMetrics(
                metrics,
                SearchChainAt(result, M.three)(),
                SearchChainAt(result, M.four)(),
                SearchChainAt(result, M.five)(),
                SearchChainAt(result, M.six)(),
                SearchChainAt(result, M.seven)(),
                SearchChainAt(result, M.eight)(),
            )()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultPayload(M.Edge):
    def __init__(self, result):
        payload = SearchChainAt(result, M.three)()
        if M.IsPair(payload)() is M.truth_value:
            if M.IdentityCompare(M.Head(payload)(), SearchWorkerPayloadLabel)() is M.truth_value:
                self.result = payload
            else:
                after_job = SearchChainDrop(SearchChainDrop(result, M.nine)(), M.one)()
                self.result = SearchWorkerPayload(
                    SearchChainAt(result, M.nine)(),
                    SearchChainAt(after_job, M.Zero)(),
                    SearchChainAt(after_job, M.one)(),
                    SearchChainAt(after_job, M.two)(),
                    SearchChainAt(after_job, M.three)(),
                    SearchChainAt(after_job, M.four)(),
                )()
        else:
            after_job = SearchChainDrop(SearchChainDrop(result, M.nine)(), M.one)()
            self.result = SearchWorkerPayload(
                SearchChainAt(result, M.nine)(),
                SearchChainAt(after_job, M.Zero)(),
                SearchChainAt(after_job, M.one)(),
                SearchChainAt(after_job, M.two)(),
                SearchChainAt(after_job, M.three)(),
                SearchChainAt(after_job, M.four)(),
            )()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultMode(M.Edge):
    def __init__(self, result):
        self.result = SearchChainAt(result, M.Zero)()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultStatus(M.Edge):
    def __init__(self, result):
        self.result = SearchChainAt(result, M.one)()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultTotalValue(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerMetricsTotalValue(SearchWorkerResultMetrics(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultProofValue(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerMetricsProofValue(SearchWorkerResultMetrics(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultSearchValue(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerMetricsSearchValue(SearchWorkerResultMetrics(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultExpanded(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerMetricsExpanded(SearchWorkerResultMetrics(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultGenerated(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerMetricsGenerated(SearchWorkerResultMetrics(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultFrontierPeak(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerMetricsFrontierPeak(SearchWorkerResultMetrics(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultFoundDepth(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerMetricsFoundDepth(SearchWorkerResultMetrics(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultJob(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerPayloadJob(SearchWorkerResultPayload(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultAfterJob(M.Edge):
    def __init__(self, result):
        self.result = SearchArgsFrom(SearchWorkerResultPayload(result)(), M.one)()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultSearchMemo(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerPayloadSearchMemo(SearchWorkerResultPayload(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultReadyPackets(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerPayloadReadyPackets(SearchWorkerResultPayload(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultReadyPacketCount(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerPayloadReadyPacketCount(SearchWorkerResultPayload(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultRegistry(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerPayloadRegistry(SearchWorkerResultPayload(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchWorkerResultPacketToken(M.Edge):
    def __init__(self, result):
        self.result = SearchWorkerPayloadPacketToken(SearchWorkerResultPayload(result)())()
        super().__init__(inputs=M.Pair(result, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobAfterGenerated(M.Edge):
    def __init__(self, job):
        self.result = M.Pair(
            SearchJobFrontierSize(job)(),
            M.Pair(
                SearchJobFrontierPeak(job)(),
                M.Pair(
                    SearchJobResultPlan(job)(),
                    M.Pair(
                        SearchJobVisited(job)(),
                        M.Pair(
                            SearchJobTheoremRuleCache(job)(),
                            M.Pair(SearchJobRewriteRules(job)(), M.EmptyList),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchCostValue(M.Edge):
    def __init__(self, cost):
        self.result = SearchArgAt(cost, M.Zero)()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchCostExpanded(M.Edge):
    def __init__(self, cost):
        self.result = SearchArgAt(cost, M.one)()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchCostGenerated(M.Edge):
    def __init__(self, cost):
        self.result = SearchArgAt(cost, M.two)()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchCostFrontierPeak(M.Edge):
    def __init__(self, cost):
        self.result = SearchArgAt(cost, M.three)()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchCostFoundDepth(M.Edge):
    def __init__(self, cost):
        self.result = SearchArgAt(cost, M.four)()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchCostOutcome(M.Edge):
    def __init__(self, cost):
        self.result = SearchArgAt(cost, M.five)()
        super().__init__(inputs=M.Pair(cost, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class BuildSearchCost(M.Edge):
    def __init__(self, plan, expanded, generated, frontier_peak, outcome, registry):
        sum_pair = M.Add(expanded, generated, registry)()
        first_sum = M.Head(sum_pair)()
        reg1 = M.Head(M.Tail(sum_pair)())()
        total_pair = M.Add(first_sum, frontier_peak, reg1)()
        total_value = M.Head(total_pair)()
        reg2 = M.Head(M.Tail(total_pair)())()
        depth_pair = M.Count(plan, reg2)()
        found_depth = M.Head(depth_pair)()
        reg3 = M.Head(M.Tail(depth_pair)())()
        self.result = M.Pair(
            SearchCost(total_value, expanded, generated, frontier_peak, found_depth, outcome)(),
            M.Pair(reg3, M.EmptyList),
        )
        super().__init__(
            inputs=M.Pair(
                plan,
                M.Pair(
                    expanded,
                    M.Pair(generated, M.Pair(frontier_peak, M.Pair(outcome, M.Pair(registry, M.EmptyList)))),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchJobProgress(M.Edge):
    def __init__(self, frontier, expanded, generated, frontier_size, frontier_peak, result_plan):
        self.result = M.Pair(
            SearchJobProgressLabel,
            M.Pair(
                frontier,
                M.Pair(
                    expanded,
                    M.Pair(
                        generated,
                        M.Pair(frontier_size, M.Pair(frontier_peak, M.Pair(result_plan, M.EmptyList))),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                frontier,
                M.Pair(
                    expanded,
                    M.Pair(
                        generated,
                        M.Pair(frontier_size, M.Pair(frontier_peak, M.Pair(result_plan, M.EmptyList))),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchJobProgressFrontier(M.Edge):
    def __init__(self, progress):
        self.result = SearchArgAt(progress, M.Zero)()
        super().__init__(inputs=M.Pair(progress, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobProgressExpanded(M.Edge):
    def __init__(self, progress):
        self.result = SearchArgAt(progress, M.one)()
        super().__init__(inputs=M.Pair(progress, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobProgressGenerated(M.Edge):
    def __init__(self, progress):
        self.result = SearchArgAt(progress, M.two)()
        super().__init__(inputs=M.Pair(progress, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobProgressFrontierSize(M.Edge):
    def __init__(self, progress):
        self.result = SearchArgAt(progress, M.three)()
        super().__init__(inputs=M.Pair(progress, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobProgressFrontierPeak(M.Edge):
    def __init__(self, progress):
        self.result = SearchArgAt(progress, M.four)()
        super().__init__(inputs=M.Pair(progress, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobProgressResultPlan(M.Edge):
    def __init__(self, progress):
        self.result = SearchArgAt(progress, M.five)()
        super().__init__(inputs=M.Pair(progress, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobStores(M.Edge):
    def __init__(self, visited, theorem_rule_cache, rewrite_rules):
        self.result = M.Pair(
            SearchJobStoresLabel,
            M.Pair(visited, M.Pair(theorem_rule_cache, M.Pair(rewrite_rules, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(visited, M.Pair(theorem_rule_cache, M.Pair(rewrite_rules, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchJobStoresVisited(M.Edge):
    def __init__(self, stores):
        self.result = SearchArgAt(stores, M.Zero)()
        super().__init__(inputs=M.Pair(stores, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobStoresTheoremRuleCache(M.Edge):
    def __init__(self, stores):
        self.result = SearchArgAt(stores, M.one)()
        super().__init__(inputs=M.Pair(stores, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobStoresRewriteRules(M.Edge):
    def __init__(self, stores):
        self.result = SearchArgAt(stores, M.two)()
        super().__init__(inputs=M.Pair(stores, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchState(M.Edge):
    def __init__(self, current, plan_rev, seen, steps_remaining, cursor=None):
        if cursor is None:
            cursor = M.EmptyList
        self.result = M.Pair(
            SearchStateLabel,
            M.Pair(current, M.Pair(plan_rev, M.Pair(seen, M.Pair(steps_remaining, M.Pair(cursor, M.EmptyList))))),
        )
        super().__init__(
            inputs=M.Pair(current, M.Pair(plan_rev, M.Pair(seen, M.Pair(steps_remaining, M.Pair(cursor, M.EmptyList))))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchStateCurrent(M.Edge):
    def __init__(self, state):
        self.result = SearchArgAt(state, M.Zero)()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchStatePlan(M.Edge):
    def __init__(self, state):
        self.result = SearchArgAt(state, M.one)()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchStateSeen(M.Edge):
    def __init__(self, state):
        self.result = SearchArgAt(state, M.two)()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchStateStepsRemaining(M.Edge):
    def __init__(self, state):
        self.result = SearchArgAt(state, M.three)()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchStateCursor(M.Edge):
    def __init__(self, state):
        self.result = SearchArgAt(state, M.four)()
        super().__init__(inputs=M.Pair(state, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchTheoremCursor(M.Edge):
    def __init__(
        self,
        rules,
        generated,
        knowledge_head_index=None,
        knowledge_exact_trie=None,
        delta=None,
        next_delta=None,
        actions_rev=None,
        current=None,
    ):
        if knowledge_head_index is None:
            knowledge_head_index = M.EmptyList
        if knowledge_exact_trie is None:
            knowledge_exact_trie = M.EmptyList
        if delta is None:
            delta = M.EmptyList
        if next_delta is None:
            next_delta = M.EmptyList
        if actions_rev is None:
            actions_rev = M.EmptyList
        if current is None:
            current = M.EmptyList
        self.result = M.Pair(
            SearchTheoremCursorLabel,
            M.Pair(
                rules,
                M.Pair(
                    generated,
                    M.Pair(
                        knowledge_head_index,
                        M.Pair(
                            knowledge_exact_trie,
                            M.Pair(
                                delta,
                                M.Pair(
                                    next_delta,
                                    M.Pair(actions_rev, M.Pair(current, M.EmptyList)),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                rules,
                M.Pair(
                    generated,
                    M.Pair(
                        knowledge_head_index,
                        M.Pair(
                            knowledge_exact_trie,
                            M.Pair(
                                delta,
                                M.Pair(
                                    next_delta,
                                    M.Pair(actions_rev, M.Pair(current, M.EmptyList)),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchTheoremCursorRules(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.Zero)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchTheoremCursorGenerated(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.one)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchTheoremCursorHeadIndex(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.two)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchTheoremCursorExactTrie(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.three)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchTheoremCursorDelta(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.four)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchTheoremCursorNextDelta(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.five)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchTheoremCursorActions(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.six)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchTheoremCursorCurrent(M.Edge):
    def __init__(self, cursor):
        if SearchChainHasAt(SearchArgs(cursor)(), M.seven)() is M.truth_value:
            self.result = SearchArgAt(cursor, M.seven)()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewritePathFrame(M.Edge):
    def __init__(self, subterm, path, rules=None, expanded=None):
        if rules is None:
            rules = M.EmptyList
        if expanded is None:
            expanded = M.false_value
        self.result = M.Pair(
            SearchRewritePathFrameLabel,
            M.Pair(subterm, M.Pair(path, M.Pair(rules, M.Pair(expanded, M.EmptyList)))),
        )
        super().__init__(inputs=M.Pair(subterm, M.Pair(path, M.Pair(rules, M.Pair(expanded, M.EmptyList)))), results=self.result)

    def __call__(self):
        return self.result


class SearchRewritePathFrameSubterm(M.Edge):
    def __init__(self, frame):
        self.result = SearchArgAt(frame, M.Zero)()
        super().__init__(inputs=M.Pair(frame, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewritePathFramePath(M.Edge):
    def __init__(self, frame):
        self.result = SearchArgAt(frame, M.one)()
        super().__init__(inputs=M.Pair(frame, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewritePathFrameRules(M.Edge):
    def __init__(self, frame):
        if SearchChainHasAt(SearchArgs(frame)(), M.two)() is M.truth_value:
            self.result = SearchArgAt(frame, M.two)()
        else:
            self.result = M.EmptyList
        super().__init__(inputs=M.Pair(frame, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewritePathFrameExpanded(M.Edge):
    def __init__(self, frame):
        if SearchChainHasAt(SearchArgs(frame)(), M.three)() is M.truth_value:
            self.result = SearchArgAt(frame, M.three)()
        else:
            self.result = M.false_value
        super().__init__(inputs=M.Pair(frame, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewriteRuleBundle(M.Edge):
    def __init__(self, rules, index_tree, wildcards):
        self.result = M.Pair(
            SearchRewriteRuleBundleLabel,
            M.Pair(rules, M.Pair(index_tree, M.Pair(wildcards, M.EmptyList))),
        )
        super().__init__(inputs=M.Pair(rules, M.Pair(index_tree, M.Pair(wildcards, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class SearchRewriteRuleBundleRules(M.Edge):
    def __init__(self, bundle):
        self.result = SearchArgAt(bundle, M.Zero)()
        super().__init__(inputs=M.Pair(bundle, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewriteRuleBundleIndex(M.Edge):
    def __init__(self, bundle):
        self.result = SearchArgAt(bundle, M.one)()
        super().__init__(inputs=M.Pair(bundle, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewriteRuleBundleWildcards(M.Edge):
    def __init__(self, bundle):
        self.result = SearchArgAt(bundle, M.two)()
        super().__init__(inputs=M.Pair(bundle, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewriteCursor(M.Edge):
    def __init__(self, rule, rest_rules, agenda, generated):
        self.result = M.Pair(
            SearchRewriteCursorLabel,
            M.Pair(rule, M.Pair(rest_rules, M.Pair(agenda, M.Pair(generated, M.EmptyList)))),
        )
        super().__init__(
            inputs=M.Pair(rule, M.Pair(rest_rules, M.Pair(agenda, M.Pair(generated, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchRewriteCursorRule(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.Zero)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewriteCursorRestRules(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.one)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewriteCursorAgenda(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.two)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchRewriteCursorGenerated(M.Edge):
    def __init__(self, cursor):
        self.result = SearchArgAt(cursor, M.three)()
        super().__init__(inputs=M.Pair(cursor, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result



class SearchJob(M.Edge):
    def __init__(
        self,
        start,
        goal,
        rules,
        heuristic,
        status,
        frontier,
        expanded,
        generated,
        frontier_peak,
        result_plan,
        visited=None,
        theorem_rule_cache=None,
        rewrite_rules=None,
        frontier_size=None,
    ):
        if visited is None:
            visited = M.EmptyList
        if theorem_rule_cache is None:
            theorem_rule_cache = M.EmptyList
        if rewrite_rules is None:
            rewrite_rules = M.EmptyList
        if frontier_size is None:
            frontier_size = M.EmptyList
        progress = SearchJobProgress(
            frontier,
            expanded,
            generated,
            frontier_size,
            frontier_peak,
            result_plan,
        )()
        stores = SearchJobStores(visited, theorem_rule_cache, rewrite_rules)()
        self.result = M.Pair(
            SearchJobLabel,
            M.Pair(
                start,
                M.Pair(
                    goal,
                    M.Pair(
                        rules,
                        M.Pair(
                            heuristic,
                            M.Pair(status, M.Pair(progress, M.Pair(stores, M.EmptyList))),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                start,
                M.Pair(
                    goal,
                    M.Pair(
                        rules,
                        M.Pair(
                            heuristic,
                            M.Pair(
                                status,
                                M.Pair(
                                    frontier,
                                    M.Pair(
                                        expanded,
                                        M.Pair(
                                            generated,
                                            M.Pair(
                                                frontier_size,
                                                M.Pair(
                                                    frontier_peak,
                                                    M.Pair(
                                                        result_plan,
                                                        M.Pair(
                                                            visited,
                                                            M.Pair(theorem_rule_cache, M.Pair(rewrite_rules, M.EmptyList)),
                                                        ),
                                                    ),
                                                ),
                                            ),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchJobStart(M.Edge):
    def __init__(self, job):
        self.result = SearchArgAt(job, M.Zero)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobGoal(M.Edge):
    def __init__(self, job):
        self.result = SearchArgAt(job, M.one)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobRules(M.Edge):
    def __init__(self, job):
        self.result = SearchArgAt(job, M.two)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobHeuristic(M.Edge):
    def __init__(self, job):
        self.result = SearchArgAt(job, M.three)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobProgressBlock(M.Edge):
    def __init__(self, job):
        progress = SearchArgAt(job, M.five)()
        if M.IsPair(progress)() is M.truth_value:
            if M.IdentityCompare(M.Head(progress)(), SearchJobProgressLabel)() is M.truth_value:
                self.result = progress
            else:
                suffix = SearchArgsFrom(job, M.eight)()
                frontier_size = M.EmptyList
                frontier_peak = SearchChainAt(suffix, M.Zero)()
                result_plan = SearchChainAt(suffix, M.one)()
                if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                    frontier_size = SearchChainAt(suffix, M.Zero)()
                    frontier_peak = SearchChainAt(suffix, M.one)()
                    result_plan = SearchChainAt(suffix, M.two)()
                self.result = SearchJobProgress(
                    progress,
                    SearchArgAt(job, M.six)(),
                    SearchArgAt(job, M.seven)(),
                    frontier_size,
                    frontier_peak,
                    result_plan,
                )()
        else:
            suffix = SearchArgsFrom(job, M.eight)()
            frontier_size = M.EmptyList
            frontier_peak = SearchChainAt(suffix, M.Zero)()
            result_plan = SearchChainAt(suffix, M.one)()
            if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                frontier_size = SearchChainAt(suffix, M.Zero)()
                frontier_peak = SearchChainAt(suffix, M.one)()
                result_plan = SearchChainAt(suffix, M.two)()
            self.result = SearchJobProgress(
                progress,
                SearchArgAt(job, M.six)(),
                SearchArgAt(job, M.seven)(),
                frontier_size,
                frontier_peak,
                result_plan,
            )()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobStoresBlock(M.Edge):
    def __init__(self, job):
        stores = SearchArgAt(job, M.six)()
        if M.IsPair(stores)() is M.truth_value:
            if M.IdentityCompare(M.Head(stores)(), SearchJobStoresLabel)() is M.truth_value:
                self.result = stores
            else:
                suffix = SearchArgsFrom(job, M.eight)()
                visited = SearchChainAt(suffix, M.two)()
                theorem_rule_cache = SearchChainAt(suffix, M.three)()
                rewrite_rules = SearchChainAt(suffix, M.four)()
                if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                    visited = SearchChainAt(suffix, M.three)()
                    theorem_rule_cache = SearchChainAt(suffix, M.four)()
                    rewrite_rules = SearchChainAt(suffix, M.five)()
                self.result = SearchJobStores(visited, theorem_rule_cache, rewrite_rules)()
        else:
            suffix = SearchArgsFrom(job, M.eight)()
            visited = SearchChainAt(suffix, M.two)()
            theorem_rule_cache = SearchChainAt(suffix, M.three)()
            rewrite_rules = SearchChainAt(suffix, M.four)()
            if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                visited = SearchChainAt(suffix, M.three)()
                theorem_rule_cache = SearchChainAt(suffix, M.four)()
                rewrite_rules = SearchChainAt(suffix, M.five)()
            self.result = SearchJobStores(visited, theorem_rule_cache, rewrite_rules)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobStatus(M.Edge):
    def __init__(self, job):
        self.result = SearchArgAt(job, M.four)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobFrontier(M.Edge):
    def __init__(self, job):
        progress = SearchArgAt(job, M.five)()
        if M.IsPair(progress)() is M.truth_value:
            if M.IdentityCompare(M.Head(progress)(), SearchJobProgressLabel)() is M.truth_value:
                self.result = SearchJobProgressFrontier(progress)()
            else:
                self.result = progress
        else:
            self.result = progress
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobExpanded(M.Edge):
    def __init__(self, job):
        progress = SearchArgAt(job, M.five)()
        if M.IsPair(progress)() is M.truth_value:
            if M.IdentityCompare(M.Head(progress)(), SearchJobProgressLabel)() is M.truth_value:
                self.result = SearchJobProgressExpanded(progress)()
            else:
                self.result = SearchArgAt(job, M.six)()
        else:
            self.result = SearchArgAt(job, M.six)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobGenerated(M.Edge):
    def __init__(self, job):
        progress = SearchArgAt(job, M.five)()
        if M.IsPair(progress)() is M.truth_value:
            if M.IdentityCompare(M.Head(progress)(), SearchJobProgressLabel)() is M.truth_value:
                self.result = SearchJobProgressGenerated(progress)()
            else:
                self.result = SearchArgAt(job, M.seven)()
        else:
            self.result = SearchArgAt(job, M.seven)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobFrontierSizePresent(M.Edge):
    def __init__(self, job):
        frontier_size = SearchJobFrontierSize(job)()
        if M.IdentityCompare(frontier_size, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            self.result = M.truth_value
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobFrontierPeak(M.Edge):
    def __init__(self, job):
        progress = SearchArgAt(job, M.five)()
        if M.IsPair(progress)() is M.truth_value:
            if M.IdentityCompare(M.Head(progress)(), SearchJobProgressLabel)() is M.truth_value:
                self.result = SearchJobProgressFrontierPeak(progress)()
            else:
                suffix = SearchArgsFrom(job, M.eight)()
                if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                    self.result = SearchChainAt(suffix, M.one)()
                else:
                    self.result = SearchChainAt(suffix, M.Zero)()
        else:
            suffix = SearchArgsFrom(job, M.eight)()
            if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                self.result = SearchChainAt(suffix, M.one)()
            else:
                self.result = SearchChainAt(suffix, M.Zero)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobFrontierSize(M.Edge):
    def __init__(self, job):
        progress = SearchArgAt(job, M.five)()
        if M.IsPair(progress)() is M.truth_value:
            if M.IdentityCompare(M.Head(progress)(), SearchJobProgressLabel)() is M.truth_value:
                self.result = SearchJobProgressFrontierSize(progress)()
            else:
                suffix = SearchArgsFrom(job, M.eight)()
                if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                    self.result = SearchChainAt(suffix, M.Zero)()
                else:
                    self.result = M.EmptyList
        else:
            suffix = SearchArgsFrom(job, M.eight)()
            if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                self.result = SearchChainAt(suffix, M.Zero)()
            else:
                self.result = M.EmptyList
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobResultPlan(M.Edge):
    def __init__(self, job):
        progress = SearchArgAt(job, M.five)()
        if M.IsPair(progress)() is M.truth_value:
            if M.IdentityCompare(M.Head(progress)(), SearchJobProgressLabel)() is M.truth_value:
                self.result = SearchJobProgressResultPlan(progress)()
            else:
                suffix = SearchArgsFrom(job, M.eight)()
                if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                    self.result = SearchChainAt(suffix, M.two)()
                else:
                    self.result = SearchChainAt(suffix, M.one)()
        else:
            suffix = SearchArgsFrom(job, M.eight)()
            if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                self.result = SearchChainAt(suffix, M.two)()
            else:
                self.result = SearchChainAt(suffix, M.one)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobVisited(M.Edge):
    def __init__(self, job):
        stores = SearchArgAt(job, M.six)()
        if M.IsPair(stores)() is M.truth_value:
            if M.IdentityCompare(M.Head(stores)(), SearchJobStoresLabel)() is M.truth_value:
                self.result = SearchJobStoresVisited(stores)()
            else:
                suffix = SearchArgsFrom(job, M.eight)()
                if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                    self.result = SearchChainAt(suffix, M.three)()
                else:
                    self.result = SearchChainAt(suffix, M.two)()
        else:
            suffix = SearchArgsFrom(job, M.eight)()
            if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                self.result = SearchChainAt(suffix, M.three)()
            else:
                self.result = SearchChainAt(suffix, M.two)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobTheoremRuleCache(M.Edge):
    def __init__(self, job):
        stores = SearchArgAt(job, M.six)()
        if M.IsPair(stores)() is M.truth_value:
            if M.IdentityCompare(M.Head(stores)(), SearchJobStoresLabel)() is M.truth_value:
                self.result = SearchJobStoresTheoremRuleCache(stores)()
            else:
                suffix = SearchArgsFrom(job, M.eight)()
                if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                    self.result = SearchChainAt(suffix, M.four)()
                else:
                    self.result = SearchChainAt(suffix, M.three)()
        else:
            suffix = SearchArgsFrom(job, M.eight)()
            if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                self.result = SearchChainAt(suffix, M.four)()
            else:
                self.result = SearchChainAt(suffix, M.three)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchJobRewriteRules(M.Edge):
    def __init__(self, job):
        stores = SearchArgAt(job, M.six)()
        if M.IsPair(stores)() is M.truth_value:
            if M.IdentityCompare(M.Head(stores)(), SearchJobStoresLabel)() is M.truth_value:
                self.result = SearchJobStoresRewriteRules(stores)()
            else:
                suffix = SearchArgsFrom(job, M.eight)()
                if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                    self.result = SearchChainAt(suffix, M.five)()
                else:
                    self.result = SearchChainAt(suffix, M.four)()
        else:
            suffix = SearchArgsFrom(job, M.eight)()
            if SearchChainHasAt(suffix, M.five)() is M.truth_value:
                self.result = SearchChainAt(suffix, M.five)()
            else:
                self.result = SearchChainAt(suffix, M.four)()
        super().__init__(inputs=M.Pair(job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LookupSearchJob(M.Edge):
    def __init__(self, start, goal, heuristic, jobs):
        self.result = self._lookup(start, goal, heuristic, jobs)
        super().__init__(inputs=M.Pair(start, M.Pair(goal, M.Pair(heuristic, M.Pair(jobs, M.EmptyList)))), results=self.result)

    def _matches(self, job, start, goal, heuristic):
        same_start = M.TermEqual(SearchJobStart(job)(), start)()
        same_goal = M.TermEqual(SearchJobGoal(job)(), goal)()
        same_heuristic = M.TermEqual(SearchJobHeuristic(job)(), heuristic)()
        return M.AndAtom(same_start, M.AndAtom(same_goal, same_heuristic)())()

    def _lookup(self, start, goal, heuristic, jobs):
        if M.IdentityCompare(jobs, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        job = M.Head(jobs)()
        if self._matches(job, start, goal, heuristic) is M.truth_value:
            return job
        return self._lookup(start, goal, heuristic, M.Tail(jobs)())

    def __call__(self):
        return self.result


class RemoveSearchJob(M.Edge):
    def __init__(self, start, goal, heuristic, jobs):
        self.result = self._remove(start, goal, heuristic, jobs)
        super().__init__(inputs=M.Pair(start, M.Pair(goal, M.Pair(heuristic, M.Pair(jobs, M.EmptyList)))), results=self.result)

    def _matches(self, job, start, goal, heuristic):
        same_start = M.TermEqual(SearchJobStart(job)(), start)()
        same_goal = M.TermEqual(SearchJobGoal(job)(), goal)()
        same_heuristic = M.TermEqual(SearchJobHeuristic(job)(), heuristic)()
        return M.AndAtom(same_start, M.AndAtom(same_goal, same_heuristic)())()

    def _remove(self, start, goal, heuristic, jobs):
        if M.IdentityCompare(jobs, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        job = M.Head(jobs)()
        rest = self._remove(start, goal, heuristic, M.Tail(jobs)())
        if self._matches(job, start, goal, heuristic) is M.truth_value:
            return rest
        return M.Pair(job, rest)

    def __call__(self):
        return self.result


class LookupSearchAttempt(M.Edge):
    def __init__(self, start, goal, heuristic, attempts):
        self.result = self._lookup(start, goal, heuristic, attempts)
        super().__init__(inputs=M.Pair(start, M.Pair(goal, M.Pair(heuristic, M.Pair(attempts, M.EmptyList)))), results=self.result)

    def _lookup(self, start, goal, heuristic, attempts):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        attempt = M.Head(attempts)()
        same_start = M.TermEqual(SearchAttemptStart(attempt)(), start)()
        same_goal = M.TermEqual(SearchAttemptGoal(attempt)(), goal)()
        same_heuristic = M.TermEqual(SearchAttemptHeuristic(attempt)(), heuristic)()
        if M.AndAtom(same_start, M.AndAtom(same_goal, same_heuristic)())() is M.truth_value:
            return attempt
        return self._lookup(start, goal, heuristic, M.Tail(attempts)())

    def __call__(self):
        return self.result


class SearchSignature(M.Edge):
    def __init__(self, start_head, goal_head):
        self.result = M.Pair(SearchSignatureLabel, M.Pair(start_head, M.Pair(goal_head, M.EmptyList)))
        super().__init__(inputs=M.Pair(start_head, M.Pair(goal_head, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchSignatureForProblem(M.Edge):
    def __init__(self, start, goal, registry):
        start_head = TermHead(start, registry)()
        goal_head = TermHead(goal, registry)()
        self.result = SearchSignature(start_head, goal_head)()
        super().__init__(inputs=M.Pair(start, M.Pair(goal, M.Pair(registry, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonSummary(M.Edge):
    def __init__(self, attempts, best_attempt, outcome):
        self.result = M.Pair(
            SearchComparisonSummaryLabel,
            M.Pair(attempts, M.Pair(best_attempt, M.Pair(outcome, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(attempts, M.Pair(best_attempt, M.Pair(outcome, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchComparisonSummaryAttempts(M.Edge):
    def __init__(self, summary):
        self.result = SearchArgAt(summary, M.Zero)()
        super().__init__(inputs=M.Pair(summary, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonSummaryBestAttempt(M.Edge):
    def __init__(self, summary):
        self.result = SearchArgAt(summary, M.one)()
        super().__init__(inputs=M.Pair(summary, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonSummaryOutcome(M.Edge):
    def __init__(self, summary):
        self.result = SearchArgAt(summary, M.two)()
        super().__init__(inputs=M.Pair(summary, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparison(M.Edge):
    def __init__(self, signature, attempts, best_attempt, outcome=None):
        if outcome is None:
            outcome = M.EmptyList
        summary = SearchComparisonSummary(attempts, best_attempt, outcome)()
        self.result = M.Pair(
            SearchComparisonLabel,
            M.Pair(signature, M.Pair(summary, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(signature, M.Pair(attempts, M.Pair(best_attempt, M.Pair(outcome, M.EmptyList)))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchComparisonSummaryBlock(M.Edge):
    def __init__(self, comparison):
        summary = SearchArgAt(comparison, M.one)()
        if M.IsPair(summary)() is M.truth_value:
            if M.IdentityCompare(M.Head(summary)(), SearchComparisonSummaryLabel)() is M.truth_value:
                self.result = summary
            else:
                outcome = M.EmptyList
                if SearchChainHasAt(SearchArgs(comparison)(), M.three)() is M.truth_value:
                    outcome = SearchArgAt(comparison, M.three)()
                self.result = SearchComparisonSummary(summary, SearchArgAt(comparison, M.two)(), outcome)()
        else:
            outcome = M.EmptyList
            if SearchChainHasAt(SearchArgs(comparison)(), M.three)() is M.truth_value:
                outcome = SearchArgAt(comparison, M.three)()
            self.result = SearchComparisonSummary(summary, SearchArgAt(comparison, M.two)(), outcome)()
        super().__init__(inputs=M.Pair(comparison, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonSignature(M.Edge):
    def __init__(self, comparison):
        self.result = SearchArgAt(comparison, M.Zero)()
        super().__init__(inputs=M.Pair(comparison, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonAttempts(M.Edge):
    def __init__(self, comparison):
        summary = SearchArgAt(comparison, M.one)()
        if M.IsPair(summary)() is M.truth_value:
            if M.IdentityCompare(M.Head(summary)(), SearchComparisonSummaryLabel)() is M.truth_value:
                self.result = SearchComparisonSummaryAttempts(summary)()
            else:
                self.result = summary
        else:
            self.result = summary
        super().__init__(inputs=M.Pair(comparison, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonBestAttempt(M.Edge):
    def __init__(self, comparison):
        summary = SearchArgAt(comparison, M.one)()
        if M.IsPair(summary)() is M.truth_value:
            if M.IdentityCompare(M.Head(summary)(), SearchComparisonSummaryLabel)() is M.truth_value:
                self.result = SearchComparisonSummaryBestAttempt(summary)()
            else:
                self.result = SearchArgAt(comparison, M.two)()
        else:
            self.result = SearchArgAt(comparison, M.two)()
        super().__init__(inputs=M.Pair(comparison, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonOutcome(M.Edge):
    def __init__(self, comparison):
        summary = SearchArgAt(comparison, M.one)()
        if M.IsPair(summary)() is M.truth_value:
            if M.IdentityCompare(M.Head(summary)(), SearchComparisonSummaryLabel)() is M.truth_value:
                outcome = SearchComparisonSummaryOutcome(summary)()
                best_attempt = SearchComparisonSummaryBestAttempt(summary)()
            else:
                outcome = M.EmptyList
                best_attempt = SearchArgAt(comparison, M.two)()
                if SearchChainHasAt(SearchArgs(comparison)(), M.three)() is M.truth_value:
                    outcome = SearchArgAt(comparison, M.three)()
        else:
            outcome = M.EmptyList
            best_attempt = SearchArgAt(comparison, M.two)()
            if SearchChainHasAt(SearchArgs(comparison)(), M.three)() is M.truth_value:
                outcome = SearchArgAt(comparison, M.three)()
        if M.Compare(outcome, M.EmptyList)() is M.truth_value:
            if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
                self.result = SearchFailureLabel
            else:
                self.result = SearchAttemptStatus(best_attempt)()
        else:
            self.result = outcome
        super().__init__(inputs=M.Pair(comparison, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonJob(M.Edge):
    def __init__(self, signature, start, goal, rules, heuristic, states, outcome):
        problem = SearchComparisonJobProblem(start, goal, rules, heuristic)()
        runtime = SearchComparisonJobRuntime(states, outcome)()
        self.result = M.Pair(
            SearchComparisonJobLabel,
            M.Pair(
                signature,
                M.Pair(problem, M.Pair(runtime, M.EmptyList)),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                signature,
                M.Pair(
                    start,
                    M.Pair(
                        goal,
                        M.Pair(rules, M.Pair(heuristic, M.Pair(states, M.Pair(outcome, M.EmptyList)))),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchComparisonJobProblem(M.Edge):
    def __init__(self, start, goal, rules, heuristic):
        self.result = M.Pair(
            SearchComparisonJobProblemLabel,
            M.Pair(
                start,
                M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.EmptyList))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                start,
                M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchComparisonJobProblemBlock(M.Edge):
    def __init__(self, comparison_job):
        problem = SearchArgAt(comparison_job, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchComparisonJobProblemLabel)() is M.truth_value:
                self.result = problem
            else:
                self.result = SearchComparisonJobProblem(
                    problem,
                    SearchArgAt(comparison_job, M.two)(),
                    SearchArgAt(comparison_job, M.three)(),
                    SearchArgAt(comparison_job, M.four)(),
                )()
        else:
            self.result = SearchComparisonJobProblem(
                problem,
                SearchArgAt(comparison_job, M.two)(),
                SearchArgAt(comparison_job, M.three)(),
                SearchArgAt(comparison_job, M.four)(),
            )()
        super().__init__(inputs=M.Pair(comparison_job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonJobRuntime(M.Edge):
    def __init__(self, states, outcome):
        self.result = M.Pair(
            SearchComparisonJobRuntimeLabel,
            M.Pair(states, M.Pair(outcome, M.EmptyList)),
        )
        super().__init__(
            inputs=M.Pair(states, M.Pair(outcome, M.EmptyList)),
            results=self.result,
        )

    def __call__(self):
        return self.result


class SearchComparisonJobRuntimeBlock(M.Edge):
    def __init__(self, comparison_job):
        runtime = SearchArgAt(comparison_job, M.two)()
        if M.IsPair(runtime)() is M.truth_value:
            if M.IdentityCompare(M.Head(runtime)(), SearchComparisonJobRuntimeLabel)() is M.truth_value:
                self.result = runtime
            else:
                self.result = SearchComparisonJobRuntime(
                    SearchArgAt(comparison_job, M.five)(),
                    SearchArgAt(comparison_job, M.six)(),
                )()
        else:
            self.result = SearchComparisonJobRuntime(
                SearchArgAt(comparison_job, M.five)(),
                SearchArgAt(comparison_job, M.six)(),
            )()
        super().__init__(inputs=M.Pair(comparison_job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonJobSignature(M.Edge):
    def __init__(self, comparison_job):
        self.result = SearchArgAt(comparison_job, M.Zero)()
        super().__init__(inputs=M.Pair(comparison_job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonJobStart(M.Edge):
    def __init__(self, comparison_job):
        problem = SearchArgAt(comparison_job, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchComparisonJobProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(problem, M.Zero)()
            else:
                self.result = problem
        else:
            self.result = problem
        super().__init__(inputs=M.Pair(comparison_job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonJobGoal(M.Edge):
    def __init__(self, comparison_job):
        problem = SearchArgAt(comparison_job, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchComparisonJobProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(problem, M.one)()
            else:
                self.result = SearchArgAt(comparison_job, M.two)()
        else:
            self.result = SearchArgAt(comparison_job, M.two)()
        super().__init__(inputs=M.Pair(comparison_job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonJobRules(M.Edge):
    def __init__(self, comparison_job):
        problem = SearchArgAt(comparison_job, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchComparisonJobProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(problem, M.two)()
            else:
                self.result = SearchArgAt(comparison_job, M.three)()
        else:
            self.result = SearchArgAt(comparison_job, M.three)()
        super().__init__(inputs=M.Pair(comparison_job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonJobHeuristic(M.Edge):
    def __init__(self, comparison_job):
        problem = SearchArgAt(comparison_job, M.one)()
        if M.IsPair(problem)() is M.truth_value:
            if M.IdentityCompare(M.Head(problem)(), SearchComparisonJobProblemLabel)() is M.truth_value:
                self.result = SearchArgAt(problem, M.three)()
            else:
                self.result = SearchArgAt(comparison_job, M.four)()
        else:
            self.result = SearchArgAt(comparison_job, M.four)()
        super().__init__(inputs=M.Pair(comparison_job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonJobStates(M.Edge):
    def __init__(self, comparison_job):
        runtime = SearchArgAt(comparison_job, M.two)()
        if M.IsPair(runtime)() is M.truth_value:
            if M.IdentityCompare(M.Head(runtime)(), SearchComparisonJobRuntimeLabel)() is M.truth_value:
                self.result = SearchArgAt(runtime, M.Zero)()
            else:
                self.result = SearchArgAt(comparison_job, M.five)()
        else:
            self.result = SearchArgAt(comparison_job, M.five)()
        super().__init__(inputs=M.Pair(comparison_job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonJobOutcome(M.Edge):
    def __init__(self, comparison_job):
        runtime = SearchArgAt(comparison_job, M.two)()
        if M.IsPair(runtime)() is M.truth_value:
            if M.IdentityCompare(M.Head(runtime)(), SearchComparisonJobRuntimeLabel)() is M.truth_value:
                self.result = SearchArgAt(runtime, M.one)()
            else:
                self.result = SearchArgAt(comparison_job, M.six)()
        else:
            self.result = SearchArgAt(comparison_job, M.six)()
        super().__init__(inputs=M.Pair(comparison_job, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LookupSearchComparisonJob(M.Edge):
    def __init__(self, signature, comparison_jobs):
        self.result = self._lookup(signature, comparison_jobs)
        super().__init__(inputs=M.Pair(signature, M.Pair(comparison_jobs, M.EmptyList)), results=self.result)

    def _lookup(self, signature, comparison_jobs):
        if M.IdentityCompare(comparison_jobs, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        comparison_job = M.Head(comparison_jobs)()
        if M.TermEqual(SearchComparisonJobSignature(comparison_job)(), signature)() is M.truth_value:
            return comparison_job
        return self._lookup(signature, M.Tail(comparison_jobs)())

    def __call__(self):
        return self.result


class RemoveSearchComparisonJob(M.Edge):
    def __init__(self, signature, comparison_jobs):
        self.result = self._remove(signature, comparison_jobs)
        super().__init__(inputs=M.Pair(signature, M.Pair(comparison_jobs, M.EmptyList)), results=self.result)

    def _remove(self, signature, comparison_jobs):
        if M.IdentityCompare(comparison_jobs, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        comparison_job = M.Head(comparison_jobs)()
        rest = self._remove(signature, M.Tail(comparison_jobs)())
        if M.TermEqual(SearchComparisonJobSignature(comparison_job)(), signature)() is M.truth_value:
            return rest
        return M.Pair(comparison_job, rest)

    def __call__(self):
        return self.result


class SearchComparisonBestHeuristic(M.Edge):
    def __init__(self, comparison):
        best_attempt = SearchComparisonBestAttempt(comparison)()
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            self.result = M.EmptyList
        else:
            self.result = SearchAttemptHeuristic(best_attempt)()
        super().__init__(inputs=M.Pair(comparison, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchComparisonHasUniqueBestAttempt(M.Edge):
    def __init__(self, comparison):
        best_attempt = SearchComparisonBestAttempt(comparison)()
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            self.result = M.false_value
        else:
            self.result = self._all_other_attempts_worse(SearchComparisonAttempts(comparison)(), best_attempt)
        super().__init__(inputs=M.Pair(comparison, M.EmptyList), results=self.result)

    def _attempt_ties_best(self, attempt, best_attempt):
        if M.TermEqual(attempt, best_attempt)() is M.truth_value:
            return M.false_value
        if M.TermEqual(SearchAttemptStatus(attempt)(), SearchAttemptStatus(best_attempt)())() is M.false_value:
            return M.false_value
        if M.TermEqual(M.TotalCostValue(SearchAttemptTotalCost(attempt)())(), M.TotalCostValue(SearchAttemptTotalCost(best_attempt)())())() is M.false_value:
            return M.false_value
        return M.truth_value

    def _all_other_attempts_worse(self, attempts, best_attempt):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return M.truth_value
        attempt = M.Head(attempts)()
        if self._attempt_ties_best(attempt, best_attempt) is M.truth_value:
            return M.false_value
        return self._all_other_attempts_worse(M.Tail(attempts)(), best_attempt)

    def __call__(self):
        return self.result


class LookupSearchComparison(M.Edge):
    def __init__(self, signature, comparisons):
        self.result = self._lookup(signature, comparisons)
        super().__init__(inputs=M.Pair(signature, M.Pair(comparisons, M.EmptyList)), results=self.result)

    def _lookup(self, signature, comparisons):
        if M.IdentityCompare(comparisons, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        comparison = M.Head(comparisons)()
        if M.TermEqual(SearchComparisonSignature(comparison)(), signature)() is M.truth_value:
            return comparison
        return self._lookup(signature, M.Tail(comparisons)())

    def __call__(self):
        return self.result


class SearchModeText(M.Edge):
    def __init__(self, mode):
        if M.IdentityCompare(mode, DFSLabel)() is M.truth_value:
            self.result = "SearchDFS"
        elif M.IdentityCompare(mode, BFSLabel)() is M.truth_value:
            self.result = "SearchBFS"
        elif M.IdentityCompare(mode, BeamLabel)() is M.truth_value:
            self.result = "SearchBeam"
        elif M.IdentityCompare(mode, AStarLabel)() is M.truth_value:
            self.result = "SearchAStar"
        elif M.IdentityCompare(mode, RewriteDFSLabel)() is M.truth_value:
            self.result = "SearchRewriteDFS"
        else:
            self.result = "Search"
        super().__init__(inputs=M.Pair(mode, M.EmptyList), results=M.EmptyList)

    def __call__(self):
        return self.result


class SearchStatusText(M.Edge):
    def __init__(self, status):
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
            self.result = "success"
        elif M.IdentityCompare(status, SearchFailureLabel)() is M.truth_value:
            self.result = "failure"
        elif M.IdentityCompare(status, SearchRunningLabel)() is M.truth_value:
            self.result = "running"
        elif M.IdentityCompare(status, SearchPausedLabel)() is M.truth_value:
            self.result = "paused"
        elif M.IdentityCompare(status, SearchTimedOutLabel)() is M.truth_value:
            self.result = "timed_out"
        elif M.IdentityCompare(status, SearchAbortedByUserLabel)() is M.truth_value:
            self.result = "aborted_by_user"
        else:
            self.result = "unknown"
        super().__init__(inputs=M.Pair(status, M.EmptyList), results=M.EmptyList)

    def __call__(self):
        return self.result


class SearchAdviceText(M.Edge):
    def __init__(self, comparison):
        heuristic = SearchComparisonBestHeuristic(comparison)()
        mode = HeuristicSearchMode(heuristic)()
        if SearchComparisonHasUniqueBestAttempt(comparison)() is M.truth_value:
            self.result = "We've found evidence " + SearchModeText(mode)() + " is best for this, so we'll use it again."
        else:
            self.result = "Comparison did not distinguish a unique best mode, so we are not claiming one."
        super().__init__(inputs=M.Pair(comparison, M.EmptyList), results=M.EmptyList)

    def __call__(self):
        return self.result

def _nat_units_or_zero(value, registry):
    text = M.PrettyTerm(value, registry)()
    if text == "[]":
        return 0
    return int(text)


class SearchMemoKey(M.Edge):
    def __init__(self, current_key, goal_key, steps_remaining):
        self.result = M.Pair(
            SearchSignatureLabel,
            M.Pair(current_key, M.Pair(goal_key, M.Pair(steps_remaining, M.EmptyList))),
        )
        super().__init__(inputs=M.Pair(current_key, M.Pair(goal_key, M.Pair(steps_remaining, M.EmptyList))), results=self.result)

    def __call__(self):
        return self.result


class SearchMemoEntry(M.Edge):
    def __init__(self, status, plan):
        self.result = M.Pair(
            SearchComparisonLabel,
            M.Pair(status, M.Pair(plan, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(status, M.Pair(plan, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class SearchMemoEntryStatus(M.Edge):
    def __init__(self, entry):
        self.result = SearchArgAt(entry, M.Zero)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class SearchMemoEntryPlan(M.Edge):
    def __init__(self, entry):
        self.result = SearchArgAt(entry, M.one)()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result

def sync_from_namespace(namespace):
    for name in (
        "DFSLabel",
        "BFSLabel",
        "BeamLabel",
        "AStarLabel",
        "RewriteDFSLabel",
        "GoalHeadOrderLabel",
        "KnowledgeLabel",
        "ContextSearchComparisonJobsLabel",
        "ContextSearchJobsLabel",
        "SearchSignatureLabel",
        "SearchComparisonLabel",
        "SearchComparisonJobLabel",
        "SearchComparisonJobProblemLabel",
        "SearchComparisonJobRuntimeLabel",
        "SearchComparisonSummaryLabel",
        "SearchCostLabel",
        "SearchJobLabel",
        "SearchJobProgressLabel",
        "SearchJobStoresLabel",
        "SearchStateLabel",
        "SearchTheoremCursorLabel",
        "SearchRewriteCursorLabel",
        "SearchRewritePathFrameLabel",
        "SearchRewriteRuleBundleLabel",
        "SearchPairKeyLabel",
        "SearchCtorKeyLabel",
        "SearchPatriciaTokenLabel",
        "SearchPatriciaPairTokenLabel",
        "SearchPatriciaStopTokenLabel",
        "SearchPatriciaLeafLabel",
        "SearchPatriciaBranchLabel",
        "SearchPatriciaChoiceLabel",
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchRunningLabel",
        "SearchPausedLabel",
        "SearchTimedOutLabel",
        "SearchAbortedByUserLabel",
        "SearchRootFastPathPhaseLabel",
        "SearchPacketSearchPhaseLabel",
        "SearchNoRootFastPathLabel",
        "SearchRootCacheResultLabel",
        "SearchRootSchemaResultLabel",
        "SearchRootGoalResultLabel",
        "SearchRootImmediateResultLabel",
        "SearchRootWaveShardLaunchLabel",
        "SearchWorkerBaselineProblemLabel",
        "SearchWorkerPacketStoresLabel",
        "SearchWorkerPacketControlsLabel",
        "SearchWorkerLaunchDispatchLabel",
        "SearchWorkerMetricsLabel",
        "SearchWorkerPayloadLabel"
    ):
        if name in namespace:
            globals()[name] = namespace[name]
