#!/usr/bin/env python3
"""Run named production tests through the real Test harness, nothing else.

Registers ONLY the requested test names (from cat_theo_machine.testsuite)
with the same _register_test call shape the default installation uses, then
runs them through the machine's RunTests/TestResultsReport — the same code
path the sharded suite uses. No shard install, no other tests.

Usage (from /home/user):
  python3 cat_theo_machine/tools/agent_workers/focused_repro.py [--packs] [--file NAMES_FILE] <test_name>...
"""
import sys
import time

sys.path.insert(0, "/home/user")

# explicit name -> class map, extracted mechanically from the registration
# block of testsuite.py (no heuristics, no getattr)
TEST_CLASSES = {
    "compare_search_modes_batched_wave_matches_sequential_success_test": "CompareSearchModesBatchedWaveMatchesSequentialSuccessTest",
    "compare_search_modes_batches_large_returned_ready_packet_wave_test": "CompareSearchModesBatchesLargeReturnedReadyPacketWaveTest",
    "compare_search_modes_builds_deep_root_wave_shards_without_recursion_test": "CompareSearchModesBuildsDeepRootWaveShardsWithoutRecursionTest",
    "compare_search_modes_console_disabled_skips_approval_replay_prompt_test": "CompareSearchModesConsoleDisabledSkipsApprovalReplayPromptTest",
    "compare_search_modes_decode_missing_payload_uses_expected_token_test": "CompareSearchModesDecodeMissingPayloadUsesExpectedTokenTest",
    "compare_search_modes_drops_exhausted_pending_packets_test": "CompareSearchModesDropsExhaustedPendingPacketsTest",
    "compare_search_modes_empty_cursor_theorem_fanout_seeds_generated_tree_test": "CompareSearchModesEmptyCursorTheoremFanoutSeedsGeneratedTreeTest",
    "compare_search_modes_empty_cursor_theorem_fanout_test": "CompareSearchModesEmptyCursorTheoremFanoutTest",
    "compare_search_modes_empty_ready_result_refills_job_frontier_test": "CompareSearchModesEmptyReadyResultRefillsJobFrontierTest",
    "compare_search_modes_enqueue_all_packets_after_exhausted_backlog_test": "CompareSearchModesEnqueueAllPacketsAfterExhaustedBacklogTest",
    "compare_search_modes_fallback_winner_uses_recorded_performance_ordering_test": "CompareSearchModesFallbackWinnerUsesRecordedPerformanceOrderingTest",
    "compare_search_modes_fill_warms_resident_pool_before_root_wave_test": "CompareSearchModesFillWarmsResidentPoolBeforeRootWaveTest",
    "compare_search_modes_finds_reusable_worker_snapshot_dir_test": "CompareSearchModesFindsReusableWorkerSnapshotDirTest",
    "compare_search_modes_fresh_root_jobs_packetize_whole_state_test": "CompareSearchModesFreshRootJobsPacketizeWholeStateTest",
    "compare_search_modes_ignores_mismatched_packet_token_result_test": "CompareSearchModesIgnoresMismatchedPacketTokenResultTest",
    "compare_search_modes_ignores_missing_packet_token_result_test": "CompareSearchModesIgnoresMissingPacketTokenResultTest",
    "compare_search_modes_ignores_stopped_mode_result_test": "CompareSearchModesIgnoresStoppedModeResultTest",
    "compare_search_modes_integrates_returned_ready_packets_test": "CompareSearchModesIntegratesReturnedReadyPacketsTest",
    "compare_search_modes_live_budget_uses_soft_window_test": "CompareSearchModesLiveBudgetUsesSoftWindowTest",
    "compare_search_modes_merges_packet_job_test": "CompareSearchModesMergesPacketJobTest",
    "compare_search_modes_missing_payload_retry_requeues_original_packet_test": "CompareSearchModesMissingPayloadRetryRequeuesOriginalPacketTest",
    "compare_search_modes_packet_budget_uses_quantum_test": "CompareSearchModesPacketBudgetUsesQuantumTest",
    "compare_search_modes_packet_budget_zero_beam_uses_packet_width_fallback_test": "CompareSearchModesPacketBudgetZeroBeamUsesPacketWidthFallbackTest",
    "compare_search_modes_packetizes_non_root_frontier_test": "CompareSearchModesPacketizesNonRootFrontierTest",
    "compare_search_modes_packetizes_wide_frontier_in_chunks_test": "CompareSearchModesPacketizesWideFrontierInChunksTest",
    "compare_search_modes_pause_requeues_active_packet_into_job_test": "CompareSearchModesPauseRequeuesActivePacketIntoJobTest",
    "compare_search_modes_pause_state_preserves_backlog_test": "CompareSearchModesPauseStatePreservesBacklogTest",
    "compare_search_modes_prunes_packets_after_best_attempt_test": "CompareSearchModesPrunesPacketsAfterBestAttemptTest",
    "compare_search_modes_refill_widens_pending_packets_test": "CompareSearchModesRefillWidensPendingPacketsTest",
    "compare_search_modes_resident_executor_ready_handshake_test": "CompareSearchModesResidentExecutorReadyHandshakeTest",
    "compare_search_modes_resident_executor_refreshes_baseline_on_generation_change_test": "CompareSearchModesResidentExecutorRefreshesBaselineOnGenerationChangeTest",
    "compare_search_modes_resident_unavailable_leaves_packet_queued_test": "CompareSearchModesResidentUnavailableLeavesPacketQueuedTest",
    "compare_search_modes_returned_ready_overreported_count_keeps_packet_shape_test": "CompareSearchModesReturnedReadyOverreportedCountKeepsPacketShapeTest",
    "compare_search_modes_returned_ready_packet_count_follows_packet_shape_test": "CompareSearchModesReturnedReadyPacketCountFollowsPacketShapeTest",
    "compare_search_modes_rewrite_fanout_produces_one_rule_packets_test": "CompareSearchModesRewriteFanoutProducesOneRulePacketsTest",
    "compare_search_modes_root_wave_records_empty_expansion_test": "CompareSearchModesRootWaveRecordsEmptyExpansionTest",
    "compare_search_modes_root_wave_replaces_exhausted_resident_test": "CompareSearchModesRootWaveReplacesExhaustedResidentTest",
    "compare_search_modes_root_wave_requires_resident_executor_test": "CompareSearchModesRootWaveRequiresResidentExecutorTest",
    "compare_search_modes_root_wave_retries_failed_shard_on_resident_test": "CompareSearchModesRootWaveRetriesFailedShardOnResidentTest",
    "compare_search_modes_root_wave_seeds_single_rewrite_handoff_test": "CompareSearchModesRootWaveSeedsSingleRewriteHandoffTest",
    "compare_search_modes_root_wave_uses_resident_executor_test": "CompareSearchModesRootWaveUsesResidentExecutorTest",
    "compare_search_modes_skips_root_cache_during_raw_benchmark_test": "CompareSearchModesSkipsRootCacheDuringRawBenchmarkTest",
    "compare_search_modes_skips_shared_root_schema_during_raw_benchmark_test": "CompareSearchModesSkipsSharedRootSchemaDuringRawBenchmarkTest",
    "compare_search_modes_stale_token_retry_requeues_original_packet_test": "CompareSearchModesStaleTokenRetryRequeuesOriginalPacketTest",
    "compare_search_modes_stop_mode_marks_only_requested_mode_test": "CompareSearchModesStopModeMarksOnlyRequestedModeTest",
    "compare_search_modes_stop_outcome_clears_pending_packet_count_test": "CompareSearchModesStopOutcomeClearsPendingPacketCountTest",
    "compare_search_modes_stopped_state_does_not_enqueue_job_frontier_test": "CompareSearchModesStoppedStateDoesNotEnqueueJobFrontierTest",
    "compare_search_modes_stores_derivation_backed_attempt_test": "CompareSearchModesStoresDerivationBackedAttemptTest",
    "compare_search_modes_success_clears_pending_packets_test": "CompareSearchModesSuccessClearsPendingPacketsTest",
    "compare_search_modes_theorem_fanout_adds_single_rewrite_handoff_test": "CompareSearchModesTheoremFanoutAddsSingleRewriteHandoffTest",
    "compare_search_modes_theorem_fanout_preserves_generated_test": "CompareSearchModesTheoremFanoutPreservesGeneratedTest",
    "compare_search_modes_worker_entry_tracks_packet_job_test": "CompareSearchModesWorkerEntryTracksPacketJobTest",
    "search_worker_baseline_uses_grouped_problem_block_test": "SearchWorkerBaselineUsesGroupedProblemBlockTest",
    "search_worker_filters_seeded_theorem_continuation_test": "SearchWorkerFiltersSeededTheoremContinuationTest",
    "search_worker_launch_pickle_roundtrip_test": "SearchWorkerLaunchPickleRoundtripTest",
    "search_worker_launch_uses_grouped_dispatch_test": "SearchWorkerLaunchUsesGroupedDispatchTest",
    "search_worker_packet_delta_uses_resident_baseline_test": "SearchWorkerPacketDeltaUsesResidentBaselineTest",
    "search_worker_packet_uses_grouped_blocks_test": "SearchWorkerPacketUsesGroupedBlocksTest",
    "search_worker_result_pickle_roundtrip_test": "SearchWorkerResultPickleRoundtripTest",
    "search_worker_resume_derivation_missing_plan_raises_runtime_error_test": "SearchWorkerResumeDerivationMissingPlanRaisesRuntimeErrorTest",
    "search_worker_resume_state_restores_saved_plan_test": "SearchWorkerResumeStateRestoresSavedPlanTest",
    "search_worker_snapshot_boot_with_runtime_namespace_test": "SearchWorkerSnapshotBootWithRuntimeNamespaceTest",
    "learned_memory_checkpoint_test": "LearnedMemoryCheckpointTest",
    "dependency_graph_checkpoint_test": "DependencyGraphCheckpointTest",
    "snapshot_save_timeout_preserves_existing_snapshot_test": "SnapshotSaveTimeoutPreservesExistingSnapshotTest",
    "snapshot_preserves_machine_edge_structure_test": "SnapshotPreservesMachineEdgeStructureTest",
    "snapshot_preserves_constructor_labels_and_chars_test": "SnapshotPreservesConstructorLabelsAndCharsTest",
    "snapshot_preserves_rule_edge_inputs_test": "SnapshotPreservesRuleEdgeInputsTest",
    "snapshot_host_class_refusal_test": "SnapshotHostClassRefusalTest",
    "snapshot_restore_rebinds_constructor_class_test": "SnapshotRestoreRebindsConstructorClassTest",
}

