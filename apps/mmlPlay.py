from lib import st7789fbuf, mhconfig, keyboard
import machine, time

"""
MicroHydra mmlPlay
Version: 1.0

Description:
A Simple and Naive MML (Music Macro Language) player for MicroHydra.
Have fun!

TODO: 
Better Sound Quality
More Buitiful & Elegant UI
Better Error Handling

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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# Set up I2S for audio output
i2s = machine.I2S(0,
                  sck=machine.Pin(_SCK_PIN),  # Serial Clock (BCLK)
                  ws=machine.Pin(_WS_PIN),    # Word Select (LRCLK)
                  sd=machine.Pin(_SD_PIN),    # Serial Data (SDATA)
                  mode=machine.I2S.TX,
                  bits=16,
                  format=machine.I2S.MONO,
                  rate=44100,
                  ibuf=1024)

# Generate a square wave buffer
def generate_square_wave(frequency, duration, volume):
    samples = bytearray(1024)
    half_period = int(44100 / (2 * frequency))
    amplitude = int(volume * 32767)

    for i in range(0, 1024, 2):
        if (i // 2) % half_period < half_period // 2:
            samples[i] = amplitude & 0xff
            samples[i + 1] = (amplitude >> 8) & 0xff
        else:
            samples[i] = (-amplitude) & 0xff
            samples[i + 1] = ((-amplitude) >> 8) & 0xff

    end_time = time.ticks_ms() + int(duration)
    while time.ticks_ms() < end_time:
        i2s.write(samples)

# init object for accessing display
tft = st7789fbuf.ST7789(
    machine.SPI(
        1, baudrate=40000000, sck=machine.Pin(36), mosi=machine.Pin(35), miso=None),
    _DISPLAY_HEIGHT,
    _DISPLAY_WIDTH,
    reset=machine.Pin(33, machine.Pin.OUT),
    cs=machine.Pin(37, machine.Pin.OUT),
    dc=machine.Pin(34, machine.Pin.OUT),
    backlight=machine.Pin(38, machine.Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
)

# object for accessing microhydra config (Delete if unneeded)
config = mhconfig.Config()

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
kb = keyboard.KeyBoard()

# Frequency table for notes in different octaves
FREQ_TABLE = {
    'C': [16.35, 32.70, 65.41, 130.81, 261.63, 523.25, 1046.50, 2093.00],
    'C#': [17.32, 34.65, 69.30, 138.59, 277.18, 554.37, 1108.73, 2217.46],
    'D': [18.35, 36.71, 73.42, 146.83, 293.66, 587.33, 1174.66, 2349.32],
    'D#': [19.45, 38.89, 77.78, 155.56, 311.13, 622.25, 1244.51, 2489.02],
    'E': [20.60, 41.20, 82.41, 164.81, 329.63, 659.25, 1318.51, 2637.02],
    'F': [21.83, 43.65, 87.31, 174.61, 349.23, 698.46, 1396.91, 2793.83],
    'F#': [23.12, 46.25, 92.50, 185.00, 369.99, 739.99, 1479.98, 2959.96],
    'G': [24.50, 49.00, 98.00, 196.00, 392.00, 783.99, 1567.98, 3135.96],
    'G#': [25.96, 51.91, 103.83, 207.65, 415.30, 830.61, 1661.22, 3322.44],
    'A': [27.50, 55.00, 110.00, 220.00, 440.00, 880.00, 1760.00, 3520.00],
    'A#': [29.14, 58.27, 116.54, 233.08, 466.16, 932.32, 1864.64, 3729.31],
    'B': [30.87, 61.74, 123.47, 246.94, 493.88, 987.76, 1975.52, 3951.04]
}

# Default settings
default_tempo = 120
default_octave = 4
default_length = 4
default_volume = 4

def get_note_frequency(note, octave):
    if note in FREQ_TABLE:
        return FREQ_TABLE[note][octave]
    return None

def parse_mml(mml_str):
    global default_tempo, default_octave, default_length, default_volume
    tft_disp(f"Parsing MML: {len(mml_str)} Chars.")
    notes = []
    tempo = default_tempo
    octave = default_octave
    length = default_length
    volume = default_volume

    i = 0
    while i < len(mml_str):
        char = mml_str[i]
        
        if char == ' ':
            i += 1
            continue
        if char in 'cdefgab':
            note = char.upper()
            i += 1
            if i < len(mml_str) and mml_str[i] in '+#':
                note += '#'
                i += 1
            elif i < len(mml_str) and mml_str[i] == '-':
                note += '-'
                i += 1
            if i < len(mml_str) and mml_str[i].isdigit():
                num_str = ''
                while i < len(mml_str) and mml_str[i].isdigit():
                    num_str += mml_str[i]
                    i += 1
                length = int(num_str)
            else:
                length = default_length
            freq = get_note_frequency(note, octave)
            duration = 60000 / tempo * 4 / length
            notes.append((freq, duration, volume))
        elif char == 'p' or char == 'r':
            i += 1
            if i < len(mml_str) and mml_str[i].isdigit():
                num_str = ''
                while i < len(mml_str) and mml_str[i].isdigit():
                    num_str += mml_str[i]
                    i += 1
                length = int(num_str)
            else:
                length = default_length
            duration = 60000 / tempo * 4 / length
            notes.append((None, duration, volume))
        elif char == 'o':
            i += 1
            if i < len(mml_str) and mml_str[i].isdigit():
                octave = int(mml_str[i])
                i += 1
        elif char == '>':
            octave += 1
            i += 1
        elif char == '<':
            octave -= 1
            i += 1
        elif char == 'l':
            i += 1
            if i < len(mml_str) and mml_str[i].isdigit():
                num_str = ''
                while i < len(mml_str) and mml_str[i].isdigit():
                    num_str += mml_str[i]
                    i += 1
                length = int(num_str)
                default_length = length
        elif char == 'v':
            i += 1
            if i < len(mml_str) and mml_str[i].isdigit():
                num_str = ''
                while i < len(mml_str) and mml_str[i].isdigit():
                    num_str += mml_str[i]
                    i += 1
                volume = int(num_str)
                default_volume = volume
        elif char == 't':
            i += 1
            if i < len(mml_str) and mml_str[i].isdigit():
                num_str = ''
                while i < len(mml_str) and mml_str[i].isdigit():
                    num_str += mml_str[i]
                    i += 1
                tempo = int(num_str)
                default_tempo = tempo
        else:
            i += 1
    return notes

#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    try:
        tft_disp("Please Input MML file name:")
        time.sleep_ms(1000)


        #Read MML file
        kb = keyboard.KeyBoard()
        keybuf = []
        while not 'ENT' in keybuf:
            tmp = kb.get_new_keys()
            if not 'BSPC' in tmp:
                keybuf += tmp
            else:
                keybuf = keybuf[:-1]

            tft_disp(''.join(keybuf))

        with open('/sd/' + ''.join(keybuf[:-1]), 'r') as f:
            mml_str = f.read()

        #Parse MML
        tft_disp("Parsing MML...")
        parsed_notes = parse_mml(mml_str)
        tft_disp("Parse Done.")

        # play the parsed notes one by one
        note_index = 0
        while note_index < len(parsed_notes):
            note, duration, volume = parsed_notes[note_index]
            tft_disp(f"Note {note_index}/{len(parsed_notes)}:({note},{int(duration)},{volume})")
            if note:
                generate_square_wave(note, duration, (config['volume']/5)*(volume/4)*0.05)
            else:
                time.sleep_ms(int(duration))  # rest for the duration
            note_index += 1
    except Exception as e:
        import sys
        with open('/sd/err.log', 'w') as f:
            sys.print_exception(e, f)
        
        while True:
            msg = f"{e}"
            tft_disp(msg[:25])
            time.sleep_ms(1000)
            tft_disp(msg[25:])
            time.sleep_ms(1000)


# start the main loop
main_loop()
