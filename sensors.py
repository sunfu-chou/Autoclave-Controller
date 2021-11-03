import typing

from max6675 import MAX6675

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from heater_controller import HeaterController


class Sensors:
    def __init__(self) -> None:
        self.max_0 = MAX6675(0)
        self.max_1 = MAX6675(1)
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(self.i2c)
        self.ads_0 = AnalogIn(self.ads, ADS.P0)
        self.ads_1 = AnalogIn(self.ads, ADS.P1)
        self.hc = HeaterController(12, 0.25)
        self.hc.start(0.0)

    def read(self) -> typing.Tuple[float, float, float, float, float]:
        return (
            self.max_0.read,
            self.max_1.read,
            self.ads_0.voltage,
            self.ads_1.voltage,
            self.hc.duty,
        )

    def kill(self) -> None:
        self.max_0.kill()
        self.max_1.kill()
        self.hc.kill()
