import socket
import json
import threading
import copy
import time
import datetime
import re
import random
from test_graphics import *
from graph_v4 import *

class test:
	def __init__(self):
		self.a=10

class robot:
	class pos:
		def __init__(self, x, y, w, heading, node):
			self.x=x
			self.y=y
			self.w=w
			self.heading=heading
			self.node=0
		def refresh(self):
			global graph
			curr_node=[0,10000]
			for vertex in graph.vertices:
				if (vertex.x-self.x)**2 + (vertex.y-self.y)**2<curr_node[1]:
					curr_node[0]=vertex.v_id
					curr_node[1]=(vertex.x-self.x)**2 + (vertex.y-self.y)**2<curr_node[1]
			w=round(self.heading/90, 0)*90
			self.node=curr_node[0]
			self.w=w
			# ~ print("position: node: ", self.node, "w: ", self.w, "x: ", self.x, "y: ", self.y, "heading: ", self.heading)
		
	def __init__(self, name, ip, x, y, heading):
		print("robot init started")
		global graph
		self.name=name
		self.ip=ip
		self.busy=False
		self.pos=self.pos(5, 10, 180, 0, 0)
		self.pos.x=x
		self.pos.y=y
		self.pos.heading=heading
		self.update_position()
		self.pos.refresh()
		graph.blocked_nodes.append(self.pos.node)
		self.IdleAvoid=threading.Event()
		self.MovingAvoid=threading.Event()
		self.Wait=threading.Event()
		self.current_route=[]
		self.removed_route=[]
		self.toFreeAfterAvoid=None
		self.ClearEarly=None
		self.NoAvoidThrough=None
	
	def command_to_bot(self, command):
		s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect(('localhost', TCP_OUT))
		command["target_ip"]=self.ip
		s.send(str.encode(json.dumps(command)))
		s.close()
		# ~ print("command sent:", command)
		time.sleep(0.4)
		return 0

	def msgbacktest(self, command):
		self.command_to_bot(command)
		ret=[]
		ret.append(command)
		return ret
		
	def manymsg(self, command):
		global stop_all
		cmd_to_send=copy.deepcopy(command)
		cmd_to_send["command"]["cmd"]=99
		cmd_to_send2=copy.deepcopy(cmd_to_send)
		del cmd_to_send["command"]["param2"]
		ret=[]
		for x in range(0, command["command"]["param2"]):
			cmd_to_send2["id"]=request_id()
			self.command_to_bot(cmd_to_send2)
			ret.append(cmd_to_send2)
			time.sleep(0.01)
			if stop_all:
				return 2
		return ret
	
	def ask(self, IP, port, msg):
		s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((IP, port))
		s.send(str.encode(json.dumps(msg)))
		return s
	
		
	def update_position(self, command=None):
		if command is not None:
			cmd={"id": command["id"],
				"target": self.name,
				"command": {
					"cmd": 10,
					},
				"status": 0}
			# ~ self.command_to_bot(command)
			comm_socket=self.ask(self.ip, 5011, cmd)			   
			data=b''
			while True:
				# ~ time.sleep(0.01)
				part = comm_socket.recv(BUFFER_SIZE)
				data+=part
				if len(part)<BUFFER_SIZE:
					#print('not rec')
					break
			string=data.decode("utf-8") 
			pos_recv = json.loads(string)
			self.pos.x=pos_recv["x"]
			self.pos.y=pos_recv["y"]
			self.pos.heading=pos_recv["heading"]
			self.pos.refresh()
			print("position: node: ", self.pos.node, "w: ", self.pos.w, "x: ", self.pos.x, "y: ", self.pos.y, "heading: ", self.pos.heading)
			command["status"]=1
			ret=[command]
			return ret
		else:
			cmd={"id": 0,
				"target": self.name,
				"command": {
					"cmd": 10,
					},
				"status": 0}
			global bots
			global picture
			try:
				comm_socket=self.ask(self.ip, 5011, cmd) #TODO rework ask
				data=b''
				while True:
					# ~ time.sleep(0.01)
					part = comm_socket.recv(BUFFER_SIZE)
					data+=part
					if len(part)<BUFFER_SIZE:
						break
				string=data.decode("utf-8") 
				pos_recv = json.loads(string)
				self.pos.x=pos_recv["x"]
				self.pos.y=pos_recv["y"]
				self.pos.heading=pos_recv["heading"]
				self.pos.refresh()
			except ConnectionRefusedError:
				try:
					removed_bot=bots.pop(self.name)
					print("removed bot pos:", removed_bot.pos.node)
					# ~ try:
						# ~ graph.parked_nodes.remove(removed_bot.pos.node)
					# ~ except ValueError:
						# ~ None
					try:
						graph.blocked_nodes.remove(removed_bot.pos.node)
					except ValueError:
						None
					# ~ graph.timekeeper.remove_future(removed_bot.name)
					# ~ graph.timekeeper.timespace.remove([])
				except IndexError:
					None
				graph.blocked_nodes=[]
				i=0
				for thisbot in bots:
					thisbot.name=i
					graph.blocked_nodes.append(thisbot.pos.node)
					i+=1
				picture.undraw_bots()
				picture.bot_graphics=picture.make_bots(bots, picture.win)
			
		
			
	def path_to(self, cmd):
		global graph
		global stop_all
		ret=[]
		if type(cmd)==int:
			cmd={
					"id": request_id(),
					"target": self.name,
					"command":{
						"cmd": 7,
						"param1": cmd
					},
					"status": 0
					}
		finish_node=cmd["command"]["param1"]
		if self.pos.node==finish_node:
			return 1
		while True:
			self.update_position()
			# ~ print("timespace when start planning:", graph.timekeeper.timespace)
			try:
				# ~ print("self.NoAvoidThrough:", self.NoAvoidThrough)
				route=graph.plan_path(self.pos.node, finish_node, self.pos.w, self.NoAvoidThrough)
			except NoPathError:
				return 2
			# ~ print("planned route: ", route)
			templist=[]
			templist.append(self.pos.node)
			templist.extend(route)
			self.current_route=templist
			print("bot ", self.name, "planned route: ", self.current_route)
			self.NoAvoidThrough=None
			path_success=self.nav_path()
			self.current_route=[]
			if stop_all:
				return 2
			if path_success==1:
				return 1
		
	
	def LookForFreeNode(self, depth=1):
		global graph
		global bots
		# ~ print("LookForFreeNode depth:", depth)
		# ~ print(self.NoAvoidThrough)
		blocked_onelist=[]
		for bot_blocked in graph.blocked_nodes: #azért van ez az egy listába gyűjtés mert felmerült lehetőségként
			blocked_onelist.append(bot_blocked) #hogy nem csak a következő hanem több node-ra előre jelzi a robot hogy hova megy
		options=[self.pos.node]
		for i in range(0, depth):
			temp_options=[]
			for option in options:
				for adjacent in graph.vertices[option-1].adj_vertices:
					if adjacent not in options and adjacent not in temp_options and adjacent != self.NoAvoidThrough: 
						temp_options.append(adjacent)
						# ~ print("added to options:", adjacent)
			options=options+temp_options
		# ~ base=copy.deepcopy(options)
		for bot in bots:
			if bot.name==self.name:
				continue
			try:
				options.remove(bot.pos.node)
			except ValueError:
				None
			for node in bot.current_route:
				# ~ print("node:", node)
				try:
					options.remove(node)
				except ValueError:
					None
		for node in self.removed_route:
			try:
				options.remove(node)
			except ValueError:
				None
		for blocked in blocked_onelist:
			try:
				options.remove(blocked)
			except ValueError:
				None
		if len(options)==0:
			return self.LookForFreeNode(depth+1)
		else:
			print("Free Node Found:", options[0])
			return options[0] #random.randint(0, len(options)-1)
		
	
		
	def IdleDodger(self):
		while True:
			if self.busy==False and self.IdleAvoid.isSet():
				self.IdleAvoid.clear()
				freenode=self.LookForFreeNode()
				self.path_to(freenode)
				time.sleep(2)
				self.IdleAvoid.set()
				time.sleep(1)
			time.sleep(0.1)
					
	def nav_path(self):
		global graph
		global stop_all
		global bots
		route=self.current_route
		# ~ print("nav_path start in bot_id:", self.name)
		for i in range(1, len(route)):
			# ~ print("next node:", route[i])
			if stop_all:
				return 2
			
			self.update_position()
			before=self.pos.node
			
			ret_element=self.goto(route[i])
			if ret_element==4:
				colliding_with=None
				j=0
				for blocked in graph.blocked_nodes:
					if route[i]==blocked:
						colliding_with=j
					j+=1
				if bots[colliding_with].busy==False:#this is the case where the other bot is idle so it will avoid
					bots[colliding_with].NoAvoidThrough=self.pos.node
					bots[colliding_with].IdleAvoid.set()
					# ~ bots[colliding_with].ClearEarly=self.name
					time.sleep(1)
					bots[colliding_with].IdleAvoid.wait()
					bots[colliding_with].IdleAvoid.clear()
					ret_element=self.goto(route[i])
				else:
					if len(bots[colliding_with].current_route)<=len(self.current_route):
						#a másik robot priority, ez a robot tér ki
						bots[colliding_with].Wait.set()
						self.removed_route=copy.deepcopy(self.current_route)
						self.current_route=[]
						freenode=self.LookForFreeNode()
						self.toFreeAfterAvoid=colliding_with
						self.path_to(freenode)
						bots[colliding_with].Wait.clear()
						return 2
					else:
						#ez a robot a priority úgyhogy a másiknak kell kitérnie
						# ~ bots[colliding_with].toFreeAfterAvoid=self.name
						bots[colliding_with].NoAvoidThrough=self.pos.node
						bots[colliding_with].MovingAvoid.set()
						time.sleep(1)
						bots[colliding_with].MovingAvoid.wait()
						bots[colliding_with].MovingAvoid.clear()
						ret_element=self.goto(route[i])
						
						
				#ez az egész mizéria arra lett volna hogy ne kelljen az egész kitérési manővert végigvárni
				#valamiért nem működött ezért ezt a részt kicommenteltem és minden egyéb rájuk hivatkozást is
				#de a bot.<valami> objectec bent maradtek a bot _init_ -jében
				#továbfejlesztési lehetőség ennek a megjavítása
				
				# ~ if self.ClearEarly is not None and i==2:
					# ~ self.IdleAvoid.set()
					# ~ self.ClearEarly=None
				# ~ if self.toFreeAfterAvoid is not None and i==2:
					# ~ bots[toFreeAfterAvoid].Wait.clear()
					# ~ self.MovingAvoid.set()
					# ~ self.toFreeAfterAvoid=None
			if ret_element==2 or ret_element==4:
				return 2
			while True:
				if watcher(ret_element)==1:
					break
				if stop_all:
					return 2
				time.sleep(0.01)
			
		# ~ print("nav_path in bot", self.name, "returns 1")
		return 1
			
	def goto(self, msg):
		global graph
		while True:
			if not self.Wait.isSet():
				break
			time.sleep(0.1)
		if type(msg) is int:
			goal=msg
			self.update_position()
			if goal in graph.blocked_nodes:
				return 4
			before=self.pos.node
			try:
				graph.blocked_nodes[self.name]=goal
			except ValueError:
				print("couldn't remove blocked vertex in nav_path")
			ret=[]
			# ~ print("graph.vertices[self.pos.node-1].adj_vertices:", graph.vertices[self.pos.node-1].adj_vertices)
			for adjacent in graph.vertices[self.pos.node-1].adj_vertices:
				# ~ print("self.pos.node:", self.pos.node, "adjacent:", adjacent)
				if adjacent==goal:
					if self.pos.node-adjacent==1:
						face={
							"id": request_id(),
							"target": self.name,
							"command":{
								"cmd": 8,
								"param1": 0
							},
						"status": 0
						}
					elif self.pos.node-adjacent==-1:
						face={
							"id": request_id(),
							"target": self.name,
							"command":{
								"cmd": 8,
								"param1": 180
							},
						"status": 0
						}
					elif self.pos.node-adjacent<-1:
						face={
							"id": request_id(),
							"target": self.name,
							"command":{
								"cmd": 8,
								"param1": 90
							},
						"status": 0
						}
					elif self.pos.node-adjacent>1:
						face={
							"id": request_id(),
							"target": self.name,
							"command":{
								"cmd": 8,
								"param1": 270
							},
						"status": 0
						}
					else:
						print("first return 2") 
						return 2
					ret_element=self.face_to(face)
					if type(ret_element) is list:
						ret.extend(ret_element)
					ret_element=self.move_f()
					ret.extend(ret_element)
					return ret
			print("second return 2")
			return 2
		else:
			cmd=copy.deepcopy(msg)
			goal=cmd["command"]["param1"]
			self.update_position()
			if goal in graph.blocked_nodes:
				return 2
			ret=[]
			for adjacent in graph.vertices[self.pos.node-1].adj_vertices:
				if adjacent==goal:
					if self.pos.node-adjacent==1:
						face={
							"id": request_id(),
							"target": self.name,
							"command":{
								"cmd": 8,
								"param1": 0
							},
						"status": 0
						}
					elif self.pos.node-adjacent==-1:
						face={
							"id": request_id(),
							"target": self.name,
							"command":{
								"cmd": 8,
								"param1": 180
							},
						"status": 0
						}
					elif self.pos.node-adjacent<-1:
						face={
							"id": request_id(),
							"target": self.name,
							"command":{
								"cmd": 8,
								"param1": 90
							},
						"status": 0
						}
					elif self.pos.node-adjacent>1:
						face={
							"id": request_id(),
							"target": self.name,
							"command":{
								"cmd": 8,
								"param1": 270
							},
						"status": 0
						}
					else: 
						return 2
					ret_element=self.face_to(face)
					if type(ret_element) is list:
						ret.extend(ret_element)
					
					ret_element=self.move_f()
					ret.extend(ret_element)
					return ret
			return 2
	
	def turn_l(self, msg=None):
		if msg is not None:
			self.command_to_bot(msg)
			ret=[]
			ret.append(msg)
		else:
			cmd={
				"id": request_id(),
				"target": self.name,
				"command":{
					"cmd": 3
				},
				"status": 0
			}
			self.command_to_bot(cmd)
			ret=[]
			ret.append(cmd)
		return ret

	def turn_r(self, msg=None):
		if msg is not None:
			self.command_to_bot(msg)
			ret=[]
			ret.append(msg)
		else:
			cmd={
				"id": request_id(),
				"target": self.name,
				"command":{
					"cmd": 4
				},
				"status": 0
			}
			self.command_to_bot(cmd)
			ret=[]
			ret.append(cmd)
		return ret
	
	def face_to(self, msg):
		global graph
		ret=[]
		self.update_position()
		goal=msg["command"]["param1"]
		if goal==self.pos.w:
			return 1
		elif goal>self.pos.w:
			no=int((goal-self.pos.w)/90)
			if no==3:
				ret_element=self.turn_l()
				ret.extend(ret_element)
			else:
				for i in range(0, no):
					ret_element=self.turn_r()
					ret.extend(ret_element)
					time.sleep(0.01)
		elif goal<self.pos.w:
			no=int((self.pos.w-goal)/90)
			if no==3:
				ret_element=self.turn_r()
				ret.extend(ret_element)
			else:
				for i in range(0, no):
					ret_element=self.turn_l()
					ret.extend(ret_element)
					time.sleep(0.01)
		else:
			return 2
		return ret
		
	def move_f(self,msg=None):
		global graph
		ret=[]
		if msg is not None:
			self.command_to_bot(msg)
			ret.append(msg)
		else:
			cmd={
				"id": request_id(),
				"target": self.name,
				"command":{
					"cmd": 1
				},
				"status": 0
			}
			self.command_to_bot(cmd)
			ret.append(cmd)
		# ~ print("move_f returns: ", ret)
		# ~ graph.blocked_nodes.remove(self.pos.node)
		return ret

	def sbs_manymsg(self, command):
		cmd_to_send=copy.deepcopy(command)
		cmd_to_send["command"]["cmd"]=99
		del cmd_to_send["command"]["param2"]
		checklist=[]
		for i in range(0, command["command"]["param2"]):
			cmd_to_send["id"]=request_id()
			checklist.append(copy.deepcopy(cmd_to_send))
		for x in range(0, len(checklist)):
			nextcmd=checklist.pop(0)
			self.command_to_bot(nextcmd)
			while True:
				result=search(nextcmd["id"], done)
				if not result=="none":
					if result["status"]==1:
						break
					if result["status"]==2:
						return 2
		return 1

