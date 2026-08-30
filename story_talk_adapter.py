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
        self.result = recognized
        super().__init__(inputs=M.Pair(M.Char(text), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class StoryDemoSummary(M.Edge):
    def __init__(self):
        demo = DemoResult()()
        same_candidate = M.Head(demo)()
        same_as = M.Head(M.Tail(demo)())()
        graph_version = M.Head(M.Tail(M.Tail(demo)())())()
        path = M.Head(M.Tail(M.Tail(M.Tail(demo)())())())()
        analogy = M.Head(M.Tail(M.Tail(M.Tail(M.Tail(demo)())())())())()
        entity_resolution = "rejected"
        if same_candidate is M.truth_value:
            entity_resolution = "verified"
        same_as_status = "not proposed"
        if M.IdentityCompare(same_as, M.EmptyList)() is M.false_value:
            same_as_status = "explicit same-as edge proposed"
        path_status = "no connection path"
        if M.IdentityCompare(path, M.EmptyList)() is M.false_value:
            path_status = "Alice-to-wolf connection path found"
        analogy_status = "no role analogy"
        if analogy is M.truth_value:
            analogy_status = "role-structured analogy verified"
        nodes = G.GraphNodes(graph_version)()
        node_status = "empty story graph"
        if M.IdentityCompare(nodes, M.EmptyList)() is M.false_value:
            node_status = "pair-schema story graph built"
        self.result = (
            "Story machine: " + node_status + "; entity resolution "
            + entity_resolution + "; " + same_as_status + "; "
            + path_status + "; " + analogy_status + "."
        )
        super().__init__(inputs=M.EmptyList, results=M.Char(self.result))

    def __call__(self):
        return self.result


class StoryTalkResponse(M.Edge):
    def __init__(self, text):
        if StoryCommandRecognized(text)() is M.truth_value:
            self.result = StoryDemoSummary()()
        else:
            self.result = ""
        super().__init__(inputs=M.Pair(M.Char(text), M.EmptyList), results=M.Char(self.result))

    def __call__(self):
        return self.result
