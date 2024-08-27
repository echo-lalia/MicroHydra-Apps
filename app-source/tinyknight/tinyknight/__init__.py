from machine import Pin, SPI
import time
import random

from . import keyboard

from . import st7789py
from . import knight_sprites as knight_bitmap
from . import vga1_bold_16x32 as big_font
from . import vga1_8x8 as small_font

tft = st7789py.ST7789(
    SPI(1, baudrate=40000000, sck=Pin(36), mosi=Pin(35), miso=None),
    135,
    240,
    reset=Pin(33, Pin.OUT),
    cs=Pin(37, Pin.OUT),
    dc=Pin(34, Pin.OUT),
    backlight=Pin(38, Pin.OUT),
    rotation=1,
    color_order=st7789py.BGR
)

tft.needs_swap = True

kb = keyboard.KeyBoard()

# GAME VARS
SPEED_INCREASE_EVERY = 8
ADD_TOP_BLOCKS_WHEN_SPEED = 12

class Obstacle:
    def __init__(self):
        self.col = 238
        self.row = 100
        self.width = 16
        self.height = 28
        self.color = st7789py.WHITE
        self.overshoot = random.randint(4, 60)
        self.speed = 7
        self.count = 0
        self.prev_col = self.col
        self.prev_row = self.row

    def move(self, score):
        self.prev_col = self.col
        self.prev_row = self.row
        
        self.col -= self.speed
        if self.col < - self.width - self.overshoot:
            self.col = 240 + self.width
            self.randomize()
            self.count +=1
            score+=5
            if self.count > SPEED_INCREASE_EVERY:
                self.count = 0
                self.speed +=1
            
    def randomize(self):
        self.width = random.randint(4,20)
        self.height = random.randint(12,32)
        self.row = 128 - self.height
        self.color = random.getrandbits(16)
        self.overshoot = random.randint(4, 60)
        
        if self.speed > ADD_TOP_BLOCKS_WHEN_SPEED:
            if random.randint(0,1):
                self.row = random.randint(30, 50)
                
        self.prev_col = self.col
        self.prev_row = self.row
    
    def draw(self):
        # overdraw previous
        tft.fill_rect(self.prev_col, self.prev_row, self.width, self.height, st7789py.BLACK)
        tft.fill_rect(self.col, self.row, self.width, self.height, self.color)

class Knight:
    def __init__(self, bitmap):
        self.bitmap = bitmap
        self.col = 1
        self.row = 100
        self.width = bitmap.WIDTH
        self.height = bitmap.HEIGHT
        self.frame = 0
        self.y_velocity = 0
        self.grounded = True
        self.buffered_jump = False
        self.dead = False
        self.visible = True
        self.prev_col = self.col
        self.prev_row = self.row
        
        # used in the opening
        self.introComplete = False
        self.inCollision = False
        self.inTransition = False
        self.waitingForInput = False
        
    def animateOpening(self):
        if self.inTransition:
            # slide everything left
            self.col -= 4
            if self.col < 10:
                self.col = 10
                self.inTransition = 0
                self.introComplete = True
            return
        
        if self.inCollision:
            self.row += self.y_velocity
            self.y_velocity += 3
            if self.row > 100:
                self.row = 100
                self.inCollision = False
                self.waitingForInput = True
            return
        
        if not self.waitingForInput:
            if self.col < 224:
                # no collision yet
                self.col += 4
                self.frame += 1
                if self.frame > 3:
                    self.frame = 0
            else:
                self.inCollision = True
                self.y_velocity = -10
                self.col = 224
                self.frame = 4
            
        
        
    def move(self, obstacle):
        self.prev_col = self.col
        self.prev_row = self.row
        if not self.visible:
            return
        # y position    
        if not self.grounded or self.dead:
            if self.row + self.y_velocity > 100 and not self.dead:
                # would touch ground next frame
                self.row = 100
                self.y_velocity = 0
                self.grounded = True
                
                if self.buffered_jump and not self.dead:
                    self.jump()
                    self.buffered_jump = False
            elif self.row + self.y_velocity > 100 and self.dead:
                self.visible = False
            else:
                self.row += self.y_velocity
                self.y_velocity += 3
            
        # animation
        if self.dead:
            self.frame = 4
        elif self.grounded:
            self.frame += 1
            if self.frame > 3:
                self.frame = 0
        else:
            self.frame = 1
    
    def jump(self):
        if not self.visible:
            return
        if self.grounded:
            self.y_velocity = -20
            self.row = 99
            self.grounded = False
        elif self.row > 60:
            self.buffered_jump = True
            
    
    def draw(self):
        if not self.visible:
            return
        # overdraw previous
        tft.fill_rect(self.prev_col, self.prev_row, self.width, self.height, st7789py.BLACK)
        tft.bitmap(self.bitmap, self.col, self.row, self.frame)
        
