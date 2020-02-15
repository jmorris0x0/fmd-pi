# -*- coding: utf-8 -*-

import time
import sys
import spidev


class HoneywellHSC:
    def __init__(self):
        self.OUTPUT_MIN = 1638.4     # 1638 counts (10% of 2^14 counts or 0x0666)
        self.OUTPUT_MAX = 14745.6    # 14745 counts (90% of 2^14 counts or 0x3999)
        self.PRESSURE_MIN = 0        # min is 0 for sensors that give absolute values
        self.PRESSURE_MAX = 258.575  # 5 psi in mmHg 
        max_speed_hz = 10000
        bus = 0
        channel = 0
        self.spi = self.open_spi(bus, channel, max_speed_hz)


    def open_spi(self, bus, channel, speed):
        spi = spidev.SpiDev()
        spi.open(bus, channel)
        spi.max_speed_hz = speed

        return spi


    def get_data(self):
        dataBytes = self.spi.readbytes(4)
        status = dataBytes[0] & 192
        pressure_counts = dataBytes[0] << 8 | dataBytes[1];
        temp = dataBytes[2] << 3 | dataBytes[3] >> 5
        real_temp = (float(temp) * 200 / 2047) - 50; # Convert digital value to °C
        real_pressure = self.counts_2_pressure(pressure_counts)

        return [status, round(real_temp, 2), round(real_pressure, 2)]


    def counts_2_pressure(self, counts):
        pressure = (counts - self.OUTPUT_MIN) * (self.PRESSURE_MAX - self.PRESSURE_MIN) / \
                   (self.OUTPUT_MAX - self.OUTPUT_MIN) + self.PRESSURE_MIN

        return pressure


    def get_pressure(self):
        return self.get_data()[2]


    def get_temp(self):
        return self.get_data()[1]


    def print_data_stream(self):
        while True:
            data = self.get_data()
            sys.stdout.write("Temp °C: " + str(data[1]) + "  mmHg: " + str(data[2]) + "\r")
            sys.stdout.flush()
            time.sleep(0.01)


#foo = HoneywellHSC()
#foo.print_data_stream()

