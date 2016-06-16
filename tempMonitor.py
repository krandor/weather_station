#!/usr/bin/python
import sys
import threading
import time
from MPL3115A2 import Mpl3115a2
from SSD1306 import Ssd1306
from TSL2591 import Tsl2591
from SHT31D import Sht31d


class GetSensorReadingsThread(threading.Thread):
    def __init__(self, mpl3115a2, tsl2591, sht31d):
        self.tempC = 0
        self.tempF = 0
        self.pressure = 0
        self.lux = 0
        self.hum = 0
        self.tw = mpl3115a2
        self.lw = tsl2591
        self.hw = sht31d
        super(GetSensorReadingsThread, self).__init__()

    def run(self):
        self.tempC = self.tw.get_temperature()  # temp in Celsius
        self.tempF = (self.tempC * 1.8) + 32  # convert Celsius to Fahrenheit
        self.pressure = (self.tw.get_pressure() / 1000)  # get pressure and convert to kPa
        full, ir = self.lw.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)
        self.lux = self.lw.calculate_lux(full, ir)  # convert raw values to lux
        self.hum = self.hw.read_humidity()  # get humidity
        time.sleep(1)

# Globals
textToWrite = ''
# Special characters
deg = u'\N{DEGREE SIGN}'

_display_wrapper = Ssd1306()  # Display Wrapper
_temp_and_press_wrapper = Mpl3115a2()  # Temperature/Pressure Wrapper
_luminosity_wrapper = Tsl2591()  # Luminosity Wrapper
_humidity_wrapper = Sht31d()  # Humidity Wrapper

try:
    # Draw a black filled box to clear the image.
    _display_wrapper.clear_display()
    # draw.rectangle((0, 0, width, height), outline=0, fill=0)

    # Draw some shapes.
    # First define some constants to allow easy resizing of shapes.
    padding = 2
    shape_width = 20
    top = padding
    bottom = _display_wrapper.height - padding
    # Move left to right keeping track of the current x position for drawing shapes.
    x = 5

    _display_wrapper.clear_display()
    _display_wrapper.draw_text('Calibrating...', x, top)
    _display_wrapper.display_image()

    _temp_and_press_wrapper.calibrate()

    #display related vars
    # i = 0
    x_max = _display_wrapper.width
    x = x_max
    text_width = 0

    #sensor related vars
    sensor_thread = None
    tempC = 0
    tempF = 0
    press = 0
    lux = 0
    hum = 0

    while 1:
        image_width = _display_wrapper.image_width()
        thread_count = threading.activeCount()

        if x <= (-1 * (text_width + x_max)):
            x = x_max

        if thread_count == 1:
            sensor_thread = GetSensorReadingsThread(_temp_and_press_wrapper, _luminosity_wrapper, _humidity_wrapper)
            sensor_thread.start()

        if sensor_thread is not None:
            sensor_tempC = sensor_thread.tempC
            sensor_tempF = sensor_thread.tempF
            sensor_press = sensor_thread.pressure
            sensor_hum = sensor_thread.hum
            sensor_lux = sensor_thread.lux

            if sensor_lux != 0:
                lux = sensor_lux

            if sensor_hum != 0:
                hum = sensor_hum

            if sensor_tempC != 0:
                tempC = sensor_tempC

            if sensor_tempF != 0:
                tempF = sensor_tempF

            if sensor_press != 0:
                press = sensor_press

        # draw readings to image
        textToWrite = 'TempC: ' + "{0:.2f}".format(tempC) + deg + 'C '
        textToWrite += 'TempF: ' + "{0:.2f}".format(tempF) + deg + 'F '
        textToWrite += 'Humidity: ' + "{0:.2f}".format(hum) + '% '
        textToWrite += 'Pressure: ' + "{0:.2f}".format(press) + ' kPa '
        textToWrite += 'Luminosity: ' + "{0:.2f}".format(lux) + ' Lux '

        text_width = _display_wrapper.get_text_width(textToWrite)

        # clear display
        _display_wrapper.clear_display()
        _display_wrapper.draw_text(textToWrite, x, top + 10)
        # Display image.
        _display_wrapper.display_image()

        print("x: {0}".format(x))
        print("x_max: {0}".format(x_max))
        print("Image Width: {0:.2f} wide".format(image_width))
        print("Text Width: {0:.2f} wide".format(text_width))
        print("Threads: {0}".format(thread_count))
        print("TempC: {0:.2f}".format(tempC) + deg + 'C ')
        print("TempF: {0:.2f}".format(tempF) + deg + 'F ')
        print('Humidity: ' + "{0:.2f}".format(hum) + '% ')
        print("Pressure: {0:.2f}".format(press) + ' kPa ')
        print("Luminosity: {0:.2f} Lux".format(lux))

        x -= 1

except OSError as err:
    print("OS Error: {0}".format(err))
    _display_wrapper.clear_display()
    _display_wrapper.display_image()
    sys.exit(1);
except KeyboardInterrupt:
    print("Keyboard Interrupt detected")
    _display_wrapper.clear_display()
    _display_wrapper.display_image()
    sys.exit(0);
