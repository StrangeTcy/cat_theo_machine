"""Checked narratives retain assumptions and refuse invalid proof receipts."""

from hyge import labels as L
from hyge import machine as M
from hyge import proof as P
from hyge import story_renderer as SR
from hyge.runtime import make_fresh_runtime


runtime = make_fresh_runtime()
registry = M.FromContextGetConstructors(runtime.graph)()
session = M.Char("checked_story_regressions")
movement_assumption = M.Pair(L.EveryStateMovesLabel, M.Pair(M.Char("descent"), M.EmptyList))
start = M.Pair(
    M.Char("Assume a primitive counterexample"),
    M.Pair(M.Char("Assume a descent schema"), M.Pair(movement_assumption, M.EmptyList)),
)
middle = M.Char("A smaller candidate follows conditionally")
goal = M.Char("The conditional target follows")
other = M.Char("An unrelated target")
rule_one = P.Rule(start, middle)()
rule_two = P.Rule(middle, goal)()
trusted = M.Pair(rule_one, M.Pair(rule_two, M.EmptyList))
action_one = P.RewriteAction(rule_one, M.EmptyList)()
action_two = P.RewriteAction(rule_two, M.EmptyList)()
step_result = P.Step(start, action_one, middle, registry)()
step_one = M.Head(step_result)()
registry = M.Head(M.Tail(step_result)())()
step_result = P.Step(middle, action_two, goal, registry)()
step_two = M.Head(step_result)()
registry = M.Head(M.Tail(step_result)())()
cost = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
built = P.Derivation(M.Pair(step_one, M.Pair(step_two, M.EmptyList)), cost, registry)()
derivation = M.Head(built)()
registry = M.Head(M.Tail(built)())()
receipt = M.Pair(
    L.ProofReceiptLabel,
    M.Pair(session, M.Pair(start, M.Pair(goal, M.Pair(derivation, registry)))),
)
policy = M.Pair(
    L.CheckPolicyLabel,
    M.Pair(session, M.Pair(start, M.Pair(goal, M.EmptyList))),
)

# Independent replay precedes every successful checked narrative.
checked = SR.RenderCheckedProofStory(receipt, trusted, registry, policy)()
story = M.Head(checked)()
verdict = M.Head(M.Tail(checked)())()
registry = M.Head(M.Tail(M.Tail(checked)())())()
assert M.IdentityCompare(M.Head(story)(), L.ProofStoryLabel)() is M.truth_value
assert M.IdentityCompare(M.Head(verdict)(), L.DerivationVerifiedLabel)() is M.truth_value
story_fields = M.Tail(story)()
assert M.Compare(M.Head(M.Tail(story_fields)())(), goal)() is M.truth_value
steps = M.Head(M.Tail(M.Tail(story_fields)())())()
first_step_fields = M.Tail(M.Head(steps)())()
second_step_fields = M.Tail(M.Head(M.Tail(steps)())())()
assert M.NatEq(M.Head(first_step_fields)(), M.one, registry)() is M.truth_value
assert M.NatEq(M.Head(second_step_fields)(), M.two, registry)() is M.truth_value
assert M.IdentityCompare(M.Tail(M.Tail(steps)())(), M.EmptyList)() is M.truth_value
summary_fields = M.Tail(M.Tail(M.Tail(story_fields)())())()
assert M.Compare(M.Head(M.Tail(summary_fields)())(), start)() is M.truth_value
assert M.Compare(M.Head(summary_fields)(), M.Char(
    "Checker B verified the target from the displayed starting assumptions "
    "under the supplied trusted rules."
))() is M.truth_value
markdown = SR.FormatStoryToMarkdown(story)
assert M.Compare(M.Char(markdown), M.Char(markdown.replace(
    "**Starting assumptions**: `Assume a primitive counterexample Assume a descent schema", ""
)))() is M.false_value
assert M.Compare(M.Char(markdown), M.Char(markdown.replace("Q.E.D.", "")))() is M.truth_value
assert M.Compare(M.Char(markdown), M.Char(markdown.replace("EveryStateMoves", "")))() is M.false_value

# The default policy remains scoped to the receipt, with identical checking.
checked = SR.RenderCheckedProofStory(receipt, trusted, registry)()
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.DerivationVerifiedLabel)() is M.truth_value

# An independently supplied policy pins session, starting state, and goal.
wrong_policy = M.Pair(L.CheckPolicyLabel,
    M.Pair(M.Char("another_session"), M.Pair(start, M.Pair(goal, M.EmptyList))))
checked = SR.RenderCheckedProofStory(receipt, trusted, registry, wrong_policy)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.CandidateScopeMismatchLabel)() is M.truth_value
wrong_policy = M.Pair(L.CheckPolicyLabel,
    M.Pair(session, M.Pair(middle, M.Pair(goal, M.EmptyList))))
checked = SR.RenderCheckedProofStory(receipt, trusted, registry, wrong_policy)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.PremiseMismatchLabel)() is M.truth_value
wrong_policy = M.Pair(L.CheckPolicyLabel,
    M.Pair(session, M.Pair(start, M.Pair(other, M.EmptyList))))
