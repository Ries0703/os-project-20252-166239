from __future__ import annotations

import pandas as pd
import streamlit as st

from ..shared.metrics import build_algorithm_gantt_figure
from ..shared.results import AlgorithmRunResult


def render_dashboard_tab(run: AlgorithmRunResult | None) -> None:
    if run is None:
        st.info("Chưa có kết quả mô phỏng. Hãy chạy simulation ở tab Simulator.")
        return

    st.subheader("Kết quả mô phỏng")
    metric_cols = st.columns(4)
    metric_cols[0].metric("Avg Turnaround", f"{run.avg_turnaround:.2f}")
    metric_cols[1].metric("Avg Waiting", f"{run.avg_waiting:.2f}")
    metric_cols[2].metric("Avg Response", f"{run.avg_response:.2f}")
    metric_cols[3].metric("Throughput", f"{run.throughput:.4f}")

    if run.gantt_entries:
        st.plotly_chart(
            build_algorithm_gantt_figure(run.gantt_entries),
            key=f"dashboard_gantt_{run.run_id}_{run.algorithm_key}",
            width="stretch",
        )

    process_rows = [
        {
            "PID": process.pid,
            "Arrival Time": process.arrival_time,
            "Burst Time": process.burst_time,
            "Completion Time": process.completion_time,
            "Turnaround": process.turnaround_time,
            "Waiting": process.waiting_time,
            "Response": process.response_time,
        }
        for process in run.process_results
    ]
    st.dataframe(pd.DataFrame(process_rows), width="stretch", hide_index=True)
