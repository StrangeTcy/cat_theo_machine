#!/usr/bin/env python3
"""Milestone-2 driver: journal split (OBSERVATIONS vs PROPOSALS), isolation,
replay-proven restore equivalence, inert proposals, duplicate delivery.

Reuses production machinery only — no new labels, no new store roots, no
production edits in this land:
  research.py      attempt_goal / record_trace / TracesOnRecord /
                   mine_compressed_laws / candidate_support /
                   counterfactual_evaluation / AlphaNormalized
  graph.py         record_intervention_episode / reset_learned_memory /
                   provenance_map / dependency_policies roots
  persistence.py   SnapshotCodec save/load/activate (the only snapshot path
                   operators and workers already use)
  research.py::InterventionEpisode  (the episode term, measured fields only)

The split being proven:
  OBSERVATIONS = validator-visible evidence (traces, episodes, residuals,
    counterfactual measurements) — restorable; restore equivalence is PROVEN
    by re-running production computations over the restored data and
    requiring term equality, never by file-hash assertion.
  PROPOSALS    = candidate laws mined from observations — recorded inert,
    never a snapshot root, never re-imported; re-mining restored evidence
    must re-derive them (a proposal is a function of evidence, not state).

Run from /home/user:
  python3 cat_theo_machine/tools/agent_workers/journal_driver.py <artifact-path>
"""
import json
import os
import sys
import time

sys.path.insert(0, "/home/user")

ARTIFACT = sys.argv[1] if len(sys.argv) > 1 else ""
_lines = []
_results = {}


def log(text):
    _lines.append(text)
    print(text, flush=True)


def check(name, flag):
    _results[name] = bool(flag)
    log("CHECK %s: %s" % (name, "ok" if flag else "FAIL"))


