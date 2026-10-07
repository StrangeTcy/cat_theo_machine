# ============================================================
# TEST 11: Gate H Declarative Surface-Language Bridge
# ============================================================
import os
import sys
import time

IMPORT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if IMPORT_ROOT not in sys.path:
    sys.path.insert(0, IMPORT_ROOT)

from cat_theo_machine import graph_task as GT
from cat_theo_machine import labels as L
from cat_theo_machine import machine as M
from cat_theo_machine import proof as P
from cat_theo_machine.runtime import make_fresh_runtime
from cat_theo_machine import surface_bridge as Bridge

t0 = time.time()
print("=== TEST 11: Gate H Declarative Surface-Language Bridge ===")
print()

print("[1] Initializing runtime, hypergraph, and registry...")
runtime = make_fresh_runtime()
graph = runtime.graph
registry = M.FromContextGetConstructors(graph)()
print("    Runtime OK.")
print()

# Surface Vocabulary Tokens (Machine Atoms)
tok_connects = M.Atom()
tok_path = M.Atom()
tok_from = M.Atom()
tok_to = M.Atom()
tok_find = M.Atom()
tok_target = M.Atom()

# Domain Nodes & Edge Tags
edge_e = M.Atom()
node_a = M.Atom()
node_b = M.Atom()
node_c = M.Atom()

var_x = M.Var()
var_pat_x = M.Pair(M.VarTag, M.Pair(var_x, M.EmptyList))

# Grammar Correspondence 1: [node_a, tok_connects, var_x] -> GraphTaskRecord(E(node_a, node_b), Query: E(node_a, ?x))
pat_stream_1 = M.Pair(
    node_a, M.Pair(tok_connects, M.Pair(var_pat_x, M.EmptyList))
)
fact_1 = M.Pair(edge_e, M.Pair(node_a, M.Pair(node_b, M.EmptyList)))
query_1 = M.Pair(edge_e, M.Pair(node_a, M.Pair(var_pat_x, M.EmptyList)))
task_tmpl_1 = GT.GraphTaskRecord(
    M.Atom(),
    L.Rung1RetrievalLabel,
    M.Pair(fact_1, M.EmptyList),
    query_1,
    node_b,
    M.EmptyList,
    M.EmptyList,
)()
render_tmpl_1 = M.Pair(
    node_a, M.Pair(tok_connects, M.Pair(var_pat_x, M.EmptyList))
)

corr_1 = Bridge.SurfaceCorrespondence(
    M.Atom(), pat_stream_1, task_tmpl_1, render_tmpl_1
)()

# Grammar Correspondence 2 (Paraphrase): [tok_path, tok_from, node_a, tok_to, var_x] -> Same GraphTaskRecord
pat_stream_2 = M.Pair(
    tok_path,
    M.Pair(
        tok_from,
        M.Pair(
            node_a,
            M.Pair(tok_to, M.Pair(var_pat_x, M.EmptyList)),
        ),
    ),
)
corr_2 = Bridge.SurfaceCorrespondence(
    M.Atom(), pat_stream_2, task_tmpl_1, render_tmpl_1
)()

grammar_rules = M.Pair(corr_1, M.Pair(corr_2, M.EmptyList))

print("[2] Test Case 1: Surface Statement Construction & Parsing...")
# Statement 1: "node_a connects ?x"
stmt_1_tokens = M.Pair(
    node_a, M.Pair(tok_connects, M.Pair(var_pat_x, M.EmptyList))
)
stmt_1 = Bridge.SurfaceStatement(stmt_1_tokens)()
parse_1_res = Bridge.ParseSurfaceToGraphTask(stmt_1, grammar_rules, registry)()
parse_tag_1 = M.Head(parse_1_res)()
is_parse_ok = (
    M.IdentityCompare(parse_tag_1, L.SurfaceParseSuccessLabel)()
    is M.truth_value
)
print(f"    Parse Verdict: {parse_tag_1} (Passed: {is_parse_ok})")
assert is_parse_ok, "Test 1 Failed: Surface statement did not parse to graph task!"

