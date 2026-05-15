from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from mlfq_os_simulator.repository import JsonRepository
from mlfq_os_simulator.ui.animation import render_simulation_animation
from mlfq_os_simulator.ui.dashboard_tab import render_dashboard_tab
from mlfq_os_simulator.ui.history_tab import render_history_tab
from mlfq_os_simulator.ui.sidebar import render_sidebar
from mlfq_os_simulator.ui.simulator_tab import render_simulator_tab

APP_ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("MLFQ_DATA_DIR", APP_ROOT / "data"))


def _flush_repository_warnings(repository: JsonRepository) -> None:
    for warning in repository.consume_warnings():
        st.warning(warning)


def main() -> None:
    st.set_page_config(page_title="MLFQ OS Simulator", page_icon="CPU", layout="wide")
    repository = JsonRepository(DATA_DIR)

    if "config" not in st.session_state:
        st.session_state["config"] = repository.load_config()
    _flush_repository_warnings(repository)

    st.title("MLFQ OS Simulator")
    st.caption("Mô phỏng thuật toán Multi-Level Feedback Queue theo đúng một mode duy nhất.")

    st.session_state["config"] = render_sidebar(st.session_state["config"], repository)
    _flush_repository_warnings(repository)

    simulator_tab, dashboard_tab, history_tab = st.tabs(["Simulator", "Dashboard", "History"])

    with simulator_tab:
        outcome = render_simulator_tab(st.session_state["config"], repository)
        if outcome is not None:
            render_simulation_animation(outcome.frames)
            st.session_state["current_run"] = outcome.run
            st.session_state["current_trace"] = outcome.frames
            _flush_repository_warnings(repository)
            st.success("Mô phỏng hoàn tất.")

    with dashboard_tab:
        render_dashboard_tab(st.session_state.get("current_run"))

    with history_tab:
        runs = repository.get_all_runs()
        _flush_repository_warnings(repository)
        render_history_tab(runs)


if __name__ == "__main__":
    main()
