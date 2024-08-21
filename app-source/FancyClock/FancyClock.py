from lib import display
from lib.userinput import UserInput
from lib.hydra import color
from launcher.icons import battery
import time
from font import vga2_16x32 as font
from font import vga1_8x16 as font2
from machine import SPI, Pin, PWM, reset
import machine
import random
from lib import battlevel
from lib.device import Device

max_bright = const(65535)
min_bright = const(22000)
bright_peak = const(65535)
bright_step = const(500)

MAX_X = Device.display_width - 16
MAX_Y = Device.display_height - 48

# a simple clock program for the cardputer
# v1.1

tft = display.Display()





blight = PWM(tft.backlight)
blight.freq(1000)
blight.duty_u16(bright_peak)


months_names = {
    1:'Jan',
    2:'Feb',
    3:'Mar',
    4:'Apr',
    5:'May',
    6:'Jun',
    7:'Jul',
    8:'Aug',
    9:'Sep',
    10:'Oct',
    11:'Nov',
    12:'Dec'
    }


def hsv_to_rgb(HSV):
    ''' Converts an integer HSV tuple (value range from 0 to 255) to an RGB tuple '''
    
    # Unpack the HSV tuple for readability
    H, S, V = HSV

    # Check if the color is Grayscale
    if S == 0:
        R = V
        G = V
        B = V
        return (R, G, B)

    # Make hue 0-5
    region = H // 43;

    # Find remainder part, make it from 0-255
    remainder = (H - (region * 43)) * 6; 

    # Calculate temp vars, doing integer multiplication
    P = (V * (255 - S)) >> 8;
    Q = (V * (255 - ((S * remainder) >> 8))) >> 8;
    T = (V * (255 - ((S * (255 - remainder)) >> 8))) >> 8;


    # Assign temp vars based on color cone region
    if region == 0:
        R = V
        G = T
        B = P
    elif region == 1:
        R = Q; 
        G = V; 
        B = P;
    elif region == 2:
        R = P; 
        G = V; 
        B = T;
    elif region == 3:
        R = P; 
        G = Q; 
        B = V;
    elif region == 4:
        R = T; 
        G = P; 
        B = V;
    else: 
        R = V; 
        G = P; 
        B = Q;

    return (R, G, B)


def get_random_colors():
    #main hue
    hue1 = random.randint(0,255)
    #bg hue
    hue2 = hue1 + random.randint(-80,80)
    
    sat1 = random.randint(0,255)
    sat2 = random.randint(50,255)

    
    val1 = random.randint(245,255)
    val2 = random.randint(10,20)
    
    
    
    #convert to color565
    ui_color = display.color565(*hsv_to_rgb((hue1,sat1,val1)))
    bg_color = display.color565(*hsv_to_rgb((hue2,sat2,val2)))
    lighter_color = display.color565(*hsv_to_rgb((hue2,max(sat2 - 5, 0),val2 + 8)))
    darker_color = display.color565(*hsv_to_rgb((hue2,min(sat2 + 60, 255),max(val2 - 4,0))))
    
    #get middle hue
    mid_color = color.mix_color565(bg_color, ui_color)
    
    return ui_color, bg_color, mid_color, lighter_color, darker_color
    
    
    
def read_battery_level(adc):
    """
    read approx battery level on the adc and return as int range 0 (low) to 3 (high)
    """
    return batt.read_level()



kb = UserInput()

moving_right = True #horizontal movement
moving_up = False #vertical movement

x_pos = 50
y_pos = 50

#random color
ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
red_color = color.color565_shiftred(mid_color)

old_minute = 0

prev_pressed_keys = kb.get_pressed_keys()
current_bright = bright_peak

#init the ADC for the battery
batt = battlevel.Battery()

batt_level = read_battery_level(batt)



#we can slightly speed up the loop by only doing some calculations every x number of frames
loop_timer = 0

#init vals for loop timer stuff:
_, month, day, hour_24, minute, _,_,_ = time.localtime()
hour_12 = hour_24 % 12
if hour_12 == 0:
    hour_12 = 12
ampm = 'AM'
if hour_24 >= 12:
    ampm = 'PM'
time_string = f"{hour_12}:{'{:02d}'.format(minute)}"
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
        
        time_string = f"{hour_12}:{'{:02d}'.format(minute)}"
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
        
        
        
    #the spot beside the date and battery
    #we have to fill AROUND the battery to prevent a flashy/glitchy display
    tft.rect(battfill_x, battfill_y, batfill_total_width , 2, bg_color, fill=True) #line above
    tft.rect(battfill_x, battfill_y + 12, batfill_total_width , 4, bg_color, fill=True) #line below
    tft.rect(batt_x + 20, battfill_y + 2, 4 , 10, bg_color, fill=True) #box right
    tft.rect(battfill_x, battfill_y + 2, batfill_total_width - 24, 10, bg_color, fill=True) #box left
    
    
    
    
    
    
    #highlight/shadow
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
    
    
    #y_collision
    if y_pos <= 1:
        y_pos = 1
        moving_up = False
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = color.color565_shiftred(mid_color)
        batt_level = read_battery_level(batt)
        
    elif y_pos >= MAX_Y:
        y_pos = MAX_Y
        moving_up = True
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = color.color565_shiftred(mid_color)
        batt_level = read_battery_level(batt)
        
        
    #x_collision
    if x_pos <= 0:
        x_pos = 0
        moving_right = True
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = color.color565_shiftred(mid_color)
        batt_level = read_battery_level(batt)
        
    elif x_pos >= MAX_X - time_width:
        x_pos = MAX_X - time_width
        moving_right = False
        ui_color, bg_color, mid_color, lighter_color, darker_color = get_random_colors()
        red_color = color.color565_shiftred(mid_color)
        batt_level = read_battery_level(batt)
    
    
    
    
    #refresh bg on 5 mins
    if minute != old_minute and minute % 5 == 0:
        old_minute = minute
        tft.fill(0)
        
    #keystrokes and backlight
    pressed_keys = kb.get_pressed_keys()
    if pressed_keys != prev_pressed_keys: # some button has been pressed
        if "GO" in pressed_keys:
            tft.fill(0)
            tft.sleep_mode(True)
            blight.duty_u16(0)
            reset()
        current_bright = bright_peak
    elif current_bright != min_bright:
        current_bright -= bright_step
        if current_bright < min_bright:
            current_bright = min_bright
        blight.duty_u16(min(max_bright,current_bright))
        
        
    prev_pressed_keys = pressed_keys
    
    if "SPC" in pressed_keys:
        current_bright = bright_peak
        time.sleep_ms(1)
    else:
        time.sleep_ms(70)
    
    tft.show()





