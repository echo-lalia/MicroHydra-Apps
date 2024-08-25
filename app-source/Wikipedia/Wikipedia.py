import requests, network, time, math, json
from machine import SPI, Pin, PWM, freq, reset
from lib.display import Display
from lib.userinput import UserInput
from lib.hydra.config import Config
from lib.device import Device
from font import vga1_8x16 as font
import neopixel

"""
A simple app to query Wikipedia for page summaries.

v1.2

Changes:
Fixed brightness, modified to use mhconfig

"""

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Function Definitions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def dotted_hline(tft, y_position, color):
    for i in range(4,220,4):
        tft.pixel(i,y_position, color)

# ~~~~~~~~~~~~~~~~~~~~~~~~~ global objects/vars ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
freq(240000000)

if "CARDPUTER" in Device:
    ledPin = Pin(21)
    led = neopixel.NeoPixel(ledPin, 1, bpp=3)

tft = Display()

config = Config()

kb = UserInput()

nic = network.WLAN(network.STA_IF)



# ~~~~~~~~~~~~~~~~~~~~~~~~~fetch article~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def user_query():
    tft.fill(config['bg_color'])
    tft.text("Enter query:", 72, 4, config['ui_color'], font=font)
    tft.show()
    
    current_value = ''
    
    pressed_keys = kb.get_pressed_keys()
    prev_pressed_keys = pressed_keys
    
    redraw = True
    
    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if ("GO" in pressed_keys and "GO" not in prev_pressed_keys) or ("ENT" in pressed_keys and "ENT" not in prev_pressed_keys): # confirm settings
                return current_value.replace(' ','_')
            
            elif 'BSPC' in pressed_keys and 'BSPC' not in prev_pressed_keys:
                current_value = current_value[0:-1]
                redraw = True
            elif 'SPC' in pressed_keys and 'SPC' not in prev_pressed_keys:
                current_value = current_value + ' '
                redraw = True
            elif "ESC" in pressed_keys and "ESC" not in prev_pressed_keys:
                reset()
            else:
                for key in pressed_keys:
                    if len(key) == 1 and key not in prev_pressed_keys:
                        current_value += key
                    redraw = True
        
        # graphics!
        if redraw:
            tft.rect(12, 59, 216, 64, config['bg_color'], fill=True)
            if len(current_value) <= 30:
                tft.text(current_value, 120 - (len(current_value) * 4), 75, config['ui_color'], font=font)
            else:
                tft.text(current_value[0:30], 24, 59, config['ui_color'], font=font)
                tft.text(current_value[30:], 120 - (len(current_value[12:]) * 4), 91, config['ui_color'], font=font)

            
            tft.show()
            redraw = False

        prev_pressed_keys = pressed_keys
    
    
    
    
