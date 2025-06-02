import time
import random
import math
from lib.display import Display

# Initialize display
display = Display()
SCREEN_WIDTH = display.width
SCREEN_HEIGHT = display.height

# Colors (RGB565)
BLACK = 0x0000
WHITE = 0xFFFF
GREEN = 0x07E0
DARK_GREEN = 0x03E0
LIGHT_GREEN = 0x07EF
RED = 0xF800

# Radar properties
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2
RADIUS = min(SCREEN_WIDTH, SCREEN_HEIGHT) // 2 - 5
SWEEP_ANGLE = 0
SWEEP_SPEED = 2

# Blip data
blips = []

# Warning system
warning_message = ""
warning_end_time = 0
WARNING_DURATION_MS = 3000

WARNING_MESSAGES = [
    "MISSILE INBOUND!",
    "NUCLEAR ATTACK!",
    "ENEMY AIRCRAFT DETECTED!",
    "INCOMING STRIKE!",
    "TORPEDO IN WATER!",
    "HOSTILE LAUNCH DETECTED!"
]

def spawn_blip():
    angle = random.uniform(0, 360)
    distance = random.uniform(20, RADIUS)
    blips.append({
        'angle': angle,
        'distance': distance,
        'lifetime': 50
    })

def polar_to_xy(angle_deg, radius):
    angle_rad = math.radians(angle_deg)
    x = int(CENTER_X + radius * math.cos(angle_rad))
    y = int(CENTER_Y + radius * math.sin(angle_rad))
    return x, y

# Main loop
last_spawn = time.ticks_ms()
spawn_interval = 2000

last_warning_check = time.ticks_ms()
warning_chance_interval = 5000

while True:
    display.fill(BLACK)

    # Draw radar circle
    for angle in range(0, 360, 10):
        x, y = polar_to_xy(angle, RADIUS)
        display.pixel(x, y, DARK_GREEN)

    # Draw sweep line
    for r in range(0, RADIUS, 2):
        x, y = polar_to_xy(SWEEP_ANGLE, r)
        display.pixel(x, y, LIGHT_GREEN)

    # Draw blips
    new_blips = []
    for blip in blips:
        if blip['lifetime'] > 0:
            bx, by = polar_to_xy(blip['angle'], blip['distance'])
            display.pixel(bx, by, WHITE)
            blip['lifetime'] -= 1
            new_blips.append(blip)
    blips = new_blips

    # Display full-screen warning message if active
    now = time.ticks_ms()
    if warning_message and time.ticks_diff(now, warning_end_time) < 0:
        # Clear screen and show big text
        display.fill(RED)
        text = warning_message
        text_x = 10
        text_y = SCREEN_HEIGHT // 2 - 10
        display.text(text, text_x, text_y, WHITE)
    else:
        warning_message = ""  # Clear after timeout

    display.show()
    time.sleep(0.05)

    # Update sweep
    SWEEP_ANGLE = (SWEEP_ANGLE + SWEEP_SPEED) % 360

    # Blip spawning
    now = time.ticks_ms()
    if time.ticks_diff(now, last_spawn) > spawn_interval:
        spawn_blip()
        last_spawn = now

    # Occasionally trigger a new warning
    if time.ticks_diff(now, last_warning_check) > warning_chance_interval:
        if random.random() < 0.3:
            warning_message = random.choice(WARNING_MESSAGES)
            warning_end_time = time.ticks_add(now, WARNING_DURATION_MS)
        last_warning_check = now
