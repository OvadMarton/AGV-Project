import time
import socket
import json
import threading
import re

class position:
	def __init__(self, x, y, heading):
		self.x=x
		self.y=y
		self.w=180
		self.heading=heading
	def update(self):
		self.w=round(self.heading/90, 0)*90
	


def tcp_read(port):
	#TCP_IP = '192.168.0.129'
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('localhost', TCP_PORT)) #todo: IP lehetőleg dinamikusan
	serversocket.listen(5)
	while True:					   
		(clientsocket, address) = serversocket.accept()	
		ct=threading.Thread(name='ct', target=client_thread, args=(clientsocket,))	
		ct.start()	

def tcp_reporter(port):
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('localhost', 5011)) #todo: IP lehetőleg dinamikusan
	serversocket.listen(5)
	while True:					   
		(clientsocket, address) = serversocket.accept()	
		ct=threading.Thread(name='ct', target=direct_report, args=(clientsocket,))	
		ct.start()	

def direct_report(socket):
	data=b''
	while True:
		time.sleep(0.1)
		part = socket.recv(BUFFER_SIZE)
		data+=part
		if len(part)<BUFFER_SIZE:
			#print('not rec')
			break
	command=json.loads(data.decode('utf-8'))
	if command["command"]["cmd"]==10: #TODO: ezt switcherrel és külön függvényekkel hogy bővíthető legyen
		global pos
		pos.update()
		posdict={
			"x": pos.x,
			"y": pos.y,
			"heading": pos.heading
		}
		string=json.dumps(posdict)
		socket.send(str.encode(string))
		socket.close()

def client_thread(socket):
	data=b''
	while True:
		time.sleep(0.1)
		part = socket.recv(BUFFER_SIZE)
		data+=part
		if len(part)<BUFFER_SIZE:
			#print('not rec')
			break
	command=data.decode('utf-8')
	commands=re.split('[\t]', command)
	msg=[]
	print("commands pre del: ", commands)
	commands.remove(commands[-1])
	print("commands post del: ", commands)
	for i in range(0, len(commands)):
		msg.append(json.loads(commands[i]))
		reply=msg[i]
		reply["status"]=3
		socket.send(str.encode(json.dumps(reply)+'\t'))
	global parancsok
	global emergency_stop_flag
	for cmd in msg:
		if cmd["command"]["cmd"]==80:
			parancsok=[]
			emergency_stop_flag=True
		else:
			parancsok.append(cmd)
	# ~ parancsok = parancsok + msg
	socket.send(str.encode("\n"))
	socket.close()

def msgbacktest(command):
	time.sleep(command["command"]["param1"])
	msg=command
	msg["status"]=1
	return msg

def report(msg):
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('localhost', TCP_REPORT))
	msgback=json.dumps(msg)
	s.send(str.encode(msgback))
	s.send('\n'.encode('utf-8'))
	s.close()

def direct_msg(string):
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('localhost', TCP_DIRECT))
	s.send(str.encode(string))
	s.send('\n'.encode('utf-8'))
	s.close()


def move_f(msg):
	global pos
	pos.update()
	time.sleep(5)
	if pos.w==0:
		pos.y-=5
	if pos.w==90:
		pos.x+=5
	if pos.w==180:
		pos.y+=5
	if pos.w==270:
		pos.x-=5
	msg["status"]=1
	return msg

def move_b(msg):
	global pos
	pos.update()
	time.sleep(5)
	if pos.w==0:
		pos.y+=5
	if pos.w==90:
		pos.x-=5
	if pos.w==180:
		pos.y-=5
	if pos.w==270:
		pos.x+=5
	msg["status"]=1
	return msg

def turn_r(msg):
	global pos
	time.sleep(2)
	if pos.w==270:
		pos.heading=0
	else:
		pos.heading+=90
	msg["status"]=1
	pos.update()
	return msg

def turn_l(msg):
	global pos
	time.sleep(2)
	if pos.w==0:
		pos.heading=270
	else:
		pos.heading-=90
	msg["status"]=1
	pos.update()
	return msg

def pos_report(msg):
	global pos
	pos.update()
	posdict={
		"x": pos.x,
		"y": pos.y,
		"heading": pos.heading
	}
	string=json.dumps(posdict)
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('localhost', 41007))
	s.send(str.encode(string))
	s.close()
	msg["status"]=1
	return msg

def execute():
	global parancsok
	while True:
		if len(parancsok) == 0:
			time.sleep(0.1)
		else:
			nextcmd=parancsok[0]
			switcher={
				99:	msgbacktest,
				1: move_f,
				2: move_b,
				3: turn_l,
				4: turn_r,
				10: pos_report
				}
			func=switcher.get(nextcmd["command"]["cmd"], hiba)
			msg=func(nextcmd)
			report(msg)
			global emergency_stop_flag
			try:
				del parancsok[0]
			except IndexError:
				if emergency_stop_flag:
					emergency_stop_flag=False
				else:
					raise IndexError

def hiba(command):
	msg=command
	msg["status"]=2
	return msg

parancsok = list()
pos=position(5, 10, 180)
BUFFER_SIZE = 1024
TCP_PORT = 41001
TCP_REPORT=41004
TCP_DIRECT=5010
emergency_stop_flag=False
parser=threading.Thread(name='Parser', target=tcp_read, args=(5005,))
parser.start()
executer=threading.Thread(name='Execute', target=execute)
executer.start()
reporter=threading.Thread(name='reporter', target=tcp_reporter, args=(5011,))
reporter.start()


