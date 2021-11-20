import threading
from sensors import Sensors
from data import Data
from read import TRead
from write import TWrite


class TCli(threading.Thread):
    def __init__(self, threadID: int, name: str, read: TRead, write: TWrite) -> None:
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

        self.sensor_read = read
        self.write_db = write

        self.func = ""
        self.value = []

        self.active = True

    def run(self) -> None:
        print("Threading {} is starting".format(self.name))

        try:
            while self.active:
                print(">", end="")
                self.func = input()
                if self.func == "q":
                    print("quit")
                    self.sensor_read.kill()
                    self.write_db.kill()
                    self.kill()
                elif self.func == "w":
                    print("press kp is {}".format(self.sensor_read.controller.kp_press))
                    print("press ki is {}".format(self.sensor_read.controller.ki_press))
                    print("temp kp is {}".format(self.sensor_read.controller.kp_temp))
                    print("temp ki is {}".format(self.sensor_read.controller.ki_temp))

                else:
                    try:
                        self.sensor_read.ss_fuzzy.press_fb = float(self.func)
                        print("Press SetPoint is {}".format(self.sensor_read.controller.setpoint_press))
                        print("Press FB is {}".format(self.sensor_read.controller.press_fb))
                        print("Press FB Linear is {}".format(self.sensor_read.controller.press_fb_n))
                        print("Temp SetPoint is {}".format(self.sensor_read.controller.setpoint_temp))
                        print("Temp FB is {}".format(self.sensor_read.controller.temp_fb))
                        print("Temp FB Linear is {}".format(self.sensor_read.controller.temp_fb_n))
                        print("Duty is {}".format(self.sensor_read.controller.duty))
                        print("Duty is {}".format(self.sensor_read.sensors.hc.duty))
                    except ValueError:
                        print("Unknown Command {}".format(self.func))
            print("Threading {} is exiting".format(self.name))

        except KeyboardInterrupt:
            pass

    def kill(self) -> None:
        self.active = False
