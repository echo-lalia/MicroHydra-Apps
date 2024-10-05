"""A simple clock program for MicroHydra.

v 1.3
"""

import random
import time

from font import vga1_8x16 as font2
from font import vga2_16x32 as font
from launcher.icons import battery
from lib import battlevel, display
from lib.hydra import color, loader
from lib.userinput import UserInput


tft = display.Display()

MAX_X = tft.width - 16
MAX_Y = tft.height - 48


months_names = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Aug',
    9: 'Sep',
    10: 'Oct',
    11: 'Nov',
    12: 'Dec',
    }


def hsv_to_rgb(HSV: tuple[float, float, float]) -> tuple[float, float, float]:
    """Convert an integer HSV tuple (value range from 0 to 255) to an RGB tuple."""

    # Unpack the HSV tuple for readability
    H, S, V = HSV

    # Check if the color is Grayscale
    if S == 0:
        R = V
        G = V
        B = V
        return (R, G, B)

    # Make hue 0-5
    region = H // 43

    # Find remainder part, make it from 0-255
    remainder = (H - (region * 43)) * 6

    # Calculate temp vars, doing integer multiplication
    P = (V * (255 - S)) >> 8
    Q = (V * (255 - ((S * remainder) >> 8))) >> 8
    T = (V * (255 - ((S * (255 - remainder)) >> 8))) >> 8

    # Assign temp vars based on color cone region
    if region == 0:
        R = V
        G = T
        B = P
    elif region == 1:
        R = Q
        G = V
        B = P
    elif region == 2:
        R = P
        G = V
        B = T
    elif region == 3:
        R = P
        G = Q
        B = V
    elif region == 4:
        R = T
        G = P
        B = V
    else:
        R = V
        G = P
        B = Q

    return (R, G, B)


def get_random_colors() -> tuple[int, int, int, int, int]:
    """Get new random colors."""
    # main hue
    hue1 = random.randint(0, 255)
    # bg hue
    hue2 = hue1 + random.randint(-80, 80)

    sat1 = random.randint(0, 255)
    sat2 = random.randint(50, 255)


    val1 = random.randint(245, 255)
    val2 = random.randint(10, 20)

    # convert to color565
    ui_color = color.color565(*hsv_to_rgb((hue1,sat1,val1)))
    bg_color = color.color565(*hsv_to_rgb((hue2,sat2,val2)))
    lighter_color = color.color565(*hsv_to_rgb((hue2,max(sat2 - 5, 0),val2 + 8)))
    darker_color = color.color565(*hsv_to_rgb((hue2,min(sat2 + 60, 255),max(val2 - 4,0))))

    # get middle hue
    mid_color = color.mix_color565(bg_color, ui_color)

    return ui_color, bg_color, mid_color, lighter_color, darker_color


def shiftred(clr: int) -> int:
    """Shift the given color towards red."""
    return color.color565_shift_to_hue(clr, 0.0, 0.1, min_sat=0.9)


kb = UserInput()

moving_right = True  # horizontal movement
moving_up = False  # vertical movement

x_pos = 50
y_pos = 50

# random color
ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
red_color = shiftred(mid_color)

old_minute = 0

prev_pressed_keys = kb.get_pressed_keys()
current_bright = 10

# init the ADC for the battery
batt = battlevel.Battery()
batt_level = batt.read_level()


# we can slightly speed up the loop by only doing some calculations every x number of frames
loop_timer = 0
bright_timer = 0

# init vals for loop timer stuff:
_, month, day, hour_24, minute, _, _, _ = time.localtime()
hour_12 = hour_24 % 12
if hour_12 == 0:
    hour_12 = 12
ampm = 'AM'
if hour_24 >= 12:
    ampm = 'PM'
time_string = f"{hour_12}:{minute:02d}"
date_string = f"{months_names[month]},{day}"
time_width = len(time_string) * 16
date_width = len(date_string) * 8
batfill_total_width = (time_width + 16) - (date_width + 4)


