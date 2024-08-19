from lib import keyboard, HydraMenu,st7789py
import machine, time, gc, os
from font import vga1_8x16 as font
machine.freq(240_000_000)
"""
MicroHydra AppStore
Version: 1.0

A Simple AppStore that can download APP from Github repository.

Have fun!

TODO:
Support Folder download
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# init object for accessing display
tft = st7789py.ST7789(
    machine.SPI(1, baudrate=40000000, sck=machine.Pin(
        36), mosi=machine.Pin(35), miso=None),
    _DISPLAY_HEIGHT,
    _DISPLAY_WIDTH,
    reset=machine.Pin(33, machine.Pin.OUT),
    cs=machine.Pin(37, machine.Pin.OUT),
    dc=machine.Pin(34, machine.Pin.OUT),
    backlight=machine.Pin(38, machine.Pin.OUT),
    rotation=1,
    color_order=st7789py.BGR
)

gc.collect()
print(gc.mem_free())
        
import mhconfig
config = mhconfig.Config()
CONFIG_SSID = config['wifi_ssid']
CONFIG_PASS = config['wifi_pass']
CONFIG_UICOLOR = config['ui_color']
del config,mhconfig

import network
try:
    NIC = network.WLAN(network.STA_IF)
    NIC.active(True)
    NIC.connect(CONFIG_SSID,CONFIG_PASS)
    tft.text(text=f"Connecting Wifi...",font=font, x0=0, y0=0,color=CONFIG_UICOLOR)
    while not NIC.isconnected():
        pass
    tft.text(text=f"{NIC.ifconfig()}",font=font, x0=0, y0=0,color=CONFIG_UICOLOR)
except Exception as e:
    import sys
    with open('/log.txt', 'w') as f:
        f.write('[AppStore]')
        sys.print_exception(e, f)
    tft.text(text=f"{e}",font=font, x0=0, y0=0,color=CONFIG_UICOLOR)

del NIC, network

if '.storeinfo' in os.listdir():
    f = open("/.storeinfo","r")
    name,url = f.read().split()
    f.close();
    
    try:
        gc.collect()
        if url != 'dir':
            tft.text(text=f"Downloading {name} from:",font=font, x0=0, y0=16,color=CONFIG_UICOLOR)
            tft.text(text=url[:30],font=font, x0=0, y0=32,color=CONFIG_UICOLOR)
            tft.text(text=url[30:60],font=font, x0=0, y0=48,color=CONFIG_UICOLOR)
            tft.text(text=url[60:],font=font, x0=0, y0=64,color=CONFIG_UICOLOR)
            import urequests
            resb = urequests.get(url,headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"})
            tft.text(text="Download Done.",font=font, x0=0, y0=80,color=CONFIG_UICOLOR)
            
            import os
            if not 'sd' in os.listdir():
                path_i = f'/apps/{name}'
            else:
                path_i = f'/sd/apps/{name}'
                
            tft.text(text=f"Writing to path:",font=font, x0=0, y0=96,color=CONFIG_UICOLOR)
            tft.text(text=path_i,font=font, x0=0, y0=112,color=CONFIG_UICOLOR)
            with open(path_i,'w',encoding='utf-8',buffering=0) as f:
                f.write(resb.text)
            
            os.remove("/.storeinfo")
            
        machine.reset()
    except Exception as e:
        import sys
        with open('/log.txt', 'w') as f:
            f.write('[APPSTORE]')
            sys.print_exception(e, f)
        
        tft.text(text=f"{e}",font=font, x0=0, y0=0,color=CONFIG_UICOLOR)
        while True:
            pass
    
    
import urequests
resb = urequests.get('https://api.github.com/repos/echo-lalia/MicroHydra-Apps/contents/apps',headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0"})
del urequests

import ujson
data0 = ujson.loads(resb.text)
del ujson, resb
data = []
for i in data0:
    data.append((i['name'],'dir' if i['type'] == 'dir' else i['download_url']))

del data0,i

gc.collect()

# object for reading keypresses
kb = keyboard.KeyBoard()

menu = HydraMenu.Menu(display_py = tft)
#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

def handle_download(name,url):
    if url != 'dir':
        with open("/.storeinfo","w") as f:
            f.write(f"{name} {url}")
        
        tft.text(text=f"Launch Store Again to install {name}",font=font, x0=0, y0=50,color=CONFIG_UICOLOR)
    else:
        tft.text(text=f"Directory Not Supported.",font=font, x0=0, y0=50,color=CONFIG_UICOLOR)
    
    time.sleep(1)
    machine.reset()

#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """
    The main loop of the program. Runs forever (until program is closed).
    """
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    # If you need to do any initial work before starting the loop, this is a decent place to do that.
    
    # create variable to remember text between loops
    
    
    for i in data:
        print(i)
        cmd = f'menu.append(HydraMenu.DoItem(menu, "{i[0]}",callback=(lambda x:handle_download("{i[0]}","{i[1]}"))))'
        print(cmd)
        eval(cmd)
        
    # create a variable to remember/decide when we need to redraw the menu:
    redraw = True

    # this loop will run our menu's logic.
    while True:
        
        # get our newly pressed keys
        keys = kb.get_new_keys()
        
        # pass each key to the handle_input method of our menu.
        for key in keys:
            menu.handle_input(key)
        
        
        # when any key is pressed, we must redraw:
        if keys:
            redraw = True
        
        # this is used to prevent unneeded redraws (and speed up the app)
        # just calling menu.draw and display.show every loop also works, but it feels slower.
        if redraw:
            # menu.draw returns True when it is mid-animation,
            # and False when the animation is done (therefore, does not need to be redrawn until another key is pressed)
            redraw = menu.draw()

# start the main loop
try:
    main_loop()
except Exception as e:
    import sys
    with open('/log.txt', 'w') as f:
        f.write('[APPSTORE]')
        sys.print_exception(e, f)
    
    tft.text(text=f"{e}",font=font, x0=0, y0=0,color=CONFIG_UICOLOR)



