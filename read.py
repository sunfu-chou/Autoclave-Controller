import time
import threading
import queue

from sensors import Sensors
from data import Data
import datetime


class TRead(threading.Thread):
    def __init__(
        self,
        threadID: int,
        name: str,
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
        print("Threading {} is starting".format(self.name))
        try:
            while self.active:
                now = time.time()
                if self.duration > 0 and now > self.stop_time:
                    break

                data = Data(datetime.datetime.utcnow())

                self.seq += 1
                data.seq = self.seq
                data.timestamp = now - self.start_time

                data.read(self.sensors)

                data.timefinished = time.time() - self.start_time

                # self.lock.acquire()
                self.queue.put(data)
                # self.lock.release()

                time.sleep((self.sample_time - (time.time() - self.start_time) % self.sample_time))
        except KeyboardInterrupt:
            pass
        print("Threading {} is exiting".format(self.name))

    def kill(self) -> None:
        self.active = False
