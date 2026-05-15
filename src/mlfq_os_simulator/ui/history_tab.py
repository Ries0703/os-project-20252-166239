from __future__ import annotations

import pandas as pd
import streamlit as st

from ..models import SimulationRun


def render_history_tab(runs: list[SimulationRun]) -> None:
    if not runs:
        st.info("Chưa có lịch sử mô phỏng.")
        return

    rows = [
        {
            "Run ID": run.run_id,
            "Timestamp": run.timestamp.isoformat(),
            "Processes": len(run.processes),
            "Avg Turnaround": round(run.avg_turnaround, 2),
            "Avg Waiting": round(run.avg_waiting, 2),
            "Avg Response": round(run.avg_response, 2),
            "Throughput": round(run.throughput, 4),
        }
        for run in runs
    ]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
