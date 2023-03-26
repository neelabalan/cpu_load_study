from __future__ import annotations

import json
import multiprocessing as mp
import os
from typing import Dict
from typing import List

import psutil
from closed_loop_actuator import ClosedLoopActuator
from controller import ControllerThread
from monitor import MonitorThread


def load_single_core(core_num: int, duration_s: int | float, target_load: float):
    """
    Load single logical core.

    core_num: number of CPU core to put some load on
    duration_s: time period in seconds in which the CPU core will be loaded.
    target_load: CPU load level in fractions of 1
    """
    process = psutil.Process(os.getpid())
    process.cpu_affinity([core_num])

    monitor = MonitorThread(core_num)
    monitor.start()

    control = ControllerThread(target_load)
    control.start()

    actuator = ClosedLoopActuator(control, monitor, duration_s, core_num, target_load)
    actuator.run()

    monitor.running.clear()
    control.running.clear()


def load_all_cores(duration_s: int | float, target_load: float):
    """
    Load all available logical cores.

    duration_s: time period in seconds in which the CPU core will be loaded.
    target_load: CPU load level in fractions of 1
    """

    processes = []
    for core_num in range(mp.cpu_count()):
        process = mp.Process(
            target=load_single_core, args=(core_num, duration_s, target_load)
        )
        processes.append(process)

    for process in processes:
        process.start()

    for process in processes:
        process.join()


def from_profile(path_to_profile_json: str):
    """Run CPU loader from a profile"""

    profile = _read_profile(path_to_profile_json)

    processes = []
    for single_sequence in profile:
        process = mp.Process(
            target=_run_single_sequence,
            args=(
                single_sequence["cpu_num"],
                single_sequence["repeat"],
                single_sequence["sequence"],
            ),
        )
        processes.append(process)

    for process in processes:
        process.start()

    for process in processes:
        process.join()


def _run_single_sequence(core_num: int, repeat: int, sequence: Dict):
    """
    Load single logical core.

    core_num: number of the core on which the load will be put
    repeat: number of iterations a single profile will be run
    sequence: single profile sequence
    """

    process = psutil.Process(os.getpid())
    process.cpu_affinity([core_num])

    monitor = MonitorThread(core_num)
    monitor.start()

    control = ControllerThread(target_cpu_load=0.01)
    control.start()

    actuator = ClosedLoopActuator(
        controller=control,
        monitor=monitor,
        duration_s=0.0,
        cpu_core_num=core_num,
        cpu_target=0.0,
    )

    for _ in range(repeat):
        for single_profile in sequence:
            target_load = single_profile["load"]
            duration_s = single_profile["duration_s"]

            control.target_cpu_load = target_load
            actuator.duration_s = duration_s
            actuator.cpu_target = target_load
            actuator.run()

    monitor.running.clear()
    control.running.clear()


def _read_profile(path_to_profile_json: str) -> List[Dict]:
    """
    Read json CPU load profile file.

    path_to_profile_json: path to CPU load profile json file
    returns: deserialized CPU load profile sequence
    """

    with open(path_to_profile_json, "r") as json_file:
        sequence = json.load(json_file)

    return sequence
