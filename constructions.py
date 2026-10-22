"""W8: goal-directed auxiliary-construction generation.

A construction schema is machine data: a goal shape it can bear on, the
premises a figure must already satisfy for the construction to be sound, and
the effect facts the constructed auxiliary object contributes. A fresh
auxiliary object is minted per proposal as an anonymous `Thingy` handle --
identity survives a snapshot round-trip, and the generator never names a
problem, a configuration, or a known auxiliary point.

The generator is goal-directed but not problem-specific. It reads only the
goal's shape (what relation it asks for) and checks the schema's soundness
premises against the current figure through the machine's own matching
(`Match`, `JoinPremises`, `MergeBindings`); there is no table of problems and
no fixed proposal order. Proposals are planner data: they become
`Construction` method terms, their effects become obligations, and the
planner's alternative machinery is what tries, keeps, or abandons them on
evidence.

Everything in this module is built and inspected with the machine's own
constructors and predicates. The pack that carries the generic inference
rules consuming these effects is `packs/geometry-constructions.pack.yaml`.
The planner method edges a proposal becomes (`Construction`,
`ConstructionObligations`, `ConstructionConclusion`) live in `planner.py`
beside the other method terms; proposals are carried into the planner as
`Construction` methods with their effects as obligations.
"""

from . import machine as M
from . import labels as L
from . import proof as P


def _var_env():
    return {}


def _var(env, name):
    """A memoized pattern variable: the same shape packs.py compiles {var: x} to."""
    key = str(name)
    if key not in env:
        env[key] = M.Pair(M.VarTag, M.Pair(M.Char(key), M.EmptyList))
    return env[key]


def _call(label, *args):
    items = M.EmptyList
    index = len(args)
    while index > 0:
        index = index - 1
        items = M.Pair(args[index], items)
    return M.Pair(label, items)


class ConstructionSchema(M.Edge):
    """
    One generic auxiliary-construction schema.

    `goal_shape` is a pattern; a goal matches the schema only through it.
    `premises` must each be present in the current figure (up to the goal's
    own bindings) for the proposal to be sound. `effects` are the facts the
    constructed object contributes; the variable named `aux` is the fresh
    object and is minted per proposal. All four fields are machine terms and
    none may mention a concrete figure.

    Planner data only. Never inserted into mathematical Knowledge.
    """

    def __init__(self, name, aux, goal_shape, premises, effects):
        self.result = M.Pair(
            L.ConstructionSchemaLabel,
            M.Pair(
                name,
                M.Pair(aux, M.Pair(goal_shape, M.Pair(premises, M.Pair(effects, M.EmptyList)))),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                name,
                M.Pair(aux, M.Pair(goal_shape, M.Pair(premises, M.Pair(effects, M.EmptyList)))),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


def SchemaName(schema):
    return M.Head(M.Tail(schema)())()


def SchemaAux(schema):
    """The fresh-object variable. It is carried by the schema itself because
    bindings are matched by identity: a fresh binding minted anywhere else
    would never reach the effects template."""
    return M.Head(M.Tail(M.Tail(schema)())())()


def SchemaGoalShape(schema):
    return M.Head(M.Tail(M.Tail(M.Tail(schema)())())())()


def SchemaPremises(schema):
    return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(schema)())())())())()


def SchemaEffects(schema):
    return M.Head(M.Tail(M.Tail(M.Tail(M.Tail(M.Tail(schema)())())())())())()


def ProposalSchema(proposal):
    """A proposal is a bare Pair(schema, Pair(effects, Empty)) -- it is not a
    schema and carries no label of its own; the schema is readable from it."""
    return M.Head(proposal)()


def ProposalEffects(proposal):
    return M.Head(M.Tail(proposal)())()


