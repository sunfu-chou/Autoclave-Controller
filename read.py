import time
import threading
import queue
import datetime

from sensors import Sensors
from data import Data
from controller import Controller


class TRead(threading.Thread):
    def __init__(
        self,
        threadID: int,
        name: str,
        queue: queue.Queue,
        sensors: Sensors,
        sample_time: float,
        duration: float,
    ) -> None:
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.queue = queue
        self.seq = 0
        self.sensors = sensors
        self.start_time = time.time()
        self.duration = duration
        self.sample_time = sample_time
        self.stop_time = self.start_time + self.duration
        self.active = True
        self.controller = Controller()

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

                # PID
                self.controller.press_fb = data.press
                self.controller.temp_fb = data.temp_0
                self.sensors.hc.duty = self.controller.PID()
                # self.controller.press_fb_n = self.controller.PressLUT(self.controller.press_fb)
                # self.controller.temp_fb_n = self.controller.TempLUT(data.temp_0)

                # SS
                # self.controller.press_fb = self.controller.PressLUT(data.press)
                # self.sensors.hc.duty = self.controller.SS(data.timestamp, self.sensors.hc.duty)

                data.timefinished = time.time() - self.start_time
                if self.seq:
                    self.queue.put(data)

                time.sleep((self.sample_time - (time.time() - self.start_time) % self.sample_time))
        except KeyboardInterrupt:
            pass
        print("Threading {} is exiting".format(self.name))

    def kill(self) -> None:
        self.active = False
