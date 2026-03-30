""" Simple library for generating some tones on the CardPuter. """
from machine import I2S
from machine import Pin
import time
import math
import random


# ~~~~~~~~~~~~~~~~~~~~~~~~~ global objects/vars ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
SCK_PIN = 41
WS_PIN = 43
SD_PIN = 42
I2S_PIN = 1
SAMPLE_RATE = 64000

audio_out = I2S(I2S_PIN,sck=Pin(SCK_PIN),ws=Pin(WS_PIN),sd=Pin(SD_PIN),mode=I2S.TX,bits=16,format=I2S.STEREO,rate=64000,ibuf=8192)



# ~~~~~~~~~~~~~~~~~~~~~~~~~ functions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

""" generate a single square wave of freq and volume """
def generateSquareWave(freq, volume):
	#the sample rate is equiv to the increment
	sampleIncrement = (math.pi / SAMPLE_RATE) * freq / 2
	currentIncrement = 0
	
	sampleList = bytearray()
	while currentIncrement < math.pi:
		#if the sine is negative, 0 of square. else, 1
		if (math.sin(currentIncrement) >  0.0):
			sample = math.floor(127.5 * volume)
		else:
			sample = 0
		sampleList += bytearray((sample, sample))
		currentIncrement += sampleIncrement
	
	return sampleList
	

""" generate a single triangle wave of freq and volume TODO """
def generateTriangleWave(freq, volume):
	#the sample rate is equiv to the increment
	sampleIncrement = (math.pi / SAMPLE_RATE) * freq / 2
	currentIncrement = 0
	
	sampleList = bytearray()
	period = 1/freq
	while currentIncrement < period:
		sample = math.floor( (math.pi * freq) * math.asin(abs(math.sin(math.pi * currentIncrement))) * 127.5 / volume)
		sampleList = bytearray((sample, sample))
		currentIncrement += sampleIncrement
			
	return sampleList
	
	
""" generate a single sine wave of freq and volume """
def generateSineWave(freq, volume):
	#the sample rate is equiv to the increment
	sampleIncrement = (math.pi / SAMPLE_RATE) * freq / 2
	currentIncrement = 0
		
	sampleList = bytearray()
	while currentIncrement < math.pi:
		sample = math.floor(((math.sin(currentIncrement)) * 127.5 * volume))
		sampleList += bytearray((sample,sample))
		currentIncrement += sampleIncrement
	return sampleList

""" generate a single sawtooth wave """
def generateSawtooth(freq, volume):
	pass

""" generate noise """
def generateNoise(freq, volume):
	sampleIncrement = (math.pi / SAMPLE_RATE) * freq / 2
	currentIncrement = 0
	
	sampleList = bytearray()
	while currentIncrement < math.pi:
		sample = math.floor(random.randrange(0, 127) * volume)
		sampleList += bytearray((sample,sample))
		currentIncrement += sampleIncrement
	
	return sampleList

	

# ~~~~~~~~~~~~~~~~~~~~~~~~~ class definition ~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class Audio:
	""" generate a sinewave tone """
	def playSin(freq, volume=0.1, duration=10):
		samples = generateSineWave(freq, volume)

		# play until the duration has elapsed
		startTick = time.ticks_ms()
		while time.ticks_diff(time.ticks_ms(), startTick) < duration:
			audio_out.write(samples)

	""" generate a squarewave tone. """
	def playSquare(freq, volume=0.1, duration=10):
		samples = generateSquareWave(freq, volume)
		
		# play until the duration has elapsed
		startTick = time.ticks_ms()
		while time.ticks_diff(time.ticks_ms(), startTick) < duration:
			audio_out.write(samples)
	
	""" generate a trianglewave tone. TODO"""
	def playTriangle(freq, volume=0.1, duration=10):
		samples = generateTriangleWave(freq, volume)
		
		# play until the duration has elapsed
		startTick = time.ticks_ms()
		while time.ticks_diff(time.ticks_ms(), startTick) < duration:
			audio_out.write(samples)

	""" generate a noise signal """
	def playNoise(freq, volume=0.1, duration=10):
		samples = generateNoise(freq, volume)
		
		# play until the duration has elapsed
		startTick = time.ticks_ms()
		while time.ticks_diff(time.ticks_ms(), startTick) < duration:
			audio_out.write(samples)

	""" play a flat noise. Used to keep the speakers from popping inbetween playing noises. """
	def playDeadAir(volume=0.1, duration=10):
		sample = math.floor(127.5 * volume)
		samples = bytearray((sample, sample))

		# play until the duration has elapsed
		startTick = time.ticks_ms()
		while time.ticks_diff(time.ticks_ms(), startTick) < duration:
			audio_out.write(samples)