def fetch_article():
    
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + user_query()
    if url == "https://en.wikipedia.org/api/rest_v1/page/summary/":
        url = "https://en.wikipedia.org/api/rest_v1/page/random/summary/"
    
    if "CARDPUTER" in Device:
        led.fill((10,0,0)); led.write() # set led
    
    tft.fill(config['bg_color'])
    tft.text('Connecting to WIFI...', 36, 30, config['ui_color'], font=font)
    tft.show()
    
    if not nic.active(): # turn on wifi if it isn't already
        nic.active(True)
    
    if "CARDPUTER" in Device:
        led.fill((10,10,0)); led.write() # set led
    
    if not nic.isconnected(): # try connecting
        try:
            nic.connect(config['wifi_ssid'], config['wifi_pass'])
        except OSError as e:
            print("Had this error when connecting:",e)
    
    
    
    while not nic.isconnected():
        time.sleep_ms(10)
    
    if "CARDPUTER" in Device:
        led.fill((0,10,10)); led.write() # set led
    
    print("Connected!")
    tft.fill(config['bg_color'])
    tft.text('Connected!', 80, 30, config['ui_color'], font=font)
    tft.show()
    
    response = requests.get(url)

    while response.status_code != 200: # only continue if valid page is found
        print(response.status_code)
        if response.status_code in (301,302):
            #this is a redirect. use redirect url instead
            redirect_name = response.headers['location']
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + redirect_name
            tft.fill(config['bg_color'])
            tft.text('Redirecting to:', 60, 30, config['ui_color'], font=font)
            tft.text('"' + redirect_name + '"', 112 - (len(redirect_name) * 4), 60, config['ui_color'], font=font)
            time.sleep_ms(10)
            response = requests.get(url)
            print(response.status_code)
        elif response.status_code == 303:
            #alternate format for redirect
            url = response.headers['location']
            tft.fill(config['bg_color'])
            tft.text('Redirecting...:', 60, 30, config['ui_color'], font=font)
            time.sleep_ms(10)
            response = requests.get(url)
        else: #404 or another error
            tft.fill(config['bg_color'])
            tft.text('No results.', 76, 50, config['ui_color'], font=font)
            time.sleep(2)
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + user_query()
            response = requests.get(url)
        
    
    if "CARDPUTER" in Device:
        led.fill((0,40,0)); led.write() # set led    
    
    result = response.content
    nic.active(False) #turn off wifi

    tft.fill(config['bg_color'])

    #split text into lines
    # TODO: this bit has been made suboptimally probably. I'm just gonna start with what feels easiest to write before optimizing.
    words = json.loads(result)["extract"].split(" ")
    #print(json.loads(result)["extract"])
    lines = []
    current_string = ""
    for word in words:
        if len(current_string) + len(word) + 1 < 30:
            current_string += word + " "
        else:
            lines.append(current_string)
            current_string = word + " "
    lines.append(current_string) # add final line

    #page lines
    for i in range(0,7):
        dotted_hline(tft, 16 + (17*i), config.palette[3])
    tft.show()
    
    if "CARDPUTER" in Device:
        led.fill((0,0,0)); led.write() # set led  
    
    return lines
    
    

#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#--------------------------------------------------------------------------------------------------



lines = fetch_article()

screen_index = -1 # the line at the top of the display. Indicates current scroll distance.

pressed_keys = kb.get_pressed_keys()
prev_pressed_keys = pressed_keys
update_display = True
while True:
    
    # handle key strokes
    pressed_keys = kb.get_pressed_keys()
    if pressed_keys != prev_pressed_keys:
        if ';' in pressed_keys and ';' not in prev_pressed_keys: # up arrow
            screen_index -= 1
            if screen_index < -1:
                screen_index = len(lines) - 7
            update_display = True
        elif '.' in pressed_keys and ';' not in prev_pressed_keys: # down arrow
            screen_index += 1
            if screen_index > len(lines) - 7:
                screen_index = -1
            update_display = True
        elif "`" in pressed_keys and '`' not in prev_pressed_keys: # esc
            lines = fetch_article()
            screen_index = -1
            update_display = True
            
    # update prev pressed keys to pressed keys
    prev_pressed_keys = pressed_keys
    
    if update_display:
        #scroll bar
        max_screen_index = max((len(lines) - 7),1)
        scrollbar_height = min(135,(135 // max_screen_index) + 16)
        scrollbar_position = math.floor((135 - scrollbar_height) * (screen_index / max_screen_index)) + 4
        if scrollbar_position > 135 - scrollbar_height:
            scrollbar_position = 135 - scrollbar_height
        tft.rect(238, 0, 2, 135, config['bg_color'], fill=True)        
        tft.rect(238, scrollbar_position, 2, scrollbar_height, config.palette[3], fill=True)
        #print(scrollbar_height, scrollbar_position)
        
        
        # update display
        #check for down arrow press for scroll direction
        if '.' in pressed_keys: #update bottom of screen first
            for idx in reversed(range(0,8)):
                line_index = screen_index + idx
                tft.rect(4,idx*17,232,16, config['bg_color'], fill=True)
                if line_index < len(lines) and line_index >= 0:
                    tft.text(lines[line_index], 4, idx*17, config['ui_color'], font=font)

        else:
            for idx in range(0,8): #update top of screen first
                line_index = screen_index + idx
                tft.rect(4,idx*17,232,16, config['bg_color'], fill=True)
                if line_index < len(lines) and line_index >= 0:
                    tft.text(lines[line_index], 4, idx*17, config['ui_color'], font=font)
        tft.show()
        update_display = False
    
    else:
        time.sleep_ms(10)
    



