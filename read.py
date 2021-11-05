import time
import threading
import queue
import bisect

from sensors import Sensors
from data import Data
import datetime


class Controller:
    def __init__(self):
        # PID
        self.press_fb = 0.0
        self.temp_fb = 0.0
        self.setpoint_press = 0.0
        self.integrated_press = 0.0
        self.error_press = 0.0
        self.kp_press = 1.0
        self.ki_press = 0.0007
        self.kd_press = 0.0

        self.setpoint_temp = 0.0
        self.integrated_temp = 0.0
        self.error_temp = 0.0
        self.kp_temp = 2.0
        self.ki_temp = 0.0004
        self.kd_temp = 0.0

        self.bp_press = [0.4782, 0.6701, 1.045, 1.6158, 2.3332, 3.4363, 3.8378, 4.3367, 6.4171, 9.4081]
        self.table_press = [-1.7934, -2.2213, -2.6226, -3.2101, -3.78, -4.4052, -4.5385, -4.7455, -5.4985, -6.2973]
        self.bp_temp = [
            30.1872595638511,
            31.6409528432436,
            31.9704263189301,
            42.179105008502,
            63.6552080230948,
            63.6898877078096,
            63.7978469738978,
            64.4951212851203,
            85.4914717116415,
            111.485040539424,
            113.59430155581,
            113.695598993841,
            129.212866342344,
            139.138331793732,
            140.406275335562,
            144.483082776884,
            145.130889411771,
            151.665873380536,
            165.504586356226,
            165.547908995439,
        ]
        self.table_temp = [
            -2.40592041889992,
            -2.40193714475503,
            -1.96606164384795,
            -1.88280410083362,
            -1.83294240935630,
            -1.77167222675508,
            -1.70512504336492,
            -1.53387209202276,
            -1.26307193253703,
            -1.25128960532926,
            -1.22594106279314,
            -0.721695991192625,
            -0.328835604819290,
            -0.313099765124867,
            -0.306065933410559,
            -0.299478277011540,
            -0.0826493895778796,
            0.252424838633181,
            0.264867254792093,
            0.335251202542455,
        ]

        # SS
        self.x1_past = 0
        self.x2_past = 0
        self.x3_past = 0
        self.x4_past = 0
        self.x5_past = 0
        self.x6_past = 0

        self.u_steady_state = 0.1608
        self.x1_steady_state = 2.72e06
        self.x2_steady_state = -1.017e05
        self.x3_steady_state = 0.143
        self.x4_steady_state = -0.1844
        self.x5_steady_state = 0.1021
        self.x6_steady_state = 0.3129
        self.K1 = 6.850961097434739e-04
        self.K2 = -3.013769863835386e-04
        self.K3 = -2.284484679905255e-06
        self.K4 = 3.968114400173553e-07
        self.K5 = -1.949292918375381e-07
        self.K6 = 2.397509518509175e-07
        self.x1 = 0.0
        self.x2 = 0.0
        self.x3 = 0.0
        self.x4 = 0.0
        self.x5 = 0.0
        self.x6 = 0.0

        self.feedback = 0.0
        # deplicated below
        self.x1_past = 0.0
        self.x2_past = 0.0
        self.x3_past = 0.0
        self.x4_past = 0.0
        self.x5_past = 0.0
        self.x6_past = 0.0

    def PID(self):
        self.error_press = self.setpoint_press - self.press_fb
        self.integrated_press += self.error_press * 0.25

        self.setpoint_temp = self.kp_press * self.error_press + self.ki_press * self.integrated_press

        self.error_temp = self.setpoint_temp - self.temp_fb
        self.integrated_temp += self.error_temp * 0.25
        self.duty = self.kp_temp * self.error_temp + self.ki_temp * self.integrated_temp

    def setPressLUT(self, press):
        idx = bisect.bisect_left(self.bp_press, press)
        self.press_fb = self.table_press[idx - 1] + (self.table_press[id] - self.table_press[id - 1]) * (
            press - self.bp_press[id - 1]
        ) / (self.bp_press[id] - self.bp_press[id - 1])
        return self.press_fb

    def setTempLUT(self, temp):
        idx = bisect.bisect_left(self.bp_temp, temp)
        self.temp_fb = self.table_temp[idx - 1] + (self.table_temp[id] - self.table_temp[id - 1]) * (
            temp - self.bp_temp[id - 1]
        ) / (self.bp_temp[id] - self.bp_temp[id - 1])
        return self.temp_fb

    def SS(self, timestamp, duty):
        if timestamp < 0.2:
            self.x1_past = 0
            self.x2_past = 0
            self.x3_past = 0
            self.x4_past = 0
            self.x5_past = 0
            self.x6_past = 0

        self.x1 = 0.999920615899239 * self.x1_past + 1121.76082548340 * duty
        self.x2 = 0.998226013220676 * self.x2_past + (-1121.48468411130) * duty
        self.x3 = (-0.781914434948314) * self.x3_past + 1.58439928733227 * duty
        self.x4 = (-0.384411449265331) * self.x4_past + (-1.58739336744947) * duty
        self.x5 = 0.131101849447955 * self.x5_past + 0.326002234363228 * self.x6_past + (-0.0828234008843126) * duty
        self.x6 = (-0.326002234363228) * self.x5_past + 0.131101849447955 * self.x6_past + 1.89755072155957 * duty

        self.feedback = (-1) * (
            self.K1 * (self.x1 - self.x1_steady_state)
            + self.K2 * (self.x2 - self.x2_steady_state)
            + self.K3 * (self.x3 - self.x3_steady_state)
            + self.K4 * (self.x4 - self.x4_steady_state)
            + self.K5 * (self.x5 - self.x5_steady_state)
            + self.K6 * (self.x6 - self.x6_steady_state)
        )
        self.x1_past = self.x1
        self.x2_past = self.x2
        self.x3_past = self.x3
        self.x4_past = self.x4
        self.x5_past = self.x5
        self.x6_past = self.x6

        duty = self.feedback + self.u_steady_state
        return duty


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
                # self.controller.setPressLUT(data.press)
                # self.controller.setTempLUT(data.temp_0)
                # self.sensors.hc.duty = self.controller.PID()

                # SS
                self.sensors.hc.duty = self.controller.SS(data.timestamp, self.sensors.hc.duty)

                data.timefinished = time.time() - self.start_time

                self.queue.put(data)

                time.sleep((self.sample_time - (time.time() - self.start_time) % self.sample_time))
        except KeyboardInterrupt:
            pass
        print("Threading {} is exiting".format(self.name))

    def kill(self) -> None:
        self.active = False
