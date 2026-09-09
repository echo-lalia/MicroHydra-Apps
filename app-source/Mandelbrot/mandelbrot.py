import time
from machine import freq, reset
from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput
from lib.hydra.color import color565

freq(240000000)

display = Display()
config = Config()
kb = UserInput()

bg_color = config.palette[2]

# Emulate the np.linspace funtion
def linspace(start, stop, num):
    step = (stop - start) / (num - 1)
    return [start + step * i for i in range(num)]

# Determine how many iterations it takes for a point to escape.
# Returns num_iterations if it never escapes (i.e. it's in the set).
def escape_count(c, num_iterations):
    z = 0
    for i in range(num_iterations):
        z = z * z + c
        if abs(z) > 2:
            return i
    return num_iterations

# Precompute a classic smooth rainbow gradient, one color per possible
# escape-iteration count (0 .. num_iterations-1). Iteration counts
# that never escape (i.e. members of the set) are drawn in bg_color.
def build_palette(num_iterations, bg_color):
    palette = []
    for i in range(num_iterations):
        t = i / num_iterations
        r = int(9 * (1 - t) * t * t * t * 255)
        g = int(15 * (1 - t) * (1 - t) * t * t * 255)
        b = int(8.5 * (1 - t) * (1 - t) * (1 - t) * t * 255)
        palette.append(color565(r, g, b))
    palette.append(bg_color)  # index == num_iterations -> in the set
    return palette

# Clear the display
display.fill(bg_color)

# Define the bounds and resolution.
# The real (x) range picks the classic full view of the set; the
# imaginary (y) range is derived from it to match the display's pixel
# aspect ratio (240x135), so the set renders correctly proportioned and
# fills the whole screen instead of being squashed/stretched.
width, height = 240, 135
xmin, xmax = -2.5, 1.0
y_range = (xmax - xmin) * height / width
ymin, ymax = -y_range / 2, y_range / 2
num_iterations = 32

palette = build_palette(num_iterations, bg_color)

# Generate the Mandelbrot set and plot into the display's framebuffer.
re = linspace(xmin, xmax, width)
im = linspace(ymin, ymax, height)

for y, imag in enumerate(im):
    for x, real in enumerate(re):
        c = complex(real, imag)
        count = escape_count(c, num_iterations)
        # Use vline() with length 1 instead of pixel(): pixel() sets the
        # display driver's "dirty rows to flush" range to (y, y), which
        # show() treats as empty and skips -- so per-row show() calls
        # would silently no-op after the first row. vline(x, y, 1, ...)
        # draws the same single pixel but sets a proper (y, y+1) range,
        # so each row actually gets flushed to the screen as it's drawn.
        display.vline(x, y, 1, palette[count])
        # yield periodically so the CPU-heavy per-pixel math doesn't
        # starve the system's idle task long enough to trip the ESP32
        # watchdog.
        if x % 20 == 0:
            time.sleep_ms(0)
    # flush this row to the screen now, so the image builds up visibly
    # line by line instead of appearing all at once at the end.
    display.show()
    time.sleep_ms(1)

# leave the finished render on screen until a key is pressed, then exit
# back to the launcher (matches how other MicroHydra apps behave).
prev_keys = kb.get_pressed_keys()
while True:
    keys = kb.get_pressed_keys()
    if keys and keys != prev_keys:
        reset()
    prev_keys = keys
    time.sleep_ms(50)
