from __future__ import annotations

import sys
from pathlib import Path

import pytest

from mlfq_os_simulator.config import AppConfig

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@pytest.fixture()
def default_config() -> AppConfig:
    return AppConfig(
        quantum_q0=4,
        quantum_q1=8,
        quantum_q2=16,
        aging_boost_interval=50,
        context_switch_time=1,
    )


@pytest.fixture()
def temp_data_dir(tmp_path: Path) -> Path:
    return tmp_path / "data"
