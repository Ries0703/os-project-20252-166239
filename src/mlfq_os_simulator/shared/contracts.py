from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from .config import AppConfig
from .process import ProcessInput
from .results import StrategySimulation


@dataclass(frozen=True, slots=True)
class AlgorithmConfigField:
    key: str
    label: str
    default: int
    min_value: int = 0
    max_value: int | None = None
    widget: Literal["number", "slider"] = "number"
    description: str = ""


@dataclass(frozen=True, slots=True)
class AlgorithmDescriptor:
    key: str
    display_name: str
    description: str
    config_fields: tuple[AlgorithmConfigField, ...]
    supports_animation: bool
    include_in_comparison: bool = True
    is_default: bool = False
    order: int = 100


class SchedulerStrategy(Protocol):
    key: str
    display_name: str
    description: str
    config_fields: tuple[AlgorithmConfigField, ...]
    supports_animation: bool
    include_in_comparison: bool
    is_default: bool
    order: int

    def simulate(
        self,
        processes: list[ProcessInput],
        config: AppConfig,
    ) -> StrategySimulation: ...
