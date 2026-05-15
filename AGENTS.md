# AGENTS.md

Tài liệu này dành cho agent làm việc trong repo này. Mục tiêu là giữ cho repo luôn ở trạng thái có thể `clone -> setup -> run` ổn định trên máy khác.

## 1. Mục tiêu repo

- Repo này dùng để triển khai `CPU Scheduling Simulator` theo kiến trúc strategy-first.
- Ưu tiên hiện tại là bootstrap repo chặt chẽ, dependency reproducible, và local run ổn định.
- Entry point chính thức của ứng dụng là `app.py`.
- Package import chính thức là `mlfq_os_simulator`.
- Script chạy app chính thức cho người dùng là `scripts/run-project.ps1`.
- Script Docker chính thức cho người dùng là `scripts/build-docker-image.ps1` và `scripts/run-docker-image.ps1`.
- Kiến trúc phase hiện tại là strategy-first: `MLFQ`, `FCFS`, `Round Robin` đều phải conform cùng scheduler contract.
- Tab `Simulator` phải algo-agnostic: chọn thuật toán qua dropdown và resolve qua service/registry, không nối tắt vào UI.
- Tab `Comparison` phải có config riêng theo từng thuật toán; không phụ thuộc selected algorithm trong `Simulator`.
- Blueprint nguồn sự thật duy nhất là `docs/superpowers/2026-05-15-scheduling-platform-blueprint.md`.

## 2. Tooling bắt buộc

- Chỉ dùng Python `3.12`
- Dùng `uv` cho:
  - khởi tạo project
  - add/remove dependency
  - sync môi trường
  - chạy command trong môi trường project
- Global tooling chỉ gồm:
  - `uv`
  - Python `3.12`
  - `ruff`
  - `ty`

## 3. Những gì không được làm

- Không cài global `streamlit`, `pytest`, `pydantic`, `pandas`, `plotly`, `filelock`
- Không tự ý bỏ `uv.lock`
- Không đổi Python sang `3.13+` nếu chưa được yêu cầu rõ ràng
- Không dùng `pip install` trực tiếp nếu việc đó có thể làm bằng `uv`
- Không xóa hoặc phá flow `scripts/setup-python-tooling.ps1`
- Không xóa hoặc phá flow `scripts/run-project.ps1`
- Không xóa hoặc phá flow `scripts/build-docker-image.ps1`
- Không xóa hoặc phá flow `scripts/run-docker-image.ps1`

## 4. Cách quản lý dependency

- Runtime dependency phải nằm trong `pyproject.toml`
- Dev dependency phải nằm trong group `dev`
- Sau khi đổi dependency phải cập nhật `uv.lock`
- Khi sync, ưu tiên:

```powershell
uv sync --all-groups --frozen --python 3.12 --managed-python --link-mode copy
```

## 5. Cách kiểm tra môi trường

Sau mọi thay đổi ảnh hưởng tới tooling hoặc dependency, agent phải kiểm tra tối thiểu:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-python-tooling.ps1
```

Khi cần xác nhận app có thể chạy theo đúng flow bàn giao:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-project.ps1 -SkipSync
```

Khi cần xác nhận đường Docker:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-docker-image.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run-docker-image.ps1
```

Khi cần xác nhận runtime deps:

```powershell
uv run --python 3.12 python -c "import filelock, pandas, plotly, pydantic, streamlit; print('Project dependencies OK')"
```

Khi cần xác nhận dev tooling local:

```powershell
uv run --group dev --python 3.12 pytest --version
uv run --group dev --python 3.12 ruff --version
uv run --group dev --python 3.12 ty --version
```

Khi cần xác nhận behavior của ứng dụng, ưu tiên:

```powershell
uv run pytest tests -q
```

Khi cần xác nhận code quality đầy đủ trước khi kết thúc task, chạy theo thứ tự:

```powershell
uv sync --all-groups --frozen --python 3.12 --managed-python --link-mode copy
uv run --python 3.12 python -c "import filelock, pandas, plotly, pydantic, streamlit; print('Project dependencies OK')"
uv run ruff check .
uv run ty check src
uv run pytest tests -q
uv run streamlit run app.py --server.headless true
```

Khi cần xác nhận cả đường local script và Docker script:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-project.ps1 -SkipSync
powershell -ExecutionPolicy Bypass -File .\scripts\build-docker-image.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run-docker-image.ps1
```

## 6. Quy tắc chỉnh sửa repo

- Nếu cần thêm file bootstrap hoặc docs, giữ nội dung ngắn, thực dụng, và bám sát trạng thái thật của repo.
- Nếu app chưa tồn tại đầy đủ, phải ghi rõ là “bootstrap xong nhưng app chưa hoàn chỉnh”.
- Nếu sửa script setup, phải giữ tính idempotent: chạy lại nhiều lần vẫn an toàn.
- Không commit runtime artifacts sinh ra trong lúc chạy như `data/config.json`, `data/history.json`, `data/*.lock`, `data/*.tmp`.
- Dữ liệu demo nhanh trên UI là transient session data; repository chỉ quản lý config và history.
- Nếu cần chạy integration test mà không muốn đụng vào `data/` mặc định, dùng biến môi trường `MLFQ_DATA_DIR`.
- Nếu chỉnh Docker flow, phải giữ được khả năng mở app qua `http://localhost:<port>` từ host machine.
- Nếu thêm thuật toán mới, phải thêm package mới dưới `algorithms/`, export `STRATEGY`, và để registry auto-discovery nạp vào; không được sửa registry/UI/comparison bằng tay.
- Không được resurrect root-level legacy modules kiểu `scheduler.py`, `models.py`, `repository.py`, `metrics.py`, `config.py`.

## 7. Ưu tiên khi làm việc

Thứ tự ưu tiên:

1. Repo clone về setup được
2. Dependency lock nhất quán giữa các máy
3. Tooling đúng chuẩn Astral
4. Dev/test commands chạy ổn
5. Sau đó mới tới tối ưu hóa cấu trúc hoặc trải nghiệm phát triển

## 8. Trước khi kết thúc một task

Agent nên tự check:

- `pyproject.toml` còn đúng `requires-python = ">=3.12,<3.13"`
- `uv.lock` có được cập nhật nếu dependency thay đổi
- `.gitignore` vẫn bỏ qua `.venv`, cache, và JSON runtime
- `scripts/setup-python-tooling.ps1` vẫn chạy pass
- `uv run pytest tests -q` vẫn pass
- Không động vào thay đổi có sẵn của user nếu không được yêu cầu
