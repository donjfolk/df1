#!/usr/bin/env python
# -*- coding: utf_8 -*-

oServer = TcpMaster(server="10.250.1.100", port=44818, src=0x0, dst=0x1, timeout_in_sec=5.0)
aTag = [('I:1/0', 16),('B19:120/03', 1),('N7:0', 3),('F15:0', 2),('I:1/0', 16),('B19:120/03', 1),('N7:0', 3),('F15:0', 2),('I:1/0', 16),('B19:120/03', 1),('N7:0', 3),('F15:0', 2),('I:1/0', 16),('B19:120/03', 1),('N7:0', 3),('F15:0', 2),('I:1/0', 16),('B19:120/03', 1),('N7:0', 3),('F15:0', 2)]
for tTag in aTag:
	try:
		print oServer.poll(tTag[0], tTag[1])
	except Exception, ex:
		print('Error:%s'%ex)


