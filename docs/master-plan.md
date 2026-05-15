# 🚀 Blueprint Thực Thi: MLFQ OS Simulator (Production-Grade)

> Trạng thái hiện tại: tài liệu này là blueprint lịch sử để tham khảo. Nguồn sự thật kỹ thuật hiện tại là `docs/superpowers/2026-05-15-scheduling-platform-blueprint.md`.

Tài liệu này không còn là bản nháp (draft) ý tưởng. Đây là **Bản Đặc Tả Thực Thi (Execution Blueprint)**. Mọi lớp (class), kiểu dữ liệu (typing), logic rẽ nhánh, và thành phần giao diện (UI components) đều được định nghĩa chính xác ở mức mã nguồn. Developer có thể nhìn vào đây để gõ code line-by-line.

---

## 1. 🧬 Đặc Tả Thực Thể & Validation (Entity & Typing Specifications)

Sử dụng `pydantic` v2 để định nghĩa Type chặt chẽ và Validate dữ liệu ở mức hệ thống.

### 1.1. Thực thể Cấu hình (`core/config.py`)
```python
from pydantic import BaseModel, Field

class AppConfig(BaseModel):
    quantum_q0: int = Field(default=4, gt=0, description="Quantum time for Queue 0")
    quantum_q1: int = Field(default=8, gt=0, description="Quantum time for Queue 1")
    quantum_q2: int = Field(default=16, gt=0, description="Quantum time for Queue 2")
    aging_boost_interval: int = Field(default=50, gt=0, description="Time to boost all to Q0")
    context_switch_time: int = Field(default=1, ge=0, description="Overhead per switch")
```

### 1.2. Thực thể Tiến trình Đầu vào (`core/models.py`)
Được dùng khi User nhập data trên giao diện.
```python
from pydantic import BaseModel, Field

class ProcessInput(BaseModel):
    pid: str = Field(..., min_length=1, description="Process ID (e.g., P1)")
    arrival_time: int = Field(..., ge=0, description="Must be >= 0")
    burst_time: int = Field(..., gt=0, description="Must be > 0")
```

### 1.3. Thực thể Trạng thái Tiến trình (`core/models.py`)
Được dùng trong nội bộ thuật toán `MLFQScheduler`. Kế thừa từ `ProcessInput`.
```python
from typing import Optional

class ProcessState(ProcessInput):
    remaining_time: int
    current_queue: int = Field(default=0, ge=0, le=2)
    start_time: int = Field(default=-1)
    completion_time: int = Field(default=0)
    
    # Tính toán Metrics
    @property
    def turnaround_time(self) -> int:
        return self.completion_time - self.arrival_time
        
    @property
    def waiting_time(self) -> int:
        return self.turnaround_time - self.burst_time
        
    @property
    def response_time(self) -> int:
        return self.start_time - self.arrival_time
```

### 1.4. Thực thể Log (Gantt Chart & Database)
Định nghĩa cấu trúc chính xác để vẽ biểu đồ và lưu file JSON.
```python
from typing import List, Literal

class GanttLogEntry(BaseModel):
    Task: str                    # PID hoặc "Idle" hoặc "CS Overhead"
    Start: int                   # Timestamp bắt đầu
    Finish: int                  # Timestamp kết thúc
    Queue: str                   # "Q0", "Q1", "Q2", "N/A"
    ColorCode: Literal["Red", "Yellow", "Green", "Gray"]

class SimulationRun(BaseModel):
    run_id: str
    timestamp: str               # ISO 8601 format
    config_used: AppConfig       # Snapshot cấu hình lúc chạy
    processes: List[ProcessState]
    gantt_log: List[GanttLogEntry]
    system_throughput: float
    avg_turnaround: float
    avg_waiting: float
```

---

## 2. 🧠 Đặc Tả Logic Cốt Lõi (Core Logic Specifications)

File: `features/1_mlfq_engine/service.py`. Lớp `MLFQScheduler`.

**Input:** `List[ProcessInput]`, `AppConfig`
**Output:** `SimulationRun`

### 2.1. Cấu trúc State Nội Bộ
```python
queues: dict[int, list[ProcessState]] = {0: [], 1: [], 2: []}
time_current: int = 0
running_proc: Optional[ProcessState] = None
current_q_time_spent: int = 0
cs_cooldown: int = 0  # Đếm ngược thời gian Context Switch
gantt_logs: list[GanttLogEntry] = []
completed_procs: list[ProcessState] = []
```

### 2.2. Vòng Lặp Chính (Time-Stepping) & Thứ tự Thực thi Tuyệt Đối
Lặp `while len(completed_procs) < len(input_processes):`. Tại mỗi `time_current` (tick), phải thực thi CHÍNH XÁC theo thứ tự sau:

