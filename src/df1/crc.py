# -*- coding: utf-8 -*-

import time, datetime, socket, string, struct


#==================================================================================================
def toHex(data):
	prntble = string.printable[:-5]
	hex = ['%02X'%ord(c) for c in data]
	asc = [c if(c in prntble) else '.' for c in data]
	ret = []
	for idx in xrange(0, len(hex), 16):
		ret.append("%s"%(' '.join((hex[idx : idx + 16])[:16])))
	return ''.join(ret)

def intHex(i):
	sValue = str(hex(i)).replace('0x','')
	if len(sValue) <= 1:
		sValue = "0%s"%sValue
	return sValue

#==================================================================================================
def crc16(data):
	crc = 0x0000
	for c in data:
		crc ^= ord(c);
		for x in range(8):
			if(crc & 1):
				crc = (crc >> 1) ^ 0xa001
			else:
				crc = crc >> 1

	return [crc & 0xff, crc / 256]
	#return struct.pack('H',crc)
	#return crc
