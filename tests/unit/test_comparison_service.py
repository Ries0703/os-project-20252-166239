from __future__ import annotations

from mlfq_os_simulator.application.services import build_comparison_service
from mlfq_os_simulator.application.workloads import curated_workloads
from mlfq_os_simulator.shared.config import AppConfig
from mlfq_os_simulator.shared.process import ProcessInput


def test_comparison_service_runs_three_algorithms() -> None:
    service = build_comparison_service()
    workload = curated_workloads()[0]

    report = service.compare(workload, AppConfig())

    assert [result.algorithm_key for result in report.results] == ["mlfq", "fcfs", "round_robin"]
    assert "response" in report.discussion.lower()


def test_comparison_service_uses_per_algorithm_config_map() -> None:
    service = build_comparison_service()
    workload = service.workload_from_current_table(
        [
            ProcessInput(pid="P1", arrival_time=0, burst_time=6),
            ProcessInput(pid="P2", arrival_time=0, burst_time=3),
        ]
    )

    report = service.compare(
        workload,
        {
            "mlfq": AppConfig(quantum_q0=5),
            "fcfs": AppConfig(context_switch_time=0),
            "round_robin": AppConfig(round_robin_quantum=2, context_switch_time=0),
        },
        strategy_keys=["round_robin", "mlfq"],
    )

    round_robin_result = next(
        result for result in report.results if result.algorithm_key == "round_robin"
    )

    assert round_robin_result.gantt_entries[0].Finish == 2
    assert "Q0 Quantum=5" in report.discussion
