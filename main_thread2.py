#!sudo python3

import time
import threading
import queue

from sensors import Sensors
from data import Data
from read import TRead
from write import TWrite
from cli import TCli


def main():

    sensors = Sensors()

    data_q = queue.Queue()
    read = TRead(1, "read_sensors", data_q, sensors, 0.25, 0)
    write = TWrite(2, "write", data_q, "./main_thread2_data/test.csv")
    cli = TCli(3, "cli", read, write)

    read.daemon = True
    write.daemon = True
    cli.daemon = True

    read.start()
    write.start()
    cli.start()

    try:
        read.join()
        write.join()
        cli.join()
    except KeyboardInterrupt:
        read.kill()
        write.kill()
        cli.kill()

    sensors.kill()
    print("Done")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
