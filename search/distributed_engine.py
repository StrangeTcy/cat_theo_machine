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
