"""Partitioned prover swarm: a search frontier split into disjoint work units.

The unit of work is one **frontier node** of a paused `SearchJob`. A frontier is
a machine chain of `SearchState` terms; this module turns it into a list of
units, each carrying

* `frontier_index` -- the node's position in the frontier, which is the *only*
  thing the merge is allowed to order by (see `merge`);
* `digest` -- a stable hash of the node's canonical text, the partition key;
* `shard` -- `digest` mapped onto a shard, i.e. which worker is offered it first.

Why single nodes and not whole shards: a depth-first search pops the frontier in
order and explores each node's subtree before moving to the next sibling, so the
first success found by a sequential search is the success at the *lowest-index*
frontier node that has one. Giving each worker a whole shard would hide which
node inside the shard produced the answer, and the merge could no longer
reproduce the sequential choice. One node per unit keeps that reproducible, and
makes disjointness and coverage a statement about a bijection between units and
frontier nodes rather than about set arithmetic over shards.

Machine purity (DAG §5.2): the frontier, its states and every term inside them
stay machine values. Python appears only in the scheduling bookkeeping -- the
digest strings, the shard integers, the unit records -- because a hash of a
canonical rendering has no machine analogue. `PrettyTerm` is used as the
canonical rendering; it is a printer over term structure, so two structurally
equal states print alike. `validation/test27_distributed_prover_swarm.py` pins
that, including across processes, because a partition function that is not
reproducible in a fresh runtime is not a partition function.

Transport: a work unit travels as a **snapshot**, not as text and not as
pickle. The coordinator builds a job whose frontier is exactly the unit's node,
stores it with `graph.store_search_job`, and saves the runtime; the worker calls
`boot_from_snapshot` and finds its job, node for node. Measured on a real unit:
the node's digest is identical on both sides of the round trip, and booting from
a unit snapshot took 7.6 s against 17 s to boot the same runtime from packs -- so
the faithful transport is also the cheaper one.

One trap, because it cost a diagnosis: `persistence` restores the constructor
registry through `multiprocessing.get_context("spawn")`, and a spawned child
re-imports the `__main__` module. A driver script without an
`if __name__ == "__main__"` guard therefore re-executes itself inside every
registry shard worker, each of which dies before writing its output, and
`boot_from_snapshot` fails with "registry shard 1/2 failed: no output produced".
That message reads like a corrupt snapshot; it is not. Guard the entry point.

Measured, on `engel_e2` from the `engel-blackboard` pack (a 3-step expansion, so
a frontier of 4 nodes, then each run taken to a terminal status in its own
process -- one process per run, because a second search inside a booted runtime
is memoised and is not a fresh one):

    baseline, whole frontier    success   plan 124d4980ae0799f6  cost cda29f2b48da3570   33.6 s
    unit 0 (5fd41873a2)         success   plan 124d4980ae0799f6  cost cda29f2b48da3570   32.4 s
    unit 1 (52f14d226f)         failure   no plan                                          2.5 s
    unit 2 (ede2a5cb0b)         failure   no plan                                          2.2 s
    unit 3 (2bf577cc28)         failure   no plan                                          1.7 s

The merge picks unit 0 -- the lowest index that succeeded -- and its plan and
proof cost are byte-for-byte the baseline's. That is the claim this module
exists to make, measured rather than argued: partitioning the frontier and
merging by frontier index reproduces the unpartitioned proof exactly.

It also fixes the honest speedup number, which is not flattering. The proof
lives entirely in one branch, so a four-way partition does not shorten the
critical path (32.4 s against 33.6 s) and the partitioned run does *more* total
work (38.8 s of unit time against 33.6 s), because each unit re-expands from the
root. What parallelism buys here is that the three dead branches are retired
concurrently in about two seconds each instead of in sequence. Record that as
the finding; do not tune it until it looks better.

Survey of the rest of the agenda, since the choice of problem is not free: Tao
1.1 and sqrt2/3/4_real are settled by a root fast path in a single step and
leave no frontier at all, the two Engel coin cases fail immediately, and
`engel_e1` expands to a frontier of 4 but exhausts at 7 expanded nodes without a
proof. `engel_e2` is the only case that both partitions and proves.

One caveat on the snapshot transport, measured rather than assumed. Round-tripping
the expanded state through `save_runtime` / `boot_from_snapshot` changes the plan
the search goes on to find, though not what the proof costs:

    baseline, booted from packs       plan 124d4980ae0799f6  cost cda29f2b48da3570
    unit 0,   booted from packs       plan 124d4980ae0799f6  cost cda29f2b48da3570
    baseline, booted from a snapshot  plan 2ad79637693297dd  cost cda29f2b48da3570
    unit 0,   booted from a snapshot  plan 2ad79637693297dd  cost cda29f2b48da3570

So the partition-and-merge equality holds inside either world -- a unit and the
unpartitioned run agree exactly, whichever way both were started -- but a
snapshot-restored swarm reproduces a proof of the same cost rather than the
byte-identical plan a pack-booted search finds. Same expanded count (5), same
proof cost, different plan: the restored state leads the search to a different
branch of equal cost. Chasing that is the snapshot codec's business (W12), not
this layer's, so it is recorded here as a boundary condition and the suite
asserts what is actually true: plan equality within one transport, and proof-cost
equality across transports and worker counts.
"""

