#!sudo python3

import os
import time
import threading
import queue

import data

from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS


class TWrite(threading.Thread):
    def __init__(self, threadID: int, name: str, lock: threading.Lock, queue: queue.Queue, filename: str) -> None:
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.lock = lock
        self.queue = queue
        self.f = open(self.get_file_name(filename), "w")
        self.active = True
        # print(Data().title())
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
                    # self.lock.acquire()
                    data = self.queue.get()
                    # print(data)
                    self.f.write(data.__str__())
                    self.write_api.write(bucket=self.bucket, record=data.to_point())
                    # self.lock.release()

                time.sleep(2)
            self.f.close()
        except KeyboardInterrupt:
            self.f.close()
        self.f.close()
        print("Threading {} is exiting".format(self.name))

    def kill(self) -> None:
        self.active = False

    def get_file_name(self, old_filename: str, start: int = 1):
        if os.path.isfile(old_filename):
            filename = os.path.splitext(old_filename)[0]
            extension = os.path.splitext(old_filename)[1]
            new_filename = f"{filename}_{str(start)}{extension}"
            if os.path.isfile(new_filename):
                new_filename = self.get_file_name(old_filename, start + 1)
        else:
            new_filename = old_filename
        return new_filename
