import threading
from sensors import Sensors
from data import Data
from read import TRead
from write import TWrite


class TCli(threading.Thread):
    """A Thread to implement Command Line Interface(CLI)
    """
    def __init__(self, threadID: int, name: str, read: TRead, write: TWrite) -> None:
        """The init method of CLI Thread

        Args:
            threadID (int): Thread ID
            name (str): Thread name
            read (TRead): Reading Thread
            write (TWrite): Writing Thread
        """
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name

        self.sensor_read = read
        self.write_db = write

        self.func = ""
        self.value = []

        self.active = True
        self.flag = False

    def run(self) -> None:
        """(Thread) Run
        """
        print("Threading {} is starting".format(self.name))

        try:
            while self.active:
                print(">", end="")
                while self.sensor_read.timestamp < 0.5:
                    pass
                print("{}, {}", self.sensor_read.ss_fuzzy.SS.u_steady_state, self.sensor_read.ss_fuzzy.SS.x1_past)
                self.func = input()
                if self.func == "q":
                    print("quit")
                    self.sensor_read.kill()
                    self.write_db.kill()
                    self.kill()

                else:
                    try:
                        self.sensor_read.ss_fuzzy.press_fb = float(self.func)
                    except:
                        print("Unknown Command {}".format(self.func))
            print("Threading {} is exiting".format(self.name))

        except KeyboardInterrupt:
            pass

    def kill(self) -> None:
        """(Thread) Kill
        """
        self.active = False
