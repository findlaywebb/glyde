"""Every concrete adapter implements a seam the core defines.

A public class in the adapters layer must subclass a port from
``glyde.core.ports``. Tolerant while the layers are empty: with no ports and no
adapter classes the check passes trivially. The moment a public class appears in
the adapters layer it must implement one of the core ports.
"""

import importlib
import inspect
import pkgutil

import glyde.adapters
from glyde.core import ports


def _public_classes(package) -> list[type]:
    classes: list[type] = []
    for info in pkgutil.walk_packages(package.__path__, prefix=f"{package.__name__}."):
        module = importlib.import_module(info.name)
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__.startswith(package.__name__) and not name.startswith("_"):
                classes.append(obj)
    for name, obj in inspect.getmembers(package, inspect.isclass):
        if obj.__module__.startswith(package.__name__) and not name.startswith("_"):
            classes.append(obj)
    return classes


def test_adapters_implement_ports() -> None:
    """Every public adapter class subclasses a core port."""
    port_types = tuple(
        obj
        for _, obj in inspect.getmembers(ports, inspect.isclass)
        if obj.__module__.startswith(ports.__name__) and not issubclass(obj, Exception)
    )
    orphans = [
        f"{cls.__module__}.{cls.__qualname__}"
        for cls in _public_classes(glyde.adapters)
        if not (port_types and issubclass(cls, port_types))
    ]
    assert not orphans, f"public adapter classes implementing no glyde.core.ports port: {orphans}"
