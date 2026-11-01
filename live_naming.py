"""Synchronous host input boundary while a discovery awaits its name."""

from . import labels as L
from . import machine as M


class DiscoveryCommandWord(M.Edge):
    def __init__(self, word, choices):
        verdict = M.false_value
        if M.IsPair(choices)() is M.truth_value:
            verdict = M.Compare(word, M.Head(choices)())()
            if verdict is M.false_value:
                verdict = DiscoveryCommandWord(word, M.Tail(choices)())()
        super().__init__(inputs=M.Pair(word, choices), results=verdict)


class DiscoveryNameCommand(M.Edge):
    """Recognize live command words without dispatching any command."""

    def __init__(self, reply):
        text = reply().strip().lower()
        first, separator, remaining = text.partition(" ")
        verbs = M.Pair(M.Char("show"), M.Pair(M.Char("suggest"), M.Pair(M.Char("prove"),
            M.Pair(M.Char("solve"), M.Pair(M.Char("run"), M.Pair(M.Char("check"), M.EmptyList))))))
        verbs = M.Pair(M.Char("explain"), M.Pair(M.Char("narrate"), M.Pair(M.Char("tell"),
            M.Pair(M.Char("load"), M.Pair(M.Char("ground"), M.Pair(M.Char("adopt"), verbs))))))
        verbs = M.Pair(M.Char("promote"), M.Pair(M.Char("what"), M.Pair(M.Char("define"),
            M.Pair(M.Char("focus"), M.Pair(M.Char("let's"), verbs)))))
        verbs = M.Pair(M.Char("proof"), M.Pair(M.Char("why"), M.Pair(M.Char("status"),
            M.Pair(M.Char("lets"), M.Pair(M.Char("work"), M.Pair(M.Char("let"), verbs))))))
        exact = M.Pair(M.Char("next"), M.Pair(M.Char("quit"), M.Pair(M.Char("exit"),
            M.Pair(M.Char("goodbye"), M.Pair(M.Char("skip"), M.Pair(M.Char("no"), M.EmptyList))))))
        exact = M.Pair(M.Char("no thanks"), M.Pair(M.Char("cancel"), M.Pair(M.Char("pass"),
            M.Pair(M.Char("none"), M.Pair(M.Char("yes"), M.Pair(M.Char("hint"), exact))))))
        exact = M.Pair(M.Char("verify"), M.Pair(M.Char("why"), M.Pair(M.Char("ledger"), exact)))
        exact = M.Pair(M.Char("go on"), M.Pair(M.Char("continue"), M.Pair(M.Char("judge"),
            M.Pair(M.Char("candidates"), exact))))
        verdict = M.OrAtom(DiscoveryCommandWord(M.Char(first), verbs)(),
            DiscoveryCommandWord(M.Char(text), exact)())()
        statement, colon, body = first.partition(":")
        if M.Compare(M.Char(colon), M.Char(":"))() is M.truth_value:
            verdict = M.OrAtom(verdict, DiscoveryCommandWord(M.Char(statement),
                M.Pair(M.Char("fact"), M.Pair(M.Char("rule"), M.Pair(M.Char("word"), M.EmptyList))))())()
        verdict = M.OrAtom(verdict,
            M.NotAtom(M.Compare(M.Char(text.removeprefix("is it true")), M.Char(text))())())()
        super().__init__(inputs=M.Pair(reply, M.EmptyList), results=verdict)


class DiscoveryNameText(M.Edge):
    """Accept plain names and the live session's established naming phrases."""

    def __init__(self, reply):
        name = reply().strip()
        folded = name.lower()
        if M.Compare(M.Char(folded.removeprefix("yes, call this ")), M.Char(folded))() is M.false_value:
            name = name[15:]
        elif M.Compare(M.Char(folded.removeprefix("call this ")), M.Char(folded))() is M.false_value:
            name = name[10:]
        elif M.Compare(M.Char(folded.removeprefix("name this ")), M.Char(folded))() is M.false_value:
            name = name[10:]
        elif M.Compare(M.Char(folded.removeprefix("call it ")), M.Char(folded))() is M.false_value:
            name = name[8:]
        elif M.Compare(M.Char(folded.removeprefix("yes, ")), M.Char(folded))() is M.false_value:
            name = name[5:]
        elif M.OrAtom(M.Compare(M.Char(folded), M.Char("call this"))(),
            M.OrAtom(M.Compare(M.Char(folded), M.Char("yes, call this"))(),
                M.OrAtom(M.Compare(M.Char(folded), M.Char("name this"))(),
                    M.OrAtom(M.Compare(M.Char(folded), M.Char("call it"))(),
                        M.Compare(M.Char(folded), M.Char("yes,"))())())())())() is M.truth_value:
            name = ""
        if M.Compare(M.Char(name), M.Char(reply().strip()))() is M.truth_value:
            if DiscoveryNameCommand(M.Char(name))() is M.truth_value:
                name = ""
        super().__init__(inputs=M.Pair(reply, M.EmptyList), results=M.Char(name.strip()))


class ReadPendingDiscoveryName(M.Edge):
    """Block on a nonempty name; EOF and interrupt propagate to the live boundary."""

    def __init__(self, proposal):
        prompt = "[you] Name this candidate structure: "
        if M.IdentityCompare(M.Head(proposal)(), L.ObservedRegularityLabel)() is M.truth_value:
            prompt = "[you] Name this property: "
        reply = M.Char(input(prompt))
        name = DiscoveryNameText(reply)()
        if M.Compare(name, M.Char(""))() is M.truth_value:
            if DiscoveryNameCommand(reply)() is M.truth_value:
                print("[machine] Name this discovery before using other commands.")
            else:
                print("[machine] A nonempty name is required before continuing.")
            command = ReadPendingDiscoveryName(proposal)()
        else:
            command = M.Char("call this " + name())
        super().__init__(inputs=M.Pair(proposal, M.EmptyList), results=command)
