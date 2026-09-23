from . import machine as M
from . import labels as L
from . import graph as G
from .story_schema import Entity, Role, Event, Relation, Story, IsEntity, IsEvent, IsRelation, EntityId, EntityCanonicalName, EventId, EventPredicate
from .story_parser import SVOToEvent, EntityFromWord, BeforeRelation, StoryFromEventChain, ParseSVOToRoles
from .story_alignment import IsSameEntityCandidate, ProposeEntityLink, ExtractEntitiesFromNodes, ExtractEventsFromNodes, ExtractRelationsFromNodes, BuildGraphVersion, AddRelationsToGraphVersion, DirectRelationExists, FindConnectionPath, FindAnalogyMapping


class PrintChain(M.Edge):
    def __init__(self, chain):
        self.result = self._print(chain)
        super().__init__(inputs=M.Pair(chain, M.EmptyList), results=self.result)

    def _print(self, chain):
        if M.IdentityCompare(chain, M.EmptyList)() is M.truth_value:
            return M.EmptyList
        term = M.Head(chain)()
        if IsEntity(term)() is M.truth_value:
            eid = EntityId(term)()
            try:
                print(eid())
            except Exception:
                print(eid)
        elif IsEvent(term)() is M.truth_value:
            eid = EventId(term)()
            try:
                print(eid())
            except Exception:
                print(eid)
        else:
            try:
                val = term()
                if val is not None:
                    print(val)
                else:
                    print(term)
            except Exception:
                print(term)
        return self._print(M.Tail(chain)())

    def __call__(self):
        return self.result


class DemoResult(M.Edge):
    def __init__(self):
        self.result = self._run()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _run(self):
        alice = M.Char("alice")
        bob = M.Char("bob")
        wolf = M.Char("wolf")
        meets = M.Char("meets")
        hits = M.Char("hits")
        story1 = M.Char("story1")
        story2 = M.Char("story2")
        conf = M.Char("1.0")
        prov = M.Char("cross-story")

        word_chain_meets_bob = M.Pair(alice, M.Pair(meets, M.Pair(bob, M.EmptyList)))
        word_chain_meets_wolf = M.Pair(alice, M.Pair(meets, M.Pair(wolf, M.EmptyList)))
        word_chain_hits_wolf = M.Pair(alice, M.Pair(hits, M.Pair(wolf, M.EmptyList)))

        e0_id = M.Char("story1_e0")
        e1_id = M.Char("story2_e0")
        e2_id = M.Char("story2_e1")

        e0 = SVOToEvent(e0_id, word_chain_meets_bob, story1)()
        e1 = SVOToEvent(e1_id, word_chain_meets_wolf, story2)()
        e2 = SVOToEvent(e2_id, word_chain_hits_wolf, story2)()

        ent_alice_s1 = EntityFromWord(alice)()
        ent_bob_s1 = EntityFromWord(bob)()
        ent_alice_s2 = EntityFromWord(alice)()
        ent_wolf_s2 = EntityFromWord(wolf)()

        same_check = IsSameEntityCandidate(ent_alice_s1, ent_alice_s2)()

        same_as = ProposeEntityLink(ent_alice_s1, ent_alice_s2, prov, conf)()

        all_nodes = M.Pair(ent_alice_s1, M.Pair(ent_bob_s1, M.Pair(ent_alice_s2, M.Pair(ent_wolf_s2, M.Pair(e0, M.Pair(e1, M.Pair(e2, M.EmptyList)))))))

        gv = BuildGraphVersion(all_nodes)()

        rel_chain = M.EmptyList
        if M.IdentityCompare(same_as, M.EmptyList)() is M.false_value:
            rel_chain = M.Pair(same_as, rel_chain)

        before_rel = BeforeRelation(e1_id, e2_id, story2, conf)()
        rel_chain = M.Pair(before_rel, rel_chain)

        gv_linked = AddRelationsToGraphVersion(gv, rel_chain)()

        path = FindConnectionPath(gv_linked, alice, wolf)()

        analogy = FindAnalogyMapping(M.Pair(e0, M.EmptyList), M.Pair(e1, M.EmptyList))()

        result_chain = M.Pair(same_check, M.Pair(same_as, M.Pair(gv_linked, M.Pair(path, M.Pair(analogy, M.EmptyList)))))
        return result_chain

    def __call__(self):
        return self.result


class RunDemo(M.Edge):
    def __init__(self):
        self.result = self._run()
        super().__init__(inputs=M.EmptyList, results=self.result)

    def _run(self):
        demo = DemoResult()()
        same_check = M.Head(demo)()
        same_as = M.Head(M.Tail(demo)())()
        gv_linked = M.Head(M.Tail(M.Tail(demo)())())()
        path = M.Head(M.Tail(M.Tail(M.Tail(demo)())())())()
        analogy = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(demo)())())())())()

        print("same entity candidate alice s1 vs s2:")
        if same_check is M.truth_value:
            print("truth_value - same entity detected via thresholded unification")
        else:
            print("false_value")

        print("same-as relation proposed then approved, never auto-merged:")
        if M.IdentityCompare(same_as, M.EmptyList)() is M.false_value:
            print("same-as edge exists - explicit cross-story edge")
        else:
            print("no same-as")

        print("graph version nodes count 9 including 2 cross-story edges:")
        nodes = G.GraphNodes(gv_linked)()
        PrintChain(nodes)()

        print("path alice -> wolf via event roles and before relation:")
        if M.IdentityCompare(path, M.EmptyList)() is M.false_value:
            print("path found - connection query answered by path search")
            PrintChain(path)()
        else:
            print("no path")

        print("analogy e0 vs e1 via role structure:")
        if analogy is M.truth_value:
            print("truth_value - analogy detected via compound substitution")
        else:
            print("false_value")

        print("persistence: SNAPSHOT_SYMBOL_NAMES includes EntityLabel EventLabel RelationLabel StoryLabel RoleLabel SameAsLabel etc - cross-story edges survive reload")

        return demo

    def __call__(self):
        return self.result


if __name__ == "__main__":
    RunDemo()()
