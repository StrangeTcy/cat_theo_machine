# ============================================================
# DIMENSION 5 / W14 — Proof Storyteller & Derivation Narrative Generator
# Translates formal hypergraph proof receipts and derivation chains
# into structured mathematical proof stories with domain rationales.
# ============================================================
from __future__ import annotations

from . import checker_b as CheckerB
from . import labels as L
from . import machine as M
from . import proof as P


class NarrativeStep(M.Edge):
    """
    Structured narrative step record.
    inputs: [step_index, rule_name, premises, conclusion, rationale_label]
    results: Pair(NarrativeStepLabel, Pair(step_index, Pair(rule_name, Pair(premises, Pair(conclusion, Pair(rationale_label, EmptyList))))))
    """

    def __init__(
        self, step_index, rule_name, premises, conclusion, rationale_label
    ):
        self.step_index = step_index
        self.rule_name = rule_name
        self.premises = premises
        self.conclusion = conclusion
        self.rationale_label = rationale_label
        self.result = M.Pair(
            L.NarrativeStepLabel,
            M.Pair(
                step_index,
                M.Pair(
                    rule_name,
                    M.Pair(
                        premises,
                        M.Pair(
                            conclusion,
                            M.Pair(rationale_label, M.EmptyList),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                step_index,
                M.Pair(
                    rule_name,
                    M.Pair(
                        premises,
                        M.Pair(
                            conclusion,
                            M.Pair(rationale_label, M.EmptyList),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class ClassifyInferenceRationale(M.Edge):
    """
    Classifies the mathematical intent/rationale of an inference step.
    """

    def __init__(self, step, registry):
        self.registry = registry
        self.result = self._classify(step)
        super().__init__(
            inputs=M.Pair(step, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _classify(self, step):
        action = P.StepAction(step, self.registry)()
        rule = P.ActionRule(action)() if (P.IsRewriteAction(action)() is M.truth_value or P.IsTheoremAction(action)() is M.truth_value) else action
        premise = P.StepCurrent(step, self.registry)()
        conclusion = P.StepNext(step, self.registry)()

        def _to_str(x):
            if x is None:
                return ""
            if callable(x):
                try:
                    return str(x())
                except Exception:
                    pass
            val = getattr(x, "value", None)
            if val is not None:
                return str(val)
            if M.IsPair(x)() is M.truth_value:
                return _to_str(M.Head(x)()) + " " + _to_str(M.Tail(x)())
            return str(x)

        step_text = f"{_to_str(action)} {_to_str(rule)} {_to_str(premise)} {_to_str(conclusion)}".lower()

        if (
            "mod" in step_text
            or "parity" in step_text
            or "obstruction" in step_text
            or "disjoint" in step_text
        ):
            return L.RationaleParityObstructionLabel

        if (
            "aux" in step_text
            or "triangle" in step_text
            or "circle" in step_text
            or "angle" in step_text
            or "point" in step_text
            or "geom" in step_text
        ):
            return L.RationaleAuxiliaryConstructionLabel

        if (
            "mono" in step_text
            or "invariant" in step_text
            or "decrease" in step_text
            or "phi" in step_text
            or "semi" in step_text
        ):
            return L.RationaleMonovariantLabel

        if (
            "descent" in step_text
            or "smaller" in step_text
            or "well_founded" in step_text
            or "order" in step_text
        ):
            return L.RationaleDescentLabel

        return L.RationaleAlgebraicLabel

    def __call__(self):
        return self.result


class ProofStory(M.Edge):
    """
    Full mathematical proof story container.
    inputs: [story_id, goal, narrative_steps, summary_text]
    results: Pair(ProofStoryLabel, Pair(story_id, Pair(goal, Pair(narrative_steps, Pair(summary_text, EmptyList)))))
    """

    def __init__(self, story_id, goal, narrative_steps, summary_text):
        self.story_id = story_id
        self.goal = goal
        self.narrative_steps = narrative_steps
        self.summary_text = summary_text
        self.result = M.Pair(
            L.ProofStoryLabel,
            M.Pair(
                story_id,
                M.Pair(
                    goal,
                    M.Pair(
                        narrative_steps,
                        M.Pair(summary_text, M.EmptyList),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                story_id,
                M.Pair(
                    goal,
                    M.Pair(
                        narrative_steps,
                        M.Pair(summary_text, M.EmptyList),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class RenderProofStory(M.Edge):
    """
    Transforms a verified ProofReceipt into a structured ProofStory hyperedge.
    """

    def __init__(self, receipt, registry):
        self.registry = registry
        self.result = self._render(receipt)
        super().__init__(
            inputs=M.Pair(receipt, M.Pair(registry, M.EmptyList)),
            results=self.result,
        )

    def _render(self, receipt):
        rec_fields = M.Tail(receipt)()
        session_id = M.Head(rec_fields)()
        start_state = M.Head(M.Tail(rec_fields)())()
        goal_state = M.Head(M.Tail(M.Tail(rec_fields)())())()
        derivation = M.Head(M.Tail(M.Tail(M.Tail(rec_fields)())())())()

        steps = P.DerivationSteps(derivation, self.registry)()
        narrative_steps = self._compile_steps(steps, M.Zero)

        summary = M.Char("Formal proof story successfully established target goal and verified receipt")

        return ProofStory(
            session_id, goal_state, narrative_steps, summary
        )()

    def _compile_steps(self, steps_cur, cur_idx_nat):
        if M.IdentityCompare(steps_cur, M.EmptyList)() is M.truth_value:
            return M.EmptyList

        step = M.Head(steps_cur)()
        succ_res = M.Succ(cur_idx_nat, self.registry)()
        next_idx_nat = M.Head(succ_res)()

        action = P.StepAction(step, self.registry)()
        rule = P.ActionRule(action)()
        premises = P.StepCurrent(step, self.registry)()
        conclusion = P.StepNext(step, self.registry)()
        rationale = ClassifyInferenceRationale(step, self.registry)()

        n_step = NarrativeStep(
            next_idx_nat, rule, premises, conclusion, rationale
        )()

        rest_steps = self._compile_steps(M.Tail(steps_cur)(), next_idx_nat)
        return M.Pair(n_step, rest_steps)

    def __call__(self):
        return self.result


def FormatStoryToMarkdown(story_node):
    """
    Formats a ProofStory hyperedge into natural Markdown text with step rationales.
    """
    def _to_str(x):
        if x is None:
            return ""
        val = getattr(x, "value", None)
        if val is not None:
            return str(val)
        try:
            p = P.RulePattern(x)()
            r = P.RuleReplacement(x)()
            p_str = _to_str(p)
            r_str = _to_str(r)
            if p_str and r_str:
                return f"{p_str} -> {r_str}"
        except Exception:
            pass
        if M.IsPair(x)() is M.truth_value:
            h = _to_str(M.Head(x)())
            t = _to_str(M.Tail(x)())
            if not t:
                return h
            return f"{h} {t}".strip()
        if callable(x) and not hasattr(x, "inputs"):
            try:
                res = x()
                if res is not None:
                    return str(res)
            except Exception:
                pass
        s = str(x)
        if "object at" in s:
            part = s.split(" ")[0].split(".")[-1]
            return part.replace("Label", "")
        return s

    story_fields = M.Tail(story_node)()
    session_id = M.Head(story_fields)()
    goal = M.Head(M.Tail(story_fields)())()
    narrative_steps = M.Head(M.Tail(M.Tail(story_fields)())())()
    summary = M.Head(M.Tail(M.Tail(M.Tail(story_fields)())())())()

    session_str = _to_str(session_id)
    goal_str = _to_str(goal)
    summary_str = _to_str(summary)

    lines = [
        f"### Proof Narrative: Session `{session_str}`",
        f"**Target Goal**: `{goal_str}`",
        "",
        "#### Derivation Steps & Mathematical Rationale:",
    ]

    cur = narrative_steps
    step_num = 1
    while M.IdentityCompare(cur, M.EmptyList)() is M.false_value:
        n_step = M.Head(cur)()
        ns_fields = M.Tail(n_step)()
        rule_name = M.Head(M.Tail(ns_fields)())()
        conclusion = M.Head(M.Tail(M.Tail(M.Tail(ns_fields)())())())()
        rationale = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(ns_fields)())())())())()

        rule_str = _to_str(rule_name)
        conc_str = _to_str(conclusion)

        rat_name = (
            rationale.__class__.__name__
            if hasattr(rationale, "__class__")
            else str(rationale)
        )
        clean_rat = rat_name.replace("Rationale", "").replace("Label", "")

        lines.append(
            f"{step_num}. **Step {step_num}** [{clean_rat}]: Applied `{rule_str}` $\\implies$ Derived `{conc_str}`"
        )

        step_num += 1
        cur = M.Tail(cur)()

    lines.append("")
    lines.append(f"**Conclusion (Q.E.D.)**: {summary_str}")
    return "\n".join(lines)


__all__ = (
    "NarrativeStep",
    "ClassifyInferenceRationale",
    "ProofStory",
    "RenderProofStory",
    "FormatStoryToMarkdown",
)