def request_id():
	global next_free_id
	next_free_id-=1
	return next_free_id

def search(msg_id, base):
		if len(base)!=0:
			for i in range(0,len(base)):
				if base[i]["id"]==msg_id:
					return base[i]
			return "none"
		return "none"
def reply_to_node(msg, socket):
	socket.send(str.encode(json.dumps(msg)))
	socket.close()	
	
	
def report_to_node(msg): #az msg-t visszaküldi a Node-red-nek
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('localhost', TCP_REPORT))
	if type(msg) is str:
		s.send(str.encode(msg))
	else:
		s.send(str.encode(json.dumps(msg)))
	s.close()

def tcp_read(port): #ez liste-el a Node-red üzeneteire és meghívja a client thread-et
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('localhost', port))
	serversocket.listen(5)
	while True:					   
		(clientsocket, address) = serversocket.accept()	
		ct=threading.Thread(name='ct', target=client_thread, args=(clientsocket,))	
		ct.start()	
		# ~ print("a client thread has started")

def collector(port):
	print("collector started")
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind(('localhost', port))
	serversocket.listen(10)
	while True:					   
		(clientsocket, address) = serversocket.accept()	
		# ~ print("connection accepted by collector from:", address)
		collect_t=threading.Thread(name='collector_thread', target=collector_thread, args=(clientsocket,))	
		collect_t.start()
	
