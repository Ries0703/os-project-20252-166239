from __future__ import annotations

from collections import defaultdict, deque
from datetime import UTC, datetime
from statistics import mean
from uuid import uuid4

from ...shared.config import AppConfig
from ...shared.process import ProcessInput
from .runtime_models import (
    GanttLogEntry,
    ProcessState,
    SimulationFrame,
    SimulationOutcome,
    SimulationRun,
)

MAX_SIMULATION_TICKS = 100_000


def _queue_label(queue_index: int | None) -> str:
    if queue_index is None:
        return "N/A"
    return f"Q{queue_index}"


def _append_gantt_entry(
    entries: list[GanttLogEntry],
    task: str,
    start: int,
    finish: int,
    queue: str,
) -> None:
    if finish <= start:
        return

    if (
        entries
        and entries[-1].Task == task
        and entries[-1].Queue == queue
        and entries[-1].Finish == start
    ):
        entries[-1].Finish = finish
        return

    entries.append(GanttLogEntry(Task=task, Start=start, Finish=finish, Queue=queue))


def _consume_context_switch_tick(
    entries: list[GanttLogEntry],
    time_current: int,
    remaining_ticks: int,
) -> tuple[int, int]:
    _append_gantt_entry(entries, "CS Overhead", time_current, time_current + 1, "N/A")
    return time_current + 1, remaining_ticks - 1