parsed_task = M.Head(M.Tail(parse_1_res)())()

print("[3] Test Case 2: Solving Parsed Task Exclusively in Graph Space...")
exec_res = GT.ExecuteGraphQuery(parsed_task, registry)()
exec_tag = M.Head(exec_res)()
is_exec_ok = (
    M.IdentityCompare(exec_tag, L.TaskSuccessLabel)() is M.truth_value
)
print(f"    Graph Query Execution: {exec_tag} (Passed: {is_exec_ok})")
assert is_exec_ok, "Test 2 Failed: Graph space execution failed!"

print("[4] Test Case 3: Paraphrase Equivalence Normalization...")
# Statement 2: "path from node_a to ?x"
stmt_2_tokens = M.Pair(
    tok_path,
    M.Pair(
        tok_from,
        M.Pair(
            node_a,
            M.Pair(tok_to, M.Pair(var_pat_x, M.EmptyList)),
        ),
    ),
)
stmt_2 = Bridge.SurfaceStatement(stmt_2_tokens)()

equiv_res = Bridge.CheckParaphraseEquivalence(
    stmt_1, stmt_2, grammar_rules, registry
)()
is_equiv = (
    M.IdentityCompare(equiv_res, M.truth_value)() is M.truth_value
)
print(
    f"    Paraphrase Equivalence Result: {equiv_res} (Passed: {is_equiv})"
)
assert is_equiv, "Test 3 Failed: Paraphrase statements not recognized as equivalent!"

print("[5] Test Case 4: Reversible Graph Binding Surface Rendering...")
render_res = Bridge.RenderGraphResultToSurface(
    exec_res, render_tmpl_1, registry
)()
render_tag = M.Head(render_res)()
is_render_ok = (
    M.IdentityCompare(render_tag, L.SurfaceRenderSuccessLabel)()
    is M.truth_value
)
rendered_statement = M.Head(M.Tail(render_res)())()
print(f"    Surface Render Verdict: {render_tag} (Passed: {is_render_ok})")
assert is_render_ok, "Test 4 Failed: Binding rendering to surface failed!"

print("[6] Test Case 5: Derivation Summary Surface Rendering...")
rule_ab = P.Rule(node_a, node_b)()
rule_bc = P.Rule(node_b, node_c)()

act_1 = P.RewriteAction(rule_ab, M.EmptyList)()
step_1_res = P.Step(node_a, act_1, node_b, registry)()
step_1 = M.Head(step_1_res)()
registry = M.Head(M.Tail(step_1_res)())()

act_2 = P.RewriteAction(rule_bc, M.EmptyList)()
step_2_res = P.Step(node_b, act_2, node_c, registry)()
step_2 = M.Head(step_2_res)()
registry = M.Head(M.Tail(step_2_res)())()

cost_zero = P.ProofCost(M.Zero, M.Zero, M.Zero, M.Zero)()
der_res = P.Derivation(
    M.Pair(step_1, M.Pair(step_2, M.EmptyList)), cost_zero, registry
)()
derivation = M.Head(der_res)()
registry = M.Head(M.Tail(der_res)())()

summary_res = Bridge.RenderDerivationSummary(
    derivation, M.EmptyList, registry
)()
summary_tag = M.Head(summary_res)()
is_summary_ok = (
    M.IdentityCompare(summary_tag, L.SurfaceRenderSuccessLabel)()
    is M.truth_value
)
print(f"    Derivation Summary Render: {summary_tag} (Passed: {is_summary_ok})")
assert is_summary_ok, "Test 5 Failed: Derivation summary render failed!"

