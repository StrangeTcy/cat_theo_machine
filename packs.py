from __future__ import annotations

import sys
import time

from . import machine as M
from .proof import MultiRule, RewriteAction, Rule, TheoremAction


class PackStringTable:
    def __init__(self):
        self.char_atoms = ()

    def _char_atom(self, symbol):
        for entry_symbol, entry_atom in self.char_atoms:
            if entry_symbol == symbol:
                return entry_atom
        atom = M.Char(symbol)
        self.char_atoms = self.char_atoms + ((symbol, atom),)
        return atom

    def encode(self, text):
        encoded = M.EmptyList
        index = len(text)
        while index > 0:
            index = index - 1
            encoded = M.Pair(self._char_atom(text[index]), encoded)
        return encoded


class PackTreeMap:
    def __init__(self, string_table):
        self.string_table = string_table
        self.entries = ()
        self.size = 0

    def store(self, name, value):
        updated = ()
        found = M.false_value
        for entry_name, entry_value in self.entries:
            if entry_name == name:
                updated = updated + ((name, value),)
                found = M.truth_value
            else:
                updated = updated + ((entry_name, entry_value),)
        if found is M.false_value:
            updated = updated + ((name, value),)
            self.size = self.size + 1
        self.entries = updated
        return value

    def lookup(self, name):
        for entry_name, entry_value in self.entries:
            if entry_name == name:
                return entry_value
        return M.EmptyList

    def __contains__(self, name):
        for entry_name, entry_value in self.entries:
            if entry_name == name:
                return True
        return False

    def __getitem__(self, name):
        for entry_name, entry_value in self.entries:
            if entry_name == name:
                return entry_value
        raise KeyError(name)

    def __len__(self):
        return self.size


class LoadedPack:

    def __init__(self, name, description, requires, rule_map, rule_chain, schema_map, examples, phi):
        self.name = name
        self.description = description
        self.requires = requires
        self.rule_map = rule_map
        self.rule_chain = rule_chain
        self.schema_map = schema_map
        self.examples = examples
        self.phi = phi
        # Machine chain of Pair(word_chain, Pair(atom, EmptyList)):
        # every symbol this pack's compilation resolved, as terms.
        self.symbol_map = M.EmptyList


