# heavily influenced and inspired by:
# https://www.reddit.com/r/CardPuter/comments/1btnrxi/mystify_screensaver_for_microhydra/
# TODO: create a mode with multiple polygons, each with a hue that shifts over time (like the original "Mystify Your Mind" screensaver)

from hydra.color import color565, hsv_to_rgb
from lib.device import Device
from lib.display import Display
from lib.userinput import UserInput
from machine import reset
from random import choice, randint


NUM_ECHOES = 13  # number of polygons displayed
NUM_POINTS = 4   # aka number of sides on the polygons
MAX_SPEED = 5    # how many pixels (in an individual dimension) a point can move per timeslice


# display dimensions in pixels
WIDTH = Device.display_width    # 240 for cardputer
HEIGHT = Device.display_height  # 135 for cardputer

disp = Display()
input = UserInput()


def main_loop():

    # random speeds/directions and initial positions
    curr_polyg = []
    for _ in range(NUM_POINTS):
        curr_polyg.append([
            randint(0, WIDTH-1),                      # x,
            randint(0, HEIGHT-1),                     # y: positions
            randint(1, MAX_SPEED) * choice([-1, 1]),  # dx,
            randint(1, MAX_SPEED) * choice([-1, 1]),  # dy: velocities
            # NOTE: this does not allow velocities to be zero, cuz it looks weird
        ])

    # fill `trail` with the initial polygon
    trail = []
    for _ in range(NUM_ECHOES):
        trail.append(curr_polyg)

    while True:

        # update next point positions for polygon
        for pt in range(len(curr_polyg)):

            # update x
            curr_polyg[pt][0] += curr_polyg[pt][2] # x1 = x0 + dx
            if curr_polyg[pt][0] < 0 or curr_polyg[pt][0] >= WIDTH:
                # we hit a wall, reverse direction
                curr_polyg[pt][2] *= -1

            # update y
            curr_polyg[pt][1] += curr_polyg[pt][3] # y1 = y0 + dy
            if curr_polyg[pt][1] < 0 or curr_polyg[pt][1] >= HEIGHT:
                curr_polyg[pt][3] *= -1

        # remove oldest echo from polygon trail and append copy of newly updated polygon
        trail.pop(0)
        trail.append([pt.copy() for pt in curr_polyg]) # NOTE: list comprehension is used to get a deeper copy

        # clear screen before drawing
        disp.fill(0)

        # draw each polygon echo...
        for pg in range(len(trail)):
            polygon = trail[pg]

            # determine (rainbow) color for this polygon
            hue = 1.0 * pg / len(trail)
            # get RGB float values and convert them to 8-bit ints
            rgbs = [int(255 * c) for c in hsv_to_rgb(hue, 1.0, 1.0)]
            color = color565(*rgbs)

            # plot each line of the polygon...
            for pt in range(len(polygon)):
                # first line drawn will be from polygon[-1] to polygon[0] (that is, from the last point to the first point)
                disp.line(polygon[pt-1][0], polygon[pt-1][1],
                          polygon[pt][0],   polygon[pt][1],
                          color)

        # paint the screen
        disp.show()

        # look for user input
        keys = input.get_new_keys()
        if "G0" in keys or "ESC" in keys or "`" in keys: # backtick '`' is the ESC key w/o the 'fn' modifier
            # GTF0 to launcher
            reset()
        if "SPC" in keys or "ENT" in keys:
            # exit loop to be re-initialized
            return

        # TODO: put a short [device-dependent?  keypress-adjustible?] sleep() here if the animation ends up being too fast?


# run!
while True:
    # looping over this allows resetting to a new initial state
    main_loop()
