import time
import threading
import queue
import datetime

from sensors import Sensors
from data import Data
from controller import SS_Fuzzy


class TRead(threading.Thread):
    """A thread for reading data and controlling in 4Hz(period 0.25s)
    """
    def __init__(
        self,
        threadID: int,
        name: str,
        queue: queue.Queue,
        sample_time: float = 0.25,
        duration: float = 0,
    ) -> None:
        """The init method of reading Thread

        Args:
            threadID (int): Thread ID
            name (str): Thread name
            queue (queue.Queue): Data for communication between Threads
            sample_time (float, optional): The sample period for reading data and controlling. Defaults to 0.25.
            duration (float, optional): Heatint duration. Defaults to 0.
        """
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
        self.ss_fuzzy.setPressSetpoint(6.0)

    def run(self) -> None:
        """(Thread) Run
        """
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

                self.sp = 6.0
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
        """(Thread) kill
        """
        self.active = False
        self.sensors.kill()