class MLFQEngine:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def run(self, processes: list[ProcessInput]) -> SimulationOutcome:
        if not processes:
            raise ValueError("At least one process is required")

        seen_pids: set[str] = set()
        for process in processes:
            if process.pid in seen_pids:
                raise ValueError(f"Duplicate pid: {process.pid}")
            seen_pids.add(process.pid)

        queues: dict[int, deque[ProcessState]] = {0: deque(), 1: deque(), 2: deque()}
        arrivals: dict[int, list[ProcessState]] = defaultdict(list)
        for index, process in enumerate(processes):
            arrivals[process.arrival_time].append(ProcessState.from_input(process, index))

        gantt_log: list[GanttLogEntry] = []
        frames: list[SimulationFrame] = []
        completed: list[ProcessState] = []
        time_current = 0
        running: ProcessState | None = None
        cs_remaining = 0
        pending_switch_from_process = False

        while len(completed) < len(processes):
            if time_current > MAX_SIMULATION_TICKS:
                raise TimeoutError("Infinite loop detected")

            q0_received_new_work = False
            tick_events: list[str] = []

            if time_current in arrivals:
                for process in arrivals[time_current]:
                    queues[0].append(process)
                q0_received_new_work = q0_received_new_work or bool(arrivals[time_current])
                tick_events.extend(
                    f"Arrival {process.pid} -> Q0" for process in arrivals[time_current]
                )

            if time_current > 0 and time_current % self.config.aging_boost_interval == 0:
                moved_processes: list[ProcessState] = []
                for queue_index in (1, 2):
                    while queues[queue_index]:
                        process = queues[queue_index].popleft()
                        process.current_queue = 0
                        process.quantum_used = 0
                        moved_processes.append(process)
                for process in moved_processes:
                    queues[0].append(process)
                q0_received_new_work = q0_received_new_work or bool(moved_processes)
                if moved_processes:
                    tick_events.append("Priority boost: waiting processes -> Q0")

                if running is not None:
                    running.current_queue = 0
                    running.quantum_used = 0
                    tick_events.append(f"Boost reset quantum for {running.pid}")

            if cs_remaining > 0:
                _append_gantt_entry(gantt_log, "CS Overhead", time_current, time_current + 1, "N/A")
                cs_remaining -= 1
                frames.append(
                    self._build_frame(
                        time_current=time_current + 1,
                        status=" | ".join(tick_events + ["Context switch"]),
                        running=None,
                        queues=queues,
                        completed=completed,
                        gantt_log=gantt_log,
                    )
                )
                time_current += 1
                continue

            if (
                running is not None
                and running.current_queue in (1, 2)
                and q0_received_new_work
                and queues[0]
            ):
                tick_events.append(f"Preempt {running.pid} for Q0 work")
                queues[running.current_queue].appendleft(running)
                running = None
                if self.config.context_switch_time > 0:
                    time_current, cs_remaining = _consume_context_switch_tick(
                        gantt_log,
                        time_current,
                        self.config.context_switch_time,
                    )
                    frames.append(
                        self._build_frame(
                            time_current=time_current,
                            status=" | ".join(tick_events + ["Context switch"]),
                            running=None,
                            queues=queues,
                            completed=completed,
                            gantt_log=gantt_log,
                        )
                    )
                    continue

            if running is None:
                next_queue_index = self._find_next_queue(queues)
                if next_queue_index is None:
                    pending_switch_from_process = False
                    _append_gantt_entry(gantt_log, "Idle", time_current, time_current + 1, "N/A")
                    frames.append(
                        self._build_frame(
                            time_current=time_current + 1,
                            status=" | ".join(tick_events + ["CPU idle"]),
                            running=None,
                            queues=queues,
                            completed=completed,
                            gantt_log=gantt_log,
                        )
                    )
                    time_current += 1
                    continue

                if pending_switch_from_process and self.config.context_switch_time > 0:
                    pending_switch_from_process = False
                    time_current, cs_remaining = _consume_context_switch_tick(
                        gantt_log,
                        time_current,
                        self.config.context_switch_time,
                    )
                    frames.append(
                        self._build_frame(
                            time_current=time_current,
                            status=" | ".join(tick_events + ["Context switch"]),
                            running=None,
                            queues=queues,
                            completed=completed,
                            gantt_log=gantt_log,
                        )
                    )
                    continue

                pending_switch_from_process = False
                running = queues[next_queue_index].popleft()
                running.current_queue = next_queue_index
                if running.start_time is None:
                    running.start_time = time_current
                tick_events.append(f"Dispatch {running.pid} from Q{next_queue_index}")

            _append_gantt_entry(
                gantt_log,
                running.pid,
                time_current,
                time_current + 1,
                _queue_label(running.current_queue),
            )
            running.remaining_time -= 1
            running.quantum_used += 1
            time_current += 1

            if running.remaining_time == 0:
                tick_events.append(f"Complete {running.pid}")
                running.completion_time = time_current
                completed.append(running)
                frames.append(
                    self._build_frame(
                        time_current=time_current,
                        status=" | ".join(tick_events),
                        running=None,
                        queues=queues,
                        completed=completed,
                        gantt_log=gantt_log,
                    )
                )
                running = None
                pending_switch_from_process = True
                continue

            if running.quantum_used >= self._quantum_for_queue(running.current_queue):
                next_queue = min(2, running.current_queue + 1)
                tick_events.append(f"Demote {running.pid} -> Q{next_queue}")
                running.current_queue = next_queue
                running.quantum_used = 0
                queues[next_queue].append(running)
                frames.append(
                    self._build_frame(
                        time_current=time_current,
                        status=" | ".join(tick_events),
                        running=None,
                        queues=queues,
                        completed=completed,
                        gantt_log=gantt_log,
                    )
                )
                running = None
                pending_switch_from_process = True
            else:
                frames.append(
                    self._build_frame(
                        time_current=time_current,
                        status=" | ".join(tick_events + [f"Run {running.pid}"]),
                        running=running,
                        queues=queues,
                        completed=completed,
                        gantt_log=gantt_log,
                    )
                )

        completed.sort(key=lambda process: process.input_order)
        self._validate_invariants(completed, gantt_log, processes)

        makespan = max((process.completion_time or 0) for process in completed)
        throughput = len(completed) / makespan if makespan > 0 else 0.0
        avg_turnaround = float(mean(process.turnaround_time for process in completed))
        avg_waiting = float(mean(process.waiting_time for process in completed))
        avg_response = float(mean(process.response_time for process in completed))

        run = SimulationRun(
            run_id=uuid4().hex,
            timestamp=datetime.now(UTC),
            config_used=self.config,
            processes=completed,
            gantt_log=gantt_log,
            throughput=throughput,
            avg_turnaround=avg_turnaround,
            avg_waiting=avg_waiting,
            avg_response=avg_response,
        )
        return SimulationOutcome(run=run, frames=frames)

    @staticmethod
    def _find_next_queue(queues: dict[int, deque[ProcessState]]) -> int | None:
        for queue_index in (0, 1, 2):
            if queues[queue_index]:
                return queue_index
        return None

    def _quantum_for_queue(self, queue_index: int) -> int:
        if queue_index == 0:
            return self.config.quantum_q0
        if queue_index == 1:
            return self.config.quantum_q1
        return self.config.quantum_q2

    def _build_frame(
        self,
        time_current: int,
        status: str,
        running: ProcessState | None,
        queues: dict[int, deque[ProcessState]],
        completed: list[ProcessState],
        gantt_log: list[GanttLogEntry],
    ) -> SimulationFrame:
        def describe(process: ProcessState) -> str:
            return f"{process.pid} (rem={process.remaining_time})"

        queue_snapshot = {
            "Q0": [describe(process) for process in queues[0]],
            "Q1": [describe(process) for process in queues[1]],
            "Q2": [describe(process) for process in queues[2]],
        }
        running_queue = "N/A" if running is None else _queue_label(running.current_queue)

        return SimulationFrame(
            time_current=time_current,
            status=status or "Tick",
            running_pid=None if running is None else running.pid,
            running_queue=running_queue,
            queue_snapshot=queue_snapshot,
            completed_pids=[process.pid for process in completed],
            gantt_log=[entry.model_copy(deep=True) for entry in gantt_log],
        )

    def _validate_invariants(
        self,
        completed: list[ProcessState],
        gantt_log: list[GanttLogEntry],
        original_processes: list[ProcessInput],
    ) -> None:
        if len(completed) != len(original_processes):
            raise ValueError("Not all processes completed")

        if any(process.remaining_time < 0 for process in completed):
            raise ValueError("A process has negative remaining time")

        total_executed = sum(
            entry.Finish - entry.Start
            for entry in gantt_log
            if entry.Task not in {"Idle", "CS Overhead"}
        )
        total_burst = sum(process.burst_time for process in original_processes)
        if total_executed != total_burst:
            raise ValueError("Executed time does not match total burst time")
