from __future__ import annotations

import pandas as pd
import streamlit as st

from ..application.comparison_models import ComparisonReport, ComparisonWorkload
from ..application.workloads import curated_workloads
from ..shared.config import AppConfig
from ..shared.contracts import AlgorithmDescriptor
from ..shared.metrics import build_algorithm_gantt_figure
from .config_fields import render_config_fields
from .simulator_tab import normalize_process_rows


def render_comparison_tab(
    comparison_service,
    config: AppConfig,
) -> None:
    st.subheader("Comparison")
    config_map = _ensure_comparison_config_map(comparison_service, config)
    _render_comparison_config_panel(comparison_service.comparison_descriptors(), config_map)

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

        st.session_state["comparison_report"] = comparison_service.compare(workload, config_map)

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


def _ensure_comparison_config_map(
    comparison_service,
    seed_config: AppConfig,
) -> dict[str, AppConfig]:
    existing = st.session_state.get("comparison_config_map", {})
    if not isinstance(existing, dict):
        existing = {}

    normalized: dict[str, AppConfig] = {}
    for descriptor in comparison_service.comparison_descriptors():
        stored = existing.get(descriptor.key)
        if isinstance(stored, AppConfig):
            normalized[descriptor.key] = stored
            continue
        if isinstance(stored, dict):
            normalized[descriptor.key] = AppConfig.model_validate(stored)
            continue
        normalized[descriptor.key] = AppConfig.model_validate(seed_config.model_dump(mode="json"))

    st.session_state["comparison_config_map"] = normalized
    return normalized


def _render_comparison_config_panel(
    descriptors: list[AlgorithmDescriptor],
    config_map: dict[str, AppConfig],
) -> None:
    st.caption(
        "Comparison dùng config riêng cho từng thuật toán, độc lập với sidebar của Simulator."
    )
    for descriptor in descriptors:
        with st.expander(
            f"{descriptor.display_name} Parameters",
            expanded=descriptor.is_default,
        ):
            st.caption(descriptor.description)
            config_map[descriptor.key] = render_config_fields(
                st,
                config_map[descriptor.key],
                descriptor.config_fields,
                f"comparison_config_{descriptor.key}",
            )

    st.session_state["comparison_config_map"] = config_map


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
                st.plotly_chart(
                    build_algorithm_gantt_figure(result.gantt_entries),
                    key=f"comparison_gantt_{report.workload_key}_{result.algorithm_key}",
                    width="stretch",
                )
            st.dataframe(
                pd.DataFrame([item.model_dump(mode="json") for item in result.process_results]),
                width="stretch",
                hide_index=True,
            )
