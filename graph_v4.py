import math
import json
import time
import threading
import copy
from MyExceptions import *
turn_cost=5
stay_in_place_cost=5


class graph:	
	class vertex:
		def __init__(self, v_id, x, y, adj_edges, adj_vertices):
			self.v_id=v_id
			self.x=x
			self.y=y
			self.adj_edges=adj_edges
			self.adj_vertices=adj_vertices
			
	class edge:
		def __init__(self, e_id, start, end, weight):
			self.e_id=e_id
			self.start=start
			self.end=end
			self.weight=weight
	class Node:
		def __init__(self, vertex, parent, depth):
			self.vertex=vertex
			self.parent=parent
			self.g=0
			self.h=0
			self.f=0
			self.depth=depth
		def same_exists(self, open_list):
			for open_node in open_list:
				if open_node==self:
					return True
			return False
			
	def __init__(self, configfile):
		with open(configfile) as config:
			temp_ver=config.read().splitlines()
		self.vertices=[]
		for i in range(0,len(temp_ver)):
			temp_ver[i]=json.loads(temp_ver[i])
			tempvertex=self.vertex(temp_ver[i]["v_id"], temp_ver[i]["x"], temp_ver[i]["y"], [], temp_ver[i]["adj_vertices"])
			self.vertices.append(tempvertex)
		temp_edges=self.generate_edges(self.vertices)
		self.edges=[]
		for i in range(0, len(temp_edges)):
			tempdict={
			"id": i+1,
			"start": temp_edges[i][0],
			"end": temp_edges[i][1],
			"weight": abs(self.vertices[(temp_edges[i][0]-1)].x-self.vertices[(temp_edges[i][1]-1)].x)+abs(self.vertices[(temp_edges[i][0]-1)].y-self.vertices[(temp_edges[i][1]-1)].y)
			}
			tempedge=self.edge(tempdict["id"], tempdict["start"], tempdict["end"], tempdict["weight"])
			self.edges.append(tempedge)
		self.blocked_nodes=[]
		self.parked_nodes=[]
		for vertex in self.vertices:
			for adjacent in vertex.adj_vertices:
				edge=self.find_edge(vertex.v_id, adjacent)
				vertex.adj_edges.append(edge)
		# ~ timer=threading.Thread(name='timer', target=self.timekeeper.run(), args=())
		# ~ timer.start()
		
	def find_direction(self, start, end):
		# ~ print("start:", start, "end:", end)
		if end not in self.vertices[start-1].adj_vertices:
			if start==end:
				raise StayInPlace
			else:
				raise InvalidFacing("nodes not adjacent")
		if start-end==-1:
			return 180
		elif start-end==1:
			return 0
		elif start-end<-1:
			return 90
		elif start-end>1:
			return 270
		else:
			raise InvalidFacing("no facing found")
	
	def change_weights(self, delta):
		for i in range(0, len(self.edges)):
			self.edges[i].weight+=delta[i]
	def generate_edges(self, vertices):
		edges=[]
		for i in range(0, len(vertices)):
			for j in range(0, len(vertices[i].adj_vertices)):
				if not (vertices[i].adj_vertices[j], vertices[i].v_id) in edges:
					edges.append((vertices[i].v_id, vertices[i].adj_vertices[j]))	
		return edges
	
	def find_edge(self, start, end):
		for edge in self.edges:
			if edge.start==start and edge.end==end:
				return edge
			if edge.start==end and edge.end==start:
				return edge
		raise NoEdge
	
		
	def plan_path(self, start_id, end_id, facing, noGoThrough=None):
		global turn_cost
		global stay_in_place_cost
		start_node=self.Node(self.vertices[start_id-1], None, 0)
		start_node.g=start_node.h=start_node.f=0
		end_node = self.Node(self.vertices[end_id-1], None, 0)
		end_node.g = end_node.h = end_node.f = 0
		
		open_list=[]
		closed_list=[]
		if end_node.vertex.v_id in self.parked_nodes:
			raise NoPathError
		open_list.append(start_node)
		while len(open_list)>0:
			current_node = open_list[0]
			current_index = 0
			for index, item in enumerate(open_list):
				if item.f < current_node.f:
					current_node = item
					current_index = index
			try:
				if current_node.vertex.v_id==current_node.parent.vertex.v_id:
					None
					# ~ print("current step is staying in place---------------------------------------------------------------------")
					# ~ print(current_node.parent.vertex.v_id, "-->", current_node.vertex.v_id)
			except AttributeError:
				None
			open_list.pop(current_index)
			closed_list.append(current_node)
			if current_node.vertex == end_node.vertex:
				path=[]
				current = current_node
				while current is not None:
					path.append(current.vertex.v_id)
					current = current.parent
				route=path[::-1]
				route.pop(0)
				# ~ print("cost of path:", current_node.g)
				# ~ print("cost of path:", current_node.f)
				return route
			children=[]
			for adjacent in current_node.vertex.adj_vertices:
				new_node=self.Node(self.vertices[adjacent-1], current_node, current_node.depth+1)
				children.append(new_node)
			stay=self.Node(current_node.vertex, current_node, current_node.depth+1)
			stay.g=current_node.g+stay_in_place_cost #TODO növekmény értékét kitalálni pontosra
			children.append(stay)
			for child in children:
				future_break=False
				if child.same_exists(closed_list) or child.vertex.v_id==noGoThrough:
					continue
				try:
					edge_to_next=self.find_edge(current_node.vertex.v_id, child.vertex.v_id)
					child.g=current_node.g+edge_to_next.weight
					# ~ print("current_node_id:", current_node.vertex.v_id, "child_node_id:", child.vertex.v_id)
					try:
						turns=abs(self.find_direction(current_node.vertex.v_id, child.vertex.v_id)-self.find_direction(current_node.parent.vertex.v_id, current_node.vertex.v_id))/90
						if turns==3:
							child.g+=turn_cost
						else:
							child.g+=turns
					except AttributeError:
						turns=abs(self.find_direction(current_node.vertex.v_id, child.vertex.v_id)-facing)/90
					except StayInPlace:
						None
				except NoEdge:
					child.g=current_node.g+stay_in_place_cost
				child.h=math.sqrt((end_node.vertex.x-child.vertex.x)**2+(end_node.vertex.y-child.vertex.y)**2)
				child.f=child.h+child.g
				if child.same_exists(open_list) or child.same_exists(closed_list):
					None
				else:
					open_list.append(child)
		return "no path"		
			
					
if __name__=="__main__":
	import json
	
	a=graph("SFGraphVerticesConfig_2.json")
	
	init_bias=[]
	# ~ for i in range(0, len(a.edges)):
		# ~ if i in [38,40,42,44,46,48,50,52,54]:
			# ~ init_bias.append(5)
		# ~ else:
			# ~ init_bias.append(0)
	output=""
	# ~ a.change_weights(init_bias)
	# ~ a.blocked_nodes.extend([13, 14])
	# ~ a.parked_nodes.extend([41,40,39,38,37,36,35,34,33,32])
	for i in range(0, len(a.edges)):
		output+="id:"+str(a.edges[i].e_id)+"; start:"+str(a.edges[i].start)+"; end:"+str(a.edges[i].end)+"; weight:"+str(a.edges[i].weight)+"\n"
	with open("edges_output.json", "w") as outputfile:
		outputfile.write(output)
	print("a")
	print(a.plan_path(6, 37, 180))

