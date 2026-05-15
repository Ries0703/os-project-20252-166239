from ...shared.process import ProcessInput
from ...shared.config import AppConfig
from .strategy import SJFSchedulerStrategy

def run_sjf_test():
    processes = [
        ProcessInput(pid="P1", arrival_time=0, burst_time=15),
        ProcessInput(pid="P2", arrival_time=2, burst_time=8),
        ProcessInput(pid="P3", arrival_time=4, burst_time=5),
        ProcessInput(pid="P4", arrival_time=1, burst_time=10),
    ]

    config = AppConfig(values={"context_switch_time": 1})
    strategy = SJFSchedulerStrategy()
    
    simulation = strategy.simulate(processes, config)
    
    print("=== KẾT QUẢ MÔ PHỎNG THUẬT TOÁN SJF ===")
    print("-" * 50)
    for p in simulation.result.process_results:
        print(f"Tiến trình [{p.pid}]: "
              f"Thời điểm đến: {p.arrival_time:2} | "
              f"Thời gian chạy (Burst): {p.burst_time:2} | "
              f"Bắt đầu: {p.start_time:2} | "
              f"Hoàn thành: {p.completion_time:2} | "
              f"Turnaround: {p.turnaround_time:2} | "
              f"Thời gian chờ: {p.waiting_time:2}")
        
    print("\n=== THỐNG KÊ (METRICS) ===")
    print("-" * 50)
    print(f"Thời gian lưu lại trung bình (Avg Turnaround): {simulation.result.avg_turnaround:.2f}")
    print(f"Thời gian chờ trung bình (Avg Waiting):        {simulation.result.avg_waiting:.2f}")
    print(f"Throughput:                                    {simulation.result.throughput:.4f}")

if __name__ == "__main__":
    run_sjf_test()