# MLFQ OS Simulator Final Spec

**Mục đích:** Đây là tài liệu đặc tả cuối cùng cho implementation. Một worker hoặc agent phải có thể đọc file này và triển khai ứng dụng từ đầu tới cuối mà không tự phát minh thêm yêu cầu sản phẩm hay thêm mode thuật toán.

**Phạm vi:** Tài liệu này đặc tả đúng một ứng dụng Streamlit mô phỏng thuật toán `Multi-Level Feedback Queue (MLFQ)` cho mục đích học tập và chấm đồ án.

## 1. Thứ tự ưu tiên tài liệu

Nếu có mâu thuẫn:

1. File này là nguồn sự thật cuối cùng cho implementation.
2. `docs/superpowers/plans/2026-05-15-mlfq-os-simulator.md` là execution plan.
3. `docs/master-plan.md` là blueprint cũ và chỉ còn giá trị tham khảo nếu không xung đột.
4. `docs/project-draft.md` là tài liệu nền tảng để hiểu bài toán.

## 2. Mục tiêu sản phẩm

Ứng dụng phải làm được đúng các việc sau:

- Cho người dùng nhập một danh sách process gồm `pid`, `arrival_time`, `burst_time`
- Cho người dùng chỉnh cấu hình MLFQ gồm quantum của `Q0`, `Q1`, `Q2`, chu kỳ `priority boost`, và `context switch time`
- Chạy mô phỏng thuật toán MLFQ
- Hiển thị animation mô phỏng quá trình thuật toán chạy với tốc độ đủ chậm để mắt người có thể theo dõi
- Hiển thị kết quả bằng:
  - metrics
  - Gantt chart
  - bảng kết quả process
  - lịch sử các lần chạy

Ứng dụng phải làm rõ được bốn hành vi cốt lõi của MLFQ:

- Process mới luôn vào `Q0`
- CPU luôn ưu tiên `Q0 -> Q1 -> Q2`
- Hết quantum thì process bị hạ queue
- `priority boost` định kỳ giúp tránh starvation

## 3. Ngoài phạm vi

Các hạng mục sau bị cấm trong deliverable đầu tiên:

- Bất kỳ thuật toán scheduling nào ngoài MLFQ
- Nhiều mode MLFQ hoặc cho người dùng đổi mode thuật toán
- Nhiều cơ chế chống đói trong cùng sản phẩm
- Dashboard benchmark, màn hình so sánh thuật toán, hoặc performance lab
- Database server, auth, multi-user, cloud deployment
- Kiến trúc extensible chỉ để “sau này thêm thuật toán”

## 4. Kiến trúc bắt buộc

- Ứng dụng là local/web app dùng Streamlit
- Logic thuật toán phải là pure engine tách khỏi UI
- UI chỉ làm:
  - nhận input
  - validate input người dùng
  - gọi scheduler
  - render output
- Animation playback phải là client-side, không được dựa vào vòng lặp rerender từng tick ở phía Streamlit server
- Persistence chỉ dùng JSON local
- Python tooling dùng `uv`
- Python version phải là `3.12`

## 5. Mô hình thuật toán được chọn

Ứng dụng chỉ implement một biến thể duy nhất:

- `Preemptive MLFQ`
- Có đúng 3 queue: `Q0`, `Q1`, `Q2`
- `Q0`, `Q1`, `Q2` đều có quantum cấu hình được
- Nếu process ở `Q2` dùng hết quantum mà chưa xong, nó vẫn ở lại `Q2`
- Cơ chế chống đói duy nhất là `global priority boost` mỗi `aging_boost_interval` tick

## 6. Quy tắc thuật toán

### 6.1. Quy tắc queue

- Process mới đến luôn vào `Q0`
- CPU chọn process theo thứ tự `Q0`, rồi `Q1`, rồi `Q2`
- Trong mỗi queue, process chờ theo FIFO
- Nếu process dùng hết quantum ở:
  - `Q0` và chưa xong: chuyển xuống `Q1`
  - `Q1` và chưa xong: chuyển xuống `Q2`
  - `Q2` và chưa xong: quay lại cuối `Q2`

