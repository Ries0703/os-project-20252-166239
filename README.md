# CPU Scheduling Simulator

Repo này là nền tảng triển khai đồ án mô phỏng điều phối CPU theo kiến trúc strategy-first. `MLFQ` là thuật toán chính, đồng thời repo có `FCFS` và `Round Robin` để chạy so sánh trên cùng workload.

Nguyên tắc mở rộng hiện tại là **zero-touch algorithm extension**: thêm thuật toán mới phải chỉ cần thêm package mới trong `algorithms/` đúng contract, không sửa `app.py`, không sửa UI, không sửa registry thủ công.

## Clone -> Setup -> Run

### 1. Clone repo

```powershell
git clone <URL_REPO>
cd os-project-20252-166239
```

### 2. Chạy script setup một lần

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-python-tooling.ps1
```

Script này sẽ tự làm các việc sau:

- đảm bảo `uv` đã được cài
- đảm bảo Python `3.12`
- đảm bảo global tooling `ruff` và `ty`
- tạo `.venv`
- cài toàn bộ project dependency và dev dependency từ `uv.lock`
- kiểm tra lại import runtime package và công cụ dev trong môi trường local

### 3. Chạy ứng dụng bằng script

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-project.ps1
```

Script này sẽ:

- sync lại môi trường project bằng `uv sync --all-groups --frozen`
- chạy Streamlit app trên cổng mặc định `8501`
- in ra URL local để mở trên browser

### 4. Chạy ứng dụng bằng lệnh `uv` trực tiếp

Nếu muốn chạy tay thay vì dùng script:

```powershell
uv run streamlit run app.py
```

Nếu muốn chạy app với thư mục dữ liệu riêng để không chạm vào `data/` mặc định:

```powershell
$env:MLFQ_DATA_DIR = ".tmp-data"
uv run streamlit run app.py
```

## Docker

### Build image

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-docker-image.ps1
```

Mặc định image tag là:

```text
mlfq-os-simulator:local
```

### Run container

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-docker-image.ps1
```

Script này sẽ:

- kiểm tra image đã tồn tại
- xóa container cũ cùng tên nếu có
- chạy container detached
- publish cổng container `8501` ra `localhost`

### Run container với cổng hoặc thư mục data riêng

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-docker-image.ps1 -Port 8502 -HostDataDir ".docker-data"
```

## Trạng thái hiện tại của repo

- Đã có `pyproject.toml`
- Đã có `uv.lock`
- Đã pin `.python-version = 3.12`
- Đã có script setup one-shot
- Đã khóa global tooling và local dependency theo đúng contract
- Đã có ứng dụng Streamlit chạy end-to-end cho mô phỏng MLFQ
- Đã có strategy base cho `MLFQ`, `FCFS`, và `Round Robin`
- Đã có tab `Comparison` để so sánh nhiều thuật toán trên cùng workload
- Tab `Comparison` có config riêng theo từng thuật toán, không phụ thuộc thuật toán đang chọn ở `Simulator`
- Đã có unit test và integration test cho scheduler, registry, comparison service, helper UI, và flow app

## File quan trọng

- `scripts/setup-python-tooling.ps1`: script one-shot để dựng môi trường
- `scripts/run-project.ps1`: script one-shot để chạy ứng dụng
- `scripts/build-docker-image.ps1`: build Docker image
- `scripts/run-docker-image.ps1`: chạy Docker container ra `localhost`
- `pyproject.toml`: khai báo dependency của project
- `uv.lock`: lockfile để mọi máy cài đúng cùng một bộ package
- `.python-version`: pin Python `3.12`
- `src/mlfq_os_simulator/`: package chính của ứng dụng
- `src/mlfq_os_simulator/shared/`: shared contracts, neutral result models, metric helpers
- `src/mlfq_os_simulator/algorithms/`: concrete strategy implementations
- `src/mlfq_os_simulator/algorithms/mlfq/`: MLFQ engine và runtime models riêng
- `src/mlfq_os_simulator/application/`: app-level services và registry wiring
- `src/mlfq_os_simulator/infrastructure/`: persistence adapters
- `Dockerfile`: image định nghĩa runtime container
- `.dockerignore`: giới hạn context khi build image
- `docs/superpowers/2026-05-15-scheduling-platform-blueprint.md`: blueprint nguồn sự thật duy nhất cho kiến trúc và triển khai
- `docs/algorithm-extension-guide.md`: hướng dẫn dev khác thêm thuật toán
- `docs/comparison-analysis.md`: phần thảo luận các yếu tố ảnh hưởng hiệu năng MLFQ

## Lệnh thường dùng

### Đồng bộ lại môi trường

```powershell
uv sync --all-groups --frozen --python 3.12 --managed-python --link-mode copy
```

### Kiểm tra package runtime có cài đủ chưa

```powershell
uv run --python 3.12 python -c "import filelock, pandas, plotly, pydantic, streamlit; print('Project dependencies OK')"
```

### Kiểm tra tooling local của repo

```powershell
uv run --group dev --python 3.12 pytest --version
uv run --group dev --python 3.12 ruff --version
uv run --group dev --python 3.12 ty --version
```

### Chạy test suite

```powershell
uv run pytest tests -q
```

### Quy trình verify chuẩn

Khi cần kiểm tra repo theo đúng flow kỹ thuật đầy đủ, chạy theo thứ tự này:

```powershell
uv sync --all-groups --frozen --python 3.12 --managed-python --link-mode copy
uv run --python 3.12 python -c "import filelock, pandas, plotly, pydantic, streamlit; print('Project dependencies OK')"
uv run ruff check .
uv run ty check src
uv run pytest tests -q
uv run streamlit run app.py --server.headless true
```

Nếu cần verify Docker end-to-end:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-docker-image.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run-docker-image.ps1
```

