from __future__ import annotations

import pandas as pd
import streamlit as st

from ..application.comparison_models import ComparisonReport, ComparisonWorkload
from ..application.workloads import curated_workloads
from ..shared.config import AppConfig
from ..shared.metrics import build_algorithm_gantt_figure
from .simulator_tab import normalize_process_rows


def render_comparison_tab(
    comparison_service,
    config: AppConfig,
) -> None:
    st.subheader("Comparison")

    workloads = curated_workloads()
    workload_map = {workload.key: workload for workload in workloads}
    workload_options = {
        "current_table": "Current Table",
        **{workload.key: workload.display_name for workload in workloads},
    }

    option_keys = list(workload_options.keys())
    selected_key = st.selectbox(
        "Workload Source",
        options=option_keys,
        format_func=lambda key: workload_options[key],
        key="comparison_workload_key",
    )

    if st.button("Compare Algorithms", type="primary", key="compare_algorithms_button"):
        workload = _resolve_workload(selected_key, workload_map)
        if workload is None:
            process_rows = st.session_state.get("process_rows", [])
            processes, errors = normalize_process_rows(process_rows)
            if errors:
                for error in errors:
                    st.error(error)
                return
            workload = comparison_service.workload_from_current_table(processes)

        st.session_state["comparison_report"] = comparison_service.compare(workload, config)

    report = st.session_state.get("comparison_report")
    if report is not None:
        render_comparison_report(report)


def _resolve_workload(
    selected_key: str,
    workload_map: dict[str, ComparisonWorkload],
) -> ComparisonWorkload | None:
    if selected_key == "current_table":
        return None
    return workload_map[selected_key]


def render_comparison_report(report: ComparisonReport) -> None:
    st.caption(report.workload_description)
    rows = [
        {
            "Algorithm": result.algorithm_display_name,
            "Processes": result.process_count,
            "Avg Turnaround": round(result.avg_turnaround, 2),
            "Avg Waiting": round(result.avg_waiting, 2),
            "Avg Response": round(result.avg_response, 2),
            "Throughput": round(result.throughput, 4),
            "Makespan": result.makespan,
        }
        for result in report.results
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

    st.info(report.discussion)

    preview_tabs = st.tabs([result.algorithm_display_name for result in report.results])
    for tab, result in zip(preview_tabs, report.results, strict=True):
        with tab:
            if result.gantt_entries:
                st.plotly_chart(build_algorithm_gantt_figure(result.gantt_entries), width="stretch")
            st.dataframe(
                pd.DataFrame([item.model_dump(mode="json") for item in result.process_results]),
                width="stretch",
                hide_index=True,
            )
