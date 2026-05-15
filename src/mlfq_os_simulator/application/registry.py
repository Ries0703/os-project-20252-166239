from __future__ import annotations

from ..shared.config import AppConfig
from ..shared.contracts import AlgorithmDescriptor, SchedulerStrategy
from ..shared.process import ProcessInput
from ..shared.results import StrategySimulation


class SchedulerRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, SchedulerStrategy] = {}

    def register(self, strategy: SchedulerStrategy) -> None:
        if strategy.key in self._strategies:
            raise ValueError(f"Duplicate scheduler strategy key: {strategy.key}")
        self._strategies[strategy.key] = strategy

    def get(self, key: str) -> SchedulerStrategy:
        try:
            return self._strategies[key]
        except KeyError as exc:
            raise KeyError(f"Unknown scheduler strategy: {key}") from exc

    def describe(self, key: str) -> AlgorithmDescriptor:
        strategy = self.get(key)
        return AlgorithmDescriptor(
            key=strategy.key,
            display_name=strategy.display_name,
            description=strategy.description,
            config_fields=strategy.config_fields,
            supports_animation=strategy.supports_animation,
            include_in_comparison=strategy.include_in_comparison,
            is_default=strategy.is_default,
            order=strategy.order,
        )

    def keys(self) -> list[str]:
        return [descriptor.key for descriptor in self.descriptors()]

    def items(self) -> list[tuple[str, SchedulerStrategy]]:
        ordered_keys = self.keys()
        return [(key, self._strategies[key]) for key in ordered_keys]

    def descriptors(self) -> list[AlgorithmDescriptor]:
        descriptors = [
            AlgorithmDescriptor(
                key=strategy.key,
                display_name=strategy.display_name,
                description=strategy.description,
                config_fields=strategy.config_fields,
                supports_animation=strategy.supports_animation,
                include_in_comparison=strategy.include_in_comparison,
                is_default=strategy.is_default,
                order=strategy.order,
            )
            for strategy in self._strategies.values()
        ]
        return sorted(
            descriptors,
            key=lambda item: (0 if item.is_default else 1, item.order, item.display_name),
        )

    def comparison_descriptors(self) -> list[AlgorithmDescriptor]:
        return [item for item in self.descriptors() if item.include_in_comparison]

    def default_descriptor(self) -> AlgorithmDescriptor:
        descriptors = self.descriptors()
        for descriptor in descriptors:
            if descriptor.is_default:
                return descriptor
        if not descriptors:
            raise ValueError("No scheduler strategies registered")
        return descriptors[0]

    def simulate(
        self,
        key: str,
        processes: list[ProcessInput],
        config: AppConfig,
    ) -> StrategySimulation:
        return self.get(key).simulate(processes, config)