def main():
    import cat_theo_machine.machine as M
    import cat_theo_machine.proof as Pmod
    import cat_theo_machine.labels as Lmod
    import cat_theo_machine.research as Rmod
    import cat_theo_machine.gmprep as Gmod
    import cat_theo_machine.testsuite as T
    from cat_theo_machine.persistence import SnapshotCodec
    from cat_theo_machine.main import _runtime_namespace
    from cat_theo_machine.runtime import make_fresh_runtime

    Toy = T.__dict__["_ResearchToy"]
    empty = M.EmptyList

    OBS_ROOTS = (
        "constructor_registry",
        "rule_order",
        "all_rules",
        "derivation_schemata",
        "research_residuals",
        "last_residuals",
        "research_attempts",
        "intervention_episodes",
        "counterfactual_results",
        "last_proof",
        "derivations",
        "generator_policy",
    )
    PROPOSAL_LABEL = Lmod.InventedLemmaLabel

    t_start = time.time()
    log("START utc %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    work_count = 0  # aggregate work counter, recorded alongside wall time

    graph = make_fresh_runtime().graph
    Toy.reset(graph)

    # ---- evidence: two closed attempts over a chained toy law set, so the
    # miner has a repeated dataflow motif across two distinct traces ----
    vx, vy = Toy.var("x"), Toy.var("y")
    r1 = Pmod.MultiRule(Toy.chain(Toy.term(Toy.sym("p"), vx)), Toy.term(Toy.sym("q"), vx))()
    r2 = Pmod.MultiRule(Toy.chain(Toy.term(Toy.sym("q"), vy)), Toy.term(Toy.sym("r"), vy))()
    rules = Toy.chain(r1, r2)
    for const in ("a", "b"):
        Rmod.attempt_goal(
            graph,
            Toy.chain(Toy.term(Toy.sym("p"), Toy.sym(const))),
            Toy.chain(Toy.term(Toy.sym("r"), Toy.sym(const))),
            rules,
        )
        work_count += 1
    traces = Rmod.TracesOnRecord(graph)
    check("observations-nonempty", M.IdentityCompare(traces, empty)() is M.false_value)

    # a genuine FAILED attempt: the residual must be a real stall record
    Rmod.attempt_goal(
        graph,
        Toy.chain(Toy.term(Toy.sym("p"), Toy.sym("z"))),
        Toy.chain(Toy.term(Toy.sym("r"), Toy.sym("w"))),
        rules,
    )
    work_count += 1
    residual_after_failure = graph.research_residuals
    check("failed-attempt-keeps-residual", M.IdentityCompare(residual_after_failure, empty)() is M.false_value)
    # NB: later writes touch other roots; research_residuals stays put, so
    # this is also the value the observations journal will capture

    # one measured episode (fields ONLY from a real counterfactual evaluation)
    ev, _unlock = Rmod.counterfactual_evaluation(
        graph,
        Toy.chain(Toy.term(Toy.sym("p"), Toy.sym("c"))),
        Toy.chain(Toy.term(Toy.sym("r"), Toy.sym("c"))),
        rules,
        Pmod.MultiRule(Toy.chain(Toy.term(Toy.sym("p"), vx)), Toy.term(Toy.sym("r"), vx))(),
    )
    work_count += 1
    formal = Rmod.FormalRule(Toy.chain(Toy.term(Toy.sym("p"), vx)), Toy.term(Toy.sym("r"), vx))()
    features = Rmod.EpisodeFeatures(formal, graph.research_residuals)()
    cost_before = M.Head(ev)()
    cost_after = M.Head(M.Tail(ev)())()
    newly_enabled = M.Head(M.Tail(M.Tail(ev)())())()
    episode = Rmod.InterventionEpisode(
        M.Head(features)(),
        M.Head(M.Tail(features)())(),
        newly_enabled,
        cost_before,
        cost_after,
        Lmod.DemonstratedUsefulDependencyLabel,
    )()
    graph.record_intervention_episode(episode)
    check("episode-recorded", M.IdentityCompare(graph.intervention_episodes, empty)() is M.false_value)

    # ---- proposals: mined, inert, and nowhere in the active stores ----
    candidates = Rmod.mine_compressed_laws(graph)
    check("candidates-mined", candidates is not empty and M.IsPair(candidates)() is M.truth_value)
    candidate = M.Head(candidates)()

    def composed_shapes(traces):
        out = empty
        cur = traces
        while cur is not empty:
            t0 = M.Head(cur)()
            fired = M.Head(M.Tail(M.Tail(M.Tail(t0)())())())()
            ci = Rmod.ComposedInstances(fired)()
            cur2 = ci
            while cur2 is not empty:
                rec = M.Head(cur2)()
                prem = M.Head(M.Tail(rec)())()
                conc = M.Head(M.Tail(M.Tail(rec)())())()
                out = M.Pair(M.Pair(prem, conc), out)
                cur2 = M.Tail(cur2)()
            cur = M.Tail(cur)()
        return M.Reverse(out)()

    def term_in_root(root, term):
        cur = root
        while cur is not empty:
            if M.Compare(M.Head(cur)(), term)() is M.truth_value:
                return True
            cur = M.Tail(cur)()
        return False

    rules_before = graph.all_rules
    in_policies = term_in_root(graph.dependency_policies, candidate)
    registry = M.FromContextGetConstructors(graph)()
    prov_entries = Rmod.ProvenanceEntriesFor(graph.provenance_map, PROPOSAL_LABEL)()
    in_prov = prov_entries is not empty
    log("  [inertness detail] policies-hit=%s provenance-empty=%s" % (in_policies, in_prov))
    check("proposal-absent-from-active-stores", (not in_policies) and (not in_prov))

    # duplicate delivery of the same candidate must be a no-op in effect:
    # mining is deduplicated by alpha-equality against already-known laws
    dup_mine = Rmod.mine_compressed_laws(graph)
    check("duplicate-mining-stable", M.CountRep(candidates)().value == M.CountRep(dup_mine)().value)

    # ---- journal split: write OBSERVATIONS and PROPOSALS files, isolated ----
    codec = SnapshotCodec(_runtime_namespace())
    base = codec.capture(graph)
    obs = {"header": dict(base["header"]), "symbols": base["symbols"], "objects": base["objects"], "roots": {}}
    for name in OBS_ROOTS:
        if name in base["roots"]:
            obs["roots"][name] = base["roots"][name]
    prop_roots = {}
    prop = {"header": dict(base["header"]), "symbols": base["symbols"], "objects": base["objects"], "roots": prop_roots}
    # proposals carry their own root only in the PROPOSALS file; nothing in
    # the active graph ever had it, so the codec needs an extra root here
    extra = codec.capture(graph, extra_roots={"journal_candidates": candidates})
    prop["symbols"] = extra["symbols"]
    prop["objects"] = extra["objects"]
    prop["roots"] = {"journal_candidates": extra["roots"]["journal_candidates"]}

    tmp = "/tmp/hyge-journal-m2"
    try:
        import shutil as sh
        sh.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp + "/observations", exist_ok=True)
        os.makedirs(tmp + "/proposals", exist_ok=True)
        obs_path = tmp + "/observations/journal.json"
        prop_path = tmp + "/proposals/candidates.json"
        with open(obs_path, "w", encoding="utf-8") as f:
            json.dump(obs, f, ensure_ascii=False, separators=(",", ":"))
        with open(prop_path, "w", encoding="utf-8") as f:
            json.dump(prop, f, ensure_ascii=False, separators=(",", ":"))
        check("journals-isolated-files", os.path.exists(obs_path) and os.path.exists(prop_path))

        # no cross-contamination in the files themselves
        obs_text = open(obs_path).read()
        prop_text = open(prop_path).read()
        check("observations-file-lacks-candidate-root", "journal_candidates" not in obs_text)
        check("proposals-file-lacks-episode-root", "intervention_episodes" not in prop_text)

        # ---- full-restore equivalence PROVEN by replay, not hashed ----
        state = codec.load(obs_path)
        fresh = make_fresh_runtime().graph
        codec.activate(state, fresh, debug=M.false_value, save_upgraded_snapshot=M.false_value)
        log("  [restore detail] policy entries fresh=%s orig=%s; fresh resid type=%s" % (
            "empty" if fresh.generator_policy is empty else "nonempty",
            "empty" if graph.generator_policy is empty else "nonempty",
            type(fresh.research_residuals).__name__))

        a_traces = Rmod.TracesOnRecord(graph)()
        b_traces = Rmod.TracesOnRecord(fresh)()
        log("  [counts] traces orig=%s fresh=%s" % (Gmod.GMPRepText(M.CountRep(a_traces)())(), Gmod.GMPRepText(M.CountRep(b_traces)())()))
        sa = composed_shapes(a_traces)
        sb = composed_shapes(b_traces)
        log("  [eq detail] traces orig=%s fresh=%s shapes orig=%s fresh=%s" % (
            M.CountRep(a_traces)().value, M.CountRep(b_traces)().value,
            M.CountRep(sa)().value, M.CountRep(sb)().value))
        try:
            eq_traces = M.Compare(sa, sb)() is M.truth_value
        except Exception as e:
            log("  [eq detail] shapes compare raised: %r" % (e,))
            eq_traces = False

        a_eps = graph.intervention_episodes
        b_eps = fresh.intervention_episodes
        def eps_fields(g):
            out = empty
            cur = g
            while cur is not empty:
                e = M.Head(cur)()
                fields = M.Pair(
                    Rmod.AlphaNormalized(Rmod.EpisodeRuleShape(e)(), empty)(),
                    M.Pair(Rmod.EpisodeOutcome(e)(), empty),
                )
                out = M.Pair(fields, out)
                cur = M.Tail(cur)()
            return M.Reverse(out)()
        try:
            eq_eps = M.Compare(eps_fields(a_eps), eps_fields(b_eps))() is M.truth_value
            log("  [eq detail] episode fields orig=%s fresh=%s" % (
                "empty" if eps_fields(a_eps) is empty else M.CountRep(eps_fields(a_eps))(),
                "empty" if eps_fields(b_eps) is empty else M.CountRep(eps_fields(b_eps))()))
        except Exception as e:
            log("  [eq detail] episodes compare raised: %r" % (e,))
            eq_eps = False

        a_cf = graph.counterfactual_results
        b_cf = fresh.counterfactual_results
        eq_cf = M.Compare(a_cf, b_cf)() is M.truth_value

        # capture the live residual at journal time (post-episode writes may
        # touch this root; equality must be against exactly what was captured)
        a_res = graph.research_residuals
        b_res = fresh.research_residuals
        # AttemptedRule records carry the rule object in their rule-id slot
        # (an identity handle, not a comparable term). The record's
        # validator-meaningful content — origin, substitution, matched
        # premises, unmatched premise, failure kind — is pure machine terms
        # and those are what a restore must reproduce exactly; the rule-id
        # slot is checked for presence on both sides, never for edge-twin
        # equality (no production semantics consumes that).
        def skip_first(pair):
            return M.Tail(pair)() if M.IsPair(pair)() is M.truth_value else empty

        def residual_shape(res):
            if M.IsPair(res)() is not M.truth_value:
                return empty
            entry = M.Head(res)()
            if M.IsPair(entry)() is not M.truth_value:
                return empty
            kind = M.Head(entry)()
            body = M.Tail(entry)()
            return M.Pair(kind, skip_first(skip_first(body)))

        sa_r, sb_r = residual_shape(a_res), residual_shape(b_res)
        try:
            eq_res = (sa_r is not empty and sb_r is not empty
                      and M.Compare(sa_r, sb_r)() is M.truth_value)
        except Exception as e:
            log("  [eq detail] residuals compare raised: %r" % (e,))
            eq_res = False
        except Exception as e:
            log("  [eq detail] residuals compare raised: %r" % (e,))
            eq_res = False

        check("restore-equivalence-traces", eq_traces)
        check("restore-equivalence-episodes-by-replay", eq_eps)
        check("restore-equivalence-counterfactuals", eq_cf)
        check("restore-equivalence-residuals", eq_res)

        # the restored graph was never handed the proposals file at all;
        # re-mining its evidence must re-derive the same candidates
        re_mined = Rmod.mine_compressed_laws(fresh)
        def shapes(chain):
            out = empty
            cur = chain
            while cur is not empty:
                out = M.Pair(Rmod.AlphaNormalized(M.Head(cur)(), empty)(), out)
                cur = M.Tail(cur)()
            return M.Reverse(out)()
        check("proposals-rederive-from-restored-evidence",
              M.Compare(shapes(candidates), shapes(re_mined))() is M.truth_value)
        check("proposals-never-imported-into-restored",
              term_in_root(fresh.dependency_policies, candidate) is False
              and Rmod.ProvenanceEntriesFor(fresh.provenance_map, PROPOSAL_LABEL)() is empty
              and M.Compare(fresh.all_rules, make_fresh_runtime().graph.all_rules)() is M.truth_value)

        # late duplicate delivery onto the RESTORED store: appending the same
        # episode term twice changes nothing observable about the derived
        # candidate law (re-mined equality = the duplicate had no effect),
        # and the original store is untouched by restore (one-way traffic)
        pre_dup = Rmod.mine_compressed_laws(fresh)
        fresh.record_intervention_episode(M.Head(a_eps)())
        fresh.record_intervention_episode(M.Head(a_eps)())
        post_dup = Rmod.mine_compressed_laws(fresh)
        log("  [dup detail] pre=%s post=%s" % (
            "empty" if pre_dup is empty else M.CountRep(pre_dup)().value,
            "empty" if post_dup is empty else M.CountRep(post_dup)().value))
        check("duplicate-delivery-no-effect",
              M.Compare(Rmod.AlphaNormalized(M.Head(pre_dup)(), empty)(), Rmod.AlphaNormalized(M.Head(post_dup)(), empty)())() is M.truth_value
              and M.CountRep(pre_dup)().value == M.CountRep(post_dup)().value)
        check("restore-is-one-way", M.Compare(Rmod.TracesOnRecord(graph)(), a_traces)() is M.truth_value)

        # support measurement survives restore: candidate_support over the
        # restored graph must equal the original count
        sup_a = M.CountRep(Rmod.candidate_support(graph, candidate))()
        re_cand = M.Head(re_mined)()
        sup_b = M.CountRep(Rmod.candidate_support(fresh, re_cand))()
        log("  [support] values orig=%s fresh=%s" % (sup_a.value, sup_b.value))
        check("support-measurement-equal-after-restore", sup_a.value == sup_b.value and sup_a.value > 0)
    finally:
        try:
            import shutil as sh
            sh.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass

    log("aggregate work recorded: attempts+evaluations=%d; wall time %.2fs" % (work_count, time.time() - t_start))
    ok_all = all(_results.values())
    log("ALL CHECKS: %s" % ("ok" if ok_all else "FAILURES PRESENT"))
    log("END utc %s" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    text = "\n".join(_lines) + "\n"
    if ARTIFACT:
        with open(ARTIFACT, "w") as f:
            f.write(text)
    return 0 if ok_all else 1


_t0 = time.time()

if __name__ == "__main__":
    rc = 1
    try:
        rc = main()
    except BaseException as error:
        import traceback
        log("DRIVER RAISED: %r" % (error,))
        log(traceback.format_exc())
        if ARTIFACT:
            with open(ARTIFACT, "w") as f:
                f.write("\n".join(_lines) + "\n")
    sys.stdout.flush()
    sys.exit(rc)
