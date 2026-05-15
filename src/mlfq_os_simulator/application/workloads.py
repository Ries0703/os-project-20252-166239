from __future__ import annotations

from ..shared.process import ProcessInput
from .comparison_models import ComparisonWorkload


def curated_workloads() -> list[ComparisonWorkload]:
    return [
        ComparisonWorkload(
            key="balanced_mix",
            display_name="Balanced Mix",
            description="Mix of short and medium jobs with moderate staggered arrivals.",
            processes=[
                ProcessInput(pid="P1", arrival_time=0, burst_time=8),
                ProcessInput(pid="P2", arrival_time=1, burst_time=4),
                ProcessInput(pid="P3", arrival_time=2, burst_time=6),
                ProcessInput(pid="P4", arrival_time=4, burst_time=3),
                ProcessInput(pid="P5", arrival_time=6, burst_time=5),
            ],
        ),
        ComparisonWorkload(
            key="interactive_heavy",
            display_name="Interactive Heavy",
            description=(
                "Frequent short jobs to highlight responsiveness and queue priority behavior."
            ),
            processes=[
                ProcessInput(pid="P1", arrival_time=0, burst_time=12),
                ProcessInput(pid="P2", arrival_time=1, burst_time=2),
                ProcessInput(pid="P3", arrival_time=2, burst_time=1),
                ProcessInput(pid="P4", arrival_time=3, burst_time=2),
                ProcessInput(pid="P5", arrival_time=4, burst_time=1),
                ProcessInput(pid="P6", arrival_time=5, burst_time=2),
            ],
        ),
        ComparisonWorkload(
            key="cpu_bound_heavy",
            display_name="CPU-Bound Heavy",
            description=(
                "Long-running jobs with sparse arrivals to reveal throughput and "
                "overhead tradeoffs."
            ),
            processes=[
                ProcessInput(pid="P1", arrival_time=0, burst_time=18),
                ProcessInput(pid="P2", arrival_time=0, burst_time=14),
                ProcessInput(pid="P3", arrival_time=3, burst_time=12),
                ProcessInput(pid="P4", arrival_time=9, burst_time=4),
            ],
        ),
    ]
