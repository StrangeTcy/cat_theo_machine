"""Import the kernel package under whatever name this checkout carries.

The validation suites write `from hyge import machine`, which resolves only
when the checkout directory is literally named `hyge` (and the legacy
`hyge.py` prototype at the repo root does not get in front of it). Every
module must be imported exactly once under its real name and then aliased
under `hyge.*`: importing the same file twice under two names would duplicate
the kernel classes, and identity checks across the copies would fail. The
package itself is name-agnostic (its modules use relative imports).
"""

import importlib
import os

import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(_HERE)
_PKG = os.path.basename(_REPO)
_PARENT = os.path.dirname(_REPO)

try:
    importlib.import_module("hyge.machine")
except ImportError:
    if _PARENT not in sys.path:
        sys.path.insert(0, _PARENT)
    importlib.import_module(_PKG + ".machine")
    _pkg = importlib.import_module(_PKG)
    assert hasattr(_pkg, "machine"), (
        "the checkout directory must carry the package (got %r)" % _PKG
    )
    sys.modules["hyge"] = _pkg
    # Alias the kernel modules the suites import. The repo root also carries
    # standalone scripts that are not importable modules, so nothing here
    # walks the directory.
    for _name in ("proof", "labels", "planner", "runtime"):
        sys.modules["hyge." + _name] = importlib.import_module(_PKG + "." + _name)
