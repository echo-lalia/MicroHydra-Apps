from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput
import machine, time
machine.freq(240000000)

"""
MicroHydra wavPlay
Version: 1.0

Description:
A Simple and Naive wav player for MicroHydra.
Have fun!

TODO: 
Time & Duration Display
Better Sound Quality
More Buitiful & Elegant UI
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_HEIGHT = 135
_DISPLAY_WIDTH = 240
_DISPLAY_WIDTH_HALF = _DISPLAY_WIDTH // 2

_CHAR_WIDTH = 8
_CHAR_WIDTH_HALF = _CHAR_WIDTH // 2

# Define pin constants
_SCK_PIN = const(41)
_WS_PIN = const(43)
_SD_PIN = const(42)

# Initialize global i2s variable
i2s = None

# init object for accessing display
tft = Display()

# object for accessing microhydra config (Delete if unneeded)
config = Config()

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

tft_disp("Loading...")

# object for reading keypresses
kb = UserInput()

# Function to read WAV file header and get sample rate
def read_wav_header(file):
    # Read and parse the WAV file header
    file.seek(0)
    riff = file.read(12)
    fmt = file.read(24)
    data_hdr = file.read(8)
    
    # Extract the sample rate from the header
    sample_rate = int.from_bytes(fmt[12:16], 'little')
    # Read the number of channels from the header
    num_channels = int.from_bytes(fmt[10:12], 'little')

    return sample_rate*num_channels

# Set up I2S for audio output
def setup_i2s(sample_rate):
    global i2s
    i2s = machine.I2S(0,
                      sck=machine.Pin(_SCK_PIN),  # Serial Clock (BCLK)
                      ws=machine.Pin(_WS_PIN),    # Word Select (LRCLK)
                      sd=machine.Pin(_SD_PIN),    # Serial Data (SDATA)
                      mode=machine.I2S.TX,
                      bits=16,
                      format=machine.I2S.MONO,
                      rate=sample_rate,
                      ibuf=1024)

#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    tft_disp("Please Input Wave file name:")
    time.sleep_ms(1000)


    #Read MML file
    keybuf = []
    while not 'ENT' in keybuf:
        tmp = kb.get_new_keys()
        if not 'BSPC' in tmp:
            keybuf += tmp
        else:
            keybuf = keybuf[:-1]

        tft_disp(''.join(keybuf))

    with open(''.join(keybuf[:-1]), 'rb') as file:
            sample_rate = read_wav_header(file)
            setup_i2s(sample_rate)
            
            tft_disp(f"Playing {''.join(keybuf[:-1])}")

            # Read and play the data
            data = file.read(1024)
            while data:
                i2s.write(data)
                data = file.read(1024)
            
            # Deinitialize I2S after use
            i2s.deinit()


# start the main loop
try:
    main_loop()
except Exception as e:
    import sys
    with open('/log.txt', 'w') as f:
        f.write('[WAVPLAYER]')
        sys.print_exception(e, f)
    
    tft.text(text=f"{e}",x=0, y=0,color=config['ui_color'])
    tft.show()
