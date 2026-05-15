# Scheduling Platform Blueprint

Tài liệu này là **nguồn sự thật duy nhất** cho kiến trúc, phạm vi, và kế hoạch triển khai của repo từ thời điểm này trở đi.

Mục tiêu của tài liệu này là thay thế hoàn toàn cách làm cũ kiểu:

- MLFQ hard-code trong app
- vá thêm comparison sau
- để nhiều file spec/plan cùng tồn tại và mâu thuẫn nhau

Từ đây về sau:

- file này là blueprint chính
- mọi implementation phải bám theo blueprint này
- nếu code lệch blueprint, code phải sửa
- nếu blueprint thiếu quyết định, blueprint phải được bổ sung trước

---

## 1. Mục tiêu sản phẩm

Repo này phải trở thành một **scheduling platform base** có thể:

1. chạy mô phỏng `MLFQ` như thuật toán chính
2. so sánh `MLFQ` với các thuật toán khác
3. để dev khác tiếp tục thêm thuật toán trong các tuần còn lại mà không cần phá kiến trúc

Phase hiện tại phải có:

- `MLFQ`
- `FCFS`
- `Round Robin`

Trong đó:

- `MLFQ` là experience chính
- `Comparison` là feature bắt buộc để đáp ứng đề bài
- kiến trúc phải đủ sạch để mở rộng sau này

---

## 2. Source of truth và tài liệu còn hiệu lực

Thứ tự ưu tiên:

1. File này
2. `README.md`
3. `AGENTS.md`
4. `docs/project-draft.md` chỉ để hiểu bài toán gốc
5. `docs/master-plan.md` chỉ là tài liệu lịch sử

Các file plan/spec cũ trong `docs/superpowers/plans` và `docs/superpowers/specs` đã bị loại bỏ và không còn hiệu lực.

---

## 3. Kiến trúc bắt buộc

Kiến trúc phải theo đúng hướng **strategy-first**, giống tinh thần NestJS:

- có shared contracts
- có concrete implementations tách riêng
- có application/service layer điều phối
- UI chỉ nói chuyện với application layer
- persistence chỉ là infrastructure adapter

### 3.1. Module structure

Code phải được tổ chức thành các vùng sau:

- `shared/`
- `algorithms/`
- `application/`
- `infrastructure/`
- `ui/`

### 3.2. Ý nghĩa từng vùng

#### `shared/`

Chứa các contract và model dùng chung:

- `ProcessInput`
- config base models
- neutral run result
- neutral trace frame
- metric helpers
- gantt helpers
- constants
- shared exceptions

`shared/` không được import ngược `algorithms`, `application`, `ui`, `infrastructure`.

#### `algorithms/`

Mỗi thuật toán là một implementation riêng:

- `algorithms/mlfq/`
- `algorithms/fcfs/`
- `algorithms/round_robin/`

Mỗi algorithm module chỉ chứa:

- strategy implementation
- config riêng nếu cần
- internal helper
- trace builder riêng nếu cần

Không để nhiều thuật toán chung một file.

#### `application/`

Là service layer điều phối:

- scheduler registry
- simulation service
- comparison service
- workload provider
- adapter logic giữa UI và strategies

UI chỉ được gọi vào `application/`.

#### `infrastructure/`

Chứa persistence và adapter ngoài:

- config repository
- history repository

Không chứa domain logic của thuật toán.

#### `ui/`

Chỉ chứa rendering và interaction:

- simulator tab
- animation
- dashboard
- history
- comparison tab

UI không được tự tính metrics, không tự quyết scheduling policy, không import concrete strategy trực tiếp.

---

## 4. Dependency direction

Direction bắt buộc:

- `ui -> application`
- `application -> shared + algorithms + infrastructure`
- `algorithms -> shared`
- `infrastructure -> shared`
- `shared -> nobody`

Điều cấm:

- `ui -> algorithms`
- `algorithms -> ui`
- `shared -> algorithms`
- `shared -> infrastructure`

---

## 5. Strategy contract

Mọi thuật toán phải implement cùng một contract:

- `key`
- `display_name`
- `supports_animation`
- `simulate(processes, config) -> StrategySimulation`

### `StrategySimulation`

Phải gồm:

- `result`
- `frames`

### `result`

Là neutral run result dùng chung cho mọi thuật toán, tối thiểu gồm:

- `run_id`
- `algorithm_key`
- `algorithm_display_name`
- `timestamp`
- `config_used`
- `process_count`
- `process_inputs`
- `process_results`
- `gantt_entries`
- `makespan`
- `throughput`
- `avg_turnaround`
- `avg_waiting`
- `avg_response`

### `frames`

Là neutral trace frame, tối thiểu gồm:

- `time_current`
- `status`
- `running_label`
- `lanes_snapshot`
- `completed_labels`
- `gantt_entries`

