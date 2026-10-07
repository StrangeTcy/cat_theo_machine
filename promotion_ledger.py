# ============================================================
# CL5 — Autonomous Closed-Loop Promotion Pipeline & Ledger
# Machine-native dual-ledger promotion state machine, ablation gates,
# rollback accounting, and end-to-end discovery orchestration.
# ============================================================
from . import evaluator as Eval
from . import invariance as Inv
from . import invariant_miner as Miner
from . import labels as L
from . import machine as M
from . import proof as P


class LedgerEntry(M.Edge):
    """
    Immutable promotion ledger record.
    inputs: [entry_id, promotion_class, candidate, receipt, provenance, version, status]
    results: Pair(LedgerEntryLabel, Pair(entry_id, ...))
    """

    def __init__(
        self,
        entry_id,
        promotion_class,
        candidate,
        receipt,
        provenance,
        version,
        status,
    ):
        self.entry_id = entry_id
        self.promotion_class = promotion_class
        self.candidate = candidate
        self.receipt = receipt
        self.provenance = provenance
        self.version = version
        self.status = status
        self.result = M.Pair(
            L.LedgerEntryLabel,
            M.Pair(
                entry_id,
                M.Pair(
                    promotion_class,
                    M.Pair(
                        candidate,
                        M.Pair(
                            receipt,
                            M.Pair(
                                provenance,
                                M.Pair(
                                    version,
                                    M.Pair(status, M.EmptyList),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                entry_id,
                M.Pair(
                    promotion_class,
                    M.Pair(
                        candidate,
                        M.Pair(
                            receipt,
                            M.Pair(
                                provenance,
                                M.Pair(
                                    version,
                                    M.Pair(status, M.EmptyList),
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


class LedgerEntryId(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(entry)())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LedgerEntryClass(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(entry)())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LedgerEntryCandidate(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(entry)())())())()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LedgerEntryReceipt(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(entry)())())())()
        )()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LedgerEntryProvenance(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(entry)())())())())()
        )()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LedgerEntryVersion(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(
            M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(entry)())())())())())()
        )()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class LedgerEntryStatus(M.Edge):
    def __init__(self, entry):
        self.result = M.Head(
            M.Tail(
                M.Tail(
                    M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(entry)())())())())()
                )()
            )()
        )()
        super().__init__(inputs=M.Pair(entry, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class PromotionLedger(M.Edge):
    """
    Dual-ledger containing separate branches for Proof Schemata and Search Policy Hints.
    inputs: [proof_schemata_entries, search_policy_entries, version_index]
    results: Pair(PromotionLedgerLabel, Pair(proof_schemata, Pair(search_policies, Pair(version, EmptyList))))
    """

    def __init__(
        self, proof_schemata_entries, search_policy_entries, version_index
    ):
        self.proof_schemata = proof_schemata_entries
        self.search_policies = search_policy_entries
        self.version_index = version_index
        self.result = M.Pair(
            L.PromotionLedgerLabel,
            M.Pair(
                proof_schemata_entries,
                M.Pair(
                    search_policy_entries,
                    M.Pair(version_index, M.EmptyList),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                proof_schemata_entries,
                M.Pair(
                    search_policy_entries,
                    M.Pair(version_index, M.EmptyList),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PromotionLedgerProofSchemata(M.Edge):
    def __init__(self, ledger):
        self.result = M.Head(M.Tail(ledger)())()
        super().__init__(
            inputs=M.Pair(ledger, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class PromotionLedgerSearchPolicies(M.Edge):
    def __init__(self, ledger):
        self.result = M.Head(M.Tail(M.Tail(ledger)())())()
        super().__init__(
            inputs=M.Pair(ledger, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class PromotionLedgerVersion(M.Edge):
    def __init__(self, ledger):
        self.result = M.Head(M.Tail(M.Tail(M.Tail(ledger)())())())()
        super().__init__(
            inputs=M.Pair(ledger, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class EmptyPromotionLedger(M.Edge):
    """
    Initializes a fresh, empty dual-ledger with version 0.
    """

    def __init__(self, registry):
        self.result = PromotionLedger(M.EmptyList, M.EmptyList, M.Zero)()
        super().__init__(
            inputs=M.Pair(registry, M.EmptyList), results=self.result
        )

    def __call__(self):
        return self.result


class QueryActivePromotions(M.Edge):
    """
    Filters and returns only active (non-revoked) entries for the given promotion class.
    """

    def __init__(self, ledger, promotion_class, registry):
        self.registry = registry
        self.result = self._query(ledger, promotion_class)
        super().__init__(
            inputs=M.Pair(
                ledger,
                M.Pair(
                    promotion_class,
                    M.Pair(registry, M.EmptyList),
                ),
            ),
            results=self.result,
        )

    def _query_rec(self, cur):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        entry = M.Head(cur)()
        status = LedgerEntryStatus(entry)()
        is_active = M.IdentityCompare(status, L.PromotionActiveLabel)()

        if is_active is M.truth_value:
            return M.Pair(entry, self._query_rec(M.Tail(cur)()))

        return self._query_rec(M.Tail(cur)())

    def _query(self, ledger, promotion_class):
        is_schema = (
            M.IdentityCompare(promotion_class, L.ProofSchemaPromotionLabel)()
        )
        if is_schema is M.truth_value:
            entries = PromotionLedgerProofSchemata(ledger)()
        else:
            entries = PromotionLedgerSearchPolicies(ledger)()

        return self._query_rec(entries)

    def __call__(self):
        return self.result


class SubmitCandidateForPromotion(M.Edge):
    """
    Multi-gate promotion state machine:
    1. Independent Checker B Verification Gate
    2. Performance Ablation & Non-Regression Gate
    3. Withheld Holdout Generalization Gate
    4. Invariant Preservation Gate (if certificate present)
    5. Atomic Ledger Commit & Version Advancement
    """

    def __init__(
        self,
        ledger,
        candidate,
        promotion_class,
        start_instance,
        goal_instance,
        baseline_cost,
        holdout_suite,
        provenance,
        rules,
        registry,
    ):
        self.registry = registry
        self.result = self._evaluate_and_promote(
            ledger,
            candidate,
            promotion_class,
            start_instance,
            goal_instance,
            baseline_cost,
            holdout_suite,
            provenance,
            rules,
        )
        super().__init__(
            inputs=M.Pair(
                ledger,
                M.Pair(
                    candidate,
                    M.Pair(
                        promotion_class,
                        M.Pair(
                            start_instance,
                            M.Pair(
                                goal_instance,
                                M.Pair(
                                    baseline_cost,
                                    M.Pair(
                                        holdout_suite,
                                        M.Pair(
                                            provenance,
                                            M.Pair(
                                                rules,
                                                M.Pair(
                                                    registry,
                                                    M.EmptyList,
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

    def _evaluate_and_promote(
        self,
        ledger,
        candidate,
        promotion_class,
        start_instance,
        goal_instance,
        baseline_cost,
        holdout_suite,
        provenance,
        rules,
    ):
        eval_res = Eval.EvaluateCandidateProof(
            candidate, start_instance, goal_instance, rules, self.registry
        )()
        eval_tag = M.Head(eval_res)()
        if (
            M.IdentityCompare(eval_tag, L.CandidateEvaluatedLabel)()
            is M.false_value
        ):
            return M.Pair(
                L.PromotionRejectedLabel,
                M.Pair(eval_tag, M.Tail(eval_res)()),
            )

        proof_receipt = M.Head(M.Tail(eval_res)())()

        ablation_res = Eval.AblationTrial(
            candidate, start_instance, goal_instance, rules, self.registry
        )()
        ablation_tag = M.Head(ablation_res)()
        if (
            M.IdentityCompare(ablation_tag, L.AblationVerifiedLabel)()
            is M.false_value
        ):
            return M.Pair(
                L.PromotionRejectedLabel,
                M.Pair(L.AblationRegressionLabel, M.Tail(ablation_res)()),
            )

        ablation_status = M.Head(M.Tail(M.Tail(ablation_res)())())()
        if (
            M.IdentityCompare(ablation_status, L.ProvedLabel)()
            is M.false_value
        ):
            return M.Pair(
                L.PromotionRejectedLabel,
                M.Pair(L.AblationRegressionLabel, M.Tail(ablation_res)()),
            )

        holdout_res = Eval.EvaluateHoldoutSuite(
            candidate, holdout_suite, rules, self.registry
        )()
        holdout_tag = M.Head(holdout_res)()
        if (
            M.IdentityCompare(holdout_tag, L.HoldoutSuiteResultLabel)()
            is M.false_value
        ):
            return M.Pair(
                L.PromotionRejectedLabel,
                M.Pair(L.HoldoutRegressionLabel, M.Tail(holdout_res)()),
            )

        passed_list = M.Head(M.Tail(holdout_res)())()
        failed_list = M.Head(M.Tail(M.Tail(holdout_res)())())()
        if M.IdentityCompare(failed_list, M.EmptyList)() is M.false_value:
            return M.Pair(
                L.PromotionRejectedLabel,
                M.Pair(
                    L.HoldoutRegressionLabel,
                    M.Pair(failed_list, M.EmptyList),
                ),
            )

        has_provenance = M.IdentityCompare(provenance, M.EmptyList)()
        if has_provenance is M.false_value:
            prov_tag = M.Head(provenance)()
            if (
                M.IdentityCompare(prov_tag, L.InvariantCertificateLabel)()
                is M.truth_value
            ):
                cert = provenance
                phi = Miner.InvariantCertificatePhi(cert)()
                pres_res = Miner.CheckInvariantPreservationAcrossRules(
                    phi, rules, self.registry
                )()
                is_pres = M.Head(pres_res)()
                if (
                    M.IdentityCompare(is_pres, M.truth_value)()
                    is M.false_value
                ):
                    return M.Pair(
                        L.PromotionRejectedLabel,
                        M.Pair(
                            L.InvariantRefutedLabel,
                            M.Tail(pres_res)(),
                        ),
                    )

        current_version = PromotionLedgerVersion(ledger)()
        succ_res = M.Succ(current_version, self.registry)()
        next_version = M.Head(succ_res)()
        entry_id = M.Atom()

        new_entry = LedgerEntry(
            entry_id,
            promotion_class,
            candidate,
            proof_receipt,
            provenance,
            next_version,
            L.PromotionActiveLabel,
        )()

        cur_schemata = PromotionLedgerProofSchemata(ledger)()
        cur_policies = PromotionLedgerSearchPolicies(ledger)()

        is_schema = (
            M.IdentityCompare(promotion_class, L.ProofSchemaPromotionLabel)()
        )
        if is_schema is M.truth_value:
            updated_schemata = M.Pair(new_entry, cur_schemata)
            updated_policies = cur_policies
        else:
            updated_schemata = cur_schemata
            updated_policies = M.Pair(new_entry, cur_policies)

        new_ledger = PromotionLedger(
            updated_schemata, updated_policies, next_version
        )()

        return M.Pair(
            L.PromotionApprovedLabel,
            M.Pair(
                new_ledger,
                M.Pair(new_entry, M.EmptyList),
            ),
        )

    def __call__(self):
        return self.result


class RollbackPromotion(M.Edge):
    """
    Rolls back / revokes an existing promotion entry from the ledger.
    Marks status as PromotionRevokedLabel with revocation provenance and advances ledger version.
    """

    def __init__(self, ledger, target_entry_id, revocation_reason, registry):
        self.registry = registry
        self.result = self._rollback(
            ledger, target_entry_id, revocation_reason
        )
        super().__init__(
            inputs=M.Pair(
                ledger,
                M.Pair(
                    target_entry_id,
                    M.Pair(
                        revocation_reason,
                        M.Pair(registry, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def _rollback_entries_rec(
        self, cur, target_entry_id, next_version, reason
    ):
        if M.IdentityCompare(cur, M.EmptyList)() is M.truth_value:
            return M.Pair(
                M.false_value,
                M.Pair(M.EmptyList, M.Pair(M.EmptyList, M.EmptyList)),
            )

        entry = M.Head(cur)()
        eid = LedgerEntryId(entry)()
        is_match = M.IdentityCompare(eid, target_entry_id)()

        if is_match is M.truth_value:
            eclass = LedgerEntryClass(entry)()
            ecand = LedgerEntryCandidate(entry)()
            ereceipt = LedgerEntryReceipt(entry)()
            eprov = M.Pair(reason, LedgerEntryProvenance(entry)())
            revoked_entry = LedgerEntry(
                eid,
                eclass,
                ecand,
                ereceipt,
                eprov,
                next_version,
                L.PromotionRevokedLabel,
            )()
            rest_entries = M.Tail(cur)()
            return M.Pair(
                M.truth_value,
                M.Pair(
                    M.Pair(revoked_entry, rest_entries),
                    M.Pair(revoked_entry, M.EmptyList),
                ),
            )

        sub_res = self._rollback_entries_rec(
            M.Tail(cur)(), target_entry_id, next_version, reason
        )
        found = M.Head(sub_res)()
        sub_list = M.Head(M.Tail(sub_res)())()
        rev_item = M.Head(M.Tail(M.Tail(sub_res)())())()

        return M.Pair(
            found,
            M.Pair(
                M.Pair(entry, sub_list),
                M.Pair(rev_item, M.EmptyList),
            ),
        )

    def _rollback(self, ledger, target_entry_id, revocation_reason):
        current_version = PromotionLedgerVersion(ledger)()
        succ_res = M.Succ(current_version, self.registry)()
        next_version = M.Head(succ_res)()

        cur_schemata = PromotionLedgerProofSchemata(ledger)()
        cur_policies = PromotionLedgerSearchPolicies(ledger)()

        res_s = self._rollback_entries_rec(
            cur_schemata, target_entry_id, next_version, revocation_reason
        )
        found_s = M.Head(res_s)()

        if found_s is M.truth_value:
            new_schemata = M.Head(M.Tail(res_s)())()
            revoked_entry = M.Head(M.Tail(M.Tail(res_s)())())()
            new_ledger = PromotionLedger(
                new_schemata, cur_policies, next_version
            )()
            return M.Pair(
                L.PromotionRevokedLabel,
                M.Pair(
                    new_ledger,
                    M.Pair(revoked_entry, M.EmptyList),
                ),
            )

        res_p = self._rollback_entries_rec(
            cur_policies, target_entry_id, next_version, revocation_reason
        )
        found_p = M.Head(res_p)()

        if found_p is M.truth_value:
            new_policies = M.Head(M.Tail(res_p)())()
            revoked_entry = M.Head(M.Tail(M.Tail(res_p)())())()
            new_ledger = PromotionLedger(
                cur_schemata, new_policies, next_version
            )()
            return M.Pair(
                L.PromotionRevokedLabel,
                M.Pair(
                    new_ledger,
                    M.Pair(revoked_entry, M.EmptyList),
                ),
            )

        return M.Pair(M.false_value, M.EmptyList)

    def __call__(self):
        return self.result


class ExecuteAutonomousDiscoveryCycle(M.Edge):
    """
    End-to-end verified closed loop:
    Trace -> Invariant Miner -> Candidate Macro -> Evaluation & Holdouts -> Checker B -> Ledger Commit
    """

    def __init__(
        self,
        training_trace,
        start_instance,
        goal_instance,
        domain_rules,
        candidate_templates,
        macro_id,
        macro_plan,
        baseline_cost,
        holdout_suite,
        promotion_class,
        ledger,
        registry,
    ):
        self.registry = registry
        self.result = self._run_cycle(
            training_trace,
            start_instance,
            goal_instance,
            domain_rules,
            candidate_templates,
            macro_id,
            macro_plan,
            baseline_cost,
            holdout_suite,
            promotion_class,
            ledger,
        )
        super().__init__(
            inputs=M.Pair(
                training_trace,
                M.Pair(
                    start_instance,
                    M.Pair(
                        goal_instance,
                        M.Pair(
                            domain_rules,
                            M.Pair(
                                candidate_templates,
                                M.Pair(
                                    macro_id,
                                    M.Pair(
                                        macro_plan,
                                        M.Pair(
                                            baseline_cost,
                                            M.Pair(
                                                holdout_suite,
                                                M.Pair(
                                                    promotion_class,
                                                    M.Pair(
                                                        ledger,
                                                        M.Pair(
                                                            registry,
                                                            M.EmptyList,
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

    def _run_cycle(
        self,
        training_trace,
        start_instance,
        goal_instance,
        domain_rules,
        candidate_templates,
        macro_id,
        macro_plan,
        baseline_cost,
        holdout_suite,
        promotion_class,
        ledger,
    ):
        has_templates = M.IdentityCompare(candidate_templates, M.EmptyList)()
        if has_templates is M.false_value:
            macro_mining_res = Miner.MineInvariantToCandidateMacro(
                training_trace,
                start_instance,
                goal_instance,
                domain_rules,
                candidate_templates,
                macro_id,
                macro_plan,
                self.registry,
            )()
            macro_tag = M.Head(macro_mining_res)()

            if (
                M.IdentityCompare(macro_tag, L.CandidateMacroLabel)()
                is M.truth_value
            ):
                candidate_macro = M.Head(M.Tail(macro_mining_res)())()
                provenance = M.Head(M.Tail(M.Tail(macro_mining_res)())())()
            else:
                candidate_macro = Eval.CandidateMacro(
                    macro_id, start_instance, goal_instance, macro_plan
                )()
                provenance = M.EmptyList
        else:
            candidate_macro = Eval.CandidateMacro(
                macro_id, start_instance, goal_instance, macro_plan
            )()
            provenance = M.EmptyList

        submit_res = SubmitCandidateForPromotion(
            ledger,
            candidate_macro,
            promotion_class,
            start_instance,
            goal_instance,
            baseline_cost,
            holdout_suite,
            provenance,
            domain_rules,
            self.registry,
        )()
        submit_tag = M.Head(submit_res)()

        if (
            M.IdentityCompare(submit_tag, L.PromotionApprovedLabel)()
            is M.false_value
        ):
            return submit_res

        new_ledger = M.Head(M.Tail(submit_res)())()
        promoted_entry = M.Head(M.Tail(M.Tail(submit_res)())())()

        return M.Pair(
            L.AutonomousCycleCompletedLabel,
            M.Pair(
                new_ledger,
                M.Pair(promoted_entry, M.EmptyList),
            ),
        )

    def __call__(self):
        return self.result


__all__ = (
    "LedgerEntry",
    "LedgerEntryId",
    "LedgerEntryClass",
    "LedgerEntryCandidate",
    "LedgerEntryReceipt",
    "LedgerEntryProvenance",
    "LedgerEntryVersion",
    "LedgerEntryStatus",
    "PromotionLedger",
    "PromotionLedgerProofSchemata",
    "PromotionLedgerSearchPolicies",
    "PromotionLedgerVersion",
    "EmptyPromotionLedger",
    "QueryActivePromotions",
    "SubmitCandidateForPromotion",
    "RollbackPromotion",
    "ExecuteAutonomousDiscoveryCycle",
)
