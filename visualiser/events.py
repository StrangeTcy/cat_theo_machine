"""Event vocabulary for the passive hypergraph observer.

This module runs *inside the observed Machine process* (see ``tap.py``). It
translates the machine's hypergraph roots into JSON-safe event dictionaries.

It never writes to the machine. Every read goes through the public accessors
(``Head``, ``Tail``, ``IsPair``, ``PrettyTerm``) and the graph's own root
attributes; nothing here calls an edge that mutates state.

Identity model
--------------
A carrier entity is identified by the text ``PrettyTerm`` renders for it, which
is exactly the equality a reader of the graph would use ("``hub``" is the same
vertex wherever it appears). Anonymous atoms all render as ``<?>``, so those are
keyed by a host-side ordinal instead -- object identity has no machine analogue
and an anonymous ``Thingy`` has no term-derived key. That is the sanctioned
host-layer exception the delegation charter names for ``persistence.py``.

Hyperedge semantics
-------------------
A graph hyperedge is ``Pair(relation, args)``. It is emitted as a *hyperedge
node* carrying the ids of its arguments in order, one id per argument, so an
n-ary edge keeps its arity and its argument positions. Nothing is flattened into
pairwise edges at this layer; the browser draws one incidence link per argument.
"""
import os
import sys
import time

from cat_theo_machine import machine as M
from cat_theo_machine import proof as Proofmod

from .protocol import EVENT_VERSION

#: ``PrettyTerm`` renders every anonymous atom this way.
ANON_TEXT = "<?>"


def machine_identity():
    """Provenance for the header event: who produced this stream."""
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return {
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "pid": os.getpid(),
        "argv": list(sys.argv),
        "cwd": os.getcwd(),
        "package": "cat_theo_machine",
        "package_root": package_root,
    }


class ChainReader:
    """Read a machine chain into host items.

    ``while IsPair`` walking is the machine's own predicate; the host list it
    fills is a reporting structure, never a machine value.
    """

    @staticmethod
    def items(chain):
        out = []
        current = chain
        while M.IsPair(current)() is M.truth_value:
            out.append(M.Head(current)())
            current = M.Tail(current)()
        return out


class TermNamer:
    """Stable display identity for machine terms.

    ``PrettyTerm`` is the renderer the rest of the repository uses for display.
    Two terms compare equal exactly when they render the same text for named
    entities, so the text is a sound key for anything with a name. Anonymous
    atoms are the exception: they all render ``<?>``, so each distinct object
    gets an ordinal, assigned on first sight and reused afterwards.
    """

    def __init__(self, registry):
        self.registry = registry
        self._anon_by_object = {}
        self._anon_count = 0
        self._text_by_object = {}

    def text(self, term):
        key = id(term)
        cached = self._text_by_object.get(key)
        if cached is not None:
            return cached
        try:
            rendered = M.PrettyTerm(term, self.registry)()
        except Exception:
            rendered = str(term)
        self._text_by_object[key] = rendered
        return rendered

    def key(self, term):
        """Display id for a term: its text, or an ordinal for anonymous atoms."""
        rendered = self.text(term)
        if rendered != ANON_TEXT:
            return "t:" + rendered
        marker = id(term)
        ordinal = self._anon_by_object.get(marker)
        if ordinal is None:
            ordinal = self._anon_count
            self._anon_by_object[marker] = ordinal
            self._anon_count = ordinal + 1
        return "anon:" + str(ordinal)

    def label(self, term):
        rendered = self.text(term)
        if rendered != ANON_TEXT:
            return rendered
        return self.key(term).replace("anon:", "anonymous-")

    def constructor(self, term):
        try:
            found = M.GetConstructor(term, self.registry)()
        except Exception:
            return ""
        if M.IdentityCompare(found, M.EmptyList)() is M.truth_value:
            return ""
        try:
            rendered = M.PrettyTerm(M.Head(found)(), self.registry)()
        except Exception:
            return ""
        return "" if rendered == ANON_TEXT else rendered


