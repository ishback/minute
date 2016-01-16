import os
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

pinOnOff = 17
pinNext = 6
pinStation = 22
pinLike = 0
pinLED = 16

# Pins for the ADC
SPICLK = 18
SPIMISO = 23
SPIMOSI = 24
SPICS = 25

# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

#set up the other pins
GPIO.setup(pinOnOff, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pinStation, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pinNext, GPIO.IN)
GPIO.setup(pinLED, GPIO.OUT)

# potentiometer connected to adc #0
volumeADC = 0;
stationADC = 1;

prev_buttonOnOff = 0
#prev_stationVal = 30 #so we always load the selected one at start
currentStation = 30
prev_buttonNext = 0

prev_potVolume = 0	 # this keeps track of the last potentiometer value
vol_tolerance = 5 # change volume when the pot has moved more than 5 'counts'

prev_potStation = 0
station_tolerance = 5

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
	if ((adcnum > 7) or (adcnum < 0)):
		return -1
	GPIO.output(cspin, True)

	GPIO.output(clockpin, False)  # start clock low
	GPIO.output(cspin, False)     # bring CS low
 
	commandout = adcnum
	commandout |= 0x18  # start bit + single-ended bit
	commandout <<= 3    # we only need to send 5 bits here
	for i in range(5):
		if (commandout & 0x80):
			GPIO.output(mosipin, True)
		else:
			GPIO.output(mosipin, False)
		commandout <<= 1
		GPIO.output(clockpin, True)
		GPIO.output(clockpin, False)
 
	adcout = 0
	# read in one empty bit, one null bit and 10 ADC bits
	for i in range(12):
		GPIO.output(clockpin, True)
		GPIO.output(clockpin, False)
		adcout <<= 1
		if (GPIO.input(misopin)):
			adcout |= 0x1
 
	GPIO.output(cspin, True)
        
	adcout >>= 1       # first bit is 'null' so drop it
	return adcout

def checkOnOff():
	buttonOnOff = GPIO.input(pinOnOff)        
	global prev_buttonOnOff
	if buttonOnOff != prev_buttonOnOff:
		if buttonOnOff:
			print("Radio ON")
			GPIO.output(pinLED,GPIO.HIGH)
			os.system('mpc -h localhost play')
		elif not buttonOnOff:
			print("Radio OFF")
			GPIO.output(pinLED, GPIO.LOW)
			#os.system('mpc stop')
			os.system('mpc -h localhost stop') # changed from pause

		#update previous input
		prev_buttonOnOff = buttonOnOff
		#slight pause to debounce
	time.sleep(0.2)

def checkVolume():
	global prev_potVolume
	global vol_tolerance
	potVolume_changed = False
	potVolume = readadc(volumeADC, SPICLK, SPIMOSI, SPIMISO, SPICS)
	potVolume_adjust = abs(potVolume - prev_potVolume)
	#print potVolume
	if (potVolume_adjust > vol_tolerance):
		potVolume_changed = True

	#print "trim_pot_changed", potVolume_changed
	if (potVolume_changed):
		set_volume = potVolume / 10.24  # convert 10bit adc0 (0-1024) trim pot read into 0-100 volume level
		print set_volume 
		set_volume = round(set_volume) # round out decimal value
		set_volume = int(set_volume)   # cast volume as integer

		#print 'Volume = {volume}%' .format(volume = set_volume)
		print 'Volume = ', set_volume
		set_vol_cmd = 'mpc -h localhost volume {volume}' .format(volume = set_volume)
		os.system(set_vol_cmd)  # set volume
		prev_potVolume = potVolume
	time.sleep(0.2)

def loadStation(s):
	print "clear and wait"
	os.system('mpc -h localhost clear')
	#os.system('mpc --wait')
	time.sleep(0.5)
	station = stationList[s]
	print "loading playlist: " + station
	stString = 'mpc -h localhost load \"'+station+'\"'
	os.system(stString)
	print "waiting..."
	#os.system('mpc --wait')  # this doesn't do anything
	time.sleep(4)
	print "finished waiting"
	if prev_buttonOnOff == 1:
		#os.system('mpc -h localhost play')
		pass
	elif prev_buttonOnOff == 0:
		os.system('mpc -h localhost stop')
	time.sleep(0.2)

def checkStation():
	global currentStation
	global prev_potStation
	global station_tolerance
	potStation_changed = False
	potStation = readadc(stationADC, SPICLK, SPIMOSI, SPIMISO, SPICS)
	potStation_adjust = abs(potStation - prev_potStation)
	#print potStation
	if (potStation_adjust > station_tolerance):
		potStation_changed = True

	if (potStation_changed):
		set_station = potStation / 44.52174  # convert 10bit adc0 (0-1024) trim pot read into 0-100 volume level
		print set_station
		set_station = round(set_station) # round out decimal value
		set_station = int(set_station)   # cast volume as integer

		print 'Station = ', set_station
		if not stationList[set_station] or set_station == currentStation:
			print "station not setup"
		else:
			print "station exists"
			loadStation(set_station)
			currentStation = set_station		

		prev_potStation = potStation
	time.sleep(0.2)


def checkStation2():
	stationVal = GPIO.input(pinStation)
	global prev_stationVal
	if stationVal != prev_stationVal: 
		print "Station changed"
		if stationVal == 0:
			loadStation(0)
			prev_stationVal = 0
		elif stationVal == 1:
			loadStation(1)
			prev_stationVal = 1
	time.sleep(0.2)

def checkNext():
	buttonNext = GPIO.input(pinNext)
	global prev_buttonNext
	if buttonNext != prev_buttonNext:
		print "Next song"
		#we want next to work only in spotify playlists
		print stationList[currentStation][:7]
		if stationList[currentStation][:7] == "spotify":
			print "current station is Spotify"
			os.system('mpc -h localhost next')
	time.sleep(0.2)

#read preset stations
with open('/home/pi/minute/stations.txt') as f:
    stationList = f.read().splitlines()
    print stationList

try:
	while True:
		checkVolume()
		checkStation()
		checkOnOff()
		checkNext()
except KeyboardInterrupt:
	GPIO.cleanup()
