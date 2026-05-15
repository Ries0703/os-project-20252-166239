from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator

SCHEMA_VERSION = 2
CORE_DEFAULTS: dict[str, int] = {
    "quantum_q0": 4,
    "quantum_q1": 8,
    "quantum_q2": 16,
    "round_robin_quantum": 4,
    "aging_boost_interval": 50,
    "context_switch_time": 1,
}


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=SCHEMA_VERSION)
    values: dict[str, int] = Field(default_factory=lambda: dict(CORE_DEFAULTS))

    @model_validator(mode="before")
    @classmethod
    def _normalize_input(cls, data: object) -> object:
        if isinstance(data, cls):
            return {
                "schema_version": data.schema_version,
                "values": dict(data.values),
            }
        if not isinstance(data, dict):
            return data

        raw = dict(data)
        schema_version = int(raw.pop("schema_version", SCHEMA_VERSION))
        merged_values: dict[str, int] = dict(CORE_DEFAULTS)

        raw_values = raw.pop("values", {})
        if isinstance(raw_values, dict):
            for key, value in raw_values.items():
                merged_values[str(key)] = int(value)

        for key, value in raw.items():
            merged_values[str(key)] = int(value)

        return {
            "schema_version": schema_version,
            "values": merged_values,
        }

    @model_serializer(mode="plain")
    def _serialize(self) -> dict[str, int]:
        return {
            "schema_version": self.schema_version,
            **CORE_DEFAULTS,
            **self.values,
        }

    def get_int(self, key: str, default: int) -> int:
        return int(self.values.get(key, CORE_DEFAULTS.get(key, default)))

    def with_updates(self, updates: dict[str, int]) -> AppConfig:
        merged = dict(self.values)
        merged.update({key: int(value) for key, value in updates.items()})
        return AppConfig(schema_version=self.schema_version, values=merged)

    @property
    def quantum_q0(self) -> int:
        return self.get_int("quantum_q0", CORE_DEFAULTS["quantum_q0"])

    @property
    def quantum_q1(self) -> int:
        return self.get_int("quantum_q1", CORE_DEFAULTS["quantum_q1"])

    @property
    def quantum_q2(self) -> int:
        return self.get_int("quantum_q2", CORE_DEFAULTS["quantum_q2"])

    @property
    def round_robin_quantum(self) -> int:
        return self.get_int("round_robin_quantum", CORE_DEFAULTS["round_robin_quantum"])

    @property
    def aging_boost_interval(self) -> int:
        return self.get_int("aging_boost_interval", CORE_DEFAULTS["aging_boost_interval"])

    @property
    def context_switch_time(self) -> int:
        return self.get_int("context_switch_time", CORE_DEFAULTS["context_switch_time"])


def default_config() -> AppConfig:
    return AppConfig(values=dict(CORE_DEFAULTS))
