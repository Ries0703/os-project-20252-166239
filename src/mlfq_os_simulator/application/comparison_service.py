from __future__ import annotations

from ..shared.config import AppConfig
from ..shared.process import ProcessInput
from .comparison_models import ComparisonReport, ComparisonWorkload
from .registry import SchedulerRegistry


class ComparisonService:
    def __init__(self, registry: SchedulerRegistry) -> None:
        self.registry = registry

    def compare(
        self,
        workload: ComparisonWorkload,
        config: AppConfig,
        strategy_keys: list[str] | None = None,
    ) -> ComparisonReport:
        keys = strategy_keys or [
            descriptor.key for descriptor in self.registry.comparison_descriptors()
        ]
        results = [
            self.registry.simulate(key, workload.processes, config).result
            for key in keys
        ]

        discussion = self._build_discussion(workload, results, config)

        return ComparisonReport(
            workload_key=workload.key,
            workload_display_name=workload.display_name,
            workload_description=workload.description,
            results=results,
            discussion=discussion,
        )

    @staticmethod
    def workload_from_current_table(
        processes: list[ProcessInput],
    ) -> ComparisonWorkload:
        return ComparisonWorkload(
            key="current_table",
            display_name="Current Table",
            description="Current process table from the simulator tab.",
            processes=processes,
        )

    def _build_discussion(
        self,
        workload: ComparisonWorkload,
        results,
        config: AppConfig,
    ) -> str:
        sorted_by_response = sorted(results, key=lambda item: item.avg_response)
        best_response = sorted_by_response[0]
        best_turnaround = min(results, key=lambda item: item.avg_turnaround)
        mlfq_descriptor = next(
            (
                descriptor
                for descriptor in self.registry.descriptors()
                if descriptor.key == "mlfq"
            ),
            None,
        )
        mlfq_factor_summary = "các quantum queue, boost interval và context switch time"
        if mlfq_descriptor is not None:
            parts = [
                f"{field.label}={config.get_int(field.key, field.default)}"
                for field in mlfq_descriptor.config_fields
            ]
            mlfq_factor_summary = ", ".join(parts)
        return (
            f"Workload `{workload.display_name}` cho thấy `{best_response.algorithm_display_name}` "
            f"có response tốt nhất ({best_response.avg_response:.2f}), trong khi "
            f"`{best_turnaround.algorithm_display_name}` có turnaround tốt nhất "
            f"({best_turnaround.avg_turnaround:.2f}). Với MLFQ, "
            f"{mlfq_factor_summary} là các yếu tố chính "
            f"ảnh hưởng fairness và throughput."
        )
