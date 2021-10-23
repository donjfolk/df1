#!/usr/bin/env python
# -*- coding: utf_8 -*-



import socket, select,struct, random
import crc


FileType = {
	'S':0x84,
	'B':0x85,
	'T':0x86,
	'C':0x87,
	'R':0x88,
	'N':0x89,
	'F':0x8A,
	'O':0x8B,
	'I':0x8C,
	'ST':0x8D,
	'A':0x8E,
	'D':0x8F,
	}


class TcpMaster(object):
	
	def __init__(self, server="127.0.0.1", port=4000, src=0, dst=1, timeout_in_sec=2):
		self.timeout_in_sec = timeout_in_sec
		self._server = server
		self._port = port
		self._sock = None
		self.src = src
		self.dst = dst
		self.dle = 0x10
		self.stx = 0x02
		self.ext = 0x03
		self.cmd = 0x0F
		self.fnc = 0XA2
		self.sts = 0x00
		self.tns = random.randint(0, 4096)#0x0F00
		self.file_type = 0x83
		self.file_num = 0x00
		self.element = 0x00
		self.sub_element = 0x00
		
	def _do_open(self):
		"""Connect to the DF1 slave"""
		if self._sock:
			self._sock.close()
		self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.set_timeout(self.timeout_in_sec)
		self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self._sock.connect((self._server, self._port))

	def _do_close(self):
		"""Close the connection with the DF1 Slave"""
		if self._sock:
			self._sock.close()
			self._sock = None
		return True
	
	def _send(self, request):
		"""Send request to the sDF1 lave"""
		try:
			flush_socket(self._sock, 3)
		except Exception as msg:
			#if we can't flush the socket successfully: a disconnection may happened
			#try to reconnect
			self._do_open()
		#print("TX:%s"%(' '.join('{:02x}'.format(ord(x)) for x in request)))
		self._sock.send(request)
	
	def _send_ack(self):
		request = struct.pack('BB',0x10, 0x06)
		#print("TX:%s"%(' '.join('{:02x}'.format(ord(x)) for x in request)))
		self._sock.send(request)

	def _send_enq(self):
		request = struct.pack('BB',0x10, 0x05)
		#print("TX:%s"%(' '.join('{:02x}'.format(ord(x)) for x in request)))
		self._sock.send(request)
	
	def _recv(self, expected_length=-1):
		"""
		Receive the response from the DF1 slave
		"""
		response = []
		length = 255
		ACK = False
		ENQ = False
		while len(response) < length:
			if response == [16,6]:
				ACK = True
				response = []
			if response == [16,5]:
				ENQ = True
				response = []
			rcv_byte = self._sock.recv(1)
			if rcv_byte:
				response.append(struct.unpack('B',rcv_byte)[0])
				#Check for End
				try:
					if response[-2:] == [0x10, 0x03]:
						length = len(response) + 2
				except:
					pass
			else:
				break
		if ACK == True:
			self._send_ack()
		if ENQ == True:
			self._send_enq()
		return response
	
	def extract_tns(self):
		return [self.tns & 0xff, self.tns / 256]
	
	
	def poll(self, sRegister, iNum):
		self.file_type = FileType[sRegister[0]]
		#Integer
		if (self.file_type == 0x89):
			self.num_bytes = iNum
			self.file_num = int(sRegister[1:].split(':')[0])
			self.element = int(sRegister[1:].split(':')[1].split('/')[0])
		#Float
		elif (self.file_type == 0x8A):
			self.num_bytes = iNum * 4
			self.file_num = int(sRegister[1:].split(':')[0])
			self.element = int(sRegister[1:].split(':')[1].split('/')[0])
		#Input
		elif (self.file_type == 0x8C):
			self.num_bytes = iNum*2
			self.file_num = int(sRegister[1:].split(':')[1].split('/')[0])
			self.element = int(sRegister[1:].split(':')[1].split('/')[0])
		#Bit
		elif (self.file_type == 0x85):
			self.num_bytes = iNum*2
			self.file_num = int(sRegister[1:].split(':')[0])
			self.element = int(sRegister[1:].split(':')[1].split('/')[0])
		else:
			raise RuntimeError('File Type:%s(%s) Not Supported Yet'%(sRegister[0], self.file_type))
			
		self.tns += 1
		aTns = self.extract_tns()
		
		data = [self.dst, self.src, self.cmd, self.sts, aTns[0], aTns[1], self.fnc, self.num_bytes, self.file_num, self.file_type, self.element, self.sub_element]
		oBuffer = ""
		for i in data:
			oBuffer += struct.pack('B',i)
		oBuffer += struct.pack('B',0x03)# Because AB Said So ??
		CRC = crc.crc16(oBuffer)
		oBuffer = struct.pack('BB',self.dle, self.stx)
		for i in data:
			oBuffer += struct.pack('B',i)
		oBuffer += struct.pack('BB',self.dle, self.ext)
		for i in CRC:
			oBuffer += struct.pack('B',i)
		oServer._send(oBuffer)
		data = oServer._recv()
		
		#DF1 if theres 0x10 then there should be two...
		for i in range(len(data)-1):
			try:
				if (data[i] == 0x10) and (data[i+1] == 0x10):
					data.pop(i)
			except:
				pass
		if (data[0:5] == [self.dle, self.stx, self.src, self.dst, 0x4F]) and (data[6:8] == [aTns[0],aTns[1]]) and (data[-4:-2] == [self.dle, self.ext]):
			
			#Integer
			if (self.file_type == 0x89) and (self.num_bytes == len(data[8:-4])):
				return tuple(data[8:-4])
			elif (self.file_type == 0x89) and (self.num_bytes != len(data[8:-4])):
				raise RuntimeError('Integer File Returned Wrong Number of Bytes:%s!=%s'%(self.num_bytes, len(data[8:-4])))
			
			#Float
			elif (self.file_type == 0x8A) and (self.num_bytes == len(data[8:-4])):
				sFormat = '<'
				for i in range(self.num_bytes / 4):
					sFormat += 'f'
				aa= bytearray(data[8:-4]) 
				return struct.unpack(sFormat, aa)
			elif (self.file_type == 0x8A) and (self.num_bytes != len(data[8:-4])):
				raise RuntimeError('Float File Returned Wrong Number of Bytes:%s!=%s'%(self.num_bytes, len(data[8:-4])))
			
			#Input
			if (self.file_type == 0x8C) and (self.num_bytes == len(data[8:-4])):
				sFormat = ''
				for i in range(self.num_bytes / 2):
					sFormat += 'h'
				aa= bytearray(data[8:-4]) 
				try:
					iBit = int(sRegister[1:].split(':')[1].split('/')[1])
					iValue = struct.unpack(sFormat, aa)[0]
					aValue = list(format(iValue, "b").zfill(16))
					aValue.reverse()
					return tuple(aValue[iBit:iBit+(self.num_bytes / 2)])
				except Exception,ex:
					print ex
					return struct.unpack(sFormat, aa)
			elif (self.file_type == 0x8C) and (self.num_bytes != len(data[8:-4])):
				raise RuntimeError('Input File Returned Wrong Number of Bytes:%s!=%s'%(self.num_bytes, len(data[8:-4])))
			
			#Bit
			if (self.file_type == 0x85) and (self.num_bytes == len(data[8:-4])):
				sFormat = ''
				for i in range(self.num_bytes / 2):
					sFormat += 'h'
				aa= bytearray(data[8:-4]) 
				try:
					iBit = int(sRegister[1:].split(':')[1].split('/')[1])
					iValue = struct.unpack(sFormat, aa)[0]
					aValue = list(format(iValue, "b").zfill(16))
					aValue.reverse()
					return tuple(aValue[iBit:iBit+(self.num_bytes / 2)])
				except Exception,ex:
					return struct.unpack(sFormat, aa)
			
			elif (self.file_type == 0x85) and (self.num_bytes != len(data[8:-4])):
				raise RuntimeError('Bit File Returned Wrong Number of Bytes:%s!=%s'%(self.num_bytes, len(data[8:-4])))
			
			else:
				return data
		elif (data[6:8] != [aTns[0],aTns[1]]):
			raise RuntimeError('Invalid TNS: %s != %s'%(data[6:8] , [aTns[0],aTns[1]]))
		else:
			raise RuntimeError('Unkown Error: Data Returned:%s'%data)

	
	
	def set_timeout(self, timeout_in_sec):
		if self._sock:
			self._sock.setblocking(timeout_in_sec > 0)
			if timeout_in_sec:
				self._sock.settimeout(timeout_in_sec)