class ConstructionProposals(M.Edge):
    """
    The generator: walk a schema chain against a goal and a figure.

    A schema proposes iff the goal matches its goal shape and its premises,
    seeded with the goal's own bindings, join against the figure (so a
    variable shared between goal and premise -- "the two flanks carry the
    same length quantity" -- must agree). Each surviving join mints one fresh
    auxiliary object and instantiates the effects. No proposal order is
    fixed beyond the schema chain itself, and nothing fires on an unsound
    figure: with the soundness premises absent there is no join, hence no
    proposal.
    """

    def __init__(self, schemas, goal, figure):
        self.result = self._walk(schemas, goal, figure)
        super().__init__(
            inputs=M.Pair(schemas, M.Pair(goal, M.Pair(figure, M.EmptyList))),
            results=self.result,
        )

    def _walk(self, schemas, goal, figure):
        acc = M.EmptyList
        cursor = schemas
        while M.IdentityCompare(cursor, M.EmptyList)() is M.false_value:
            schema = M.Head(cursor)()
            cursor = M.Tail(cursor)()
            match = M.Match(SchemaGoalShape(schema), goal)()
            if M.IdentityCompare(M.Head(match)(), M.truth_value)() is M.false_value:
                continue
            goal_binds = M.Tail(match)()
            joins = P.JoinPremises(SchemaPremises(schema), figure, goal_binds)()
            jcursor = joins
            while M.IdentityCompare(jcursor, M.EmptyList)() is M.false_value:
                binding = M.Head(jcursor)()
                jcursor = M.Tail(jcursor)()
                fresh_binds = M.Pair(
                    M.Pair(SchemaAux(schema), M.Pair(M.Thingy(), M.EmptyList)), M.EmptyList
                )
                merged = M.MergeBindings(binding, fresh_binds)()
                if M.IdentityCompare(M.Head(merged)(), M.truth_value)() is M.false_value:
                    continue
                effects = P.InstantiateFactList(SchemaEffects(schema), M.Tail(merged)())()
                acc = M.Pair(M.Pair(schema, M.Pair(effects, M.EmptyList)), acc)
        return acc

    def __call__(self):
        return self.result


# ---------------------------------------------------------------------------
# the generic schemas this branch ships
# ---------------------------------------------------------------------------


def BisectorCompletion():
    """
    A goal asking whether two corner-symmetric angles of a triangle are equal
    is borne by bisecting the apex: sound only when the two flanks carry the
    same length quantity (the figure is isosceles at `u`), effective because
    the fresh foot `aux` on the base induces two sub-triangles the schema
    rules can compare.
    """
    env = _var_env()
    u = _var(env, "u")
    v = _var(env, "v")
    w = _var(env, "w")
    x = _var(env, "x")
    aux = _var(env, "aux")

    goal_shape = _call(L.EqualAngleLabel, _call(L.AngleLabel, u, v, w), _call(L.AngleLabel, u, w, v))
    premises = M.Pair(
        _call(L.TriangleLabel, u, v, w),
        M.Pair(
            _call(L.LengthLabel, _call(L.SegmentLabel, u, v), x),
            M.Pair(_call(L.LengthLabel, _call(L.SegmentLabel, u, w), x), M.EmptyList),
        ),
    )
    # The foot sits on the base in both segment orientations: term matching
    # is orientation-sensitive, and both ray identities are needed.
    effects = M.Pair(
        _call(L.PointOnLabel, aux, _call(L.SegmentLabel, v, w)),
        M.Pair(
            _call(L.PointOnLabel, aux, _call(L.SegmentLabel, w, v)),
            M.Pair(
                _call(L.BisectorFromLabel, u, aux, v, w),
                M.Pair(
                    _call(L.TriangleLabel, u, v, aux),
                    M.Pair(_call(L.TriangleLabel, u, w, aux), M.EmptyList),
                ),
            ),
        ),
    )
    return ConstructionSchema(M.Char("bisector-completion"), aux, goal_shape, premises, effects)()


def CircumcircleCompletion():
    """
    A goal asking that a vertex lie on a circle is borne by completing the
    triangle's circumcircle: sound when the vertex is a vertex of a triangle
    in the figure, effective because the fresh circle `aux` is the one object
    the schema rules need to admit every vertex.
    """
    env = _var_env()
    t = _var(env, "t")
    v = _var(env, "v")
    k = _var(env, "k")
    aux = _var(env, "aux")

    goal_shape = _call(L.OnCircleLabel, v, k)
    premises = M.Pair(
        _call(L.VertexOfLabel, t, v),
        M.Pair(_call(L.TriangleLabel, t), M.EmptyList),
    )
    effects = M.Pair(_call(L.CircumcircleOfLabel, aux, t), M.EmptyList)
    return ConstructionSchema(
        M.Char("circumcircle-completion"), aux, goal_shape, premises, effects
    )()


def DefaultSchemas():
    """The schema chain this branch ships: completion schemas, nothing else."""
    return M.Pair(BisectorCompletion(), M.Pair(CircumcircleCompletion(), M.EmptyList))


__all__ = (
    "ConstructionSchema",
    "SchemaName",
    "SchemaAux",
    "SchemaGoalShape",
    "SchemaPremises",
    "SchemaEffects",
    "ProposalSchema",
    "ProposalEffects",
    "ConstructionProposals",
    "BisectorCompletion",
    "CircumcircleCompletion",
    "DefaultSchemas",
)
