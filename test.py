with open('/home/pi/minute/stations.txt') as f:
	stations = f.read().splitlines() 
	print stations
