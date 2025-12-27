from machine import freq
from lib.display import Display
from lib.userinput import UserInput
from font import vga1_8x16 as font
import sys
import time

# Set CPU frequency
freq(240_000_000)

# Initialize display and user input
tft = Display(use_tiny_buf=True)
kb = UserInput()  # Initialize UserInput for handling key presses

# Configure backlight
blight = tft.backlight
blight.freq(1000)
blight.duty_u16(40000)

# Colors for the display
bg_color = 0x000000  # Black background
text_color = 0xFFFFFF  # White text
highlight_color = 0x00FF00  # Highlighted menu item color

# Menu items
menu_items = ["Option 1", "Option 2", "Exit"]

# Function to display Hello World
def show_hello_world():
    tft.fill(bg_color)  # Clear the screen
    tft.text("Hello World", 60, 70, text_color, font)
    tft.text("Press G0 for menu", 20, 110, text_color, font)
    tft.show()

# Function to render the menu
def draw_menu(current_selection):
    tft.fill(bg_color)  # Clear the screen
    tft.text("Menu", 10, 10, text_color, font)

    for i, item in enumerate(menu_items):
        color = highlight_color if i == current_selection else text_color
        tft.text(item, 20, 50 + i * 20, color, font)  # Render menu items
    tft.show()

# Function to handle the menu
def menu_screen():
    current_selection = 0  # Default selection is the first item

    while True:
        # Draw the menu
        draw_menu(current_selection)

        # Get the pressed keys
        pressed_keys = kb.get_pressed_keys()

        # Handle navigation keys (; for UP, . for DOWN)
        if ";" in pressed_keys:  # UP key
            current_selection = (current_selection - 1) % len(menu_items)  # Wrap around
        elif "." in pressed_keys:  # DOWN key
            current_selection = (current_selection + 1) % len(menu_items)

        # Handle ENT key for selection
        if "ENT" in pressed_keys:  # Select the current menu item
            selected_item = menu_items[current_selection]
            if selected_item == "Exit":
                # Exit the application
                tft.fill(bg_color)
                tft.text("Exiting...", 50, 70, text_color, font)
                tft.show()
                time.sleep(1)
                sys.exit()
            else:
                # Show selection confirmation and return to Hello World
                tft.fill(bg_color)
                tft.text(f"Selected: {selected_item}", 20, 70, text_color, font)
                tft.show()
                time.sleep(1.5)
                return  # Return to Hello World screen

        time.sleep(0.1)  # Polling delay to avoid CPU overuse

# Main program logic
def main():
    while True:
        # Show Hello World and wait for G0 to be pressed
        show_hello_world()

        while True:
            pressed_keys = kb.get_pressed_keys()
            if "G0" in pressed_keys:  # Wait for G0 to open the menu
                menu_screen()  # Enter the menu once G0 is pressed
                break  # Exit the loop and return to Hello World

# Run the app
main()