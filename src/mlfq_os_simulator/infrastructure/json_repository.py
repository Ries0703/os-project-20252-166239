from __future__ import annotations

import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from filelock import FileLock
from pydantic import TypeAdapter, ValidationError

from ..shared.config import AppConfig, default_config
from ..shared.results import AlgorithmRunResult


class JsonRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.config_path = data_dir / "config.json"
        self.history_path = data_dir / "history.json"
        self._warnings: list[str] = []

    def load_config(self) -> AppConfig:
        default = default_config()
        if not self.config_path.exists():
            self.save_config(default)
            return default

        recovered = False
        with self._lock_for(self.config_path):
            try:
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                return AppConfig.model_validate(data)
            except (OSError, json.JSONDecodeError, ValidationError):
                recovered = True

        if recovered:
            self._warnings.append("`config.json` bị lỗi và đã được khôi phục về cấu hình mặc định.")
            self.save_config(default)
        return default

    def save_config(self, config: AppConfig) -> None:
        self._write_json(self.config_path, config.model_dump(mode="json"))

    def get_all_runs(self) -> list[AlgorithmRunResult]:
        if not self.history_path.exists():
            self._write_json(self.history_path, [])
            return []

        adapter = TypeAdapter(list[AlgorithmRunResult])
        recovered = False
        with self._lock_for(self.history_path):
            try:
                data = json.loads(self.history_path.read_text(encoding="utf-8"))
                return adapter.validate_python(data)
            except (OSError, json.JSONDecodeError, ValidationError):
                recovered = True

        if recovered:
            self._warnings.append("`history.json` bị lỗi và đã được khôi phục về lịch sử rỗng.")
            self._write_json(self.history_path, [])
        return []

    def save_run(self, run: AlgorithmRunResult) -> None:
        runs = self.get_all_runs()
        runs.append(run)
        payload = [item.model_dump(mode="json") for item in runs[-20:]]
        self._write_json(self.history_path, payload)

    def consume_warnings(self) -> list[str]:
        warnings = self._warnings[:]
        self._warnings.clear()
        return warnings

    def _lock_for(self, path: Path) -> FileLock:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return FileLock(str(path.with_suffix(path.suffix + ".lock")))

    def _write_json(self, path: Path, payload: Any) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        lock = self._lock_for(path)
        with lock:
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.data_dir,
                delete=False,
                suffix=".tmp",
            ) as temp_file:
                json.dump(payload, temp_file, ensure_ascii=False, indent=2)
                temp_path = Path(temp_file.name)
            temp_path.replace(path)
