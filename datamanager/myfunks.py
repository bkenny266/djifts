##MYFUNKS - utility functions  

def deleteAfter(line, delimeter):
	pos = 0
	for char in line:
		if char == delimeter:
			break
		pos += 1

	return line[:pos].strip()

def convertToSecs(str, period = 1):
#Converts 00:00 format into seconds
#Period is optional, defaults to no modification (period 1)
	timeMins, timeSecs = splitTime(str)
	return timeMins*60 + timeSecs + ((period * 20 - 20) * 60)


def convertFromSecs(secIn):
#Convert seconds into a more readable 00:00 format
	mins = secIn / 60
	secs = secIn % 60
	if mins < 10:
		mins = "0" + str(mins)
	if secs < 10:
		secs = "0" + str(secs)
	return str(mins) + ":" + str(secs)

def splitTime(str):
	## Splits a time divided by a : (format is 00:00) into two integers
	pos = 0
	for char in str:
		if char == ':':
			break
		pos+=1
	return int(str[:pos]), int(str[pos+1:])
