#!sudo python3

import os
import time
import threading
import queue
import datetime

import data

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


class TWrite(threading.Thread):
    def __init__(self, threadID: int, name: str, queue: queue.Queue) -> None:
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.queue = queue
        self.active = True

        self.filename = filename = "./data/" + datetime.datetime.today().strftime("%m%d_%H%M%S") + ".csv"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.f = open(filename, "w")
        print("file touched:", filename)
        self.f.write(data.Data().title())

        self.token = "vMzfHTBmtruTYBaMZHItmwyHhgvGyRwLbRCbyYbdWRdNDdxBx4xrqPDtoIiIkKRWITqLG5JcSfWSLfnA59vsxQ=="
        self.bucket = "Pot"
        self.client = InfluxDBClient(url="http://localhost:8086", token=self.token, org="NTHU")
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)

    def run(self) -> None:
        print("Threading {} is starting".format(self.name))

        try:
            while self.active:
                while self.queue.qsize() > 0:
                    data = self.queue.get()
                    self.f.write(data.__str__())
                    self.write_api.write(bucket=self.bucket, record=data.to_point())

                time.sleep(2)
            self.f.close()
        except KeyboardInterrupt:
            self.f.close()
        self.f.close()
        print("Threading {} is exiting".format(self.name))

    def kill(self) -> None:
        self.active = False
