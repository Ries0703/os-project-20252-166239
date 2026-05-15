from __future__ import annotations

import pandas as pd
import streamlit as st

from ..shared.results import AlgorithmRunResult


def render_history_tab(runs: list[AlgorithmRunResult]) -> None:
    if not runs:
        st.info("Chưa có lịch sử mô phỏng.")
        return

    rows = [
        {
            "Run ID": run.run_id,
            "Timestamp": run.timestamp.isoformat(),
            "Algorithm": run.algorithm_display_name,
            "Processes": len(run.process_results),
            "Avg Turnaround": round(run.avg_turnaround, 2),
            "Avg Waiting": round(run.avg_waiting, 2),
            "Avg Response": round(run.avg_response, 2),
            "Throughput": round(run.throughput, 4),
        }
        for run in runs
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
