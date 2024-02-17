import requests, network, json, time, math
from machine import SPI, Pin, PWM, freq, reset
from lib import st7789py, keyboard, microhydra
from font import vga1_8x16 as font


# version: 1.0

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Function Definitions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def dotted_hline(tft, y_position, color):
    for i in range(4,220,4):
        tft.pixel(i,y_position, color)

# ~~~~~~~~~~~~~~~~~~~~~~~~~ global objects/vars ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

freq(240000000)
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

with open("config.json", "r") as conf:
    config = json.loads(conf.read())
    ui_color = config["ui_color"]
    bg_color = config["bg_color"]
    ui_sound = config["ui_sound"]
    volume = config["volume"]
    wifi_ssid = config["wifi_ssid"]
    wifi_pass = config["wifi_pass"]
    
mid_color = microhydra.mix_color565(ui_color, bg_color)

kb = keyboard.KeyBoard()

nic = network.WLAN(network.STA_IF)


# ~~~~~~~~~~~~~~~~~~~~~~~~~fetch article~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def user_query():
    tft.fill(bg_color)
    tft.text(font, "Enter query:", 72, 4, ui_color, bg_color)
    
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
            tft.fill_rect(12, 59, 216, 64, bg_color)
            if len(current_value) <= 30:
                tft.text(font, current_value, 120 - (len(current_value) * 4), 75, ui_color, bg_color)
            else:
                tft.text(font, current_value[0:30], 24, 59, ui_color, bg_color)
                tft.text(font, current_value[30:], 120 - (len(current_value[12:]) * 4), 91, ui_color, bg_color)

            
            
            redraw = False

        prev_pressed_keys = pressed_keys
    
    
    
    
def fetch_article():
    
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + user_query()
    if url == "https://en.wikipedia.org/api/rest_v1/page/summary/":
        url = "https://en.wikipedia.org/api/rest_v1/page/random/summary/"
    
    tft.fill(bg_color)
    tft.text(font, 'Connecting to WIFI...', 36, 30, ui_color, bg_color)

    if not nic.active(): # turn on wifi if it isn't already
        nic.active(True)
        
    if not nic.isconnected(): # try connecting
        try:
            nic.connect(wifi_ssid, wifi_pass)
        except OSError as e:
            print("Had this error when connecting:",e)

    while not nic.isconnected():
        time.sleep_ms(5)

    print("Connected!")
    tft.fill(bg_color)
    tft.text(font, 'Connected!', 80, 30, ui_color, bg_color)
    
    response = requests.get(url)

    while response.status_code != 200: # only continue if valid page is found
        print(response.status_code)
        if response.status_code in (301,302):
            #this is a redirect. use redirect url instead
            redirect_name = response.headers['location']
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + redirect_name
            tft.fill(bg_color)
            tft.text(font, 'Redirecting to:', 60, 30, ui_color, bg_color)
            tft.text(font, '"' + redirect_name + '"', 112 - (len(redirect_name) * 4), 60, ui_color, bg_color)
            time.sleep_ms(5)
            response = requests.get(url)
            print(response.status_code)
        elif response.status_code == 303:
            #alternate format for redirect
            url = response.headers['location']
            tft.fill(bg_color)
            tft.text(font, 'Redirecting...:', 60, 30, ui_color, bg_color)
            time.sleep_ms(5)
            response = requests.get(url)
        else: #404 or another error
            tft.fill(bg_color)
            tft.text(font, 'No results.', 76, 50, ui_color, bg_color)
            time.sleep(2)
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + user_query()
            response = requests.get(url)
            
    result = response.content
    nic.active(False) #turn off wifi

    tft.fill(bg_color)

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
        dotted_hline(tft, 16 + (17*i), mid_color)

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
        tft.fill_rect(238, 0, 2, 135, bg_color)        
        tft.fill_rect(238, scrollbar_position, 2, scrollbar_height, mid_color)
        #print(scrollbar_height, scrollbar_position)
        
        
        # update display
        #check for down arrow press for scroll direction
        if '.' in pressed_keys: #update bottom of screen first
            for idx in reversed(range(0,8)):
                line_index = screen_index + idx
                tft.fill_rect(4,idx*17,232,16, bg_color)
                if line_index < len(lines) and line_index >= 0:
                    tft.text(font, lines[line_index], 4, idx*17, ui_color, bg_color)

        else:
            for idx in range(0,8): #update top of screen first
                line_index = screen_index + idx
                tft.fill_rect(4,idx*17,232,16, bg_color)
                if line_index < len(lines) and line_index >= 0:
                    tft.text(font, lines[line_index], 4, idx*17, ui_color, bg_color)
        update_display = False
    
    else:
        time.sleep_ms(10)
    

