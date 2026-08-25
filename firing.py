from __future__ import annotations

from . import labels as Lmod
from . import machine as M

class FiringRecord(M.Edge):
    """A committed firing together with its exact graph and trace counts."""

    def __init__(
        self,
        law,
        g0,
        g1,
        trace,
        nodes_before,
        nodes_after,
        edges_before,
        edges_after,
        trace_steps,
    ):
        self.result = M.Pair(
            Lmod.FiringRecordLabel,
            M.Pair(
                law,
                M.Pair(
                    g0,
                    M.Pair(
                        g1,
                        M.Pair(
                            trace,
                            M.Pair(
                                nodes_before,
                                M.Pair(
                                    nodes_after,
                                    M.Pair(
                                        edges_before,
                                        M.Pair(
                                            edges_after,
                                            M.Pair(trace_steps, M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        )
        super().__init__(
            inputs=M.Pair(
                law,
                M.Pair(
                    g0,
                    M.Pair(
                        g1,
                        M.Pair(
                            trace,
                            M.Pair(
                                nodes_before,
                                M.Pair(
                                    nodes_after,
                                    M.Pair(
                                        edges_before,
                                        M.Pair(
                                            edges_after,
                                            M.Pair(trace_steps, M.EmptyList),
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
            results=self.result,
        )

    def __call__(self):
        return self.result


class FiringRecordLaw(M.Edge):
    def __init__(self, record):
        self.result = M.Head(M.Tail(record)())()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordG0(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordG1(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordTrace(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordNodesBefore(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordNodesAfter(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordEdgesBefore(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordEdgesAfter(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


class FiringRecordTraceSteps(M.Edge):
    def __init__(self, record):
        args = M.Tail(record)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        args = M.Tail(args)()
        self.result = M.Head(args)()
        super().__init__(inputs=M.Pair(record, M.EmptyList), results=self.result)

    def __call__(self):
        return self.result


__all__ = (
    "FiringRecord",
    "FiringRecordLaw",
    "FiringRecordG0",
    "FiringRecordG1",
    "FiringRecordTrace",
    "FiringRecordNodesBefore",
    "FiringRecordNodesAfter",
    "FiringRecordEdgesBefore",
    "FiringRecordEdgesAfter",
    "FiringRecordTraceSteps",
)
