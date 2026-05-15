from __future__ import annotations

from mlfq_os_simulator.algorithms.mlfq.engine import MLFQEngine
from mlfq_os_simulator.shared.config import AppConfig
from mlfq_os_simulator.shared.process import ProcessInput
from mlfq_os_simulator.ui.simulator_tab import build_demo_process_rows


def _gantt_tuples(run) -> list[tuple[str, int, int, str]]:
    return [(entry.Task, entry.Start, entry.Finish, entry.Queue) for entry in run.gantt_log]


def test_single_process_demotes_across_all_queues() -> None:
    config = AppConfig(
        quantum_q0=4,
        quantum_q1=8,
        quantum_q2=16,
        aging_boost_interval=50,
        context_switch_time=0,
    )
    run = MLFQEngine(config).run([ProcessInput(pid="P1", arrival_time=0, burst_time=20)]).run

    assert _gantt_tuples(run) == [
        ("P1", 0, 4, "Q0"),
        ("P1", 4, 12, "Q1"),
        ("P1", 12, 20, "Q2"),
    ]
    assert run.avg_turnaround == 20.0
    assert run.avg_waiting == 0.0
    assert run.avg_response == 0.0
    assert run.throughput == 0.05


def test_preemption_by_new_q0_process() -> None:
    config = AppConfig(
        quantum_q0=2,
        quantum_q1=4,
        quantum_q2=8,
        aging_boost_interval=50,
        context_switch_time=0,
    )
    processes = [
        ProcessInput(pid="P1", arrival_time=0, burst_time=7),
        ProcessInput(pid="P2", arrival_time=3, burst_time=1),
    ]

    run = MLFQEngine(config).run(processes).run

    assert _gantt_tuples(run) == [
        ("P1", 0, 2, "Q0"),
        ("P1", 2, 3, "Q1"),
        ("P2", 3, 4, "Q0"),
        ("P1", 4, 7, "Q1"),
        ("P1", 7, 8, "Q2"),
    ]


def test_priority_boost_moves_waiting_processes_back_to_q0() -> None:
    config = AppConfig(
        quantum_q0=1,
        quantum_q1=1,
        quantum_q2=2,
        aging_boost_interval=4,
        context_switch_time=0,
    )
    processes = [
        ProcessInput(pid="P1", arrival_time=0, burst_time=5),
        ProcessInput(pid="P2", arrival_time=0, burst_time=5),
    ]

    run = MLFQEngine(config).run(processes).run

    assert _gantt_tuples(run) == [
        ("P1", 0, 1, "Q0"),
        ("P2", 1, 2, "Q0"),
        ("P1", 2, 3, "Q1"),
        ("P2", 3, 4, "Q1"),
        ("P1", 4, 5, "Q0"),
        ("P2", 5, 6, "Q0"),
        ("P1", 6, 7, "Q1"),
        ("P2", 7, 8, "Q1"),
        ("P1", 8, 9, "Q0"),
        ("P2", 9, 10, "Q0"),
    ]


def test_context_switch_overhead_is_logged() -> None:
    config = AppConfig(
        quantum_q0=4,
        quantum_q1=8,
        quantum_q2=16,
        aging_boost_interval=50,
        context_switch_time=1,
    )
    processes = [
        ProcessInput(pid="P1", arrival_time=0, burst_time=1),
        ProcessInput(pid="P2", arrival_time=0, burst_time=1),
    ]

    run = MLFQEngine(config).run(processes).run

    assert _gantt_tuples(run) == [
        ("P1", 0, 1, "Q0"),
        ("CS Overhead", 1, 2, "N/A"),
        ("P2", 2, 3, "Q0"),
    ]


def test_idle_cpu_is_logged_before_first_arrival() -> None:
    config = AppConfig(
        quantum_q0=4,
        quantum_q1=8,
        quantum_q2=16,
        aging_boost_interval=50,
        context_switch_time=0,
    )

    run = MLFQEngine(config).run([ProcessInput(pid="P1", arrival_time=3, burst_time=2)]).run

    assert _gantt_tuples(run) == [
        ("Idle", 0, 3, "N/A"),
        ("P1", 3, 5, "Q0"),
    ]


def test_duplicate_pid_is_rejected() -> None:
    config = AppConfig()
    processes = [
        ProcessInput(pid="P1", arrival_time=0, burst_time=1),
        ProcessInput(pid="P1", arrival_time=1, burst_time=2),
    ]

    try:
        MLFQEngine(config).run(processes)
    except ValueError as exc:
        assert "Duplicate pid" in str(exc)
    else:
        raise AssertionError("Expected duplicate pid to fail")


def test_sample_data_runs_to_completion() -> None:
    processes = [ProcessInput(**row) for row in build_demo_process_rows()]
    run = MLFQEngine(AppConfig()).run(processes).run

    assert len(run.processes) == len(processes)
    assert all(process.remaining_time == 0 for process in run.processes)


def test_simulate_returns_trace_frames() -> None:
    processes = [ProcessInput(pid="P1", arrival_time=0, burst_time=3)]
    outcome = MLFQEngine(AppConfig(context_switch_time=0)).run(processes)

    assert outcome.frames
    assert outcome.frames[-1].completed_pids == ["P1"]
