# Comparison Analysis

## Mục tiêu

Phần này dùng để đáp ứng yêu cầu chính thức: so sánh `MLFQ` với thuật toán khác và thảo luận các yếu tố ảnh hưởng hiệu năng của `MLFQ`.

## Thuật toán dùng để so sánh

- `MLFQ`
- `FCFS`
- `Round Robin`

## Workloads chuẩn

- `Balanced Mix`
- `Interactive Heavy`
- `CPU-Bound Heavy`

## Các yếu tố ảnh hưởng chính

### 1. Quantum của MLFQ

- `quantum_q0`, `quantum_q1`, `quantum_q2` ảnh hưởng trực tiếp tới phản hồi của job ngắn và số lần preempt.
- Quantum nhỏ hơn giúp response tốt hơn cho interactive jobs, nhưng tăng số context switch.
- Quantum lớn hơn có thể giảm overhead nhưng làm MLFQ gần hơn với các thuật toán ít ưu tiên hơn.

### 2. Aging boost interval

- Nếu `aging_boost_interval` quá lớn, process ở queue thấp chờ lâu hơn.
- Nếu interval nhỏ hơn, fairness tốt hơn nhưng MLFQ có thể ít phân tầng hơn về hành vi.

### 3. Context switch time

- Khi `context_switch_time` tăng, các thuật toán preemptive chịu penalty rõ hơn.
- `MLFQ` và `Round Robin` thường nhạy hơn `FCFS` với overhead này.

### 4. Loại workload

- Workload nhiều job ngắn đến dày:
  - MLFQ thường có `avg_response` tốt hơn
- Workload thiên CPU-bound:
  - FCFS có thể đạt `makespan` hoặc throughput cạnh tranh hơn do ít interruption
- Workload cân bằng:
  - MLFQ thường đạt tradeoff tốt giữa fairness và responsiveness

### 5. Fairness vs throughput

- `MLFQ` ưu tiên responsiveness và chống starvation.
- `FCFS` đơn giản và ít overhead nhưng dễ làm short jobs chờ lâu.
- `Round Robin` công bằng hơn `FCFS`, nhưng không có phân tầng ưu tiên như `MLFQ`.

## Cách đọc bảng comparison

Khi xem tab `Comparison`, nên đọc:

1. `avg_response` để đánh giá mức phản hồi
2. `avg_waiting` để đánh giá độ trễ tổng quát
3. `avg_turnaround` để đánh giá thời gian hoàn tất end-to-end
4. `throughput` và `makespan` để đánh giá hiệu suất tổng thể

## Kết luận phase hiện tại

Mục tiêu của comparison phase không phải chứng minh MLFQ luôn tốt nhất.  
Mục tiêu là cho thấy:

- khi nào MLFQ có lợi thế rõ ràng
- khi nào baseline algorithms có thể cạnh tranh hơn
- cấu hình và workload nào làm hiệu năng MLFQ thay đổi đáng kể
