Bạn đang làm việc trong repo `D:\dev\school\os\os-project-20252-166239`.

Mục tiêu: thêm 1 thuật toán scheduling mới theo kiến trúc zero-touch hiện tại, sao cho:
- không sửa `D:\dev\school\os\os-project-20252-166239\app.py`
- không sửa UI shell trong `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\ui\`
- không đăng ký registry bằng tay
- không sửa comparison flow bằng tay
- thuật toán mới tự xuất hiện trong `Simulator`
- nếu bật comparison thì tự xuất hiện trong `Comparison`

Làm theo workflow này, không bỏ bước:

1. Đọc source of truth
- `D:\dev\school\os\os-project-20252-166239\docs\superpowers\2026-05-15-scheduling-platform-blueprint.md`
- `D:\dev\school\os\os-project-20252-166239\docs\algorithm-extension-guide.md`
- `D:\dev\school\os\os-project-20252-166239\AGENTS.md`

2. Hiểu contract extension hiện tại
- `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\shared\contracts.py`
- `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\shared\results.py`
- `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\shared\config.py`

3. Hiểu cơ chế auto-discovery và orchestration
- `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\application\strategy_loader.py`
- `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\application\registry.py`
- `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\application\services.py`
- `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\application\comparison_service.py`

4. Xem reference implementations trước khi code
- đơn giản:
  - `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\algorithms\fcfs\strategy.py`
  - `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\algorithms\round_robin\strategy.py`
- phức tạp hơn:
  - `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\algorithms\mlfq\strategy.py`
  - `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\algorithms\mlfq\engine.py`

5. Tạo package mới
- tạo thư mục:
  - `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\algorithms\<algorithm_key>\`
- tối thiểu có:
  - `__init__.py`
  - `strategy.py`

6. Implement strategy đúng contract
Trong `strategy.py`, implement đầy đủ:
- `key`
- `display_name`
- `description`
- `config_fields`
- `supports_animation`
- `include_in_comparison`
- `is_default`
- `order`
- `simulate(processes, config) -> StrategySimulation`

7. Config rules
- chỉ dùng `AlgorithmConfigField` để khai báo config
- strategy đọc config bằng `config.get_int(...)`
- không thêm field riêng vào UI
- không sửa `render_sidebar(...)`

8. Trace rules
- phải trả `frames` hợp lệ, không được để rỗng nếu algorithm cần hiển thị runtime
- mỗi frame phải conform `AlgorithmTraceFrame`
- nếu algorithm đơn giản, dùng lane kiểu:
  - `Ready`
  - `CPU`
  - `Completed`
- không sửa `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\ui\animation.py` chỉ để cứu thuật toán mới

9. Export strategy để auto-discovery thấy được
Trong `__init__.py`, phải export:
- `STRATEGY = <YourStrategyClass>()`

Reference:
- `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\algorithms\fcfs\__init__.py`
- `D:\dev\school\os\os-project-20252-166239\src\mlfq_os_simulator\algorithms\round_robin\__init__.py`

10. Comparison participation
- nếu muốn thuật toán tự xuất hiện ở tab `Comparison`, đặt:
  - `include_in_comparison = True`
- nếu không, đặt:
  - `include_in_comparison = False`
- không sửa `comparison_service.py` để add key thủ công

11. Viết test bắt buộc
Đọc reference tests:
- `D:\dev\school\os\os-project-20252-166239\tests\unit\test_comparison_schedulers.py`
- `D:\dev\school\os\os-project-20252-166239\tests\unit\test_algorithm_registry.py`
- `D:\dev\school\os\os-project-20252-166239\tests\unit\test_comparison_service.py`
- `D:\dev\school\os\os-project-20252-166239\tests\integration\test_app.py`

Phải thêm ít nhất:
- deterministic unit test cho thuật toán mới
- registry discovery test nếu cần
- comparison test nếu `include_in_comparison = True`

12. Không được làm
- không sửa `app.py` trừ khi bạn chứng minh contract shared đang thiếu thật
- không sửa `ui/` chỉ vì thuật toán mới không conform trace contract
- không hard-code algorithm key mới vào registry
- không nối tắt vào persistence
- không resurrect legacy modules

13. Verify bắt buộc sau khi xong
Chạy đúng thứ tự:
- `uv sync --all-groups --frozen --python 3.12 --managed-python --link-mode copy`
- `uv run ruff check .`
- `uv run ty check src`
- `uv run pytest tests -q`

14. Kết quả bàn giao phải gồm
- các file mới/đổi
- thuật toán mới xuất hiện ở `Simulator` mà không sửa UI shell
- nếu opted-in, thuật toán mới xuất hiện ở `Comparison`
- test pass đầy đủ
- giải thích ngắn gọn lane model và config semantics của thuật toán mới

Nếu trong lúc làm bạn thấy phải sửa platform wiring để thêm riêng thuật toán này, dừng lại và nêu rõ vì sao contract hiện tại chưa đủ, thay vì vá tắt.
