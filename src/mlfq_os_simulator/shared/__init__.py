"""Shared contracts, models, and helpers for all scheduling algorithms."""

from .config import SCHEMA_VERSION, AppConfig, default_config
from .contracts import AlgorithmConfigField, AlgorithmDescriptor, SchedulerStrategy
from .metrics import (
    build_algorithm_gantt_figure,
    build_gantt_figure,
    calculate_algorithm_metrics,
)
from .process import ProcessInput
from .results import (
    AlgorithmGanttEntry,
    AlgorithmProcessResult,
    AlgorithmRunResult,
    AlgorithmTraceFrame,
    StrategySimulation,
)

__all__ = [
    "AlgorithmGanttEntry",
    "AlgorithmProcessResult",
    "AlgorithmRunResult",
    "AlgorithmTraceFrame",
    "AlgorithmDescriptor",
    "AlgorithmConfigField",
    "AppConfig",
    "SCHEMA_VERSION",
    "SchedulerStrategy",
    "StrategySimulation",
    "ProcessInput",
    "build_algorithm_gantt_figure",
    "build_gantt_figure",
    "calculate_algorithm_metrics",
    "default_config",
]
