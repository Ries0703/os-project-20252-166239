from __future__ import annotations

import streamlit as st

from ..application.services import SimulationService
from ..infrastructure.json_repository import JsonRepository
from ..shared.config import AppConfig
from .config_fields import render_config_fields


def render_sidebar(
    current_config: AppConfig,
    repository: JsonRepository,
    simulation_service: SimulationService,
    selected_algorithm: str,
) -> AppConfig:
    descriptor = simulation_service.describe_algorithm(selected_algorithm)

    st.sidebar.header("Cấu hình Scheduler")
    st.sidebar.caption(f"{descriptor.display_name}: {descriptor.description}")
    candidate = render_config_fields(
        st.sidebar,
        current_config,
        descriptor.config_fields,
        "sidebar_config",
    )
    if st.sidebar.button("Lưu cấu hình", key="save_config_button", width="stretch"):
        repository.save_config(candidate)
        st.session_state["config"] = candidate
        st.sidebar.success("Đã lưu cấu hình.")
        return candidate

    return current_config
