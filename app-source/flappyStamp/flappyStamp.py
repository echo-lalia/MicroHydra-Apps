"""A simple little game for MicroHydra."""

from lib.display.fancydisplay import FancyDisplay
from lib.hydra.beeper import Beeper
from lib.hydra.config import Config
from lib.userinput import UserInput
from machine import freq
from array import array
import math, time, random
import _thread
from esp32 import NVS
from font import vga2_16x32 as fontbig
from font import vga1_8x16 as fontsmall



# ~~~~~~~~~~~~~~~~~~~~~~~~~~ constants and globals: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

bg_color1 = const(0)
bg_color2 = const(2051)

stamp_shape = array('h',( 1,3, 3,1, 28,1, 30,3,   30,20, 28,22, 3,22, 1,20 ))
stamp_usb = array('h',( 31,8, 33,8, 33,15, 31,15 ))
stamp_eye  = array('h', (19,9, 21,7, 25,7, 26,8, 26,12, 19,12))
stamp_pupil  = array('h', (23,8, 24,8, 24,10, 23,10))
stamp_gpio = array('h', (4,19, 7,16, 20,16, 18,19))

stamp_title = array('h', (4,4, 10,4, 10,12, 4,12))
stamp_btn = array('h', (13,4, 16,4, 16,12, 13,12))

diamond_shape = array('h',(12,0, 24,12, 12,24, 0,12))

scroll_rate = -2





freq(240_000_000)

tft = FancyDisplay()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~ functions: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def ease_in_circ(x: float) -> float:
    """Apply easing."""
    return 1 - math.sqrt(1 - (x ** 2))


