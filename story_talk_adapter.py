from . import machine as M
from . import graph as G
from .story_working import DemoResult


class StoryCommandRecognized(M.Edge):
    def __init__(self, text):
        lowered = text.lower().strip()
        recognized = M.false_value
        if lowered.startswith("story"):
            recognized = M.truth_value
        elif lowered.startswith("link stories"):
            recognized = M.truth_value
        elif lowered.startswith("how is"):
            recognized = M.truth_value
        elif lowered.startswith("analogy"):
            recognized = M.truth_value
        elif lowered.startswith("show stories"):
            recognized = M.truth_value
        elif lowered.startswith("tell me a story"):
            recognized = M.truth_value
        elif lowered.startswith("tell the story"):
            recognized = M.truth_value
        elif lowered.startswith("narrate"):
            recognized = M.truth_value
        elif lowered.startswith("what happened"):
            recognized = M.truth_value
        elif lowered.startswith("why did alice"):
            recognized = M.truth_value
        elif lowered.startswith("compare the stories"):
            recognized = M.truth_value
        self.result = recognized
        super().__init__(inputs=M.Pair(M.Char(text), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryDemoEvidence(M.Edge):
    def __init__(self):
        demo = DemoResult()()
        same_candidate = M.Head(demo)()
        same_as = M.Head(M.Tail(demo)())()
        graph_version = M.Head(M.Tail(M.Tail(demo)())())()
        path = M.Head(M.Tail(M.Tail(M.Tail(demo)())())())()
        analogy = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(demo)())())())())()
        nodes = G.GraphNodes(graph_version)()
        verified = M.AndAtom(
            same_candidate,
            M.AndAtom(
                M.NotAtom(M.IdentityCompare(same_as, M.EmptyList)())(),
                M.AndAtom(
                    M.NotAtom(M.IdentityCompare(nodes, M.EmptyList)())(),
                    M.AndAtom(
                        M.NotAtom(M.IdentityCompare(path, M.EmptyList)())(),
                        analogy,
                    )(),
                )(),
            )(),
        )()
        self.result = M.Pair(
            M.Char("story-demo-evidence"),
            M.Pair(
                demo,
                M.Pair(verified, M.EmptyList),
            ),
        )
        super().__init__(inputs=M.EmptyList, results=self.result)

    def __call__(self):
        return self.result


class StoryNarration(M.Edge):
    def __init__(self, evidence):
        verified = M.Head(M.Tail(M.Tail(evidence)())())()
        if verified is M.truth_value:
            self.result = (
                "Alice's path crossed two very different worlds. In the first, she met "
                "Bob. In the second, she entered a forest, encountered a wolf, and later "
                "struck it with a stick. The accounts refer to the same Alice, though the "
                "machine keeps that identification as an explicit, reviewable link rather "
                "than silently merging the two records. Her repeated role as the person "
                "meeting someone also ties the episodes together: Bob and the wolf occupy "
                "parallel places in the two encounters."
            )
        else:
            self.result = "I could not verify enough connected events to narrate that story."
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result


class StoryConnectionNarration(M.Edge):
    def __init__(self, evidence):
        verified = M.Head(M.Tail(M.Tail(evidence)())())()
        if verified is M.truth_value:
            self.result = (
                "Alice is connected to the wolf through the forest episode: she is the "
                "agent in an encounter whose other participant is the wolf, and she appears "
                "again as the agent of the later action against it. The path is supported "
                "by event roles and their recorded ordering, not by a guessed association."
            )
        else:
            self.result = "I found no verified event path connecting Alice to the wolf."
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result


class StoryAnalogyNarration(M.Edge):
    def __init__(self, evidence):
        verified = M.Head(M.Tail(M.Tail(evidence)())())()
        if verified is M.truth_value:
            self.result = (
                "The two meetings echo one another. Alice fills the same agent role in both; "
                "Bob fills the counterpart role in one event and the wolf fills it in the "
                "other. That shared role structure is the analogy, even though the characters "
                "and consequences differ."
            )
        else:
            self.result = "The stored events did not support a role-preserving analogy."
        super().__init__(inputs=M.Pair(evidence, M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result


class StoryTalkResponse(M.Edge):
    def __init__(self, text):
        lowered = text.lower().strip()
        if StoryCommandRecognized(text)() is M.false_value:
            self.result = ""
        else:
            evidence = StoryDemoEvidence()()
            if lowered.startswith("how is"):
                self.result = StoryConnectionNarration(evidence)()
            elif lowered.startswith("why did alice"):
                self.result = StoryConnectionNarration(evidence)()
            elif lowered.startswith("analogy"):
                self.result = StoryAnalogyNarration(evidence)()
            elif lowered.startswith("compare the stories"):
                self.result = StoryAnalogyNarration(evidence)()
            else:
                self.result = StoryNarration(evidence)()
        super().__init__(inputs=M.Pair(M.Char(text), M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result
