import os
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

pinOnOff = 17
pinNext = 6
pinStation = 22
pinLike = 0
pinLED = 18

GPIO.setup(pinOnOff, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(pinStation, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#GPIO.setup(pinOnOff, GPIO.IN)
GPIO.setup(pinNext, GPIO.IN)
#GPIO.add_event_detect(pinLike, GPIO.RISING, callback=my_callback, bouncetime=200)
#GPIO.setup(pinLike, GPIO.IN)
GPIO.setup(pinLED, GPIO.OUT)

prev_buttonOnOff = 0
prev_stationVal = 5 #so we always load the selected one at start
prev_buttonNext = 0

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
			os.system('mpc -h localhost pause')

		#update previous input
		prev_buttonOnOff = buttonOnOff
		#slight pause to debounce
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
	#os.system('mpc --wait')
	time.sleep(5)
	print "finished waiting"
	#os.system('mpc -h localhost stop')

def checkStation():
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
		if stationList[prev_stationVal][7:] == "spotify":
			print "current station is Spotify"
			os.system('mpc -h localhost next')
	time.sleep(0.2)

print("here")

#stop mpc
os.system('sudo service mpd stop')

#start forked-daapd
os.system('sudo /etc/init.d/forked-daapd restart')
time.sleep(30) #wait until the forked-daapd build the playlist list

os.system('mpc -h localhost lsplaylists')

#read preset stations
with open('/home/pi/minute/stations.txt') as f:
    stationList = f.read().splitlines()
    print stationList

try:
	while True:
		checkStation()
		checkOnOff()
		checkNext()
except KeyboardInterrupt:
	GPIO.cleanup()
