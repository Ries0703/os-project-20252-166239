from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from mlfq_os_simulator.config import AppConfig
from mlfq_os_simulator.models import ProcessState, SimulationRun
from mlfq_os_simulator.repository import JsonRepository


def _build_run(run_id: str = "run-1") -> SimulationRun:
    process = ProcessState(
        pid="P1",
        arrival_time=0,
        burst_time=1,
        input_order=0,
        remaining_time=0,
        current_queue=0,
        quantum_used=0,
        start_time=0,
        completion_time=1,
    )
    return SimulationRun(
        run_id=run_id,
        timestamp=datetime.now(UTC),
        config_used=AppConfig(),
        processes=[process],
        gantt_log=[],
        throughput=1.0,
        avg_turnaround=1.0,
        avg_waiting=0.0,
        avg_response=0.0,
    )


def test_load_config_creates_default_when_missing(temp_data_dir: Path) -> None:
    repository = JsonRepository(temp_data_dir)

    config = repository.load_config()

    assert config == AppConfig()
    assert repository.config_path.exists()


def test_history_is_pruned_to_twenty_entries(temp_data_dir: Path) -> None:
    repository = JsonRepository(temp_data_dir)

    for index in range(25):
        repository.save_run(_build_run(run_id=f"run-{index}"))

    runs = repository.get_all_runs()

    assert len(runs) == 20
    assert runs[0].run_id == "run-5"
    assert runs[-1].run_id == "run-24"


def test_corrupt_config_falls_back_to_default(temp_data_dir: Path) -> None:
    repository = JsonRepository(temp_data_dir)
    temp_data_dir.mkdir(parents=True, exist_ok=True)
    repository.config_path.write_text("{bad json", encoding="utf-8")

    config = repository.load_config()

    assert config == AppConfig()
    warnings = repository.consume_warnings()
    assert warnings


def test_corrupt_history_falls_back_to_empty(temp_data_dir: Path) -> None:
    repository = JsonRepository(temp_data_dir)
    temp_data_dir.mkdir(parents=True, exist_ok=True)
    repository.history_path.write_text("{bad json", encoding="utf-8")

    runs = repository.get_all_runs()

    assert runs == []
    warnings = repository.consume_warnings()
    assert warnings


def test_save_config_writes_json_document(temp_data_dir: Path) -> None:
    repository = JsonRepository(temp_data_dir)
    config = AppConfig(
        quantum_q0=2,
        quantum_q1=3,
        quantum_q2=5,
        aging_boost_interval=10,
        context_switch_time=0,
    )

    repository.save_config(config)

    data = json.loads(repository.config_path.read_text(encoding="utf-8"))
    assert data["quantum_q0"] == 2
