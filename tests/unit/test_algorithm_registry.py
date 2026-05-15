from __future__ import annotations

from mlfq_os_simulator.application.services import build_scheduler_registry
from mlfq_os_simulator.shared.config import AppConfig
from mlfq_os_simulator.shared.process import ProcessInput


def test_registry_contains_phase_one_algorithms() -> None:
    registry = build_scheduler_registry()

    assert registry.keys() == ["mlfq", "fcfs", "round_robin"]


def test_registry_exposes_algorithm_descriptors() -> None:
    registry = build_scheduler_registry()

    descriptor = registry.describe("round_robin")

    assert descriptor.display_name == "Round Robin"
    assert [field.key for field in descriptor.config_fields] == [
        "round_robin_quantum",
        "context_switch_time",
    ]
    assert descriptor.supports_animation is True


def test_registry_can_discover_comparison_participants() -> None:
    registry = build_scheduler_registry()

    assert [item.key for item in registry.comparison_descriptors()] == [
        "mlfq",
        "fcfs",
        "round_robin",
    ]
    assert registry.default_descriptor().key == "mlfq"


def test_registry_simulates_mlfq() -> None:
    registry = build_scheduler_registry()
    result = registry.simulate(
        "mlfq",
        [ProcessInput(pid="P1", arrival_time=0, burst_time=2)],
        AppConfig(),
    )

    assert result.result.algorithm_display_name == "MLFQ"