class GraphDigest:
    """A full, cached reading of one hypergraph.

    ``read()`` walks every root and returns ``{"nodes", "edges", "counts"}``.
    Item dictionaries are cached by display key, so a poll that changes nothing
    costs one chain walk and no rendering.
    """

    def __init__(self, graph, runtime=None, rule_cap=60, include_rules=True):
        self.graph = graph
        self.runtime = runtime
        self.rule_cap = rule_cap
        self.include_rules = include_rules
        self.registry = M.FromContextGetConstructors(graph)()
        self.namer = TermNamer(self.registry)
        self._node_cache = {}
        self._edge_cache = {}
        self._rule_cache = {}
        self._rule_text_cache = {}

    # -- roots ------------------------------------------------------------
    def _nodes_chain(self):
        return self.graph.nodes

    def _edges_chain(self):
        return self.graph.edges

    def _rules_chain(self):
        if self.runtime is not None:
            try:
                return self.runtime.ordered_rules()
            except Exception:
                pass
        try:
            return M.FromContextGetRuleOrder(self.graph)()
        except Exception:
            return M.EmptyList

    def _root_chain(self, name):
        """One of the graph's derived roots, by name, read fresh each time.

        The graph replaces these attributes whenever its context changes, so the
        reading has to come from the object, not from a snapshot taken once.
        """
        try:
            if name == "derivations":
                return self.graph.derivations
            if name == "search_history":
                return self.graph.search_history
            if name == "search_jobs":
                return self.graph.search_jobs
        except AttributeError:
            return None
        return None

    def _root_count(self, name):
        chain = self._root_chain(name)
        if chain is None:
            return 0
        if M.IsPair(chain)() is not M.truth_value:
            return 0
        count = 0
        current = chain
        while M.IsPair(current)() is M.truth_value:
            count += 1
            current = M.Tail(current)()
        return count

    # -- items ------------------------------------------------------------
    def _node_item(self, term):
        key = self.namer.key(term)
        cached = self._node_cache.get(key)
        if cached is not None:
            return cached
        item = {
            "id": key,
            "kind": "node",
            "label": self.namer.label(term),
            "term": self.namer.text(term),
            "constructor": self.namer.constructor(term),
            "declared": True,
            "source": "node store",
        }
        self._node_cache[key] = item
        return item

    def _term_item(self, term):
        key = self.namer.key(term)
        cached = self._node_cache.get(key)
        if cached is not None:
            return cached
        item = {
            "id": key,
            "kind": "term",
            "label": self.namer.label(term),
            "term": self.namer.text(term),
            "constructor": self.namer.constructor(term),
            "declared": False,
            "source": "hyperedge argument",
        }
        self._node_cache[key] = item
        return item

    def _edge_parts(self, edge):
        """(relation text, argument terms, result terms) for a graph hyperedge.

        Canonical hyperedges are ``Pair(relation, args)``; registered ``Edge``
        subclasses expose ``EdgeInputs``/``EdgeResults`` instead. Both shapes are
        read, and neither is flattened.
        """
        if M.IsPair(edge)() is M.truth_value:
            relation = self.namer.text(M.Head(edge)())
            arguments = ChainReader.items(M.Tail(edge)())
            return relation, arguments, []
        try:
            arguments = ChainReader.items(M.EdgeInputs(edge)())
        except Exception:
            arguments = []
        try:
            results = ChainReader.items(M.EdgeResults(edge)())
        except Exception:
            results = []
        try:
            relation = self.namer.text(edge)
        except Exception:
            relation = str(edge)
        return relation, arguments, results

    def _edge_item(self, edge):
        relation, arguments, results = self._edge_parts(edge)
        argument_keys = [self.namer.key(term) for term in arguments]
        result_keys = [self.namer.key(term) for term in results]
        key = "e:" + relation + "(" + ",".join(argument_keys) + ")"
        if result_keys:
            key = key + "->" + ",".join(result_keys)
        cached = self._edge_cache.get(key)
        if cached is not None:
            return cached, arguments, results
        item = {
            "id": key,
            "kind": "hyperedge",
            "label": relation,
            "term": self.namer.text(edge),
            "constructor": self.namer.constructor(edge),
            "relation": relation,
            "arity": len(argument_keys) + len(result_keys),
            "arguments": argument_keys,
            "results": result_keys,
            "source": "edge store",
        }
        self._edge_cache[key] = item
        return item, arguments, results

    def _rule_item(self, rule):
        # Compiling can hand back a fresh object per call, so remember the text
        # against the object to keep both the cost and the ids stable.
        text = self._rule_text_cache.get(id(rule))
        if text is None:
            try:
                text = Proofmod.PrettyRule(rule, self.registry)()
            except Exception:
                text = "<rule>"
            self._rule_text_cache[id(rule)] = text
        key = "r:" + text
        cached = self._rule_cache.get(key)
        if cached is not None:
            return cached, [], []
        try:
            premises = ChainReader.items(M.RulePremises(rule)())
        except Exception:
            premises = []
        try:
            replacement = [M.RuleReplacement(rule)()]
        except Exception:
            replacement = []
        item = {
            "id": key,
            "kind": "rule",
            "label": text,
            "term": text,
            "constructor": "",
            "arity": len(premises) + len(replacement),
            "arguments": [self.namer.key(term) for term in premises],
            "results": [self.namer.key(term) for term in replacement],
            "source": "rule store",
        }
        self._rule_cache[key] = item
        return item, premises, replacement

    # -- read -------------------------------------------------------------
    def read(self):
        """Read every root. Returns item tables keyed by display id."""
        nodes = {}
        edges = {}

        for term in ChainReader.items(self._nodes_chain()):
            item = self._node_item(term)
            nodes[item["id"]] = item

        for edge in ChainReader.items(self._edges_chain()):
            item, arguments, results = self._edge_item(edge)
            edges[item["id"]] = item
            for term in arguments:
                term_item = self._term_item(term)
                nodes.setdefault(term_item["id"], term_item)
            for term in results:
                term_item = self._term_item(term)
                nodes.setdefault(term_item["id"], term_item)

        rule_total = 0
        if self.include_rules:
            for rule in ChainReader.items(self._rules_chain()):
                rule_total += 1
                if rule_total > self.rule_cap:
                    continue
                item, premises, replacement = self._rule_item(rule)
                edges[item["id"]] = item
                for term in premises + replacement:
                    term_item = self._term_item(term)
                    nodes.setdefault(term_item["id"], term_item)

        counts = {
            "nodes": len(nodes),
            "edges": len(edges),
            "rule_total": rule_total,
            "derivations": self._root_count("derivations"),
            "search_history": self._root_count("search_history"),
            "search_jobs": self._root_count("search_jobs"),
        }
        return {"nodes": nodes, "edges": edges, "counts": counts}


