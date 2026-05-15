# Algorithm Extension Guide

Tài liệu này mô tả contract mở rộng dài hạn của scheduling platform.

## Mục tiêu

Thêm một thuật toán mới phải là **zero-touch extension**:

- không sửa `app.py`
- không sửa `ui/`
- không sửa `application/services.py`
- không sửa `application/comparison_service.py`
- không sửa registry bằng tay

Nếu phải sửa các file đó để thêm thuật toán mới, kiến trúc đang bị dùng sai.

## Hiểu đúng về “zero-touch”

`Zero-touch` ở đây chỉ áp dụng cho **platform wiring**.

Nó **không** có nghĩa là:

- thuật toán mới tự sinh ra
- chỉ copy file là chạy đúng
- không cần viết test
- không cần nghĩ về trace hoặc metrics

Ý nghĩa chính xác là:

- không phải sửa app shell
- không phải sửa UI shell
- không phải sửa registry bằng tay
- không phải sửa comparison flow bằng tay

Phần vẫn phải tự làm nghiêm túc:

- logic scheduling của chính thuật toán
- trace frames hợp lệ cho animation/UI chung
- config semantics của chính thuật toán
- deterministic tests và regression tests

## 1. Cấu trúc package bắt buộc

Mỗi thuật toán mới tạo một package mới dưới:

- `src/mlfq_os_simulator/algorithms/<algorithm_key>/`

Tối thiểu cần:

- `src/mlfq_os_simulator/algorithms/<algorithm_key>/__init__.py`
- `src/mlfq_os_simulator/algorithms/<algorithm_key>/strategy.py`

## 2. Contract bắt buộc

`strategy.py` phải implement `SchedulerStrategy` từ:

- `src/mlfq_os_simulator/shared/contracts.py`

Các metadata bắt buộc:

- `key`
- `display_name`
- `description`
- `config_fields`
- `supports_animation`
- `include_in_comparison`
- `is_default`
- `order`

Method bắt buộc:

- `simulate(processes, config) -> StrategySimulation`

## 3. Cấu hình thuật toán

Mỗi strategy tự khai báo field cấu hình bằng `AlgorithmConfigField`.

Ví dụ:

```python
config_fields = (
    AlgorithmConfigField("sjf_alpha", "SJF Alpha", 2, min_value=1),
    AlgorithmConfigField("context_switch_time", "Context Switch Time", 1, min_value=0, max_value=20),
)
```

Ý nghĩa:

- Sidebar sẽ tự render field này
- Giá trị sẽ tự persist qua `AppConfig`
- Strategy đọc lại bằng `config.get_int("sjf_alpha", 2)`

Không thêm field mới vào `shared/config.py` cho từng thuật toán riêng.

## 4. Discovery tự động

`__init__.py` của package thuật toán phải export một biến tên `STRATEGY`.

Ví dụ:

```python
from .strategy import SJFStrategy

STRATEGY = SJFStrategy()
```

Registry sẽ tự scan mọi package con trong `src/mlfq_os_simulator/algorithms/` và nạp `STRATEGY`.

Không đăng ký tay trong code trung tâm nữa.

## 5. Tham gia Simulator và Comparison

### Simulator

Chỉ cần strategy package được discover thành công là nó tự xuất hiện trong dropdown của tab `Simulator`.

### Comparison

Muốn thuật toán tự xuất hiện trong tab `Comparison`, đặt:

- `include_in_comparison = True`

Muốn chỉ cho chạy riêng ở `Simulator`, đặt:

- `include_in_comparison = False`

Không sửa `ComparisonService` để thêm key thủ công.

## 6. Output bắt buộc

`simulate(...)` phải trả về:

- `StrategySimulation`
  - `result: AlgorithmRunResult`
  - `frames: list[AlgorithmTraceFrame]`

Nguyên tắc:

- `result` phải dùng neutral models trong `shared/results.py`
- `frames` phải đủ hợp lệ để animation renderer dùng lại được
- nếu thuật toán không có queue phức tạp, vẫn có thể trả lane đơn giản như `Ready`, `CPU`, `Completed`