**Bước 1: Circuit Breaker Check**
*   Nếu `time_current > 100_000`, `raise TimeoutError("Infinite loop detected")`.

**Bước 2: Xử lý Process Mới Đến (Arrival)**
*   Tìm tất cả Process có `arrival_time == time_current`.
*   Tạo object `ProcessState`, gán `remaining_time = burst_time`.
*   Đẩy vào mảng `queues[0]`. (Tie-breaker: Sắp xếp theo thứ tự nhập liệu gốc nếu trùng Arrival).

**Bước 3: Xử lý Aging (Priority Boost)**
*   Nếu `time_current > 0` VÀ `time_current % config.aging_boost_interval == 0`:
    *   Lấy tất cả process trong `queues[1]` và `queues[2]` dồn hết vào đuôi `queues[0]`.
    *   Set `current_queue = 0` cho tất cả các process đó.
    *   Nếu `running_proc` đang tồn tại và khác `None`, ép `running_proc.current_queue = 0`. Reset `current_q_time_spent = 0`. (Nghĩa là process đang chạy cũng được bơm thêm 1 bình Quantum của Q0).

**Bước 4: Xử lý Context Switch (Đang bị treo)**
*   Nếu `cs_cooldown > 0`:
    *   Ghi log "CS Overhead" từ `time_current` đến `time_current + 1`.
    *   `cs_cooldown -= 1`, `time_current += 1`.
    *   `continue` (Bỏ qua các bước dưới, chuyển sang tick tiếp theo).

**Bước 5: Xử lý Preemption (Cướp CPU)**
*   Nếu `running_proc` đang chạy ở Q1 hoặc Q2, MÀ `queues[0]` vừa có phần tử mới (do Bước 2 hoặc Bước 3 sinh ra):
    *   Ghi log `running_proc` vào `gantt_logs`.
    *   Đẩy `running_proc` trở lại đầu hàng đợi `queues[running_proc.current_queue]`.
    *   Set `running_proc = None`, `cs_cooldown = config.context_switch_time`.
    *   `continue` (Kích hoạt Context switch ở tick sau).

**Bước 6: Chọn Process Để Chạy (Dispatch)**
*   Nếu `running_proc is None`:
    *   Duyệt Q0 -> Q1 -> Q2. Tìm process đầu tiên. Lấy ra khỏi queue làm `running_proc`.
    *   Nếu tìm thấy: Set `cs_cooldown = config.context_switch_time` (nếu đây không phải process đầu tiên của hệ thống). Đánh dấu `start_time = time_current` nếu đang là `-1`.
    *   Nếu KHÔNG tìm thấy (Mọi queue đều rỗng): Ghi log "Idle", `time_current += 1`, `continue`.

**Bước 7: Thực thi (Execute Burst)**
*   `running_proc.remaining_time -= 1`
*   `current_q_time_spent += 1`
*   `time_current += 1`

**Bước 8: Kiểm tra Hoàn Thành / Hạ Cấp (End of Tick)**
*   **Case A (Hoàn Thành):** Nếu `running_proc.remaining_time == 0`:
    *   Ghi log hoàn thành vào `gantt_logs`. Ghi `completion_time`.
    *   Đẩy vào `completed_procs`.
    *   `running_proc = None`, `current_q_time_spent = 0`.
*   **Case B (Demotion - Hạ cấp):** Nếu `current_q_time_spent == config.quantum_qX` (Dựa trên Queue hiện tại):
    *   Ghi log vào `gantt_logs`.
    *   `next_q = min(2, running_proc.current_queue + 1)`
    *   `running_proc.current_queue = next_q`
    *   Đẩy `running_proc` vào đuôi `queues[next_q]`.
    *   `running_proc = None`, `current_q_time_spent = 0`.

---

## 3. 🎨 Đặc Tả Giao Diện (UI Specifications - Streamlit)

Mọi thao tác UI phải validate theo Type Hint. Sử dụng `st.session_state` để chứa `AppConfig` và `SimulationRun` sau khi hoàn tất.

### 3.1. Sidebar (Quản Lý Cấu Hình Global)
*   **Vị trí:** `st.sidebar`
*   **UI Components:**
    *   `st.number_input("Q0 Quantum", min_value=1, value=4, step=1)`
    *   `st.number_input("Q1 Quantum", min_value=1, value=8, step=1)`
    *   `st.number_input("Q2 Quantum", min_value=1, value=16, step=1)`
    *   `st.slider("Aging Boost Interval (ms)", min_value=10, max_value=200, value=50)`
    *   `st.number_input("Context Switch Time", min_value=0, max_value=5, value=1)`
    *   `st.button("💾 Save Configuration")`
*   **Logic:** Bấm Save -> Pass qua `AppConfig(**kwargs)` -> Gọi `JsonRepository.save_config()` -> Cập nhật `st.session_state.config`.