### Chạy app bằng script với thư mục dữ liệu/cổng riêng

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run-project.ps1 -Port 8502 -DataDir ".tmp-data"
```

### Build và run Docker nhanh

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build-docker-image.ps1
powershell -ExecutionPolicy Bypass -File .\scripts\run-docker-image.ps1
```

### Chạy riêng unit test hoặc integration test

```powershell
uv run pytest tests/unit -q
uv run pytest tests/integration -q
```

## Quy ước môi trường

- Global machine tooling chỉ gồm:
  - `uv`
  - Python `3.12`
  - `ruff`
  - `ty`
- Thư viện ứng dụng và test **không** cài global
- Mọi dependency của repo phải đi qua `pyproject.toml` và `uv.lock`
- Khi máy khác pull repo về, ưu tiên chạy script setup thay vì cài tay
- Khi cần xác nhận behavior, ưu tiên chạy test suite thay vì bấm tay trên app
- Dữ liệu demo nhanh cho UI là dữ liệu transient trong lớp UI/session, không đi qua repository
- Đường local và đường Docker là hai flow độc lập; script local không phụ thuộc Docker
- UI không gọi trực tiếp implementation của thuật toán; comparison và simulator đi qua application service/registry
- Root modules kiểu `scheduler.py`, `models.py`, `repository.py`, `config.py`, `metrics.py` không còn là canonical entrypoint sau hard-cut refactor

## Khi bàn giao cho máy khác

Checklist tối thiểu:

1. `git clone` repo
2. chạy `.\scripts\setup-python-tooling.ps1`
3. xác nhận script báo `Setup complete`
4. chạy `uv run pytest tests -q`
5. chạy `.\scripts\run-project.ps1`

Nếu bàn giao theo đường Docker:

1. `git clone` repo
2. chạy `.\scripts\build-docker-image.ps1`
3. chạy `.\scripts\run-docker-image.ps1`
4. mở `http://localhost:8501`

## Ghi chú

- Entry point chính thức của ứng dụng là `app.py`.
- Package import chính thức là `mlfq_os_simulator`.
- Thư mục `data/` được commit với baseline tối thiểu của app.
- `data/config.json` và `data/history.json` là runtime artifacts local, do app tự tạo lại nếu thiếu.
- Không commit `data/config.json`, `data/history.json`, `*.lock`, hoặc `*.tmp` trong `data/`.
- `Comparison` tab hiện so sánh `MLFQ`, `FCFS`, và `Round Robin`.
- `Comparison` dùng config snapshot riêng cho từng thuật toán trong session state; không reuse sidebar config của `Simulator` một cách ngầm nữa.
- Nếu PowerShell hiện warning từ `PSReadLine`, có thể bỏ qua nếu script vẫn kết thúc thành công.
