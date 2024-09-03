import time, math, random
from lib.display import Display

# Setup
display = Display()

# Constants for modes and timing
modes = ["waveform", "blink", "command", "data_stream"]
mode = random.choice(modes)  # Start with a random mode
last_switch = time.ticks_ms()
switch_interval = 3000  # Switch mode every 3 seconds

# Helper functions
def display_waveform():
    for x in range(display.width):
        y = int((math.sin(x / display.width * 4 * math.pi + time.ticks_ms() / 1000) + 1) / 2 * display.height)
        display.pixel(x, y, 0x07E0)  # Green pixel
    display.show()

def display_blink_effect():
    for _ in range(50):  # Generate 50 random stars
        x, y = random.randint(0, display.width - 1), random.randint(0, display.height - 1)
        display.pixel(x, y, 0x07E0)  # Green pixel
    display.show()

def display_command_simulation():
    display.fill(0x0000)  # Clear display
    commands = ["Scan network...", "Decrypting data...", "Infiltrating system..."]
    for i, cmd in enumerate(commands):
        display.text(cmd, 0, i * 20, 0x07E0)
    display.show()
    time.sleep(1)  # Pause to simulate "execution" of command

def display_data_stream():
    display.fill(0x0000)  # Clear display
    for x in range(0, display.width, 10):  # Create columns of data
        for y in range(0, display.height, 10):
            data = hex(random.randint(0, 255))[2:].upper()
            display.text(data, x, y, 0x07E0)  # Display hex data
    display.show()

# Main loop
while True:
    current_time = time.ticks_ms()
    if time.ticks_diff(current_time, last_switch) > switch_interval:
        mode = random.choice(modes)  # Change mode randomly
        last_switch = current_time

    if mode == "waveform":
        display_waveform()
    elif mode == "blink":
        display_blink_effect()
    elif mode == "command":
        display_command_simulation()
    elif mode == "data_stream":
        display_data_stream()

    time.sleep(0.1)  # Adjust for desired animation speed
