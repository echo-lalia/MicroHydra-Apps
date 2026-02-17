"""Print a key from the major/minor scale everytime the user presses enter."""
import random
from machine import Pin, freq
from lib.display import Display
from lib.userinput import UserInput
from lib.hydra.config import Config
from lib.device import Device
from lib.hydra.popup import UIOverlay
from font import vga1_8x16 as fontSmall
from font import vga2_16x32 as fontBig
import time

try:
    from .Audio import Audio as Audio
except ImportError:
    from apps.RandomScale.Audio import Audio as Audio



# ~~~~~~~~~~~~~~~~~~~~~~~~~ global objects/vars ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
freq(240000000)

if "CARDPUTER" in Device:
    import neopixel
    led = neopixel.NeoPixel(Pin(21), 1, bpp=3)

tft = Display(use_tiny_buf=("spi_ram" not in Device))

config = Config()

kb = UserInput()


OVERLAY = UIOverlay()

DISPLAY_WIDTH = Device.display_width
DISPLAY_HEIGHT = Device.display_height
DISPLAY_WIDTH_HALF = DISPLAY_WIDTH // 2
DISPLAY_HEIGHT_HALF = DISPLAY_HEIGHT // 2

MAX_H_CHARS = DISPLAY_WIDTH // 8
MAX_V_LINES = DISPLAY_HEIGHT // 16


PLAY_MAJOR_OR_MINOR_FLAG = "Major"   # set to 'Major' if major, 'Minor' if minor
scales = ["A", "a", "Ab", "B", "b", "Bb", "bb", "C", "c", "c#", "D", "d", "Db", "E", "e", "Eb", "eb", "F", "f", "f#", "G", "g", "Gb", "g#"]     # capital letters major, lowercase minor
notesInScale = {
    "A":  220,
    "a":  220,
    "Ab": 207.65,
    "B":  246.94,
    "b":  246.94,
    "Bb": 233.08,
    "bb": 233.08,
    "C":  130.81,
    "c":  130.81,
    "c#": 138.59,
    "D":  146.83,
    "d":  146.83,
    "Db": 138.59,
    "E":  164.81,
    "e":  164.81,
    "Eb": 155.56,
    "eb": 155.56,
    "F":  174.61,
    "f":  174.61,
    "f#": 185,
    "G":  196,
    "g":  196,
    "Gb": 185,
    "g#": 207.65
}






# ~~~~~~~~~~~~~~~~~~~~~~~~~ functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


""" Print the next scale to the CardPuter screen """
def printNextScaleToScreen(text, clr_idx=8):
    global PLAY_MAJOR_OR_MINOR_FLAG
    text = str(text) + " " + PLAY_MAJOR_OR_MINOR_FLAG 
    print(text)
    tft.fill(config.palette[2])
    x = DISPLAY_WIDTH_HALF - (len(text) * 8)
    tft.text("Your next scale is:", 5, 10, config.palette[clr_idx], font=fontSmall)
    tft.text(text, x, DISPLAY_HEIGHT_HALF, config.palette[clr_idx], font=fontBig)
    tft.show()


""" raise a note by a half-step """
def raiseByHalfStep(startingNote):
    return startingNote * 1.05946309436


""" raise a note by a whole-step """
def raiseByWholeStep(startingNote):
    return startingNote * 1.12246204831


""" raise a starting note multiple times in the major scale formula, returning a list of frequencies """
def noteToMajorScale(startingNote):
    scaleNotes = [startingNote]
    scaleNotes.append(raiseByWholeStep(startingNote))
    scaleNotes.append(raiseByWholeStep(scaleNotes[-1]))
    scaleNotes.append(raiseByHalfStep(scaleNotes[-1]))
    scaleNotes.append(raiseByWholeStep(scaleNotes[-1]))
    scaleNotes.append(raiseByWholeStep(scaleNotes[-1]))
    scaleNotes.append(raiseByWholeStep(scaleNotes[-1]))
    scaleNotes.append(raiseByHalfStep(scaleNotes[-1]))

    return scaleNotes


""" raise a starting note multiple times in the minor scale formula, returning a list of frequencies """
def noteToMinorScale(startingNote):
    scaleNotes = [startingNote]
    scaleNotes.append(raiseByWholeStep(startingNote))
    scaleNotes.append(raiseByHalfStep(scaleNotes[-1]))
    scaleNotes.append(raiseByWholeStep(scaleNotes[-1]))
    scaleNotes.append(raiseByWholeStep(scaleNotes[-1]))
    scaleNotes.append(raiseByHalfStep(scaleNotes[-1]))
    scaleNotes.append(raiseByWholeStep(scaleNotes[-1]))
    scaleNotes.append(raiseByWholeStep(scaleNotes[-1]))

    return scaleNotes


# ~~~~~~~~~~~~~~~~~~~~~~~~~ class definition ~~~~~~~~~~~~~~~~~~~~~~~~~~~~


""" Randomly yield a scale from a list of scales and play the scale using audio """
class RandomScale:
    def __init__(self, scales):
        self.scalesList = scales
        self.possibleScales = self.scalesList
        self.prevScales = []

    """ generator for the random scales """
    def getScale(self):

        # trim from the list of previously used scales if there are too much
        if(len(self.prevScales) > 15):
           self.prevScales.pop(0)

        # subtract the previous scales to form a list of possible scales to use
        self.possibleScales = self.listDifference(self.scalesList, self.prevScales)

        # chose a random scale from the list of possible ones
        chosenScale = random.choice(self.possibleScales)
        self.prevScales.append(chosenScale)

        # determine if we are currently playing a major or minor scale
        global PLAY_MAJOR_OR_MINOR_FLAG
        if (chosenScale.islower()):
            PLAY_MAJOR_OR_MINOR_FLAG = "Minor"
        else:
            PLAY_MAJOR_OR_MINOR_FLAG = "Major"

        yield chosenScale


    """ subtract the elements of listB from listA """
    def listDifference(self, listA, listB):
        
        # simply iterate over all the elements of listA and if they are in listB, don't add them to the returnList
        returnList = []
        for element in listA:
            if (element not in listB):
                returnList.append(element)

        return returnList
        

    """ use audio library to play the chosen scale """
    def playScale(self, scale):

        # get the frequency of the notes in the scale
        global PLAY_MAJOR_OR_MINOR_FLAG
        if (PLAY_MAJOR_OR_MINOR_FLAG == "Major"):
            notesToPlay = noteToMajorScale(notesInScale[scale])
        else:
            notesToPlay = noteToMinorScale(notesInScale[scale])

        # play all of the notes
        for note in notesToPlay:
            Audio.playSin(note, 0.75, 175)
            time.sleep_ms(40)

        
# ~~~~~~~~~~~~~~~~~~~~~~~~~ main loop ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# keep printing scales
randomScaleChooser = RandomScale(scales)
printNextScale = True
while True:
    if (printNextScale):
        nextScale = next(randomScaleChooser.getScale())
        printNextScaleToScreen(nextScale)
        randomScaleChooser.playScale(nextScale)
        printNextScale = False
        
    # handle key strokes
    keys = kb.get_new_keys()
    kb.ext_dir_keys(keys)
    
    if "ENT" in keys: # ok button pressed, next scale
        printNextScale = True
        continue
