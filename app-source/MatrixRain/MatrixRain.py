import time, random
from lib.display import Display

# Initialize display
display = Display()
SCREEN_WIDTH = display.width
SCREEN_HEIGHT = display.height

CHAR_WIDTH = 8
CHAR_HEIGHT = 12
POSSIBLE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
NUM_DROPS = (SCREEN_WIDTH // CHAR_WIDTH) // 2

HEAD_COLOR = 0xFFFF
TAIL_COLOR = 0x07E0  # Green

class RainDrop:
    def __init__(self, x):
        self.x = x
        self.reset()
    def reset(self):
        self.y = random.randint(-SCREEN_HEIGHT, 0)
        self.length = random.randint(5, 15)
        self.speed = random.randint(1, 3)
        self.chars = [random.choice(POSSIBLE_CHARS) for _ in range(self.length)]

drops = []
for i in range(NUM_DROPS):
    drop_x = i * (CHAR_WIDTH * 2)
    if drop_x < SCREEN_WIDTH - CHAR_WIDTH:
        drops.append(RainDrop(drop_x))
    else:
        last_possible_x = SCREEN_WIDTH - CHAR_WIDTH
        offset_for_remaining = (NUM_DROPS - i) * CHAR_WIDTH 
        calculated_x = last_possible_x - offset_for_remaining
        drops.append(RainDrop(max(0, calculated_x)))

while True:
    display.fill(0x0000)  # Clear screen to black
    for drop in drops:
        drop.y += drop.speed
        if drop.y - (drop.length * CHAR_HEIGHT) > SCREEN_HEIGHT:
            drop.reset()
        for i in range(drop.length):
            char_y = drop.y - (i * CHAR_HEIGHT)
            color = HEAD_COLOR if i == 0 else TAIL_COLOR
            if 0 <= char_y < SCREEN_HEIGHT:
                display.text(drop.chars[i % len(drop.chars)], drop.x, char_y, color)
    display.show()
    time.sleep(0.05)