def check_collisions(sprite, obstacle):
    if (
            sprite.col < obstacle.col + obstacle.width and
            sprite.col + sprite.width > obstacle.col and
            sprite.row < obstacle.row + obstacle.height and
            sprite.row + sprite.height > obstacle.row
          ) :
            sprite.dead = True
            sprite.y_velocity = -20
        
def show_menu(sprite):
    title = "tinyKnight"
    length = len(title)
    
    tft.fill(st7789py.BLACK)
    tft.text(big_font, title, tft.width // 2 - length // 2 * big_font.WIDTH,
        tft.height // 2 - big_font.HEIGHT)
    
    tft.show()
    
    pressed_keys = []
    prev_pressed_keys = []
    
    play_game = False
    
    while not play_game:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if "ENT" in pressed_keys and "ENT" not in prev_pressed_keys: # up arrow
                sprite.inTransition = True
                sprite.waitingForInput = False
        
        if sprite.introComplete:
            play_game = True
                
        sprite.animateOpening()
        tft.fill(st7789py.BLACK)
        tft.text(big_font, title, tft.width // 2 - length // 2 * big_font.WIDTH,
            tft.height // 2 - big_font.HEIGHT)
        tft.hline(0, 128, 240, st7789py.WHITE)
        if sprite.waitingForInput:
            tft.text(small_font, "ok to start", 126, 116)
        sprite.draw()
        tft.show()
        
def play_game():
    tft.fill(st7789py.BLACK)
    tft.show()

    score = 0

    sprite = Knight(knight_bitmap)

    obstacle = Obstacle()

    show_menu(sprite)
    
    pressed_keys = []
    prev_pressed_keys = []

    isGameOver = False
    
    tft.fill(st7789py.BLACK)
    tft.show()
    
    while not isGameOver:
        score += 1
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            if ";" in pressed_keys and ";" not in prev_pressed_keys: # up arrow
                sprite.jump()
                
        prev_pressed_keys = pressed_keys
        
        tft.hline(0, 128, 240, st7789py.WHITE)
        tft.text(small_font, str(score), tft.width - len(str(score)) * small_font.WIDTH,
            2)
        
        sprite.move(obstacle)
        obstacle.move(score)
        check_collisions(sprite, obstacle)
        isGameOver = not sprite.visible
        
        sprite.draw()
        obstacle.draw()
        tft.show()
        
        time.sleep(0.01)
        
    gameover_text = "Game Over"
    tft.text(big_font, gameover_text, tft.width // 2 - len(gameover_text) // 2 * big_font.WIDTH,
            tft.height // 2 - big_font.HEIGHT)
    score_text = "Score: " + str(score)
    tft.text(small_font, score_text, tft.width // 2 - len(score_text) // 2 * small_font.WIDTH,
            tft.height // 2 - small_font.HEIGHT + 40)
    tft.show()
    end_screen = True
    while end_screen:
        pressed_keys = kb.get_pressed_keys()
        if pressed_keys != prev_pressed_keys:
            end_screen = False

while True:
    play_game()