from __future__ import annotations

import hashlib

from .. import machine as M

# Hex characters of the digest read as the shard index. Eight hex digits is 32
# bits of the hash: far more than any shard count this swarm runs with, so the
# mapping is uniform without being sensitive to the digest's low bits.
DIGEST_HEX_WIDTH = 8


def node_text(state, registry):
    """Canonical text of one frontier node -- the basis of its partition key."""
    return M.PrettyTerm(M.SearchStateCurrent(state)(), registry)()


def canonical_digest(text):
    """Stable digest of a canonical rendering. Text in, hex out."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def shard_of(digest, shard_count):
    """Map a digest onto a shard. Pure, and total for any digest."""
    if shard_count < 1:
        raise ValueError("shard count must be at least 1, got " + str(shard_count))
    return int(digest[:DIGEST_HEX_WIDTH], 16) % shard_count


class Unit:
    """One frontier node, offered to the swarm as an independent job."""

    def __init__(self, unit_id, frontier_index, text, digest, shard):
        self.unit_id = unit_id
        self.frontier_index = frontier_index
        self.text = text
        self.digest = digest
        self.shard = shard

    def as_dict(self):
        return {
            "unit_id": self.unit_id,
            "frontier_index": self.frontier_index,
            "text": self.text,
            "digest": self.digest,
            "shard": self.shard,
        }


def partition_frontier(frontier, registry, shard_count, prefix="unit"):
    """Split a machine frontier into units, one per node, in frontier order.

    Returns `(units, frontier_size)`. `units[i].frontier_index == i`, so the
    caller can assert coverage (`len(units) == frontier_size`) and disjointness
    (no digest assigned to two indices) without trusting this module.
    """
    units = []
    index = 0
    rest = frontier
    while M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
        state = M.Head(rest)()
        text = node_text(state, registry)
        digest = canonical_digest(text)
        units.append(
            Unit(
                "%s-%03d-%s" % (prefix, index, digest[:10]),
                index,
                text,
                digest,
                shard_of(digest, shard_count),
            )
        )
        rest = M.Tail(rest)()
        index += 1
    return units, index


def shard_sizes(units, shard_count):
    """How many units each shard was offered. Empty shards are legal."""
    sizes = [0] * shard_count
    for unit in units:
        sizes[unit.shard] += 1
    return sizes


def partition_is_exact(units, frontier_size):
    """Disjointness and coverage in one predicate.

    Coverage: every frontier node became exactly one unit, and the indices are
    0..n-1 with no gaps. Disjointness: no two units claim the same node, which
    for a digest-keyed partition means no index repeats. Both are checked here
    so the suite asserts them from the returned data rather than assuming them.
    """
    if len(units) != frontier_size:
        return False
    indices = [unit.frontier_index for unit in units]
    if sorted(indices) != list(range(frontier_size)):
        return False
    return len(set(indices)) == len(indices)


def merge(results):
    """Pick the winning unit result, independent of arrival order.

    `results` is an iterable of records, each with at least `frontier_index`,
    `status` and (on success) whatever the caller needs to rebuild the proof.
    The winner is the *successful* result with the lowest frontier index, which
    is exactly the node a sequential depth-first search over the same frontier
    would have reached first. Ties are impossible -- one unit per node -- but a
    digest tiebreak is kept so the choice is total even if a caller ever hands
    over two results for one node.

    Returns `(winner, ordered)` where `ordered` is every result sorted by the
    same key, so a caller can show the selection did not depend on the order it
    was given.
    """
    ordered = sorted(results, key=lambda record: (record.get("frontier_index", 0), record.get("digest", "")))
    winner = None
    for record in ordered:
        if record.get("status") == "ok":
            winner = record
            break
    return winner, ordered


# --------------------------------------------------------------------- planning
#
# The expansion below is the expensive part of a swarm run -- measured at 17 s
# against a 20 s pack boot -- and it is *identical* in every worker, because
# every worker would otherwise repeat it from the root. So it happens once, in
# the coordinator, and each unit travels as a snapshot that boots in 7.6 s. That
# is the difference between a suite that fits its wall-clock budget and one that
# costs 330 s.


def nat(count, registry):
    """A machine natural number, built the only way counting is allowed here."""
    value = M.Zero
    for _ in range(count):
        pair = M.Succ(value, registry)()
        value = M.Head(pair)()
        registry = M.Head(M.Tail(pair)())()
    return value, registry


def step_limit(graph, rules, registry):
    """The engine's own bound on steps, as the search worker derives it."""
    limit = graph.next_rule_index
    empty = M.IdentityCompare(limit, M.EmptyList)() is M.truth_value
    if empty or M.NatEq(limit, M.Zero, registry)() is M.truth_value:
        representation = M.CountRep(rules)()
        limit = M.Atom()
        limit.value = representation
    return limit