### Trace không được làm qua loa

Coding agent phải hiểu rõ:

- trace là contract thật, không phải “để sau”
- nếu `frames` rỗng hoặc sai shape thì UI animation sẽ hỏng
- nếu lane naming không nhất quán thì animation và comparison preview sẽ khó đọc

Tối thiểu mỗi frame phải trả được:

- `time_current`
- `status`
- `running_label`
- `lanes_snapshot`
- `completed_labels`
- `gantt_entries`

Nếu thuật toán không có nhiều queue, vẫn phải mô hình hóa lane tối thiểu có nghĩa, ví dụ:

- `Ready`
- `CPU`
- `Completed`

Không được hard-code special-case mới trong renderer chỉ để cứu một thuật toán mới.

## 7. Quy tắc kiến trúc

- Strategy không import `ui/`
- Strategy không import `infrastructure/`
- Strategy không ghi file JSON trực tiếp
- Strategy không phụ thuộc implementation của strategy khác
- Không nối tắt thuật toán mới vào UI
- Không viết special-case trong `app.py` cho riêng một algorithm

## 8. Điểm hở và giới hạn hiện tại

Đây là các giới hạn thật mà implementer phải biết trước:

- `AppConfig` hiện là key-value config với giá trị số nguyên
  - phù hợp cho quantum, threshold, interval, context switch
  - **chưa** phù hợp cho config kiểu chuỗi, enum phức tạp, list, nested object
- Sidebar auto-render hiện chỉ hỗ trợ widget:
  - `number`
  - `slider`
- Comparison hiện assume mọi thuật toán có thể sinh:
  - `AlgorithmRunResult`
  - `AlgorithmTraceFrame`
  - metrics cùng semantic chung
- Discussion text trong comparison hiện vẫn thiên về yếu tố hiệu năng của `MLFQ`
  - thuật toán mới vẫn chạy được
  - nhưng nếu muốn discussion chuyên sâu cho thuật toán đó thì phải nâng shared discussion layer, không vá cục bộ
- Animation renderer là generic, nhưng vẫn giả định:
  - time progression rời rạc
  - gantt entries dùng numeric timeline
  - lanes snapshot có thể biểu diễn bằng text list
- Zero-touch chỉ đúng nếu thuật toán mới nằm trong cùng họ cấu hình và output contract hiện tại
  - nếu thuật toán mới cần loại config mới hoặc visualization mới, phải nâng contract shared trước
  - không được lách bằng hack trong UI hoặc app shell

## 9. Những việc implementer vẫn bắt buộc phải làm

Khi thêm thuật toán mới, coding agent **vẫn phải tự tư duy** và hoàn thành:

1. thiết kế scheduling semantics
2. xử lý tie-breaker rõ ràng
3. quyết định lane model cho trace
4. tính metrics đúng theo contract chung
5. viết deterministic tests
6. viết test cho discovery/registry nếu cần
7. viết test comparison nếu `include_in_comparison = True`

Không được hiểu tài liệu này theo kiểu:

- “chỉ cần export `STRATEGY` là xong”
- “UI tự hiện nghĩa là thuật toán đúng”
- “không cần test vì platform đã lo hết”

## 10. Test bắt buộc

Khi thêm thuật toán mới, tối thiểu phải có:

- deterministic strategy test
- registry discovery test
- simulator smoke/integration nếu thuật toán có animation khác biệt
- comparison service test nếu `include_in_comparison = True`

Vị trí test thường dùng:

- `tests/unit/test_comparison_schedulers.py`
- `tests/unit/test_algorithm_registry.py`
- `tests/unit/test_comparison_service.py`
- `tests/integration/test_app.py`

## 11. Checklist hoàn tất

1. Tạo package mới trong `algorithms/`
2. Implement `SchedulerStrategy`
3. Export `STRATEGY` trong `__init__.py`
4. Dùng `AlgorithmConfigField` cho mọi config riêng
5. Dùng neutral result/trace contract
6. Thêm test phù hợp
7. Chạy `uv run ruff check .`
8. Chạy `uv run ty check src`
9. Chạy `uv run pytest tests -q`
