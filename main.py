#!sudo python3

from os import times
import time
import threading
import sys

import numpy as np

import pigpio

from max6675 import MAX6675

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

from heater_controller import HeaterController

import datetime

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

############
# MAX6675  #
############
pi = pigpio.pi()
max_0 = MAX6675(pi, 0)
max_1 = MAX6675(pi, 1)

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
hc.start(0.3)

############
# INFLUXDB #
############
token = "vMzfHTBmtruTYBaMZHItmwyHhgvGyRwLbRCbyYbdWRdNDdxBx4xrqPDtoIiIkKRWITqLG5JcSfWSLfnA59vsxQ=="
bucket = "Pot"
client = InfluxDBClient(url="http://localhost:8086", token=token, org="NTHU")
write_api = client.write_api(write_options=SYNCHRONOUS)

############
#  PARAMS  #
############
seq = 0
sample_time = 0.25
duration = 0

############
# ---------#
############
_measurement = str(datetime.date.today())
_measurement = "Pot"
start_time = time.time()
stop = start_time + duration

timestamp = 0.0
_temp_0 = 0.0
_temp_1 = 0.0
_volt_0 = 0.0
_volt_1 = 0.0
temp_0 = 0.0
temp_1 = 0.0
press = 0.0
volt_in = 0.0


def input_sign(old_duty, t):
    if 0 < t and t < 5 * 60:
        return 0.6
    else:
        return 0.6


def main() -> None:
    global seq
    global timestamp
    global _temp_0
    global _temp_1
    global _volt_0
    global _volt_1
    global temp_0
    global temp_1
    global press
    global volt_in
    try:
        while True:
            now = time.time()
            if duration > 0 and now >= stop:
                break

            seq += 1
            timestamp = now - start_time

            _temp_0 = float(max_0.read)
            _temp_1 = float(max_1.read)
            _volt_0 = float(ads_0.voltage)
            _volt_1 = float(ads_1.voltage)

            temp_0 = _temp_0 * 0.8129 + 13.534
            temp_1 = _temp_1 * 0.8129 + 13.534
            press = (_volt_0 - 0.5) / 4.0 * 17.0
            volt_in = _volt_1

            # hc.duty = input_sign(hc.duty, timestamp)

            p = (
                Point(_measurement)
                .field("seq", seq)
                .field("timestamp", timestamp)
                .field("_temp_0", _temp_0)
                .field("_temp_1", _temp_1)
                .field("_volt_0", _volt_0)
                .field("_volt_1", _volt_1)
                .field("temp_0", temp_0)
                .field("temp_1", temp_1)
                .field("press", press)
                .field("volt_in", volt_in)
                .field("input_duty", hc.duty)
            )
            # print(
            #     seq,
            #     ", ",
            #     timestamp,
            #     ", ",
            #     _temp_0,
            #     ", ",
            #     _temp_1,
            #     ", ",
            #     _volt_0,
            #     ", ",
            #     _volt_1,
            #     ", ",
            #     temp_0,
            #     ", ",
            #     temp_1,
            #     ", ",
            #     press,
            #     ", ",
            #     volt_in,
            #     ", ",
            #     hc.duty,
            # )

            write_api.write(bucket=bucket, record=p)
            time.sleep((sample_time - (time.time() - start_time)) % sample_time)

    except KeyboardInterrupt:
        print("")


if __name__ == "__main__":
    threading1 = threading.Thread(target=main)
    threading1.daemon = True
    threading1.start()

    # print(
    #     "seq",
    #     ", ",
    #     "timestamp",
    #     ", ",
    #     "_temp_0",
    #     ", ",
    #     "_temp_1",
    #     ", ",
    #     "_volt_0",
    #     ", ",
    #     "_volt_1",
    #     ", ",
    #     "temp_0",
    #     ", ",
    #     "temp_1",
    #     ", ",
    #     "press",
    #     ", ",
    #     "volt_in",
    #     ", ",
    #     "hc.duty",
    # )
    try:
        while True:
            in_str = input().lower()
            try:
                duty = float(in_str)
                hc.duty = duty
                print("set duty to {}".format(hc.duty))
            except:

                if in_str.lower() == "q":
                    pi.spi_close(max_0.sensor)
                    pi.spi_close(max_1.sensor)
                    hc.stop()
                    break
                else:
                    print("input error")
    except KeyboardInterrupt:
        pi.spi_close(max_0.sensor)
        pi.spi_close(max_1.sensor)
        hc.stop()
        sys.exit()
