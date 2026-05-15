from __future__ import annotations

from mlfq_os_simulator.shared.config import CORE_DEFAULTS, AppConfig


def test_app_config_accepts_dynamic_algorithm_fields() -> None:
    config = AppConfig(context_switch_time=0, my_custom_quantum=7)

    assert config.context_switch_time == 0
    assert config.get_int("my_custom_quantum", 3) == 7


def test_app_config_serializes_flat_document() -> None:
    config = AppConfig(values={"custom_field": 9})

    payload = config.model_dump(mode="json")

    assert payload["schema_version"] >= 2
    assert payload["quantum_q0"] == CORE_DEFAULTS["quantum_q0"]
    assert payload["custom_field"] == 9