def digi_gradient(tft,x,y,width,height,color1,color2):
    """Draw a simple gradient-like pattern of lines."""

    gap_height = 13

    bar_height = 1

    write_y = y

    while write_y < height + y:
        tft.rect(x,write_y,width,bar_height,color1,fill=True)
        write_y += bar_height
        tft.rect(x,write_y,width,gap_height,color2,fill=True)
        write_y += gap_height

        if gap_height > 1:
            gap_height -= 1
        else:
            bar_height += 1


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ CLASSES: ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Obstacle:
    """The obsticals to dodge."""

    def __init__(self, tft: FancyDisplay, x: int, gaps: list[int, int]):
        """Create an obstical at the given X."""
        self.x = x
        self.y = random.randint(0,85)
        self.gaps = gaps
        self.gap = random.randint(gaps[0],gaps[1])
        self.style = -1
        self.tft = tft
        self.counted = True # has it already been counted

    def randomize(self):
        """Re-randomize the obstical."""
        self.gap = random.randint(gaps[0],gaps[1])
        self.y = random.randint(0,135-self.gap)
        self.style = random.randint(0,2)

    def draw(self):
        """Draw the obstical."""
        tft = self.tft

        #only draw when we are on the right edge, otherwise scrolling will take care of it
        if self.style == 0:
            #draw ourselves in our current location

            #top memory
            top_height = self.y

            num_chips = top_height // 20

            tft.rect(self.x, 0, 40, top_height, 1093, fill=True)
            tft.rect(self.x+2, 0, 4, top_height-10, 65300,fill=True)

            tft.hline(self.x, top_height, 40, 992)

            for i in range(num_chips):
                tft.rect(self.x+14, self.y-24 - (24*i) , 22, 18, 12678,fill=True)

            #bottom memory
            bottom_start_point = top_height + self.gap
            bottom_height = 136 - bottom_start_point

            num_chips = bottom_height // 20

            tft.rect(self.x, bottom_start_point, 40, bottom_height, 1093, fill=True)
            tft.rect(self.x+2, bottom_start_point+10, 4, bottom_height, 65300,fill=True)

            for i in range(num_chips):
                tft.rect(self.x+14, bottom_start_point + 6 + (24*i) , 22, 18, 12678,fill=True)

            tft.hline(self.x, bottom_start_point-1, 40, 9509)

            #right bar prevents streaks on display
            digi_gradient(tft,self.x+40,0,3,135,bg_color1 ,bg_color2)
            #tft.rect(self.x+40, 0, 2, 135, 0)

        elif self.style == 1:
            #draw ourselves in our current location

            #top board
            top_height = self.y

            tft.rect(self.x, 0, 40, top_height, 12851, fill=True)
            tft.rect(self.x + 8, top_height - 8, 24, 4, 27536, fill=True)

            if top_height > 40:
                tft.polygon(diamond_shape,self.x + 8, top_height - 54, 12678, fill=True)
            else:
                tft.polygon(diamond_shape,self.x + 8, top_height - 42, 12678, fill=True)

            tft.hline(self.x, top_height, 40, 2127)

            #bottom board
            bottom_start_point = top_height + self.gap
            bottom_height = 136 - bottom_start_point

            tft.rect(self.x, bottom_start_point-1, 40, bottom_height, 12851, fill=True)

            tft.hline(self.x, bottom_start_point-1, 12, 23412  )
            tft.hline(self.x+12, bottom_start_point-1, 16, 38066)
            tft.hline(self.x+28, bottom_start_point-1, 12, 23412   )

            tft.rect(self.x + 12, bottom_start_point, 16, 18, 27536 , fill=True)

            tft.rect(self.x + 11, bottom_start_point + 28, 18, 18, 12678, fill=True)

            #right bar prevents streaks on display
            digi_gradient(tft,self.x+40,0,3,135,bg_color1 ,bg_color2)

        elif self.style == 2:
            #top board
            top_height = self.y

            tft.rect(self.x, 0, 40, top_height, 1093, fill=True)
            tft.rect(self.x+5, 0, 30, top_height-10, 12678, fill=True)
            tft.rect(self.x+9, 0, 22, top_height-14, 12851 , fill=True)

            tft.hline(self.x, top_height, 40, 992)

            #bottom board
            bottom_start_point = top_height + self.gap
            bottom_height = 136 - bottom_start_point

            tft.rect(self.x, bottom_start_point-1, 40, bottom_height, 1093, fill=True)
            tft.rect(self.x+5, bottom_start_point + 10, 30, bottom_height-10, 12678, fill=True)
            tft.rect(self.x+9, bottom_start_point + 14, 22, bottom_height-14, 12851 , fill=True)

            tft.hline(self.x, bottom_start_point-1, 40, 9509 )
            #right bar prevents streaks on display
            digi_gradient(tft,self.x+40,0,3,135,bg_color1 ,bg_color2)


    def move(self, scroll_rate: int):
        """Move the obstical."""
        self.x += scroll_rate
        if self.x <= -70:
            self.x = 240
            self.randomize()
            self.counted = False



class Stamp:
    """The player class."""

    def __init__(self, tft: FancyDisplay, x: int, y: int):
        """Initialize the player."""
        self.x = x
        self.y = y
        self.tft = tft
        self.angle = 0

    def draw(self):
        """Draw the player."""
        self.tft.polygon(stamp_shape,self.x,self.y,50744, angle=self.angle, center_x=15, center_y=11,fill=True)
        self.tft.polygon(stamp_shape,self.x,self.y,63357, angle=self.angle, center_x=15, center_y=11)
        self.tft.polygon(stamp_usb, self.x, self.y, 50712, angle=self.angle, center_x=15, center_y=11,fill=True)
        self.tft.polygon(stamp_eye,self.x,self.y,34971, angle=self.angle, center_x=15, center_y=11)
        self.tft.polygon(stamp_pupil,self.x,self.y,0, angle=self.angle, center_x=15, center_y=11,fill=True)
        self.tft.polygon(stamp_gpio,self.x,self.y,25977, angle=self.angle, center_x=15, center_y=11,fill=True)
        self.tft.polygon(stamp_title,self.x,self.y,50452, angle=self.angle, center_x=15, center_y=11,fill=True)
        self.tft.polygon(stamp_btn,self.x,self.y,30223, angle=self.angle, center_x=15, center_y=11,fill=True)



