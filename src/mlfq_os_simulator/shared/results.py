from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .config import AppConfig
from .process import ProcessInput


class AlgorithmProcessResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pid: str
    arrival_time: int = Field(ge=0)
    burst_time: int = Field(gt=0)
    start_time: int = Field(ge=0)
    completion_time: int = Field(ge=0)
    turnaround_time: int
    waiting_time: int
    response_time: int


class AlgorithmGanttEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    Task: str
    Start: int = Field(ge=0)
    Finish: int = Field(gt=0)
    Lane: str


class AlgorithmRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    algorithm_key: str
    algorithm_display_name: str
    timestamp: datetime
    config_used: AppConfig
    process_count: int
    process_inputs: list[ProcessInput]
    process_results: list[AlgorithmProcessResult]
    gantt_entries: list[AlgorithmGanttEntry]
    makespan: int = Field(ge=0)
    throughput: float
    avg_turnaround: float
    avg_waiting: float
    avg_response: float


@dataclass(slots=True)
class AlgorithmTraceFrame:
    time_current: int
    status: str
    running_label: str | None
    lanes_snapshot: dict[str, list[str]]
    completed_labels: list[str]
    gantt_entries: list[AlgorithmGanttEntry]


@dataclass(slots=True)
class StrategySimulation:
    result: AlgorithmRunResult
    frames: list[AlgorithmTraceFrame]
