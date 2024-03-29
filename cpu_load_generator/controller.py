import time
from threading import Event
from threading import Thread


class ControllerThread(Thread):
    """Controller of the CPU status"""

    def __init__(self, target_cpu_load: float, sampling_interval: float = 0.1):
        super(ControllerThread, self).__init__()

        self._target_cpu_load = (
            target_cpu_load  # target CPU load should be provided as input
        )
        self._sampling_interval = sampling_interval

        self.sleep_time_s = 0.0
        self.running = Event()

        # it is the frequency at which the controller sends control signals to the
        # actuator, which is the device that physically adjusts the process variable.
        self._actuation_period = 0.1  # in seconds

        self._alpha_filter_coefficient = 0.2  # filter coefficient
        self._current_cpu_load = 0  # current CPU load returned from the Monitor thread
        self._cpu_period_s = 0.03
        self._integral_const_pi_regulator = 0.2  # integral constant of th PI regulator
        self._prop_const_pi_reg = 0.2  # proportional constant of the PI regulator
        self._integral_error = 0  # integral error

    @property
    def cpu(self) -> float:
        """Get the current CPU load.

        returns: current cpu load

        """
        return self._current_cpu_load

    @property
    def target_cpu_load(self) -> float:
        """Get the target CPU load.

        returns: target CPU load

        """
        return self._target_cpu_load

    @target_cpu_load.setter
    def target_cpu_load(self, load: float):
        """Set target CPU load.

        param load: set target CPU load
        type load: float

        """
        self._target_cpu_load = load

    @cpu.setter
    def cpu(self, value: float):
        """
        Set the current CPU load.
        first-order low-pass filter with exponential smoothing
        This filtered value can then be used as a more stable and smoothed representation
        of the CPU load, which is less susceptible to noise or random fluctuations.
        """
        # first order filter on the measurement samples
        self._current_cpu_load = (
            self._alpha_filter_coefficient * value
            + (1 - self._alpha_filter_coefficient) * self._current_cpu_load
        )

    def run(self):
        """Start and run the Controller thread."""
        self.running.set()
        last_time_stamp = time.time()

        while self.running.is_set():
            time.sleep(self._sampling_interval)
            # computes the proportional error
            # P_error = Kp * (setpoint - process_variable)
            err = self._target_cpu_load - self._current_cpu_load * 0.01

            current_time_stamp = time.time()
            sample_interval_s = current_time_stamp - last_time_stamp
            self._integral_error = self._integral_error + err * sample_interval_s
            last_time_stamp = current_time_stamp
            self._cpu_period_s = (
                self._prop_const_pi_reg * err
                + self._integral_const_pi_regulator * self._integral_error
            )

            # anti wind up control
            if self._cpu_period_s < 0:
                self._cpu_period_s = 0
                self._integral_error = self._integral_error - err * sample_interval_s
            if self._cpu_period_s > self._actuation_period:
                self._cpu_period_s = self._actuation_period
                self._integral_error = self._integral_error - err * sample_interval_s

            self.sleep_time_s = self._actuation_period - self._cpu_period_s
