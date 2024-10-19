"""Fish.

Designed for the M5Stack Cardputer.

A fish swims across the screen.

Press "P" to enter play mode and the fish will swim through a hoop.
Press "ESC" to return to default mode.
Press "F" to feed the fish. The fish's health will increase when fed.
Press "G0" to exit.

Author: Dan Ruscoe (danruscoe@protonmail.com)
Version: 1.0.0
"""

import time

from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput
from machine import reset
from random import randint

_DISPLAY_HEIGHT = const(135)
_DISPLAY_WIDTH = const(240)
_FRAME_INTERVAL = const(10)
_FISH_WIDTH = const(25)
_FISH_HEIGHT = const(12)
_FISH_TAIL_LENGTH = const(10)
_FISH_EYE_SIZE = const(2)
_FISH_SPEED = const(1)
_HOOP_DIAMETER = const(40)
_FOOD_DIAMETER = const(4)
_FOOD_SPEED = const(2)
_MAX_HEALTH = const(3)
_HEALTH_DEGRADE_DELAY = const(10000)
_TERRAIN_BLOCK_SIZE = const(5)
_HUD_ICON_SIZE = const(3)

tft = Display()
config = Config()
kb = UserInput()

fish_direction = 1
fish_health = 0
health_delta = 0
fish_x = (_DISPLAY_WIDTH // 2)
fish_y = (_DISPLAY_HEIGHT // 2)
food_x = 0
food_y = 0
play_mode = False
feed_mode = False
terrain = []

def process_input():
    global play_mode

    keys = kb.get_new_keys()

    if keys:
        # "G0" button exits to the launcher.
        if "G0" in keys:
            reset()
        # Esc with or without Fn key to exit all modes.
        if "ESC" in keys or "`" in keys:
            play_mode = False
        # P to enter play mode.
        if "p" in keys:
            play_mode = True
        # F to enter feed mode.
        if "f" in keys:
            spawn_food()

def draw_terrain():
    global terrain

    for i in range(0, len(terrain)):
        tft.fill_rect((i * _TERRAIN_BLOCK_SIZE), (_DISPLAY_HEIGHT - terrain[i]), _TERRAIN_BLOCK_SIZE, terrain[i], config.palette[8])

def draw_fish():
    global fish_x
    global fish_y
    global play_mode

    # Draw the fish's body.
    tft.ellipse(fish_x, fish_y, _FISH_WIDTH, _FISH_HEIGHT, config.palette[8], True)
    # Draw the fish's eye.
    tft.ellipse((fish_x + ((_FISH_WIDTH - 10) * fish_direction)), fish_y, _FISH_EYE_SIZE, _FISH_EYE_SIZE, config.palette[0], True)
    # Draw the fish's tail.
    for i in range(0, _FISH_TAIL_LENGTH):
        tft.line(((fish_x - (_FISH_WIDTH * fish_direction)) - (i * fish_direction)), (fish_y + i), ((fish_x - (_FISH_WIDTH * fish_direction )) - (i * fish_direction)), (fish_y - i), config.palette[8])

def draw_hoop():
    tft.ellipse((_DISPLAY_WIDTH // 2), (_DISPLAY_HEIGHT // 2), _HOOP_DIAMETER, _HOOP_DIAMETER, config.palette[8], False)

def draw_food():
    tft.ellipse(food_x, food_y, _FOOD_DIAMETER, _FOOD_DIAMETER, config.palette[8], True)

def draw_hud():
    global fish_health, health_delta

    if (health_delta >= _HEALTH_DEGRADE_DELAY):
        fish_health -= 1

        if (fish_health <= 0):
            fish_health = 0

        health_delta = 0

    for i in range(1, 4):
        fill_icon = (fish_health >= i)
        tft.ellipse(((_HUD_ICON_SIZE * 3) * i), (_HUD_ICON_SIZE * 2), _HUD_ICON_SIZE, _HUD_ICON_SIZE, config.palette[8], fill_icon)

def spawn_food():
    global feed_mode
    global food_x
    global food_y

    feed_mode = True

    food_x = randint(0, _DISPLAY_WIDTH)
    food_y = 0

def move_food():
    global fish_direction
    global fish_y
    global food_y

    if (food_y < (_DISPLAY_HEIGHT // 2)):
        food_y += _FOOD_SPEED
    else:
        if ((food_x < fish_x) & (fish_direction == 1)):
            fish_direction = -1
        elif ((food_x > fish_x) & (fish_direction == -1)):
            fish_direction = 1

def eat_food():
    global feed_mode
    global fish_health

    fish_health += 1

    if (fish_health >= _MAX_HEALTH):
        fish_health = _MAX_HEALTH

    feed_mode = False

def move_fish():
    global fish_direction
    global fish_x
    global fish_y

    # Move fish forwards (relative to the fish's direction).
    fish_x += (_FISH_SPEED * fish_direction)

    # Reverse the fish's direction if it reaches the edge of the screen.
    if ((fish_direction == 1) & (fish_x >= _DISPLAY_WIDTH)):
        fish_direction = -1
    elif ((fish_direction == -1) & (fish_x <= 0)):
        fish_direction = 1

def main_loop():
    global terrain, health_delta

    i = 0
    while i < _DISPLAY_WIDTH:
        height = randint(_TERRAIN_BLOCK_SIZE, (_TERRAIN_BLOCK_SIZE * 2))
        terrain.append(height)
        i += _TERRAIN_BLOCK_SIZE

    while True:
        tft.fill(config.palette[2])

        process_input()

        if (feed_mode == True):
            move_food()
            draw_food()

            if (fish_x == food_x):
                eat_food()

        move_fish()
        draw_terrain()
        draw_fish()

        if (play_mode == True):
            draw_hoop()

        draw_hud()

        tft.show()

        health_delta += _FRAME_INTERVAL

        time.sleep_ms(_FRAME_INTERVAL)

main_loop()
