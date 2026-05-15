from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = 1


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(default=SCHEMA_VERSION)
    quantum_q0: int = Field(default=4, gt=0)
    quantum_q1: int = Field(default=8, gt=0)
    quantum_q2: int = Field(default=16, gt=0)
    aging_boost_interval: int = Field(default=50, gt=0)
    context_switch_time: int = Field(default=1, ge=0)


def default_config() -> AppConfig:
    return AppConfig()
