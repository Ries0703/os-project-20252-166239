from __future__ import annotations

import pandas as pd

from mlfq_os_simulator.metrics import build_gantt_figure, gantt_to_dataframe
from mlfq_os_simulator.models import GanttLogEntry
from mlfq_os_simulator.ui.simulator_tab import build_demo_process_rows, normalize_process_rows


def test_normalize_process_rows_accepts_valid_rows() -> None:
    rows = [
        {"pid": "P1", "arrival_time": 0, "burst_time": 3},
        {"pid": "P2", "arrival_time": 1.0, "burst_time": "4"},
    ]

    processes, errors = normalize_process_rows(rows)

    assert errors == []
    assert [process.pid for process in processes] == ["P1", "P2"]
    assert processes[1].burst_time == 4


def test_normalize_process_rows_reports_validation_errors() -> None:
    rows = [
        {"pid": "", "arrival_time": 0, "burst_time": 3},
        {"pid": "P1", "arrival_time": -1, "burst_time": 3},
        {"pid": "P1", "arrival_time": 0, "burst_time": 0},
    ]

    _, errors = normalize_process_rows(rows)

    assert any("PID không được để trống" in error for error in errors)
    assert any("Arrival Time phải >= 0" in error for error in errors)


def test_normalize_process_rows_rejects_empty_table() -> None:
    _, errors = normalize_process_rows([])

    assert errors == ["Bảng process đang rỗng hoặc không có dòng hợp lệ."]


def test_gantt_to_dataframe_builds_expected_columns() -> None:
    dataframe = gantt_to_dataframe(
        [
            GanttLogEntry(Task="P1", Start=0, Finish=2, Queue="Q0"),
            GanttLogEntry(Task="Idle", Start=2, Finish=3, Queue="N/A"),
        ]
    )

    assert isinstance(dataframe, pd.DataFrame)
    assert list(dataframe.columns) == ["Task", "Start", "Finish", "Queue"]
    assert dataframe.iloc[0]["Task"] == "P1"


def test_build_demo_process_rows_returns_reasonable_demo_data() -> None:
    rows = build_demo_process_rows()

    assert len(rows) == 5
    assert rows[0]["arrival_time"] == 0
    assert all(int(row["burst_time"]) > 0 for row in rows)


def test_build_gantt_figure_uses_numeric_time_axis() -> None:
    figure = build_gantt_figure(
        [
            GanttLogEntry(Task="P1", Start=0, Finish=4, Queue="Q0"),
            GanttLogEntry(Task="P2", Start=4, Finish=6, Queue="Q1"),
        ]
    )

    assert len(figure.data) == 2
    assert figure.layout.xaxis.range[0] == 0
    assert figure.data[0]["base"][0] == 0
    assert figure.data[0]["x"][0] == 4
