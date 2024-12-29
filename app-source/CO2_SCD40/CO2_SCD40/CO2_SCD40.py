# needs an SCD40 CO2 device attached via I2C
# e.g. https://docs.m5stack.com/en/unit/co2

try:
    import scd4x
except ImportError:
    from apps.CO2_SCD40 import scd4x

import time
from machine import Pin, I2C, reset
from lib.display import Display
from lib.hydra.config import Config
from lib.userinput import UserInput
from font import vga2_16x32 as font


display=Display(use_tiny_buf=True)
config = Config()
kb = UserInput()
display.fill(config.palette[2])
WAIT_TIME_SECS = 5


def process_keys():

    keys = kb.get_new_keys()

    if keys:
        # "G0" button exits to the launcher.
        if "G0" in keys:
            reset()

def main():

    while True:
		
		process_keys()
		
		if scd.data_ready:
			temperature = scd.temperature
			relative_humidity = scd.relative_humidity
			co2_ppm_level = scd.CO2
		
		
		co2_text =  'CO2 ppm:{:,}'.format(co2_ppm_level)
		temp_text = 'Temp: {:.2f} C'.format(temperature)
		hum_text =  'Rel Hum:{:.1f} %'.format(relative_humidity)
		
		display.fill(config.palette[2])
		display.text(
				co2_text,
				0, #X
				0, # Y
				config.palette[10],
				font=font
                )
		display.text(
				temp_text,
				0, #X
				font.HEIGHT * 1, # Y
				config.palette[10],
				font=font
                )
		display.text(
				hum_text,
				0, #X
				font.HEIGHT * 2, # Y
				config.palette[10],
				font=font
                )
		display.show()
		time.sleep(WAIT_TIME_SECS)


# Set up
i2c = I2C(0, sda=Pin(2), scl=Pin(1),timeout=8000)   # cardputer pin settings

# check for SCD40 sensor via i2c scan for device with address 0x62 (int 98)
results = i2c.scan()
if len(results) == 0 or 98 not in results:

	display.text(
				'No SCD40 found',
				0, #X
				0, # Y
				config.palette[10],
				font=font
                )
	display.show()
	time.sleep(WAIT_TIME_SECS)
	reset()
	
else:
	
	scd = scd4x.SCD4X(i2c)
	scd.start_periodic_measurement()  # start_low_periodic_measurement() is a lower power alternative

	display.text(
					'Preparing...',
					0, #X
					0, # Y
					config.palette[10],
					font=font
					)
	display.text(
					'Hold GO to exit',
					0, #X
					font.HEIGHT * 1, # Y
					config.palette[10],
					font=font
					)
	display.show()

	# wait for sensor to warm up
	time.sleep(WAIT_TIME_SECS)
	
	main()





