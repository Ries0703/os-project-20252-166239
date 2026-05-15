"""Shortest Job First algorithm implementation."""

from .strategy import SJFSchedulerStrategy

STRATEGY = SJFSchedulerStrategy()

__all__ = ["SJFSchedulerStrategy", "STRATEGY"]