def root_job(start, goal, rules, heuristic, limit):
    """A search job at the root: one frontier node, nothing expanded yet."""
    return M.SearchJob(
        start,
        goal,
        rules,
        heuristic,
        M.SearchRunningLabel,
        M.Pair(M.SearchState(start, M.EmptyList, M.EmptyList, limit)(), M.EmptyList),
        M.Zero,
        M.Zero,
        M.Zero,
        M.EmptyList,
        M.EmptyList,
        M.EmptyList,
        M.EmptyList,
        M.one,
    )()


def rebuild_job(job, frontier, status=None):
    """The same job with a different frontier -- that is all a work unit is.

    Everything the search accumulated on the way to this frontier (the visited
    set, the theorem-rule cache, the rewrite rules, the counters) is carried
    across unchanged, so a unit resumes the search rather than restarting it.
    """
    return M.SearchJob(
        M.SearchJobStart(job)(),
        M.SearchJobGoal(job)(),
        M.SearchJobRules(job)(),
        M.SearchJobHeuristic(job)(),
        M.SearchRunningLabel if status is None else status,
        frontier,
        M.SearchJobExpanded(job)(),
        M.SearchJobGenerated(job)(),
        M.SearchJobFrontierPeak(job)(),
        M.EmptyList,
        M.SearchJobVisited(job)(),
        M.SearchJobTheoremRuleCache(job)(),
        M.SearchJobRewriteRules(job)(),
        None,
    )()


def expand_frontier(graph, job, registry, burst_steps, shard_count=1):
    """Run `burst_steps` of search and return the frontier it leaves behind.

    Returns `(job, registry, units, size)`. The caller owns the runtime; this
    only advances the job, which is what makes the expansion shareable -- the
    coordinator does it once and every unit inherits the result. `shard_count`
    only decides which worker is *offered* each unit first; it never changes the
    set of units.
    """
    from . import engine as _engine

    budget, registry = nat(burst_steps, registry)
    pair = _engine.SearchBurst(graph, job, budget, registry)()
    job = M.Head(pair)()
    registry = M.Head(M.Tail(pair)())()
    graph._replace_context(constructors=registry)
    frontier = M.SearchJobFrontier(job)()
    units, size = partition_frontier(frontier, registry, shard_count)
    return job, registry, units, size


def size_of(frontier):
    """How many nodes a machine frontier holds."""
    count = 0
    rest = frontier
    while M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
        rest = M.Tail(rest)()
        count += 1
    return count


def only_node(frontier, index):
    """A frontier holding exactly the node at `index`, and nothing else."""
    chosen = M.EmptyList
    rest = frontier
    position = 0
    while M.IdentityCompare(rest, M.EmptyList)() is M.false_value:
        if position == index:
            chosen = M.Pair(M.Head(rest)(), M.EmptyList)
        rest = M.Tail(rest)()
        position += 1
    return chosen


def write_unit(runtime, path, namespace, job):
    """Save a runtime holding exactly one search job: that is a work unit.

    The context is set to this job alone rather than going through
    `store_search_job`, which prepends. In practice that prepend is harmless
    here -- `store_search_job` first removes any job with the same start, goal
    and heuristic, and every unit of one problem shares all three, so the list
    never grows past one. But that is a side effect of a deduplication rule, not
    a guarantee, and a swarm over several problems would not get it. `read_unit`
    refuses a snapshot holding more than one job, so the writer states the
    invariant instead of inheriting it.
    """
    from ..runtime import save_runtime

    runtime.graph._replace_context(search_jobs=M.Pair(job, M.EmptyList))
    save_runtime(runtime, path, namespace)
    return path


def read_unit(path, namespace):
    """Boot a unit snapshot and return `(runtime, graph, registry, job)`.

    The unit is the single job the coordinator stored. A snapshot with more than
    one job in it is a bug in the writer, not something to guess about.
    """
    from ..runtime import boot_from_snapshot

    runtime = boot_from_snapshot(path, namespace)
    graph = runtime.graph
    registry = M.FromContextGetConstructors(graph)()
    jobs = M.FromContextGetSearchJobs(graph)()
    if M.IdentityCompare(jobs, M.EmptyList)() is M.truth_value:
        raise RuntimeError("unit snapshot holds no search job: " + str(path))
    job = M.Head(jobs)()
    if M.IdentityCompare(M.Tail(jobs)(), M.EmptyList)() is M.false_value:
        raise RuntimeError("unit snapshot holds more than one search job: " + str(path))
    return runtime, graph, registry, job

