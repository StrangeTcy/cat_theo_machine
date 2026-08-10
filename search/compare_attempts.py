from __future__ import annotations

from .. import machine as M
from ..heuristics import *
from ..proof import *
from ..proof import _debug
from .model import *


class _ComparisonAttemptMixin:
    def _attempt_total_value(self, attempt):
        total_cost = SearchAttemptTotalCost(attempt)()
        return M.TotalCostValue(total_cost)()

    def _attempt_better(self, attempt, best_attempt):
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return M.truth_value
        attempt_status = SearchAttemptStatus(attempt)()
        best_status = SearchAttemptStatus(best_attempt)()
        attempt_succeeded = M.IdentityCompare(attempt_status, SearchSuccessLabel)()
        best_succeeded = M.IdentityCompare(best_status, SearchSuccessLabel)()
        if attempt_succeeded is M.truth_value:
            if best_succeeded is M.false_value:
                return M.truth_value
        if attempt_succeeded is M.false_value:
            if best_succeeded is M.truth_value:
                return M.false_value
        return M.NatLess(self._attempt_total_value(attempt), self._attempt_total_value(best_attempt), self.registry)()

    def _zero_proof_cost(self):
        return ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()

    def _zero_search_cost(self, outcome):
        search_cost_pair = BuildSearchCost(M.EmptyList, M.Zero, M.Zero, M.Zero, outcome, self.registry)()
        search_cost = M.Head(search_cost_pair)()
        self.registry = M.Head(M.Tail(search_cost_pair)())()
        return search_cost

    def _mode_attempt_from_plan(self, heuristic, status, plan, search_cost):
        derivation = M.EmptyList
        proof_cost = self._zero_proof_cost()
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
            derivation_pair = BuildDerivation(self.start, plan, self.registry)()
            derivation = M.Head(derivation_pair)()
            self.registry = M.Head(M.Tail(derivation_pair)())()
            if M.Compare(derivation, M.EmptyList)() is M.false_value:
                proof_cost_pair = DerivationCost(derivation, self.registry)()
                proof_cost = M.Head(proof_cost_pair)()
                self.registry = M.Head(M.Tail(proof_cost_pair)())()
        total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, self.registry)()
        total_cost = M.Head(total_cost_pair)()
        self.registry = M.Head(M.Tail(total_cost_pair)())()
        return SearchAttempt(
            self.start,
            self.goal,
            heuristic,
            status,
            derivation,
            proof_cost,
            search_cost,
            total_cost,
        )()

    def _attempt_better_with_elapsed(self, attempt, elapsed_seconds, best_attempt, best_elapsed_seconds):
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return M.truth_value
        attempt_status = SearchAttemptStatus(attempt)()
        best_status = SearchAttemptStatus(best_attempt)()
        attempt_succeeded = M.IdentityCompare(attempt_status, SearchSuccessLabel)()
        best_succeeded = M.IdentityCompare(best_status, SearchSuccessLabel)()
        if attempt_succeeded is M.truth_value:
            if best_succeeded is M.false_value:
                return M.truth_value
        if attempt_succeeded is M.false_value:
            if best_succeeded is M.truth_value:
                return M.false_value
        attempt_total = self._attempt_total_value(attempt)
        best_total = self._attempt_total_value(best_attempt)
        if M.NatLess(attempt_total, best_total, self.registry)() is M.truth_value:
            return M.truth_value
        if M.NatLess(best_total, attempt_total, self.registry)() is M.truth_value:
            return M.false_value
        if best_elapsed_seconds is None:
            return M.truth_value
        if best_elapsed_seconds - elapsed_seconds > 0.0:
            return M.truth_value
        if elapsed_seconds - best_elapsed_seconds > 0.0:
            return M.false_value
        attempt_search_cost = SearchAttemptSearchCost(attempt)()
        best_search_cost = SearchAttemptSearchCost(best_attempt)()
        attempt_expanded = SearchCostExpanded(attempt_search_cost)()
        best_expanded = SearchCostExpanded(best_search_cost)()
        if M.NatLess(attempt_expanded, best_expanded, self.registry)() is M.truth_value:
            return M.truth_value
        if M.NatLess(best_expanded, attempt_expanded, self.registry)() is M.truth_value:
            return M.false_value
        attempt_peak = SearchCostFrontierPeak(attempt_search_cost)()
        best_peak = SearchCostFrontierPeak(best_search_cost)()
        if M.NatLess(attempt_peak, best_peak, self.registry)() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _comparison_result_plan(self, result_value):
        if M.Compare(result_value, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if IsDerivation(result_value, self.registry)() is M.truth_value:
            return self._plan_from_derivation_steps(DerivationSteps(result_value, self.registry)())
        return result_value

    def _comparison_result_derivation(self, result_value):
        if M.Compare(result_value, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        if IsDerivation(result_value, self.registry)() is M.truth_value:
            return result_value
        derivation_pair = BuildDerivation(self.start, result_value, self.registry)()
        derivation = M.Head(derivation_pair)()
        self.registry = M.Head(M.Tail(derivation_pair)())()
        return derivation

    def _comparison_state_attempt_or_current(self, state):
        job = self._comparison_state_job(state)
        status = self._comparison_state_status(state)
        mode = self._comparison_state_mode(state)
        heuristic = self._heuristic_for_mode(mode)

        result_value = SearchJobResultPlan(job)()
        plan = result_value
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.false_value:
            plan = M.EmptyList
        else:
            plan = self._comparison_result_plan(result_value)

        search_cost_pair = BuildSearchCost(
            plan,
            SearchJobExpanded(job)(),
            SearchJobGenerated(job)(),
            SearchJobFrontierPeak(job)(),
            status,
            self.registry,
        )()
        search_cost = M.Head(search_cost_pair)()
        self.registry = M.Head(M.Tail(search_cost_pair)())()

        proof_cost = ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
        derivation = M.EmptyList
        if M.IdentityCompare(status, SearchSuccessLabel)() is M.truth_value:
            derivation = self._comparison_result_derivation(result_value)
            if M.Compare(derivation, M.EmptyList)() is M.false_value:
                _debug(
                    "search-compare: computing derivation cost for "
                    + SearchModeText(mode)()
                )
                proof_cost_pair = DerivationCost(derivation, self.registry)()
                proof_cost = M.Head(proof_cost_pair)()
                self.registry = M.Head(M.Tail(proof_cost_pair)())()

        total_cost_pair = BuildTotalCost(proof_cost, search_cost, heuristic, self.registry)()
        total_cost = M.Head(total_cost_pair)()
        self.registry = M.Head(M.Tail(total_cost_pair)())()

        return SearchAttempt(
            self.start,
            self.goal,
            heuristic,
            status,
            derivation,
            proof_cost,
            search_cost,
            total_cost,
        )()

    def _finished_attempts(self, states, acc):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return self._reverse(acc, M.EmptyList)
        state = M.Head(states)()
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.truth_value:
            return self._finished_attempts(M.Tail(states)(), acc)
        _debug(
            "search-compare: finalizing attempt for "
            + SearchModeText(self._comparison_state_mode(state))()
            + " status="
            + SearchStatusText(self._comparison_state_status(state))()
        )
        attempt = self._comparison_state_attempt_or_current(state)
        _debug(
            "search-compare: attempt ready root="
            + self._comparison_root_fast_path_result_text(state)
            + " "
            + self._attempt_summary_text(attempt)
        )
        return self._finished_attempts(M.Tail(states)(), M.Pair(attempt, acc))

    def _best_attempt_in_attempts(self, attempts, best_attempt):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return best_attempt
        attempt = M.Head(attempts)()
        next_best = best_attempt
        if self._attempt_better(attempt, best_attempt) is M.truth_value:
            next_best = attempt
        return self._best_attempt_in_attempts(M.Tail(attempts)(), next_best)

    def _best_finished_attempt(self, states, best_attempt):
        if M.IdentityCompare(states, M.EmptyList)() is M.truth_value:
            return best_attempt
        state = M.Head(states)()
        next_best = best_attempt
        if M.IdentityCompare(self._comparison_state_status(state), SearchRunningLabel)() is M.false_value:
            attempt = self._comparison_state_attempt_or_current(state)
            if self._attempt_better(attempt, best_attempt) is M.truth_value:
                next_best = attempt
        return self._best_finished_attempt(M.Tail(states)(), next_best)

    def _best_finished_attempt_text(self, states):
        best_attempt = self._best_finished_attempt(states, M.EmptyList)
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return "none yet"
        return (
            SearchModeText(HeuristicSearchMode(SearchAttemptHeuristic(best_attempt)())())()
            + " status="
            + SearchStatusText(SearchAttemptStatus(best_attempt)())()
            + " total="
            + self._nat_text(self._attempt_total_value(best_attempt))
        )

    def _attempt_summary_text(self, attempt):
        heuristic = SearchAttemptHeuristic(attempt)()
        mode = HeuristicSearchMode(heuristic)()
        return (
            SearchModeText(mode)()
            + " status="
            + SearchStatusText(SearchAttemptStatus(attempt)())()
            + " total="
            + self._nat_text(TotalCostValue(SearchAttemptTotalCost(attempt)())())
            + " proof="
            + self._nat_text(Pmod.ProofCostValue(SearchAttemptProofCost(attempt)())())
            + " search="
            + self._nat_text(SearchCostValue(SearchAttemptSearchCost(attempt)())())
        )

    def _attempts_summary_text(self, attempts):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return "none"
        here = self._attempt_summary_text(M.Head(attempts)())
        rest = self._attempts_summary_text(M.Tail(attempts)())
        if rest == "none":
            return here
        return here + " | " + rest

    def _attempt_ties_best(self, attempt, best_attempt):
        if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.TermEqual(SearchAttemptStatus(attempt)(), SearchAttemptStatus(best_attempt)())() is M.false_value:
            return M.false_value
        if M.TermEqual(TotalCostValue(SearchAttemptTotalCost(attempt)())(), TotalCostValue(SearchAttemptTotalCost(best_attempt)())())() is M.false_value:
            return M.false_value
        return M.truth_value

    def _best_attempt_modes_text(self, attempts, best_attempt):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return ""
        attempt = M.Head(attempts)()
        rest = self._best_attempt_modes_text(M.Tail(attempts)(), best_attempt)
        if self._attempt_ties_best(attempt, best_attempt) is M.false_value:
            return rest
        here = SearchModeText(HeuristicSearchMode(SearchAttemptHeuristic(attempt)())())()
        if rest == "":
            return here
        return here + ", " + rest

    def _best_attempt_mode_count(self, attempts, best_attempt):
        if M.IdentityCompare(attempts, M.EmptyList)() is M.truth_value:
            return M.Zero
        rest = self._best_attempt_mode_count(M.Tail(attempts)(), best_attempt)
        if self._attempt_ties_best(M.Head(attempts)(), best_attempt) is M.false_value:
            return rest
        return self._succ_nat_local(rest)


    def _comparison_has_usable_best_attempt(self, comparison):
        if M.Compare(comparison, M.EmptyList)() is M.truth_value:
            return M.false_value
        if M.Compare(SearchComparisonBestAttempt(comparison)(), M.EmptyList)() is M.truth_value:
            return M.false_value
        return M.truth_value

    def _comparison_should_rerun(self, comparison):
        if self._comparison_has_usable_best_attempt(comparison) is M.truth_value:
            return M.false_value
        best_attempt = SearchComparisonBestAttempt(comparison)()
        outcome = SearchComparisonOutcome(comparison)()
        if M.Compare(outcome, M.EmptyList)() is M.truth_value:
            if M.Compare(best_attempt, M.EmptyList)() is M.truth_value:
                outcome = SearchFailureLabel
            else:
                outcome = SearchAttemptStatus(best_attempt)()
        if M.OrAtom(
            M.OrAtom(M.IdentityCompare(outcome, SearchPausedLabel)(), M.IdentityCompare(outcome, SearchTimedOutLabel)())(),
            M.IdentityCompare(outcome, SearchAbortedByUserLabel)(),
        )() is M.truth_value:
            return M.truth_value
        return M.false_value

    def _beam_width(self, mode):
        width = HeuristicBeamWidth(self.heuristic)()
        if M.IdentityCompare(mode, BeamLabel)() is M.false_value:
            return width
        if M.NatEq(width, M.Zero, self.registry)() is M.truth_value:
            return M.three
        return width

    def _heuristic_for_mode(self, mode):
        return Heuristic(
            mode,
            HeuristicRuleOrder(self.heuristic)(),
            self._beam_width(mode),
            HeuristicAlpha(self.heuristic)(),
            HeuristicBeta(self.heuristic)(),
            HeuristicCanonicalStrength(self.heuristic)(),
        )()

    def _plan_from_derivation_steps(self, steps):
        if M.IdentityCompare(steps, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        step = M.Head(steps)()
        action = StepAction(step, self.registry)()
        return M.Pair(action, self._plan_from_derivation_steps(M.Tail(steps)()))



def sync_from_namespace(namespace):
    for name in (
        "BeamLabel",
        "SearchSuccessLabel",
        "SearchFailureLabel",
        "SearchRunningLabel",
        "SearchPausedLabel",
        "SearchTimedOutLabel",
        "SearchAbortedByUserLabel",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [name for name in globals() if not name.startswith("_") or name.startswith("_ComparisonAttemptMixin")]
