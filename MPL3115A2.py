import numpy as np
from smbus import SMBus
from sys import exit

# I2C ADDRESS / BITS
MPL3115A2_ADDRESS = 0x60

# REGISTERS
MPL3115A2_REGISTER_STATUS = 0x00
MPL3115A2_REGISTER_STATUS_TDR = 0x02
MPL3115A2_REGISTER_STATUS_PDR = 0x04
MPL3115A2_REGISTER_STATUS_PTDR = 0x08

MPL3115A2_REGISTER_PRESSURE_CSB = 0x02
MPL3115A2_REGISTER_PRESSURE_LSB = 0x03
MPL3115A2_REGISTER_PRESSURE_MSB = 0x01

MPL3115A2_REGISTER_TEMP_MSB = 0x04
MPL3115A2_REGISTER_TEMP_LSB = 0x05

MPL3115A2_REGISTER_DR_STATUS = 0x06

MPL3115A2_OUT_P_DELTA_MSB = 0x07
MPL3115A2_OUT_P_DELTA_CSB = 0x08
MPL3115A2_OUT_P_DELTA_LSB = 0x09

MPL3115A2_OUT_T_DELTA_MSB = 0x0A
MPL3115A2_OUT_T_DELTA_LSB = 0x0B

MPL3115A2_BAR_IN_MSB = 0x14

MPL3115A2_WHOAMI = 0x0C

# BITS
MPL3115A2_PT_DATA_CFG = 0x13
MPL3115A2_PT_DATA_CFG_TDEFE = 0x01
MPL3115A2_PT_DATA_CFG_PDEFE = 0x02
MPL3115A2_PT_DATA_CFG_DREM = 0x04

MPL3115A2_CTRL_REG1 = 0x26
MPL3115A2_CTRL_REG1_SBYB = 0x01
MPL3115A2_CTRL_REG1_OST = 0x02
MPL3115A2_CTRL_REG1_RST = 0x04
MPL3115A2_CTRL_REG1_OS1 = 0x00
MPL3115A2_CTRL_REG1_OS2 = 0x08
MPL3115A2_CTRL_REG1_OS4 = 0x10
MPL3115A2_CTRL_REG1_OS8 = 0x18
MPL3115A2_CTRL_REG1_OS16 = 0x20
MPL3115A2_CTRL_REG1_OS32 = 0x28
MPL3115A2_CTRL_REG1_OS64 = 0x30
MPL3115A2_CTRL_REG1_OS128 = 0x38
MPL3115A2_CTRL_REG1_RAW = 0x40
MPL3115A2_CTRL_REG1_ALT = 0x80
MPL3115A2_CTRL_REG1_BAR = 0x00
MPL3115A2_CTRL_REG2 = 0x27
MPL3115A2_CTRL_REG3 = 0x28
MPL3115A2_CTRL_REG4 = 0x29
MPL3115A2_CTRL_REG5 = 0x2A

MPL3115A2_REGISTER_STARTCONVERSION = 0x12


class Mpl3115a2(object):
    _bus = None

    def __init__(self, i2c_bus = 0):
        """
        :type i2c_bus: int specifying i2c bus number
        """
        self._bus = SMBus(i2c_bus)
        whoami = self._bus.read_byte_data(MPL3115A2_ADDRESS, MPL3115A2_WHOAMI)

        if whoami != 0xc4:
            print("MPL3115A2 not active.")
            exit(1)

        # Set MPL3115A2 oversampling to 128, put in Barometer mode, enabled standby on CTRL_REG1
        self._bus.write_byte_data(
            MPL3115A2_ADDRESS,
            MPL3115A2_CTRL_REG1,
            MPL3115A2_CTRL_REG1_SBYB |
            MPL3115A2_CTRL_REG1_OS128 |
            MPL3115A2_CTRL_REG1_BAR)

        # Configure MPL3115A2
        self._bus.write_byte_data(
            MPL3115A2_ADDRESS,
            MPL3115A2_PT_DATA_CFG,
            MPL3115A2_PT_DATA_CFG_TDEFE |
            MPL3115A2_PT_DATA_CFG_PDEFE |
            MPL3115A2_PT_DATA_CFG_DREM)

    def poll(self):
        sta = 0
        while not (sta & MPL3115A2_REGISTER_STATUS_PDR):
            sta = self._bus.read_byte_data(MPL3115A2_ADDRESS, MPL3115A2_REGISTER_STATUS)

    def altitude(self):
        # print "Reading Altitude Data..."
        self._bus.write_byte_data(
            MPL3115A2_ADDRESS,
            MPL3115A2_CTRL_REG1,
            MPL3115A2_CTRL_REG1_SBYB |
            MPL3115A2_CTRL_REG1_OS128 |
            MPL3115A2_CTRL_REG1_ALT)  # change to altimeter mode

        self.poll()

        msb, csb, lsb = self._bus.read_i2c_block_data(MPL3115A2_ADDRESS, MPL3115A2_REGISTER_PRESSURE_MSB, 3)
        # print msb, csb, lsb

        alt = float((((msb << 24) | (csb << 16) | lsb) * 10) / 65536)

        # correct sign
        if alt > (1 << 15):
            alt -= 1 << 16

        return alt

    def pressure(self):
        # print "Reading Pressure Data..."
        self._bus.write_byte_data(
            MPL3115A2_ADDRESS,
            MPL3115A2_CTRL_REG1,
            MPL3115A2_CTRL_REG1_SBYB |
            MPL3115A2_CTRL_REG1_OS128 |
            MPL3115A2_CTRL_REG1_BAR)  # change to barometer mode

        self.poll()

        msb, csb, lsb = self._bus.read_i2c_block_data(MPL3115A2_ADDRESS, MPL3115A2_REGISTER_PRESSURE_MSB, 3)
        # print msb, csb, lsb

        return ((msb << 16) | (csb << 8) | lsb) / 64.

    def calibrate(self):
        # print "Calibrating..."
        p = 0
        t = 0
        a = 0
        calibration_rounds = 5

        for _i in np.arange(0, calibration_rounds, 1):
            p += self.pressure()
            t += self.temperature()
            a += self.altitude()
            print("Calibration Round: {0} of {1}".format(_i, calibration_rounds))

        pa = int((p / 10) / 2)
        ta = (t / 10)
        aa = (a / 10)

        self._bus.write_i2c_block_data(MPL3115A2_ADDRESS, MPL3115A2_BAR_IN_MSB, [pa >> 8 & 0xff, pa & 0xff])

        return [pa, ta, aa]

    def temperature(self):
        # print "Reading Temperature Data..."

        self._bus.write_byte_data(
            MPL3115A2_ADDRESS,
            MPL3115A2_CTRL_REG1,
            MPL3115A2_CTRL_REG1_SBYB |
            MPL3115A2_CTRL_REG1_OS128 |
            MPL3115A2_CTRL_REG1_BAR)

        self.poll()

        t_data = self._bus.read_i2c_block_data(MPL3115A2_ADDRESS, 0x04, 2)
        # status = _bus.read_byte_data(MPL3115A2_ADDRESS, 0x00)

        # print t_data

        return t_data[0] + (t_data[1] >> 4) / 16.0
