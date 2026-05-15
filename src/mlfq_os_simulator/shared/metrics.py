from __future__ import annotations

from collections.abc import Sequence
from statistics import mean

import pandas as pd
import plotly.graph_objects as go

from .results import AlgorithmGanttEntry, AlgorithmProcessResult

COLOR_MAP = {
    "Q0": "#ef4444",
    "Q1": "#f59e0b",
    "Q2": "#22c55e",
    "N/A": "#6b7280",
    "CPU": "#4b5563",
    "Ready": "#2563eb",
    "Running": "#7c3aed",
    "Completed": "#10b981",
    "Main": "#6b7280",
}


def algorithm_gantt_to_dataframe(entries: Sequence[AlgorithmGanttEntry]) -> pd.DataFrame:
    if not entries:
        return pd.DataFrame(columns=["Task", "Start", "Finish", "Lane"])
    return pd.DataFrame([entry.model_dump(mode="json") for entry in entries])


def gantt_to_dataframe(entries: Sequence[AlgorithmGanttEntry]) -> pd.DataFrame:
    return algorithm_gantt_to_dataframe(entries)


def build_algorithm_gantt_figure(entries: Sequence[AlgorithmGanttEntry]) -> go.Figure:
    dataframe = algorithm_gantt_to_dataframe(entries)
    lane_order = (
        tuple(dict.fromkeys(dataframe["Lane"].tolist()))
        if not dataframe.empty
        else ("Main",)
    )
    return _build_timeline_figure(dataframe, lane_order=lane_order)


def build_gantt_figure(entries: Sequence[AlgorithmGanttEntry]) -> go.Figure:
    return build_algorithm_gantt_figure(entries)


def _build_timeline_figure(
    dataframe: pd.DataFrame,
    lane_order: Sequence[str],
) -> go.Figure:
    figure = go.Figure()

    if dataframe.empty:
        figure.update_layout(
            xaxis_title="Time",
            yaxis_title="Task",
            showlegend=False,
            margin=dict(l=24, r=24, t=24, b=24),
        )
        return figure

    dataframe["Duration"] = dataframe["Finish"] - dataframe["Start"]
    present_lanes = set(dataframe["Lane"].unique())
    ordered_lanes = [lane for lane in lane_order if lane in present_lanes]

    for lane_name in ordered_lanes:
        lane_rows = dataframe[dataframe["Lane"] == lane_name]
        figure.add_trace(
            go.Bar(
                name=lane_name,
                x=lane_rows["Duration"],
                y=lane_rows["Task"],
                base=lane_rows["Start"],
                orientation="h",
                marker_color=COLOR_MAP.get(lane_name, "#6b7280"),
                customdata=lane_rows[["Start", "Finish"]],
                hovertemplate=(
                    "Task=%{y}<br>"
                    "Lane=" + lane_name + "<br>"
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
        legend_title_text="Lane",
    )
    figure.update_xaxes(range=[0, max_finish + 1], dtick=tick_step)
    figure.update_yaxes(autorange="reversed")
    return figure


def calculate_algorithm_metrics(
    processes: Sequence[AlgorithmProcessResult],
) -> dict[str, float]:
    if not processes:
        return {
            "avg_turnaround": 0.0,
            "avg_waiting": 0.0,
            "avg_response": 0.0,
            "throughput": 0.0,
            "makespan": 0.0,
        }

    makespan = max(process.completion_time for process in processes)
    throughput = len(processes) / makespan if makespan > 0 else 0.0

    return {
        "avg_turnaround": float(mean(process.turnaround_time for process in processes)),
        "avg_waiting": float(mean(process.waiting_time for process in processes)),
        "avg_response": float(mean(process.response_time for process in processes)),
        "throughput": float(throughput),
        "makespan": float(makespan),
    }