def collector_thread(sock):
	# ~ print("collector thread started")
	data=b''
	global done
	while True:
		# ~ time.sleep(0.01)
		part = sock.recv(BUFFER_SIZE)
		data+=part
		if len(part)<BUFFER_SIZE:
			break
	# ~ print(data)
	commands=re.split('[\n]', data.decode('utf-8'))
	commands=remove_values_from_list(commands,'')
	sock.send(str.encode('\n'))
	# ~ print("commands:", commands)
	for command in commands:
		# ~ print("command:", command)
		parsed=json.loads(command)
		# ~ print("collector parsed:", parsed)
		done.append(parsed)
	# ~ print("collector thread recieved and appended:", command)
	sock.close()
	

def remove_values_from_list(the_list, val):
   return [value for value in the_list if value != val]

def client_thread(socket): #a client_thread beolvassa az üzeneteket a Node-red től és eltárolja a parancsol list-ben
	data=b''
	while True:
		# ~ time.sleep(0.01)
		part = socket.recv(BUFFER_SIZE)
		data+=part
		if len(part)<BUFFER_SIZE:
			#print('not rec')
			break
	string=data.decode("utf-8") 
	# ~ print("recieved command:", string)
	msg = json.loads(string)
	global parancsok
	global stop_all
	if msg["command"]["cmd"]==80:
		stop_all=True
		print("stop all set to true")
		socket.close()
	else:
		parancsok.append(msg)
		socket.close()

