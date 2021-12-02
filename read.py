import time
import threading
import queue
import datetime

from sensors import Sensors
from data import Data
from controller import SS_Fuzzy


class TRead(threading.Thread):
    def __init__(
        self,
        threadID: int,
        name: str,
        queue: queue.Queue,
        sample_time: float,
        duration: float,
    ) -> None:
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.queue = queue
        self.seq = 0
        self.sensors = Sensors()
        self.start_time = time.time()
        self.duration = duration
        self.sample_time = sample_time
        self.stop_time = self.start_time + self.duration
        self.active = True
        self.timestamp = 0.0

        self.ss_fuzzy = SS_Fuzzy()
        self.ss_fuzzy.setPressSetpoint(8.0)

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
                self.timestamp = data.timestamp

                data.read(self.sensors)
                data.press_fuzzy = self.ss_fuzzy.Fuzzy.press_fb
                data.duty_ss = self.ss_fuzzy.duty_ss
                data.duty_fuzzy = self.ss_fuzzy.Fuzzy.output
                data.idx_strategy = self.ss_fuzzy.idx

                self.sp = 8.0
                self.ss_fuzzy.setPressSetpoint(self.sp)
                self.sensors.hc.duty = self.ss_fuzzy.run(data.timestamp, self.sensors.hc.duty, data.press)

                data.timefinished = time.time() - self.start_time

                if self.seq:
                    self.queue.put(data)

                time.sleep((self.sample_time - (time.time() - self.start_time) % self.sample_time))
        except KeyboardInterrupt:
            pass
        print("Threading {} is exiting".format(self.name))

    def kill(self) -> None:
        self.active = False
        self.sensors.kill()
