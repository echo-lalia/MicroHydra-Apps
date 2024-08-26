import machine, time

from lib import userinput
from lib.hydra.config import Config
from lib import display
from lib.kanji import Kanji
"""
MicroHydra App Template
Version: 1.0


This is a basic skeleton for a MicroHydra app, to get you started.

There is no specific requirement in the way a MicroHydra app must be organized or styled.
The choices made here are based entirely on my own preferences and stylistic whims;
please change anything you'd like to suit your needs (or ignore this template entirely if you'd rather)

This template is not intended to enforce a specific style, or to give guidelines on best practices,
it is just intended to provide an easy starting point for learners,
or provide a quick start for anyone that just wants to whip something up.

Have fun!

TODO: replace the above description with your own!
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
tft = DISPLAY = display.Display(
    use_tiny_buf=True,
    )

# object for accessing microhydra config (Delete if unneeded)
config = Config()

# object for reading keypresses
kb = userinput.UserInput()

kanji = Kanji(tft)
#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

# Add any function definitions you want here
# def hello_world():
#     print("Hello world!")

def show_file(fn,idx):
    fn.seek(idx)
    buf = fn.read(100)
    buf = buf.replace('\n','').replace('\r','')
    # clear framebuffer 
    tft.fill(config['bg_color'])
    
    # write current text to framebuffer
    for i in range(5):
        kanji.text(buf[i*10:(i+1)*10],0,i*8*3,config["ui_color"],scale = 3)
        
    return fn.tell()

def tft_disp(current_text):
    tft.fill(config['bg_color'])
    tft.text(
        text=current_text,
        # center text on x axis:
        x=_DISPLAY_WIDTH_HALF - (len(current_text) * _CHAR_WIDTH_HALF), 
        y=50,
        color=config['ui_color']
    )
    tft.show()


#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """
    The main loop of the program. Runs forever (until program is closed).
    """
    tft_disp("Please Input Text file name:")
    time.sleep_ms(1000)


    #Read file
    keybuf = []
    while not 'ENT' in keybuf:
        tmp = kb.get_new_keys()
        if not 'BSPC' in tmp:
            keybuf += tmp
        else:
            keybuf = keybuf[:-1]

        tft_disp(''.join(keybuf))
    
    cur_tl = 0
    tl_rec = [0]
    
    with open(''.join(keybuf[:-1]),"r",encoding='utf-8') as f:
        keybuf = []
        while True:
            try:
                cur_tl = tl_rec[-1]
                tl_rec.append(show_file(f,cur_tl))
            except:
                tl_rec = tl_rec[:-2]
            
            while not ',' in keybuf and not '/' in keybuf:
                keybuf = kb.get_new_keys()
            
            if ',' in keybuf:
                tl_rec = tl_rec[:-2]
            else:
                pass
            
            #print(tl_rec,cur_tl)
            keybuf = []

# start the main loop
try:
    main_loop()
except Exception as e:
    import sys
    with open('/log.txt', 'w') as f:
        f.write('[KANJIREADER]')
        sys.print_exception(e, f)
    
    tft.text(
            text=f"{e}",
            # center text on x axis:
            x=0, 
            y=0,
            color=config['ui_color']
            )
    tft.show()