class PackLoader:
    """
    Loader for human-authored HYGE YAML knowledge packs.

    Packs are SOURCE knowledge.
    Snapshots are runtime memory.
    Do not load the same pack twice into the same graph for now.
    """

    def __init__(self, namespace):
        self.namespace = namespace
        self.string_table = PackStringTable()
        # The one place host text meets machine atoms. Every `sym:`
        # resolution is recorded here as Pair(word_chain, Pair(atom,
        # EmptyList)) -- the association itself as a machine term, so
        # nothing downstream ever needs to consult a module namespace
        # to learn what a name denotes. word_chain is the symbol text
        # as interned Char atoms, the same interning every `char:` in
        # a pack already receives.
        self.symbol_map = M.EmptyList
        self._symbol_map_names = ()

    def _chain(self, items):
        L = M.EmptyList
        for item in reversed(items):
            L = M.Pair(item, L)
        return L

    def _compile_term(self, spec, var_env=None):
        if var_env is None:
            var_env = {}

        if not isinstance(spec, dict):
            raise RuntimeError(f"Bad term spec: {spec}")

        if "sym" in spec:
            name = spec["sym"]
            if name not in self.namespace:
                raise RuntimeError(f"Unknown symbol in pack: {name}")
            atom = self.namespace[name]
            if name not in self._symbol_map_names:
                self._symbol_map_names = self._symbol_map_names + (name,)
                self.symbol_map = M.Pair(
                    M.Pair(
                        self.string_table.encode(name),
                        M.Pair(atom, M.EmptyList),
                    ),
                    self.symbol_map,
                )
            return atom

        if "var" in spec:
            name = spec["var"]
            key = str(name)
            if key not in var_env:
                var_env[key] = M.Pair(M.VarTag, M.Pair(M.Char(key), M.EmptyList))
            return var_env[key]

        if "char" in spec:
            return self.string_table._char_atom(str(spec["char"]))

        if "pair" in spec:
            pair_items = spec["pair"]
            if not isinstance(pair_items, list) or len(pair_items) != 2:
                raise RuntimeError(f"'pair' must have exactly two items: {spec}")
            return M.Pair(
                self._compile_term(pair_items[0], var_env),
                self._compile_term(pair_items[1], var_env)
            )

        if "list" in spec:
            items = spec["list"]
            if not isinstance(items, list):
                raise RuntimeError(f"'list' must be a list: {spec}")
            compiled_items = ()
            for x in items:
                compiled_items = compiled_items + (self._compile_term(x, var_env),)
            return self._chain(compiled_items)

        if "call" in spec:
            call = spec["call"]
            if "head" not in call or "args" not in call:
                raise RuntimeError(f"'call' requires 'head' and 'args': {spec}")

            head = self._compile_term(call["head"], var_env)
            args = call["args"]
            if not isinstance(args, list):
                raise RuntimeError(f"'args' must be a list: {spec}")

            compiled_args = ()
            for x in args:
                compiled_args = compiled_args + (self._compile_term(x, var_env),)
            return M.Pair(head, self._chain(compiled_args))

        raise RuntimeError(f"Unknown term form in pack: {spec}")

    def _lookup_rule(self, rid, rule_map, schema_id):
        if rid not in rule_map:
            raise RuntimeError(f"Unknown rule id '{rid}' in schema '{schema_id}'")
        return rule_map[rid]

    def _compile_rewrite_path(self, spec, schema_id):
        if not isinstance(spec, list):
            raise RuntimeError(f"'rewrite.path' must be a list in schema '{schema_id}'")

        path_items = ()
        for segment in spec:
            if segment == 0 or segment == "head" or segment == "left":
                path_items = path_items + (M.Zero,)
            elif segment == 1 or segment == "tail" or segment == "right":
                path_items = path_items + (M.one,)
            else:
                raise RuntimeError(f"Bad rewrite path segment '{segment}' in schema '{schema_id}'")
        return self._chain(path_items)

    def _compile_plan_item(self, spec, rule_map, schema_id):
        if isinstance(spec, str):
            return TheoremAction(self._lookup_rule(spec, rule_map, schema_id))()

        if not isinstance(spec, dict):
            raise RuntimeError(f"Bad plan item in schema '{schema_id}': {spec}")

        if "theorem" in spec:
            return TheoremAction(self._lookup_rule(spec["theorem"], rule_map, schema_id))()

        if "rewrite" in spec:
            rewrite_spec = spec["rewrite"]
            if not isinstance(rewrite_spec, dict):
                raise RuntimeError(f"'rewrite' plan item must be an object in schema '{schema_id}'")
            if "rule" not in rewrite_spec:
                raise RuntimeError(f"'rewrite' plan item requires 'rule' in schema '{schema_id}'")
            rule = self._lookup_rule(rewrite_spec["rule"], rule_map, schema_id)
            path = self._compile_rewrite_path(rewrite_spec.get("path", []), schema_id)
            return RewriteAction(rule, path)()

        raise RuntimeError(f"Unknown plan item form in schema '{schema_id}': {spec}")

    def load_pack_dict(self, data, graph):

        if not isinstance(data, dict):
            raise RuntimeError("Pack must be a mapping/object")

        # Each pack's symbol_map lists the associations THIS pack's
        # compilation crossed the boundary for; the loader is shared
        # across packs, so the recorder resets per load.
        self.symbol_map = M.EmptyList
        self._symbol_map_names = ()

        if data.get("format") != "hyge-pack":
            raise RuntimeError("Wrong pack format")

        if data.get("version") != 1:
            raise RuntimeError("Unsupported pack version")

        name = data.get("name", "unnamed-pack")
        description = data.get("description", "")
        requires = data.get("requires", ())
        if requires is None:
            requires = ()
        else:
            requires = tuple(requires)

        try:
            self.string_table = graph._pack_string_table
        except AttributeError:
            graph._pack_string_table = self.string_table

        try:
            loaded_pack_names = graph._loaded_pack_names
        except AttributeError:
            loaded_pack_names = PackTreeMap(self.string_table)
            graph._loaded_pack_names = loaded_pack_names

        if name in loaded_pack_names:
            raise RuntimeError(f"Pack already loaded into this graph: {name}")

        sys.stdout.write(f"Reading pack {name}...\n")
        sys.stdout.flush()
        pack_start = time.monotonic()

        rule_specs = tuple(data.get("rules", ()))
        schema_specs = tuple(data.get("schemata", ()))
        example_specs = tuple(data.get("examples", ()))

        rule_map = PackTreeMap(self.string_table)
        rule_order = ()
        all_rules = graph.all_rules
        graph_rule_order = graph.rule_order
        next_rule_index = graph.next_rule_index

        for r in rule_specs:
            rid = r["id"]
            var_env = {}
            replacement = self._compile_term(r["replacement"], var_env)
            if "premises" in r:
                premise_specs = r["premises"]
                # fuck isinstance
                # if not isinstance(premise_specs, list) or not premise_specs:
                #     raise RuntimeError(f"'premises' must be a non-empty list in rule '{rid}'")
                compiled_premises = ()
                for spec in premise_specs:
                    compiled_premises = compiled_premises + (self._compile_term(spec, var_env),)
                premises = self._chain(compiled_premises)
                rule_obj = MultiRule(premises, replacement)
            else:
                pattern = self._compile_term(r["pattern"], var_env)
                rule_obj = Rule(pattern, replacement)
            canonical_rule = rule_obj
            key = M.Atom()
            all_rules = M.TreeInsert(all_rules, key, canonical_rule, M.AllConstructors)()
            graph_rule_order = M.Pair(canonical_rule, graph_rule_order)

            rule_map.store(rid, canonical_rule)
            rule_order = rule_order + (canonical_rule,)

        rule_chain = self._chain(rule_order)

        schema_map = PackTreeMap(self.string_table)
        derivation_schemata = graph.derivation_schemata

        for s in schema_specs:
            sid = s["id"]
            var_env = {}
            start = self._compile_term(s["start"], var_env)
            goal = self._compile_term(s["goal"], var_env)

            plan_specs = s["plan"]
            plan_rules = ()
            for spec in plan_specs:
                plan_rules = plan_rules + (self._compile_plan_item(spec, rule_map, sid),)

            plan_chain = self._chain(plan_rules)
            entry = M.Pair(start, M.Pair(goal, M.Pair(plan_chain, M.EmptyList)))
            key = M.Atom()
            derivation_schemata = M.TreeInsert(derivation_schemata, key, entry, M.AllConstructors)()
            schema_map.store(sid, (start, goal, plan_chain))

        examples = PackTreeMap(self.string_table)
        phi = self._compile_term(data["phi"], {})

        for e in example_specs:
            eid = e["id"]
            var_env = {}
            start = self._compile_term(e["start"], var_env)
            goal = self._compile_term(e["goal"], var_env)
            examples.store(eid, (start, goal))

        elapsed = time.monotonic() - pack_start
        sys.stdout.write(f"\rReading pack {name}, done in {elapsed:.2f}s\n")
        sys.stdout.flush()

        graph._replace_context(
            constructors=M.AllConstructors,
            all_rules=all_rules,
            rule_order=graph_rule_order,
            next_rule_index=next_rule_index,
            derivation_schemata=derivation_schemata,
        )
        loaded_pack_names.store(name, M.truth_value)

        loaded = LoadedPack(
            name=name,
            description=description,
            requires=requires,
            rule_map=rule_map,
            rule_chain=rule_chain,
            schema_map=schema_map,
            examples=examples,
            phi=phi,
        )
        loaded.symbol_map = self.symbol_map
        return loaded

    def load_pack_file(self, path, graph):
        import yaml

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return self.load_pack_dict(data, graph)


__all__ = ["LoadedPack", "PackLoader", "PackTreeMap", "pack_summary"]


def pack_summary(pack):
    return {
        "name": pack.name,
        "description": pack.description,
        "requires": tuple(pack.requires),
        "rule_count": len(pack.rule_map),
        "schema_count": len(pack.schema_map),
        "example_count": len(pack.examples),
    }
