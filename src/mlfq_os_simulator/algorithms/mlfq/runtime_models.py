from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ...shared.config import SCHEMA_VERSION, AppConfig
from ...shared.process import ProcessInput


class ProcessState(ProcessInput):
    input_order: int = Field(ge=0)
    remaining_time: int = Field(ge=0)
    current_queue: int = Field(default=0, ge=0, le=2)
    quantum_used: int = Field(default=0, ge=0)
    start_time: int | None = Field(default=None, ge=0)
    completion_time: int | None = Field(default=None, ge=0)

    @classmethod
    def from_input(cls, process: ProcessInput, input_order: int) -> ProcessState:
        return cls(
            pid=process.pid,
            arrival_time=process.arrival_time,
            burst_time=process.burst_time,
            input_order=input_order,
            remaining_time=process.burst_time,
        )

    @property
    def turnaround_time(self) -> int:
        if self.completion_time is None:
            raise ValueError("completion_time is not set")
        return self.completion_time - self.arrival_time

    @property
    def waiting_time(self) -> int:
        return self.turnaround_time - self.burst_time

    @property
    def response_time(self) -> int:
        if self.start_time is None:
            raise ValueError("start_time is not set")
        return self.start_time - self.arrival_time


class GanttLogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Task: str
    Start: int = Field(ge=0)
    Finish: int = Field(gt=0)
    Queue: str


class SimulationRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=SCHEMA_VERSION)
    run_id: str
    timestamp: datetime
    config_used: AppConfig
    processes: list[ProcessState]
    gantt_log: list[GanttLogEntry]
    throughput: float
    avg_turnaround: float
    avg_waiting: float
    avg_response: float


@dataclass(slots=True)
class SimulationFrame:
    time_current: int
    status: str
    running_pid: str | None
    running_queue: str
    queue_snapshot: dict[str, list[str]]
    completed_pids: list[str]
    gantt_log: list[GanttLogEntry]


@dataclass(slots=True)
class SimulationOutcome:
    run: SimulationRun
    frames: list[SimulationFrame]
