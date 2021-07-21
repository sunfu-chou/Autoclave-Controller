#!sudo python3

import os
import time
import threading
import typing
import queue

import numpy as np
from numpy.distutils.conv_template import parse_string

import pigpio

from max6675 import MAX6675

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from heater_controller import HeaterController

import datetime

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS, WriteApi, WriteType


class Sensors:
    def __init__(
        self,
        max_0: MAX6675,
        max_1: MAX6675,
        ads_0: AnalogIn,
        ads_1: AnalogIn,
        hc: HeaterController,
    ) -> None:
        self.max_0 = max_0
        self.max_1 = max_1
        self.ads_0 = ads_0
        self.ads_1 = ads_1
        self.hc = hc

    def read(self) -> typing.Tuple[float, float, float, float, float]:
        return (
            self.max_0.read,
            self.max_1.read,
            self.ads_0.voltage,
            self.ads_1.voltage,
            self.hc.duty,
        )


class Data:
    def __init__(self, now=datetime.datetime.utcnow()) -> None:
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

    def to_point(self, measurement="Pot") -> Point:
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


class SensorRead(threading.Thread):
    def __init__(
        self,
        threadID,
        name,
        lock: threading.Lock,
        queue: queue.Queue,
        sensors: Sensors,
        start_time: float,
        duration: float,
        sample_time: float,
    ) -> None:
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.lock = lock
        self.queue = queue
        self.seq = 0
        self.sensors = sensors
        self.start_time = start_time
        self.duration = duration
        self.sample_time = sample_time
        self.stop_time = self.start_time + self.duration
        self.active = True

    def run(self) -> None:
        try:
            while self.active:
                now = time.time()
                data = Data(datetime.datetime.utcnow())
                if self.duration > 0 and now > self.stop_time:
                    break

                self.seq += 1
                data.seq = self.seq
                data.timestamp = now - self.start_time

                (
                    data.raw_temp_0,
                    data.raw_temp_1,
                    data.raw_volt_0,
                    data.raw_volt_1,
                    data.duty,
                ) = self.sensors.read()

                data.temp_0 = data.raw_temp_0 * 0.8129 + 13.534
                data.temp_1 = data.raw_temp_1 * 0.8129 + 13.534
                data.press = (data.raw_volt_0 - 0.5) / 4.0 * 17.0
                data.volt_in = data.raw_volt_1
                data.timefinished = time.time() - self.start_time
                self.lock.acquire()
                self.queue.put(data)
                self.lock.release()
                time.sleep((self.sample_time - (time.time() - self.start_time) % self.sample_time))
        except KeyboardInterrupt:
            pass
        print("{} is exiting".format(self.name))

    def kill(self) -> None:
        self.active = False


class WriteDB(threading.Thread):
    def __init__(
        self,
        threadID,
        name,
        lock: threading.Lock,
        queue: queue.Queue,
        write_api: WriteApi,
        bucket,
        filename,
    ) -> None:
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.lock = lock
        self.queue = queue
        self.write_api = write_api
        self.bucket = bucket
        self.f = open(self.get_file_name("./data/data.csv"), "w")
        self.active = True
        # print(Data().title())
        self.f.write(Data().title())

    def run(self) -> None:
        try:
            while self.active:
                while self.queue.qsize() > 0:
                    self.lock.acquire()
                    data = self.queue.get()
                    # print(data)
                    self.f.write(data.__str__())
                    self.write_api.write(bucket=self.bucket, record=data.to_point())
                    self.lock.release()

                time.sleep(2)
            self.f.close()
        except KeyboardInterrupt:
            self.f.close()
        print("{} is exiting".format(self.name))

    def kill(self) -> None:
        self.active = False

    def get_file_name(self, old_filename, start=1):
        if os.path.isfile(old_filename):
            filename = os.path.splitext(old_filename)[0]
            extension = os.path.splitext(old_filename)[1]
            new_filename = f"{filename}_{str(start)}{extension}"
            if os.path.isfile(new_filename):
                new_filename = self.get_file_name(old_filename, start + 1)
        else:
            new_filename = old_filename
        return new_filename


class Cli(threading.Thread):
    def __init__(self, threadID, name, sensor_read: SensorRead, write_db) -> None:
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.func = ""
        self.value = []
        self.active = True
        self.sensor_read = sensor_read
        self.write_db = write_db

    def run(self) -> None:
        try:
            while self.active:
                print(">", end="")
                self.func = input()
                if self.func == "q":
                    print("quit")
                    self.sensor_read.kill()
                    self.write_db.kill()
                    self.kill()
                else:
                    try:
                        self.sensor_read.sensors.hc.duty = float(self.func)
                        print("set duty to {}".format(self.sensor_read.sensors.hc.duty))
                    except ValueError:
                        pass
            print("{} is exiting".format(self.name))

        except KeyboardInterrupt:
            pass

    def kill(self) -> None:
        self.active = False


def main():

    ############
    # MAX6675  #
    ############
    # pi = pigpio.pi()
    max_0 = MAX6675(0)
    max_1 = MAX6675(1)

    ############
    # ADS1115  #
    ############
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    ads_0 = AnalogIn(ads, ADS.P0)
    ads_1 = AnalogIn(ads, ADS.P1)

    ############
    #   PWM    #
    ############
    hc = HeaterController(12, 10e3)
    hc.start(0.0)

    ############
    # INFLUXDB #
    ############
    token = "vMzfHTBmtruTYBaMZHItmwyHhgvGyRwLbRCbyYbdWRdNDdxBx4xrqPDtoIiIkKRWITqLG5JcSfWSLfnA59vsxQ=="
    bucket = "Pot"
    client = InfluxDBClient(url="http://localhost:8086", token=token, org="NTHU")
    write_api = client.write_api(write_options=SYNCHRONOUS)

    sensors = Sensors(max_0, max_1, ads_0, ads_1, hc)

    data_q = queue.Queue()
    lock = threading.Lock()
    sensor_read = SensorRead(1, "sensor_read", lock, data_q, sensors, time.time(), 0, 0.25)
    write_db = WriteDB(2, "write_db", lock, data_q, write_api, bucket, "/home/ubuntu/pot/0901.csv")
    cli = Cli(3, "cli", sensor_read, write_db)

    sensor_read.daemon = True
    write_db.daemon = True
    cli.daemon = True
    sensor_read.start()
    write_db.start()
    cli.start()

    try:
        sensor_read.join()
        write_db.join()
        cli.join()
    except KeyboardInterrupt:
        sensor_read.kill()
        write_db.kill()
        cli.kill()

    max_0.kill()
    max_1.kill()
    hc.stop()
    print("Done")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