def execute(): #ez nézi a parancsok list-et és meghívja a manager-t hogy végezze el a parancsot- majd törli azt
	global parancsok
	while True:
		if len(parancsok) == 0:
			time.sleep(0.1)
		else:
			try:
				nextcmd=parancsok[0]
			except IndexError:
				continue
			i=0
			try:
				while bots[nextcmd["target"]].busy==True:
					i+=1
					nextcmd=parancsok[i]
			except IndexError:
				continue
			switcher={
				99:	"msgbacktest",
				98: "manymsg",
				97: "sbs_manymsg",
				10: "update_position",
				3: "turn_l",
				4: "turn_r",
				6: "goto",
				8: "face_to",
				1: "move_f",
				7: "path_to"
				}
			func=switcher.get(nextcmd["command"]["cmd"], "hiba")
			bots[nextcmd["target"]].busy=True
			# ~ print(func)
			manager_thread=threading.Thread(name='manager', target=manager, args=(func, nextcmd,))
			manager_thread.start()
			del parancsok[i]
			
def manager(func, cmd): #a manager a megkapott parancsnak megfelelően jár el
	target=cmd["target"]
	func_copy=copy.deepcopy(func)
	func_copy=getattr(bots[target], func_copy)
	ids=func_copy(cmd)
	msg=copy.deepcopy(cmd)
	if type(ids)==list:
		result=watcher(ids)
		msg["status"]=result
		report_to_node(msg)
	if type(ids)==int:
		msg["status"]=ids
		report_to_node(msg)
	if func_copy!="update_position":
		func_to_call=getattr(bots[target], "update_position")
		func_to_call()
	bots[target].busy=False
	# ~ print("busy set to false")
	
	
