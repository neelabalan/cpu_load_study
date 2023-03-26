from __future__ import annotations
import time

import os
import psutil


class ClosedLoopActuator:
    """Generates CPU load by tuning the sleep time."""

    def __init__(self, controller, monitor, duration_s, cpu_core_num, cpu_target):
        self._controller = controller
        self._monitor = monitor
        self._duration_s = duration_s
        self._cpu_core_num = cpu_core_num
        self._cpu_target = cpu_target

        self._actuation_period = 0.05

    @property
    def duration_s(self) -> float | int:
        """Get CPU load duration"""
        return self._duration_s

    @duration_s.setter
    def duration_s(self, duration_s: float | int):
        """Set duration of CPU load"""
        self._duration_s = duration_s

    @property
    def cpu_target(self) -> float:
        """Get CPU load target"""
        return self._cpu_target

    @cpu_target.setter
    def cpu_target(self, target_cpu_load: float):
        """Set target CPU load"""
        self._cpu_target = target_cpu_load

    def run(self):
        process = psutil.Process(os.getpid())
        process.cpu_affinity([self._cpu_core_num])
        start_time = time.time()

        while (time.time() - start_time) <= self._duration_s:
            self._controller.cpu = self._monitor.current_cpu_load
            sleep_time = self._controller.sleep_time_s
            self._generate_load(sleep_time)

    def _generate_load(self, sleep_time):
        """Generate some CPU load during time period."""
        interval = time.time() + self._actuation_period - sleep_time
        # generates some load
        counter = 213123
        while time.time() < interval:
            counter * counter
            counter = counter + 1
        # controller actuation
        time.sleep(sleep_time)
