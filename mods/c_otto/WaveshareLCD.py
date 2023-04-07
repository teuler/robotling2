from machine import Pin,SPI,PWM
import framebuf
import time
import micropython

black =   const(0x0000)
red   =   const(0x07E0)
green =   const(0x001F)
blue  =   const(0xf800)
white =   const(0xffff)
        
class LCD_1inch14(framebuf.FrameBuffer):
          
    _BL         = const (13)
    _DC         = const ( 8)
    _RST        = const (12)
    _MOSI       = const (11)
    _SCK        = const (10)
    _CS         = const ( 9)
    _LCD_width  = const (240)
    _LCD_height = const (135)

        
    def __init__(self):
        self.cs = Pin(_CS,Pin.OUT)
        self.rst = Pin(_RST,Pin.OUT)
        
        self.cs(1)
        self.spi = SPI(1)
        self.spi = SPI(1,1000_000)
        self.spi = SPI(1,10000_000,polarity=0, phase=0,sck=Pin(_SCK),mosi=Pin(_MOSI),miso=None)

        self.dc = Pin(_DC,Pin.OUT)
        self.dc(1)

        self.pwm = PWM(Pin(_BL))
        self.pwm.freq(1000)

        self._buffer = bytearray(_LCD_height * _LCD_width * 2)
        super().__init__(self._buffer, _LCD_width, _LCD_height, framebuf.RGB565)
        self.init_display()
        
        self.keyA = Pin(15,Pin.IN, Pin.PULL_UP)
        self.keyB = Pin(17,Pin.IN, Pin.PULL_UP)
#   self.JoyU = Pin( 2,Pin.IN, Pin.PULL_UP)             bereits für M2 PWM benutzt
        self.JoyD = Pin(18,Pin.IN, Pin.PULL_UP)
        self.JoyL = Pin(16,Pin.IN, Pin.PULL_UP)
        self.JoyR = Pin(20,Pin.IN, Pin.PULL_UP)
#   self.JoyS = Pin( 3,Pin.IN, Pin.PULL_UP)             bereits für D0 auf dem IO-Stecker benutzt
     
    def is_pressed (self, Button):
        return (Button () == 0)
    
    def BUTTON_A(self):
        return self.keyA.value ()
 
    def BUTTON_B(self):
        return self.keyB.value ()
    
    def get_width (self):
        return _LCD_width
    
    def get_height (self):
        return _LCD_height
    
    def write_func (self, cmd, data):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)
        if (len(data)>0):
            self.dc(1)
            self.cs(0)
            self.spi.write(data)
            self.cs(1)

    def init_display(self):
        """Initialize dispaly"""  
        self.rst(1)
        self.rst(0)
        self.rst(1)
        
        self.write_func (0x36, bytes([0x70]))
        self.write_func (0x3A, bytes([0x05]))
        self.write_func (0xB2, bytes([0x0C,0x0C,0x00,0x33,0x33]))
        self.write_func (0xB7, bytes([0x35]))
        self.write_func (0xBB, bytes([0x19]))
        self.write_func (0xC0, bytes([0x2C]))
        self.write_func (0xC2, bytes([0x01]))
        self.write_func (0xC3, bytes([0x12]))
        self.write_func (0xC4, bytes([0x20]))
        self.write_func (0xC6, bytes([0x0F]))
        self.write_func (0xD0, bytes([0xA4,0xA1]))
        self.write_func (0xE0, bytes([0xD0,0x04,0x0D,0x11,0x13,0x2B,0x3F,0x54,0x4C,0x18,0x0D,0x0B,0x1F,0x23]))
        self.write_func (0xE1, bytes([0xD0,0x04,0x0C,0x11,0x13,0x2C,0x3F,0x44,0x51,0x2F,0x1F,0x1F,0x20,0x23]))
        self.write_func (0x21, bytes([]))
        self.write_func (0x11, bytes([]))
        self.write_func (0x29, bytes([]))

    def show(self):
        self.write_func (0x2A, bytes([0x00,0x28,0x01,0x17]))
        self.write_func (0x2B, bytes([0x00,0x35,0x00,0xBB]))
        self.write_func (0x2C, bytes([]))

        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self._buffer)
        self.cs(1)
        
    def LCDfill (self):
        self.fill(self.Pen)
        
    def SetBL (self, value):
        self.pwm.duty_u16(value)

        
if __name__=='__main__':
    micropython.mem_info()

    LCD = LCD_1inch14()
    LCD.SetBL (16384)
    micropython.mem_info()
    LCD.fill(white)
 
    LCD.show()
    LCD.text("Raspberry Pi Pico",60,40,red)
    LCD.text("PicoGo",60,60,green)
    LCD.text("Pico-LCD-1.14",60,80,blue)
    
    LCD.hline(10,10,220,blue)
    LCD.hline(10,125,220,blue)
    LCD.vline(10,10,115,blue)
    LCD.vline(230,10,115,blue)
    
    
    LCD.rect(12,12,20,20,red)
    LCD.rect(12,103,20,20,red)
    LCD.rect(208,12,20,20,red)
    LCD.rect(208,103,20,20,red)
    
    LCD.show()
    key0 = Pin(2 ,Pin.IN, Pin.PULL_UP)
    key1 = Pin(18,Pin.IN, Pin.PULL_UP)
    key2 = Pin(15,Pin.IN, Pin.PULL_UP)
    key3 = Pin(17,Pin.IN, Pin.PULL_UP)
    while(1):
        if(key0.value() == 0):
            LCD.fill_rect(12,12,20,20,red)
        else :
            LCD.fill_rect(12,12,20,20,white)
            LCD.rect(12,12,20,20,red)
            
        if(key1.value() == 0):
            LCD.fill_rect(12,103,20,20,red)
        else :
            LCD.fill_rect(12,103,20,20,white)
            LCD.rect(12,103,20,20,red)
            
        if(key2.value() == 0):
            LCD.fill_rect(208,12,20,20,red)
        else :
            LCD.fill_rect(208,12,20,20,white)
            LCD.rect(208,12,20,20,red)
            
        if(key3.value() == 0):
            LCD.fill_rect(208,103,20,20,red)
        else :
            LCD.fill_rect(208,103,20,20,white)
            LCD.rect(208,103,20,20,red)
            
            
        LCD.show()
    time.sleep(1)
    LCD.fill(0xFFFF)

