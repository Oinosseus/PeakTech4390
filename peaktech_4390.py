#!/usr/bin/env python3

import serial
import time
import sys
import argparse

class DataPacket(object):


    def __init__(self, raw_data_packet):
        self.__rawdata = raw_data_packet
        self.__reset_values()
        self.decodeRawData()


    def __reset_values(self):
        self.Unit  = ""
        self.Value = 0.0
        self.AC    = False
        self.DC    = False
        self.Auto  = False
        self.USB   = False


    def bcd2int(self, bcd_value):
        bcd_value = bcd_value & 0x7f

        def a2b(a):
            b = 0
            for i in a:
                b |= (1 << i)
            return b

        if bcd_value == a2b([0, 2, 3, 4, 5, 6]):
            return 0
        elif bcd_value == a2b([0, 2]):
            return 1
        elif bcd_value == a2b([4, 0, 1, 6, 3]):
            return 2
        elif bcd_value == a2b([4, 0, 2, 3, 1]):
            return 3
        elif bcd_value == a2b([5, 1, 0, 2]):
            return 4
        elif bcd_value == a2b([4, 5, 1, 2, 3]):
            return 5
        elif bcd_value == a2b([4, 5, 6, 3, 2, 1]):
            return 6
        elif bcd_value == a2b([4, 0, 2]):
            return 7
        elif bcd_value == a2b([0, 1, 2, 3, 4, 5, 6]):
            return 8
        elif bcd_value == a2b([3, 2, 0, 4, 5, 1]):
            return 9
        else:
            raise ValueError("Cannot convert 0x%02x BCD value to int" % bcd_value)


    def decodeRawData(self):
        self.__reset_values()

        # raw data check
        if len(self.__rawdata) != 10 or self.__rawdata[:2] != [0xa5, 0xa5]:
            print("Wrong Packet:", self.__rawdata)
            return

        # Byte 2L
        if self.__rawdata[2] & (1 << 3):
            self.AC = True
        if self.__rawdata[2] & (1 << 2):
            self.DC = True
        if self.__rawdata[2] & (1 << 1):
            self.Auto = True
        if self.__rawdata[2] & (1 << 0):
            self.USB = True

        # determine digits of the value
        Digit3 = (self.__rawdata[2] & 0xf0) | (self.__rawdata[3] & 0x0f)
        Digit2 = (self.__rawdata[3] & 0xf0) | (self.__rawdata[4] & 0x0f)
        Digit1 = (self.__rawdata[4] & 0xf0) | (self.__rawdata[5] & 0x0f)
        Digit0 = (self.__rawdata[5] & 0xf0) | (self.__rawdata[6] & 0x0f)
        self.Value = self.bcd2int(Digit3) * 10**3 + self.bcd2int(Digit2) * 10**2 + self.bcd2int(Digit1) * 10**1 + self.bcd2int(Digit0) * 10**0

        # determine decimal divider and sign
        if Digit0 & 0x80:
            self.Value /= 10
        if Digit1 & 0x80:
            self.Value /= 100
        if Digit2 & 0x80:
            self.Value /= 1000
        if Digit3 & 0x80:
            self.Value *= -1

        # determine unit prefix
        if self.__rawdata[6] & (1 << 7):
            self.Unit += "n"
        if self.__rawdata[3] & (1 << 7):
            self.Unit += "u"
        if self.__rawdata[7] & (1 << 7):
            self.Unit += "m"
        if self.__rawdata[7] & (1 << 1):
            self.Unit += "k"
        if self.__rawdata[7] & (1 << 5):
            self.Unit += "M"


        # determine unit
        if self.__rawdata[6] & (1 << 6):
            self.Unit = "Ohm"
        if self.__rawdata[7] & (1 << 6):
            self.Unit = "%"
        if self.__rawdata[7] & (1 << 2):
            self.Unit = "F"
        if self.__rawdata[8] & (1 << 7):
            self.Unit = "degF"
        if self.__rawdata[8] & (1 << 6):
            self.Unit = "degC"
        if self.__rawdata[8] & (1 << 3):
            self.Unit = "A"
        if self.__rawdata[8] & (1 << 2):
            self.Unit = "V"
        if self.__rawdata[8] & (1 << 1):
            self.Unit = "Hz"


def b2i(bytes):
    return int.from_bytes(bytes, byteorder='big')



def wait4packet(serdev):

    # wait for sync
    raw_packet = [0, 0]
    while True:
        byte = serdev.read(1)

        if len(byte) > 0:
            raw_packet.pop(0)
            raw_packet.append(b2i(byte))

        if raw_packet == [0xa5, 0xa5]:
            break

    # read data
    for i in range(8):
        raw_packet.append(b2i(serdev.read(1)))

    # create data packet object
    return DataPacket(raw_packet)



def main():

    # -------------------------------------------------------------------------
    #                               argparse
    # -------------------------------------------------------------------------

    # program description
    description  = "Data logging from PeakTech 4390 multimeter.\n "
    description += "To store output in a file: '" + __file__ + " | tee log.csv'"

    # create parser
    parser = argparse.ArgumentParser(description=description)

    # device option
    parser.add_argument('-d', '--device', action="store",
                        default="/dev/ttyUSB0", type=str,
                        help="This is the ttyUSB device of the multimeter (default: /dev/ttyUSB0)")

    # parse
    args = parser.parse_args()



    # -------------------------------------------------------------------------
    #                               main loop
    # -------------------------------------------------------------------------

    time_start = time.time()
    with serial.Serial(args.device, baudrate=4800, timeout=1) as serdev:

        while True:
            data_packet = wait4packet(serdev)
            time_passed = time.time() - time_start

            data_string  = ""
            data_string += "%0.4f, s" % time_passed
            data_string += ", "
            data_string += str(data_packet.Value) + ", " + data_packet.Unit

            print(data_string)
            sys.stdout.flush()



if __name__ == "__main__":
    main()
