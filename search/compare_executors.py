from __future__ import annotations

import queue
import time

from .. import machine as M
from .. import proof as Pmod
from ..heuristics import *
from ..labels import *
from ..proof import *
from ..proof import _debug
from .model import *


class _ComparisonExecutorMixin:
    def _worker_baseline(self, state):
        parent_job = self._comparison_state_job(state)
        return SearchWorkerBaseline(
            M.FromContextGetConstructors(self.graph)(),
            SearchJobStart(parent_job)(),
            SearchJobGoal(parent_job)(),
            SearchJobRules(parent_job)(),
            SearchJobHeuristic(parent_job)(),
            SearchJobRewriteRules(parent_job)(),
            self._comparison_generation,
        )()

    def _worker_setup(self, state):
        return SearchWorkerSetup(self._comparison_state_mode(state), self._worker_baseline(state))()

    def _worker_problem_packet(self, state, packet_descriptor, step_budget, packet_token):
        parent_job = self._comparison_state_job(state)
        return SearchWorkerPacket(
            packet_descriptor,
            M.EmptyList,
            SearchJobVisited(parent_job)(),
            M.EmptyList,
            SearchJobRewriteRules(parent_job)(),
            step_budget,
            Pmod.DEBUG_TRACE_STATE(),
            M.truth_value,
            M.truth_value,
            packet_token,
            self._comparison_generation,
        )()

    def _comparison_packet_budget(self, mode, packet_state):
        packet = packet_state
        packet_state = self._comparison_packet_state(mode, packet)
        if M.IdentityCompare(packet_state, M.EmptyList)() is M.truth_value:
            return M.one
        quantum = HeuristicBeamWidth(self.heuristic)()
        if M.NatEq(quantum, M.Zero, self.registry)() is M.truth_value:
            quantum = self._comparison_packet_frontier_width(mode)
        else:
            quantum = self._succ_nat_local(quantum)
        if M.IsPair(packet)() is M.truth_value:
            if M.IdentityCompare(M.Head(packet)(), SearchJobLabel)() is M.truth_value:
                frontier_size = SearchJobFrontierSize(packet)()
                scaled_pair = M.Multiply(frontier_size, quantum, self.registry)()
                quantum = M.Head(scaled_pair)()
                self.registry = M.Head(M.Tail(scaled_pair)())()
                if M.NatEq(quantum, M.Zero, self.registry)() is M.truth_value:
                    return M.one
                return quantum
        return self._nat_min_local(SearchStateStepsRemaining(packet_state)(), quantum)

    def _comparison_packet_job_for_state(self, state, packet_state):
        if M.IsPair(packet_state)() is M.truth_value:
            if M.IdentityCompare(M.Head(packet_state)(), SearchJobLabel)() is M.truth_value:
                return packet_state
        mode = self._comparison_state_mode(state)
        packet_state = self._comparison_packet_state(mode, packet_state)
        parent_job = self._comparison_state_job(state)
        return SearchJob(
            SearchJobStart(parent_job)(),
            SearchJobGoal(parent_job)(),
            SearchJobRules(parent_job)(),
            SearchJobHeuristic(parent_job)(),
            SearchRunningLabel,
            M.Pair(packet_state, M.EmptyList),
            M.Zero,
            M.Zero,
            M.Zero,
            M.EmptyList,
            SearchJobVisited(parent_job)(),
            M.EmptyList,
            SearchJobRewriteRules(parent_job)(),
            M.one,
        )()

    def _total_resident_executor_count(self, workers, idle_executors):
        return self._nat_add_local(self._worker_entry_count(workers), self._idle_executor_count(idle_executors))

    def _desired_resident_executor_total(self, states, workers, idle_executors):
        resident = self._total_resident_executor_count(workers, idle_executors)
        target_total = self._comparison_live_process_budget(states, workers)
        if M.NatLess(target_total, resident, self.registry)() is M.truth_value:
            return resident
        return target_total

    def _resident_executor(self, slot, process, task_queue, result_queue):
        return M.Pair(
            slot,
            M.Pair(
                process,
                M.Pair(
                    task_queue,
                    M.Pair(
                        result_queue,
                        M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList))),
                    ),
                ),
            ),
        )

    def _resident_executor_with_baseline(self, executor, generation, mode, rewrite_rules):
        return M.Pair(
            self._resident_executor_slot(executor),
            M.Pair(
                self._resident_executor_process(executor),
                M.Pair(
                    self._resident_executor_task_queue(executor),
                    M.Pair(
                        self._resident_executor_result_queue(executor),
                        M.Pair(generation, M.Pair(mode, M.Pair(rewrite_rules, M.EmptyList))),
                    ),
                ),
            ),
        )

    def _resident_executor_slot(self, executor):
        return M.Head(executor)()

    def _resident_executor_process(self, executor):
        return M.Head(M.Tail(executor)())()

    def _resident_executor_task_queue(self, executor):
        return M.Head(M.Tail(M.Tail(executor)())())()

    def _resident_executor_result_queue(self, executor):
        return M.Head(M.Tail(M.Tail(M.Tail(executor)())())())()

    def _resident_executor_generation(self, executor):
        suffix = M.Tail(M.Tail(M.Tail(M.Tail(executor)())())())()
        if M.IdentityCompare(suffix, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(suffix)()

    def _resident_executor_mode(self, executor):
        suffix = M.Tail(M.Tail(M.Tail(M.Tail(executor)())())())()
        if M.IdentityCompare(suffix, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        tail = M.Tail(suffix)()
        if M.IdentityCompare(tail, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(tail)()

    def _resident_executor_rewrite_rules(self, executor):
        suffix = M.Tail(M.Tail(M.Tail(M.Tail(executor)())())())()
        if M.IdentityCompare(suffix, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        tail = M.Tail(suffix)()
        if M.IdentityCompare(tail, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rewrite_payload = M.Tail(tail)()
        if M.IdentityCompare(rewrite_payload, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(rewrite_payload)()

    def _worker_entry(self, mode, executor, packet_job, packet_token):
        return M.Pair(mode, M.Pair(executor, M.Pair(packet_job, M.Pair(packet_token, M.Pair(time.time(), M.EmptyList)))))

    def _worker_entry_mode(self, entry):
        return M.Head(entry)()

    def _worker_entry_executor(self, entry):
        return M.Head(M.Tail(entry)())()

    def _worker_entry_process(self, entry):
        return self._resident_executor_process(self._worker_entry_executor(entry))

    def _worker_entry_queue(self, entry):
        return self._resident_executor_result_queue(self._worker_entry_executor(entry))

    def _worker_entry_packet_job(self, entry):
        return M.Head(M.Tail(M.Tail(entry)())())()

    def _worker_entry_packet_token(self, entry):
        payload = M.Tail(M.Tail(entry)())()
        if M.IdentityCompare(payload, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        rest = M.Tail(payload)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return M.Head(rest)()

    def _worker_entry_slot(self, entry):
        return self._resident_executor_slot(self._worker_entry_executor(entry))

    def _worker_entry_started_at(self, entry):
        payload = M.Tail(M.Tail(entry)())()
        if M.IdentityCompare(payload, M.EmptyList)() is M.truth_value:
            return None
        rest = M.Tail(payload)()
        if M.IdentityCompare(rest, M.EmptyList)() is M.truth_value:
            return None
        started_payload = M.Tail(rest)()
        if M.IdentityCompare(started_payload, M.EmptyList)() is M.truth_value:
            return None
        return M.Head(started_payload)()

    def _worker_entry_elapsed_seconds(self, entry):
        started_at = self._worker_entry_started_at(entry)
        if started_at is None:
            return 0.0
        elapsed_seconds = time.time() - started_at
        if elapsed_seconds < 0.0:
            return 0.0
        return elapsed_seconds

    def _oldest_active_worker_entry(self, workers):
        best_entry = M.EmptyList
        remaining_workers = workers
        best_elapsed_seconds = -1.0
        while M.IdentityCompare(remaining_workers, M.EmptyList)() is M.false_value:
            candidate = M.Head(remaining_workers)()
            candidate_elapsed_seconds = self._worker_entry_elapsed_seconds(candidate)
            if candidate_elapsed_seconds > best_elapsed_seconds:
                best_entry = candidate
                best_elapsed_seconds = candidate_elapsed_seconds
            remaining_workers = M.Tail(remaining_workers)()
        return best_entry

    def _sync_graph_live_compare_snapshot(self, states, workers, idle_executors):
        self.graph._search_compare_live_signature = self.signature
        self.graph._search_compare_live_start = self.start
        self.graph._search_compare_live_goal = self.goal
        self.graph._search_compare_live_states = states
        self.graph._search_compare_live_workers = workers
        self.graph._search_compare_live_idle_executors = idle_executors

    def _clear_graph_live_compare_snapshot(self):
        self.graph._search_compare_live_signature = M.EmptyList
        self.graph._search_compare_live_start = M.EmptyList
        self.graph._search_compare_live_goal = M.EmptyList
        self.graph._search_compare_live_states = M.EmptyList
        self.graph._search_compare_live_workers = M.EmptyList
        self.graph._search_compare_live_idle_executors = M.EmptyList

    def _worker_entry_count(self, workers):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return M.Zero
        count = M.Atom()
        count.value = M.CountRep(workers)()
        return count

    def _idle_executor_count(self, idle_executors):
        if M.IdentityCompare(idle_executors, M.EmptyList)() is M.truth_value:
            return M.Zero
        count = M.Atom()
        count.value = M.CountRep(idle_executors)()
        return count

    def _spawn_parallel_executor(self, mp_context, slot):
        from .runtime import _SearchModeWorkerExecutor

        slot_text = self._nat_text(slot)
        task_queue = mp_context.Queue()
        result_queue = mp_context.Queue()
        process = mp_context.Process(
            target=_SearchModeWorkerExecutor,
            args=(slot_text, task_queue, result_queue),
        )
        process.start()
        executor = self._resident_executor(slot, process, task_queue, result_queue)
        if self._await_parallel_executor_ready(executor) is M.false_value:
            self._retire_parallel_executor(executor, "retiring unready resident executor ")
            raise RuntimeError("search-compare: resident executor did not acknowledge startup")
        _debug(
            "search-compare: resident executor "
            + slot_text
            + " ready pid="
            + str(process.pid)
        )
        return executor

    def _parallel_executor_ready_message(self, payload):
        if M.IsPair(payload)() is M.false_value:
            return M.false_value
        return M.IdentityCompare(M.Head(payload)(), SearchWorkerReadyLabel)()

    def _await_parallel_executor_ready(self, executor):
        process = self._resident_executor_process(executor)
        result_queue = self._resident_executor_result_queue(executor)
        while process.is_alive():
            try:
                payload = result_queue.get_nowait()
            except queue.Empty:
                time.sleep(0.01)
                continue
            if self._parallel_executor_ready_message(payload) is M.truth_value:
                return M.truth_value
            return M.false_value
        return M.false_value

    def _start_parallel_executor_pool(self, mp_context):
        _debug("search-compare: elastic resident executor pool starts empty and grows on demand")
        return M.EmptyList

    def _grow_parallel_executor_pool(self, mp_context, idle_executors, states, workers):
        target_total = self._desired_resident_executor_total(states, workers, idle_executors)
        current_total = self._total_resident_executor_count(workers, idle_executors)
        spawned_now = M.Zero
        spawned_rev = M.EmptyList
        while M.NatLess(current_total, target_total, self.registry)() is M.truth_value:
            slot = self._succ_nat_local(current_total)
            try:
                executor = self._spawn_parallel_executor(mp_context, slot)
            except Exception as error:
                _debug(
                    "search-compare: resident executor spawn unavailable at slot "
                    + self._nat_text(slot)
                    + " ("
                    + str(error)
                    + "); leaving the remaining branch wave queued for retry"
                )
                break
            spawned_rev = M.Pair(executor, spawned_rev)
            current_total = slot
            spawned_now = self._succ_nat_local(spawned_now)
        if M.NatEq(spawned_now, M.Zero, self.registry)() is M.false_value:
            _debug(
                "search-compare: expanded elastic resident executor pool by "
                + self._nat_text(spawned_now)
                + " local workers; local capacity now "
                + self._nat_text(current_total)
            )
        return Append(idle_executors, self._reverse(spawned_rev, M.EmptyList))()

    def _shutdown_idle_parallel_executors(self, idle_executors):
        if M.IdentityCompare(idle_executors, M.EmptyList)() is M.truth_value:
            return
        executor = M.Head(idle_executors)()
        self._retire_parallel_executor(executor, "shutting down idle packet worker ")
        self._shutdown_idle_parallel_executors(M.Tail(idle_executors)())

    def _retire_parallel_executor(self, executor, prefix_text):
        process = self._resident_executor_process(executor)
        task_queue = self._resident_executor_task_queue(executor)
        slot_text = self._nat_text(self._resident_executor_slot(executor))
        if process.is_alive():
            _debug(
                "search-compare: "
                + prefix_text
                + slot_text
                + " pid="
                + str(process.pid)
            )
            task_queue.put(None)
            process.join(0.1)
            if process.is_alive():
                process.terminate()
                process.join()

    def _kill_parallel_worker_entry(self, entry):
        process = self._worker_entry_process(entry)
        if process.is_alive():
            _debug(
                "search-compare: terminating unfinished packet for "
                + SearchModeText(self._worker_entry_mode(entry))()
                + " on resident executor "
                + self._nat_text(self._worker_entry_slot(entry))
                + " pid="
                + str(process.pid)
            )
            process.terminate()
        process.join()

    def _parallel_launch_result_launch(self, result):
        return M.Head(result)()

    def _parallel_launch_result_process(self, result):
        return M.Head(M.Tail(result)())()

    def _parallel_launch_result_queue(self, result):
        return M.Head(M.Tail(M.Tail(result)())())()

    def _dequeue_parallel_worker_launch(self, state, launch_slot, launch_budget):
        (
            mode,
            parent_job,
            search_memo,
            active_before,
            pending_packets,
            pending_packets_count,
            phase,
            completed_packets,
            root_fast_path_result,
            stop_reason,
        ) = self._comparison_state_unpack(state)
        packet_state = M.Head(pending_packets)()
        remaining_packets = M.Tail(pending_packets)()
        step_budget = self._comparison_packet_budget(mode, packet_state)
        branch_serial = self._nat_add_local(
            completed_packets,
            active_before,
        )
        branch_serial = self._succ_nat_local(branch_serial)

        _debug(
            "search-compare: staging resident lease "
            + self._nat_text(launch_slot)
            + "/"
            + self._nat_text(launch_budget)
            + " -> "
            + SearchModeText(mode)()
            + " packet "
            + self._nat_text(branch_serial)
        )

        packet_token = self._succ_nat_local(self._comparison_packet_token)
        self._comparison_packet_token = packet_token
        setup = self._worker_setup(state)
        payload = self._worker_problem_packet(state, packet_state, step_budget, packet_token)

        active_packets = self._succ_nat_local(active_before)
        remaining_count = self._pred_nat_or_zero_local(pending_packets_count)

        next_state = self._comparison_state_update(
            state,
            active_packets=active_packets,
            pending_packets=remaining_packets,
            pending_packets_count=remaining_count,
        )
        launch = SearchWorkerLaunch(
            mode,
            setup,
            payload,
            packet_state,
            launch_slot,
            launch_budget,
            branch_serial,
        )()

        _debug(
            "search-compare: staged "
            + self._nat_text(launch_slot)
            + "/"
            + self._nat_text(launch_budget)
            + " resident leases already; latest="
            + SearchModeText(mode)()
            + " packet "
            + self._nat_text(branch_serial)
        )
        return M.Pair(next_state, M.Pair(launch, M.EmptyList))

    def _collect_parallel_worker_launches(self, mp_context, states, workers, idle_executors):
        worker_budget = self._comparison_live_process_budget(states, workers)
        self._current_worker_process_budget = worker_budget
        current_workers = workers
        current_worker_count = self._worker_entry_count(workers)
        current_states = states
        current_idle_executors = idle_executors
        launched_now = M.Zero
        best_cost = self._comparison_best_finished_attempt_cost(states)

        while M.NatLess(current_worker_count, worker_budget, self.registry)() is M.truth_value:
            state = self._next_dispatchable_state(current_states, best_cost)
            if M.Compare(state, M.EmptyList)() is M.truth_value:
                break
            state = self._comparison_state_without_exhausted_pending_packets(state, best_cost)
            if self._comparison_state_has_dispatchable_work(state, best_cost) is M.false_value:
                break
            launch_slot = self._succ_nat_local(current_worker_count)
            queued = self._dequeue_parallel_worker_launch(state, launch_slot, worker_budget)
            next_state = M.Head(queued)()
            launch = M.Head(M.Tail(queued)())()
            started = self._start_parallel_workers(
                mp_context,
                current_workers,
                current_idle_executors,
                M.Pair(launch, M.EmptyList),
            )
            started_now = M.Head(started)()
            current_idle_executors = M.Head(M.Tail(started)())()
            if M.IdentityCompare(started_now, M.EmptyList)() is M.truth_value:
                mode = SearchWorkerLaunchMode(launch)()
                branch_serial = SearchWorkerLaunchBranchSerial(launch)()
                _debug(
                    "search-compare: resident executor unavailable; leaving "
                    + SearchModeText(mode)()
                    + " packet "
                    + self._nat_text(branch_serial)
                    + " queued for resident retry"
                )
                break
            current_workers = Append(started_now, current_workers)()
            current_worker_count = self._succ_nat_local(current_worker_count)
            launched_now = self._succ_nat_local(launched_now)
            current_states = self._replace_comparison_state(
                current_states,
                self._comparison_state_mode(state),
                next_state,
            )

        return M.Pair(
            current_states,
            M.Pair(
                current_workers,
                M.Pair(current_idle_executors, M.Pair(launched_now, M.EmptyList)),
            ),
        )

    def _start_parallel_workers(self, mp_context, workers, idle_executors, launches):
        if M.IdentityCompare(launches, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(idle_executors, M.EmptyList))

        launched_workers_rev = M.EmptyList
        remaining_launches = launches
        remaining_idle_executors = idle_executors
        resident_total = self._nat_add_local(
            self._worker_entry_count(workers),
            self._idle_executor_count(idle_executors),
        )

        while M.IdentityCompare(remaining_launches, M.EmptyList)() is M.false_value:
            launch = M.Head(remaining_launches)()
            mode = SearchWorkerLaunchMode(launch)()
            branch_serial = SearchWorkerLaunchBranchSerial(launch)()
            if M.IdentityCompare(remaining_idle_executors, M.EmptyList)() is M.truth_value:
                next_slot = self._succ_nat_local(resident_total)
                _debug(
                    "search-compare: spawning resident executor on demand for "
                    + SearchModeText(mode)()
                    + " packet "
                    + self._nat_text(branch_serial)
                )
                try:
                    executor = self._spawn_parallel_executor(mp_context, next_slot)
                except Exception as error:
                    _debug(
                        "search-compare: resident executor spawn unavailable while leasing "
                        + SearchModeText(mode)()
                        + " packet "
                        + self._nat_text(branch_serial)
                        + " ("
                        + str(error)
                        + "); leaving the remaining branch wave queued for retry"
                    )
                    break
                resident_total = next_slot
            else:
                executor = M.Head(remaining_idle_executors)()
                remaining_idle_executors = M.Tail(remaining_idle_executors)()

            packet_state = SearchWorkerLaunchPacketState(launch)()
            launch_slot = SearchWorkerLaunchSlot(launch)()
            launch_budget = SearchWorkerLaunchBudget(launch)()
            launch_setup = SearchWorkerLaunchSetup(launch)()
            launch_payload = SearchWorkerLaunchPayload(launch)()
            launch_baseline = SearchWorkerSetupBaseline(launch_setup)()
            baseline_rewrite_rules = SearchWorkerBaselineRewriteRules(launch_baseline)()
            packet_token = SearchWorkerPacketPacketToken(launch_payload)()
            task_queue = self._resident_executor_task_queue(executor)
            slot_text = self._nat_text(self._resident_executor_slot(executor))
            live_after_lease = self._nat_add_local(
                self._worker_entry_count(workers),
                self._succ_nat_local(self._worker_entry_count(launched_workers_rev)),
            )

            _debug(
                "search-compare: leasing resident executor "
                + slot_text
                + " for "
                + SearchModeText(mode)()
                + " packet "
                + self._nat_text(branch_serial)
                + " ("
                + self._nat_text(launch_slot)
                + "/"
                + self._nat_text(launch_budget)
                + ") live="
                + self._nat_text(live_after_lease)
                + " idle="
                + self._nat_text(self._idle_executor_count(remaining_idle_executors))
            )

            queued_payload = launch_payload
            payload_rewrite_rules = SearchWorkerPacketRewriteRules(launch_payload)()
            send_setup = M.false_value
            if M.TermEqual(self._resident_executor_generation(executor), self._comparison_generation)() is M.false_value:
                send_setup = M.truth_value
            elif M.TermEqual(self._resident_executor_mode(executor), mode)() is M.false_value:
                send_setup = M.truth_value
            elif M.IdentityCompare(payload_rewrite_rules, M.EmptyList)() is M.false_value:
                executor_rewrite_rules = self._resident_executor_rewrite_rules(executor)
                if M.IdentityCompare(executor_rewrite_rules, M.EmptyList)() is M.truth_value:
                    send_setup = M.truth_value
                elif M.TermEqual(executor_rewrite_rules, payload_rewrite_rules)() is M.false_value:
                    send_setup = M.truth_value
            if M.IdentityCompare(send_setup, M.truth_value)() is M.truth_value:
                task_queue.put(launch_setup)
                executor = self._resident_executor_with_baseline(
                    executor,
                    self._comparison_generation,
                    mode,
                    baseline_rewrite_rules,
                )
            if M.IdentityCompare(payload_rewrite_rules, M.EmptyList)() is M.false_value:
                queued_payload = SearchWorkerPacket(
                    SearchWorkerPacketDescriptor(launch_payload)(),
                    SearchWorkerPacketSearchMemo(launch_payload)(),
                    SearchWorkerPacketVisited(launch_payload)(),
                    SearchWorkerPacketTheoremRuleCache(launch_payload)(),
                    M.EmptyList,
                    SearchWorkerPacketStepBudget(launch_payload)(),
                    SearchWorkerPacketDebugTrace(launch_payload)(),
                    SearchWorkerPacketIgnoreRootFastPaths(launch_payload)(),
                    SearchWorkerPacketDiscoveryMode(launch_payload)(),
                    SearchWorkerPacketPacketToken(launch_payload)(),
                    SearchWorkerPacketGeneration(launch_payload)(),
                )()
            launch = SearchWorkerLaunch(
                mode,
                launch_setup,
                queued_payload,
                packet_state,
                launch_slot,
                launch_budget,
                branch_serial,
            )()
            task_queue.put(launch)
            launched_workers_rev = M.Pair(
                self._worker_entry(mode, executor, packet_state, packet_token),
                launched_workers_rev,
            )

            _debug(
                "search-compare: leased "
                + self._nat_text(launch_slot)
                + "/"
                + self._nat_text(launch_budget)
                + " local executors already; latest="
                + SearchModeText(mode)()
                + " packet "
                + self._nat_text(branch_serial)
            )
            remaining_launches = M.Tail(remaining_launches)()

        return M.Pair(
            self._reverse(launched_workers_rev, M.EmptyList),
            M.Pair(remaining_idle_executors, M.EmptyList),
        )

    def _fill_parallel_workers(self, mp_context, idle_executors, states, workers):
        current_states = states
        current_workers = workers
        current_idle_executors = idle_executors
        prior_total_queued = self._comparison_total_queued_packets(current_states)

        if self._comparison_states_need_shared_root_wave(current_states) is M.truth_value:
            current_idle_executors = self._grow_parallel_executor_pool(
                mp_context,
                current_idle_executors,
                current_states,
                current_workers,
            )
        self._comparison_root_wave_idle_executors = current_idle_executors
        current_states = self._comparison_prepare_shared_root_wave(current_states)
        current_idle_executors = self._comparison_root_wave_idle_executors
        best_cost = self._comparison_best_finished_attempt_cost(current_states)

        _debug(
            "search-compare: rechecking fixed mode frontiers for newly packetizable work before refill; "
            + self._comparison_live_process_budget_text(current_states, current_workers)
        )
        current_states = self._comparison_states_enqueue_all_packets(current_states, best_cost, M.truth_value)
        next_total_queued = self._comparison_total_queued_packets(current_states)
        if M.NatLess(prior_total_queued, next_total_queued, self.registry)() is M.truth_value:
            _debug(
                "search-compare: all fixed mode frontiers are packetized; total ready branches="
                + self._nat_text(next_total_queued)
                + "; "
                + self._comparison_live_process_budget_text(current_states, current_workers)
            )

        launchable_budget = self._comparison_live_process_budget(current_states, current_workers)
        launchable_workers = self._worker_entry_count(current_workers)
        if M.NatLess(launchable_workers, launchable_budget, self.registry)() is M.truth_value:
            total_queued = self._comparison_total_queued_packets(current_states)
            launch_now = self._nat_sub_or_zero_local(launchable_budget, launchable_workers)
            remaining_queued = self._nat_sub_or_zero_local(total_queued, launch_now)
            _debug(
                "search-compare: global branch backlog currently has "
                + self._nat_text(total_queued)
                + " ready branches; launching "
                + self._nat_text(launch_now)
                + " resident executors now, "
                + self._nat_text(remaining_queued)
                + " still queued"
            )
            _debug(
                "search-compare: "
                + self._comparison_live_process_budget_text(current_states, current_workers)
                + " for "
                + self._mode_chain_text(self._mode_chain())
            )
            _debug(
                "search-compare: scheduler sees "
                + self._comparison_live_process_budget_text(current_states, current_workers)
                + "; leasing resident workers now"
            )

        queued = self._collect_parallel_worker_launches(mp_context, current_states, current_workers, current_idle_executors)
        current_states = M.Head(queued)()
        current_workers = M.Head(M.Tail(queued)())()
        current_idle_executors = M.Head(M.Tail(M.Tail(queued)())())()
        launched_now = M.Head(M.Tail(M.Tail(M.Tail(queued)())())())()
        if M.NatEq(launched_now, M.Zero, self.registry)() is M.false_value:
            _debug(
                "search-compare: launched "
                + self._nat_text(launched_now)
                + " resident worker leases this cycle; "
                + self._comparison_live_process_budget_text(current_states, current_workers)
            )

        self._current_worker_process_budget = self._comparison_live_process_budget(current_states, current_workers)
        return M.Pair(
            current_states,
            M.Pair(current_workers, M.Pair(current_idle_executors, M.EmptyList)),
        )

    def _first_finished_worker(self, workers, acc):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.Pair(self._reverse(acc, M.EmptyList), M.EmptyList)))
        entry = M.Head(workers)()
        process = self._worker_entry_process(entry)
        result_queue = self._worker_entry_queue(entry)

        try:
            payload = result_queue.get_nowait()
            return M.Pair(
                entry,
                M.Pair(
                    payload,
                    M.Pair(Append(self._reverse(acc, M.EmptyList), M.Tail(workers)())(), M.EmptyList),
                ),
            )
        except queue.Empty:
            if process.is_alive():
                return self._first_finished_worker(M.Tail(workers)(), M.Pair(entry, acc))
            process.join(0.01)
            return M.Pair(
                entry,
                M.Pair(
                    None,
                    M.Pair(Append(self._reverse(acc, M.EmptyList), M.Tail(workers)())(), M.EmptyList),
                ),
            )

    def _terminate_parallel_workers(self, workers):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return
        entry = M.Head(workers)()
        self._kill_parallel_worker_entry(entry)
        self._terminate_parallel_workers(M.Tail(workers)())

    def _terminate_parallel_workers_for_mode(self, mp_context, workers, idle_executors, mode, kept):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return M.Pair(self._reverse(kept, M.EmptyList), M.Pair(idle_executors, M.EmptyList))
        entry = M.Head(workers)()
        if M.IdentityCompare(self._worker_entry_mode(entry), mode)() is M.truth_value:
            self._kill_parallel_worker_entry(entry)
            return self._terminate_parallel_workers_for_mode(mp_context, M.Tail(workers)(), idle_executors, mode, kept)
        return self._terminate_parallel_workers_for_mode(mp_context, M.Tail(workers)(), idle_executors, mode, M.Pair(entry, kept))

    def _terminate_parallel_workers_not_selected(self, mp_context, workers, idle_executors, selected_modes, kept):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return M.Pair(self._reverse(kept, M.EmptyList), M.Pair(idle_executors, M.EmptyList))
        entry = M.Head(workers)()
        if self._mode_selected(selected_modes, self._worker_entry_mode(entry)) is M.false_value:
            self._kill_parallel_worker_entry(entry)
            return self._terminate_parallel_workers_not_selected(mp_context, M.Tail(workers)(), idle_executors, selected_modes, kept)
        return self._terminate_parallel_workers_not_selected(mp_context, M.Tail(workers)(), idle_executors, selected_modes, M.Pair(entry, kept))

    def _requeue_worker_entry_for_pause(self, states, entry):
        mode = self._worker_entry_mode(entry)
        packet_state = self._worker_entry_packet_job(entry)
        prior_state = self._comparison_state_for_mode(states, mode)
        next_states = states
        if M.IdentityCompare(prior_state, M.EmptyList)() is M.false_value:
            if M.IdentityCompare(self._comparison_state_status(prior_state), SearchRunningLabel)() is M.truth_value:
                packet_job = self._comparison_packet_job_for_state(prior_state, packet_state)
                requeued_job = self._merge_compare_jobs(mode, self._comparison_state_job(prior_state), packet_job)
                active_packets = self._pred_nat_or_zero_local(self._comparison_state_active_packets(prior_state))
                next_state = self._comparison_state_update(
                    prior_state,
                    job=requeued_job,
                    active_packets=active_packets,
                )
                next_states = self._replace_comparison_state(states, mode, next_state)
                _debug(
                    "search-compare: requeued unfinished packet for "
                    + SearchModeText(mode)()
                    + " pid="
                    + str(self._worker_entry_process(entry).pid)
                )
        return next_states

    def _requeue_worker_entry_for_retry(self, states, entry):
        mode = self._worker_entry_mode(entry)
        packet_descriptor = self._worker_entry_packet_job(entry)
        prior_state = self._comparison_state_for_mode(states, mode)
        if M.IdentityCompare(prior_state, M.EmptyList)() is M.truth_value:
            return states
        if M.IdentityCompare(self._comparison_state_status(prior_state), SearchRunningLabel)() is M.false_value:
            return states

        active_packets = self._pred_nat_or_zero_local(self._comparison_state_active_packets(prior_state))
        pending_packets = M.Pair(packet_descriptor, self._comparison_state_pending_packets(prior_state))
        pending_packets_count = self._succ_nat_local(self._comparison_state_pending_packets_count(prior_state))
        next_state = self._comparison_state_update(
            prior_state,
            active_packets=active_packets,
            pending_packets=pending_packets,
            pending_packets_count=pending_packets_count,
        )
        _debug(
            "search-compare: requeued rejected "
            + SearchModeText(mode)()
            + " packet for resident retry; mode-active-processes="
            + self._nat_text(active_packets)
            + " mode-queued-packets="
            + self._nat_text(pending_packets_count)
        )
        return self._replace_comparison_state(states, mode, next_state)

    def _requeue_parallel_workers_for_pause(self, states, workers):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return states
        next_states = self._requeue_worker_entry_for_pause(states, M.Head(workers)())
        return self._requeue_parallel_workers_for_pause(next_states, M.Tail(workers)())

    def _signal_parallel_worker_entry(self, entry):
        process = self._worker_entry_process(entry)
        if process.is_alive():
            _debug(
                "search-compare: pause signalling "
                + SearchModeText(self._worker_entry_mode(entry))()
                + " pid="
                + str(process.pid)
            )
            process.terminate()

    def _signal_parallel_workers(self, workers):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return
        self._signal_parallel_worker_entry(M.Head(workers)())
        self._signal_parallel_workers(M.Tail(workers)())

    def _join_parallel_workers_quick(self, workers, timeout_seconds):
        if M.IdentityCompare(workers, M.EmptyList)() is M.truth_value:
            return
        self._worker_entry_process(M.Head(workers)()).join(timeout_seconds)
        self._join_parallel_workers_quick(M.Tail(workers)(), timeout_seconds)

    def _pause_parallel_workers(self, states, workers):
        worker_count = self._worker_entry_count(workers)
        if M.NatEq(worker_count, M.Zero, self.registry)() is M.truth_value:
            return states
        _debug(
            "search-compare: pause requested; reclaiming "
            + self._nat_text(worker_count)
            + " in-flight branch packets"
        )
        next_states = self._requeue_parallel_workers_for_pause(states, workers)
        _debug(
            "search-compare: pause signalling "
            + self._nat_text(worker_count)
            + " worker processes"
        )
        self._signal_parallel_workers(workers)
        self._join_parallel_workers_quick(workers, 0.0)
        _debug("search-compare: pause requeued packets and signalled worker shutdown")
        return next_states

    def _comparison_total_queued_packets(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.Zero
        rest = self._comparison_total_queued_packets(M.Tail(states)())
        return self._nat_add_local(self._comparison_state_pending_packets_count(M.Head(states)()), rest)

    def _comparison_best_finished_attempt_cost(self, states):
        best_attempt = self._best_finished_attempt(states, M.EmptyList)
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        return self._attempt_total_value(best_attempt)

    def _comparison_live_process_budget(self, states, workers):
        active_workers = self._worker_entry_count(workers)
        soft_target = self._nat_add_local(self._comparison_machine_parallelism, self._count_states(states))
        if M.NatLess(soft_target, active_workers, self.registry)() is M.truth_value:
            return active_workers
        return soft_target

    def _comparison_live_process_budget_text(self, states, workers):
        active_workers = self._worker_entry_count(workers)
        queued_packets = self._comparison_total_queued_packets(states)
        soft_target = self._nat_add_local(self._comparison_machine_parallelism, self._count_states(states))
        live_budget = self._comparison_live_process_budget(states, workers)
        return (
            "total-active-processes="
            + self._nat_text(active_workers)
            + " total-queued-packets="
            + self._nat_text(queued_packets)
            + " machine-target="
            + self._nat_text(self._comparison_machine_parallelism)
            + " soft-target="
            + self._nat_text(soft_target)
            + " live-budget="
            + self._nat_text(live_budget)
        )

    def _comparison_total_completed_packets(self, states):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return M.Zero
        rest = self._comparison_total_completed_packets(M.Tail(states)())
        return self._nat_add_local(self._comparison_state_completed_packets(M.Head(states)()), rest)

    def _comparison_eta_text(self, states, workers):
        if self._comparison_prompt_guard is None:
            return "rough eta unknown"
        elapsed_seconds = time.time() - self._comparison_prompt_guard.started_at
        if elapsed_seconds <= 0.0:
            return "rough eta unknown"
        completed_packets = self._comparison_total_completed_packets(states)
        completed_text = self._nat_text(completed_packets)
        try:
            completed_count = float(completed_text)
        except Exception:
            return "rough eta unknown"
        if completed_count <= 0.0:
            active_workers = self._worker_entry_count(workers)
            queued_packets = self._comparison_total_queued_packets(states)
            live_budget = self._nat_add_local(active_workers, queued_packets)
            oldest_entry = self._oldest_active_worker_entry(workers)
            if M.Compare(oldest_entry, M.EmptyList)() is M.false_value:
                oldest_mode = self._worker_entry_mode(oldest_entry)
                oldest_state = self._comparison_packet_state(oldest_mode, self._worker_entry_packet_job(oldest_entry))
                return (
                    "rough eta unavailable before first completion; oldest live packet "
                    + SearchModeText(oldest_mode)()
                    + " has run "
                    + self._seconds_text(self._worker_entry_elapsed_seconds(oldest_entry))
                    + " stage="
                    + self._state_stage_text(oldest_state)
                    + " "
                    + self._state_next_action_text(oldest_state)
                    + "; overall elapsed "
                    + self._seconds_text(elapsed_seconds)
                    + " with "
                    + self._nat_text(active_workers)
                    + " active processes, "
                    + self._nat_text(queued_packets)
                    + " queued packets, live-budget "
                    + self._nat_text(live_budget)
                )
            return (
                "rough eta unavailable before first completion; elapsed "
                + self._seconds_text(elapsed_seconds)
                + " with "
                + self._nat_text(active_workers)
                + " active processes, "
                + self._nat_text(queued_packets)
                + " queued packets, live-budget "
                + self._nat_text(live_budget)
            )
        outstanding_packets = self._comparison_live_process_budget(states, workers)
        outstanding_text = self._nat_text(outstanding_packets)
        try:
            outstanding_count = float(outstanding_text)
        except Exception:
            return "rough eta unknown"
        packet_rate = completed_count / elapsed_seconds
        if packet_rate <= 0.0:
            return "rough eta unknown"
        eta_seconds = outstanding_count / packet_rate
        rate_per_minute = packet_rate * 60.0
        return (
            "rough eta "
            + self._seconds_text(eta_seconds)
            + " at about "
            + "{:.1f}".format(rate_per_minute)
            + " completed-packets/min if the backlog does not widen much"
        )



def sync_from_namespace(namespace):
    for name in (
        "SearchJobLabel",
        "SearchSuccessLabel",
        "SearchRunningLabel",
        "SearchPausedLabel",
        "SearchAbortedByUserLabel",
        "SearchWorkerReadyLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonExecutorMixin")]
