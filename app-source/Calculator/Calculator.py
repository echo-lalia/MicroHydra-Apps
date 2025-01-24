"""
My first micro python app "calculator"
"""

import time

from lib import display, userinput
from lib.hydra import config

from font import vga1_8x16 as midfont
from font import vga2_16x32 as bigfont
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ _CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_MH_DISPLAY_HEIGHT = const(135)
_MH_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_MH_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL_OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
DISPLAY = display.Display()

# object for accessing microhydra config (Delete if unneeded)
CONFIG = config.Config()

# object for reading keypresses (or other user input)
INPUT = userinput.UserInput()
# --------------------------------------------------------------------------------------------------
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """Run the main loop of the program.

    Runs forever (until program is closed).
    """

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    # If you need to do any initial work before starting the loop, this is a decent place to do it.

    # create variable to remember text between loops

    text_field = []
    value = "0"
    while True:  # Fill this loop with your program logic! (delete old code you don't need)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # put user input logic here

        # get list of newly pressed keys
        keys = INPUT.get_new_keys()
        
        good_symbols=str("1234567890=+x\\^*/-.")
        #print(good_symbols)
        # if there are keys, convert them to a string, and store for display
        if keys:
            print(keys)
            if "ENT" in keys:
                try:
                    value = str(eval(str(value)))
                except:
                    value = "ERROR"
            elif "c" in keys or "`" in keys:
                value = "0"
            elif "BSPC" in keys and len(value) > 0:
                value = list(value)
                value.pop()
                value = ''.join(value)
            elif keys[0] in good_symbols:
                if value == "0" or value == "ERROR":
                    value = ""
                    
                if keys[0] == "=":
                    value = value+"+"
                elif keys[0] == "x":
                    value = value+"*"
                elif keys[0] == "\\":
                    value = value+"/"
                else:
                    value = str(value)+keys[0]
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN GRAPHICS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # put graphics rendering logic here

        # clear framebuffer
        DISPLAY.fill(CONFIG.palette[2])

        # write current text to framebuffer
        DISPLAY.text(text="Calculator",x=45,y=10,color=CONFIG.palette[8],font=bigfont)
        DISPLAY.hline(x=0, y=45, length=250, color=CONFIG.palette[8])
        DISPLAY.text(text=value,x=10,y=50,color=CONFIG.palette[8],font=bigfont)
        ltime = time.localtime()
        DISPLAY.text(text=f"Use c or esc for clear {ltime[3]}:{ltime[4]}",x=10,y=115,color=CONFIG.palette[8],font=midfont)
        DISPLAY.vline(x=190, y=110, length=30, color=CONFIG.palette[8])
        DISPLAY.hline(x=0, y=110, length=250, color=CONFIG.palette[8])
        # write framebuffer to display
        DISPLAY.show()


        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # anything that needs to be done to prepare for next loop

        # do nothing for 10 milliseconds
        time.sleep_ms(10)



# start the main loop
main_loop()