def title(tft: FancyDisplay, score: int, high_score: int, shared_data: dict, lock: _thread.LockType):
    """Draw the title text."""
    tft.ellipse(120,44,90,10,bg_color1,fill=True)
    tft.text("FlappyStamp!", 29,18,47489, font=fontbig)
    tft.text("FlappyStamp!", 28,16,53710, font=fontbig)
    tft.text("FlappyStamp!", 27,14,60230, font=fontbig)
    tft.text("FlappyStamp!", 26,12,62674, font=fontbig)
    tft.text("FlappyStamp!", 25,10,47489, font=fontbig)
    tft.text("FlappyStamp!", 24,9, 57116, font=fontbig)

    tft.ellipse(60,70,28,12,bg_color1, fill=True)
    tft.ellipse(180,70,28,12,bg_color1, fill=True)
    tft.text( "Score:", 38, 64, 47489, font=fontsmall)
    tft.text( "Best:", 162, 64, 47489, font=fontsmall)
    tft.text( "Score:", 38, 63, 57116, font=fontsmall)
    tft.text( "Best:", 162, 63, 57116, font=fontsmall)

    tft.rect(55 - (len(str(score)) * 8), 90, 10 +(len(str(score)) * 16),32, bg_color1 , fill=True)
    tft.rect(175 - (len(str(high_score)) * 8), 90, 10 +(len(str(high_score)) * 16), 32, bg_color1 , fill=True)

    tft.text( str(score), 61 - (len(str(score)) * 8), 92, 47489, font=fontbig)
    tft.text( str(score), 60 - (len(str(score)) * 8), 90, 57116, font=fontbig)

    tft.text( str(high_score), 181 - (len(str(high_score)) * 8), 92, 47489, font=fontbig)
    tft.text( str(high_score), 180 - (len(str(high_score)) * 8), 90, 57116, font=fontbig)

    tft.show()
    time.sleep_ms(100)

    while True:
        time.sleep_ms(10)

        with lock:
            if shared_data["new_keys"]:
                digi_gradient(tft,0,0,240,135,bg_color1 ,bg_color2)
                return


# thread1 can take care of our timing stuff.
# thread1 cant access spi without thread0 sleeping
def thread_1(lock: _thread.LockType, shared_data: dict):  # noqa: PLR0915
    """Run the main loop for the second thread."""
    import time, _thread, math
    from lib.userinput import UserInput  # noqa: F811
    from esp32 import NVS

    nvs = NVS("flappyStamp")
    high_score = 0
    try:
        high_score = nvs.get_i32("high_score")
    except:
        nvs.set_i32("high_score",0)
        nvs.commit()

    kb = UserInput()
    pressed_keys = set(kb.get_pressed_keys())
    prev_pressed_keys = pressed_keys

    obs = shared_data["obs"]
    stamp = shared_data["stamp"]

    stamp_accel = 0
    stamp_exact_y = stamp.y
    points = 0
    hit = False


    while True:
        # without sleep the other thread cant use spi
        time.sleep_ms(1)

        # gravity
        stamp_accel += 0.004

        pressed_keys = set(kb.get_pressed_keys())

        new_keys = pressed_keys.copy()
        new_keys -= prev_pressed_keys

        if new_keys:
            stamp_accel = -0.4

        # update our character's position!
        if not hit:
            stamp_exact_y += stamp_accel
            if stamp_exact_y >= 110:
                stamp_exact_y = 110
                stamp_accel = 0
            elif stamp_exact_y <= 0:
                stamp_exact_y = 0
                stamp_accel = 0
            stamp.y = math.floor(stamp_exact_y)
            stamp.angle = stamp_accel

        # count number of passed obs
        for ob in obs:
            if not ob.counted and ob.x < 20:
                ob.counted = True
                points += 1

            # check for collisions!
            # first narrow by x position, and dont count invisible obs
            # then narrow by y position of stamp
            if (-5 < ob.x < 35 and ob.style != -1) \
            and (ob.y > stamp.y + 2 or (ob.y + ob.gap) < (stamp.y + 25)):
                if points > high_score:
                    high_score = points
                    nvs.set_i32("high_score", high_score)
                    nvs.commit()
                hit = True

        with lock:
            shared_data['score'] = points
            shared_data["score_width"] = len(str(points)) * 8
            shared_data["hit"] = hit
            shared_data["high_score"] = high_score
            shared_data['new_keys'] = new_keys
            if shared_data['restarting']:
                shared_data['restarting'] = False
                points = 0
                stamp_accel = 0
                stamp_exact_y = 60
                hit = False
        prev_pressed_keys = pressed_keys