def watcher(ids): #a done listában keresi az ids listának megfelelő id-vel rendelkező parancsokat
	#ha valamelyik 2-es eredménnyel tér vissza akkor 2-est return öl
	#ha mindegyik id-vel 1-es eredményt talál akkor 1-et return-öl
	global done
	global stop_all
	while True:
		time.sleep(0.1)
		if stop_all:
			return 2
		count=0
		for i in range(0, len(ids)):
			result=search(ids[i]["id"], done)
			if result != "none":
				if result["status"]==2:
					return 2
				if result["status"]==1:
					count+=1
		if count==len(ids):
			return 1
def hiba(self, command):
	time.sleep(1)

def live_telemetry():
	global graph
	global bots
	s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect(('localhost', TELEMETRY))
	
	while True:
		try:
			if len(graph.blocked_nodes) != len(set(graph.blocked_nodes)):
				print("collision--------------------------------------------------------------------------------------------")
				now=datetime.datetime.now()
				positions=[]
				routes=[]
				for bot in bots:
					positions.append(bot.pos.node)
					routes.append(bot.current_route)
				collision_dict={
					"time": now.strftime("%Y/%m/%d, %H:%M:%S"),
					"bot_positions": positions,
					"routes:": routes
				}
				with open("collision_log.json", "a") as outputfile:
					outputfile.write(json.dumps(collision_dict))
					outputfile.write("\n")
				outputfile.close()
				time.sleep(2)
		except IndexError:
			None
		try:
			telem={
				"robot0_node": bots[0].pos.node,
				"robot1_node": bots[1].pos.node,
				"blocked_vertices": graph.blocked_nodes,
				"parked_nodes": graph.parked_nodes,
				# ~ "timespace": graph.timekeeper.timespace
				}
			s.send(str.encode(json.dumps(telem)))
		except IndexError:
			None
		time.sleep(0.1)
			
