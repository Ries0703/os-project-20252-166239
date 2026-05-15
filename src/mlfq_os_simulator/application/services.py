from __future__ import annotations

from ..shared.config import AppConfig
from ..shared.contracts import AlgorithmDescriptor
from ..shared.process import ProcessInput
from .comparison_service import ComparisonService
from .registry import SchedulerRegistry
from .strategy_loader import discover_strategies


def build_scheduler_registry() -> SchedulerRegistry:
    registry = SchedulerRegistry()
    for strategy in discover_strategies():
        registry.register(strategy)
    return registry


class SimulationService:
    def __init__(self, registry: SchedulerRegistry) -> None:
        self.registry = registry

    def run_algorithm(
        self,
        algorithm_key: str,
        processes: list[ProcessInput],
        config: AppConfig,
    ):
        return self.registry.simulate(algorithm_key, processes, config)

    def available_algorithms(self) -> list[AlgorithmDescriptor]:
        return self.registry.descriptors()

    def describe_algorithm(self, algorithm_key: str) -> AlgorithmDescriptor:
        return self.registry.describe(algorithm_key)

    def default_algorithm_key(self) -> str:
        return self.registry.default_descriptor().key


def build_comparison_service(registry: SchedulerRegistry | None = None) -> ComparisonService:
    return ComparisonService(registry or build_scheduler_registry())
