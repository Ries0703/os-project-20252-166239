"""FCFS algorithm implementation."""

from .strategy import FCFSSchedulerStrategy

STRATEGY = FCFSSchedulerStrategy()

__all__ = ["FCFSSchedulerStrategy", "STRATEGY"]
