#! python3 
# sudo python -m debugpy --listen 0.0.0.0:64825 --wait-for-client ./main_thread.py

import queue

from read import TRead
from write import TWrite
from cli import TCli


def main():
    data_q = queue.Queue()
    read = TRead(1, "read_sensors", data_q, 0.25, 0)
    write = TWrite(2, "write", data_q)
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

    print("Done")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
