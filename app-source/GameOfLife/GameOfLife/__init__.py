from lib import st7789fbuf, mhconfig, keyboard
import machine, time, framebuf, math, random

machine.freq(240_000_000)

"""
Conways Game of Life
Version: 1.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)


# pixeldisplay/cells:
_PX_SIZE = const(4)
_PX_DISPLAY_WIDTH = const(_DISPLAY_WIDTH // _PX_SIZE)
_PX_DISPLAY_HEIGHT = const((_DISPLAY_HEIGHT+1) // _PX_SIZE)

_INNER_PX_SIZE = const(_PX_SIZE-2)
_PX_SIZE_HALF = const(_PX_SIZE//2)

_PX_CHAR_SIZE = const(8)
_PX_MAX_CHAR_X = const(_PX_DISPLAY_WIDTH-_PX_CHAR_SIZE)
_PX_MAX_CHAR_Y = const(_PX_DISPLAY_HEIGHT-_PX_CHAR_SIZE)

_GLIDER = const(
"""
.O
..O
OOO
""")

_GOOSE = const(
"""
OOO
O.........OO
.O......OOO.O
...OO..OO
....O
........O
....OO...O
...O.O.OO
...O.O..O.OO
..O....OO
..OO
..OO
""")

_POLE = const(
"""
..........OO
...........O
.........O
.......O.O

.....O.O

...O.O

..OO
O
OO
""")

_PERIOD2 = const(
"""
.....OOO...............OOO
....O...O.............O...O
...OO....O...........O....OO
..O.O.OO.OO...OOO...OO.OO.O.O
.OO.O....O.OO.OOO.OO.O....O.OO
O....O...O....O.O....O...O....O
............O.....O
OO.......OO.........OO.......OO
""")

_GUN = const(
"""
........................O
......................O.O
............OO......OO............OO
...........O...O....OO............OO
OO........O.....O...OO
OO........O...O.OO....O.O
..........O.....O.......O
...........O...O
............OO
""")

_P7 = const(
"""
.O..O....
.....O...
O.....O..
OO....O..
.....O...
....O....
...OOOO.O
...O...O.
.O...O...
O.OOOO...
....O....
...O.....
..O....OO
..O.....O
...O.....
....O..O.
""")

_LIGHTWEIGHT = const(
"""
.O..O
O
O...O
OOOO
""")

_COPPERHEAD = const(
"""
.OO..OO.
...OO...
...OO...
O.O..O.O
O......O
........
O......O
.OO..OO.
..OOOO..
........
...OO...
...OO...
""")

_C3 = const(
"""
.......OO.O
....OO.O.OO.OOO
.OOOO..OO......O
O....O...O...OO
.OO
""")

_PINWHEEL = const(
"""
......OO
......OO

....OOOO
OO.O....O
OO.O..O.O
...O...OO.OO
...O.O..O.OO
....OOOO

