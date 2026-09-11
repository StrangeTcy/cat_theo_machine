"""Check real subprocess receipts with machine structural equality.

This is a test reader, not a replacement worker or a mocked coordinator.
Run after live has exited, against its isolated state and input fixture.
"""
import os
import sys

from . import machine as M
from . import graph as G
from . import wire as W
from . import proof_ingress as I


class WorkerReceiptRegression(M.Edge):
    def __init__(self, state_dir, input_path):
        self.result = M.truth_value
        expected = M.EmptyList
        with open(input_path, "r", encoding="utf-8") as stream:
            for line in stream:
                request = I.LiveProofRequest(I.ProofTokenStream(line)())
                if request.goal is not M.EmptyList:
                    direct = I.MathematicalSentence(request.claim)
                    if M.Compare(direct.goal, request.goal)() is M.false_value:
                        self.result = M.false_value
                    expected = M.Pair(direct.goal, expected)
        observed = M.EmptyList
        total = "0"
        with os.scandir(os.path.join(state_dir, "search_compare")) as runs:
            for run in runs:
                if not run.is_dir():
                    continue
                with os.scandir(run.path) as files:
                    for entry in files:
                        if not entry.name.endswith(".request.wire"):
                            continue
                        base = entry.path.removesuffix(".request.wire")
                        with open(entry.path, "rb") as stream:
                            submitted = W.deserialize_term(stream.read())
                        with open(base + ".received.wire", "rb") as stream:
                            received = W.deserialize_term(stream.read())
                        with open(base + ".search-goal.wire", "rb") as stream:
                            searched = W.deserialize_term(stream.read())
                        if M.Compare(submitted, received)() is M.false_value or M.Compare(received, searched)() is M.false_value:
                            print("FAIL: worker transport changed a goal: " + entry.path)
                            self.result = M.false_value
                        goal = M.Head(M.Tail(received)())()
                        found = M.false_value
                        remaining = expected
                        while remaining is not M.EmptyList:
                            if M.Compare(goal, M.Head(remaining)())() is M.truth_value:
                                found = M.truth_value
                            remaining = M.Tail(remaining)()
                        if found is M.false_value:
                            print("FAIL: received a goal absent from the direct-parser corpus")
                            self.result = M.false_value
                        observed = M.Pair(goal, observed)
                        total = G.GMPSuccText(total)()
        remaining = expected
        while remaining is not M.EmptyList:
            goal = M.Head(remaining)()
            count = "0"
            receipts = observed
            while receipts is not M.EmptyList:
                if M.Compare(goal, M.Head(receipts)())() is M.truth_value:
                    count = G.GMPSuccText(count)()
                receipts = M.Tail(receipts)()
            # Existing comparison coordinator fans one foreground request
            # into five search modes. It is not five user proof requests.
            if G.GMPEqualText(count, "5")() is M.false_value:
                print("FAIL: expected five comparison-worker receipts, observed " + count)
                self.result = M.false_value
            remaining = M.Tail(remaining)()
        self.count = M.GMPRep(total)
        print("Comparison-worker receipts checked: " + total)
        super().__init__(inputs=M.Pair(M.Char(state_dir), M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


if __name__ == "__main__":
    if WorkerReceiptRegression(os.environ["HYGE_SNAPSHOT_DIR"], sys.argv[1])() is M.truth_value:
        print("PASS: direct parser == dispatcher == worker request == receipt == search goal")
    else:
        raise SystemExit("FAIL: worker receipt regression")
