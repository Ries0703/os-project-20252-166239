from __future__ import annotations

from importlib import import_module
from pkgutil import iter_modules

from .. import algorithms as algorithms_package
from ..shared.contracts import SchedulerStrategy


def discover_strategies() -> list[SchedulerStrategy]:
    strategies: list[SchedulerStrategy] = []
    discovered_modules = sorted(
        iter_modules(algorithms_package.__path__),
        key=lambda item: item.name,
    )
    for module_info in discovered_modules:
        if not module_info.ispkg:
            continue
        package = import_module(f"{algorithms_package.__name__}.{module_info.name}")
        strategy = getattr(package, "STRATEGY", None)
        if strategy is None:
            raise ImportError(
                f"Algorithm package '{module_info.name}' must export STRATEGY in __init__.py"
            )
        strategies.append(strategy)
    return strategies
