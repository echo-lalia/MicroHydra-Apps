import time
import random
import math
from lib.display import Display
from lib.userinput import UserInput
from lib.hydra import beeper

kb=UserInput()
tft=Display()
beep = beeper.Beeper()

bound=[0,235,130,0]
pos=[118.0,75.0]
vel=[0.0,0.0]
xint=118.0
yint=75.0
speed=100.0
sgrowth=1.5
plen=32
pbound=[0,134-plen]
scorezone=20.0
ppos=[scorezone,53.0]
pint=53.0
pspeed=4
delta=0.015
colint=65504
col = colint
vol=10
score=0

def rdr():
    global pos, ppos
    tft.fill(0)
    tft.rect(int(pos[0]),int(pos[1]),4,4,col,True)
    tft.rect(int(ppos[0]),int(ppos[1]),4,plen,col,True)
    tft.text(str(score),5,5,col)
    tft.show()

        
def clc():
    global pos, vel
    mult = speed * math.log(score+2,sgrowth)
    pos[0] += vel[0] * delta * mult
    pos[1] += vel[1] * delta 


def cld(b):
    global pos, vel, score
    mult=delta*speed*math.log(score+2,sgrowth)
    if (pos[1] <= b[0]):
        beep.play(('D4'),100,vol)
        vel[1] = -vel[1]
    if (pos[0] <= b[3]):
        vel[0] = -vel[0]
    if (pos[1] >= b[2]):
        beep.play(('D4'),100,vol)
        vel[1] = -vel[1]
    if (pos[0] >= b[1]):
        vel[0] = -vel[0]
        beep.play(('D2'),100,vol)
    if (pos[1]>ppos[1] and pos[1]<(ppos[1]+plen) and pos[0]<(ppos[0]+4) and vel[0]<0):
        vel[0] = -vel[0]
        pos[0]=ppos[0]
        score += 1
        colorshift()
        beep.play(('D3'),150,vol)
        vel[1] -= (ppos[1]-pos[1]+plen/2)*math.log(score+2)
    if (pos[0]<scorezone):
        rdr()
        beep.play(('D2','A2','D2'),80,vol)
        time.sleep(2)
        score = 0
        rst()  

def colorshift():
    global col, altcol
    if score <= 62:
        col -= 32

def rst():
    global pos, vel, score, col
    score=0
    pos = [xint, yint]
    v2 = (random.random()-0.5)*20
    vel = [-1,v2]
    col = colint

while (True):
    newkeys=kb.get_new_keys()
    keypres=kb.get_pressed_keys()
    if "ENT" in newkeys:
        rst()        
    if "v" in newkeys:
        if vol==0:
            vol = 10
        else:
            vol = 0
    if ";" in keypres:
        ppos[1] -= pspeed
    if "." in keypres:
        ppos[1] += pspeed
        
    clc()
    cld(bound)
    
    rdr()
    time.sleep_ms(int(1000*delta))
