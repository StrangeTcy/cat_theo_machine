from __future__ import annotations

import gc
import json
import multiprocessing
import os
import pickle
import sys
import tempfile
import threading
import time
import gmpy2

from . import machine as M
from . import context as Ctxmod
from . import constructors as C
from . import wire as Wiremod
from . import core as Core
from . import graph as Gmod
from . import gmprep as Gmpmod
from . import heuristics as Hmod
from . import labels as Lmod
from . import matching as Xmod
from . import prettyprinting as Prettymod
from . import proof as Pmod
from . import rewrite_rules as Rmod
from . import search as Smod
from . import theorem_rules as Tmod
from . import trees as T

SNAPSHOT_CAPTURE_PROGRESS_SECONDS = 2.0
SNAPSHOT_DEADLINE_OBJECT_INTERVAL = 128


class SnapshotSaveTimeout(RuntimeError):
    def __init__(
        self,
        timeout_seconds,
        phase,
        elapsed_seconds,
        discovered_count,
        encoded_count,
        temporary_path,
        temporary_size,
    ):
        self.timeout_seconds = timeout_seconds
        self.phase = phase
        self.elapsed_seconds = elapsed_seconds
        self.discovered_count = discovered_count
        self.encoded_count = encoded_count
        self.temporary_path = temporary_path
        self.temporary_size = temporary_size
        message = (
            "snapshot save FAILED: exceeded "
            + format(timeout_seconds, ".0f")
            + " seconds during "
            + phase
            + " (elapsed "
            + format(elapsed_seconds, ".1f")
            + "s; objects discovered="
            + str(discovered_count)
            + "; encoded="
            + str(encoded_count)
        )
        if temporary_path is not None:
            message = message + "; temporary file=" + temporary_path
            if temporary_size is not None:
                message = message + " (" + str(temporary_size) + " bytes)"
        message = message + ")"
        super().__init__(message)


class SnapshotSaveDeadline:
    def __init__(self, timeout_seconds):
        self.timeout_seconds = timeout_seconds
        self.started_at = time.monotonic()
        self.expires_at = self.started_at + timeout_seconds
        self.phase = "namespace synchronization"
        self.discovered_count = 0
        self.encoded_count = 0
        self.temporary_path = None
        self.state = "active"
        self.timeout_error = None
        self.lock = threading.Lock()
        self.watchdog = threading.Timer(timeout_seconds, self.expire)
        self.watchdog.daemon = True
        self.watchdog.start()

    def set_phase(self, phase):
        with self.lock:
            self.phase = phase

    def set_counts(self, discovered_count, encoded_count):
        with self.lock:
            self.discovered_count = discovered_count
            self.encoded_count = encoded_count

    def set_temporary_path(self, temporary_path):
        with self.lock:
            self.temporary_path = temporary_path

    def expire(self):
        with self.lock:
            if self.state != "active":
                return
            temporary_size = None
            if self.temporary_path is not None:
                try:
                    temporary_size = os.path.getsize(self.temporary_path)
                except OSError:
                    temporary_size = None
            if self.temporary_path is not None:
                quarantine_path = (
                    self.temporary_path
                    + ".timed-out-"
                    + str(int(time.monotonic() * 1000000))
                )
                try:
                    os.replace(self.temporary_path, quarantine_path)
                    self.temporary_path = quarantine_path
                except OSError:
                    pass
            self.timeout_error = SnapshotSaveTimeout(
                self.timeout_seconds,
                self.phase,
                time.monotonic() - self.started_at,
                self.discovered_count,
                self.encoded_count,
                self.temporary_path,
                temporary_size,
            )
            self.state = "expired"
            print(str(self.timeout_error), flush=True)

    def require_remaining(self, phase):
        timeout_reached = None
        with self.lock:
            self.phase = phase
            if self.state == "expired":
                raise self.timeout_error
            if time.monotonic() >= self.expires_at:
                timeout_reached = "yes"
            else:
                return self.expires_at - time.monotonic()
        if timeout_reached is not None:
            self.expire()
            raise self.timeout_error

    def require_capture_progress(self, phase, discovered_count, encoded_count):
        timeout_reached = None
        with self.lock:
            self.phase = phase
            self.discovered_count = discovered_count
            self.encoded_count = encoded_count
            if self.state == "expired":
                raise self.timeout_error
            if time.monotonic() >= self.expires_at:
                timeout_reached = "yes"
            else:
                return self.expires_at - time.monotonic()
        if timeout_reached is not None:
            self.expire()
            raise self.timeout_error

    def replace_temporary_snapshot(self, path):
        timeout_reached = None
        with self.lock:
            if self.state == "expired":
                raise self.timeout_error
            if time.monotonic() >= self.expires_at:
                timeout_reached = "yes"
            else:
                os.replace(self.temporary_path, path)
                self.temporary_path = None
                self.state = "replaced"
        if timeout_reached is not None:
            self.expire()
            raise self.timeout_error

    def discard_temporary_output(self):
        with self.lock:
            if self.temporary_path is None:
                return
            try:
                os.remove(self.temporary_path)
                print(
                    "snapshot save: removed incomplete temporary output "
                    + self.temporary_path,
                    flush=True,
                )
                self.temporary_path = None
            except OSError:
                pass

    def close(self):
        with self.lock:
            if self.state == "active":
                self.state = "completed"
        self.watchdog.cancel()