### 6.2. Quy tắc preemption

- Nếu một process đang chạy ở `Q1` hoặc `Q2`
- và trong cùng tick `Q0` có process mới khả dụng
- thì process đang chạy bị preempt
- process bị preempt quay lại **đầu queue hiện tại**
- quantum đã dùng ở queue hiện tại được giữ nguyên
- sau đó CPU phải xử lý `context switch` trước khi chạy process khác

### 6.3. Quy tắc priority boost

Ở mỗi tick mà:

- `time_current > 0`
- và `time_current % aging_boost_interval == 0`

thì:

- toàn bộ process đang chờ trong `Q1` và `Q2` được chuyển về đuôi `Q0` theo thứ tự ổn định
- mọi process đó được đặt `current_queue = 0`
- nếu đang có process chạy:
  - process đó không bị requeue
  - `current_queue` của nó được đặt thành `0`
  - quantum-used của nó được reset

Không có cơ chế aging nào khác.

### 6.4. Quy tắc context switch

- `context switch time` được tính bằng tick
- `CS Overhead` chỉ bị tính khi chuyển trực tiếp từ process này sang process khác
- Không tính `CS Overhead` cho:
  - lần dispatch đầu tiên của hệ thống
  - chuyển từ `Idle` sang process đầu tiên sau một đoạn rảnh CPU

## 7. Tick order bắt buộc

Ở mỗi tick, scheduler phải xử lý đúng thứ tự này:

1. Circuit breaker
2. Arrival ingestion
3. Priority boost
4. Context switch cooldown handling
5. Preemption check
6. Dispatch if CPU is free
7. Execute one time unit
8. Resolve completion or demotion

Không được đổi thứ tự này.

## 8. Invariants bắt buộc

- Tổng CPU time của process bằng tổng `burst_time` đầu vào
- Không process nào có `remaining_time < 0`
- Mỗi process hoàn thành đúng một lần
- `start_time` chỉ được ghi một lần, ở tick CPU thực sự chạy process đó lần đầu
- `completion_time` là tick ngay sau đơn vị thực thi cuối cùng
- `throughput = completed_process_count / makespan`
- `makespan = max(completion_time)` và phải > 0

## 9. Input contract

### 9.1. Process input

Mỗi process có:

- `pid: str`
- `arrival_time: int`
- `burst_time: int`

Validation:

- `pid` không rỗng
- `pid` không trùng
- `arrival_time >= 0`
- `burst_time > 0`

### 9.2. Config input

Config gồm:

- `quantum_q0: int`
- `quantum_q1: int`
- `quantum_q2: int`
- `aging_boost_interval: int`
- `context_switch_time: int`

Validation:

- mọi quantum > 0
- `aging_boost_interval > 0`
- `context_switch_time >= 0`

## 10. Output contract

### 10.1. Process metrics

Mỗi process hoàn thành phải có:

- `turnaround_time = completion_time - arrival_time`
- `waiting_time = turnaround_time - burst_time`
- `response_time = start_time - arrival_time`

### 10.2. Run metrics

Mỗi lần chạy phải có:

- `avg_turnaround`
- `avg_waiting`
- `avg_response`
- `throughput`

### 10.3. Gantt contract

Mỗi segment Gantt phải có:

- `Task`
- `Start`
- `Finish`
- `Queue`

Rules:

- interval là `[Start, Finish)`
- segment kề nhau có cùng `Task` và `Queue` phải được merge
- `Idle` và `CS Overhead` phải xuất hiện trong Gantt khi có

## 11. Persistence contract

Ứng dụng chỉ dùng:

- `data/config.json`
- `data/history.json`

Rules:

- mọi thao tác ghi phải dùng lock + temp file + replace
- file thiếu thì auto-create
- JSON hỏng thì fallback an toàn
- config fallback về default
- history fallback về danh sách rỗng
- history chỉ giữ tối đa 20 bản ghi, mới nhất nằm cuối

## 12. UI contract

Ứng dụng phải có đúng ba khu vực chức năng:

### 12.1. Sidebar cấu hình

- chỉnh `Q0`, `Q1`, `Q2`, `boost interval`, `context switch`
- lưu config xuống JSON