Không encode queue-specific assumptions như `Q0/Q1/Q2` vào contract chung.

---

## 6. Thuật toán trong phase hiện tại

### `MLFQ`

- là thuật toán chính
- có animation sâu nhất
- vẫn phải conform strategy contract

### `FCFS`

- là baseline comparison
- không cần parity animation với MLFQ
- phải sinh summary và trace hợp lệ

### `Round Robin`

- là baseline comparison có quantum
- default comparison quantum = `4`
- phải sinh summary và trace hợp lệ

### Ngoài phạm vi phase này

- `SJF`
- `Priority`
- `EDF`
- các biến thể advanced khác

---

## 7. Persistence contract

Persistence chỉ quản lý:

- `data/config.json`
- `data/history.json`

Không lưu:

- transient UI state
- demo rows
- curated workloads cho comparison

History schema được phép thay đổi để phục vụ neutral architecture.

Mỗi record history phải đủ để:

- biết thuật toán nào đã chạy
- biết input nào đã được dùng
- biết config snapshot nào đã được dùng
- hiển thị summary metrics
- hiển thị Gantt summary

Không bắt buộc phải lưu full animation trace vào history ở phase này.

---

## 8. UI contract

App phải có ít nhất 4 khu vực:

1. `Simulator`
2. `Dashboard`
3. `History`
4. `Comparison`

### `Simulator`

- nhận process table
- cho chỉnh config
- nạp demo rows nhanh
- chạy strategy chính mặc định là `MLFQ`
- phát animation

### `Dashboard`

- hiển thị summary của run gần nhất
- dùng neutral result contract

### `History`

- hiển thị các run đã lưu
- không assume MLFQ-only

### `Comparison`

- nhận `Current Table` hoặc curated workload
- chạy `MLFQ`, `FCFS`, `Round Robin`
- hiển thị bảng metrics comparison
- có static Gantt preview nếu cần
- có block discussion ngắn

---

## 9. Comparison workloads

Phải có đúng 3 curated workloads trong phase hiện tại:

- `Balanced Mix`
- `Interactive Heavy`
- `CPU-Bound Heavy`

Workloads này:

- nằm trong code
- thuộc application/comparison layer
- không đi qua repository

---

## 10. Discussion requirement

Repo phải có cả:

- UI comparison block
- file tài liệu analysis

Các yếu tố phải được thảo luận:

- `quantum_q0`
- `quantum_q1`
- `quantum_q2`
- `aging_boost_interval`
- `context_switch_time`
- workload mix
- arrival density
- fairness vs throughput

Discussion phải bám trên kết quả đo, không chỉ lý thuyết chung chung.

---

## 11. Extension requirement

Repo phải có tài liệu `docs/algorithm-extension-guide.md` đủ để dev khác:

- tạo strategy mới
- đăng ký vào registry
- thêm test
- cắm vào comparison layer

không cần reverse-engineer codebase.

---

## 12. Definition of done

Phase này chỉ hoàn tất khi:

1. `MLFQ`, `FCFS`, `Round Robin` cùng conform strategy contract
2. app vẫn chạy ổn
3. `Comparison` tab hoạt động
4. persistence vẫn ổn
5. docs mới phản ánh đúng kiến trúc mới
6. test suite và static checks pass

---

## 13. Kế hoạch triển khai chuẩn

Thứ tự bắt buộc:

1. viết lại source-of-truth docs
2. dựng shared contracts/results
3. dựng registry + application services
4. chuyển `MLFQ` thành concrete strategy
5. migrate app hiện tại sang service/registry
6. thêm `FCFS`
7. thêm `Round Robin`
8. thêm comparison service
9. thêm comparison UI
10. thêm extension guide + analysis docs
11. cleanup legacy shims

Không được làm comparison UI trước khi có strategy contract đúng nghĩa.

---

## 14. Điều cấm

- Không vá app hiện tại bằng cách gọi thẳng strategy mới từ UI
- Không để `scheduler.py` ở root package tiếp tục là implementation thật mãi mãi
- Không để `models.py` tiếp tục trộn shared contract với MLFQ-specific runtime model lâu dài
- Không để repository tiếp tục ở sai tầng nếu kiến trúc đã chuyển sang strategy-first
- Không giữ lại `core/` song song với `shared/`; sau hard-cut chỉ còn một shared layer duy nhất

---

## 15. Kỳ vọng với code hiện tại

Code hiện tại có thể ở trạng thái chuyển tiếp, nhưng mục tiêu cuối phải là:

- không còn legacy MLFQ-only boundary
- không còn mixed contracts
- không còn “wrapper strategy bên ngoài, engine thật nằm chỗ cũ” kéo dài

Tức là refactor này phải kết thúc bằng kiến trúc sạch, không phải dừng ở nửa đường.
