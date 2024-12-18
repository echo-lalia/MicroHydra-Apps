"""A simple app to query Wikipedia for page summaries.

v1.3

Changes:
Fixed brightness, modified to use mhconfig

"""
import requests, network, time, json
from machine import Pin, freq
from lib.display import Display
from lib.userinput import UserInput
from lib.hydra.config import Config
from lib.device import Device
from lib.hydra.popup import UIOverlay
from font import vga1_8x16 as font



# ~~~~~~~~~~~~~~~~~~~~~~~~~ global objects/vars ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
freq(240000000)

if "CARDPUTER" in Device:
    import neopixel
    led = neopixel.NeoPixel(Pin(21), 1, bpp=3)

tft = Display(use_tiny_buf=("spi_ram" not in Device))

config = Config()

kb = UserInput()

nic = network.WLAN(network.STA_IF)

OVERLAY = UIOverlay()

DISPLAY_WIDTH = Device.display_width
DISPLAY_HEIGHT = Device.display_height
DISPLAY_WIDTH_HALF = DISPLAY_WIDTH // 2
DISPLAY_HEIGHT_HALF = DISPLAY_HEIGHT // 2

MAX_H_CHARS = DISPLAY_WIDTH // 8
MAX_V_LINES = DISPLAY_HEIGHT // 16


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Function Definitions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def dotted_hline(tft, y_position, color):
    for i in range(4, DISPLAY_WIDTH - 20, 4):
        tft.pixel(i, y_position, color)


def gprint(text, clr_idx=8):
    text = str(text)
    print(text)
    tft.fill(config.palette[2])
    x = DISPLAY_WIDTH_HALF - (len(text) * 4)
    tft.text(text, x, DISPLAY_HEIGHT_HALF, config.palette[clr_idx], font=font)
    tft.show()


def errprint(text):
    text = str(text)
    print(text)
    tft.fill(config.palette[1])
    OVERLAY.error(text)


# ~~~~~~~~~~~~~~~~~~~~~~~~~fetch article~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
def fetch_article():
    
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + OVERLAY.text_entry(start_value='', title="Enter query:")
    if url == "https://en.wikipedia.org/api/rest_v1/page/summary/":
        url = "https://en.wikipedia.org/api/rest_v1/page/random/summary/"

    if "CARDPUTER" in Device:
        led.fill((10,0,0)); led.write() # set led

    gprint('Connecting to WIFI...', clr_idx=6)
    
    if not nic.active(): # turn on wifi if it isn't already
        nic.active(True)
    
    if "CARDPUTER" in Device:
        led.fill((10,10,0)); led.write() # set led
    
    # keep trying to connect until command works
    while True:
        try:
            nic.connect(config['wifi_ssid'], config['wifi_pass'])
            break
        except Exception as e:
            gprint(f"Got this error while connecting: {repr(e)}", clr_idx=11)

    # wait until connected
    gprint(f"Waiting for connection...")
    while not nic.isconnected():
        time.sleep_ms(100)
            
    if "CARDPUTER" in Device:
        led.fill((0,10,10)); led.write() # set led
    
    gprint("Making request...", clr_idx=6)
    
    response = requests.get(url)

    while response.status_code != 200: # only continue if valid page is found
        print(response.status_code)
        if response.status_code in (301, 302):
            #this is a redirect. use redirect url instead
            redirect_name = response.headers['location']
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + redirect_name
            gprint(f"Redirecting to '{redirect_name}'", clr_idx=6)
            time.sleep_ms(10)
            response = requests.get(url)
            print(response.status_code)

        elif response.status_code == 303:
            #alternate format for redirect
            url = response.headers['location']
            gprint("Redirecting...", clr_idx=6)
            time.sleep_ms(10)
            response = requests.get(url)

        else: #404 or another error
            gprint("No results.", clr_idx=11)
            time.sleep(2)
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + OVERLAY.text_entry(start_value='', title="Enter query:")
            response = requests.get(url)


    if "CARDPUTER" in Device:
        led.fill((0,40,0)); led.write() # set led    
    
    result = response.content
    nic.active(False) #turn off wifi
    # delete response to (hopefully) free memory
    del response

    tft.fill(config.palette[2])

    #split text into lines
    words = json.loads(result)["extract"].split(" ")

    lines = []
    current_string = ""
    for word in words:
        if len(current_string) + len(word) + 1 < MAX_H_CHARS:
            current_string += word + " "
        else:
            lines.append(current_string)
            current_string = word + " "
    lines.append(current_string) # add final line

    #page lines
    for i in range(1, MAX_V_LINES):
        dotted_hline(tft, (17*i) - 1, config.palette[4])
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

keys = kb.get_new_keys()

update_display = True
while True:
    
    # handle key strokes
    keys = kb.get_new_keys()
    kb.ext_dir_keys(keys)
    
    if keys:
        if 'UP' in keys: # up arrow
            screen_index -= 1
            if screen_index < -1:
                screen_index = len(lines) - 7
            update_display = True
        elif 'DOWN' in keys: # down arrow
            screen_index += 1
            if screen_index > len(lines) - 7:
                screen_index = -1
            update_display = True
        elif "ESC" in keys: # esc
            lines = fetch_article()
            screen_index = -1
            update_display = True


    if update_display:
        #scroll bar
        max_screen_index = max((len(lines) - (MAX_V_LINES - 1)), 1)
        scrollbar_height = min(DISPLAY_HEIGHT, (DISPLAY_HEIGHT // max_screen_index) + 16)
        scrollbar_position = int((DISPLAY_HEIGHT - scrollbar_height) * (screen_index / max_screen_index)) + 4
        if scrollbar_position > DISPLAY_HEIGHT - scrollbar_height:
            scrollbar_position = DISPLAY_HEIGHT - scrollbar_height
        tft.rect(DISPLAY_WIDTH - 2, 0, 2, DISPLAY_HEIGHT, config.palette[1], fill=True)        
        tft.rect(DISPLAY_WIDTH - 2, scrollbar_position, 2, scrollbar_height, config.palette[6], fill=True)


        # update display
        #check for down arrow press for scroll direction
        for idx in range(0, MAX_V_LINES): #update top of screen first
            line_index = screen_index + idx
            tft.rect(0, idx*17, DISPLAY_WIDTH-2, 16, config.palette[2], fill=True)
            if line_index < len(lines) and line_index >= 0:
                tft.text(lines[line_index], 4, idx*17, config.palette[8], font=font)

        tft.show()
        update_display = False

    else:
        time.sleep_ms(10)
