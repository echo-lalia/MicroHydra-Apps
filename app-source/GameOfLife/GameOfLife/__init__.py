"""Conways Game of Life.

Version: 2.1
"""
from lib.display import Display
from lib.hydra import color
from lib.userinput import UserInput
import machine, time, framebuf, math, random
from lib.device import Device

machine.freq(240_000_000)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_HEIGHT = Device.display_height
_DISPLAY_WIDTH = Device.display_width
_DISPLAY_WIDTH_HALF = (_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(8)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)



# pixeldisplay/cells:
_PX_SIZE = const(4)
_PX_DISPLAY_WIDTH = (_DISPLAY_WIDTH // _PX_SIZE)
_PX_DISPLAY_HEIGHT = ((_DISPLAY_HEIGHT+1) // _PX_SIZE)

_INNER_PX_SIZE = const(_PX_SIZE-2)
_PX_SIZE_HALF = const(_PX_SIZE//2)

_PX_CHAR_SIZE = const(8)
_PX_MAX_CHAR_X = (_PX_DISPLAY_WIDTH-_PX_CHAR_SIZE)
_PX_MAX_CHAR_Y = (_PX_DISPLAY_HEIGHT-_PX_CHAR_SIZE)

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
DISPLAY = Display()

# # object for accessing microhydra config (Delete if unneeded)
# CONFIG = mhconfig.Config()

# object for reading keypresses
KB = UserInput()


PIXEL_DISPLAY = None # defined below
PREVIOUS_FRAME = None


PLAYING = True


COLORS = [0] * 8
DARKER = [0] * 8

#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

@micropython.native
def mix(val2: float, val1: float, fac=0.5) -> float:
    """Mix two values to the weight of fac."""
    return (val1 * fac) + (val2 * (1.0 - fac))

@micropython.native
def hsv_to_color565(h: float, s: float, v: float) -> int:
    """Convert h, s, and v floats to an rgb565 int."""
    r,g,b = color.hsv_to_rgb(h, s, v)
    r *= 31; g *= 63; b *= 31

    r = math.floor(r)
    g = math.floor(g)
    b = math.floor(b)

    return color.combine_color565(r,g,b)

@micropython.native
def gen_new_colors():
    """Generate new colors."""
    global COLORS, DARKER  # noqa: PLW0602

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
    """Add a new glider to the sim."""
    glider_pixels = (1,0,0,0,1,1,1,1,0)

    # iterate over 3*3 grid:
    for i in range(9):
        ix = x + ((i % 3) * x_dir)
        iy = y + ((i // 3) * y_dir)

        buffer.pixel(ix % _PX_DISPLAY_WIDTH, iy % _PX_DISPLAY_HEIGHT, glider_pixels[i])


def add_diamond(buffer, x, y):
    """Add a "4-8-12" diamond/pure glider generator."""
    for iy in range(0,9,2):
        ix = abs(4 - iy)
        width = (12 - ix*2)
        buffer.hline(
            (x + ix) % _PX_DISPLAY_WIDTH,
            (y + iy) % _PX_DISPLAY_HEIGHT,
            width, 1)


def add_pattern(pattern, buffer, x, y, flip_x = False, flip_y = False):  # noqa: FBT002
    """Add a pattern to the framebuffer from a text representation."""

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
    """Randomize all cell values."""
    for y in range(_DISPLAY_HEIGHT):
        for x in range(_DISPLAY_WIDTH):
            buf.pixel(
                x,y,
                random.randint(0,1)
                )


def fbuf_copy(source_fbuf: framebuf.FrameBuffer, target_fbuf: framebuf.FrameBuffer):
    """Copy framebuf contents to target framebuffer."""
    target_fbuf.blit(source_fbuf, 0, 0)

#--------------------------------------------------------------------------------------------------
#--------------------------------------- CLASS DEFINITIONS: ---------------------------------------
#--------------------------------------------------------------------------------------------------

class PixelDisplay:
    """This class operates as a sub-display.

    It creates a retro, pixel-art style look in a window.
    """

    def __init__(
        self,
        display_fbuf,
        width=32,
        height=30,
        px_size=4,
        color=46518):
        """Init the PixelDisplay."""

        self.width_bytes = math.ceil(width/8)
        bufsize = (self.width_bytes * height)

        self.buf = framebuf.FrameBuffer(bytearray(bufsize), width, height, framebuf.MONO_HLSB)
        self.px_size = px_size
        self.width = width
        self.height = height
        self.color = color
        self.display = display_fbuf

    def life(self, previous_frame):
        """Step the simulation."""
        if PLAYING:
            self._life(previous_frame)
        else:
            self._draw()

    @micropython.viper
    def _draw(self):
        display = self.display
        height = int(self.height)
        width = int(self.width)
        px_display_width = int(_PX_DISPLAY_WIDTH)
        px_display_height = int(_PX_DISPLAY_HEIGHT)

        # iterate over each cell
        for px_y in range(height):
            for px_x in range(width):

                # count neighbors
                is_alive = int(self.buf.pixel(px_x, px_y)) == 1

                # start count by subtracting self (will be added later)
                neighbors = -1 if is_alive else 0

                # start in the top left
                x = px_x-1; y = px_y-1

                # count each value in a 3*3 grid:
                for i in range(9):
                    ix = x + (i % 3)
                    iy = y + (i // 3)

                    neighbors += int(self.buf.pixel(
                        ix % px_display_width,
                        iy % px_display_height,
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
        px_display_width = int(_PX_DISPLAY_WIDTH)
        px_display_height = int(_PX_DISPLAY_HEIGHT)

        width_bytes = int(self.width_bytes)
        prev_ptr = ptr8(previous_frame)
        new_ptr = ptr8(new_frame)

        # iterate over each cell
        px_y = 0
        while px_y < height:
            px_x = 0
            while px_x < width:

                # manually extract pixel value, to avoid performance overhead from calling `fbuf.pixel`
                byte_idx = px_x//8 + px_y*width_bytes
                byte_shift = (7 - px_x % 8)
                is_alive = bool(
                    # Calculate the byte index for the given pixel/cell
                    prev_ptr[byte_idx]
                    # Shift the retrieved byte so that the rightmost bit is the target pixel.
                    >> byte_shift
                    # bitwise AND to cut off all but the rightmost bit (result is 0 or 1).
                    & 1
                )

                # count neighbors
                # start count by subtracting self (will be added later)
                neighbors = -1 if is_alive else 0

                # start in the top left
                x = px_x-1; y = px_y-1

                # count each value in a 3*3 grid:
                n = 0
                while n < 9:
                    nx = (x + (n % 3)) % px_display_width
                    ny = (y + (n // 3)) % px_display_height
                    # manually extract each neighbor value, to avoid performance overhead from `fbuf.pixel` method.
                    neighbors += (
                        # Calculate the byte index for the given pixel/cell
                        prev_ptr[nx//8 + ny*width_bytes]
                        # Shift the retrieved byte so that the rightmost bit is the target pixel.
                        >> (7 - nx % 8)
                        # bitwise AND to cut off all but the rightmost bit (result is 0 or 1).
                        & 1
                    )
                    n += 1

                color_idx = neighbors - 1


                # play the game!

                if is_alive:
                    # Any live cell with fewer than two live neighbors dies, as if by underpopulation.
                    # Any live cell with more than three live neighbors dies, as if by overpopulation.
                    if neighbors < 2 or neighbors > 3:
                        is_alive = False

                    # Any live cell with two or three live neighbors lives on to the next generation.
                    # (do nothing)

                # Any dead cell with exactly three live neighbors becomes a live cell, as if by reproduction.
                elif neighbors == 3:
                    is_alive = True
                    color_idx = 4


                # set our state (Again, avoiding the use of `fbuf.pixel` for speed).
                new_ptr[byte_idx] = (
                    # Erase the previous value from the byte
                    (new_ptr[byte_idx] & ~(1 << byte_shift))
                    # Shift the new value to the correct position and bitwise OR it into place.
                    | (int(is_alive) << byte_shift)
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
                px_x += 1
            px_y += 1


    def fill(self, color):
        """Fill with color."""
        self.buf.fill(color)

    def line(self, *args):
        """Draw a line."""
        self.buf.line(*args)

    def rect(self, *args):
        """Draw a rectangle."""
        self.buf.rect(*args)

    def text(self, *args):
        """Draw some text."""
        self.buf.text(*args)

    def center_text(self, text, x, y, color):
        """Draw text centered at the given location."""
        x -= len(text) * 4
        self.buf.text(text,x,y,color)

    def ellipse(self, *args):
        """Draw an ellipse."""
        self.buf.ellipse(*args)

    def pixel(self, *args) -> int:
        """Draw or get a pixel."""
        return self.buf.pixel(*args)



#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """Run the main loop of the program. Runs forever (until program is closed)."""
    global PIXEL_DISPLAY, PREVIOUS_FRAME, PLAYING  # noqa: PLW0603
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
    slow_mode = False

    # Start with a random soup
    random_soup(PIXEL_DISPLAY.buf)

    while True:

        DISPLAY.fill(0)

        # copy current frame into prev frame for comparison
        fbuf_copy(PIXEL_DISPLAY.buf, PREVIOUS_FRAME.buf)

        PIXEL_DISPLAY.life(PREVIOUS_FRAME.buf)

        # get list of newly pressed keys
        keys = KB.get_new_keys()

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

            elif key == "G0":
                random_soup(PIXEL_DISPLAY.buf)

            elif key == "SPC" and "CTL" in KB.key_state:
                # step once
                PLAYING = False
                fbuf_copy(PIXEL_DISPLAY.buf, PREVIOUS_FRAME.buf)
                PIXEL_DISPLAY._life(PREVIOUS_FRAME.buf)  # noqa: SLF001

            elif key == "s" and "CTL" in KB.key_state:
                # slow mode toggle
                slow_mode = not slow_mode

            elif key == "SPC":
                PLAYING = not PLAYING

            elif key == "ESC":
                machine.reset()

            elif key != "CTL": # ctl used above so can't be used as a shape
                PIXEL_DISPLAY.text(key,x,y,1)

        DISPLAY.show()


        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if counter >= 10:
            gen_new_colors()
            counter = 0
        elif slow_mode:
            time.sleep_ms(50)

        counter += 1


# start the main loop
main_loop()