def bot_checker():
	print("checker started")
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	serversocket.bind((server_ip, 5015))
	serversocket.listen(5)
	while True:					   
		(clientsocket, address) = serversocket.accept()	
		print("bot checker accepted:", address)
		collect_t=threading.Thread(name='checker_thread', target=checker_thread, args=(clientsocket,))	
		collect_t.start()
	
def checker_thread(socket):
	print("checker thread started")
	global picture
	global bots
	global graph
	data=b''
	while True:
		# ~ time.sleep(0.1)
		part = socket.recv(BUFFER_SIZE)
		data+=part
		if len(part)<BUFFER_SIZE:
			break
	ip=data.decode("utf-8") 
	bots.append(robot(len(bots), ip, 5, 10, 180))
	# ~ graph.timekeeper.timespace.append([])	
	picture.old_graphics=copy.copy(picture.bot_graphics)
	picture.bot_graphics=picture.make_bots(bots, picture.win)
	bot_Idle_Thread=threading.Thread(name='idle_dodger', target=bots[-1].IdleDodger)
	bot_Idle_Thread.start()
	
	
# ~ def look_for_collision(): 
		# ~ global graph
		# ~ global bots
		# ~ for bot in bots
	
if __name__=="__main__":
	import socket
	parancsok=[]
	done=[]
	server_ip = "192.168.56.1" #socket.gethostbyname(socket.gethostname())
	BUFFER_SIZE = 1024
	TCP_PORT = 41000
	TCP_OUT=41002
	TCP_COLLECT=41005
	TCP_REPORT=41006
	TELEMETRY=6000
	bots=[]
	tests=[]
	next_free_id=0
	stop_all=False
	graph=graph("SFGraphVerticesConfig_2.json")
	listener=threading.Thread(name='listener', target=tcp_read, args=(TCP_PORT,))
	listener.start()
	collector=threading.Thread(name='collector', target=collector, args=(TCP_COLLECT,))
	collector.start()
	executer=threading.Thread(name='executer', target=execute, args=())
	executer.start()
	telemetry=threading.Thread(name='live_telemetry', target=live_telemetry, args=())
	telemetry.start()
	checker=threading.Thread(name='checker', target=bot_checker, args=())
	checker.start()
	picture=graphic(graph, bots)
	print("main  loop starting")
	while True:
		output=""
		for node in graph.vertices:
			output+=str(node.v_id) + "--" + str(node.adj_vertices) + "\n"
		with open("nodes_check.json", "w") as outputfile:
			outputfile.write(output)
		for bot in bots:
			bot.update_position()
		if len(done)>2000:
			done=done[-2000:-1]
		try:
			picture.update(bots)
		except IndexError:
			picture.win.update()
			print("no graphics object available")
		if stop_all:
			parancsok=[]
			for bot in bots:
				msg={
					"id": 0,
					"target": bot.name,
					"command": {
						"cmd": 80
					},
					"status": 0
				}
				bot.command_to_bot(msg)
			time.sleep(10)
			parancsok=[]
			graph.blocked_nodes=[]
			for bot in bots:
				bot.update_position()
				graph.blocked_nodes.append(bot.pos.node)
				print("added to blocked_nodes:", bot.pos.node)
			stop_all=False
			print("stop all set to false")
		time.sleep(0.01)
