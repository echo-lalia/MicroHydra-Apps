from machine import freq
from lib.display import Display
from lib.userinput import UserInput
from font import vga1_8x16 as font
from lib.hydra.config import Config
import sys
import time

# Set CPU frequency
freq(240_000_000)

# Initialize display and user input
tft = Display(use_tiny_buf=True)
kb = UserInput()

# Configure backlight
blight = tft.backlight
blight.freq(1000)
blight.duty_u16(40000)

# Load configuration palette for colors
config = Config()
ui_color = config.palette[8]  # Foreground/active text color
bg_color = config.palette[2]  # Background color
inactive_color = config.palette[5]  # Inactive menu item text color

# Menu items
menu_items = ["Option 1", "About", "Exit"]

# Function to display the menu
def draw_menu(current_selection, pressed_keys=None):
    tft.fill(bg_color)  # Clear the screen

    # Display raw keypress data at the top for debugging (if provided)
    if pressed_keys is not None:
        debug_text = str(pressed_keys)
        tft.text(f"Keys: {debug_text}", 10, 10, ui_color, font)

    # Draw each menu item
    for i, item in enumerate(menu_items):
        color = ui_color if i == current_selection else inactive_color  # Active vs. inactive color
        x = 10
        y = 50 + i * 20  # Vertical spacing for items
        tft.text(item, x, y, color, font)

    tft.show()

# Function to handle menu navigation and selection
def menu_screen():
    current_selection = 0  # Default to the first menu item
    prev_pressed_keys = []

    while True:
        # Read currently pressed keys
        pressed_keys = kb.get_pressed_keys()

        # Render menu items with the current selection
        draw_menu(current_selection, pressed_keys)

        # Navigation logic
        if ";" in pressed_keys and ";" not in prev_pressed_keys:  # UP key
            current_selection = (current_selection - 1) % len(menu_items)  # Wrap to the last item if at the top
        elif "." in pressed_keys and "." not in prev_pressed_keys:  # DOWN key
            current_selection = (current_selection + 1) % len(menu_items)  # Wrap to the first item if at the bottom

        # Selection logic
        if "GO" in pressed_keys or "ENT" in pressed_keys:  # Confirm with GO or ENT key
            selected_item = menu_items[current_selection]
            if selected_item == "Exit":
                # Exit action
                tft.fill(bg_color)
                tft.text("Exiting...", 60, 50, ui_color, font)
                tft.show()
                time.sleep(1)
                sys.exit()  # Exits the application
            else:
                # Show selected item screen and return when "BSPC" is pressed
                show_selected_option(selected_item)
                return  # Exits the menu state back to "Hello World"

        # Track the previous pressed keys to handle single key press detection
        prev_pressed_keys = pressed_keys
        time.sleep(0.1)  # Polling delay for smoother key handling

# Function to display the selected option and stay until BSPC is pressed
def show_selected_option(selected_item):
    tft.fill(bg_color)

    if selected_item == "About":
        # Special behavior for "About" option
        tft.text("About:", 10, 50, ui_color, font)
        tft.text("Hello World App", 10, 70, inactive_color, font)
        tft.text("Version: 1.0.0", 10, 90, inactive_color, font)
        tft.text("Press BSPC to go back", 10, 130, inactive_color, font)
    else:
        # Generic behavior for all other options
        tft.text(f"{selected_item} screen", 10, 50, ui_color, font)
        tft.text("Press BSPC to go back", 10, 90, inactive_color, font)

    tft.show()

    # Wait until BSPC is pressed to return
    while True:
        pressed_keys = kb.get_pressed_keys()
        if "BSPC" in pressed_keys:  # Return to Hello World
            break
        time.sleep(0.1)

# Main function to display "Hello World" and handle transitions
def main():
    while True:
        # Clear the screen and show the "Hello World" message
        tft.fill(bg_color)
        tft.text("Hello World", 60, 70, ui_color, font)
        tft.text("Press G0 for Context Menu", 10, 110, ui_color, font)
        tft.show()

        # Wait for G0 to enter menu screen
        while True:
            pressed_keys = kb.get_pressed_keys()
            if "G0" in pressed_keys:
                menu_screen()  # Display menu screen
                break  # Go back to the "Hello World" screen after exiting the menu

# Run the application
main()