SNAPSHOT_SYMBOL_NAMES = [
    "EmptyList",
    "Zero",
    "truth_value",
    "false_value",
    "VarTag",
    "TreeLabel",
    "ZeroLabel",
    "SuccLabel",
    "PairLabel",
    "ThingyLabel",
    "HypergraphLabel",
    "TestLabel",
    "TestOKLabel",
    "TestFailLabel",
    "TestNameLabel",
    "SequenceLabel",
    "LimitLabel",
    "IsCauchyLabel",
    "IsRealLabel",
    "DFSLabel",
    "BFSLabel",
    "BeamLabel",
    "AStarLabel",
    "KnowledgeLabel",
    "LimitLabel",
    "MachineContextLabel",
    "ContextSearchComparisonJobsLabel",
    "ContextSearchJobsLabel",
    "ContextSearchMemoLabel",
    "ContextNatValueIndexLabel",
    "ContextDependencyRequestsLabel",
    "ContextDependencyGraphLabel",
    "ContextGeneratorMetricsLabel",
    "ContextLastProofLabel",
    "ContextResearchResidualsLabel",
    "ContextProvenanceMapLabel",
    "ContextGeneratorPolicyLabel",
    "ContextLastResidualsLabel",
    "ContextCounterfactualResultsLabel",
    "ContextResearchModeLabel",
    "DependencyRequestLabel",
    "GoalDependsOnDependencyLabel",
    "DependencyDependsOnDependencyLabel",
    "GoalResidualLabel",
    "BlockingConditionLabel",
    "BridgePlanLabel",
    "CounterfactualEvidenceLabel",
    "DependencyStatusLabel",
    "ProvenanceMapLabel",
    "GeneratorMetricsLabel",
    "GeneratorPolicyLabel",
    "ResearchModeLabel",
    "DependencyGraphLabel",
    "ResidualStateLabel",
    "SearchCostBeforeLabel",
    "SearchCostAfterLabel",
    "NewlyEnabledFiringsLabel",
    "RemovedObligationsLabel",
    "NewObligationsLabel",
    "GoalClosedLabel",
    "ProvenanceLabel",
    "DomainAxiomLabel",
    "LibraryTheoremLabel",
    "HumanSuppliedTrustedTheoremLabel",
    "PrewrittenProofLadderLabel",
    "DerivationCacheHitLabel",
    "SchemaReplayLabel",
    "SearchDerivedLabel",
    "InventedLemmaLabel",
    "InvariantLabel",
    "InventedObjectLabel",
    "InventedTransformationLabel",
    "CounterexampleLabel",
    "FailureLabel",
    "DependencyRequestProvenanceLabel",
    "PendingStatusLabel",
    "ApprovedStatusLabel",
    "RejectedStatusLabel",
    "RefinedStatusLabel",
    "TheoremKindLabel",
    "ObjectKindLabel",
    "RepresentationKindLabel",
    "TransformationKindLabel",
    "TacticKindLabel",
    "DomainPropertyKindLabel",
    "ZeroSuccessorResidualLabel",
    "MissingPremiseFailureLabel",
    "InterventionEpisodeLabel",
    "FormalRuleLabel",
    "PolicyPredictionLabel",
    "DependencySuppliedByTheoremLabel",
    "DependencyUnlockedResidualLabel",
    "ObservedMissingPremiseLabel",
    "SpeculativeDependencyLabel",
    "HumanSuppliedStrategyPriorLabel",
    "DemonstratedUsefulDependencyLabel",
    "LearnedDependencyPolicyLabel",
    "HumanSuppliedTrustedTheoremWithoutUnlockLabel",
    "AttemptedRuleLabel",
    "AlphaPlaceholderLabel",
    "NoApplicableRuleLabel",
    "PatternMatchFailureLabel",
    "ObligationFailureLabel",
    "UncharacterizedStallLabel",
    "ParentGoalLabel",
    "ResidualsLabel",
    "FormalStatementLabel",
    "AssumptionsLabel",
    "DependencyIdLabel",
    "GeneratorIdLabel",
    "GeneratorStatsLabel",
    "ProposedCountLabel",
    "ApprovedCountLabel",
    "RejectedCountLabel",
    "UsefulCountLabel",
    "UsedCountLabel",
    "MeanCostReductionLabel",
    "ReuseCountLabel",
    "LastProofLabel",
    "LastResidualsLabel",
    "CounterfactualResultLabel",
    "FiniteLabel",
    "TotalMapLabel",
    "CardinalityLabel",
    "NatLessLabel",
    "InLabel",
    "NonEmptyLabel",
    "AttainsLabel",
    "ExtremalAtLabel",
    "VariationLabel",
    "BetterLabel",
    "ExistsLabel",
    "NotLabel",
    "ContradictionLabel",
    "CollisionLabel",
    "ExtremalLabel",
    "SymmetryLabel",
    "PigeonholeLabel",
    "DivideLabel",
    "BijectionLabel",
    "DoubleCountLabel",
    "ExtremalMinLabel",
    "ExtremalMaxLabel",
    "PlannerAlternativeLabel",
    "ProofCostLabel",
    "NewtonErrorIdentityLabel",
    "NewtonErrorShrinksLabel",
    "NewtonPositiveLabel",
    "NewtonStepTermLabel",
    "RealNumLabel",
    "RewriteDFSLabel",
    "GoalHeadOrderLabel",
    "SearchComparisonLabel",
    "SearchComparisonJobLabel",
    "SearchComparisonJobProblemLabel",
    "SearchComparisonJobRuntimeLabel",
    "SearchComparisonSummaryLabel",
    "SearchSignatureLabel",
    "SearchAttemptLabel",
    "HeuristicPerformanceLabel",
    "SearchCostLabel",
    "SearchSuccessLabel",
    "SearchFailureLabel",
    "SearchTimedOutLabel",
    "SearchAbortedByUserLabel",
    "SearchJobLabel",
    "SearchJobProgressLabel",
    "SearchJobStoresLabel",
    "SearchPairKeyLabel",
    "SearchPausedLabel",
    "SearchCtorKeyLabel",
    "ExactAtomKeyLabel",
    "ExactPairKeyLabel",
    "ExactCtorKeyLabel",
    "IndexAtomKeyLabel",
    "IndexPairKeyLabel",
    "IndexCtorKeyLabel",
    "TreePairKeyLabel",
    "TreeCtorKeyLabel",
    "TreeBucketLabel",
    "TreeBucketEntryLabel",
    "TreePatriciaTokenLabel",
    "TreePatriciaPairTokenLabel",
    "TreePatriciaStopTokenLabel",
    "TreePatriciaLeafLabel",
    "TreePatriciaBranchLabel",
    "TreePatriciaChoiceLabel",
    "SearchRootFastPathPhaseLabel",
    "SearchPacketSearchPhaseLabel",
    "SearchNoRootFastPathLabel",
    "SearchRootCacheResultLabel",
    "SearchRootSchemaResultLabel",
    "SearchRootGoalResultLabel",
    "SearchRootImmediateResultLabel",
    "SearchRootRulePacketLabel",
    "SearchRootWaveShardLaunchLabel",
    "SearchFrontierStatePacketLabel",
    "SearchWorkerBaselineLabel",
    "SearchWorkerBaselineProblemLabel",
    "SearchWorkerSetupLabel",
    "SearchWorkerReadyLabel",
    "SearchWorkerPacketLabel",
    "SearchWorkerPacketStoresLabel",
    "SearchWorkerPacketControlsLabel",
    "SearchWorkerStandalonePacketLabel",
    "SearchWorkerLaunchDispatchLabel",
    "SearchWorkerMetricsLabel",
    "SearchWorkerPayloadLabel",
    "SearchMatchAlternativesCursorLabel",
    "SearchMatchCursorLabel",
    "SearchRewriteCursorLabel",
    "SearchRewritePathFrameLabel",
    "SearchRewriteRuleBundleLabel",
    "SearchRunningLabel",
    "SearchStateLabel",
    "SearchTheoremCursorLabel",
    "SearchPatriciaTokenLabel",
    "SearchPatriciaPairTokenLabel",
    "SearchPatriciaStopTokenLabel",
    "SearchPatriciaLeafLabel",
    "SearchPatriciaBranchLabel",
    "SearchPatriciaChoiceLabel",
    "SequenceLabel",
    "SqrtLabel",
    "SqrtSeqCauchyLabel",
    "SqrtSeqTermLabel",
    "StepLabel",
    "SuccLabel",
    "TestFailLabel",
    "TestLabel",
    "TestNameLabel",
    "TestOKLabel",
    "TheoremActionLabel",
    "ThingyLabel",
    "TotalCostLabel",
    "TreeLabel",
    "WholeLabel",
    "IncreasingLabel",
    "DecreasingLabel",
    "BoundedAboveLabel",
    "BoundedBelowLabel",
    "ConvergesLabel",
    "GapContractsLabel",
    "LimitValueLabel",
    "MoveErasesLabel",
    "TerminalLabel",
    "BoardSumObservableLabel",
    "BoardSumLabel",
    "ParityLabel",
    "IsEvenLabel",
    "AbsDiffLabel",
    "MinLabel",
    "InitialBoardLabel",
    "FinalNumberLabel",
    "BlackboardProblemLabel",
    "OddLabel",
    "EvenLabel",
    "FractionLabel",
    "ExprAddLabel",
    "ExprMulLabel",
    "ExprFracLabel",
    "ExprDivLabel",
    "ExprPowLabel",
    "ExprIntLabel",
    "ExprNegLabel",
    "ExprEqLabel",
    "ExprLtLabel",
    "RewriteActionLabel",
    "DerivationLabel",
    "InsertionOrderLabel",
    "ContextConstructorsLabel",
    "ContextNodesLabel",
    "ContextEdgesLabel",
    "ContextTestsLabel",
    "ContextTestResultsLabel",
    "ContextAllRulesLabel",
    "ContextNextRuleIndexLabel",
    "ContextRuleOrderLabel",
    "ContextDerivationsLabel",
    "ContextDerivationSchemataLabel",
    "ContextSearchHistoryLabel",
    "ContextSearchComparisonsLabel",
    "PositiveLabel",
    "NonNegativeLabel",
    "GeometryFactLabel",
    "PolygonLabel",
    "EdgesLabel",
    "VerticesLabel",
    "TriangleLabel",
    "GivenLabel",
    "NeedLabel",
    "ParameterLabel",
    "SolvedLabel",
    "AreaLabel",
    "SideLengthsLabel",
    "AnglesLabel",
    "LengthLabel",
    "FirstAngleLabel",
    "FirstEdgeLabel",
    "SecondEdgeLabel",
    "ThirdEdgeLabel",
    "SecondAngleLabel",
    "ThirdAngleLabel",
    "CommonDifferenceLabel",
    "SineLabel",
    "CosineLabel",
    "SineRuleAvailableLabel",
    "CosineRuleAvailableLabel",
    "AreaFormulaAvailableLabel",
    "HeronFormulaAvailableLabel",
    "TriangleInequalityAvailableLabel",
    "PhysicalConstraintsKnownLabel",
    "EvaluateProblemLabel",
    "AlgebraicApproachLabel",
    "ArithmeticProgressionLabel",
    "CommonDifferenceGivenLabel",
    "CommonDifferenceParameterLabel",
    "SymmetricProgressionNotationLabel",
    "MiddleTermAverageLabel",
    "TaoProblem11TriangleLabel",
    "LessonLabel",
    "EntryLabel",
    "GroundedExampleLabel",
    "SourceLabel",
    "SurfaceLabel",
    "MathematicsLabel",
    "HistoryLabel",
    "ProblemLabel",
    "HintLabel",
    "UsesStrategyLabel",
    "DerivationFragmentLabel",
    "GoalLabel",
    "ClaimsLabel",
    "SupportsLabel",
    "HistoricalContradictsLabel",
    "OccursOnLabel",
    "BeforeLabel",
    "CausesLabel",
    "ParticipatesInLabel",
    "OccursAtLabel",
    "ClaimStoreLabel",
    "CorrespondenceLawLabel",
    "ZeroLabel",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
]


def _restore_constructor_registry_shard_worker(snapshot_path, shard_index, shard_count, output_path):
    """Spawn-safe worker for restoring a shard of constructor_registry.

    Must be module-level so Windows multiprocessing "spawn" can import it.
    """

    def _record_ref_id(field):
        if field.get("tag") != "ref":
            return None
        return field.get("id")

    def _pair_record(records_by_id, obj_id):
        record = records_by_id.get(obj_id)
        if record is None:
            return None
        if "head" in record and "tail" in record:
            return record
        if "value" in record:
            ref_id = _record_ref_id(record.get("value"))
            if ref_id is None:
                return None
            ref_record = records_by_id.get(ref_id)
            if ref_record is None:
                return None
            if "head" in ref_record and "tail" in ref_record:
                return ref_record
        return None

    def _pair_head_id(records_by_id, pair_id):
        record = _pair_record(records_by_id, pair_id)
        if record is None:
            return None
        return _record_ref_id(record.get("head"))

    def _pair_tail_id(records_by_id, pair_id):
        record = _pair_record(records_by_id, pair_id)
        if record is None:
            return None
        return _record_ref_id(record.get("tail"))

    def _atom_value_id(records_by_id, atom_id):
        record = records_by_id.get(atom_id)
        if record is None:
            return None
        if "value" not in record:
            return None
        return _record_ref_id(record.get("value"))

    def _tree_root_id(records_by_id, tree_id, empty_id, tree_label_id):
        if tree_id is None or tree_id == empty_id:
            return empty_id
        payload_id = _atom_value_id(records_by_id, tree_id)
        if payload_id is None:
            return empty_id
        payload_head_id = _pair_head_id(records_by_id, payload_id)
        if payload_head_id == tree_label_id:
            payload_tail_id = _pair_tail_id(records_by_id, payload_id)
            if payload_tail_id is None:
                return empty_id
            return _pair_head_id(records_by_id, payload_tail_id)
        return payload_head_id

    def _iter_tree_node_items_from_records(records_by_id, node_id, empty_id):
        current = node_id
        stack = []

        while current is not None or stack:
            while current is not None and current != empty_id:
                stack.append(current)
                payload_id = _atom_value_id(records_by_id, current)
                if payload_id is None:
                    current = empty_id
                    break
                fact_tail_id = _pair_tail_id(records_by_id, payload_id)
                if fact_tail_id is None:
                    current = empty_id
                    break
                branches_id = _pair_tail_id(records_by_id, fact_tail_id)
                if branches_id is None:
                    current = empty_id
                    break
                current = _pair_head_id(records_by_id, branches_id)

            if not stack:
                return

            node = stack.pop()
            payload_id = _atom_value_id(records_by_id, node)
            if payload_id is None:
                current = empty_id
                continue

            key_id = _pair_head_id(records_by_id, payload_id)
            fact_tail_id = _pair_tail_id(records_by_id, payload_id)
            if fact_tail_id is None:
                current = empty_id
                continue

            fact_id = _pair_head_id(records_by_id, fact_tail_id)
            if key_id is not None and fact_id is not None:
                yield (key_id, fact_id)

            branches_id = _pair_tail_id(records_by_id, fact_tail_id)
            if branches_id is None:
                current = empty_id
                continue
            right_pair_id = _pair_tail_id(records_by_id, branches_id)
            if right_pair_id is None:
                current = empty_id
                continue
            current = _pair_head_id(records_by_id, right_pair_id)

    try:
        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        empty_id = snapshot["symbols"]["EmptyList"]
        tree_label_id = snapshot["symbols"].get("TreeLabel")
        ctor_tree_id = snapshot["roots"]["constructor_registry"]

        records_by_id = {record["id"]: record for record in snapshot["objects"]}
        root_id = _tree_root_id(records_by_id, ctor_tree_id, empty_id, tree_label_id)

        items = ()
        for key_id, fact_id in _iter_tree_node_items_from_records(records_by_id, root_id, empty_id):
            if (key_id % shard_count) == shard_index:
                items = items + ((key_id, fact_id),)

        temp_path = output_path + ".tmp"
        with open(temp_path, "wb") as f:
            pickle.dump(("ok", items), f)
        os.replace(temp_path, output_path)
    except Exception as exc:
        temp_path = output_path + ".tmp"
        with open(temp_path, "wb") as f:
            pickle.dump(("err", str(exc)), f)
        os.replace(temp_path, output_path)