### 12.2. Simulator

- nhập bảng process
- có nút nạp dữ liệu demo nhanh vào bảng
- nút chạy simulation
- validation lỗi phải chặn scheduler nếu input sai
- animation được phát ngay trong khu vực Simulator sau khi run thành công

### 12.3. Dashboard và History

- Dashboard:
  - metrics
  - Gantt chart
  - bảng process result
- History:
  - danh sách run đã lưu

UI phải đủ rõ để giảng viên nhìn là hiểu thuật toán đang làm gì. UI không cần thêm màn hình ngoài lõi này.

## 13. Acceptance fixtures

Implementation chỉ được coi là đúng khi match các fixtures sau.

### Fixture A: Single process demotion path

- Config: `q0=4`, `q1=8`, `q2=16`, `boost=50`, `cs=0`
- Input: `P1 arrival=0 burst=20`
- Expected Gantt:
  - `P1 Q0 0-4`
  - `P1 Q1 4-12`
  - `P1 Q2 12-20`
- Expected:
  - `turnaround=20`
  - `waiting=0`
  - `response=0`
  - `throughput=0.05`

### Fixture B: Preemption by new Q0 work

- Config: `q0=2`, `q1=4`, `q2=8`, `boost=50`, `cs=0`
- Input:
  - `P1 arrival=0 burst=7`
  - `P2 arrival=3 burst=1`
- Expected Gantt:
  - `P1 Q0 0-2`
  - `P1 Q1 2-3`
  - `P2 Q0 3-4`
  - `P1 Q1 4-7`
  - `P1 Q2 7-8`

### Fixture C: Global boost

- Config: `q0=1`, `q1=1`, `q2=2`, `boost=4`, `cs=0`
- Input:
  - `P1 arrival=0 burst=5`
  - `P2 arrival=0 burst=5`
- Expected Gantt:
  - `P1 Q0 0-1`
  - `P2 Q0 1-2`
  - `P1 Q1 2-3`
  - `P2 Q1 3-4`
  - `P1 Q0 4-5`
  - `P2 Q0 5-6`
  - `P1 Q1 6-7`
  - `P2 Q1 7-8`
  - `P1 Q0 8-9`
  - `P2 Q0 9-10`

### Fixture D: Context switch

- Config: `q0=4`, `q1=8`, `q2=16`, `boost=50`, `cs=1`
- Input:
  - `P1 arrival=0 burst=1`
  - `P2 arrival=0 burst=1`
- Expected Gantt:
  - `P1 Q0 0-1`
  - `CS Overhead N/A 1-2`
  - `P2 Q0 2-3`

### Fixture E: Idle CPU

- Config: `q0=4`, `q1=8`, `q2=16`, `boost=50`, `cs=0`
- Input:
  - `P1 arrival=3 burst=2`
- Expected Gantt:
  - `Idle N/A 0-3`
  - `P1 Q0 3-5`

### Fixture F: Invalid input

Expected:

- duplicate `pid` bị chặn
- `arrival_time < 0` bị chặn
- `burst_time <= 0` bị chặn
- bảng rỗng bị chặn
- scheduler không được gọi
- history không được ghi

## 14. Definition of done

Deliverable chỉ được coi là hoàn tất khi:

1. Clone repo
2. Chạy script setup
3. Chạy app
4. Nhập sample data hoặc dữ liệu tay
5. Chạy simulation
6. Xem được animation mô phỏng trên UI
7. Xem được Gantt, metrics, bảng process, history
8. Test pass
9. Không cần cài tay dependency ngoài script setup

## 15. Ghi chú cho implementer

- Nếu thấy nhu cầu “thêm mode cho tương lai”, bỏ qua.
- Nếu thấy nhu cầu “thêm thuật toán để đẹp hơn”, bỏ qua.
- Nếu có chỗ phải tự quyết giữa nhiều cách hiểu, quay về file này trước, không quay về `project-draft` để mở rộng scope.
- Plan có thể nói chi tiết hơn về thứ tự task, nhưng behavior cuối cùng phải tuân thủ spec này.