....OO
....OO
""")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
DISPLAY = st7789fbuf.ST7789(
    machine.SPI(
        1,baudrate=40000000,sck=machine.Pin(36),mosi=machine.Pin(35),miso=None),
    _DISPLAY_HEIGHT,
    _DISPLAY_WIDTH,
    reset=machine.Pin(33, machine.Pin.OUT),
    cs=machine.Pin(37, machine.Pin.OUT),
    dc=machine.Pin(34, machine.Pin.OUT),
    backlight=machine.Pin(38, machine.Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
    )

# # object for accessing microhydra config (Delete if unneeded)
# CONFIG = mhconfig.Config()

# object for reading keypresses
KB = keyboard.KeyBoard()


PIXEL_DISPLAY = None # defined below
PREVIOUS_FRAME = None


PLAYING = True


COLORS = [0] * 8
DARKER = [0] * 8

#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

@micropython.native
def mix(val2, val1, fac=0.5):
    """Mix two values to the weight of fac"""
    output = (val1 * fac) + (val2 * (1.0 - fac))
    return output

@micropython.native
def hsv_to_color565(h,s,v):
    r,g,b = mhconfig.hsv_to_rgb(h, s, v)
    r *= 31; g *= 63; b *= 31
    
    r = math.floor(r)
    g = math.floor(g)
    b = math.floor(b)
    
    return mhconfig.combine_color565(r,g,b)

@micropython.native
def gen_new_colors():
    global COLORS, DARKER
    
    h1 = (time.ticks_ms() / 100000)
    h2 = (h1 - 0.8)
    
    
    for i in range(8):
        fac = i/7
        COLORS[i] = hsv_to_color565(
            mix(h1, h2, fac),
            mix(0.7, 0, fac),
            mix(0.7, 1, fac)
            )
        DARKER[i] = hsv_to_color565(
            mix(h1, h2, fac),
            1,
            mix(0.1, 0.5, fac)
            )
    
def add_glider(buffer, x, y, x_dir=1, y_dir=1):
    glider_pixels = (1,0,0,0,1,1,1,1,0)
    
    # iterate over 3*3 grid:
    for i in range(9):
        ix = x + ((i % 3) * x_dir)
        iy = y + ((i // 3) * y_dir)
        
        buffer.pixel(ix % _PX_DISPLAY_WIDTH, iy % _PX_DISPLAY_HEIGHT, glider_pixels[i])
        
def add_diamond(buffer, x, y):
    # adds a "4-8-12" diamond/pure glider generator
    
    for iy in range(0,9,2):
        ix = abs(4 - iy)
        width = (12 - ix*2)
        
        buffer.hline(
            (x + ix) % _PX_DISPLAY_WIDTH,
            (y + iy) % _PX_DISPLAY_HEIGHT,
            width, 1)
        
def add_pattern(pattern, buffer, x, y, flip_x = False, flip_y = False):
    """Add a pattern to the framebuffer from a text representation"""
    
    start_x = x
    
    for char in pattern:
        if char == "\n":
            x = start_x
            y += -1 if flip_y else 1
        
        elif char == 'O':
            buffer.pixel(
                x % _PX_DISPLAY_WIDTH,
                y % _PX_DISPLAY_HEIGHT,
                1)
        
        x += -1 if flip_x else 1
    
def random_soup(buf):
    for y in range(_DISPLAY_HEIGHT):
        for x in range(_DISPLAY_WIDTH):
            buf.pixel(
                x,y,
                random.randint(0,1)
                )
    
def fbuf_copy(source_fbuf, target_fbuf):
    target_fbuf.blit(source_fbuf, 0, 0)

#--------------------------------------------------------------------------------------------------
#--------------------------------------- CLASS DEFINITIONS: ---------------------------------------
#--------------------------------------------------------------------------------------------------

class PixelDisplay:
    """
    This class operates as a sub-display.
    It creates a retro, pixel-art style look in a window.
    """
    def __init__(
        self,
        display_fbuf,
        width=32,
        height=30,
        px_size=4,
        color=46518,
        ):
        
        bufsize = ((math.ceil(width/8)*8) * height) // 8
        
        self.buf = framebuf.FrameBuffer(bytearray(bufsize), width, height, framebuf.MONO_HLSB)
        self.px_size = px_size
        self.width = width
        self.height = height
        self.color = color
        self.display = display_fbuf
        
    def life(self, previous_frame):
        if PLAYING:
            self._life(previous_frame)
        else:
            self._draw(previous_frame)
    
    @micropython.viper      
    def _draw(self, previous_frame):
        display = self.display
        height = int(self.height)
        width = int(self.width)
        
        # iterate over each cell
        for px_y in range(height):
            for px_x in range(width):
                
                # count neighbors
                is_alive = int(self.buf.pixel(px_x, px_y)) == 1
                
                # start count by subtracting self (will be added later)
                if is_alive:
                    neighbors = -1
                else:
                    neighbors = 0
                
                # start in the top left
                x = px_x-1; y = px_y-1 
                
                # count each value in a 3*3 grid:
                for i in range(9):
                    ix = x + (i % 3)
                    iy = y + (i // 3)
                    
                    neighbors += int(self.buf.pixel(
                        ix % _PX_DISPLAY_WIDTH,
                        iy % _PX_DISPLAY_HEIGHT,
                        ))
                
                # draw ourselves!
                if is_alive:
                    display.fill_rect(
                        (px_x * _PX_SIZE)+1,
                        (px_y * _PX_SIZE)+1,
                        _INNER_PX_SIZE, _INNER_PX_SIZE,
                        COLORS[neighbors-1]
                        )
                    display.rect(
                        (px_x * _PX_SIZE),
                        (px_y * _PX_SIZE),
                        _PX_SIZE, _PX_SIZE,
                        DARKER[neighbors-1]
                        )
    
    @micropython.viper
    def _life(self, previous_frame):
        display = self.display
        height = int(self.height)
        width = int(self.width)
        new_frame = self.buf
        
        # iterate over each cell
        for px_y in range(height):
            for px_x in range(width):
                
                # count neighbors
                is_alive = int(previous_frame.pixel(px_x, px_y)) == 1
                
                # start count by subtracting self (will be added later)
                neighbors = -1 if is_alive else 0
                
                #new_neighbors = neighbors
                
                # start in the top left
                x = px_x-1; y = px_y-1 
                
                # count each value in a 3*3 grid:
                for i in range(9):
                    ix = x + (i % 3)
                    iy = y + (i // 3)
                    
                    
                    neighbors += int(previous_frame.pixel(
                        ix % _PX_DISPLAY_WIDTH,
                        iy % _PX_DISPLAY_HEIGHT,
                        ))
                    
                color_idx = neighbors - 1
                    
                
                # play the game!
                
                if is_alive:
                    # Any live cell with fewer than two live neighbors dies, as if by underpopulation.
                    if neighbors < 2:
                        is_alive = False
                    
                    # Any live cell with more than three live neighbors dies, as if by overpopulation.
                    elif neighbors > 3:
                        is_alive = False
                        
                    # Any live cell with two or three live neighbors lives on to the next generation.
                    # (do nothing)
                    
                else:
                    # Any dead cell with exactly three live neighbors becomes a live cell, as if by reproduction.
                    if neighbors == 3:
                        is_alive = True
                        color_idx = 4
                
                # set our state
                self.buf.pixel(
                    px_x, px_y,
                    1 if is_alive else 0,
                    )
                
                
                
                # draw ourselves!
                if is_alive:
                    
                    display.fill_rect(
                        (px_x * _PX_SIZE)+1,
                        (px_y * _PX_SIZE)+1,
                        _INNER_PX_SIZE, _INNER_PX_SIZE,
                        COLORS[color_idx]
                        )
                    display.rect(
                        (px_x * _PX_SIZE),
                        (px_y * _PX_SIZE),
                        _PX_SIZE, _PX_SIZE,
                        DARKER[color_idx]
                        )
                    
                    
    
    def fill(self, color):
        self.buf.fill(color)
        
    def line(self, *args):
        self.buf.line(*args)
        
    def rect(self, *args):
        self.buf.rect(*args)
        
    def text(self, *args):
        self.buf.text(*args)
    
    def center_text(self, text, x, y, color):
        x -= len(text) * 4
        self.buf.text(text,x,y,color)
    
    def ellipse(self, *args):
        self.buf.ellipse(*args)
        
    def pixel(self, *args):
        return self.buf.pixel(*args)



#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """
    The main loop of the program. Runs forever (until program is closed).
    """
    global PIXEL_DISPLAY, PREVIOUS_FRAME, PLAYING
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    # If you need to do any initial work before starting the loop, this is a decent place to do that.
    
    
    PIXEL_DISPLAY = PixelDisplay(
        DISPLAY,
        width=_PX_DISPLAY_WIDTH,
        height=_PX_DISPLAY_HEIGHT,
        px_size=_PX_SIZE
        )
    PREVIOUS_FRAME = PixelDisplay(
        DISPLAY,
        width=_PX_DISPLAY_WIDTH,
        height=_PX_DISPLAY_HEIGHT,
        px_size=_PX_SIZE
        )
    
    counter = 0
    
    while True:
        
        DISPLAY.fill(0)
        
        # copy current frame into prev frame for comparison
        fbuf_copy(PIXEL_DISPLAY.buf, PREVIOUS_FRAME.buf)
        
        
        PIXEL_DISPLAY.life(PREVIOUS_FRAME.buf)
        
        # get list of newly pressed keys
        keys = KB.get_new_keys()
        
        # if there are keys, convert them to a string, and store for display
        for key in keys:
            x = random.randint(0,_PX_MAX_CHAR_X)
            y = random.randint(0,_PX_MAX_CHAR_Y)
            
            if key == 'BSPC':
                PIXEL_DISPLAY.fill(0)
                
            elif key == 'UP':
                add_pattern(_GLIDER, PIXEL_DISPLAY.buf, x, y, True, True)
            elif key == 'DOWN':
                add_pattern(_GLIDER, PIXEL_DISPLAY.buf, x, y, False, False)
            elif key == 'RIGHT':
                add_pattern(_GLIDER, PIXEL_DISPLAY.buf, x, y, False, True)
            elif key == 'LEFT':
                add_pattern(_GLIDER, PIXEL_DISPLAY.buf, x, y, True, False)
                
            elif key == "F1":
                add_diamond(PIXEL_DISPLAY.buf, x, y)
                
            elif key == "F2":
                add_pattern(
                    _GOOSE, PIXEL_DISPLAY.buf, x, y,
                    random.randint(0,1), random.randint(0,1))
                
            elif key == "F3":
                add_pattern(
                    _POLE, PIXEL_DISPLAY.buf, x, y,
                    random.randint(0,1), random.randint(0,1))
                
            elif key == "F4":
                add_pattern(
                    _PERIOD2, PIXEL_DISPLAY.buf, x, y,
                    random.randint(0,1), random.randint(0,1))
                
            elif key == "F5":
                add_pattern(
                    _P7, PIXEL_DISPLAY.buf, x, y,
                    random.randint(0,1), random.randint(0,1))
                
            elif key == "F6":
                add_pattern(
                    _LIGHTWEIGHT, PIXEL_DISPLAY.buf, x, y,
                    random.randint(0,1), random.randint(0,1))
                
            elif key == "F7":
                add_pattern(
                    _COPPERHEAD, PIXEL_DISPLAY.buf, x, y,
                    random.randint(0,1), random.randint(0,1))
                
            elif key == "F8":
                add_pattern(
                    _C3, PIXEL_DISPLAY.buf, x, y,
                    random.randint(0,1), random.randint(0,1))
                
            elif key == "F9":
                add_pattern(
                    _PINWHEEL, PIXEL_DISPLAY.buf, x, y,
                    random.randint(0,1), random.randint(0,1))
                
            elif key == "F10":
                add_pattern(
                    _GUN, PIXEL_DISPLAY.buf, x, y,
                    random.randint(0,1), random.randint(0,1))
            
            elif key == "GO":
                random_soup(PIXEL_DISPLAY.buf)
                
            elif key == "SPC" and "CTL" in KB.key_state:
                # step once
                PLAYING = False
                fbuf_copy(PIXEL_DISPLAY.buf, PREVIOUS_FRAME.buf)
                PIXEL_DISPLAY._life(PREVIOUS_FRAME.buf)
                
            elif key == "SPC":
                PLAYING = not PLAYING
                
            elif key == "ESC":
                machine.reset()
            
            elif key != "CTL": # ctl used above so can't be used as a shape
                PIXEL_DISPLAY.text(key,x,y,1)
    
        DISPLAY.show()
        
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        if counter == 0:
            gen_new_colors()
        else:
            time.sleep_ms(1)
            
        counter = (counter + 1) % 10


# start the main loop
main_loop()