config = Config()
ui_sound = config["ui_sound"]

beep = Beeper()


nvs = NVS("flappyStamp")
high_score = 0
try:
    high_score = nvs.get_i32("high_score")
except:
    nvs.set_i32("high_score", 0)
    nvs.commit()

digi_gradient(tft, 0, 0, 240, 135, bg_color1, bg_color2)

# shared list of two values for min/max gaps
gaps = [60, 100]

obs = (Obstacle(tft, 240, gaps), Obstacle(tft, 85, gaps))

stamp = Stamp(tft,10,60)

lock = _thread.allocate_lock()
shared_data = {
    "tft":tft,
    "stamp":stamp,
    "obs":obs,
    "new_keys":set(),
    "score":0,
    "score_width":8,
    "hit":False,
    "high_score":high_score,
    "restarting":False,
}

_thread.start_new_thread(thread_1, (lock, shared_data))

score = 0
score_width = 8

title(tft, score, high_score, shared_data, lock)
beep.play(("C3","C4","C4"), 100)
hit = False

while True:
    # blank out area behind stamp
    digi_gradient(tft,0,0,50,135,bg_color1 ,bg_color2)

    # calculate new gaps difficulty from current score
    # min gap
    gaps[0] = max(60 - (score // 3), 40)
    gaps[1] = max(110 - score,60)
    # very hard to get through a gap of 40-45, but speed actually makes it more possible.
    if gaps[0] <= 45:
        scroll_rate = -3

    for ob in obs:
        ob.move(scroll_rate)
        ob.draw()

    stamp.draw()

    # lock
    with lock:
        score = shared_data["score"]
        score_width = shared_data["score_width"]
        hit = shared_data["hit"]
        high_score = shared_data["high_score"]


    if hit:
        hit = False
        time.sleep_ms(100)

        # hit animation
        digi_gradient(tft,0,0,240,135,bg_color1 ,bg_color2)
        obs[0].draw()
        obs[1].draw()
        stamp.draw()
        beep.play(("E3","C3","C3"), 100)
        stamp_accel = -4
        stamp_exact_y = stamp.y
        for i in range(100):
            time.sleep_ms(10)
            stamp_accel += 0.5
            stamp_exact_y += stamp_accel
            stamp.y = math.floor(stamp_exact_y)
            stamp.angle = stamp_accel / 2
            digi_gradient(tft,0,0,50,135,bg_color1 ,bg_color2)

            if obs[0].x < obs[1].x:
                obs[0].draw()
            else:
                obs[1].draw()

            stamp.draw()
            tft.show()
            if stamp.y > 100 and i > 50:
                break

        title(tft,score,high_score,shared_data, lock)
        beep.play(("C3","C4","C4"), 100)
        with lock:
            shared_data["restarting"] = True
        # reset game
        score = 0
        stamp.y = 60
        for ob in obs:
            ob.style = -1
            ob.counted = True
        obs[0].x = 240; obs[1].x = 85

    # scorecard
    tft.rect(118 - (score_width // 2),5,score_width + 4,12,bg_color2,fill=True)
    tft.hline(120 - (score_width // 2),17,score_width,bg_color1)
    tft.text(str(score),120 - (score_width // 2), 8, 50744)

    tft.show()

    time.sleep_us(10)