class SnapshotState:
    def __init__(
        self,
        roots,
        symbols,
        root_ids,
        symbol_ids,
        id_to_obj,
        records,
        needs_upgrade,
        canonical_nats=None,
    ):
        self.roots = roots
        self.symbols = symbols
        self.root_ids = root_ids
        self.symbol_ids = symbol_ids
        self.id_to_obj = id_to_obj
        self.records = records
        self.needs_upgrade = needs_upgrade
        self.upgrade_roots = ()
        # record id -> (canonical key, symbol name or None), carried over from
        # capture, where "was this object a canonical Nat" is still answerable.
        self.canonical_nats = canonical_nats if canonical_nats is not None else {}


class SnapshotCodec:
    ROOT_NAMES = [
        "constructor_registry",
        "all_rules",
        "rule_order",
        "derivations",
        "derivation_schemata",
        "search_history",
        "search_comparisons",
        "search_comparison_jobs",
        "search_jobs",
        "search_memo",
        "nat_value_index",
        "dependency_requests",
        "dependency_graph",
        "generator_metrics",
        "last_proof",
        "research_residuals",
        "provenance_map",
        "generator_policy",
        "last_residuals",
        "counterfactual_results",
        "research_mode",
        "research_attempts",
        "intervention_episodes",
        "dependency_policies",
    ]

    def __init__(self, namespace, symbol_names=None):
        self.namespace = namespace
        self.symbol_names = symbol_names if symbol_names is not None else SNAPSHOT_SYMBOL_NAMES
        self.object_id_index = M.EmptyList
        self.next_id = M.GMPRep("1")
        self.capture_progress = M.false_value
        self.capture_started_at = 0.0
        self.capture_last_progress_at = 0.0
        self.capture_discovered_count = 0
        self.capture_encoded_count = 0
        self.capture_visited_count = 0
        self.capture_next_deadline_visit = 0
        self.capture_next_deadline_encoding = 0
        self.capture_free_queue = M.EmptyList
        self.last_capture_discovery_seconds = 0.0
        self.last_capture_record_seconds = 0.0
        self.last_capture_total_seconds = 0.0

    def _restore_tree_root_worker(queue, state, namespace, root_name, registry):
        # Legacy worker retained for older platforms, but on Windows "spawn"
        # this is fragile because `namespace` can contain non-picklable objects.
        try:
            codec = SnapshotCodec(namespace)
            result = codec._restore_tree_root(state, root_name, registry)
            queue.put((root_name, result))
        except Exception as exc:
            queue.put((root_name, exc))

    def _ns_get(self, name):
        if name not in self.namespace:
            raise RuntimeError("Snapshot namespace missing symbol: " + name)
        return self.namespace[name]

    def _is_pair_object(self, obj):
        try:
            obj.head.value
            obj.tail.value
        except Exception:
            return M.false_value
        return M.truth_value

    def _is_edge_object(self, obj):
        try:
            marker = obj._snapshot_edge_marker
        except Exception:
            try:
                obj.inputs
                obj.results
            except Exception:
                return M.false_value
            return M.truth_value
        if marker.id == obj.id:
            return M.truth_value
        return M.false_value

    def _captured_object_id(self, target):
        return T.IdentityRedBlackNatLookupValue(self.object_id_index, target)()

    def _capture_oid_number(self, oid):
        return int(oid()())

    def _take_capture_oid(self):
        self.next_id = M.GMPRep(self.capture_discovered_count + 2)

    def _scalar_payload(self, x):
        try:
            x.id
        except Exception:
            try:
                return self._encode_scalar(x)
            except (TypeError, ValueError):
                return None
        return None

    def _registry_entries_snapshot_root(self, registry):
        """Snapshot format 4: persist constructor_registry as its entry chain.

        Restore has always replayed TreeInsert from (key, fact) entries and
        thrown the serialised trie nodes away, so the Patricia structure is
        pure derived data on the wire. Capturing the entry chain instead of
        walking the trie removes the trie and key_store objects from the
        snapshot entirely. Old snapshots (version 3, trie-shaped root) stay
        readable: every load path keeps its tree-shaped branch.
        """
        empty = self._ns_get("EmptyList")
        if registry is empty:
            return empty
        tree_label = self._ns_get("TreeLabel")
        try:
            payload = registry()
            if payload is None:
                return registry
            if payload.head.value is not tree_label:
                return registry
        except Exception:
            return registry
        return self._ns_get("TreeEntries")(registry)()

    def _rebuild_tree_from_entry_chain(self, chain):
        rebuilt = self._ns_get("Tree")(self._ns_get("EmptyList"))
        empty = self._ns_get("EmptyList")
        head = self._ns_get("Head")
        tail = self._ns_get("Tail")
        identity = self.namespace["IdentityCompare"]
        truth = self.namespace["truth_value"]
        current = chain
        while identity(current, empty)() is not truth:
            entry = head(current)()
            key = head(entry)()
            fact = head(tail(entry)())()
            rebuilt = self._ns_get("TreeInsert")(rebuilt, key, fact, rebuilt)()
            current = tail(current)()
        return rebuilt

    def _collect_tree_items(self, tree):
        return self._collect_tree_items_from_entries(self._ns_get("TreeEntries")(tree)())

    def _collect_tree_items_from_entries(self, entries):
        if self.namespace["IdentityCompare"](entries, self.namespace["EmptyList"])() is self.namespace["truth_value"]:
            return ()
        entry = self._ns_get("Head")(entries)()
        key = self._ns_get("Head")(entry)()
        fact = self._ns_get("Head")(self._ns_get("Tail")(entry)())()
        return ((key, fact),) + self._collect_tree_items_from_entries(self._ns_get("Tail")(entries)())

    def _rebuild_tree(self, tree, registry):
        rebuilt = self.namespace["Tree"](self.namespace["EmptyList"])
        for key, fact in self._collect_tree_items(tree):
            rebuilt = self.namespace["TreeInsert"](rebuilt, key, fact, registry)()
        return rebuilt

    def _is_current_tree(self, tree):
        # "Current tree" means a modern Patricia-backed tree, not a legacy TreeNode.
        # Support both the general Tree (`trees.IsTree`) and the search-specific
        # patricia tree (`search.SearchPatriciaIsTree`) representations.
        # An empty tree or empty root (EmptyList) is also current.
        if M.Compare(tree, self._ns_get("EmptyList"))() is M.truth_value:
            return M.truth_value
        try:
            if "IsTree" in self.namespace:
                if self.namespace["IsTree"](tree)() is self.namespace["truth_value"]:
                    return M.truth_value
        except Exception:
            pass
        try:
            if "SearchPatriciaIsTree" in self.namespace:
                if self.namespace["SearchPatriciaIsTree"](tree)() is self.namespace["truth_value"]:
                    return M.truth_value
        except Exception:
            pass
        return M.false_value

    def _is_entry_chain(self, obj):
        # Snapshot format 4 stores tree roots as (key, fact) entry chains.
        # Format 3 and older stored Tree/TreeNode atoms, never a bare Pair,
        # so a Pair-shaped root uniquely identifies the entry-chain format.
        return self._is_pair_object(obj)

    def _restore_tree_root(self, state, root_name, registry):
        if root_name not in state.root_ids:
            return self.namespace["EmptyList"]
        loaded_tree = state.roots.get(root_name, self.namespace["EmptyList"])
        if self._is_entry_chain(loaded_tree) is M.truth_value:
            return self._rebuild_tree_from_entry_chain(loaded_tree)
        if self._is_current_tree(loaded_tree) is M.truth_value:
            return loaded_tree
        return self._rebuild_tree_from_record_id(state, state.root_ids[root_name], registry)

    def _restore_tree_roots_parallel(self, state, registry, root_names, debug=M.false_value):
        if not root_names:
            return {}

        # Windows uses "spawn": do not pass `namespace`/`state` into child
        # processes (namespace may contain modules -> unpicklable).
        #
        # Instead, reload the snapshot file inside each subprocess and rebuild
        # the specific root from records.
        try:
            snapshot_path = state.snapshot_path
        except AttributeError:
            snapshot_path = ""
        if not snapshot_path:
            raise RuntimeError("parallel root restore requires state.snapshot_path")

        num_workers = min(8, len(root_names), Wiremod.host_process_budget(0))
        if debug is M.truth_value:
            print(
                "DEBUG: restoring roots",
                root_names,
                "using",
                num_workers,
                "processes",
            )

        processes = ()
        started = {}
        last_heartbeat = {}
        output_paths = {}
        temp_dir = tempfile.mkdtemp(prefix="hyge-root-restore-", dir=os.path.dirname(os.path.abspath(__file__)))
        try:
            ctx = multiprocessing.get_context("spawn")
            for root_name in root_names:
                output_path = os.path.join(temp_dir, root_name + ".pickle")
                proc = ctx.Process(
                    target=_restore_tree_root_from_snapshot_file_worker,
                    args=(snapshot_path, root_name, output_path),
                )
                proc.start()
                processes = processes + (proc,)
                started[root_name] = time.monotonic()
                last_heartbeat[root_name] = started[root_name]
                output_paths[root_name] = output_path
                if debug is M.truth_value:
                    print(
                        "DEBUG: restore worker started:",
                        root_name,
                        f"(pid={proc.pid})",
                        flush=True,
                    )

            results = {}
            received = 0
            while received < len(root_names):
                now = time.monotonic()
                for proc, root_name in zip(processes, root_names):
                    if root_name in results:
                        continue
                    proc.join(timeout=0.0)
                    if os.path.exists(output_paths[root_name]):
                        with open(output_paths[root_name], "rb") as f:
                            payload = pickle.load(f)
                        status = payload[0]
                        value = payload[1]
                        received = received + 1
                        if status != "ok":
                            raise RuntimeError("restore worker failed for " + root_name + ": " + value)
                        results[root_name] = value
                        if debug is M.truth_value:
                            elapsed = time.monotonic() - started.get(root_name, time.monotonic())
                            print(
                                f"DEBUG: restore worker finished: {root_name} ({elapsed:.2f}s)",
                                flush=True,
                            )
                    elif proc.is_alive():
                        if debug is M.truth_value:
                            elapsed = now - started.get(root_name, now)
                            if now - last_heartbeat.get(root_name, 0.0) >= 2.0:
                                print(
                                    f"DEBUG: restore worker {root_name} (pid={proc.pid}) still running, {elapsed:.1f}s elapsed...",
                                    flush=True,
                                )
                                last_heartbeat[root_name] = now
                    else:
                        raise RuntimeError("restore worker failed for " + root_name + ": no output produced")
                if received < len(root_names):
                    time.sleep(0.05)
        except Exception as exc:
            print("ERROR: multiprocessing restore failed: " + str(exc), flush=True)
            raise
        finally:
            for proc in processes:
                proc.join()
            for root_name in root_names:
                if root_name in output_paths:
                    try:
                        os.remove(output_paths[root_name])
                    except OSError:
                        pass
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass

        return results

    def _restore_constructor_registry_parallel(self, state, debug=M.false_value):
        """Restore constructor_registry using multiple spawned workers (Windows-safe)."""
        loaded_registry = state.roots.get(
            "constructor_registry", self.namespace["EmptyList"],
        )
        if self._is_entry_chain(loaded_registry) is M.truth_value:
            # Snapshot format 4: the root is already the (key, fact) entry
            # chain that replay consumes, so the record-scanning shard
            # workers have nothing to do — rebuild directly in-process.
            if debug is M.truth_value:
                print(
                    "DEBUG: constructor_registry is an entry chain; "
                    "rebuilding in-process",
                    flush=True,
                )
            return self._rebuild_tree_from_entry_chain(loaded_registry)
        try:
            snapshot_path = state.snapshot_path
        except AttributeError:
            snapshot_path = ""
        if not snapshot_path:
            return self._restore_tree_root(state, "constructor_registry", loaded_registry)

        ctx = multiprocessing.get_context("spawn")
        shard_count = min(8, Wiremod.host_process_budget(0))
        if debug is M.truth_value:
            print(f"DEBUG: restoring constructor_registry using {shard_count} processes", flush=True)

        procs = ()
        output_paths = ()
        temp_dir = tempfile.mkdtemp(prefix="hyge-registry-restore-", dir=os.path.dirname(os.path.abspath(__file__)))
        t0 = time.monotonic()
        for shard_index in range(shard_count):
            output_path = os.path.join(temp_dir, "shard-" + str(shard_index) + ".pickle")
            proc = ctx.Process(
                target=_restore_constructor_registry_shard_worker,
                args=(snapshot_path, shard_index, shard_count, output_path),
            )
            proc.start()
            procs = procs + (proc,)
            output_paths = output_paths + (output_path,)
            if debug is M.truth_value:
                print(
                    f"DEBUG: registry worker started: shard {shard_index+1}/{shard_count} (pid={proc.pid})",
                    flush=True,
                )

        partials = [None] * shard_count
        received = 0
        try:
            while received < shard_count:
                for shard_index in range(shard_count):
                    if partials[shard_index] is not None:
                        continue
                    proc = procs[shard_index]
                    output_path = output_paths[shard_index]
                    proc.join(timeout=0.0)
                    if os.path.exists(output_path):
                        with open(output_path, "rb") as f:
                            payload = pickle.load(f)
                        status = payload[0]
                        value = payload[1]
                        if status != "ok":
                            raise RuntimeError("registry shard " + str(shard_index + 1) + "/" + str(shard_count) + " failed: " + value)
                        partials[shard_index] = value
                        received += 1
                        if debug is M.truth_value:
                            print(
                                f"DEBUG: registry worker finished: shard {shard_index+1}/{shard_count} ({time.monotonic() - t0:.2f}s)",
                                flush=True,
                            )
                    elif not proc.is_alive():
                        raise RuntimeError("registry shard " + str(shard_index + 1) + "/" + str(shard_count) + " failed: no output produced")
                if received < shard_count:
                    time.sleep(0.05)
        finally:
            for proc in procs:
                try:
                    proc.join()
                except Exception:
                    pass
            for output_path in output_paths:
                try:
                    os.remove(output_path)
                except OSError:
                    pass
            try:
                os.rmdir(temp_dir)
            except OSError:
                pass

        merged = self._ns_get("Tree")(self._ns_get("EmptyList"))
        for partial in partials:
            if not partial:
                continue
            for key_id, fact_id in partial:
                k = state.id_to_obj[key_id]
                v = state.id_to_obj[fact_id]
                merged = self._ns_get("TreeInsert")(merged, k, v, merged)()

        if debug is M.truth_value:
            print(f"DEBUG: constructor_registry merged ({time.monotonic() - t0:.2f}s)", flush=True)
        return merged

    def _tree_lookup_exhaustive(self, tree, key):
        for item_key, item_fact in self._collect_tree_items(tree):
            if self.namespace["IdentityCompare"](key, item_key)() is self.namespace["truth_value"]:
                return item_fact
        return self.namespace["EmptyList"]

    def _record_ref_id(self, payload):
        if payload["tag"] == "ref":
            return payload["id"]
        return None

    def _record_by_id(self, state, obj_id):
        if obj_id is None:
            return None
        if obj_id not in state.records:
            return None
        return state.records[obj_id]

    def _pair_record(self, state, obj_id):
        record = self._record_by_id(state, obj_id)
        if record is None:
            return None
        if "head" in record:
            if "tail" in record:
                return record
        if "value" in record:
            ref_id = self._record_ref_id(record["value"])
            if ref_id is None:
                return None
            ref_record = self._record_by_id(state, ref_id)
            if ref_record is None:
                return None
            if "head" in ref_record:
                if "tail" in ref_record:
                    return ref_record
        return None

    def _pair_head_id(self, state, pair_id):
        record = self._pair_record(state, pair_id)
        if record is None:
            return None
        return self._record_ref_id(record["head"])

    def _pair_tail_id(self, state, pair_id):
        record = self._pair_record(state, pair_id)
        if record is None:
            return None
        return self._record_ref_id(record["tail"])

    def _atom_value_id(self, state, atom_id):
        record = self._record_by_id(state, atom_id)
        if record is None:
            return None
        if "value" not in record:
            return None
        return self._record_ref_id(record["value"])

    def _tree_root_id(self, state, tree_id):
        if tree_id == state.symbol_ids["EmptyList"]:
            return state.symbol_ids["EmptyList"]
        if tree_id is None:
            return state.symbol_ids["EmptyList"]
        payload_id = self._atom_value_id(state, tree_id)
        if payload_id is None:
            return state.symbol_ids["EmptyList"]
        payload_head_id = self._pair_head_id(state, payload_id)
        tree_label_id = state.symbol_ids.get("TreeLabel")
        if payload_head_id == tree_label_id:
            payload_tail_id = self._pair_tail_id(state, payload_id)
            if payload_tail_id is None:
                return state.symbol_ids["EmptyList"]
            return self._pair_head_id(state, payload_tail_id)
        return payload_head_id

    def _tree_node_items_from_records(self, state, node_id):
        # Legacy helper retained for compatibility; prefer the streaming iterator
        # `_iter_tree_node_items_from_records` for performance.
        return tuple(self._iter_tree_node_items_from_records(state, node_id))


    def _iter_tree_node_items_from_records(self, state, node_id):
        """Yield (key_id, fact_id) by inorder traversal of legacy TreeNode records.

        Avoids recursive tuple concatenation (which is O(n^2) and extremely slow).
        """
        empty_id = state.symbol_ids["EmptyList"]
        current = node_id
        stack = []

        while current is not None or stack:
            while (
                current is not None
                and current != empty_id
           
            ):
                stack.append(current)
                payload_id = self._atom_value_id(state, current)
                if payload_id is None:
                    current = empty_id
                    break
                fact_tail_id = self._pair_tail_id(state, payload_id)
                if fact_tail_id is None:
                    current = empty_id
                    break
                branches_id = self._pair_tail_id(state, fact_tail_id)
                if branches_id is None:
                    current = empty_id
                    break
                current = self._pair_head_id(state, branches_id)

            if not stack:
                return

            node = stack.pop()
            payload_id = self._atom_value_id(state, node)
            if payload_id is None:
                current = empty_id
                continue

            key_id = self._pair_head_id(state, payload_id)
            fact_tail_id = self._pair_tail_id(state, payload_id)
            if fact_tail_id is None:
                current = empty_id
                continue

            fact_id = self._pair_head_id(state, fact_tail_id)
            if key_id is not None and fact_id is not None:
                yield (key_id, fact_id)

            branches_id = self._pair_tail_id(state, fact_tail_id)
            if branches_id is None:
                current = empty_id
                continue
            right_pair_id = self._pair_tail_id(state, branches_id)
            if right_pair_id is None:
                current = empty_id
                continue
            current = self._pair_head_id(state, right_pair_id)

    def _tree_lookup_record_fact_id(self, state, tree_id, key_id):
        root_id = self._tree_root_id(state, tree_id)
        items = self._tree_node_items_from_records(state, root_id)
        for item_key_id, item_fact_id in items:
            if item_key_id == key_id:
                return item_fact_id
        return state.symbol_ids["EmptyList"]

    def _rebuild_tree_from_record_id(self, state, tree_id, registry):
        root_id = self._tree_root_id(state, tree_id)
        root_record = self._record_by_id(state, root_id)
        if root_record is not None:
            if root_record.get("class") == "TreeNode":
                rebuilt = self._ns_get("Tree")(self._ns_get("EmptyList"))
                try:
                    root_name = self._restore_debug_root_name
                except AttributeError:
                    root_name = None
                last_report = time.monotonic()
                inserted = 0
                for key_id, fact_id in self._iter_tree_node_items_from_records(state, root_id):
                    rebuilt = self._ns_get("TreeInsert")(
                        rebuilt,
                        state.id_to_obj[key_id],
                        state.id_to_obj[fact_id],
                        registry,
                    )()
                    inserted += 1
                    if root_name is not None:
                        now = time.monotonic()
                        if now - last_report >= 2.0:
                            print(
                                f"DEBUG: worker rebuilding {root_name}: inserted {inserted} entries",
                                flush=True,
                            )
                            last_report = now
                return rebuilt
        tree_obj = state.id_to_obj.get(tree_id, self._ns_get("EmptyList"))
        return self._rebuild_tree(tree_obj, registry)

    def _encode_field(self, x):
        if x is None:
            return {"tag": "none"}
        scalar = self._scalar_payload(x)
        if scalar is not None:
            return {"tag": "scalar", "value": scalar}
        oid = self._captured_object_id(x)
        if oid is not M.EmptyList:
            return {"tag": "ref", "id": self._capture_oid_number(oid)}
        return {"tag": "scalar", "value": self._encode_scalar(x)}

    def _encode_scalar(self, x):
        try:
            json.dumps(x)
            return {"kind": "json", "value": x}
        except TypeError:
            try:
                value = gmpy2.mpz(x)
            except (TypeError, ValueError):
                raise
            return {"kind": "mpz", "value": str(value)}

    def _decode_scalar(self, payload):
        try:
            payload.get("kind")
        except AttributeError:
            return payload
        if payload.get("kind") is None:
            return payload["value"]
        if payload.get("kind") == "json":
            return payload["value"]
        if payload.get("kind") == "mpz":
            return gmpy2.mpz(payload["value"])
        raise RuntimeError("Unknown scalar encoding in snapshot")

    def _decode_field(self, payload, id_to_obj):
        tag = payload["tag"]
        if tag == "none":
            return None
        if tag == "ref":
            return id_to_obj[payload["id"]]
        return self._decode_scalar(payload["value"])

    def _child_refs(self, obj):
        if self._is_pair_object(obj) is M.truth_value:
            return (obj.head.value, obj.tail.value)
        if self._is_edge_object(obj) is M.truth_value:
            return (obj.inputs, obj.results, obj.value)
        if obj.value is None:
            return ()
        return (obj.value,)

    def _queue_uncaptured(self, candidate, queue, Pair):
        if candidate is None:
            return queue
        if self._scalar_payload(candidate) is not None:
            return queue
        if self._captured_object_id(candidate) is not M.EmptyList:
            return queue
        if self.capture_free_queue is M.EmptyList:
            return Pair(candidate, queue)
        reusable = self.capture_free_queue
        self.capture_free_queue = reusable.tail.value
        reusable.head.value = candidate
        reusable.tail.value = queue
        return reusable

    def _intern(self, obj, deadline=None):
        # Non-recursive intern. Use a machine Pair chain as the work queue so we
        # don't depend on Python recursion or Python container worklists.
        if obj is None:
            return None
        if self._scalar_payload(obj) is not None:
            return None

        existing = self._captured_object_id(obj)
        if existing is not M.EmptyList:
            return existing
        root_oid = M.EmptyList

        Pair = self.namespace["Pair"]
        EmptyList = self.namespace["EmptyList"]

        queue = EmptyList
        current = obj
        active = M.truth_value
        while active is M.truth_value:
            if current is None:
                if queue is EmptyList:
                    active = M.false_value
                    continue
                consumed = queue
                current = consumed.head.value
                queue = consumed.tail.value
                consumed.tail.value = self.capture_free_queue
                self.capture_free_queue = consumed
                continue
            self.capture_visited_count = self.capture_visited_count + 1
            if deadline is not None:
                if self.capture_visited_count >= self.capture_next_deadline_visit:
                    deadline.require_capture_progress(
                        "capture discovery",
                        self.capture_discovered_count,
                        self.capture_encoded_count,
                    )
                    self.capture_next_deadline_visit = (
                        self.capture_visited_count + SNAPSHOT_DEADLINE_OBJECT_INTERVAL
                    )
            if self._scalar_payload(current) is not None:
                current = None
                continue
            insertion = T.IdentityRedBlackNatInsertMissing(
                self.object_id_index,
                current,
                self.next_id,
            )
            next_object_id_index = insertion()
            if insertion.inserted is M.false_value:
                current = None
                continue
            if root_oid is M.EmptyList:
                root_oid = insertion.inserted_value

            self._take_capture_oid()
            self.object_id_index = next_object_id_index
            self.capture_discovered_count = self.capture_discovered_count + 1
            if self.capture_progress is M.truth_value:
                capture_now = time.monotonic()
                if capture_now - self.capture_last_progress_at >= SNAPSHOT_CAPTURE_PROGRESS_SECONDS:
                    print(
                        "snapshot capture: discovery: "
                        + str(self.capture_discovered_count)
                        + " objects found ("
                        + format(capture_now - self.capture_started_at, ".1f")
                        + "s elapsed)",
                        flush=True,
                    )
                    self.capture_last_progress_at = capture_now

            if self._is_pair_object(current) is M.truth_value:
                queue = self._queue_uncaptured(current.head.value, queue, Pair)
                current = current.tail.value
                continue
            if self._is_edge_object(current) is M.truth_value:
                queue = self._queue_uncaptured(current.inputs, queue, Pair)
                queue = self._queue_uncaptured(current.results, queue, Pair)
                current = current.value
                continue
            current = current.value

        return root_oid

    def _record_for(self, obj, oid):
        if self._is_pair_object(obj) is M.truth_value:
            return {
                "id": oid,
                "head": self._encode_field(obj.head.value),
                "tail": self._encode_field(obj.tail.value),
            }

        if self._is_edge_object(obj) is M.truth_value:
            return {
                "id": oid,
                "inputs": self._encode_field(obj.inputs),
                "results": self._encode_field(obj.results),
                "value": self._encode_field(obj.value),
            }

        try:
            symbol = obj.symbol
        except Exception:
            symbol = None
        if symbol is not None:
            return {
                "id": oid,
                "symbol": symbol,
                "value": self._encode_field(obj.value),
            }

        record = {
            "id": oid,
            "value": self._encode_field(obj.value),
        }
        marker = self._capture_nat_marker(obj)
        if marker is not None:
            record["canonical_family"] = marker[0]
            record["canonical_key"] = marker[1]
            if marker[2] is not None:
                record["canonical_name"] = marker[2]
        return record

    def _capture_nat_marker(self, obj):
        """The canonical-family marker for a plain atom, or None.

        Three identity contracts cross a persistence boundary and only one
        of them is this: sharing inside the snapshot's own object graph,
        named singletons, and canonical-family identity. This stamps the
        third, on objects the *structure* says are Nats — `Zero`, or a term
        whose constructor in the live registry is `SuccLabel` — never on
        objects that merely look like numbers. A GMPRep carrier holding
        numeric 2 has no Succ constructor and gets no marker. A Char
        carrying "2" has no Succ constructor and gets no marker. Nothing
        here reads a payload to decide what a thing is.

        The value is read only after Nat-ness is established, and then it is
        read by `NatRepOf`, the machine's own rep, with the cached rep as a
        fallback for a Nat whose successor chain the registry no longer
        carries. It is taken at capture because that is where the question
        is answerable: after a restore the chains are gone and `NatRepOf`
        returns EmptyList for a Nat holding its value as an mpz, which is
        why the marker has to travel with the record.
        """

        registry = getattr(self, "_capture_registry", None)
        if registry is None:
            return None
        # Only a machine object can be a Nat. The namespace holds things
        # that are not -- a hypergraph has no `.id` at all, and asking
        # `NatRepOf` about one raises inside the structural comparison.
        try:
            obj.id
        except Exception:
            return None
        empty = M.EmptyList
        text = ""
        if obj is self.namespace["Zero"]:
            text = "0"
        else:
            try:
                rep = M.NatRepOf(obj, registry)()
            except Exception:
                return None
            if M.IdentityCompare(rep, empty)() is M.false_value:
                text = self._rep_text(rep)
            if not text:
                # `NatRepOf` needs a cached rep or the successor chain, and
                # a named Nat that has neither is still a Nat by
                # construction. A Char and a GMPRep carrier fail both
                # tests: no rep that reads as a number, no Succ
                # constructor.
                constructor = C.GetConstructor(obj, registry)()
                if M.IdentityCompare(constructor, empty)() is M.truth_value:
                    return None
                if M.IdentityCompare(M.Head(constructor)(), self.namespace["SuccLabel"])() is M.false_value:
                    return None
                text = self._rep_text(getattr(obj, "value", None))
            if not text:
                return None
        return ("nat", text, self._capture_nat_names.get(id(obj)))

    def _rep_text(self, rep):
        """The decimal text of a rep: a GMPRep, or the mpz itself."""

        if rep is None:
            return ""
        text = str(rep)
        if text.isdigit():
            return text
        try:
            text = str(rep())
        except Exception:
            return ""
        if text.isdigit():
            return text
        return ""

    def _encode_captured_subtree(
        self,
        tree,
        objects,
        discovery_finished_at,
        deadline,
    ):
        if tree is M.EmptyList:
            return
        self._encode_captured_subtree(
            tree.head.value,
            objects,
            discovery_finished_at,
            deadline,
        )
        entry = tree.value
        obj = entry.head.value
        oid = self._capture_oid_number(entry.tail)
        objects[oid - 1] = self._record_for(obj, oid)
        self.capture_encoded_count = self.capture_encoded_count + 1
        if deadline is not None:
            if self.capture_encoded_count >= self.capture_next_deadline_encoding:
                deadline.require_capture_progress(
                    "record encoding",
                    self.capture_discovered_count,
                    self.capture_encoded_count,
                )
                self.capture_next_deadline_encoding = (
                    self.capture_encoded_count + SNAPSHOT_DEADLINE_OBJECT_INTERVAL
                )
        if self.capture_progress is M.truth_value:
            capture_now = time.monotonic()
            if capture_now - self.capture_last_progress_at >= SNAPSHOT_CAPTURE_PROGRESS_SECONDS:
                print(
                    "snapshot capture: record encoding: "
                    + str(self.capture_encoded_count)
                    + " / "
                    + str(self.capture_discovered_count)
                    + " objects ("
                    + format(capture_now - discovery_finished_at, ".1f")
                    + "s in phase, "
                    + format(capture_now - self.capture_started_at, ".1f")
                    + "s total)",
                    flush=True,
                )
                self.capture_last_progress_at = capture_now
        self._encode_captured_subtree(
            tree.tail.value,
            objects,
            discovery_finished_at,
            deadline,
        )

    def _capture_from_roots(self, roots, progress=M.false_value, deadline=None):
        self.object_id_index = M.EmptyList
        self.next_id = M.GMPRep("1")
        self.capture_progress = progress
        self.capture_started_at = time.monotonic()
        self.capture_last_progress_at = self.capture_started_at
        self.capture_discovered_count = 0
        self.capture_encoded_count = 0
        self.capture_visited_count = 0
        self.capture_next_deadline_visit = 0
        self.capture_next_deadline_encoding = 0
        self.capture_free_queue = M.EmptyList
        self.last_capture_discovery_seconds = 0.0
        self.last_capture_record_seconds = 0.0
        self.last_capture_total_seconds = 0.0
        if deadline is not None:
            deadline.require_remaining("capture discovery")
        if self.capture_progress is M.truth_value:
            print("snapshot capture: discovery started", flush=True)

        for name in roots:
            if deadline is not None:
                deadline.require_remaining("capture discovery")
            if self.capture_progress is M.truth_value:
                print(
                    "snapshot capture: root "
                    + name
                    + " starting at "
                    + str(self.capture_discovered_count)
                    + " objects",
                    flush=True,
                )
            self._intern(roots[name], deadline)
            if self.capture_progress is M.truth_value:
                print(
                    "snapshot capture: root "
                    + name
                    + " complete at "
                    + str(self.capture_discovered_count)
                    + " objects",
                    flush=True,
                )

        symbols = {}
        for name in self.symbol_names:
            if deadline is not None:
                deadline.require_remaining("capture discovery")
            if name in self.namespace:
                obj = self.namespace[name]
                symbols[name] = obj
                self._intern(obj, deadline)

        discovery_finished_at = time.monotonic()
        self.last_capture_discovery_seconds = discovery_finished_at - self.capture_started_at
        object_count = int(self.next_id()) - 1
        if self.capture_progress is M.truth_value:
            print(
                "snapshot capture: discovery complete: "
                + str(object_count)
                + " objects in "
                + format(self.last_capture_discovery_seconds, ".2f")
                + "s",
                flush=True,
            )
            print(
                "snapshot capture: record encoding started: "
                + str(object_count)
                + " objects",
                flush=True,
            )

        objects = [None] * object_count
        self.capture_last_progress_at = discovery_finished_at
        if deadline is not None:
            deadline.require_capture_progress(
                "record encoding",
                self.capture_discovered_count,
                self.capture_encoded_count,
            )
        self._encode_captured_subtree(
            self.object_id_index,
            objects,
            discovery_finished_at,
            deadline,
        )
        if deadline is not None:
            deadline.require_capture_progress(
                "record encoding",
                self.capture_discovered_count,
                self.capture_encoded_count,
            )
        for name in self.namespace:
            if deadline is not None:
                deadline.require_remaining("record encoding")
            namespace_object = self.namespace[name]
            try:
                namespace_object.id
            except Exception:
                continue
            namespace_oid = self._captured_object_id(namespace_object)
            if namespace_oid is M.EmptyList:
                continue
            namespace_oid_number = self._capture_oid_number(namespace_oid)
            if "name" in objects[namespace_oid_number - 1]:
                continue
            record = {
                "id": namespace_oid_number,
                "name": name,
            }
            marker = self._capture_nat_marker(namespace_object)
            if marker is not None:
                record["canonical_family"] = marker[0]
                record["canonical_key"] = marker[1]
                if marker[2] is not None:
                    record["canonical_name"] = marker[2]
            objects[namespace_oid_number - 1] = record

        records_finished_at = time.monotonic()
        self.last_capture_record_seconds = records_finished_at - discovery_finished_at
        if self.capture_progress is M.truth_value:
            print(
                "snapshot capture: record encoding complete: "
                + str(self.capture_encoded_count)
                + " objects in "
                + format(self.last_capture_record_seconds, ".2f")
                + "s",
                flush=True,
            )

        root_ids = {}
        for name in roots:
            root_ids[name] = self._capture_oid_number(
                self._captured_object_id(roots[name])
            )

        symbol_ids = {}
        for name in symbols:
            symbol_ids[name] = self._capture_oid_number(
                self._captured_object_id(symbols[name])
            )

        self.last_capture_total_seconds = time.monotonic() - self.capture_started_at
        if self.capture_progress is M.truth_value:
            print(
                "snapshot capture: complete: "
                + str(object_count)
                + " objects in "
                + format(self.last_capture_total_seconds, ".2f")
                + "s",
                flush=True,
            )

        snapshot = {
            "header": {"format": "hyge-proof-kernel", "version": 4, "protocol_version": 3},
            "roots": root_ids,
            "symbols": symbol_ids,
            "objects": objects,
        }
        return snapshot

    def capture_objects(self, roots, progress=M.false_value, deadline=None):
        collection_thresholds = gc.get_threshold()
        gc.set_threshold(0)
        try:
            return self._capture_from_roots(roots, progress, deadline)
        finally:
            gc.set_threshold(*collection_thresholds)

    def capture(self, graph, extra_roots=None, progress=M.false_value, deadline=None):
        # Canonical-family markers are decided here, at capture, while the
        # live registry still holds the successor chains and the live index
        # still names the Nat for each value. After a restore neither is
        # true, which is why the marker has to travel with the record.
        self._capture_registry = graph.constructor_registry
        self._capture_nat_names = {}
        for name in self.namespace:
            symbol = self.namespace[name]
            if symbol is not None:
                self._capture_nat_names.setdefault(id(symbol), name)
        roots = {
            "constructor_registry": self._registry_entries_snapshot_root(
                graph.constructor_registry,
            ),
            "all_rules": graph.all_rules,
            "rule_order": graph.rule_order,
            "derivations": graph.derivations,
            "derivation_schemata": graph.derivation_schemata,
            "search_history": graph.search_history,
            "search_comparisons": graph.search_comparisons,
            "search_comparison_jobs": graph.search_comparison_jobs,
            "search_jobs": graph.search_jobs,
            "search_memo": graph.search_memo,
            "nat_value_index": graph.nat_value_index,
            "dependency_requests": getattr(graph, "dependency_requests", M.EmptyList),
            "dependency_graph": getattr(graph, "dependency_graph", M.EmptyList),
            "generator_metrics": getattr(graph, "generator_metrics", M.EmptyList),
            "last_proof": getattr(graph, "last_proof", M.EmptyList),
            "research_residuals": getattr(graph, "research_residuals", M.EmptyList),
            "provenance_map": getattr(graph, "provenance_map", M.EmptyList),
            "generator_policy": getattr(graph, "generator_policy", M.EmptyList),
            "last_residuals": getattr(graph, "last_residuals", M.EmptyList),
            "counterfactual_results": getattr(graph, "counterfactual_results", M.EmptyList),
            "research_mode": getattr(graph, "research_mode", M.EmptyList),
            "research_attempts": getattr(graph, "research_attempts", M.EmptyList),
            "intervention_episodes": getattr(graph, "intervention_episodes", M.EmptyList),
            "dependency_policies": getattr(graph, "dependency_policies", M.EmptyList),
        }
        if extra_roots is not None:
            for name in extra_roots:
                roots[name] = extra_roots[name]
        collection_thresholds = gc.get_threshold()
        gc.set_threshold(0)
        try:
            return self._capture_from_roots(roots, progress, deadline)
        finally:
            gc.set_threshold(*collection_thresholds)

    def save(self, graph, path, progress=M.truth_value, deadline=None):
        save_started_at = time.monotonic()
        if progress is M.truth_value:
            print("snapshot save: capture discovery starting", flush=True)
        snapshot = self.capture(graph, progress=progress, deadline=deadline)
        capture_finished_at = time.monotonic()
        if progress is M.truth_value:
            print(
                "snapshot save: capture finished in "
                + format(capture_finished_at - save_started_at, ".2f")
                + "s; JSON write starting",
                flush=True,
            )
        tmp_path = path + ".tmp"
        try:
            if deadline is not None:
                deadline.set_temporary_path(tmp_path)
                deadline.require_remaining("JSON writing")
            payload = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
            if deadline is not None:
                deadline.require_remaining("JSON encoding")
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            if deadline is not None:
                deadline.require_remaining("JSON writing")
            write_finished_at = time.monotonic()
            if progress is M.truth_value:
                try:
                    snapshot_bytes = os.path.getsize(tmp_path)
                except OSError:
                    snapshot_bytes = None
                if snapshot_bytes is None:
                    print(
                        "snapshot save: JSON write complete in "
                        + format(write_finished_at - capture_finished_at, ".2f")
                        + "s; atomic replace starting",
                        flush=True,
                    )
                else:
                    print(
                        "snapshot save: JSON write complete: "
                        + str(snapshot_bytes)
                        + " bytes in "
                        + format(write_finished_at - capture_finished_at, ".2f")
                        + "s; atomic replace starting",
                        flush=True,
                    )
            if deadline is not None:
                deadline.require_remaining("atomic replacement")
                deadline.replace_temporary_snapshot(path)
            else:
                os.replace(tmp_path, path)
            if progress is M.truth_value:
                print(
                    "snapshot save: complete in "
                    + format(time.monotonic() - save_started_at, ".2f")
                    + "s",
                    flush=True,
                )
            self.object_id_index = M.EmptyList
            self.capture_free_queue = M.EmptyList
            return path
        except Exception:
            if deadline is not None:
                deadline.discard_temporary_output()
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
            self.object_id_index = M.EmptyList
            self.capture_free_queue = M.EmptyList
            raise

    def load_snapshot(self, snapshot):
        if snapshot["header"]["format"] != "hyge-proof-kernel":
            raise RuntimeError("Wrong snapshot format")
        if snapshot["header"]["version"] not in (3, 4):
            raise RuntimeError("Unsupported snapshot version")

        id_to_obj = {}
        Atom = self.namespace["Atom"]
        EmptyList = self.namespace["EmptyList"]
        symbol_names_by_id = {}
        for name in snapshot["symbols"]:
            oid = snapshot["symbols"][name]
            symbol_names_by_id[oid] = name

        for record in snapshot["objects"]:
            record_id = record["id"]
            if record_id in symbol_names_by_id:
                symbol_name = symbol_names_by_id[record_id]
                if symbol_name in self.namespace:
                    existing_symbol = self.namespace[symbol_name]
                    id_to_obj[record_id] = existing_symbol
                    continue
            if "name" in record:
                symbol_name = record["name"]
                if symbol_name not in self.namespace:
                    raise RuntimeError("Snapshot namespace missing symbol: " + symbol_name)
                id_to_obj[record_id] = self.namespace[symbol_name]
                continue
            if "head" in record:
                obj = self.namespace["Pair"](EmptyList, EmptyList)
            elif "inputs" in record:
                obj = self.namespace["Edge"](EmptyList, EmptyList)
            elif "symbol" in record:
                obj = self.namespace["Char"](record["symbol"])
            else:
                obj = self.namespace["Atom"]()

            id_to_obj[record["id"]] = obj

        for record in snapshot["objects"]:
            obj = id_to_obj[record["id"]]
            if "name" in record:
                continue
            if "head" in record:
                obj.head.value = self._decode_field(record["head"], id_to_obj)
                obj.tail.value = self._decode_field(record["tail"], id_to_obj)
            elif "symbol" in record:
                obj.symbol = record["symbol"]
                obj.value = self._decode_field(record["value"], id_to_obj)
            elif "inputs" in record:
                obj.inputs = self._decode_field(record["inputs"], id_to_obj)
                obj.results = self._decode_field(record["results"], id_to_obj)
                obj.value = self._decode_field(record["value"], id_to_obj)
                obj._snapshot_edge_marker = obj
            else:
                obj.value = self._decode_field(record["value"], id_to_obj)

        roots = {}
        for name in snapshot["roots"]:
            roots[name] = id_to_obj[snapshot["roots"][name]]

        symbols = {}
        for name in snapshot["symbols"]:
            symbols[name] = id_to_obj[snapshot["symbols"][name]]

        records = {record["id"]: record for record in snapshot["objects"]}
        canonical_nats = {}
        for record in snapshot["objects"]:
            if record.get("canonical_family") != "nat":
                continue
            canonical_nats[record["id"]] = (
                record["canonical_key"],
                record.get("canonical_name"),
            )
        state = SnapshotState(
            roots,
            symbols,
            snapshot["roots"],
            snapshot["symbols"],
            id_to_obj,
            records,
            M.false_value,
            canonical_nats,
        )

        upgrade_roots = ()
        for root_name in (
            "constructor_registry",
            "all_rules",
            "derivations",
            "derivation_schemata",
            "search_memo",
            "nat_value_index",
        ):
            if root_name not in state.root_ids:
                continue
            root_id = self._tree_root_id(state, state.root_ids[root_name])
            root_record = self._record_by_id(state, root_id)
            if root_record is None:
                continue
            if root_record.get("class") != "TreeNode":
                continue
            state.needs_upgrade = M.truth_value
            upgrade_roots = upgrade_roots + (root_name,)
        state.upgrade_roots = upgrade_roots

        return state

    def load(self, path):
        with open(path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)
        state = self.load_snapshot(snapshot)
        state.snapshot_path = os.path.abspath(path)
        return state

    def _sync_namespace_modules(self):
        """Point every module's globals at the namespace's symbols.

        Restore resolves named symbols to the objects the namespace names,
        so a pass that replaces an object has to run this or the modules
        keep pointing at the one it replaced.
        """

        Core.sync_from_namespace(self.namespace)
        Ctxmod.sync_from_namespace(self.namespace)
        Lmod.sync_from_namespace(self.namespace)
        T.sync_from_namespace(self.namespace)
        C.sync_from_namespace(self.namespace)
        Gmpmod.sync_from_namespace(self.namespace)
        Prettymod.sync_from_namespace(self.namespace)
        Pmod.sync_from_namespace(self.namespace)
        Smod.sync_from_namespace(self.namespace)

    def activate(
        self,
        state,
        graph,
        debug=M.false_value,
        save_upgraded_snapshot=M.truth_value,
    ):
        t0 = time.monotonic()
        for name in state.symbols:
            self.namespace[name] = state.symbols[name]
        if debug is M.truth_value:
            print(f"DEBUG: activate: installed {len(state.symbols)} symbols ({time.monotonic() - t0:.2f}s)", flush=True)
        Core.sync_from_namespace(self.namespace)
        Ctxmod.sync_from_namespace(self.namespace)
        Lmod.sync_from_namespace(self.namespace)
        T.sync_from_namespace(self.namespace)
        C.sync_from_namespace(self.namespace)
        Gmpmod.sync_from_namespace(self.namespace)
        Prettymod.sync_from_namespace(self.namespace)
        Pmod.sync_from_namespace(self.namespace)
        Smod.sync_from_namespace(self.namespace)
        if debug is M.truth_value:
            print(f"DEBUG: activate: synced modules ({time.monotonic() - t0:.2f}s)", flush=True)

        if debug is M.truth_value:
            print("DEBUG: activate: restoring constructor_registry (parallel)...", flush=True)
        t_reg0 = time.monotonic()
        rebuilt_registry = self._restore_constructor_registry_parallel(state, debug=debug)
        if debug is M.truth_value:
            print(f"DEBUG: activate: constructor_registry restored ({time.monotonic() - t_reg0:.2f}s)", flush=True)

        root_names = ["all_rules", "derivations", "derivation_schemata"]
        if debug is M.truth_value:
            print("DEBUG: activate: restoring large roots in parallel...", flush=True)
        restored = self._restore_tree_roots_parallel(state, rebuilt_registry, root_names, debug=debug)
        rebuilt_all_rules = restored["all_rules"]
        rebuilt_derivations = restored["derivations"]
        rebuilt_derivation_schemata = restored["derivation_schemata"]
        if debug is M.truth_value:
            print(f"DEBUG: activate: large roots restored ({time.monotonic() - t0:.2f}s total)", flush=True)

        rebuilt_search_memo = self._ns_get("Tree")(self._ns_get("EmptyList"))
        if "search_memo" in state.root_ids:
            if debug is M.truth_value:
                print("DEBUG: activate: restoring search_memo...", flush=True)
            rebuilt_search_memo = self._restore_tree_root(state, "search_memo", rebuilt_registry)

        rebuilt_nat_value_index = self._ns_get("Tree")(self._ns_get("EmptyList"))
        if "nat_value_index" in state.root_ids:
            if debug is M.truth_value:
                print("DEBUG: activate: restoring nat_value_index...", flush=True)
            rebuilt_nat_value_index = self._restore_tree_root(state, "nat_value_index", rebuilt_registry)

        if debug is M.truth_value:
            print("DEBUG: activate: replacing graph context...", flush=True)
        graph._replace_context(
            constructors=rebuilt_registry,
            all_rules=rebuilt_all_rules,
            rule_order=state.roots["rule_order"],
            derivations=rebuilt_derivations,
            derivation_schemata=rebuilt_derivation_schemata,
            search_history=state.roots.get("search_history", self._ns_get("EmptyList")),
            search_comparisons=state.roots.get("search_comparisons", self._ns_get("EmptyList")),
            search_comparison_jobs=state.roots.get("search_comparison_jobs", self._ns_get("EmptyList")),
            search_jobs=state.roots.get("search_jobs", self._ns_get("EmptyList")),
            search_memo=rebuilt_search_memo,
            nat_value_index=rebuilt_nat_value_index,
            dependency_requests=state.roots.get("dependency_requests", self._ns_get("EmptyList")),
            dependency_graph=state.roots.get("dependency_graph", self._ns_get("EmptyList")),
            generator_metrics=state.roots.get("generator_metrics", self._ns_get("EmptyList")),
            last_proof=state.roots.get("last_proof", self._ns_get("EmptyList")),
            research_residuals=state.roots.get("research_residuals", self._ns_get("EmptyList")),
            provenance_map=state.roots.get("provenance_map", self._ns_get("EmptyList")),
            generator_policy=state.roots.get("generator_policy", self._ns_get("EmptyList")),
            last_residuals=state.roots.get("last_residuals", self._ns_get("EmptyList")),
            counterfactual_results=state.roots.get("counterfactual_results", self._ns_get("EmptyList")),
            research_mode=state.roots.get("research_mode", self._ns_get("EmptyList")),
            research_attempts=state.roots.get("research_attempts", self._ns_get("EmptyList")),
            intervention_episodes=state.roots.get("intervention_episodes", self._ns_get("EmptyList")),
            dependency_policies=state.roots.get("dependency_policies", self._ns_get("EmptyList")),
        )
        self.namespace["AllConstructors"] = graph.constructor_registry

        graph.refresh_context()

        # If we had to rebuild legacy roots, persist an upgraded snapshot so
        # future boots skip the TreeInsert rebuild cost.
        #
        # This is intentionally automatic and atomic: the rebuild already paid
        # the full cost, so we make it one-time.
        try:
            snapshot_path = state.snapshot_path
        except AttributeError:
            snapshot_path = ""
        if snapshot_path:
            needs_upgrade = M.false_value
            for root_name in root_names:
                loaded_tree = state.roots.get(root_name, self._ns_get("EmptyList"))
                if self._is_current_tree(loaded_tree) is M.false_value:
                    needs_upgrade = M.truth_value
                    break
            if needs_upgrade is M.truth_value:
                if save_upgraded_snapshot is M.truth_value:
                    if debug is M.truth_value:
                        print("DEBUG: activate: saving upgraded snapshot...", flush=True)
                    t_save0 = time.monotonic()
                    self.save(graph, snapshot_path, progress=debug)
                    if debug is M.truth_value:
                        print(f"DEBUG: activate: upgraded snapshot saved ({time.monotonic() - t_save0:.2f}s)", flush=True)
                elif debug is M.truth_value:
                    print("DEBUG: activate: deferred upgraded snapshot save", flush=True)

        # Canonical-family identity is restored last: it needs the roots
        # activation just rebuilt, and it runs after any upgraded snapshot is
        # written because a published checkpoint is not rewritten by a fix.
        canonicalized = self._canonicalize_restored_nats(state, graph, debug=debug)
        if debug is M.truth_value:
            print(
                f"DEBUG: activate: canonicalized {canonicalized} restored Nats ({time.monotonic() - t0:.2f}s total)",
                flush=True,
            )
        return graph

    def _canonicalize_restored_nats(self, state, graph, debug=M.false_value):
        """D3: make every restored Nat the Nat the machine builds for its value.

        Restore fabricates one object per record and reconnects only what
        two contracts cover: sharing inside the snapshot's own object graph,
        and named singletons, which resolve to the live object of that name.
        Canonical-family identity is the third contract and was missing: a
        snapshot that mentions the number two in five places restored five
        twos, none of them the Nat the runtime names, so `TermEqual` and
        `IdentityCompare` over restored value-bearing state were false while
        `NatEq`, which reads the value, agreed.

        Which objects are Nats is *not* decided here. It was decided at
        capture and travelled in the record, because after a restore the
        machine cannot answer it: the registry does not carry the successor
        chains and `NatRepOf` returns EmptyList for a Nat holding its value
        as an mpz. Deciding it here would mean guessing from a payload, and
        a GMPRep carrier and a digit Char both look like numbers.

        The canonical representative is looked up, never built: either the
        named symbol the namespace already resolves, or `NatFromRep`, which
        is the interning entry point and registers what it has to build.
        The live runtime is the authority, so the restored copies are inputs
        to this map and not competing canonical objects.

        Staged, because the order is the fix:

          1. map each marked restored record to the canonical Nat
          2. substitute, from the roots the active graph owns
          3. re-point roots, symbols and the id map
          4. rebuild the value index from the canonicalised entries
        """

        if not state.canonical_nats:
            return 0

        registry = graph.constructor_registry
        empty = self.namespace["EmptyList"]
        # value text -> Nat, from the index the snapshot already carries, so
        # a value that is indexed is never built.
        index_by_value = self._nat_index_by_value(graph.nat_value_index)
        deferred = 0
        canonical = {}
        for record_id in state.canonical_nats:
            text, name = state.canonical_nats[record_id]
            if text in canonical:
                continue
            named = self.namespace.get(name) if name is not None else None
            if named is not None:
                canonical[text] = named
                continue
            existing = index_by_value.get(text)
            if existing is not None:
                canonical[text] = existing
                continue
            try:
                pair = M.NatFromRep(M.GMPRep(text), registry)()
            except RecursionError:
                # Building a Nat registers it in the constructor registry,
                # whose structural key is nested as deeply as the Nat is
                # long, so a large one exhausts the interpreter stack. That
                # is the machine's own limit and it is not this pass's to
                # raise: the value is left as restore produced it rather
                # than taking the boot down with it.
                deferred = deferred + 1
                continue
            canonical[text] = M.Head(pair)()
            registry = M.Head(M.Tail(pair)())()

        remap = {}
        for record_id in state.canonical_nats:
            obj = state.id_to_obj.get(record_id)
            if obj is None:
                continue
            text, _name = state.canonical_nats[record_id]
            canonical_nat = canonical.get(text)
            if canonical_nat is None or canonical_nat is obj:
                continue
            remap[id(obj)] = canonical_nat

        if not remap:
            if debug is M.truth_value and deferred:
                print(f"DEBUG: canonicalize: {deferred} Nats deferred (too large to build)", flush=True)
            return 0

        # 2. Substitute from the roots the active graph owns. `state.roots`
        #    still points at the *loaded* trees while activation rebuilt new
        #    ones, so seeding from it would rewrite the superseded copies.
        #    The map is consulted before descending: a root that *is* a Nat
        #    has no parent field through which it could be replaced.
        seen = set()
        for seed in self._canonicalize_seeds(state, graph):
            replacement = remap.get(id(seed))
            self._substitute_canonical(seed if replacement is None else replacement, remap, seen)

        # 3. Roots, symbols and the id map, which are reached directly and
        #    not through a field.
        # Only a name the context owns can be handed to it: a snapshot may
        # carry extra roots, and `ReplaceContext` rejects what it does not
        # know.
        context_names = set(self.ROOT_NAMES)
        changed_roots = {}
        for name in state.roots:
            current = state.roots[name]
            replacement = remap.get(id(current))
            if replacement is not None:
                state.roots[name] = replacement
                if name in context_names:
                    changed_roots[name] = replacement
        for name in state.symbols:
            current = state.symbols[name]
            replacement = remap.get(id(current))
            if replacement is not None:
                state.symbols[name] = replacement
                self.namespace[name] = replacement
        for record_id in state.id_to_obj:
            current = state.id_to_obj[record_id]
            replacement = remap.get(id(current))
            if replacement is not None:
                state.id_to_obj[record_id] = replacement

        for name in self.ROOT_NAMES:
            current = getattr(graph, name, None)
            if current is None:
                continue
            replacement = remap.get(id(current))
            if replacement is not None:
                changed_roots[name] = replacement

        if changed_roots:
            graph._replace_context(**changed_roots)

        # 4. The index last, rebuilt from the canonical representatives: a
        #    preserved index would keep naming the superseded atoms, and
        #    `NatFromRep` is what everything else asks.
        self._rebuild_nat_value_index(graph, canonical, remap, registry)
        self._sync_namespace_modules()
        if debug is M.truth_value and deferred:
            print(f"DEBUG: canonicalize: {deferred} Nats deferred (too large to build)", flush=True)
        return len(remap)

    def _canonicalize_seeds(self, state, graph):
        """Every object the restored state is reachable from, once each."""

        seeds = []
        seen = set()
        groups = [
            state.roots.values(),
            state.symbols.values(),
            state.id_to_obj.values(),
            [getattr(graph, name, None) for name in self.ROOT_NAMES],
        ]
        for group in groups:
            for obj in group:
                if obj is None or id(obj) in seen:
                    continue
                seen.add(id(obj))
                seeds.append(obj)
        return seeds

    def _substitute_canonical(self, seed, remap, seen):
        """Walk one restored object graph, re-pointing it through the map.

        Iterative and visited-bounded: the restored state is cyclic and this
        runs on every boot.
        """

        stack = [seed]
        while stack:
            obj = stack.pop()
            if obj is None or id(obj) in seen:
                continue
            seen.add(id(obj))
            if self._is_pair_object(obj) is M.truth_value:
                head = obj.head
                replacement = remap.get(id(head.value))
                if replacement is not None:
                    head.value = replacement
                tail = obj.tail
                replacement = remap.get(id(tail.value))
                if replacement is not None:
                    tail.value = replacement
                stack.append(head.value)
                stack.append(tail.value)
                continue
            if self._is_edge_object(obj) is M.truth_value:
                for field in ("inputs", "results", "value"):
                    current = getattr(obj, field, None)
                    if current is None:
                        continue
                    replacement = remap.get(id(current))
                    if replacement is not None:
                        setattr(obj, field, replacement)
                        current = replacement
                    stack.append(current)
                continue
            current = getattr(obj, "value", None)
            if current is None:
                continue
            replacement = remap.get(id(current))
            if replacement is not None:
                obj.value = replacement
                current = replacement
            try:
                current.id
            except Exception:
                continue
            stack.append(current)

    def _nat_index_by_value(self, index):
        """value text -> Nat, from the index the snapshot already carries."""

        by_value = {}
        empty = self.namespace["EmptyList"]
        walker = T.TreeEntries(index)()
        while M.IdentityCompare(walker, empty)() is M.false_value:
            entry = M.Head(walker)()
            key = M.Head(entry)()
            fact = M.Head(M.Tail(entry)())()
            walker = M.Tail(walker)()
            text = self._index_key_text(key)
            if text and text not in by_value:
                by_value[text] = fact
        return by_value

    def _index_key_text(self, key):
        """The decimal text of a Nat value key: a chain of digit Chars."""

        text = ""
        walker = key
        while M.IsPair(walker)() is M.truth_value:
            element = M.Head(walker)()
            try:
                text = text + str(element())
            except Exception:
                return ""
            walker = M.Tail(walker)()
        return text if text.isdigit() else ""

    def _rebuild_nat_value_index(self, graph, canonical, remap, registry):
        """Rebuild the Nat value index from the canonicalised entries.

        The index is rebuilt rather than substituted in place because it is
        a derived structure: what has to survive is the value -> Nat
        mapping, and the cheapest way to be sure of that is to reinsert the
        canonical representatives. If the restored index cannot be
        enumerated -- a shape `TreeEntries` does not read -- it is left
        exactly as the substitution left it, which is correct but not
        complete; wiping an unreadable index would be worse.
        """

        index = graph.nat_value_index
        empty = self.namespace["EmptyList"]

        # value text -> Nat, seeded from the restored index so that values
        # no record was marked for survive, then overlaid with the
        # canonical representatives so that a canonical value always wins.
        by_value = {}
        entries = T.TreeEntries(index)()
        walker = entries
        while M.IdentityCompare(walker, empty)() is M.false_value:
            entry = M.Head(walker)()
            key = M.Head(entry)()
            fact = M.Head(M.Tail(entry)())()
            walker = M.Tail(walker)()
            text = self._index_key_text(key)
            if not text:
                continue
            replacement = remap.get(id(fact))
            by_value[text] = fact if replacement is None else replacement
        for text in canonical:
            by_value[text] = canonical[text]

        from .math.peano import NatValueKey

        rebuilt = self.namespace["Tree"](empty)
        tree_insert = self.namespace["TreeInsert"]
        for text in by_value:
            try:
                rebuilt = tree_insert(
                    rebuilt,
                    NatValueKey(M.GMPRep(text))(),
                    by_value[text],
                    registry,
                )()
            except RecursionError:
                # An unindexable value is not worth losing the index over.
                continue
        index.value = rebuilt.value
        return len(by_value)


