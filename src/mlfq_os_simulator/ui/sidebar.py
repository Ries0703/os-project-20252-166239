from __future__ import annotations

import streamlit as st

from ..config import AppConfig
from ..repository import JsonRepository


def render_sidebar(current_config: AppConfig, repository: JsonRepository) -> AppConfig:
    st.sidebar.header("Cấu hình MLFQ")
    candidate = AppConfig(
        quantum_q0=st.sidebar.number_input(
            "Q0 Quantum",
            min_value=1,
            value=current_config.quantum_q0,
            step=1,
        ),
        quantum_q1=st.sidebar.number_input(
            "Q1 Quantum",
            min_value=1,
            value=current_config.quantum_q1,
            step=1,
        ),
        quantum_q2=st.sidebar.number_input(
            "Q2 Quantum",
            min_value=1,
            value=current_config.quantum_q2,
            step=1,
        ),
        aging_boost_interval=st.sidebar.slider(
            "Aging Boost Interval",
            min_value=1,
            max_value=200,
            value=current_config.aging_boost_interval,
        ),
        context_switch_time=st.sidebar.number_input(
            "Context Switch Time",
            min_value=0,
            max_value=20,
            value=current_config.context_switch_time,
            step=1,
        ),
    )

    if st.sidebar.button("Lưu cấu hình", width="stretch"):
        repository.save_config(candidate)
        st.session_state["config"] = candidate
        st.sidebar.success("Đã lưu cấu hình.")
        return candidate

    return current_config