class EventStream:
    """Builds the JSONL records the journal holds.

    One vocabulary for the whole pipeline: the observed process, the server's
    recorder and a replay all speak ``session.start`` / ``nodes.added`` /
    ``edges.added`` / ``items.removed`` / ``counts`` / ``session.stop``.
    """

    def __init__(self, source=None):
        self.source = source or {}
        self.seq = 0
        self.started = time.time()

    def _stamp(self, record):
        record["v"] = EVENT_VERSION
        record["seq"] = self.seq
        record["t"] = round(time.time(), 6)
        record["elapsed"] = round(time.time() - self.started, 6)
        self.seq += 1
        return record

    def start(self, machine=None, journal=None, note=None):
        return self._stamp(
            {
                "type": "session.start",
                "machine": machine or {},
                "source": self.source,
                "journal": journal,
                "note": note,
            }
        )

    def added(self, nodes=(), edges=()):
        records = []
        node_items = list(nodes)
        edge_items = list(edges)
        if node_items:
            records.append(self._stamp({"type": "nodes.added", "items": node_items}))
        if edge_items:
            records.append(self._stamp({"type": "edges.added", "items": edge_items}))
        return records

    def removed(self, node_ids=(), edge_ids=()):
        if not node_ids and not edge_ids:
            return []
        return [
            self._stamp(
                {
                    "type": "items.removed",
                    "nodes": list(node_ids),
                    "edges": list(edge_ids),
                }
            )
        ]

    def counts(self, counts):
        return self._stamp({"type": "counts", "counts": counts})

    def stop(self, reason):
        return self._stamp({"type": "session.stop", "reason": reason})
