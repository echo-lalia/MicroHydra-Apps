import time, esp32, json, os, machine

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CONSTANTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
_SEPARATOR = const("|//|")
_PATH_HERE_FLASH = const("/apps/")
_PATH_HERE_SD = const("/sd/apps/")


# sleep states
_SLEEP_HOLD_BRIGHT = const(0)
_SLEEP_DIMMING = const(1)
_SLEEP_HOLD_DIM = const(2)
_SLEEP_HOLD_DISPLAY_OFF = const(3)
# sleep state times (milliseconds)
_TIME_HOLD_BRIGHT = const(10000)
_TIME_DIMMING = const(20000)
_TIME_HOLD_DIM = const(60000)
_TIME_HOLD_DISPLAY_OFF = const(10000)

_DEFAULT_CONFIG = const('{"sleep_timer": null, "sleep_state": 0}')

_LOOP_SLEEP_MS = const(100)

_MAX_BRIGHT = const(65535)
_MIN_BRIGHT = const(8000)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ GLOBAL OBJECTS: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SLEEP_MANAGER = None

RTC = None
CONFIG = None

DISPLAY = None
KB = None
BLIGHT = None

APP_NAME = None

#--------------------------------------------------------------------------------------------------
#-------------------------------------- FUNCTION DEFINITIONS: -------------------------------------
#--------------------------------------------------------------------------------------------------

def mix(val2, val1, fac=0.5):
    """Mix two values to the weight of fac"""
    output = (val1 * fac) + (val2 * (1.0 - fac))
    return output

    

#--------------------------------------------------------------------------------------------------
#--------------------------------------- CLASS DEFINITIONS: ---------------------------------------
#--------------------------------------------------------------------------------------------------

# class handles reading/writing current app state, which can be stored in memory
class SleepManager:
    def __init__(self, rtc, config, display, kb):
        global SLEEP_MANAGER, RTC, CONFIG, DISPLAY, KB, BLIGHT, APP_NAME
        
        
        SLEEP_MANAGER = self
        RTC = rtc
        CONFIG = config
        DISPLAY = display
        KB = kb
        BLIGHT = DISPLAY.backlight
        BLIGHT.duty_u16(_MAX_BRIGHT)
        
        mem = rtc.memory().decode()
        try:
            self.state = json.loads(mem)
        except ValueError:
            self.state = json.loads(_DEFAULT_CONFIG)
            
        self.state["sleep_timer"] = time.ticks_ms()
        self.state["sleep_state"] = _SLEEP_HOLD_BRIGHT
        
        APP_NAME = __name__.replace('.','/').split('/')[-2]
        
    def __getitem__(self, key):
        return self.state[key]
    def __setitem__(self, key, value):
        self.state[key] = value
    
    
    def store(self):
        """Store our state in the RTC memory"""
        # check if we live in the apps path
        path_list = __name__.replace('.','/').split('/')
        if path_list[0] == "sd" or path_list[1] == "sd":
            rtcdata = _PATH_HERE_SD + APP_NAME + _SEPARATOR + json.dumps(self.state)
        else:
            rtcdata = _PATH_HERE_FLASH + APP_NAME + _SEPARATOR + json.dumps(self.state)
        print(path_list)
        print(rtcdata)
        RTC.memory(rtcdata)

    def go_to_sleep(self):
        print('going to sleep...')
        # sleep display
        DISPLAY.inversion_mode(False)
        DISPLAY.inversion_mode(True)
        DISPLAY.fill(0)
        DISPLAY.show()
        DISPLAY.sleep_mode(True)
        
        # turn off keyboard output pins
        KB.a0.value(0)
        KB.a1.value(0)
        KB.a2.value(0)
        
        # set up deep sleep
        self.store()
        esp32.wake_on_ext0(pin = KB.G0, level = esp32.WAKEUP_ALL_LOW)
        machine.deepsleep()

        
    def track_sleep_time(self):
        
        # reset sleep time when any key is pressed
        if KB.key_state:
            self['sleep_timer'] = time.ticks_ms()
            self['sleep_state'] = _SLEEP_HOLD_BRIGHT
            BLIGHT.duty_u16(_MAX_BRIGHT)
            return
        
        # remember the start time if not already set
        if not self['sleep_timer']:
            self['sleep_timer'] = time.ticks_ms()

        state = self['sleep_state']
        time_elapsed = time.ticks_diff(time.ticks_ms(), self['sleep_timer'])
        
        if state == _SLEEP_HOLD_BRIGHT: # hold bright for a set amount of time
            
            if time_elapsed >= _TIME_HOLD_BRIGHT:
                self['sleep_state'] = _SLEEP_DIMMING
                self['sleep_timer'] = time.ticks_ms()
            return
            
        elif state == _SLEEP_DIMMING: # dim display from light to dark
            
            if time_elapsed >= _TIME_DIMMING:
                BLIGHT.duty_u16(_MIN_BRIGHT)
                self['sleep_state'] = _SLEEP_HOLD_DIM
                self['sleep_timer'] = time.ticks_ms()
            
            else:
                fac = time_elapsed / _TIME_DIMMING
                BLIGHT.duty_u16(int(
                    mix(_MAX_BRIGHT, _MIN_BRIGHT, fac)
                    ))
            return
        
        elif state == _SLEEP_HOLD_DIM: # hold at a dim level for a while
            if time_elapsed >= _TIME_HOLD_DIM:
                self['sleep_state'] = _SLEEP_HOLD_DISPLAY_OFF
                self['sleep_timer'] = time.ticks_ms()
                BLIGHT.duty_u16(0)
            return
                
        elif state == _SLEEP_HOLD_DISPLAY_OFF: # hold with the display off for a while, before deep sleeping
            if time_elapsed >= _TIME_HOLD_DISPLAY_OFF:
                self.go_to_sleep()
            return
    
#--------------------------------------------------------------------------------------------------
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ Main Loop: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def manage(self):
        """Run a single cycle of SleepManager's logic"""
        self.track_sleep_time()

    
if __name__ == '__main__':
    from apps import Clock_LE