__all__ = [
    "SNAPSHOT_SYMBOL_NAMES",
    "SnapshotState",
    "SnapshotCodec",
    "SnapshotSaveDeadline",
    "SnapshotSaveTimeout",
]


def _runtime_namespace_for_restore():
    if "NatValueIndex" not in vars(M):
        M.NatValueIndex = M.Tree(M.EmptyList)
    namespace = dict(vars(M))
    namespace.update(vars(Hmod))
    namespace.update(vars(Lmod))
    namespace.update(vars(Pmod))
    namespace.update(vars(Gmod))
    namespace.update(vars(Xmod))
    namespace.update(vars(Rmod))
    namespace.update(vars(Smod))
    namespace.update(vars(Tmod))
    for name in (
        "Zero",
        "one",
        "two",
        "three",
        "four",
        "five",
        "six",
        "seven",
        "eight",
        "nine",
        "ZeroLabel",
        "SuccLabel",
        "PairLabel",
        "TreeLabel",
        "NatValueIndex",
        "DIGIT_0",
        "DIGIT_1",
        "DIGIT_2",
        "DIGIT_3",
        "DIGIT_4",
        "DIGIT_5",
        "DIGIT_6",
        "DIGIT_7",
        "DIGIT_8",
        "DIGIT_9",
        "DIGITS",
    ):
        if name in vars(M):
            namespace[name] = vars(M)[name]
    return namespace


def _restore_tree_root_from_snapshot_file(snapshot_path: str, root_name: str):
    namespace = _runtime_namespace_for_restore()
    codec = SnapshotCodec(namespace)
    state = codec.load(snapshot_path)
    loaded_registry = state.roots["constructor_registry"]
    rebuilt_registry = codec._restore_tree_root(state, "constructor_registry", loaded_registry)
    codec._restore_debug_root_name = root_name
    if root_name == "constructor_registry":
        return rebuilt_registry
    return codec._restore_tree_root(state, root_name, rebuilt_registry)


def _restore_tree_root_from_snapshot_file_worker(snapshot_path: str, root_name: str, output_path: str):
    try:
        result = _restore_tree_root_from_snapshot_file(snapshot_path, root_name)
        temp_path = output_path + ".tmp"
        with open(temp_path, "wb") as f:
            pickle.dump(("ok", result), f)
        os.replace(temp_path, output_path)
    except Exception as exc:
        temp_path = output_path + ".tmp"
        with open(temp_path, "wb") as f:
            pickle.dump(("err", str(exc)), f)
        os.replace(temp_path, output_path)
