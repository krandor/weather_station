#!/usr/bin/python
import sys
import threading
import time
from MPL3115A2 import Mpl3115a2
from SSD1306 import Ssd1306
from TSL2591 import Tsl2591


class GetSensorReadingsThread(threading.Thread):
    def __init__(self, mpl3115a2, tsl2591):
        self.tempC = 0
        self.tempF = 0
        self.pressure = 0
        self.lux = 0
        self.tw = mpl3115a2
        self.lw = tsl2591
        super(GetSensorReadingsThread, self).__init__()

    def run(self):
        self.tempC = self.tw.temperature()  # temp in Celcius
        self.tempF = (self.tempC * 1.8) + 32
        self.pressure = (self.tw.pressure() / 1000)  # get pressure and convert to kPa
        full, ir = self.lw.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
        print("full: {0} ir: {1}".format(full, ir))
        self.lux = self.lw.calculate_lux(full, ir)  # convert raw values to lux
        time.sleep(3)

# Globals
textToWrite = ''

# Special characters
deg = u'\N{DEGREE SIGN}'

dw = Ssd1306()
tw = Mpl3115a2()
lw = Tsl2591()

try:
    # Draw a black filled box to clear the image.
    dw.clearDisplay()
    # draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Draw some shapes.
    # First define some constants to allow easy resizing of shapes.
    padding = 2
    shape_width = 20
    top = padding
    bottom = dw.height - padding
    # Move left to right keeping track of the current x position for drawing shapes.
    x = 5

    dw.clearDisplay()
    dw.drawText('Calibrating...', x, top)
    dw.displayImage()

    tw.calibrate()

    i = 0
    x_max = dw.width
    x = x_max

    sensor_thread = None
    tempC = 0
    tempF = 0
    press = 0
    lux = 0

    while 1:
        image_width = dw.imageWidth()
        thread_count = threading.activeCount()
        if x <= (-1 * (x_max + image_width)):
            x = x_max

        if thread_count == 1:
            sensor_thread = GetSensorReadingsThread(tw, lw)
            sensor_thread.start()

        if sensor_thread is not None:
            tempC = sensor_thread.tempC
            tempF = sensor_thread.tempF
            press = sensor_thread.pressure
            sensor_lux = sensor_thread.lux
            if sensor_lux != 0:
                lux = sensor_lux

        # draw readings to image
        textToWrite = 'TempC: ' + "{0:.2f}".format(tempC) + deg + 'C '
        textToWrite += 'TempF: ' + "{0:.2f}".format(tempF) + deg + 'F '
        textToWrite += 'Pressure: ' + "{0:.2f}".format(press) + ' kPa '
        textToWrite += 'Luminosity: ' + "{0:.2f}".format(lux) + ' Lux '

        # clear display
        dw.clearDisplay()
        dw.drawText(textToWrite, x, top + 10)
        # Display image.
        dw.displayImage()
        print("x: {0}".format(x))
        print("{0:.2f} wide".format(image_width))
        print("threads: {0}".format(thread_count))
        print("{0:.2f}".format(tempC) + deg + 'C ')
        print("{0:.2f}".format(tempF) + deg + 'F ')
        print("{0:.2f}".format(press) + ' kPa ')
        print("{0:.2f} Lux".format(lux))

        x -= 1

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
