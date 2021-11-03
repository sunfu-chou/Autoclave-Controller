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
                else:
                    try:
                        self.sensor_read.sensors.hc.setpoint_press = float(self.func)
                        print("set Press SetPoint to {}".format(self.sensor_read.sensors.hc.setpoint_press))
                        print("Temp SetPoint is {}".format(self.sensor_read.sensors.hc.setpoint_temp))
                        print("Error Press is {}".format(self.sensor_read.sensors.hc.error_press))
                        print("Error Temp is {}".format(self.sensor_read.sensors.hc.error_temp))
                        print("Duty is {}".format(self.sensor_read.sensors.hc.duty))
                    except ValueError:
                        print("Unknown Command {}".format(self.func))
            print("Threading {} is exiting".format(self.name))

        except KeyboardInterrupt:
            pass

    def kill(self) -> None:
        self.active = False
