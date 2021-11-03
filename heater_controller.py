"""heater_controller.py
    Brief:
        An inplementation of pigpio for control pwm in non-blocking mode.
    
         _____
        /  /::\       ___           ___
       /  /:/\:\     /  /\         /  /\
      /  /:/  \:\   /  /:/        /  /:/
     /__/:/ \__\:| /__/::\       /  /:/
     \  \:\ /  /:/ \__\/\:\__   /  /::\
      \  \:\  /:/     \  \:\/\ /__/:/\:\
       \  \:\/:/       \__\::/ \__\/  \:\
        \  \::/        /__/:/       \  \:\
         \__\/         \__\/         \__\/
    
    Author:
        sunfu.chou (sunfu.chou@gmail.com)
    Version:
        0.2.1
    Date:
        2021-05-27

"""
import pigpio


def _constrain(num, min, max):
    """Constrain a number within [min, max].

    Args:
        num (int | float): the number should be constrained.
        min (int | float): minimum.
        max (int | float): maximum.

    Returns:
        int| float: the constrained number.
    """
    if num < min:
        return min
    if num > max:
        return max
    return num


class HeaterController:
    """A encapsulation of pigpio for control pwm in non-blocking mode."""

    # The max value of duty cycle range.
    DUTY_RANGE = int(1e6)

    def __init__(self, pin: int, freq: int = int(1e5), exceptions: bool = True) -> "HeaterController":
        """The init method of HeaterController.

        Args:
            pin (int): The BCM pin number of pwm.
            freq (int, optional): The frequency of pwm. Defaults to int(1e5).
            exceptions (bool, optional): If pigpio raise exceptions. Defaults to True.
        """
        self._pin = pin
        self._freq = int(freq)
        self._duty = 0

        self.pi = pigpio.pi()
        pigpio.exceptions = exceptions
        self.pi.set_mode(self._pin, pigpio.OUTPUT)
        self.pi.callback(self._pin, pigpio.RISING_EDGE, self._callback)

        self.setpoint_press = 0.0
        self.integrated_press = 0.0
        self.error_press = 0.0
        self.kp_press = 1
        self.ki_press = 0.0007
        self.kd_press = 0.0

        self.setpoint_temp = 0.0
        self.integrated_temp = 0.0
        self.error_temp = 0.0
        self.kp_temp = 2.0
        self.ki_temp = 0.0004
        self.kd_temp = 0.0

    def kill(self) -> None:
        self.stop()

    def _callback(self, pin: int = None, level: int = None, tick: int = None) -> int:
        """The callback function used to control pwm.

        Args:
            pin (int, optional): The GPIO which has changed state. Defaults to None.
            level (int optional): 0 = change to low (a falling edge)
                                  1 = change to high (a rising edge)
                                  2 = no level change (a watchdog timeout).
                                  Defaults to None.
            tick (int, optional): The number of microseconds since boot
                                  WARNING: this wraps around from
                                  4294967295 to 0 roughly every 72 minutes.
                                  Defaults to None.

        """
        if self._pin not in [12, 13, 18, 19]:
            return -1
        self._freq = int(_constrain(self._freq, 1, 187.5e6))
        self._duty = _constrain(self._duty, 0.0, 1.0)

        return self.pi.hardware_PWM(
            self._pin,
            int(self._freq),
            int(self._duty * self.DUTY_RANGE),
        )

    def start(self, duty: float = 0.0) -> int:
        """To start generating pwm.

        Args:
            duty (float, optional): duty cycle in ratio.(0.0 - 1.0) Defaults to 0.0.

        Returns:
            pigpio error code.
        """
        self._duty = duty
        return self._callback(self._pin)

    def stop(self) -> int:
        """To stop generating pwm.

        Returns:
            pigpio error code.
        """
        self._duty = 0
        self._callback(self._pin)
        ret = self.pi.set_mode(self._pin, pigpio.INPUT)
        self.pi.stop()
        return ret

    @property
    def pin(self) -> int:
        """To get pwm pin.

        Returns:
            int: The pwm pin.
        """
        return self._pin

    @property
    def freq(self) -> int:
        """To get pwm frequency.

        Returns:
            int: The pwm frequency.
        """
        return self._freq

    @property
    def duty(self) -> float:
        """To get pwm duty cycle.

        Returns:
            float: The pwm duty cycle.(0.0 - 1.0)
        """
        return self._duty

    @pin.setter
    def pin(self, pin: int) -> int:
        """To set pwm pin.

        Args:
            pin (int): pwm pin.

        Returns:
            pigpio error code.
        """
        self.pi.set_mode(self._pin, pigpio.INPUT)
        self._pin = pin
        self.pi.set_mode(self._pin, pigpio.OUTPUT)
        return self._callback(self._pin)

    @freq.setter
    def freq(self, freq: int) -> int:
        """To set pwm frequency.

        Args:
            freq (int): The frequency of pwm.

        Returns:
            pigpio error code.
        """
        self._freq = freq
        return self._callback(self._pin)

    @duty.setter
    def duty(self, duty: float) -> int:
        """To set pwm duty cycle.

        Args:
            duty (float): duty cycle in ratio.(0.0 - 1.0)

        Returns:
            pigpio error code.
        """
        self._duty = duty
        return self._callback(self._pin)
