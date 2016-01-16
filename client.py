from mpd import MPDClient

client = MPDClient ()
client.connect('localhost', 6600)
status=client.status()
print 'status = ', status

client.pause()

client.disconnect()
