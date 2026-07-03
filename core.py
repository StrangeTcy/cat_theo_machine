from __future__ import annotations

import uuid


class Atom:
    """A primitive indivisible element with a single mutable slot."""

    _id_constructor = None

    def __init__(self):
        if Atom._id_constructor is None:
            raise RuntimeError("Identity constructor not installed")
        self.id = Atom._id_constructor(self)
        self.value = None

    def __call__(self):
        return self.value


class Edge(Atom):
    """Connects atoms (or hypergraphs) and represents a relation."""

    def __init__(self, inputs=None, results=None):
        super().__init__()
        self.inputs = inputs if inputs is not None else EmptyList
        self.results = results if results is not None else EmptyList

    def __call__(self):
        return self.results


class EdgeInputs(Edge):
    def __init__(self, edge):
        self.result = edge.inputs
        super().__init__(inputs=Pair(edge, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class EdgeResults(Edge):
    def __init__(self, edge):
        self.result = edge.results
        super().__init__(inputs=Pair(edge, EmptyList), results=self.result)

    def __call__(self):
        return self.result


class UniqueId(Edge):
    def __init__(self, source):
        self.source = source
        self.token = uuid.uuid4()

    def __call__(self):
        return self.token


def install_identity():
    def make_id(atom):
        return UniqueId(atom)()

    Atom._id_constructor = make_id


install_identity()


class Thingy(Atom):
    pass


class Same(Atom):
    pass


class Diff(Atom):
    pass


class Var(Atom):
    pass


class VarTag(Atom):
    pass


VarTag = VarTag()
truth_value = Same()
false_value = Diff()


EmptyList = Thingy()


class Pair(Atom):
    def __init__(self, head, tail):
        super().__init__()
        self.head = Atom()
        self.tail = Atom()
        self.head.value = head
        self.tail.value = tail


class Head(Atom):
    def __init__(self, pair):
        self.p = pair

    def __call__(self):
        return self.p.head.value


class Tail(Atom):
    def __init__(self, pair):
        self.p = pair

    def __call__(self):
        return self.p.tail.value


class IsPair(Edge):

    def __init__(self, x):
        # print(f"DEBUG: IsPair has received x {x} of type {type(x).__name__}")

        c = GetConstructor(x)()

        if Compare(c, EmptyList)() is not truth_value:
            # print(f"DEBUG: our {x} had a constructor: {c}")
            atom_result = false_value

        else:
            # print(f"DEBUG: our {x} DOES NOT have a constructor")

        # Oh well, another dirty python trick
        # But we'll get rid of it eventually
        # TODO!!    
            try:
                hx = Head(x)()
                tx = Tail(x)()

                # print(f"DEBUG: we've split our {x} into Head {hx} and Tail {tx}")
                atom_result = truth_value
            except:
                atom_result = false_value    
                # raise TypeError("No, this was not a Pair!")
                # print(f"DEBUG: No, this was not a Pair! It was {x} of type {type(x).__name__}")


  
        self.result = atom_result

        super().__init__(
            inputs=Pair(x, EmptyList),
            results=self.result
        )

    def __call__(self):
        return self.result






class InputOf(Edge):
    def __init__(self, input_node, edge=None):
        self.input_node = input_node
        if edge is None:
            self.result = Atom()
            super().__init__(inputs=[input_node], results=[self.result])
        else:
            super().__init__(inputs=[input_node, edge], results=[])


class IdentityCompare(Edge):
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.result = Thingy()
        super().__init__(inputs=Pair(x, Pair(y, EmptyList)), results=self.result)

    def __call__(self):
        if self.x.id == self.y.id:
            self.result = truth_value
        else:
            self.result = false_value
        return self.result


AtomSet = Atom()
EmptySet = Thingy()


class Member(Edge):
    def __init__(self, x, S):
        InputOf(x, self)
        super().__init__(inputs=[x, S], results=[EmptySet])


Zero = Atom()
InputOf(EmptySet, Zero)


class IdentityLess(Edge):
    def __init__(self, x, y):
        if x.id < y.id:
            self.result = truth_value
        else:
            self.result = false_value

    def __call__(self):
        return self.result


class Char(Atom):
    def __init__(self, symbol):
        super().__init__()
        self.symbol = symbol

    def __call__(self):
        return self.symbol


LPAREN = Char("(")
RPAREN = Char(")")
COMMA = Char(",")
SPACE = Char(" ")
LBRACK = Char("[")
RBRACK = Char("]")

# Digit singletons for structural keys and printing.
DIGIT_0 = Char("0")
DIGIT_1 = Char("1")
DIGIT_2 = Char("2")
DIGIT_3 = Char("3")
DIGIT_4 = Char("4")
DIGIT_5 = Char("5")
DIGIT_6 = Char("6")
DIGIT_7 = Char("7")
DIGIT_8 = Char("8")
DIGIT_9 = Char("9")

# Machine list of digit singletons (0..9).
DIGITS = Pair(
    DIGIT_0,
    Pair(
        DIGIT_1,
        Pair(
            DIGIT_2,
            Pair(
                DIGIT_3,
                Pair(
                    DIGIT_4,
                    Pair(
                        DIGIT_5,
                        Pair(
                            DIGIT_6,
                            Pair(
                                DIGIT_7,
                                Pair(DIGIT_8, Pair(DIGIT_9, EmptyList)),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    ),
)


def sync_from_namespace(namespace):
    for name in (
        "EmptyList",
        "Zero",
        "VarTag",
        "truth_value",
        "false_value",
        "LPAREN",
        "RPAREN",
        "COMMA",
        "SPACE",
        "LBRACK",
        "RBRACK",
        "DIGITS",
    ):
        if name in namespace:
            globals()[name] = namespace[name]


__all__ = [
    "Atom",
    "Edge",
    "EdgeInputs",
    "EdgeResults",
    "UniqueId",
    "install_identity",
    "Thingy",
    "Same",
    "Diff",
    "Var",
    "VarTag",
    "truth_value",
    "false_value",
    "EmptyList",
    "Pair",
    "Head",
    "Tail",
    "IsPairCell",
    "InputOf",
    "IdentityCompare",
    "AtomSet",
    "EmptySet",
    "Member",
    "Zero",
    "IdentityLess",
    "Char",
    "LPAREN",
    "RPAREN",
    "COMMA",
    "SPACE",
    "LBRACK",
    "RBRACK",
    "DIGIT_0",
    "DIGIT_1",
    "DIGIT_2",
    "DIGIT_3",
    "DIGIT_4",
    "DIGIT_5",
    "DIGIT_6",
    "DIGIT_7",
    "DIGIT_8",
    "DIGIT_9",
    "DIGITS",
    "sync_from_namespace",
]
