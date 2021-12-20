import typing

from max6675 import MAX6675
import pigpio

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from heater_controller import HeaterController


class Sensors:
    """An integration for all sensor
    """
    def __init__(self) -> None:
        self.pi = pigpio.pi()
        self.max_0 = MAX6675(self.pi, 0)
        self.max_1 = MAX6675(self.pi, 1)
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c)
        self.ads_0 = AnalogIn(self.ads, ADS.P0)
        self.ads_1 = AnalogIn(self.ads, ADS.P1)
        self.hc = HeaterController(self.pi, 12, 0.25)
        self.hc.start(0.0)

    def read(self) -> typing.Tuple[float, float, float, float, float]:
        """To read all sensor data

        Returns:
            typing.Tuple[float, float, float, float, float]: temperature 0, temperature 1, ADC Volt 0, ADC Volt 1, Output dutucycle 1
        """
        return (
            float(self.max_0.read),
            float(self.max_1.read),
            float(self.ads_0.voltage),
            float(self.ads_1.voltage),
            float(self.hc.duty),
        )

    def kill(self) -> None:
        """To stop all sensors
        """
        self.max_0.kill()
        self.max_1.kill()
        self.hc.kill()
