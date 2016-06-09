#!/usr/bin/python
import time
import sys
import numpy as np
import Adafruit_SSD1306
import Image
import ImageDraw
import ImageFont
from smbus import SMBus
from sys import exit

# Special characters
deg = u'\N{DEGREE SIGN}'

# Raspberry Pi pin configuration for display:
RST = "22"

# I2C ADDRESS / BITS
MPL3115A2_ADDRESS = 0x60
SSD1306_ADDRESS = 0x3C
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


class DisplayWrapper:
    _display = None
    _draw = None
    _image = None
    _font = None
    _height = 0
    _width = 0

    def __init__(self):
        # 128x32 display with hardware I2C:
        self._display = Adafruit_SSD1306.SSD1306_128_32(rst=RST, i2c_bus=0)
        # Initialize library.
        self._display.begin()
        # Clear display.
        self._display.clear()
        self._display.display()
        # Create blank image for drawing.
        # Make sure to create image with mode '1' for 1-bit color.
        self._width = self._display.width
        self._height = self._display.height
        self._image = Image.new('1', (self._width, self._height))
        # Get drawing object to draw on image.
        self._draw = ImageDraw.Draw(self._image)
        # Load default font.
        self._font = ImageFont.load_default()

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    def clearDisplay(self):
        self._draw.rectangle((0, 0, self._width, self._height), outline=0, fill=0)

    def drawText(self, texttowrite, x, y):
        self._draw.text((x, y), texttowrite, font=self._font, fill=255)

    def displayImage(self):
        self._display.image(self._image)
        self._display.display()


_bus = SMBus(0)

whoami = _bus.read_byte_data(MPL3115A2_ADDRESS, MPL3115A2_WHOAMI)

if whoami != 0xc4:
    print("MPL3115A2 not active.")
    exit(1)

# Set MPL3115A2 oversampling to 128, put in Altimeter mode, enabled standby on CTRL_REG1
_bus.write_byte_data(
    MPL3115A2_ADDRESS,
    MPL3115A2_CTRL_REG1,
    MPL3115A2_CTRL_REG1_SBYB |
    MPL3115A2_CTRL_REG1_OS128 |
    MPL3115A2_CTRL_REG1_ALT)

# Configure MPL3115A2
_bus.write_byte_data(
    MPL3115A2_ADDRESS,
    MPL3115A2_PT_DATA_CFG,
    MPL3115A2_PT_DATA_CFG_TDEFE |
    MPL3115A2_PT_DATA_CFG_PDEFE |
    MPL3115A2_PT_DATA_CFG_DREM)


def poll():
    #    print "Polling..."
    sta = 0
    while not (sta & MPL3115A2_REGISTER_STATUS_PDR):
        sta = _bus.read_byte_data(MPL3115A2_ADDRESS, MPL3115A2_REGISTER_STATUS)


def altitude():
    # print "Reading Altitude Data..."
    _bus.write_byte_data(
        MPL3115A2_ADDRESS,
        MPL3115A2_CTRL_REG1,
        MPL3115A2_CTRL_REG1_SBYB |
        MPL3115A2_CTRL_REG1_OS128 |
        MPL3115A2_CTRL_REG1_ALT)  # change to altimeter mode

    poll()

    msb, csb, lsb = _bus.read_i2c_block_data(MPL3115A2_ADDRESS, MPL3115A2_REGISTER_PRESSURE_MSB, 3)
    # print msb, csb, lsb

    alt = float((((msb << 24) | (csb << 16) | (lsb)) * 10) / 65536)

    # correct sign
    if alt > (1 << 15):
        alt -= 1 << 16

    return alt


def pressure():
    # print "Reading Pressure Data..."
    _bus.write_byte_data(
        MPL3115A2_ADDRESS,
        MPL3115A2_CTRL_REG1,
        MPL3115A2_CTRL_REG1_SBYB |
        MPL3115A2_CTRL_REG1_OS128 |
        MPL3115A2_CTRL_REG1_BAR)  # change to barometer mode

    poll()

    msb, csb, lsb = _bus.read_i2c_block_data(MPL3115A2_ADDRESS, MPL3115A2_REGISTER_PRESSURE_MSB, 3)
    # print msb, csb, lsb

    return ((msb << 16) | (csb << 8) | lsb) / 64.


def calibrate():
    # print "Calibrating..."
    p = 0
    t = 0
    a = 0

    for i in np.arange(1, 6, 1):
        p = p + pressure()
        t = t + temperature()
        a = a + altitude()
        # print "p: "+str(p)+" t: "+str(t)

    pa = int((p / 10) / 2)
    ta = (t / 10)
    aa = (a / 10)
    _bus.write_i2c_block_data(MPL3115A2_ADDRESS, MPL3115A2_BAR_IN_MSB, [pa >> 8 & 0xff, pa & 0xff])

    return [pa, ta, aa]


def temperature():
    # print "Reading Temperature Data..."

    _bus.write_byte_data(
        MPL3115A2_ADDRESS,
        MPL3115A2_CTRL_REG1,
        MPL3115A2_CTRL_REG1_SBYB |
        MPL3115A2_CTRL_REG1_OS128 |
        MPL3115A2_CTRL_REG1_BAR)

    poll()

    t_data = _bus.read_i2c_block_data(MPL3115A2_ADDRESS, 0x04, 2)
    #status = _bus.read_byte_data(MPL3115A2_ADDRESS, 0x00)

    # print t_data

    return t_data[0] + (t_data[1] >> 4) / 16.0


dw = DisplayWrapper()

try:
    # Draw a black filled box to clear the image.
    dw.clearDisplay()
    # draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Draw some shapes.
    # First define some constants to allow easy resizing of shapes.
    padding = 2
    shape_width = 20
    top = padding
    bottom = dw.height() - padding
    # Move left to right keeping track of the current x position for drawing shapes.
    x = 5

    dw.clearDisplay()
    dw.drawText('Calibrating...', x, top)
    dw.displayImage()

    calibrate()

    i = 0

    while 1:
        # get readings
        tempC = temperature()  # temp in Celcius
        tempF = (tempC * 1.8) + 32
        press = (pressure() / 1000)  # get pressure and convert to kPa
        # clear display
        dw.clearDisplay()
        # draw readings to image
        dw.drawText('TempC: ' + "{0:.2f}".format(tempC) + deg + ' C', x, top)
        dw.drawText('TempF: ' + "{0:.2f}".format(tempF) + deg + ' F', x, top + 10)
        dw.drawText('Pressure: ' + "{0:.2f}".format(press) + ' kPa', x, top + 20)
        # Display image.
        dw.displayImage()

except OSError as err:
    print("OS Error: {0}".format(err))
    dw.clearDisplay()
    dw.displayImage()
    sys.exit(1);
except KeyboardInterrupt:
    print("Keyboard Interrupt detected")
    dw.clearDisplay()
    dw.displayImage()
    sys.exit(0);
