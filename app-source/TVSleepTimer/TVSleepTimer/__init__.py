"""
TVSleepTimer - a MicroHydra app for the Cardputer.

Lets you type in a number of minutes, counts down, and sends the
configured TV "power" IR code when it reaches zero. Time can be added
to a running countdown with a button press.

Confirmed working for an LG OLED77C9PUB: NEC protocol, address=0x04,
command=0x08, 33% carrier duty (see config.json).

Controls:
  entry screen:      digits to type minutes, BSPC to erase, ENT to start
  countdown screen:   ; : add minutes (config "add_minutes")
                      . : subtract minutes
                      G0: cancel and return to entry screen
  done screen:        any key returns to entry screen
"""

import json
import time
from machine import Pin
from lib.display import Display
from lib.userinput import UserInput
from lib.hydra.color import color565
from font import vga2_16x32 as big_font
from font import vga1_8x16 as small_font

from .ir_tx import IRTransmitter


# Same IR LED pin used by MicroHydra's built-in "IR" app.
PIN_IR_LED = const(44)

DIGITS = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9")

# fixed screen regions, so we only ever clear/redraw the part that
# actually changed (instead of tft.fill()-ing the whole screen every
# tick, which causes a visible flash).
DIGIT_AREA = (40, 40, 160, 32)  # big countdown text
ENTRY_DIGIT_AREA = (40, 56, 160, 32)  # big minutes-entry text (extra gap under labels)
STATUS_AREA = (8, 90, 224, 16)


def load_config():
    """Find and load this app's config.json, whether it's installed on
    internal flash or on the SD card.
    """
    for path in (
        "/apps/TVSleepTimer/config.json",
        "/sd/apps/TVSleepTimer/config.json",
        "config.json",
    ):
        try:
            with open(path) as conf_file:
                return json.load(conf_file)
        except OSError:
            continue
    raise OSError("Could not find TVSleepTimer/config.json")


config = load_config()
ui_color = color565(*config.get("ui_color_rgb", [160, 20, 20]))
bg_color = color565(*config.get("bg_color_rgb", [0, 0, 0]))
tv_label = f'{config.get("tv_brand", "?")} {config.get("tv_model", "?")}'
default_minutes = config.get("default_minutes", 30)
add_minutes = config.get("add_minutes", 10)
power_duty = config.get("power_duty", 33)


def send_power_signal():
    protocol = config.get("power_protocol", "raw")
    if protocol == "nec":
        return ir.send_nec(config["power_address"], config["power_command"])
    power_signal = config.get("power_signal", [])
    if not power_signal:
        return False
    return ir.send_raw(power_signal)


# display setup (matches the pattern used by other MicroHydra apps)
tft = Display()

kb = UserInput()
ir = IRTransmitter(Pin(PIN_IR_LED, Pin.OUT), duty=power_duty)


