

from __future__ import annotations
 
from datetime import UTC, datetime
from uuid import uuid4
 
from ...shared.config import AppConfig
from ...shared.contracts import AlgorithmConfigField
from ...shared.metrics import calculate_algorithm_metrics
from ...shared.process import ProcessInput
from ...shared.results import (
    AlgorithmGanttEntry,
    AlgorithmProcessResult,
    AlgorithmRunResult,
    AlgorithmTraceFrame,
    StrategySimulation,
)
 
 
class SJFSchedulerStrategy:
    key: str = "sjf"
    display_name: str = "SJF"
    description: str = "Shortest Job First không preemptive, ưu tiên tiến trình có burst time ngắn nhất."
    config_fields: tuple[AlgorithmConfigField, ...] = (
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
    is_default: bool = False
    order: int = 20
 
    def simulate(
        self,
        processes: list[ProcessInput],
        config: AppConfig,
    ) -> StrategySimulation:
        # Sort processes by arrival time, then by original index to break ties deterministically
        arrivals = sorted(
            [(index, process) for index, process in enumerate(processes)],
            key=lambda item: (item[1].arrival_time, item[0]),
        )
        #Create the ready queue as a list (we'll sort it by burst time at each step); it holds tuples of (original_index, ProcessInput)
        ready: list[tuple[int, ProcessInput]] = []
        gantt_entries: list[AlgorithmGanttEntry] = []
        process_results: list[AlgorithmProcessResult] = []
        frames: list[AlgorithmTraceFrame] = []
        time_current = 0
        arrival_index = 0
        last_running_pid: str | None = None
 
        while arrival_index < len(arrivals) or ready:
            # Push all newly arrived processes into the ready queue
            while (
                arrival_index < len(arrivals)
                and arrivals[arrival_index][1].arrival_time <= time_current
            ):
                ready.append(arrivals[arrival_index])
                arrival_index += 1
 
            if not ready:
                # CPU idle until next arrival
                next_arrival = arrivals[arrival_index][1].arrival_time
                gantt_entries.append(
                    AlgorithmGanttEntry(
                        Task="Idle",
                        Start=time_current,
                        Finish=next_arrival,
                        Lane="CPU",
                    )
                )
                time_current = next_arrival
                last_running_pid = None
                continue
 
           
            # Choose the process with the shortest burst time (SJF), break ties by arrival time, then by original index
            # then to ensure stable sorting, we sort by burst time, then by arrival time, then by original index
            ready.sort(key=lambda item: (item[1].burst_time, item[1].arrival_time, item[0]))
            _, process = ready.pop(0)
 
            # Context switch 
            if last_running_pid is not None and config.context_switch_time > 0:
                cs_finish = time_current + config.context_switch_time
                gantt_entries.append(
                    AlgorithmGanttEntry(
                        Task="CS Overhead",
                        Start=time_current,
                        Finish=cs_finish,
                        Lane="CS",
                    )
                )
                time_current = cs_finish
                frames.append(
                    AlgorithmTraceFrame(
                        time_current=time_current,
                        status="Context switch overhead",
                        running_label="CS Overhead",
                        lanes_snapshot={"Ready": [item[1].pid for item in ready], "CPU": []},
                        completed_labels=[item.pid for item in process_results],
                        gantt_entries=[entry.model_copy(deep=True) for entry in gantt_entries],
                    )
                )
 
            # Run the chosen process to completion (non-preemptive)
            start_time = time_current
            finish_time = time_current + process.burst_time
            gantt_entries.append(
                AlgorithmGanttEntry(
                    Task=process.pid,
                    Start=start_time,
                    Finish=finish_time,
                    Lane="CPU",
                )
            )
            time_current = finish_time
            process_results.append(
                AlgorithmProcessResult(
                    pid=process.pid,
                    arrival_time=process.arrival_time,
                    burst_time=process.burst_time,
                    start_time=start_time,
                    completion_time=finish_time,
                    turnaround_time=finish_time - process.arrival_time,
                    waiting_time=(finish_time - process.arrival_time) - process.burst_time,
                    response_time=start_time - process.arrival_time,
                )
            )
            frames.append(
                AlgorithmTraceFrame(
                    time_current=time_current,
                    status=f"Run {process.pid} to completion",
                    running_label=process.pid,
                    lanes_snapshot={"Ready": [item[1].pid for item in ready], "CPU": []},
                    completed_labels=[item.pid for item in process_results],
                    gantt_entries=[entry.model_copy(deep=True) for entry in gantt_entries],
                )
            )
            last_running_pid = process.pid
 
        # Sort process_results back to the original order of processes for consistent output
        process_results.sort(
            key=lambda item: next(i for i, p in enumerate(processes) if p.pid == item.pid)
        )
        metrics = calculate_algorithm_metrics(process_results)
        result = AlgorithmRunResult(
            run_id=uuid4().hex,
            algorithm_key=self.key,
            algorithm_display_name=self.display_name,
            timestamp=datetime.now(UTC),
            config_used=config,
            process_count=len(processes),
            process_inputs=processes,
            process_results=process_results,
            gantt_entries=gantt_entries,
            makespan=int(metrics["makespan"]),
            throughput=metrics["throughput"],
            avg_turnaround=metrics["avg_turnaround"],
            avg_waiting=metrics["avg_waiting"],
            avg_response=metrics["avg_response"],
        )
        return StrategySimulation(result=result, frames=frames)