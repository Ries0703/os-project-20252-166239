from __future__ import annotations

from mlfq_os_simulator.algorithms.mlfq.strategy import MLFQStrategy
from mlfq_os_simulator.shared.config import AppConfig
from mlfq_os_simulator.shared.process import ProcessInput


def test_mlfq_strategy_conforms_to_contract() -> None:
    strategy = MLFQStrategy()
    result = strategy.simulate([ProcessInput(pid="P1", arrival_time=0, burst_time=3)], AppConfig())

    assert strategy.key == "mlfq"
    assert result.result.algorithm_key == "mlfq"
    assert result.result.process_count == 1
    assert result.frames
