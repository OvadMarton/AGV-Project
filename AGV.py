# -*- coding: utf-8 -*-
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
	


def tcp_read(port, run_event):
	#TCP_IP = '192.168.0.129'
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	serversocket.bind((own_ip, TCP_PORT)) 
	serversocket.listen(5)
	while run_event.is_set():					   
		(clientsocket, address) = serversocket.accept()	
		ct=threading.Thread(name='ct', target=client_thread, args=(clientsocket,))	
		ct.start()	
	serversocket.close()

def tcp_reporter(port, run_event):
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	serversocket.bind((own_ip, port)) 
	serversocket.listen(5)
	while run_event.is_set():				   
		(clientsocket, address) = serversocket.accept()	
		ct=threading.Thread(name='ct', target=direct_report, args=(clientsocket,))	
		ct.start()	
		time.sleep(0.01)
		
	
def direct_report(socket): #bővíthető tetszőlegesen a még a parancs queue-t kikerülő parancsokkal
	data=b''
	while True:
		# ~ time.sleep(0.01)
		part = socket.recv(BUFFER_SIZE)
		data+=part
		if len(part)<BUFFER_SIZE:
			#print('not rec')
			break
	try:
		command=json.loads(data.decode('utf-8'))
		if command["command"]["cmd"]==10: 
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
	except ValueError:
		socket.close()

def client_thread(socket):
	data=b''
	while True:
		# ~ time.sleep(0.01)
		part = socket.recv(BUFFER_SIZE)
		data+=part
		if len(part)<BUFFER_SIZE:
			#print('not rec')
			break
	command=data.decode('utf-8')
	print("command_string:", command, "\n")
	msg=json.loads(command) 
	reply=msg
	reply["status"]=3
	socket.send(str.encode(json.dumps(reply)+'\t'))
	socket.send(str.encode("\n"))
	# ~ print("msg recieved:", msg, "\n")
	global parancsok
	parancsok = parancsok + [msg]
	socket.close()

def msgbacktest(command):
	print("command:", command)
	time.sleep(command["command"]["param1"])
	msg=command
	print("msg:", msg)
	msg["status"]=1
	return msg

def report(msg):
	global last_report
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((SERVER_IP, TCP_REPORT))
	time.sleep(0.2)
	msgback=json.dumps(msg)
	s.send(str.encode(msgback))
	s.send('\n'.encode('utf-8'))
	s.close()
	print("report sent:", msg)
	last_report=msg
	time.sleep(0.1)

def direct_msg(string):
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((SERVER_IP, TCP_DIRECT))
	s.send(str.encode(string))
	s.send('\n'.encode('utf-8'))
	s.close()


def move_f(msg):
	global pos
	pos.update()
	time.sleep(1)
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
	time.sleep(0.5)
	if pos.w==270:
		pos.heading=0
	else:
		pos.heading+=90
	msg["status"]=1
	pos.update()
	return msg

def turn_l(msg):
	global pos
	time.sleep(0.5)
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
	s.connect((SERVER_IP, 41007))
	s.send(str.encode(string))
	s.close()
	msg["status"]=1
	return msg

def execute(run_event):
	global parancsok
	global last_report
	# ~ idle_counter=0
	while run_event.is_set():
		if len(parancsok) == 0:
			# ~ idle_counter+=1
			time.sleep(0.1)
			# ~ if idle_counter>100: #ennek a counternek a lényege az hogy néha a reportok valamiért képesek elveszni így a szerver
				# ~ report(last_report) #nem tudja hogy kész a robot, ezért ha 10 másodpercig nics semmi parancs, újraküldjük a reportot
				# ~ idle_counter=0
		else:
			# ~ idle_counter=0
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
			# ~ print("nextcmd:", nextcmd)
			msg=func(nextcmd)
			# ~ print("msg (funck return):", msg)
			report(msg)
			del parancsok[0]
def check_in():
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print(SERVER_IP)
	s.connect((SERVER_IP, CHECK_IN))
	s.send(str.encode(socket.gethostbyname(socket.gethostname())))
	s.close()
	print("checked in")
	

def hiba(command):
	msg=command
	msg["status"]=2
	return msg


if __name__=="__main__":
	own_ip=socket.gethostbyname(socket.gethostname())
	print(own_ip)
	parancsok = list()
	pos=position(5, 10, 180)
	BUFFER_SIZE = 1024
	TCP_PORT = 41001
	TCP_REPORT=41004
	TCP_DIRECT=5010
	CHECK_IN=5015
	last_report={
		"id": 1,
		"target": 0,
		"command": {
			"cmd": 99
		},
		"status": 1
	}

	run_event = threading.Event()
	run_event.set()
	SERVER_IP="192.168.56.1" #TODO: beállítani a szerver IP-jére amikor szerver és robot kikerül
	parser=threading.Thread(name='Parser', target=tcp_read, args=(5005,run_event,))
	parser.start()
	executer=threading.Thread(name='Execute', target=execute, args=(run_event,))
	executer.start()
	reporter=threading.Thread(name='reporter', target=tcp_reporter, args=(5011,run_event,))
	reporter.start()
	check_in()
	try:
		while True:
			time.sleep(0.1)
	except KeyboardInterrupt:
		print("start closing")
		run_event.clear()
		s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((socket.gethostbyname(socket.gethostname()), TCP_PORT))
		s.close()
		# ~ s2=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# ~ s2.connect((socket.gethostbyname(socket.gethostname()), 5011))
		# ~ s2.close()
		parser.join()
		print("parser closed")
		executer.join()
		print("executer closed")
		reporter.join()
		print("threads closed")
	