while True:

    #loop timer stuff; only update every x number of frames
    if loop_timer > 100:
        loop_timer = 0

        _, month, day, hour_24, minute, _,_,_ = time.localtime()

        hour_12 = hour_24 % 12
        if hour_12 == 0:
            hour_12 = 12

        ampm = 'AM'
        if hour_24 >= 12:
            ampm = 'PM'

        time_string = f"{hour_12}:{minute:02d}"
        date_string = f"{months_names[month]},{day}"
        time_width = len(time_string) * 16
        date_width = len(date_string) * 8

        batfill_total_width = (time_width + 16) - (date_width + 4)

    else:
        loop_timer += 1



    #add main graphics first
    tft.rect(
        x_pos,
        y_pos,
        time_width + 18, 49,
        bg_color,
        fill=True
    )
    tft.text(
        time_string,
        x_pos,
        y_pos,
        ui_color,
        font=font,
    )
    tft.text(
        ampm,
        time_width + x_pos,16 + y_pos,
        mid_color,
        font=font2,
    )

    #date
    tft.fill_rect(x_pos,y_pos + 32, 4, 16, bg_color)
    tft.text(
        date_string,
        x_pos + 4,
        y_pos + 32,
        mid_color,
        font=font2,
        )


    # extract useful positions for fill section
    battfill_x = x_pos + date_width + 4
    battfill_y = y_pos + 32
    batt_x = x_pos + time_width - 8

    # battery
    tft.bitmap(battery, batt_x, y_pos + 34, palette=(bg_color,red_color), index=batt_level)


    # the spot beside the date and battery
    # we have to fill AROUND the battery to prevent a flashy/glitchy display
    tft.rect(battfill_x, battfill_y, batfill_total_width , 2, bg_color, fill=True)  # line above
    tft.rect(battfill_x, battfill_y + 12, batfill_total_width , 4, bg_color, fill=True)  # line below
    tft.rect(batt_x + 20, battfill_y + 2, 4 , 10, bg_color, fill=True)  # box right
    tft.rect(battfill_x, battfill_y + 2, batfill_total_width - 24, 10, bg_color, fill=True)  # box left




    # highlight/shadow
    tft.hline(x_pos-2, y_pos-1, time_width + 20, lighter_color)
    tft.hline(x_pos-2, y_pos+48, time_width + 20, darker_color)


    if moving_right:
        x_pos += 1
    else:
        x_pos -= 1

    if moving_up:
        y_pos -= 1
    else:
        y_pos +=1


    # y_collision
    if y_pos <= 1:
        y_pos = 1
        moving_up = False
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = shiftred(mid_color)
        batt_level = batt.read_level()

    elif y_pos >= MAX_Y:
        y_pos = MAX_Y
        moving_up = True
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = shiftred(mid_color)
        batt_level = batt.read_level()

    # x_collision
    if x_pos <= 0:
        x_pos = 0
        moving_right = True
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = shiftred(mid_color)
        batt_level = batt.read_level()

    elif x_pos >= MAX_X - time_width:
        x_pos = MAX_X - time_width
        moving_right = False
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = shiftred(mid_color)
        batt_level = batt.read_level()



    # refresh bg on 5 mins
    if minute != old_minute and minute % 5 == 0:
        old_minute = minute
        tft.fill(0)

    # keystrokes and backlight
    pressed_keys = kb.get_pressed_keys()
    if pressed_keys != prev_pressed_keys:  # some button has been pressed
        if "G0" in pressed_keys:
            loader.launch_app()
        current_bright = 10
        tft.set_brightness(current_bright)
        bright_timer = 0
    elif "SPC" in pressed_keys:
        current_bright = 10
        time.sleep_ms(1)
        bright_timer = 0
    elif bright_timer >= 50 and current_bright > 0:
        current_bright -= 1
        tft.set_brightness(current_bright)
        bright_timer = 0
    else:
        bright_timer += 1
        time.sleep_ms(60)

    prev_pressed_keys = pressed_keys


    tft.show()
