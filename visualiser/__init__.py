"""Read-only observation and visualisation of a running Machine hypergraph.

The package is split along one line:

* ``tap``, ``events`` and the example workload run *inside* the observed Machine
  process and may use the kernel.
* ``server``, ``state``, ``sessions`` and everything under ``web/`` are the
  observer: they import the standard library only, so the viewer cannot execute,
  launch or modify the Machine even by accident.
"""
