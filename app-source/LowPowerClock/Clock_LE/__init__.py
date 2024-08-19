from lib import st7789fbuf, mhconfig, keyboard, battlevel
import machine, time, random, math
from font import vga2_16x32 as font

try:
    # relative import for when launched from microhydra
    from . import powermanager, pixeldisplay
except:
    # absolute import path needed when running from editor
    from apps.Clock_LE import powermanager, pixeldisplay


"""
Clock (Low Energy)
Version: 1.0

This simple clock app is designed to be run at a low CPU frequency (40mhz instead of 240mhz).
It also utilizes a custom 'power manager' module that puts the device into (and wakes the device up from) deep sleep.
"""

machine.freq(40_000_000)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_DISPLAY_WIDTH_HALF = const(_DISPLAY_WIDTH // 2)

_CHAR_WIDTH = const(16)
_CHAR_WIDTH_HALF = const(_CHAR_WIDTH // 2)
_CHAR_HEIGHT = const(32)

_WHITE = const(65535)
_GRAY = const(42324)
_BLACK = const(0)

_PX_SIZE = const(5)

_BIG_CHAR_WIDTH = const(8*_PX_SIZE)
_BIG_CHAR_HEIGHT = const(8*_PX_SIZE)

_AM_PM_WIDTH = const(_CHAR_WIDTH*2)
_CLOCK_TIME_WIDTH = const((_BIG_CHAR_WIDTH*4)+_AM_PM_WIDTH+1)
_CLOCK_BOX_PADDING = const(5)

_CLOCK_BOX_WIDTH = const(_CLOCK_TIME_WIDTH+_CLOCK_BOX_PADDING+_CLOCK_BOX_PADDING)
_CLOCK_BOX_WIDTH_HALF = const(_CLOCK_BOX_WIDTH//2)
_CLOCK_BOX_HEIGHT = const(_BIG_CHAR_HEIGHT+_CHAR_HEIGHT+_CLOCK_BOX_PADDING+_CLOCK_BOX_PADDING)

_AMPM_Y_OFFSET = const(_CLOCK_BOX_PADDING+_BIG_CHAR_HEIGHT-_CHAR_HEIGHT)
_DATE_Y_OFFSET = const(_CLOCK_BOX_PADDING+_BIG_CHAR_HEIGHT+4)
_DATE_X_OFFSET = const(_CLOCK_BOX_PADDING+16)

_CLOCK_MINIMUM_X = const(1)
_CLOCK_MINIMUM_Y = const(1)
_CLOCK_MAXIMUM_X = const(_DISPLAY_WIDTH - _CLOCK_MINIMUM_X - _CLOCK_BOX_WIDTH)
_CLOCK_MAXIMUM_Y = const(_DISPLAY_HEIGHT - _CLOCK_MINIMUM_Y - _CLOCK_BOX_HEIGHT)

_MOVEMENT_WIDTH_X = const(_CLOCK_MAXIMUM_X-_CLOCK_MINIMUM_X)
_MOVEMENT_WIDTH_Y = const(_CLOCK_MAXIMUM_Y-_CLOCK_MINIMUM_Y)

_BATT_X_OFFSET = const(_CLOCK_BOX_WIDTH-56)
_BATT_Y_OFFSET = const(_CLOCK_BOX_HEIGHT-26)

_SLEEP_STATE_HOLD_DIM = const(2)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# init object for accessing display
DISPLAY = st7789fbuf.ST7789(
    machine.SPI(
        1,baudrate=40000000,sck=machine.Pin(36),mosi=machine.Pin(35),miso=None),
    _DISPLAY_HEIGHT,
    _DISPLAY_WIDTH,
    reset=machine.Pin(33, machine.Pin.OUT),
    cs=machine.Pin(37, machine.Pin.OUT),
    dc=machine.Pin(34, machine.Pin.OUT),
    backlight=machine.Pin(38, machine.Pin.OUT),
    rotation=1,
    color_order=st7789fbuf.BGR
    )

# object for accessing microhydra config (Delete if unneeded)
CONFIG = mhconfig.Config()

# object for reading keypresses
KB = keyboard.KeyBoard()

# power manager helps us go sleep and wake up :)
POWER_MANAGER = powermanager.SleepManager(machine.RTC(), CONFIG, DISPLAY, KB)
PIXEL_DISPLAY = pixeldisplay.PixelDisplay(DISPLAY,width=40,height=8,px_size=_PX_SIZE,color=46518)

BATT = battlevel.Battery()

CLOCK_X = _CLOCK_MINIMUM_X
CLOCK_Y = _CLOCK_MINIMUM_Y
MOVING_RIGHT = True
MOVING_UP = False

HAS_CHANGED_COLOR = False

PREV_MINUTE = -1

MONTH = 0
DAY = 0
HOUR_24 = 0
HOUR_12 = 0
MINUTE = 0
AMPM = 'AM'

#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

def frame_switcher(frametime):
    """Switch between two frames on a regular interval. Used for simple animations.
    Returns 1 or 0 depending on the frame.
    """
    double_time = frametime*2
    nowtime = time.ticks_ms() % double_time
    return 1 if (nowtime > frametime) else 0

def round_clamp_int(value, minimum, maximum):
    """Convert float to int, clamping and rounding as well."""
    value = math.floor(
        round(value)
        )
    if value < minimum:
        value = minimum
    elif value > maximum:
        value = maximum
    return value

def ping_pong(value,maximum):
    odd_pong = (int(value / maximum) % 2 == 1)
    mod = value % maximum
    if odd_pong:
        return maximum - mod
    else:
        return mod

def random_gauss(loc=0, scale=1, clamp_range=None):
    """Simple implementation of a random gaussian function. (NOT highly optimized.)"""
    
    R1 = random.random()
    R2 = random.random()
    
    gauss = math.sqrt(-2*math.log(R1))*math.cos(2*math.pi*R2)
    
    
    
    if scale != 1:
        gauss *= scale
        
    if loc:
        # move center location up or down
        gauss += loc
    
    if clamp_range:
        # minimum/maximum values possible
        minimum = min(clamp_range); maximum = max(clamp_range)
        width = maximum - minimum
        
        gauss -= minimum
        gauss = ping_pong(gauss,width)
        gauss += minimum

        

            
    return gauss

def round_rect(x,y,width,height,r,color):
    """This is super unoptimized. Should be used sparringly."""
    DISPLAY.fill_rect(
        x+r, y,
        width-(r*2),
        height,
        color
        )
    DISPLAY.fill_rect(
        x, y+r,
        r,
        height-(r*2),
        color
        )
    DISPLAY.fill_rect(
        x+(width-r), y+r,
        r,
        height-(r*2),
        color
        )# x, y, xr, yr, color, fill=False)
    DISPLAY.ellipse(x+r,y+r,r,r,color, fill=True)
    DISPLAY.ellipse(x+(width-r)-1,y+r,r,r,color, fill=True)
    DISPLAY.ellipse(x+(width-r)-1,y+(height-r)-1,r,r,color, fill=True)
    DISPLAY.ellipse(x+r,y+(height-r)-1,r,r,color, fill=True)

def get_random_colors():
    """Get two random RGB565 colors, using HSV functions in mhconfig"""
    
    # generate random color
    h = random.random()
    s = random_gauss(loc=1,scale=0.5,clamp_range=(0,1))
    v = random_gauss(loc=1,scale=0.25,clamp_range=(0.5,1))
    
    # generate second colors hue by adding gauss to first color
    h2 = h + random_gauss(loc=0,scale=0.2)
    s2 = random_gauss(loc=1,scale=0.25,clamp_range=(0,1))
    
    # higher saturation usually looks darker. So, prevent the lighter color from having higher saturation.
    if s > s2:
        s2 = min(s2 + 0.3, 1)
        s = max(s - 0.3, 1)
    
    # make sure bg value isnt too close to fg value
    if v < 0.8:
        v2 = random_gauss(loc=0,scale=0.05,clamp_range=(0,0.2))
    else:
        v2 = random_gauss(loc=0,scale=0.2,clamp_range=(0,0.4))
    
    r,g,b = mhconfig.hsv_to_rgb(h,s,v)
    r2,g2,b2 = mhconfig.hsv_to_rgb(h2,s2,v2)
    
    # convert to rgb 565
    r *= 31; g *= 63; b *= 31
    r2 *= 31;g2 *= 63;b2 *= 31
    
    r = round_clamp_int(r, 0, 31)
    g = round_clamp_int(g, 0, 63)
    b = round_clamp_int(b, 0, 31)
    r2 = round_clamp_int(r2, 0, 31)
    g2 = round_clamp_int(g2, 0, 63)
    b2 = round_clamp_int(b2, 0, 31)
    
    return (
        mhconfig.combine_color565(r,g,b),
        mhconfig.combine_color565(r2,g2,b2)
        )

def set_new_colors():
    ui_color, bg_color = get_random_colors()
    CONFIG['ui_color'] = ui_color
    CONFIG['bg_color'] = bg_color
    CONFIG.generate_palette()
    PIXEL_DISPLAY.color = ui_color
    
def update_time():
    global MONTH, DAY, HOUR_24, HOUR_12, MINUTE, AMPM
    _, MONTH, DAY, HOUR_24, MINUTE, _,_,_ = time.localtime()
    
    HOUR_12 = HOUR_24 % 12
    if HOUR_12 == 0:
        HOUR_12 = 12
    AMPM = 'AM'
    if HOUR_24 >= 12:
        AMPM = 'PM'
    

def get_day_suffix():
    _SUFFIX_MAP = const((
        'th','st','nd','rd'
        ))
    digit = int(str(DAY)[-1])
    if digit < len(_SUFFIX_MAP):
        return _SUFFIX_MAP[digit]
    else:
        return 'th'

def draw_battery(x,y):
    _BATT_WIDTH = const(36)
    _BATT_HEIGHT = const(18)
    _NUB_WIDTH = const(4)
    _NUB_HEIGHT = const(8)
    _NUB_Y_OFFSET = const((_BATT_HEIGHT-_NUB_HEIGHT)//2)
    _BATT_PADDING = const(2)
    _BATT_INNER_WIDTH = const(_BATT_WIDTH - (_BATT_PADDING*2))
    _BATT_INNER_HEIGHT = const(_BATT_HEIGHT - (_BATT_PADDING*2))
    
    _FILL_LEVELS = const((1, _BATT_INNER_WIDTH//3, (_BATT_INNER_WIDTH//3)*2, _BATT_INNER_WIDTH))
    
    level = BATT.read_level()
    DISPLAY.fill_rect(x+1,y+1,_BATT_WIDTH,_BATT_HEIGHT,0)
    DISPLAY.fill_rect(x+_BATT_WIDTH+1,y+_NUB_Y_OFFSET+1, _NUB_WIDTH, _NUB_HEIGHT, 0)
    
    DISPLAY.fill_rect(
        x,y,_BATT_WIDTH,_BATT_HEIGHT,
        _GRAY if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[2]
        )
    DISPLAY.fill_rect(
        x+_BATT_PADDING,y+_BATT_PADDING,_BATT_INNER_WIDTH,_BATT_INNER_HEIGHT,
        _BLACK if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[1]
        )
    DISPLAY.fill_rect(
        x+_BATT_WIDTH,y+_NUB_Y_OFFSET, _NUB_WIDTH, _NUB_HEIGHT,
        _GRAY if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[2]
        )
    
    # fill battery level
    DISPLAY.fill_rect(
        x+_BATT_PADDING+1,y+_BATT_PADDING+1,
        _FILL_LEVELS[level]-2,
        _BATT_INNER_HEIGHT-2,
        _GRAY if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[3]
        )
    
    
    
def draw_clock():
    _MONTH_NAMES = const((
        'Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'
        ))
    _COLON_WIDTH_PIXELS = const(1)
    _COLON_WIDTH = const(_COLON_WIDTH_PIXELS*_PX_SIZE)
    
    
    update_time()
    
    hour_str = str(HOUR_12)
    minute_str = '{:02d}'.format(MINUTE)
    
    PIXEL_DISPLAY.fill(0)
    PIXEL_DISPLAY.text(hour_str, 0,0, 1)
    PIXEL_DISPLAY.text(minute_str, len(hour_str)*8+_COLON_WIDTH_PIXELS, 0, 1)
    
    # draw background
    round_rect(
        CLOCK_X-2,CLOCK_Y-2,_CLOCK_BOX_WIDTH+4,_CLOCK_BOX_HEIGHT+4,19,
        _GRAY if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[2]
        )
    round_rect(
        CLOCK_X,CLOCK_Y,_CLOCK_BOX_WIDTH,_CLOCK_BOX_HEIGHT,17 ,
        _BLACK if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[0]
        )
    round_rect(
        CLOCK_X,CLOCK_Y,_CLOCK_BOX_WIDTH,_DATE_Y_OFFSET,17,
        _BLACK if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[1]
        )
    
    # calculate clock position
    current_clock_width = ((len(hour_str) + len(minute_str)) * _BIG_CHAR_WIDTH) + _AM_PM_WIDTH + _COLON_WIDTH
    time_centered_x = CLOCK_X + (_CLOCK_BOX_WIDTH_HALF - (current_clock_width//2))
    
    # draw clock
    PIXEL_DISPLAY.color = CONFIG.palette[0]
    PIXEL_DISPLAY.draw(time_centered_x+1, CLOCK_Y+_CLOCK_BOX_PADDING+2)
    PIXEL_DISPLAY.color = _WHITE if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[5]
    PIXEL_DISPLAY.draw(time_centered_x, CLOCK_Y+_CLOCK_BOX_PADDING)
    
    # draw ':'
    if frame_switcher(1000):
        DISPLAY.bitmap_text(font, ':', time_centered_x+(len(hour_str)*_BIG_CHAR_WIDTH)-4, CLOCK_Y+_CLOCK_BOX_PADDING+4, CONFIG.palette[0])
        DISPLAY.bitmap_text(
            font, ':', time_centered_x+(len(hour_str)*_BIG_CHAR_WIDTH)-5, CLOCK_Y+_CLOCK_BOX_PADDING+2,
            _GRAY if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[4]
            )
        
    # draw am/pm
    DISPLAY.bitmap_text(font, AMPM, time_centered_x+(current_clock_width)-_AM_PM_WIDTH+3, CLOCK_Y+_AMPM_Y_OFFSET+2, CONFIG.palette[0])
    DISPLAY.bitmap_text(
        font, AMPM, time_centered_x+(current_clock_width)-_AM_PM_WIDTH+2, CLOCK_Y+_AMPM_Y_OFFSET,
        _GRAY if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[3]
        )
    
    
    date_string = f"{_MONTH_NAMES[MONTH-1]} {DAY}"
    DISPLAY.bitmap_text(font, date_string, CLOCK_X+_DATE_X_OFFSET+1, CLOCK_Y+_DATE_Y_OFFSET+1, 0)
    DISPLAY.bitmap_text(
        font, date_string, CLOCK_X+_DATE_X_OFFSET, CLOCK_Y+_DATE_Y_OFFSET,
        _GRAY if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[4]
        )
    
    DISPLAY.text(get_day_suffix(), CLOCK_X+_DATE_X_OFFSET+(len(date_string)*_CHAR_WIDTH)+3, CLOCK_Y+_DATE_Y_OFFSET+5, 0)
    DISPLAY.text(
        get_day_suffix(), CLOCK_X+_DATE_X_OFFSET+(len(date_string)*_CHAR_WIDTH)+2, CLOCK_Y+_DATE_Y_OFFSET+4,
        _GRAY if POWER_MANAGER['sleep_state'] == _SLEEP_STATE_HOLD_DIM else CONFIG.palette[2]
        )
    
    draw_battery(CLOCK_X + _BATT_X_OFFSET, CLOCK_Y + _BATT_Y_OFFSET)
    
    

def move_box():
    global MOVING_RIGHT, MOVING_UP, CLOCK_X, CLOCK_Y, HAS_CHANGED_COLOR
    _X_DIVIDER = const(25431)
    _Y_DIVIDER = const(34451)
    
    timenow = time.ticks_ms()
    x_factor = ping_pong(timenow, _X_DIVIDER) / _X_DIVIDER
    y_factor = ping_pong(timenow, _Y_DIVIDER) / _Y_DIVIDER
    
    CLOCK_X = _CLOCK_MINIMUM_X + math.floor(round(x_factor * _MOVEMENT_WIDTH_X))
    CLOCK_Y = _CLOCK_MINIMUM_Y + math.floor(round(y_factor * _MOVEMENT_WIDTH_Y))
    
    # collision/changing colors
    
    if HAS_CHANGED_COLOR == False:
        if (CLOCK_X == _CLOCK_MINIMUM_X
            or CLOCK_X == _CLOCK_MAXIMUM_X
            or CLOCK_Y == _CLOCK_MINIMUM_Y
            or CLOCK_Y == _CLOCK_MAXIMUM_Y):
        
            set_new_colors()
            HAS_CHANGED_COLOR = True
        
    else: # HAS_CHANGED_COLOR == True
        if not (CLOCK_X == _CLOCK_MINIMUM_X
            or CLOCK_X == _CLOCK_MAXIMUM_X
            or CLOCK_Y == _CLOCK_MINIMUM_Y
            or CLOCK_Y == _CLOCK_MAXIMUM_Y):
            HAS_CHANGED_COLOR = False


#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def main_loop():
    """
    The main loop of the program. Runs forever (until program is closed).
    """
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INITIALIZATION: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    # If you need to do any initial work before starting the loop, this is a decent place to do that.
    set_new_colors()
    # create variable to remember text between loops
    current_text = "Hello World!" 
    
    counter = 0
    
    while True:
        
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ INPUT: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        # get list of newly pressed keys
        keys = KB.get_new_keys()
        
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ MAIN GRAPHICS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        POWER_MANAGER.manage()
        
        if counter == 0 or keys:
            move_box()
            DISPLAY.fill(0)
            draw_clock()
            DISPLAY.show()
        elif counter % 5 == 0:
            move_box()
            
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ HOUSEKEEPING: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        
        if keys:
            time.sleep_ms(1)
        else:
            time.sleep_ms(10)
            
        counter = (counter + 1) % 10

# start the main loop
main_loop()