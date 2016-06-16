import smbus
import time

# SHT31D default address.
SHT31_I2CADDR = 0x44

# SHT31D Registers

SHT31_MEAS_HIGHREP_STRETCH = 0x2C06
SHT31_MEAS_MEDREP_STRETCH = 0x2C0D
SHT31_MEAS_LOWREP_STRETCH = 0x2C10
SHT31_MEAS_HIGHREP = 0x2400
SHT31_MEAS_MEDREP = 0x240B
SHT31_MEAS_LOWREP = 0x2416
SHT31_READSTATUS = 0xF32D
SHT31_CLEARSTATUS = 0x3041
SHT31_SOFTRESET = 0x30A2
SHT31_HEATER_ON = 0x306D
SHT31_HEATER_OFF = 0x3066

SHT31_STATUS_DATA_CRC_ERROR = 0x0001
SHT31_STATUS_COMMAND_ERROR = 0x0002
SHT31_STATUS_RESET_DETECTED = 0x0010
SHT31_STATUS_TEMPERATURE_ALERT = 0x0400
SHT31_STATUS_HUMIDITY_ALERT = 0x0800
SHT31_STATUS_HEATER_ACTIVE = 0x2000
SHT31_STATUS_ALERT_PENDING = 0x8000


class Sht31d(object):
    def __init__(
            self,
            i2c_bus=0,
            sensor_address=SHT31_I2CADDR
    ):
        self.bus = smbus.SMBus(i2c_bus)
        self.sensor_address = sensor_address

    def poll(self):
        sta = 0
        while not sta:
            print("Status: {0}".format(sta))
            sta = self.bus.read_byte_data(self.sensor_address, SHT31_READSTATUS)

    def read_status(self):
        self.write_command(SHT31_READSTATUS)
        buffer = self.bus.read_byte_data(self.sensor_address, 0, 3)
        stat = buffer[0] << 8 | buffer[1]
        if buffer[2] != self.crc8(buffer[0:2]):
            return None
        return stat

    def read_temperature(self):
        success, temp, hum = self.read_temperature_humidity()
        if not success:
            return 0

        return temp

    def read_humidity(self):
        success, temp, hum = self.read_temperature_humidity()
        if not success:
            return 0

        return hum

    def set_heater(self, doEnable=True):
        if doEnable:
            self.write_command(SHT31_HEATER_ON)
        else:
            self.write_command(SHT31_HEATER_OFF)

    def is_heater_active(self):
        return bool(self.read_status() & SHT31_STATUS_HEATER_ACTIVE)

    def read_temperature_humidity(self):
        self.write_command(SHT31_MEAS_HIGHREP)
        time.sleep(0.015)
        buffer = self.bus.read_i2c_block_data(self.sensor_address, 0, 6)

        if buffer[2] != self.crc8(buffer[0:2]):
            return False, float("nan"), float("nan")

        rawTemperature = buffer[0] << 8 | buffer[1]
        temperature = 175.0 * rawTemperature / 0xFFFF - 45.0

        if buffer[5] != self.crc8(buffer[3:5]):
            return False, float("nan"), float("nan")

        rawHumidity = buffer[3] << 8 | buffer[4]
        humidity = 100.0 * rawHumidity / 0xFFFF

        return True, temperature, humidity

    def write_command(self, command):
        self.bus.write_byte_data(
            self.sensor_address,
            command >> 8, command & 0xFF)

    def crc8(self, buffer):
        """ Polynomial 0x31 (x8 + x5 +x4 +1) """

        polynomial = 0x31;
        crc = 0xFF;

        index = 0
        for index in range(0, len(buffer)):
            crc ^= buffer[index]
            for i in range(8, 0, -1):
                if crc & 0x80:
                    crc = (crc << 1) ^ polynomial
                else:
                    crc = (crc << 1)
        return crc & 0xFF
