from __future__ import annotations

import json
import multiprocessing
import os
import pickle
import sys
import tempfile
import time
import gmpy2

from . import machine as M
from . import context as Ctxmod
from . import constructors as C
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
    def __init__(self, roots, symbols, root_ids, symbol_ids, id_to_obj, records, needs_upgrade):
        self.roots = roots
        self.symbols = symbols
        self.root_ids = root_ids
        self.symbol_ids = symbol_ids
        self.id_to_obj = id_to_obj
        self.records = records
        self.needs_upgrade = needs_upgrade
        self.upgrade_roots = ()


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
    ]

    def __init__(self, namespace, symbol_names=None):
        self.namespace = namespace
        self.symbol_names = symbol_names if symbol_names is not None else SNAPSHOT_SYMBOL_NAMES
        self.obj_to_id = {}
        self.next_id = 1

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
        return self._ns_get("IsPair")(obj)() is self._ns_get("truth_value")

    def _is_edge_object(self, obj):
        try:
            marker = obj._snapshot_edge_marker
        except Exception:
            try:
                obj.inputs
                obj.results
            except Exception:
                return self._ns_get("false_value")
            return self._ns_get("truth_value")
        return self._ns_get("IdentityCompare")(marker, obj)() is self._ns_get("truth_value")

    def _captured_object_id(self, target):
        for obj in self.obj_to_id:
            oid = self.obj_to_id[obj]
            if obj is target:
                return oid
        return None

    def _scalar_payload(self, x):
        try:
            return self._encode_scalar(x)
        except (TypeError, ValueError):
            return None

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

    def _restore_tree_root(self, state, root_name, registry):
        if root_name not in state.root_ids:
            return self.namespace["EmptyList"]
        loaded_tree = state.roots.get(root_name, self.namespace["EmptyList"])
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

        num_workers = min(8, len(root_names), multiprocessing.cpu_count())
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
        try:
            snapshot_path = state.snapshot_path
        except AttributeError:
            snapshot_path = ""
        if not snapshot_path:
            loaded_registry = state.roots["constructor_registry"]
            return self._restore_tree_root(state, "constructor_registry", loaded_registry)

        ctx = multiprocessing.get_context("spawn")
        shard_count = min(8, multiprocessing.cpu_count())
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
        oid = self._captured_object_id(x)
        if oid is not None:
            return {"tag": "ref", "id": oid}
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
        if self._is_pair_object(obj):
            return (obj.head.value, obj.tail.value)
        if self._is_edge_object(obj) is self._ns_get("truth_value"):
            return (obj.inputs, obj.results, obj.value)
        if obj.value is None:
            return ()
        return (obj.value,)

    def _intern(self, obj):
        # Non-recursive intern. Use a machine Pair chain as the work queue so we
        # don't depend on Python recursion or Python container worklists.
        if obj is None:
            return None
        if self._scalar_payload(obj) is not None:
            return None

        existing = self._captured_object_id(obj)
        if existing is not None:
            return existing

        Pair = self.namespace["Pair"]
        EmptyList = self.namespace["EmptyList"]
        Head = self.namespace["Head"]
        Tail = self.namespace["Tail"]
        IdentityCompare = self.namespace["IdentityCompare"]
        truth_value = self.namespace["truth_value"]

        queue = Pair(obj, EmptyList)
        while IdentityCompare(queue, EmptyList)() is not truth_value:
            current = Head(queue)()
            queue = Tail(queue)()
            if current is None:
                continue
            if self._scalar_payload(current) is not None:
                continue
            if self._captured_object_id(current) is not None:
                continue

            oid = self.next_id
            self.next_id += 1
            self.obj_to_id[current] = oid

            for child in self._child_refs(current):
                if child is None:
                    continue
                if self._scalar_payload(child) is not None:
                    continue
                if self._captured_object_id(child) is not None:
                    continue
                queue = Pair(child, queue)

        return self._captured_object_id(obj)

    def _record_for(self, obj):
        oid = self.obj_to_id[obj]
        namespace_name = None
        for name in self.namespace:
            if self.namespace[name] is obj:
                namespace_name = name
                break
        if namespace_name is not None:
            return {
                "id": oid,
                "name": namespace_name,
            }

        if self._is_pair_object(obj):
            return {
                "id": oid,
                "head": self._encode_field(obj.head.value),
                "tail": self._encode_field(obj.tail.value),
            }

        if self._is_edge_object(obj) is self._ns_get("truth_value"):
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

        return {
            "id": oid,
            "value": self._encode_field(obj.value),
        }

    def _capture_from_roots(self, roots):
        self.obj_to_id = {}
        self.next_id = 1

        for name in roots:
            self._intern(roots[name])

        symbols = {}
        for name in self.symbol_names:
            if name in self.namespace:
                obj = self.namespace[name]
                symbols[name] = obj
                self._intern(obj)

        objects = [None] * len(self.obj_to_id)
        for obj in self.obj_to_id:
            oid = self.obj_to_id[obj]
            objects[oid - 1] = self._record_for(obj)

        root_ids = {}
        for name in roots:
            root_ids[name] = self.obj_to_id[roots[name]]

        symbol_ids = {}
        for name in symbols:
            symbol_ids[name] = self.obj_to_id[symbols[name]]

        return {
            "header": {"format": "hyge-proof-kernel", "version": 3, "protocol_version": 3},
            "roots": root_ids,
            "symbols": symbol_ids,
            "objects": objects,
        }

    def capture_objects(self, roots):
        return self._capture_from_roots(roots)

    def capture(self, graph, extra_roots=None):
        roots = {
            "constructor_registry": graph.constructor_registry,
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
        }
        if extra_roots is not None:
            for name in extra_roots:
                roots[name] = extra_roots[name]
        return self._capture_from_roots(roots)

    def save(self, graph, path):
        snapshot = self.capture(graph)
        tmp_path = path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
        return path

    def load_snapshot(self, snapshot):
        if snapshot["header"]["format"] != "hyge-proof-kernel":
            raise RuntimeError("Wrong snapshot format")
        if snapshot["header"]["version"] != 3:
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
        state = SnapshotState(
            roots,
            symbols,
            snapshot["roots"],
            snapshot["symbols"],
            id_to_obj,
            records,
            M.false_value,
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

    def activate(self, state, graph, debug=M.false_value):
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
                if debug is M.truth_value:
                    print("DEBUG: activate: saving upgraded snapshot...", flush=True)
                t_save0 = time.monotonic()
                self.save(graph, snapshot_path)
                if debug is M.truth_value:
                    print(f"DEBUG: activate: upgraded snapshot saved ({time.monotonic() - t_save0:.2f}s)", flush=True)

        return graph


__all__ = [
    "SNAPSHOT_SYMBOL_NAMES",
    "SnapshotState",
    "SnapshotCodec",
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