def draw_triangle_up(x, y, w, h, color):
    """Draw a small filled upward-pointing triangle in a w x h box
    (top-left at x, y) using horizontal-line scanlines -- the display
    driver doesn't have a filled-triangle primitive of its own.
    """
    for row in range(h):
        line_width = (row + 1) * w // h
        tft.hline(x + (w - line_width) // 2, y + row, line_width, color)


def draw_triangle_down(x, y, w, h, color):
    """Same as draw_triangle_up, but pointing down."""
    for row in range(h):
        line_width = (h - row) * w // h
        tft.hline(x + (w - line_width) // 2, y + row, line_width, color)


def update_big_text(text, area=DIGIT_AREA):
    """Redraw only the big centered text region (countdown / minutes
    entry), instead of clearing the whole screen.
    """
    x, y, w, h = area
    tft.fill_rect(x, y, w, h, bg_color)
    text_x = 120 - len(text) * 16 // 2
    tft.text(text, text_x, y, ui_color, big_font)
    tft.show()


def update_status(status):
    """Redraw only the status-line region."""
    x, y, w, h = STATUS_AREA
    tft.fill_rect(x, y, w, h, bg_color)
    tft.text(status, x, y, ui_color, small_font)
    tft.show()


def draw_entry_static():
    tft.fill(bg_color)
    tft.text("TV Sleep Timer", 8, 8, ui_color, small_font)
    tft.text(tv_label, 8, 28, ui_color, small_font)
    tft.text("type minutes, ENT: start", 8, 112, ui_color, small_font)
    tft.show()


def entry_screen():
    """Let the user type a number of minutes. Returns the chosen minute
    count (int), or None if the user pressed G0 to exit the app.
    """
    minutes_str = str(default_minutes)
    is_default = True  # first digit press replaces the default, not appends
    draw_entry_static()
    update_big_text(f"{minutes_str} min", area=ENTRY_DIGIT_AREA)

    prev_pressed_keys = kb.get_pressed_keys()
    while True:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            redraw = False

            if "G0" in pressed_keys:
                return None

            if "ENT" in pressed_keys and "ENT" not in prev_pressed_keys:
                if minutes_str != "" and int(minutes_str) > 0:
                    return int(minutes_str)

            elif "BSPC" in pressed_keys and "BSPC" not in prev_pressed_keys:
                minutes_str = minutes_str[:-1]
                is_default = False
                redraw = True

            else:
                for key in pressed_keys:
                    if (
                        key in DIGITS
                        and key not in prev_pressed_keys
                        and len(minutes_str) < 4  # cap at 9999 minutes
                    ):
                        if is_default:
                            minutes_str = key
                            is_default = False
                        # avoid leading zeros (e.g. "0" -> "5" not "05")
                        elif minutes_str in ("", "0"):
                            minutes_str = key
                        else:
                            minutes_str += key
                        redraw = True

            if redraw:
                update_big_text(f"{minutes_str} min", area=ENTRY_DIGIT_AREA)

        prev_pressed_keys = pressed_keys


def format_countdown(seconds_left):
    minutes, seconds = divmod(int(seconds_left), 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes:02}:{seconds:02}"


def draw_countdown_static():
    tft.fill(bg_color)
    tft.text(tv_label, 8, 8, ui_color, small_font)

    # hint line: [icon] +Nm   [icon] -Nm   G0: cancel
    x, y = 4, 118
    draw_triangle_up(x, y + 4, 8, 8, ui_color)
    x += 12
    add_label = f"+{add_minutes}m"
    tft.text(add_label, x, y, ui_color, small_font)
    x += len(add_label) * 8 + 8

    draw_triangle_down(x, y + 4, 8, 8, ui_color)
    x += 12
    sub_label = f"-{add_minutes}m"
    tft.text(sub_label, x, y, ui_color, small_font)
    x += len(sub_label) * 8 + 8

    tft.text("G0: cancel", x, y, ui_color, small_font)
    tft.show()


def countdown_screen(minutes):
    """Runs the countdown. Sends the TV power-off signal at zero.
    Returns when the user cancels (G0) or the timer finishes.
    """
    seconds_left = minutes * 60
    end_time = time.time() + seconds_left

    status = "Counting down..."
    draw_countdown_static()
    update_big_text(format_countdown(seconds_left))
    update_status(status)
    prev_display_seconds = int(seconds_left)

    prev_pressed_keys = kb.get_pressed_keys()
    while True:
        seconds_left = end_time - time.time()

        if seconds_left <= 0:
            send_power_signal()
            update_big_text(format_countdown(0))
            update_status("Sent power-off code! Any key...")
            prev = kb.get_pressed_keys()
            while kb.get_pressed_keys() == prev:
                pass
            return

        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if "G0" in pressed_keys:
                return

            if ";" in pressed_keys and ";" not in prev_pressed_keys:
                end_time += add_minutes * 60
                seconds_left = end_time - time.time()
                update_status(f"+{add_minutes} min added")
                update_big_text(format_countdown(seconds_left))
                prev_display_seconds = int(seconds_left)

            elif "." in pressed_keys and "." not in prev_pressed_keys:
                end_time = max(time.time() + 1, end_time - add_minutes * 60)
                seconds_left = end_time - time.time()
                update_status(f"-{add_minutes} min")
                update_big_text(format_countdown(seconds_left))
                prev_display_seconds = int(seconds_left)

        prev_pressed_keys = pressed_keys

        # only redraw the countdown once per second, to avoid flicker
        if int(seconds_left) != prev_display_seconds:
            prev_display_seconds = int(seconds_left)
            update_big_text(format_countdown(seconds_left))


def show_error(exc):
    """Show a crash on-screen (instead of silently bouncing back to the
    launcher) so it's obvious something went wrong.
    """
    tft.fill(bg_color)
    tft.text("Error:", 8, 8, ui_color, small_font)
    msg = str(exc)
    for i in range(0, len(msg), 26):
        tft.text(msg[i:i + 26], 8, 32 + (i // 26) * 16, ui_color, small_font)
    tft.text("press any key to exit", 8, 118, ui_color, small_font)
    tft.show()
    prev = kb.get_pressed_keys()
    while kb.get_pressed_keys() == prev:
        pass


def main():
    while True:
        minutes = entry_screen()
        if minutes is None:
            return
        countdown_screen(minutes)


try:
    main()
except Exception as e:
    print(e)
    show_error(e)
