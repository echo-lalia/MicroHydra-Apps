import random, json, time, math
from machine import SPI, Pin, PWM, freq, reset, Timer
from lib import st7789py, keyboard, beeper
from font import vga1_8x16 as small_font
from font import vga2_16x32 as big_font
import neopixel


freq(240000000)
ledPin = Pin(21)
led = neopixel.NeoPixel(ledPin, 1, bpp=3)

tft = st7789py.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    135,
    240,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=None,
    rotation=1,
    color_order=st7789py.BGR
    )
blight = PWM(Pin(38, Pin.OUT))
blight.freq(1000)
blight.duty_u16(40000)

kb = keyboard.KeyBoard()
beep = beeper.Beeper()
led = neopixel.NeoPixel(ledPin, 1, bpp=3)

numbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "."]

with open("config.json", "r") as conf:
    config = json.loads(conf.read())
    ui_color = config["ui_color"]
    bg_color = config["bg_color"]
    
def start_timer(time_qty, units):
    time_started = time.time()
    time_amount = float(time_qty)
    seconds_to_count = 0
    if units is "seconds":
        seconds_to_count = time_amount
    elif units is "minutes":
        seconds_to_count = time_amount * 60
    elif units is "hours":
        seconds_to_count = time_amount * 60 * 60

    display = ""
    prev_display = ""
    time_left = seconds_to_count
    
    display_x = random.randint(4, 240 - len("00:00:00")*16 - 16)
    display_y = random.randint(4, 135 - 32 - 4)
    updated = False
    
    dim_timer = time.time()
    dim_countdown = 30
    dimmed = True
    
    prev_pressed_keys = []
    pressed_keys = []
    
    while time_left > 0:
        prev_display = display
        
        time_so_far = time.time() - time_started
        time_left = seconds_to_count - time_so_far
        
        hours = int(time_left // 3600)
        minutes = int((time_left % 3600) // 60)
        seconds = int(time_left % 60)
        
        # update display position every 10 seconds
        if seconds % 10 is 5 and not updated:
            display_x = random.randint(4, 240 - len("00:00:00")*16 - 4)
            display_y = random.randint(4, 135 - 32 - 4)
            updated = True
            
        # reset 10 second timer triggered flag
        if seconds % 10 is 0 and updated:
            updated = False
        
        display = ""
        
        # dim display
        if (time.time() - dim_timer) > dim_countdown:
            blight.duty_u16(22000)
            dimmed = True
            
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if "ESC" in pressed_keys and "ESC" not in prev_pressed_keys:
                return
            dimmed = False
            blight.duty_u16(40000)
            dim_countdown = 30
            dim_timer = time.time()
        
        prev_pressed_keys = pressed_keys
        
        if hours > 0:
            display += f"{int(hours)}:"
        display += f"{minutes:02}:"
        display += f"{seconds:02}"
        
        if display != prev_display and time_left > 0:
            tft.fill(bg_color)
            tft.text(big_font, display, display_x, display_y, ui_color, bg_color)

    blight.duty_u16(40000)
    tft.fill(bg_color)
    tft.text(big_font, "00:00", 120 - len(display)*16//2, 70 - 16, ui_color, bg_color)
    tft.text(small_font, "< any key >", 120 - len(display)*16//2, 118, ui_color, bg_color)
    
    timer = Timer(1, mode=Timer.PERIODIC, period=1000, callback = lambda t: alarm())
    
    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            timer.deinit()
            return
        
        prev_pressed_keys = pressed_keys

def alarm():
    led.fill((255,255,255)); led.write() # set led
    beep.play(("C3","C4","C5"), 100, 0)
    led.fill((0,0,0)); led.write() # set led

def main():
    pressed_keys = kb.get_pressed_keys()
    prev_pressed_keys = pressed_keys
    current_units = "minutes"
    time_value = "0"
    
    redraw = True
    
    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if "h" in pressed_keys and "h" not in prev_pressed_keys and current_units is not "hours":
                current_units = "hours"
            elif 'm' in pressed_keys and 'm' not in prev_pressed_keys and current_units is not "minutes":
                current_units = "minutes"
            elif 's' in pressed_keys and 's' not in prev_pressed_keys and current_units is not "seconds":
                current_units = "seconds"
            elif ',' in pressed_keys and ',' not in prev_pressed_keys: # left
                if current_units is "minutes":
                    current_units = "seconds"
                elif current_units is "hours":
                    current_units = "minutes"
            elif '/' in pressed_keys and '/' not in prev_pressed_keys: # left
                if current_units is "seconds":
                    current_units = "minutes"
                elif current_units is "minutes":
                    current_units = "hours"
            elif "ENT" in pressed_keys and "ENT" not in prev_pressed_keys and time_value is not "0":
                start_timer(time_value, current_units)
                time_value = "0"
                current_units = "minutes"
                redraw = True
            elif "BSPC" in pressed_keys and "BSPC" not in prev_pressed_keys:
                if len(time_value) > 1:
                    time_value = time_value[:-1]
                else:
                    time_value = "0"
            else:
                for key in pressed_keys:
                    if len(key) == 1 and key not in prev_pressed_keys:
                        if key in numbers:
                            if key == "." and "." in time_value:
                                # max 1 decimal point
                                pass
                            elif key == "0" and time_value == "0":
                                # can't keep adding if the first digit it zeros
                                pass
                            else:
                                time_value += key
                                
            if time_value != "0":
                # remove leading 0s
                time_value = time_value.lstrip("0")
                if time_value[0] is ".":
                    time_value = "0" + time_value
            redraw = True
            
        
        if redraw:
            tft.fill(bg_color)
            
            tft.text(big_font, time_value, 120- len(time_value)*16//2, 70 - 16 - 10, ui_color, bg_color)
            tft.text(small_font, current_units, 120 - len(current_units)*8//2, 70 + 24 - 10, ui_color, bg_color)
            
            select = ""
            if current_units is "seconds":
                select += "[ s ] "
            else:
                select += "  s   "
            if current_units is "minutes":
                select += "[ m ] "
            else:
                select += "  m   "
            if current_units is "hours":
                select += "[ h ]"
            else:
                select += "  h  "
            tft.text(small_font, select, 120 - len(select)*8//2, 118, ui_color, bg_color)
            redraw = False
        
        prev_pressed_keys = pressed_keys
        
main()