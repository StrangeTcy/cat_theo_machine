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

    def __init__(self, name, description, requires, rule_map, rule_chain, schema_map, examples, phi, origin=None):
        self.name = name
        self.description = description
        self.requires = requires
        # Declared origin tag (a machine Char from learning.origin_tag_for_text);
        # defaults to primitive. Read from the pack header 'origin:' field.
        self.origin = origin
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

        # D11-MAP. Per-pack, opt-in, and set fresh by every load_pack_dict
        # call: a pack that declares nothing sees an empty map, so an
        # unported pack compiles exactly as it did before this existed.
        self.surface_map = {}
        self.surface_audit = ()
        self.surface_rule_audit = ()
        self._surface_this_rule = ()

    def _record_surface_use(self, label_name, label_atom, surface_atom, surface_name):
        """Note that a constructor head was compiled through the mapping."""
        entry = (label_name, label_atom, surface_atom, surface_name)
        self._surface_this_rule = self._surface_this_rule + (entry,)

    def _chain(self, items):
        L = M.EmptyList
        for item in reversed(items):
            L = M.Pair(item, L)
        return L

    def _compile_term(self, spec, var_env=None, as_head=False):
        """Compile one pack term.

        `as_head` is true only in the head position of a `call`. D11-MAP
        maps a pack symbol to the research-surface atom **there and only
        there**: a label used as data must not be silently rewritten into
        a surface atom just because the pack declared a mapping for it.
        """
        if var_env is None:
            var_env = {}

        if not isinstance(spec, dict):
            raise RuntimeError(f"Bad term spec: {spec}")

        if "sym" in spec:
            name = spec["sym"]
            if name not in self.namespace:
                raise RuntimeError(f"Unknown symbol in pack: {name}")
            atom = self.namespace[name]
            if as_head and name in self.surface_map:
                # The symbol_map below still records the namespace atom:
                # what a name denotes is unchanged, only this head
                # position is spoken in the research vocabulary.
                surface_name = self.surface_map[name]
                surface_atom = self.string_table._char_atom(surface_name)
                self._record_surface_use(name, atom, surface_atom, surface_name)
                atom = surface_atom
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

            head = self._compile_term(call["head"], var_env, as_head=True)
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
        origin_text = data.get("origin", "primitive")
        if requires is None:
            requires = ()
        else:
            requires = tuple(requires)

        # D11-MAP: pack-local surface declaration. Opt-in and scoped to
        # constructor heads in this pack only. Validated eagerly so a typo
        # fails at load rather than silently compiling a Label.
        surface_spec = data.get("surface", None)
        if surface_spec is None:
            surface_spec = {}
        if not isinstance(surface_spec, dict):
            raise RuntimeError(
                f"Pack '{name}': 'surface' must be a map of pack symbol -> surface name"
            )
        self.surface_map = {}
        self.surface_audit = ()
        self.surface_rule_audit = ()
        self._surface_this_rule = ()
        for label_name, surface_name in surface_spec.items():
            if not isinstance(label_name, str) or not isinstance(surface_name, str):
                raise RuntimeError(
                    f"Pack '{name}': bad 'surface' entry {label_name!r}: {surface_name!r}"
                )
            if surface_name == "":
                raise RuntimeError(
                    f"Pack '{name}': 'surface' maps '{label_name}' to an empty name"
                )
            if label_name not in self.namespace:
                raise RuntimeError(
                    f"Pack '{name}': 'surface' names unknown symbol '{label_name}'"
                )
            self.surface_map[label_name] = surface_name

        try:
            self.string_table = graph._pack_string_table
        except AttributeError:
            graph._pack_string_table = self.string_table

        # D11-MAP: now that the pack's string table is the graph's, build
        # the audit atoms from the same table the rule heads will come
        # from, so a recorded surface_atom is the atom actually compiled.
        for label_name, surface_name in self.surface_map.items():
            self.surface_audit = self.surface_audit + (
                (label_name, self.namespace[label_name],
                 self.string_table._char_atom(surface_name), surface_name),
            )
        for label_name, _label_atom, _surface_atom, surface_name in self.surface_audit:
            # The audit term is (pack_id, label_atom, surface_atom); the
            # atoms are carried in self.surface_audit for programmatic
            # readers, and named here because a ConstructorLabel has no
            # host text to print.
            sys.stdout.write(
                "PackSurfaceMapping(pack=%s, label=%s, surface=%s)\n"
                % (name, label_name, surface_name)
            )
        if self.surface_audit:
            sys.stdout.flush()

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
            self._surface_this_rule = ()
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

            # D11-MAP audit: a rule whose head was compiled through the
            # mapping is reachable from research goals only by that path,
            # so the attribution is recorded here, at compile time, and
            # not left to be inferred from a match later.
            for label_name, label_atom, surface_atom, surface_name in self._surface_this_rule:
                sys.stdout.write(
                    "LibraryRuleMatchedViaSurfaceMapping(rule=%s, pack=%s, "
                    "label=%s, surface=%s)\n" % (rid, name, label_name, surface_name)
                )
                self.surface_rule_audit = self.surface_rule_audit + (
                    (rid, label_name, label_atom, surface_atom, surface_name),
                )
            if self._surface_this_rule:
                sys.stdout.flush()

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

        from .provenance import origin_tag_for_text

        origin_tag = origin_tag_for_text(origin_text)
        origin_scan = rule_chain
        while M.IdentityCompare(origin_scan, M.EmptyList)() is M.false_value:
            graph.tag_rule_origin(M.Head(origin_scan)(), origin_tag)
            origin_scan = M.Tail(origin_scan)()

        loaded = LoadedPack(
            name=name,
            description=description,
            requires=requires,
            rule_map=rule_map,
            rule_chain=rule_chain,
            schema_map=schema_map,
            examples=examples,
            phi=phi,
            origin=origin_tag,
        )
        loaded.symbol_map = self.symbol_map
        # D11-MAP: what this pack declared, and which rules were compiled
        # through it. Empty for every pack that declares nothing.
        loaded.surface_mapping_audit = tuple(
            "PackSurfaceMapping(pack=%s, label=%s, surface=%s)"
            % (name, label_name, surface_name)
            for label_name, _la, _sa, surface_name in self.surface_audit
        )
        loaded.surface_mapped_rules = tuple(
            "LibraryRuleMatchedViaSurfaceMapping(rule=%s, pack=%s, label=%s, surface=%s)"
            % (rid, name, label_name, surface_name)
            for rid, label_name, _la, _sa, surface_name in self.surface_rule_audit
        )
        # Per-pack scoping: leave no mapping behind for the next pack.
        self.surface_map = {}
        self.surface_audit = ()
        self.surface_rule_audit = ()
        self._surface_this_rule = ()
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
