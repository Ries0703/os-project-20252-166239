"""Round Robin algorithm implementation."""

from .strategy import DEFAULT_RR_QUANTUM, RoundRobinSchedulerStrategy

STRATEGY = RoundRobinSchedulerStrategy()

__all__ = ["DEFAULT_RR_QUANTUM", "RoundRobinSchedulerStrategy", "STRATEGY"]
