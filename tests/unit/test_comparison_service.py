from __future__ import annotations

from mlfq_os_simulator.application.services import build_comparison_service
from mlfq_os_simulator.application.workloads import curated_workloads
from mlfq_os_simulator.shared.config import AppConfig


def test_comparison_service_runs_three_algorithms() -> None:
    service = build_comparison_service()
    workload = curated_workloads()[0]

    report = service.compare(workload, AppConfig())

    assert [result.algorithm_key for result in report.results] == ["mlfq", "fcfs", "round_robin"]
    assert "response" in report.discussion.lower()
