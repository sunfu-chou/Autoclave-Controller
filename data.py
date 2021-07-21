#!sudo python3

from influxdb_client import Point
from sensors import Sensors
import datetime


class Data:
    def __init__(self, now = datetime.datetime.utcnow(), sensors: Sensors = Sensors()) -> None:
        self.seq = 0
        self.timestamp = 0.0
        self.raw_temp_0 = 0.0
        self.raw_temp_1 = 0.0
        self.raw_volt_0 = 0.0
        self.raw_volt_1 = 0.0
        self.temp_0 = 0.0
        self.temp_1 = 0.0
        self.press = 0.0
        self.volt_in = 0.0
        self.duty = 0.0
        self.timefinished = 0.0
        self.now = now
        self.sensors = sensors

    def __str__(self) -> str:
        return "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(
            self.seq,
            self.timestamp,
            self.timefinished,
            self.raw_temp_0,
            self.raw_temp_1,
            self.raw_volt_0,
            self.raw_volt_1,
            self.temp_0,
            self.temp_1,
            self.press,
            self.volt_in,
            self.duty,
        )

    def title(self) -> str:
        return "{}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {}\n".format(
            "seq",
            "timestamp",
            "timefinished",
            "raw_temp_0",
            "raw_temp_1",
            "raw_volt_0",
            "raw_volt_1",
            "temp_0",
            "temp_1",
            "press",
            "volt_in",
            "duty",
        )

    def read(self, sensors: Sensors) -> None:
        (
            self.raw_temp_0,
            self.raw_temp_1,
            self.raw_volt_0,
            self.raw_volt_1,
            self.duty,
        ) = sensors.read()

        self.temp_0 = self.raw_temp_0 * 0.8129 + 13.534
        self.temp_1 = self.raw_temp_1 * 0.8129 + 13.534
        self.press = (self.raw_volt_0 - 0.5) / 4.0 * 17.0
        self.volt_in = self.raw_volt_1

    def to_point(self, measurement: str = "Pot") -> Point:
        return (
            Point(measurement)
            .field("seq", self.seq)
            .field("timestamp", self.timestamp)
            .field("timefinished", self.timefinished)
            .field("raw_temp_0", self.raw_temp_0)
            .field("raw_temp_1", self.raw_temp_1)
            .field("raw_volt_0", self.raw_volt_0)
            .field("raw_volt_1", self.raw_volt_1)
            .field("temp_0", self.temp_0)
            .field("temp_1", self.temp_1)
            .field("press", self.press)
            .field("volt_in", self.volt_in)
            .field("input_duty", self.duty)
            .time(self.now)
        )
