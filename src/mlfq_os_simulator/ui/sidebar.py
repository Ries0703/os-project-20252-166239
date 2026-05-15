from __future__ import annotations

import streamlit as st

from ..application.services import SimulationService
from ..infrastructure.json_repository import JsonRepository
from ..shared.config import AppConfig
from ..shared.contracts import AlgorithmConfigField


def render_sidebar(
    current_config: AppConfig,
    repository: JsonRepository,
    simulation_service: SimulationService,
    selected_algorithm: str,
) -> AppConfig:
    descriptor = simulation_service.describe_algorithm(selected_algorithm)

    st.sidebar.header("Cấu hình Scheduler")
    st.sidebar.caption(f"{descriptor.display_name}: {descriptor.description}")

    def render_field(field: AlgorithmConfigField) -> int:
        current_value = current_config.get_int(field.key, field.default)
        if field.widget == "slider":
            return int(
                st.sidebar.slider(
                    field.label,
                    min_value=field.min_value,
                    max_value=field.max_value or max(field.default, field.min_value),
                    value=current_value,
                    help=field.description or None,
                )
            )
        return int(
            st.sidebar.number_input(
                field.label,
                min_value=field.min_value,
                max_value=field.max_value,
                value=current_value,
                step=1,
                help=field.description or None,
            )
        )

    updates = {field.key: render_field(field) for field in descriptor.config_fields}
    candidate = current_config.with_updates(updates)
    if st.sidebar.button("Lưu cấu hình", key="save_config_button", width="stretch"):
        repository.save_config(candidate)
        st.session_state["config"] = candidate
        st.sidebar.success("Đã lưu cấu hình.")
        return candidate

    return current_config
