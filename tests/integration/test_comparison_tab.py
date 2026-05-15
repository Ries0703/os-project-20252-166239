from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_comparison_tab_renders_results(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MLFQ_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("MLFQ_ANIMATION_DELAY", "0")

    at = AppTest.from_file("app.py")
    at.run()
    at.button[2].click()
    at.run()

    assert len(at.exception) == 0
    assert len(at.dataframe) >= 1
