from __future__ import annotations

from typing import Any

from ..shared.config import AppConfig
from ..shared.contracts import AlgorithmConfigField


def render_config_fields(
    scope: Any,
    current_config: AppConfig,
    fields: tuple[AlgorithmConfigField, ...],
    key_prefix: str,
) -> AppConfig:
    def render_field(field: AlgorithmConfigField) -> int:
        current_value = current_config.get_int(field.key, field.default)
        widget_key = f"{key_prefix}_{field.key}"
        if field.widget == "slider":
            return int(
                scope.slider(
                    field.label,
                    min_value=field.min_value,
                    max_value=field.max_value or max(field.default, field.min_value),
                    value=current_value,
                    help=field.description or None,
                    key=widget_key,
                )
            )
        return int(
            scope.number_input(
                field.label,
                min_value=field.min_value,
                max_value=field.max_value,
                value=current_value,
                step=1,
                help=field.description or None,
                key=widget_key,
            )
        )

    updates = {field.key: render_field(field) for field in fields}
    return current_config.with_updates(updates)
