from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_app_boots_and_shows_empty_dashboard_when_no_run(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MLFQ_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MLFQ_ANIMATION_DELAY", "0")

    at = AppTest.from_file("app.py")
    at.run()

    assert len(at.title) == 1
    assert at.title[0].value == "CPU Scheduling Simulator"
    assert at.selectbox[0].value == "mlfq"
    assert any("Chưa có kết quả mô phỏng" in info.value for info in at.info)


def test_app_run_button_executes_simulation_and_persists_history(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("MLFQ_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MLFQ_ANIMATION_DELAY", "0")

    at = AppTest.from_file("app.py")
    at.run()
    at.button[1].click()
    at.run()

    assert len(at.exception) == 0
    assert any("Mô phỏng hoàn tất." in item.value for item in at.success)
    assert len(at.metric) == 4
    assert len(at.dataframe) >= 2
    assert (tmp_path / "data" / "history.json").exists()


def test_app_can_switch_algorithm_in_simulator(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MLFQ_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MLFQ_ANIMATION_DELAY", "0")

    at = AppTest.from_file("app.py")
    at.run()
    at.selectbox[0].set_value("round_robin")
    at.run()
    at.button[1].click()
    at.run()

    assert len(at.exception) == 0
    assert any("Mô phỏng hoàn tất." in item.value for item in at.success)
    assert any("Round Robin" in caption.value for caption in at.caption)


def test_app_comparison_tab_does_not_raise_duplicate_plotly_ids(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("MLFQ_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MLFQ_ANIMATION_DELAY", "0")

    at = AppTest.from_file("app.py")
    at.run()
    at.button[2].click()
    at.run()

    assert len(at.exception) == 0
    assert len(at.dataframe) >= 1