print("[7] Test Case 6: Handling Unsupported Phrasing (Parse Failure)...")
unsupported_tokens = M.Pair(
    tok_find, M.Pair(tok_target, M.Pair(node_c, M.EmptyList))
)
unsupported_stmt = Bridge.SurfaceStatement(unsupported_tokens)()
unsupp_parse = Bridge.ParseSurfaceToGraphTask(
    unsupported_stmt, grammar_rules, registry
)()
unsupp_tag = M.Head(unsupp_parse)()
is_unsupp_failed = (
    M.IdentityCompare(unsupp_tag, L.SurfaceParseFailureLabel)()
    is M.truth_value
)
print(
    f"    Unsupported Phrasing Tag: {unsupp_tag} (Rejected as expected: {is_unsupp_failed})"
)
assert (
    is_unsupp_failed
), "Test 6 Failed: Unsupported phrasing was not rejected!"

print("[8] Test Case 7: Ambiguity Detection (Multiple Parse Trees)...")
# Add conflicting rule with same surface pattern
ambig_corr = Bridge.SurfaceCorrespondence(
    M.Atom(), pat_stream_1, task_tmpl_1, render_tmpl_1
)()
ambig_grammar = M.Pair(corr_1, M.Pair(ambig_corr, M.EmptyList))

ambig_parse = Bridge.ParseSurfaceToGraphTask(
    stmt_1, ambig_grammar, registry
)()
ambig_tag = M.Head(ambig_parse)()
is_ambig_caught = (
    M.IdentityCompare(ambig_tag, L.SurfaceAmbiguityLabel)()
    is M.truth_value
)
print(
    f"    Ambiguity Detection Tag: {ambig_tag} (Caught as expected: {is_ambig_caught})"
)
assert is_ambig_caught, "Test 7 Failed: Grammar ambiguity was not caught!"

print("[9] Test Case 8: Native Concept Definition Lookup and Explanation Rendering...")
defs = Bridge.BuildStandardDefinitions(registry)()

# Query 'subdomain'
q_subdomain = Bridge.QueryConceptDefinition(M.Char("subdomain"), defs)()
q_subdomain_tag = M.Head(q_subdomain)()
assert (
    M.IdentityCompare(q_subdomain_tag, L.SurfaceParseSuccessLabel)()
    is M.truth_value
), "Test 8 Failed: Subdomain concept lookup failed!"
subdomain_def = M.Head(M.Tail(q_subdomain)())()
subdomain_exp = Bridge.RenderConceptExplanation(subdomain_def)()
subdomain_text = subdomain_exp() if callable(subdomain_exp) else getattr(subdomain_exp, "value", str(subdomain_exp))
print(f"    Subdomain Explanation: '{subdomain_text}'")
assert "subset of a base domain" in str(subdomain_text), "Test 8 Failed: Subdomain explanation text mismatch!"

# Query 'obstruction'
q_obstruction = Bridge.QueryConceptDefinition(M.Char("obstruction"), defs)()
q_obstruction_tag = M.Head(q_obstruction)()
assert (
    M.IdentityCompare(q_obstruction_tag, L.SurfaceParseSuccessLabel)()
    is M.truth_value
), "Test 8 Failed: Obstruction concept lookup failed!"
obstruction_def = M.Head(M.Tail(q_obstruction)())()
obstruction_exp = Bridge.RenderConceptExplanation(obstruction_def)()
obstruction_text = obstruction_exp() if callable(obstruction_exp) else getattr(obstruction_exp, "value", str(obstruction_exp))
print(f"    Obstruction Explanation: '{obstruction_text}'")
assert "structural invariant conflict" in str(obstruction_text), "Test 8 Failed: Obstruction explanation text mismatch!"

# Query unknown concept
q_unknown = Bridge.QueryConceptDefinition(M.Char("nonexistent_concept"), defs)()
q_unknown_tag = M.Head(q_unknown)()
assert (
    M.IdentityCompare(q_unknown_tag, L.DefinitionNotFoundLabel)()
    is M.truth_value
), "Test 8 Failed: Nonexistent concept lookup should return DefinitionNotFoundLabel!"
print(f"    Unknown Concept Lookup Tag: {q_unknown_tag} (Not found as expected)")

print()
print(
    f"=== ALL 8 GATE H SURFACE-LANGUAGE BRIDGE TESTS PASSED in {time.time() - t0:.3f}s ==="
)
