from __future__ import annotations

from mlfq_os_simulator.algorithms.fcfs.strategy import FCFSSchedulerStrategy
from mlfq_os_simulator.algorithms.round_robin.strategy import RoundRobinSchedulerStrategy
from mlfq_os_simulator.shared.config import AppConfig
from mlfq_os_simulator.shared.process import ProcessInput


def test_fcfs_runs_in_arrival_order() -> None:
    strategy = FCFSSchedulerStrategy()
    processes = [
        ProcessInput(pid="P1", arrival_time=0, burst_time=4),
        ProcessInput(pid="P2", arrival_time=1, burst_time=2),
    ]

    result = strategy.simulate(processes, AppConfig(context_switch_time=0)).result

    assert [(entry.Task, entry.Start, entry.Finish) for entry in result.gantt_entries] == [
        ("P1", 0, 4),
        ("P2", 4, 6),
    ]


def test_round_robin_rotates_on_quantum() -> None:
    strategy = RoundRobinSchedulerStrategy()
    processes = [
        ProcessInput(pid="P1", arrival_time=0, burst_time=6),
        ProcessInput(pid="P2", arrival_time=0, burst_time=3),
    ]

    result = strategy.simulate(processes, AppConfig(context_switch_time=0)).result

    assert [(entry.Task, entry.Start, entry.Finish) for entry in result.gantt_entries] == [
        ("P1", 0, 4),
        ("P2", 4, 7),
        ("P1", 7, 9),
    ]
