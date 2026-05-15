from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from mlfq_os_simulator.application.services import (
    SimulationService,
    build_comparison_service,
    build_scheduler_registry,
)
from mlfq_os_simulator.infrastructure.json_repository import JsonRepository
from mlfq_os_simulator.ui.animation import render_simulation_animation
from mlfq_os_simulator.ui.comparison_tab import render_comparison_tab
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
    st.set_page_config(page_title="CPU Scheduling Simulator", page_icon="CPU", layout="wide")
    repository = JsonRepository(DATA_DIR)
    registry = build_scheduler_registry()
    simulation_service = SimulationService(registry)
    comparison_service = build_comparison_service(registry)
    default_algorithm_key = simulation_service.default_algorithm_key()

    if "config" not in st.session_state:
        st.session_state["config"] = repository.load_config()
    if "selected_algorithm" not in st.session_state:
        st.session_state["selected_algorithm"] = default_algorithm_key
    available_algorithm_keys = {
        item.key for item in simulation_service.available_algorithms()
    }
    if st.session_state["selected_algorithm"] not in available_algorithm_keys:
        st.session_state["selected_algorithm"] = default_algorithm_key
    _flush_repository_warnings(repository)

    st.title("CPU Scheduling Simulator")
    st.caption("Mô phỏng MLFQ, FCFS và Round Robin trên cùng một nền strategy-first.")

    st.session_state["config"] = render_sidebar(
        st.session_state["config"],
        repository,
        simulation_service,
        st.session_state["selected_algorithm"],
    )
    _flush_repository_warnings(repository)

    simulator_tab, dashboard_tab, history_tab, comparison_tab = st.tabs(
        ["Simulator", "Dashboard", "History", "Comparison"]
    )

    with simulator_tab:
        outcome = render_simulator_tab(st.session_state["config"], repository, simulation_service)
        if outcome is not None:
            render_simulation_animation(outcome.frames)
            st.session_state["current_run"] = outcome.result
            st.session_state["current_trace"] = outcome.frames
            _flush_repository_warnings(repository)
            st.success("Mô phỏng hoàn tất.")

    with dashboard_tab:
        render_dashboard_tab(st.session_state.get("current_run"))

    with history_tab:
        runs = repository.get_all_runs()
        _flush_repository_warnings(repository)
        render_history_tab(runs)

    with comparison_tab:
        render_comparison_tab(comparison_service, st.session_state["config"])


if __name__ == "__main__":
    main()
