from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from ..shared.process import ProcessInput
from ..shared.results import AlgorithmRunResult


class ComparisonWorkload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    display_name: str
    description: str
    processes: list[ProcessInput]


class ComparisonReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    workload_key: str
    workload_display_name: str
    workload_description: str
    results: list[AlgorithmRunResult]
    discussion: str
