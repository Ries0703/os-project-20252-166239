from __future__ import annotations

from collections.abc import Sequence

import pandas as pd
import streamlit as st

from ..infrastructure.json_repository import JsonRepository
from ..shared.config import AppConfig
from ..shared.process import ProcessInput

DEFAULT_SIMULATOR_ALGORITHM = "mlfq"


def build_demo_process_rows() -> list[dict[str, int | str]]:
    return [
        {"pid": "P1", "arrival_time": 0, "burst_time": 9},
        {"pid": "P2", "arrival_time": 1, "burst_time": 4},
        {"pid": "P3", "arrival_time": 2, "burst_time": 7},
        {"pid": "P4", "arrival_time": 4, "burst_time": 3},
        {"pid": "P5", "arrival_time": 6, "burst_time": 5},
    ]


def _coerce_int(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if value.is_integer():
            return int(value)
        raise ValueError
    if isinstance(value, str):
        return int(value.strip())
    raise ValueError


def normalize_process_rows(
    rows: Sequence[dict[str, object]],
) -> tuple[list[ProcessInput], list[str]]:
    errors: list[str] = []
    normalized: list[ProcessInput] = []
    seen_pids: set[str] = set()

    for index, row in enumerate(rows, start=1):
        pid_raw = row.get("pid", "")
        pid = "" if pd.isna(pid_raw) else str(pid_raw).strip()
        arrival_raw = row.get("arrival_time", 0)
        burst_raw = row.get("burst_time", 0)

        if not pid:
            errors.append(f"Dòng {index}: PID không được để trống.")
            continue
        if pid in seen_pids:
            errors.append(f"Dòng {index}: PID `{pid}` bị trùng.")
            continue

        try:
            if pd.isna(arrival_raw) or pd.isna(burst_raw):
                raise ValueError
            arrival_time = _coerce_int(arrival_raw)
            burst_time = _coerce_int(burst_raw)
        except (TypeError, ValueError):
            errors.append(f"Dòng {index}: Arrival Time và Burst Time phải là số nguyên.")
            continue

        if arrival_time < 0:
            errors.append(f"Dòng {index}: Arrival Time phải >= 0.")
            continue
        if burst_time <= 0:
            errors.append(f"Dòng {index}: Burst Time phải > 0.")
            continue

        process = ProcessInput(pid=pid, arrival_time=arrival_time, burst_time=burst_time)
        normalized.append(process)
        seen_pids.add(pid)

    if not normalized:
        errors.append("Bảng process đang rỗng hoặc không có dòng hợp lệ.")

    return normalized, errors


def render_simulator_tab(
    config: AppConfig,
    repository: JsonRepository,
    simulation_service,
) -> object | None:
    st.subheader("Nhập dữ liệu process")

    algorithm_descriptors = simulation_service.available_algorithms()
    algorithm_options = {
        descriptor.key: descriptor for descriptor in algorithm_descriptors
    }
    if "selected_algorithm" not in st.session_state:
        st.session_state["selected_algorithm"] = DEFAULT_SIMULATOR_ALGORITHM
    if st.session_state["selected_algorithm"] not in algorithm_options:
        st.session_state["selected_algorithm"] = DEFAULT_SIMULATOR_ALGORITHM

    selected_algorithm = st.selectbox(
        "Algorithm",
        options=list(algorithm_options.keys()),
        index=list(algorithm_options.keys()).index(st.session_state["selected_algorithm"]),
        format_func=lambda key: algorithm_options[key].display_name,
        key="selected_algorithm",
    )
    selected_descriptor = algorithm_options[selected_algorithm]
    st.caption(
        f"Đang mô phỏng: {selected_descriptor.display_name} — {selected_descriptor.description}"
    )

    if "process_rows" not in st.session_state:
        st.session_state["process_rows"] = build_demo_process_rows()

    process_df = pd.DataFrame(st.session_state["process_rows"])
    edited_df = st.data_editor(
        process_df,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            "pid": st.column_config.TextColumn("PID", required=True),
            "arrival_time": st.column_config.NumberColumn(
                "Arrival Time",
                min_value=0,
                step=1,
                required=True,
            ),
            "burst_time": st.column_config.NumberColumn(
                "Burst Time",
                min_value=1,
                step=1,
                required=True,
            ),
        },
        key="process_editor",
    )
    st.session_state["process_rows"] = edited_df.to_dict("records")

    generated_col, run_col = st.columns(2)
    if generated_col.button("Auto Generate Data", key="generate_demo_button", width="stretch"):
        st.session_state["process_rows"] = build_demo_process_rows()
        st.rerun()

    if run_col.button(
        f"Run {selected_descriptor.display_name} Simulation",
        type="primary",
        key="run_simulation_button",
        width="stretch",
    ):
        process_rows = edited_df.to_dict("records")
        processes, errors = normalize_process_rows(process_rows)
        if errors:
            for error in errors:
                st.error(error)
            return None

        outcome = simulation_service.run_algorithm(selected_algorithm, processes, config)
        repository.save_run(outcome.result)
        return outcome

    return None
