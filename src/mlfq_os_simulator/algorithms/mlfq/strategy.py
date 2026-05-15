from __future__ import annotations

from ...shared.config import AppConfig
from ...shared.contracts import AlgorithmConfigField
from ...shared.process import ProcessInput
from ...shared.results import (
    AlgorithmGanttEntry,
    AlgorithmProcessResult,
    AlgorithmRunResult,
    AlgorithmTraceFrame,
    StrategySimulation,
)
from .engine import MLFQEngine


class MLFQStrategy:
    key: str = "mlfq"
    display_name: str = "MLFQ"
    description: str = "Multi-Level Feedback Queue với Q0/Q1/Q2, preemption và priority boost."
    config_fields: tuple[AlgorithmConfigField, ...] = (
        AlgorithmConfigField("quantum_q0", "Q0 Quantum", 4, min_value=1),
        AlgorithmConfigField("quantum_q1", "Q1 Quantum", 8, min_value=1),
        AlgorithmConfigField("quantum_q2", "Q2 Quantum", 16, min_value=1),
        AlgorithmConfigField(
            "aging_boost_interval",
            "Aging Boost Interval",
            50,
            min_value=1,
            max_value=200,
            widget="slider",
        ),
        AlgorithmConfigField(
            "context_switch_time",
            "Context Switch Time",
            1,
            min_value=0,
            max_value=20,
        ),
    )
    supports_animation: bool = True
    include_in_comparison: bool = True
    is_default: bool = True
    order: int = 0

    def simulate(
        self,
        processes: list[ProcessInput],
        config: AppConfig,
    ) -> StrategySimulation:
        outcome = MLFQEngine(config).run(processes)
        run = outcome.run

        result = AlgorithmRunResult(
            run_id=run.run_id,
            algorithm_key=self.key,
            algorithm_display_name=self.display_name,
            timestamp=run.timestamp,
            config_used=config,
            process_count=len(run.processes),
            process_inputs=processes,
            process_results=[
                AlgorithmProcessResult(
                    pid=process.pid,
                    arrival_time=process.arrival_time,
                    burst_time=process.burst_time,
                    start_time=process.start_time or 0,
                    completion_time=process.completion_time or 0,
                    turnaround_time=process.turnaround_time,
                    waiting_time=process.waiting_time,
                    response_time=process.response_time,
                )
                for process in run.processes
            ],
            gantt_entries=[
                AlgorithmGanttEntry(
                    Task=entry.Task,
                    Start=entry.Start,
                    Finish=entry.Finish,
                    Lane=entry.Queue,
                )
                for entry in run.gantt_log
            ],
            makespan=max((process.completion_time or 0) for process in run.processes),
            throughput=run.throughput,
            avg_turnaround=run.avg_turnaround,
            avg_waiting=run.avg_waiting,
            avg_response=run.avg_response,
        )

        frames = [
            AlgorithmTraceFrame(
                time_current=frame.time_current,
                status=frame.status,
                running_label=(
                    None
                    if frame.running_pid is None
                    else f"{frame.running_pid} ({frame.running_queue})"
                ),
                lanes_snapshot=frame.queue_snapshot,
                completed_labels=frame.completed_pids,
                gantt_entries=[
                    AlgorithmGanttEntry(
                        Task=entry.Task,
                        Start=entry.Start,
                        Finish=entry.Finish,
                        Lane=entry.Queue,
                    )
                    for entry in frame.gantt_log
                ],
            )
            for frame in outcome.frames
        ]

        return StrategySimulation(result=result, frames=frames)
