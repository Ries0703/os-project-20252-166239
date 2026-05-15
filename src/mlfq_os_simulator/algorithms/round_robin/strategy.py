from __future__ import annotations

from collections import deque
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

DEFAULT_RR_QUANTUM = 4


class RoundRobinSchedulerStrategy:
    key: str = "round_robin"
    display_name: str = "Round Robin"
    description: str = "Round Robin với ready queue FIFO và quantum cấu hình được."
    config_fields: tuple[AlgorithmConfigField, ...] = (
        AlgorithmConfigField("round_robin_quantum", "Round Robin Quantum", 4, min_value=1),
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
        arrivals = sorted(
            [(index, process) for index, process in enumerate(processes)],
            key=lambda item: (item[1].arrival_time, item[0]),
        )
        ready: deque[dict[str, int | str | bool]] = deque()
        gantt_entries: list[AlgorithmGanttEntry] = []
        frames: list[AlgorithmTraceFrame] = []
        result_index: dict[str, AlgorithmProcessResult] = {}
        time_current = 0
        arrival_index = 0
        last_running_pid: str | None = None

        def enqueue_arrivals() -> None:
            nonlocal arrival_index
            while (
                arrival_index < len(arrivals)
                and arrivals[arrival_index][1].arrival_time <= time_current
            ):
                _, process = arrivals[arrival_index]
                ready.append(
                    {
                        "pid": process.pid,
                        "arrival_time": process.arrival_time,
                        "burst_time": process.burst_time,
                        "remaining_time": process.burst_time,
                        "started": False,
                    }
                )
                arrival_index += 1

        while arrival_index < len(arrivals) or ready:
            enqueue_arrivals()

            if not ready:
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

            current = ready.popleft()
            pid = str(current["pid"])
            arrival_time = int(current["arrival_time"])
            burst_time = int(current["burst_time"])
            remaining_time = int(current["remaining_time"])
            started = bool(current["started"])
            if (
                last_running_pid is not None
                and last_running_pid != pid
                and config.context_switch_time > 0
            ):
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
                enqueue_arrivals()
                frames.append(
                    AlgorithmTraceFrame(
                        time_current=time_current,
                        status="Context switch overhead",
                        running_label="CS Overhead",
                        lanes_snapshot={"Ready": [str(item["pid"]) for item in ready], "CPU": []},
                        completed_labels=[
                            key for key, item in result_index.items() if item.completion_time > 0
                        ],
                        gantt_entries=[entry.model_copy(deep=True) for entry in gantt_entries],
                    )
                )

            start_time = time_current if not started else result_index[pid].start_time
            quantum = config.round_robin_quantum or DEFAULT_RR_QUANTUM
            slice_time = min(quantum, remaining_time)
            finish_time = time_current + slice_time

            gantt_entries.append(
                AlgorithmGanttEntry(Task=pid, Start=time_current, Finish=finish_time, Lane="CPU")
            )
            time_current = finish_time
            remaining_time -= slice_time

            if pid not in result_index:
                result_index[pid] = AlgorithmProcessResult(
                    pid=pid,
                    arrival_time=arrival_time,
                    burst_time=burst_time,
                    start_time=start_time,
                    completion_time=0,
                    turnaround_time=0,
                    waiting_time=0,
                    response_time=start_time - arrival_time,
                )

            enqueue_arrivals()

            if remaining_time > 0:
                ready.append(
                    {
                        "pid": pid,
                        "arrival_time": arrival_time,
                        "burst_time": burst_time,
                        "remaining_time": remaining_time,
                        "started": True,
                    }
                )
                status = f"Run {pid} for quantum {slice_time}"
            else:
                completion_time = time_current
                result_index[pid] = AlgorithmProcessResult(
                    pid=pid,
                    arrival_time=arrival_time,
                    burst_time=burst_time,
                    start_time=start_time,
                    completion_time=completion_time,
                    turnaround_time=completion_time - arrival_time,
                    waiting_time=(completion_time - arrival_time) - burst_time,
                    response_time=start_time - arrival_time,
                )
                status = f"Complete {pid}"

            completed_labels = [
                key for key, item in result_index.items() if item.completion_time > 0
            ]
            frames.append(
                AlgorithmTraceFrame(
                    time_current=time_current,
                    status=status,
                    running_label=pid,
                    lanes_snapshot={"Ready": [str(item["pid"]) for item in ready], "CPU": []},
                    completed_labels=completed_labels,
                    gantt_entries=[entry.model_copy(deep=True) for entry in gantt_entries],
                )
            )
            last_running_pid = pid

        process_results = [result_index[process.pid] for process in processes]
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
