from . import machine as _machine


def make_lazy_exports(names):
    names = tuple(names)

    def __getattr__(name):
        if name in names:
            return getattr(_machine, name)
        raise AttributeError(f"module has no attribute {name!r}")

    def __dir__():
        return sorted(names)

    return __getattr__, __dir__
