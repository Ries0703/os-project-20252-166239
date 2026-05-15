from __future__ import annotations

from collections.abc import Sequence
from statistics import mean

import pandas as pd
import plotly.graph_objects as go

from .models import GanttLogEntry, ProcessState

COLOR_MAP = {
    "Q0": "#ef4444",
    "Q1": "#f59e0b",
    "Q2": "#22c55e",
    "N/A": "#6b7280",
}


def calculate_run_metrics(processes: Sequence[ProcessState]) -> dict[str, float]:
    if not processes:
        return {
            "avg_turnaround": 0.0,
            "avg_waiting": 0.0,
            "avg_response": 0.0,
            "throughput": 0.0,
        }

    makespan = max(process.completion_time or 0 for process in processes)
    throughput = len(processes) / makespan if makespan > 0 else 0.0

    return {
        "avg_turnaround": float(mean(process.turnaround_time for process in processes)),
        "avg_waiting": float(mean(process.waiting_time for process in processes)),
        "avg_response": float(mean(process.response_time for process in processes)),
        "throughput": float(throughput),
    }


def gantt_to_dataframe(entries: Sequence[GanttLogEntry]) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame(columns=["Task", "Start", "Finish", "Queue"])
    return pd.DataFrame([entry.model_dump(mode="json") for entry in entries])


def build_gantt_figure(entries: Sequence[GanttLogEntry]) -> go.Figure:
    figure = go.Figure()
    dataframe = gantt_to_dataframe(entries)

    if dataframe.empty:
        figure.update_layout(
            xaxis_title="Time",
            yaxis_title="Task",
            showlegend=False,
            margin=dict(l=24, r=24, t=24, b=24),
        )
        return figure

    dataframe["Duration"] = dataframe["Finish"] - dataframe["Start"]
    present_queues = set(dataframe["Queue"].unique())
    queue_order = [queue for queue in ("Q0", "Q1", "Q2", "N/A") if queue in present_queues]

    for queue_name in queue_order:
        queue_rows = dataframe[dataframe["Queue"] == queue_name]
        figure.add_trace(
            go.Bar(
                name=queue_name,
                x=queue_rows["Duration"],
                y=queue_rows["Task"],
                base=queue_rows["Start"],
                orientation="h",
                marker_color=COLOR_MAP.get(queue_name, "#6b7280"),
                customdata=queue_rows[["Start", "Finish"]],
                hovertemplate=(
                    "Task=%{y}<br>"
                    "Queue=" + queue_name + "<br>"
                    "Start=%{customdata[0]}<br>"
                    "Finish=%{customdata[1]}<extra></extra>"
                ),
            )
        )

    max_finish = int(dataframe["Finish"].max())
    tick_step = max(1, max_finish // 10)

    figure.update_layout(
        barmode="overlay",
        xaxis_title="Time",
        yaxis_title="Task",
        bargap=0.35,
        margin=dict(l=24, r=24, t=24, b=24),
        legend_title_text="Queue",
    )
    figure.update_xaxes(range=[0, max_finish + 1], dtick=tick_step)
    figure.update_yaxes(autorange="reversed")
    return figure
