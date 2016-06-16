import Adafruit_SSD1306
import Image
import ImageDraw
import ImageFont

# I2C ADDRESS / BITS
SSD1306_ADDRESS = 0x3C


class Ssd1306(object):
    _display = None
    _draw = None
    _image = None
    _font = None
    _height = 0
    _width = 0

    def __init__(self, i2c_bus = 0, ssd1306_rst = "22"):
        """
        :type i2c_bus: int specifying i2c bus number
        :type ssd1306_rst: string specifying GPIO pin for RST
        """
        # 128x32 display with hardware I2C:
        self._display = Adafruit_SSD1306.SSD1306_128_32(rst=ssd1306_rst, i2c_bus=i2c_bus)
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

    def imageWidth(self):
        width, height = self._image.size
        return width
