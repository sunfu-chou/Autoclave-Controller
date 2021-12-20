import time
import pigpio


class MAX6675:
    "An implemetation for communication to MAX6675"

    def __init__(self, pi: pigpio.pi, cs: int = 0) -> None:
        """The init method of MAX6675

        Args:
            pi (pigpio.pi): pigpio handler
            cs (int, optional): chip select channel. Defaults to 0.
        """
        self.cs = cs
        self.pi = pi
        self.sensor = self.pi.spi_open(cs, 1000000, 0)
        self.t = time.time()
        self._temp = 0.0
        self._raw_data = [0, 0]
        self.read

    def kill(self) -> None:
        """To stop MAX6675
        """
        self.pi.spi_close(self.sensor)

    @property
    def read(self) -> float:
        """To read MAX6675 temperature

        Returns:
            float: The temperature MAX6675 read
        """
        if time.time() - self.t < 0.22:
            return self._temp
        self.t = time.time()
        n_bits, self._raw_data = self.pi.spi_read(self.sensor, 2)
        ret = 0.0
        if n_bits == 2:
            self._temp = (self._raw_data[0] << 8) | self._raw_data[1]
            if self.available:
                ret = (self._temp >> 3) / 4.0
        return ret

    @property
    def available(self) -> bool:
        """To check if data is available

        Returns:
            bool: Is data available
        """
        if (self._temp & 0x8006) == 0:
            return True
        if self._raw_data[0] & 0x80:
            # print("MSB error")
            return False
        if self._raw_data[1] & 0x04:
            # print("Thermocouple Connection error")
            return False
        if self._raw_data[1] & 0x02:
            # print("Device ID error")
            return False
        if self._raw_data[1] & 0x01:
            # print("Tri-state error")
            return False

    def __str__(self) -> str:
        return "{:d} {} {:08b} {:08b}".format(self.cs, self.available, self._raw_data[0], self._raw_data[1])