checked = SR.RenderCheckedProofStory(receipt, trusted, registry, wrong_policy)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.GoalMismatchLabel)() is M.truth_value

# Changing the requested endpoint cannot reuse the old proof as success.
altered = M.Pair(L.ProofReceiptLabel,
    M.Pair(session, M.Pair(start, M.Pair(other, M.Pair(derivation, M.EmptyList)))))
checked = SR.RenderCheckedProofStory(altered, trusted, registry)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.GoalMismatchLabel)() is M.truth_value

# A missing trust entry is reported as an unknown rule, with no story.
checked = SR.RenderCheckedProofStory(receipt, M.Pair(rule_one, M.EmptyList), registry)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.UnknownRuleLabel)() is M.truth_value

# A valid-looking step after the wrong predecessor is still rejected.
built = P.Derivation(M.Pair(step_two, M.EmptyList), cost, registry)()
broken_derivation = M.Head(built)()
registry = M.Head(M.Tail(built)())()
altered = M.Pair(L.ProofReceiptLabel,
    M.Pair(session, M.Pair(start, M.Pair(goal, M.Pair(broken_derivation, M.EmptyList)))))
checked = SR.RenderCheckedProofStory(altered, trusted, registry)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.StepDiscontinuityLabel)() is M.truth_value

# Empty derivations only establish an endpoint already present at the start.
built = P.Derivation(M.EmptyList, cost, registry)()
empty_derivation = M.Head(built)()
registry = M.Head(M.Tail(built)())()
altered = M.Pair(L.ProofReceiptLabel,
    M.Pair(session, M.Pair(start, M.Pair(goal, M.Pair(empty_derivation, M.EmptyList)))))
checked = SR.RenderCheckedProofStory(altered, trusted, registry)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.GoalMismatchLabel)() is M.truth_value
identity_receipt = M.Pair(L.ProofReceiptLabel,
    M.Pair(session, M.Pair(start, M.Pair(start, M.Pair(empty_derivation, M.EmptyList)))))
checked = SR.RenderCheckedProofStory(identity_receipt, M.EmptyList, registry)()
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.DerivationVerifiedLabel)() is M.truth_value

# Unknown derivation atoms cannot masquerade as empty identity proofs.
altered = M.Pair(L.ProofReceiptLabel,
    M.Pair(session, M.Pair(start, M.Pair(start, M.Pair(M.Atom(), M.EmptyList)))))
checked = SR.RenderCheckedProofStory(altered, trusted, registry)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.PremiseMismatchLabel)() is M.truth_value

# Short and wrongly tagged records fail without generating a narrative.
checked = SR.RenderCheckedProofStory(M.Atom(), trusted, registry)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.PremiseMismatchLabel)() is M.truth_value
checked = SR.RenderCheckedProofStory(M.Pair(L.ProofReceiptLabel, M.EmptyList), trusted, registry)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.PremiseMismatchLabel)() is M.truth_value
checked = SR.RenderCheckedProofStory(M.Pair(L.CheckPolicyLabel, M.Tail(receipt)()), trusted, registry)()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.PremiseMismatchLabel)() is M.truth_value
checked = SR.RenderCheckedProofStory(receipt, trusted, registry, M.Atom())()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.PremiseMismatchLabel)() is M.truth_value
checked = SR.RenderCheckedProofStory(receipt, trusted, registry, M.Pair(L.CheckPolicyLabel, M.EmptyList))()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.PremiseMismatchLabel)() is M.truth_value
checked = SR.RenderCheckedProofStory(receipt, trusted, registry, M.Pair(L.ProofReceiptLabel, M.Tail(policy)()))()
assert M.IdentityCompare(M.Head(checked)(), M.EmptyList)() is M.truth_value
assert M.IdentityCompare(M.Head(M.Head(M.Tail(checked)())())(), L.PremiseMismatchLabel)() is M.truth_value

# Raw rendering explicitly carries no proof-verification claim.
raw = SR.RenderProofStory(receipt, registry)()
raw_fields = M.Tail(raw)()
raw_summary_fields = M.Tail(M.Tail(M.Tail(raw_fields)())())()
assert M.Compare(M.Head(raw_summary_fields)(), M.Char(
    "Unchecked receipt narrative; proof verification has not been performed."
))() is M.truth_value
assert M.Compare(M.Head(M.Tail(raw_summary_fields)())(), start)() is M.truth_value
raw_markdown = SR.FormatStoryToMarkdown(raw)
assert M.Compare(M.Char(raw_markdown), M.Char(raw_markdown.replace("Q.E.D.", "")))() is M.truth_value
assert M.Compare(M.Char(raw_markdown), M.Char(raw_markdown.replace("Checker B verified", "")))() is M.truth_value

print("Checked story regressions passed: valid replay, scope, assumptions, malformed records, rejected proofs, and unchecked status.")
