"""CL0 policy probe for the charter-v2 G method registry.

This deliberately tests policy, not mathematical obligation completeness.
Bijection and DoubleCount remain constructible legacy terms but must not be
accepted as v2 methods.
"""

from cat_theo_machine import machine as M
from cat_theo_machine import planner as P


def require_machine_truth(value, message):
    if value is not M.truth_value:
        raise AssertionError(message)


def main():
    assert P.V2_METHODS == (
        "Invariance",
        "Extremal",
        "Pigeonhole",
        "Divide",
        "Symmetry",
    )
    assert P.LEGACY_BLOCKED_METHODS == ("Bijection", "DoubleCount")

    extremal = P.Extremal(M.EmptyList, M.Zero, P.ExtremalMin()(), M.EmptyList)()
    pigeonhole = P.Pigeonhole(M.EmptyList, M.EmptyList, M.EmptyList)()
    divide = P.Divide(M.EmptyList, M.EmptyList, M.Zero)()
    symmetry = P.Symmetry(M.EmptyList, M.EmptyList)()
    bijection = P.Bijection(M.EmptyList, M.EmptyList, M.EmptyList, M.EmptyList)()
    double_count = P.DoubleCount(M.EmptyList, M.EmptyList, M.EmptyList)()

    for name, method in (
        ("Extremal", extremal),
        ("Pigeonhole", pigeonhole),
        ("Divide", divide),
        ("Symmetry", symmetry),
    ):
        require_machine_truth(P.IsV2PlannerMethod(method), f"{name} was not accepted as v2")
        if P.IsLegacyBlockedPlannerMethod(method) is M.truth_value:
            raise AssertionError(f"{name} was classified as blocked")

    for name, method in (("Bijection", bijection), ("DoubleCount", double_count)):
        require_machine_truth(
            P.IsLegacyBlockedPlannerMethod(method),
            f"{name} was not classified as legacy-blocked",
        )
        if P.IsV2PlannerMethod(method) is M.truth_value:
            raise AssertionError(f"{name} was accepted as v2")

    print("G_METHOD_REGISTRY_PASS")


if __name__ == "__main__":
    main()