def main():
    import cat_theo_machine.machine as M
    import cat_theo_machine.graph as Gmod
    import cat_theo_machine.proof as Pmod
    import cat_theo_machine.testsuite as T
    from cat_theo_machine.runtime import make_fresh_runtime, boot_from_packs

    names = sys.argv[1:]
    use_packs = False
    if names and names[0] == "--packs":
        use_packs = True
        names = names[1:]
    if names and names[0] == "--file":
        with open(names[1]) as handle:
            names = [line.strip() for line in handle if line.strip()]
    log = []
    log.append("FOCUSED REPRO utc %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    log.append("names: %d, packs: %s" % (len(names), "yes" if use_packs else "no"))

    if use_packs:
        # some family tests reference theorem-pack vocabulary; the sharded
        # production suite always boots packs, so reproduce that context
        from cat_theo_machine.main import PACK_PATHS, _runtime_namespace
        Pmod.SetDebugTrace(M.false_value)()
        runtime, _packs = boot_from_packs(PACK_PATHS, _runtime_namespace())
        runtime.graph._search_disable_console = M.truth_value
    else:
        runtime = make_fresh_runtime()
    graph = runtime.graph
    empty = M.EmptyList

    registered = 0
    for name in names:
        cls_name = TEST_CLASSES.get(name)
        if cls_name is None:
            log.append("REGISTER-SKIP %s: not in harness map" % name)
            continue
        cls = T.__dict__.get(cls_name)
        if cls is None:
            log.append("REGISTER-SKIP %s: class %s not found in testsuite" % (name, cls_name))
            continue
        edge = cls(graph)
        T._register_test(graph, name, empty, edge, M.truth_value)
        registered += 1
        log.append("registered %s (%s)" % (name, cls_name))
    log.append("registered %d of %d" % (registered, len(names)))

    t0 = time.time()
    report = runtime.run_tests_report()
    log.append("elapsed %.2fs" % (time.time() - t0))
    log.append("TEST_REPORT_BEGIN")
    log.append(report)
    log.append("TEST_REPORT_END")
    text = "\n".join(log)
    print(text, flush=True)
    if report == "All the tests have passed.":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
