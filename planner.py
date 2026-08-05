from __future__ import annotations

from . import labels as L
from . import machine as M
from . import proof as P
from . import search as S


class PlannerProblem(M.Edge):
    def __init__(self, mathematical_state, goal, rules, heuristic):
        self.result = M.Pair(
            L.PlannerProblemLabel,
            M.Pair(
                M.Zero,
                M.Pair(
                    mathematical_state,
                    M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.Pair(M.Zero, M.EmptyList)))),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                mathematical_state,
                M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.EmptyList))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PlannerObligation(M.Edge):
    def __init__(self, obligation_id, problem_id, goal, status, selected_rule, bindings):
        self.result = M.Pair(
            L.PlannerObligationLabel,
            M.Pair(
                obligation_id,
                M.Pair(
                    problem_id,
                    M.Pair(goal, M.Pair(status, M.Pair(selected_rule, M.Pair(bindings, M.EmptyList)))),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                obligation_id,
                M.Pair(
                    problem_id,
                    M.Pair(goal, M.Pair(status, M.Pair(selected_rule, M.Pair(bindings, M.EmptyList)))),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PlannerDependency(M.Edge):
    def __init__(self, parent_id, child_id):
        self.result = M.Pair(
            L.PlannerDependencyLabel,
            M.Pair(parent_id, M.Pair(child_id, M.EmptyList)),
        )
        super().__init__(inputs=M.Pair(parent_id, M.Pair(child_id, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PlannerJob(M.Edge):
    def __init__(self, problem_id, obligation_id, search_job):
        self.result = M.Pair(
            L.PlannerJobLabel,
            M.Pair(problem_id, M.Pair(obligation_id, M.Pair(search_job, M.EmptyList))),
        )
        super().__init__(
            inputs=M.Pair(problem_id, M.Pair(obligation_id, M.Pair(search_job, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PlannerStateRecord(M.Edge):
    def __init__(self, problems, obligations, dependencies, jobs, next_obligation_id, registry):
        self.result = M.Pair(
            problems,
            M.Pair(
                obligations,
                M.Pair(
                    dependencies,
                    M.Pair(jobs, M.Pair(next_obligation_id, M.Pair(registry, M.EmptyList))),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                problems,
                M.Pair(
                    obligations,
                    M.Pair(
                        dependencies,
                        M.Pair(jobs, M.Pair(next_obligation_id, M.Pair(registry, M.EmptyList))),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PlannerState(M.Edge):
    def __init__(self, problem, registry):
        fields = M.Tail(problem)()
        problem_id = M.Head(fields)()
        fields = M.Tail(fields)()
        mathematical_state = M.Head(fields)()
        fields = M.Tail(fields)()
        goal = M.Head(fields)()
        fields = M.Tail(fields)()
        rules = M.Head(fields)()
        fields = M.Tail(fields)()
        heuristic = M.Head(fields)()
        root_id = M.Head(M.Tail(fields)())()
        root = PlannerObligation(
            root_id,
            problem_id,
            goal,
            L.PendingLabel,
            M.EmptyList,
            M.EmptyList,
        )()
        next_pair = M.Succ(root_id, registry)()
        next_id = M.Head(next_pair)()
        next_registry = M.Head(M.Tail(next_pair)())()
        canonical_problem = M.Pair(
            L.PlannerProblemLabel,
            M.Pair(
                problem_id,
                M.Pair(
                    mathematical_state,
                    M.Pair(goal, M.Pair(rules, M.Pair(heuristic, M.Pair(root_id, M.EmptyList)))),
                ),
            ),
        )
        self.result = PlannerStateRecord(
            M.Pair(canonical_problem, M.EmptyList),
            M.Pair(root, M.EmptyList),
            M.EmptyList,
            M.EmptyList,
            next_id,
            next_registry,
        )()
        super().__init__(inputs=M.Pair(problem, M.Pair(registry, M.EmptyList)), results=self.result)

    def __call__(self):
        return self.result


class PlannerStep(M.Edge):
    def __init__(self, graph, state, step_budget):
        fields = state
        problems = M.Head(fields)()
        fields = M.Tail(fields)()
        obligations = M.Head(fields)()
        fields = M.Tail(fields)()
        dependencies = M.Head(fields)()
        fields = M.Tail(fields)()
        jobs = M.Head(fields)()
        fields = M.Tail(fields)()
        next_obligation_id = M.Head(fields)()
        registry = M.Head(M.Tail(fields)())()
        changed = M.false_value

        current_jobs = jobs
        selected_planner_job = M.EmptyList
        while M.IdentityCompare(current_jobs, M.EmptyList)() is M.false_value:
            candidate = M.Head(current_jobs)()
            candidate_fields = M.Tail(candidate)()
            candidate_fields = M.Tail(candidate_fields)()
            candidate_fields = M.Tail(candidate_fields)()
            candidate_search_job = M.Head(candidate_fields)()
            candidate_status = S.SearchJobStatus(candidate_search_job)()
            if M.IdentityCompare(candidate_status, S.SearchRunningLabel)() is M.truth_value:
                burst_pair = S.SearchBurst(graph, candidate_search_job, step_budget, registry)()
                stepped_search_job = M.Head(burst_pair)()
                registry = M.Head(M.Tail(burst_pair)())()
                selected_fields = M.Tail(candidate)()
                selected_problem_id = M.Head(selected_fields)()
                selected_fields = M.Tail(selected_fields)()
                selected_obligation_id = M.Head(selected_fields)()
                selected_planner_job = PlannerJob(
                    selected_problem_id,
                    selected_obligation_id,
                    stepped_search_job,
                )()
                rebuilt_jobs = M.EmptyList
                remaining_jobs = jobs
                while M.IdentityCompare(remaining_jobs, M.EmptyList)() is M.false_value:
                    existing_planner_job = M.Head(remaining_jobs)()
                    existing_fields = M.Tail(existing_planner_job)()
                    existing_fields = M.Tail(existing_fields)()
                    existing_obligation_id = M.Head(existing_fields)()
                    if M.TermEqual(existing_obligation_id, selected_obligation_id)() is M.truth_value:
                        rebuilt_jobs = M.Pair(selected_planner_job, rebuilt_jobs)
                    else:
                        rebuilt_jobs = M.Pair(existing_planner_job, rebuilt_jobs)
                    remaining_jobs = M.Tail(remaining_jobs)()
                jobs = M.EmptyList
                while M.IdentityCompare(rebuilt_jobs, M.EmptyList)() is M.false_value:
                    jobs = M.Pair(M.Head(rebuilt_jobs)(), jobs)
                    rebuilt_jobs = M.Tail(rebuilt_jobs)()
                changed = M.truth_value
                break
            if M.OrAtom(
                M.IdentityCompare(candidate_status, S.SearchSuccessLabel)(),
                M.IdentityCompare(candidate_status, S.SearchFailureLabel)(),
            )() is M.truth_value:
                selected_planner_job = candidate
                break
            current_jobs = M.Tail(current_jobs)()

        if M.IdentityCompare(selected_planner_job, M.EmptyList)() is M.false_value:
            selected_fields = M.Tail(selected_planner_job)()
            selected_problem_id = M.Head(selected_fields)()
            selected_fields = M.Tail(selected_fields)()
            selected_obligation_id = M.Head(selected_fields)()
            selected_search_job = M.Head(M.Tail(selected_fields)())()
            selected_status = S.SearchJobStatus(selected_search_job)()
            if M.OrAtom(
                M.IdentityCompare(selected_status, S.SearchSuccessLabel)(),
                M.IdentityCompare(selected_status, S.SearchFailureLabel)(),
            )() is M.truth_value:
                obligation_status = L.FailedLabel
                if M.IdentityCompare(selected_status, S.SearchSuccessLabel)() is M.truth_value:
                    obligation_status = L.ProvedLabel
                    selected_problem = M.EmptyList
                    remaining_problems = problems
                    while M.IdentityCompare(remaining_problems, M.EmptyList)() is M.false_value:
                        candidate_problem = M.Head(remaining_problems)()
                        candidate_problem_id = M.Head(M.Tail(candidate_problem)())()
                        if M.TermEqual(candidate_problem_id, selected_problem_id)() is M.truth_value:
                            selected_problem = candidate_problem
                            break
                        remaining_problems = M.Tail(remaining_problems)()
                    if M.IdentityCompare(selected_problem, M.EmptyList)() is M.false_value:
                        problem_fields = M.Tail(selected_problem)()
                        problem_id = M.Head(problem_fields)()
                        problem_fields = M.Tail(problem_fields)()
                        mathematical_state = M.Head(problem_fields)()
                        problem_fields = M.Tail(problem_fields)()
                        problem_goal = M.Head(problem_fields)()
                        problem_fields = M.Tail(problem_fields)()
                        problem_rules = M.Head(problem_fields)()
                        problem_fields = M.Tail(problem_fields)()
                        problem_heuristic = M.Head(problem_fields)()
                        problem_root = M.Head(M.Tail(problem_fields)())()
                        result_plan = S.SearchJobResultPlan(selected_search_job)()
                        if M.IdentityCompare(result_plan, M.EmptyList)() is M.false_value:
                            derivation_pair = P.BuildDerivation(mathematical_state, result_plan, registry)()
                            derivation = M.Head(derivation_pair)()
                            registry = M.Head(M.Tail(derivation_pair)())()
                            if M.IdentityCompare(derivation, M.EmptyList)() is M.false_value:
                                mathematical_state = P.DerivationEnd(derivation, registry)()
                                graph._replace_context(constructors=registry)
                                graph.add_derivation(
                                    S.SearchJobStart(selected_search_job)(),
                                    S.SearchJobGoal(selected_search_job)(),
                                    derivation,
                                )
                        updated_problem = M.Pair(
                            L.PlannerProblemLabel,
                            M.Pair(
                                problem_id,
                                M.Pair(
                                    mathematical_state,
                                    M.Pair(
                                        problem_goal,
                                        M.Pair(problem_rules, M.Pair(problem_heuristic, M.Pair(problem_root, M.EmptyList))),
                                    ),
                                ),
                            ),
                        )
                        reversed_problems = M.EmptyList
                        remaining_problems = problems
                        while M.IdentityCompare(remaining_problems, M.EmptyList)() is M.false_value:
                            candidate_problem = M.Head(remaining_problems)()
                            candidate_problem_id = M.Head(M.Tail(candidate_problem)())()
                            if M.TermEqual(candidate_problem_id, selected_problem_id)() is M.truth_value:
                                reversed_problems = M.Pair(updated_problem, reversed_problems)
                            else:
                                reversed_problems = M.Pair(candidate_problem, reversed_problems)
                            remaining_problems = M.Tail(remaining_problems)()
                        problems = M.EmptyList
                        while M.IdentityCompare(reversed_problems, M.EmptyList)() is M.false_value:
                            problems = M.Pair(M.Head(reversed_problems)(), problems)
                            reversed_problems = M.Tail(reversed_problems)()
                reversed_obligations = M.EmptyList
                remaining_obligations = obligations
                while M.IdentityCompare(remaining_obligations, M.EmptyList)() is M.false_value:
                    candidate_obligation = M.Head(remaining_obligations)()
                    candidate_fields = M.Tail(candidate_obligation)()
                    candidate_id = M.Head(candidate_fields)()
                    candidate_fields = M.Tail(candidate_fields)()
                    candidate_problem_id = M.Head(candidate_fields)()
                    candidate_fields = M.Tail(candidate_fields)()
                    candidate_goal = M.Head(candidate_fields)()
                    candidate_fields = M.Tail(candidate_fields)()
                    candidate_fields = M.Tail(candidate_fields)()
                    candidate_rule = M.Head(candidate_fields)()
                    candidate_bindings = M.Head(M.Tail(candidate_fields)())()
                    if M.TermEqual(candidate_id, selected_obligation_id)() is M.truth_value:
                        candidate_obligation = PlannerObligation(
                            candidate_id,
                            candidate_problem_id,
                            candidate_goal,
                            obligation_status,
                            candidate_rule,
                            candidate_bindings,
                        )()
                    reversed_obligations = M.Pair(candidate_obligation, reversed_obligations)
                    remaining_obligations = M.Tail(remaining_obligations)()
                obligations = M.EmptyList
                while M.IdentityCompare(reversed_obligations, M.EmptyList)() is M.false_value:
                    obligations = M.Pair(M.Head(reversed_obligations)(), obligations)
                    reversed_obligations = M.Tail(reversed_obligations)()
                reversed_jobs = M.EmptyList
                remaining_jobs = jobs
                while M.IdentityCompare(remaining_jobs, M.EmptyList)() is M.false_value:
                    candidate_job = M.Head(remaining_jobs)()
                    candidate_fields = M.Tail(candidate_job)()
                    candidate_fields = M.Tail(candidate_fields)()
                    candidate_obligation_id = M.Head(candidate_fields)()
                    if M.TermEqual(candidate_obligation_id, selected_obligation_id)() is M.false_value:
                        reversed_jobs = M.Pair(candidate_job, reversed_jobs)
                    remaining_jobs = M.Tail(remaining_jobs)()
                jobs = M.EmptyList
                while M.IdentityCompare(reversed_jobs, M.EmptyList)() is M.false_value:
                    jobs = M.Pair(M.Head(reversed_jobs)(), jobs)
                    reversed_jobs = M.Tail(reversed_jobs)()
                changed = M.truth_value

        if M.IdentityCompare(selected_planner_job, M.EmptyList)() is M.truth_value:
            propagated_parent_id = M.EmptyList
            remaining_dependencies = dependencies
            while M.IdentityCompare(remaining_dependencies, M.EmptyList)() is M.false_value:
                dependency_fields = M.Tail(M.Head(remaining_dependencies)())()
                parent_id = M.Head(dependency_fields)()
                child_id = M.Head(M.Tail(dependency_fields)())()
                parent_status = M.EmptyList
                child_status = M.EmptyList
                status_obligations = obligations
                while M.IdentityCompare(status_obligations, M.EmptyList)() is M.false_value:
                    status_fields = M.Tail(M.Head(status_obligations)())()
                    status_id = M.Head(status_fields)()
                    status_fields = M.Tail(status_fields)()
                    status_fields = M.Tail(status_fields)()
                    status_fields = M.Tail(status_fields)()
                    if M.TermEqual(status_id, parent_id)() is M.truth_value:
                        parent_status = M.Head(status_fields)()
                    if M.TermEqual(status_id, child_id)() is M.truth_value:
                        child_status = M.Head(status_fields)()
                    status_obligations = M.Tail(status_obligations)()
                if M.AndAtom(
                    M.IdentityCompare(parent_status, L.PendingLabel)(),
                    M.IdentityCompare(child_status, L.FailedLabel)(),
                )() is M.truth_value:
                    propagated_parent_id = parent_id
                    break
                remaining_dependencies = M.Tail(remaining_dependencies)()

            if M.IdentityCompare(propagated_parent_id, M.EmptyList)() is M.false_value:
                reversed_obligations = M.EmptyList
                remaining_obligations = obligations
                while M.IdentityCompare(remaining_obligations, M.EmptyList)() is M.false_value:
                    candidate_obligation = M.Head(remaining_obligations)()
                    candidate_fields = M.Tail(candidate_obligation)()
                    candidate_id = M.Head(candidate_fields)()
                    candidate_fields = M.Tail(candidate_fields)()
                    candidate_problem_id = M.Head(candidate_fields)()
                    candidate_fields = M.Tail(candidate_fields)()
                    candidate_goal = M.Head(candidate_fields)()
                    candidate_fields = M.Tail(candidate_fields)()
                    candidate_fields = M.Tail(candidate_fields)()
                    candidate_rule = M.Head(candidate_fields)()
                    candidate_bindings = M.Head(M.Tail(candidate_fields)())()
                    if M.TermEqual(candidate_id, propagated_parent_id)() is M.truth_value:
                        candidate_obligation = PlannerObligation(
                            candidate_id,
                            candidate_problem_id,
                            candidate_goal,
                            L.FailedLabel,
                            candidate_rule,
                            candidate_bindings,
                        )()
                    reversed_obligations = M.Pair(candidate_obligation, reversed_obligations)
                    remaining_obligations = M.Tail(remaining_obligations)()
                obligations = M.EmptyList
                while M.IdentityCompare(reversed_obligations, M.EmptyList)() is M.false_value:
                    obligations = M.Pair(M.Head(reversed_obligations)(), obligations)
                    reversed_obligations = M.Tail(reversed_obligations)()
                changed = M.truth_value

            remaining_obligations = obligations
            decomposed_id = propagated_parent_id
            while M.IdentityCompare(remaining_obligations, M.EmptyList)() is M.false_value:
                if M.IdentityCompare(decomposed_id, M.EmptyList)() is M.false_value:
                    break
                obligation = M.Head(remaining_obligations)()
                obligation_fields = M.Tail(obligation)()
                obligation_id = M.Head(obligation_fields)()
                obligation_fields = M.Tail(obligation_fields)()
                problem_id = M.Head(obligation_fields)()
                obligation_fields = M.Tail(obligation_fields)()
                obligation_goal = M.Head(obligation_fields)()
                obligation_fields = M.Tail(obligation_fields)()
                obligation_status = M.Head(obligation_fields)()
                obligation_fields = M.Tail(obligation_fields)()
                selected_rule = M.Head(obligation_fields)()
                active_job = M.false_value
                remaining_jobs = jobs
                while M.IdentityCompare(remaining_jobs, M.EmptyList)() is M.false_value:
                    candidate_job_fields = M.Tail(M.Head(remaining_jobs)())()
                    candidate_job_fields = M.Tail(candidate_job_fields)()
                    if M.TermEqual(M.Head(candidate_job_fields)(), obligation_id)() is M.truth_value:
                        active_job = M.truth_value
                        break
                    remaining_jobs = M.Tail(remaining_jobs)()
                if M.AndAtom(
                    M.IdentityCompare(obligation_status, L.PendingLabel)(),
                    M.AndAtom(
                        M.IdentityCompare(selected_rule, M.EmptyList)(),
                        M.IdentityCompare(active_job, M.false_value)(),
                    )(),
                )() is M.truth_value:
                    problem = M.EmptyList
                    remaining_problems = problems
                    while M.IdentityCompare(remaining_problems, M.EmptyList)() is M.false_value:
                        candidate_problem = M.Head(remaining_problems)()
                        if M.TermEqual(M.Head(M.Tail(candidate_problem)())(), problem_id)() is M.truth_value:
                            problem = candidate_problem
                            break
                        remaining_problems = M.Tail(remaining_problems)()
                    if M.IdentityCompare(problem, M.EmptyList)() is M.false_value:
                        problem_fields = M.Tail(problem)()
                        problem_fields = M.Tail(problem_fields)()
                        problem_fields = M.Tail(problem_fields)()
                        problem_rules = M.Head(M.Tail(problem_fields)())()
                        remaining_rules = problem_rules
                        matched_rule = M.EmptyList
                        matched_bindings = M.EmptyList
                        while M.IdentityCompare(remaining_rules, M.EmptyList)() is M.false_value:
                            candidate_rule = M.Head(remaining_rules)()
                            candidate_replacement = P.RuleReplacement(candidate_rule)()
                            conclusion_match = M.Match(candidate_replacement, obligation_goal)()
                            if M.AndAtom(
                                M.IdentityCompare(P.IsVarPattern(candidate_replacement)(), M.false_value)(),
                                M.IdentityCompare(M.Head(conclusion_match)(), M.truth_value)(),
                            )() is M.truth_value:
                                candidate_premises = P.RulePremises(candidate_rule)()
                                candidate_bindings = M.Tail(conclusion_match)()
                                candidate_admissible = M.truth_value
                                premises_to_check = candidate_premises
                                while M.IdentityCompare(premises_to_check, M.EmptyList)() is M.false_value:
                                    instantiated = M.Instantiate(M.Head(premises_to_check)(), candidate_bindings)()
                                    premise_goal = M.Head(instantiated)()
                                    existing_obligations = obligations
                                    while M.IdentityCompare(existing_obligations, M.EmptyList)() is M.false_value:
                                        existing_fields = M.Tail(M.Head(existing_obligations)())()
                                        existing_fields = M.Tail(existing_fields)()
                                        existing_problem_id = M.Head(existing_fields)()
                                        existing_fields = M.Tail(existing_fields)()
                                        existing_goal = M.Head(existing_fields)()
                                        existing_status = M.Head(M.Tail(existing_fields)())()
                                        if M.AndAtom(
                                            M.TermEqual(existing_problem_id, problem_id)(),
                                            M.TermEqual(existing_goal, premise_goal)(),
                                        )() is M.truth_value:
                                            if M.IdentityCompare(existing_status, L.ProvedLabel)() is M.false_value:
                                                candidate_admissible = M.false_value
                                                break
                                        existing_obligations = M.Tail(existing_obligations)()
                                    if M.IdentityCompare(candidate_admissible, M.false_value)() is M.truth_value:
                                        break
                                    premises_to_check = M.Tail(premises_to_check)()
                                if M.AndAtom(
                                    M.IdentityCompare(candidate_premises, M.EmptyList)(),
                                    M.IdentityCompare(candidate_admissible, M.truth_value)(),
                                )() is M.false_value:
                                    if M.IdentityCompare(candidate_admissible, M.truth_value)() is M.truth_value:
                                        matched_rule = candidate_rule
                                        matched_bindings = candidate_bindings
                                        break
                            remaining_rules = M.Tail(remaining_rules)()
                        if M.IdentityCompare(matched_rule, M.EmptyList)() is M.false_value:
                            reversed_obligations = M.EmptyList
                            obligations_to_rebuild = obligations
                            while M.IdentityCompare(obligations_to_rebuild, M.EmptyList)() is M.false_value:
                                candidate_obligation = M.Head(obligations_to_rebuild)()
                                candidate_fields = M.Tail(candidate_obligation)()
                                candidate_id = M.Head(candidate_fields)()
                                candidate_fields = M.Tail(candidate_fields)()
                                candidate_problem_id = M.Head(candidate_fields)()
                                candidate_fields = M.Tail(candidate_fields)()
                                candidate_goal = M.Head(candidate_fields)()
                                candidate_fields = M.Tail(candidate_fields)()
                                candidate_status = M.Head(candidate_fields)()
                                if M.TermEqual(candidate_id, obligation_id)() is M.truth_value:
                                    candidate_obligation = PlannerObligation(
                                        candidate_id,
                                        candidate_problem_id,
                                        candidate_goal,
                                        candidate_status,
                                        matched_rule,
                                        matched_bindings,
                                    )()
                                reversed_obligations = M.Pair(candidate_obligation, reversed_obligations)
                                obligations_to_rebuild = M.Tail(obligations_to_rebuild)()
                            obligations = M.EmptyList
                            while M.IdentityCompare(reversed_obligations, M.EmptyList)() is M.false_value:
                                obligations = M.Pair(M.Head(reversed_obligations)(), obligations)
                                reversed_obligations = M.Tail(reversed_obligations)()
                            remaining_premises = P.RulePremises(matched_rule)()
                            while M.IdentityCompare(remaining_premises, M.EmptyList)() is M.false_value:
                                instantiated = M.Instantiate(M.Head(remaining_premises)(), matched_bindings)()
                                premise_goal = M.Head(instantiated)()
                                child_id = next_obligation_id
                                next_pair = M.Succ(next_obligation_id, registry)()
                                next_obligation_id = M.Head(next_pair)()
                                registry = M.Head(M.Tail(next_pair)())()
                                child = PlannerObligation(
                                    child_id,
                                    problem_id,
                                    premise_goal,
                                    L.PendingLabel,
                                    M.EmptyList,
                                    M.EmptyList,
                                )()
                                obligations = M.Pair(child, obligations)
                                dependencies = M.Pair(
                                    PlannerDependency(obligation_id, child_id)(),
                                    dependencies,
                                )
                                remaining_premises = M.Tail(remaining_premises)()
                            decomposed_id = obligation_id
                            changed = M.truth_value
                            break
                remaining_obligations = M.Tail(remaining_obligations)()

            if M.IdentityCompare(decomposed_id, M.EmptyList)() is M.truth_value:
                remaining_obligations = obligations
                while M.IdentityCompare(remaining_obligations, M.EmptyList)() is M.false_value:
                    obligation = M.Head(remaining_obligations)()
                    obligation_fields = M.Tail(obligation)()
                    obligation_id = M.Head(obligation_fields)()
                    obligation_fields = M.Tail(obligation_fields)()
                    problem_id = M.Head(obligation_fields)()
                    obligation_fields = M.Tail(obligation_fields)()
                    obligation_goal = M.Head(obligation_fields)()
                    obligation_status = M.Head(M.Tail(obligation_fields)())()
                    active_job = M.false_value
                    remaining_jobs = jobs
                    while M.IdentityCompare(remaining_jobs, M.EmptyList)() is M.false_value:
                        candidate_job_fields = M.Tail(M.Head(remaining_jobs)())()
                        candidate_job_fields = M.Tail(candidate_job_fields)()
                        if M.TermEqual(M.Head(candidate_job_fields)(), obligation_id)() is M.truth_value:
                            active_job = M.truth_value
                            break
                        remaining_jobs = M.Tail(remaining_jobs)()
                    dependencies_ready = M.truth_value
                    remaining_dependencies = dependencies
                    while M.IdentityCompare(remaining_dependencies, M.EmptyList)() is M.false_value:
                        dependency_fields = M.Tail(M.Head(remaining_dependencies)())()
                        parent_id = M.Head(dependency_fields)()
                        child_id = M.Head(M.Tail(dependency_fields)())()
                        if M.TermEqual(parent_id, obligation_id)() is M.truth_value:
                            child_status = L.PendingLabel
                            child_obligations = obligations
                            while M.IdentityCompare(child_obligations, M.EmptyList)() is M.false_value:
                                child_fields = M.Tail(M.Head(child_obligations)())()
                                if M.TermEqual(M.Head(child_fields)(), child_id)() is M.truth_value:
                                    child_fields = M.Tail(child_fields)()
                                    child_fields = M.Tail(child_fields)()
                                    child_fields = M.Tail(child_fields)()
                                    child_status = M.Head(child_fields)()
                                    break
                                child_obligations = M.Tail(child_obligations)()
                            if M.IdentityCompare(child_status, L.ProvedLabel)() is M.false_value:
                                dependencies_ready = M.false_value
                                break
                        remaining_dependencies = M.Tail(remaining_dependencies)()
                    if M.AndAtom(
                        M.IdentityCompare(obligation_status, L.PendingLabel)(),
                        M.AndAtom(
                            M.IdentityCompare(active_job, M.false_value)(),
                            M.IdentityCompare(dependencies_ready, M.truth_value)(),
                        )(),
                    )() is M.truth_value:
                        problem = M.EmptyList
                        remaining_problems = problems
                        while M.IdentityCompare(remaining_problems, M.EmptyList)() is M.false_value:
                            candidate_problem = M.Head(remaining_problems)()
                            if M.TermEqual(M.Head(M.Tail(candidate_problem)())(), problem_id)() is M.truth_value:
                                problem = candidate_problem
                                break
                            remaining_problems = M.Tail(remaining_problems)()
                        if M.IdentityCompare(problem, M.EmptyList)() is M.false_value:
                            problem_fields = M.Tail(problem)()
                            problem_fields = M.Tail(problem_fields)()
                            mathematical_state = M.Head(problem_fields)()
                            problem_fields = M.Tail(problem_fields)()
                            problem_fields = M.Tail(problem_fields)()
                            problem_rules = M.Head(problem_fields)()
                            problem_heuristic = M.Head(M.Tail(problem_fields)())()
                            start_state = S.SearchState(
                                mathematical_state,
                                M.EmptyList,
                                M.EmptyList,
                                M.EmptyList,
                            )()
                            search_job = S.SearchJob(
                                mathematical_state,
                                obligation_goal,
                                problem_rules,
                                problem_heuristic,
                                S.SearchRunningLabel,
                                M.Pair(start_state, M.EmptyList),
                                M.Zero,
                                M.Zero,
                                M.Zero,
                                M.EmptyList,
                                M.EmptyList,
                                M.EmptyList,
                                M.EmptyList,
                                M.one,
                            )()
                            jobs = M.Pair(PlannerJob(problem_id, obligation_id, search_job)(), jobs)
                            changed = M.truth_value
                            break
                    remaining_obligations = M.Tail(remaining_obligations)()

        graph._replace_context(constructors=registry)
        next_state = PlannerStateRecord(
            problems,
            obligations,
            dependencies,
            jobs,
            next_obligation_id,
            registry,
        )()
        self.result = M.Pair(next_state, M.Pair(changed, M.EmptyList))
        super().__init__(
            inputs=M.Pair(graph, M.Pair(state, M.Pair(step_budget, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


class PlannerRun(M.Edge):
    def __init__(self, graph, state, step_budget):
        current_state = state
        running = M.truth_value
        while M.IdentityCompare(running, M.truth_value)() is M.truth_value:
            state_fields = M.Tail(current_state)()
            obligations = M.Head(state_fields)()
            root_status = L.PendingLabel
            current_obligations = obligations
            while M.IdentityCompare(current_obligations, M.EmptyList)() is M.false_value:
                obligation_fields = M.Tail(M.Head(current_obligations)())()
                obligation_id = M.Head(obligation_fields)()
                if M.TermEqual(obligation_id, M.Zero)() is M.truth_value:
                    obligation_fields = M.Tail(obligation_fields)()
                    obligation_fields = M.Tail(obligation_fields)()
                    obligation_fields = M.Tail(obligation_fields)()
                    root_status = M.Head(obligation_fields)()
                    break
                current_obligations = M.Tail(current_obligations)()
            if M.OrAtom(
                M.IdentityCompare(root_status, L.ProvedLabel)(),
                M.IdentityCompare(root_status, L.FailedLabel)(),
            )() is M.truth_value:
                running = M.false_value
            else:
                step_pair = PlannerStep(graph, current_state, step_budget)()
                next_state = M.Head(step_pair)()
                changed = M.Head(M.Tail(step_pair)())()
                current_state = next_state
                if M.IdentityCompare(changed, M.false_value)() is M.truth_value:
                    running = M.false_value
        self.result = current_state
        super().__init__(
            inputs=M.Pair(graph, M.Pair(state, M.Pair(step_budget, M.EmptyList))),
            results=self.result,
        )

    def __call__(self):
        return self.result


__all__ = (
    "PlannerProblem",
    "PlannerObligation",
    "PlannerDependency",
    "PlannerJob",
    "PlannerStateRecord",
    "PlannerState",
    "PlannerStep",
    "PlannerRun",
)