### 3.2. Tab 1: Simulator (Nhập liệu & Chạy)
*   **Vị trí:** Cột trái của Main Area.
*   **UI Components:**
    *   `st.data_editor`: Render danh sách `ProcessInput`. Cho phép User thêm/sửa/xóa dòng tự do (num_rows="dynamic").
    *   Cột trong bảng: `PID` (string), `Arrival Time` (int, min 0), `Burst Time` (int, min 1).
    *   `st.button("🎲 Auto Generate Data")`: Hàm random sinh ra 5 process.
    *   `st.button("🚀 Run MLFQ Simulation", type="primary")`
*   **Validation:** Bấm Run -> Duyệt các dòng của `data_editor`. Dòng nào Burst <= 0 sẽ gọi `st.error("Burst time must be > 0")` và **không chạy thuật toán**.

### 3.3. Tab 2: Dashboard (Hiển thị Kết Quả)
*   Được render TỰ ĐỘNG khi `st.session_state.current_run` tồn tại.
*   **UI Components:**
    *   **Hàng 1:** 3 `st.metric` card hiển thị: Avg Turnaround, Avg Waiting, Avg Response Time.
    *   **Hàng 2:** `st.plotly_chart` vẽ biểu đồ Gantt.
        *   Dữ liệu: Lấy mảng `gantt_logs` từ `SimulationRun`.
        *   Cấu hình Plotly: `px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Queue", color_discrete_map={"Q0":"red", "Q1":"yellow", "Q2":"green", "Idle":"gray", "CS Overhead":"black"})`
    *   **Hàng 3:** `st.dataframe` hiển thị danh sách `ProcessState` đã hoàn thành chi tiết từng metric để giảng viên dễ chấm.

### 3.4. Tab 3: History (Lịch sử)
*   **UI Components:** `st.dataframe` load từ `JsonRepository.get_all_runs()`. Hiển thị ID lần chạy, thời gian, và các thông số AVG.

---

## 4. 🗃️ Đặc Tả Repository (Storage Logic)

Sử dụng `data/history.json` và `data/config.json`. Bắt buộc phải bọc thao tác đọc ghi qua `FileLock`.

```python
# Ví dụ Validation & Type Casting tại tầng Repo
def save_run(run: SimulationRun) -> None:
    # 1. Lock file
    # 2. Đọc file cũ thành list
    # 3. Append run.model_dump(mode="json")
    # 4. Cắt tỉa (Prune) nếu len > 20
    # 5. Ghi đè file
    pass
```

---

## 5. ⏳ Tiến Trình Thực Thi Tuyệt Đối (The 5-Hour Strict Blueprint)

Chỉ code đúng những gì được đặc tả ở trên. Không làm lệch để bảo toàn quỹ thời gian 5 tiếng.

| Thời Gian | Chức Năng (Features) | File Cần Thao Tác | Validation/Checklist |
| :--- | :--- | :--- | :--- |
| **0:00 - 1:00** | **Base Models & Config UI** | `core/models.py`, `core/config.py`, `app.py`, `features/settings/view.py` | Pydantic class chuẩn chưa? Sidebar chỉnh sửa config và lưu xuống JSON hoạt động chưa? (Mở lại file xem config.json có đổi số không). |
| **1:00 - 3:00** | **Core Algorithm (Trọng Tâm)** | `features/mlfq/service.py` | Viết chính xác 8 BƯỚC của vòng lặp Time-Stepping. Quăng TimeoutError nếu time > 100k. In thử Gantt log ra Console xem đúng chưa. |
| **3:00 - 4:00** | **UI View & Dashboard** | `features/mlfq/view.py`, `features/dashboard/view.py` | Bảng `st.data_editor` bắt lỗi số âm thành công. Vẽ Plotly Gantt Chart lên màu đúng theo Queue. Các hàm tính AVG Metrics tính đúng toán học. |
| **4:00 - 4:45** | **Repository & History** | `core/repository.py`, `features/history/view.py` | Cài đặt `filelock`. Bấm Run 3 lần liên tiếp xem file history.json có lưu đủ 3 cục RunId không. Load Dataframe Tab 3 thành công. |
| **4:45 - 5:00** | **Đóng gói Docker** | `Dockerfile`, `docker-compose.yml` | Chạy lệnh docker build. Đảm bảo chạy container truy cập localhost:8501 thấy giao diện. Mount data volume thành công. |

Bản đặc tả này đóng vai trò như một **Software Requirement Specification (SRS) + Low Level Design (LLD)**. Mọi thứ đã rõ ràng đến mức Developer chỉ cần chuyển thể từ ngôn ngữ tiếng Việt ở Bước 2 sang ngôn ngữ Python là hoàn thành ứng dụng.
