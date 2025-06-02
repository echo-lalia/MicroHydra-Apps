import time
from lib.display import Display

# Initialize display
display = Display()
SCREEN_WIDTH = display.width
SCREEN_HEIGHT = display.height

# Strobe settings
STROBE_COLORS = [0xFFFF, 0xF800, 0x07E0, 0x001F]  # White, Red, Green, Blue
STROBE_SPEED = 0.1  # Default strobe interval in seconds

# Main loop
color_index = 0

while True:
    display.fill(STROBE_COLORS[color_index])
    display.show()
    color_index = (color_index + 1) % len(STROBE_COLORS)
    time.sleep(STROBE_SPEED)
