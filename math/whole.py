from __future__ import annotations

from ..labels import WholeLabel
from ..machine import IsWhole, Whole, WholeAdd, WholeLeft, WholeMultiply, WholeRight
from ..prettyprinting import WholeText

__all__ = [
    "WholeLabel",
    "Whole",
    "WholeLeft",
    "WholeRight",
    "IsWhole",
    "WholeAdd",
    "WholeMultiply",
    "WholeText",
]
